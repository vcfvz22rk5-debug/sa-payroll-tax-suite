"""
server.py - the dashboard's web server.

Standard library only: http.server for the HTTP, sqlite3 for the data
and json for the API. There is no Flask, no Node, nothing to install.

    payroll-suite serve            # http://localhost:8000

The browser asks for JSON, the server answers with JSON, and the
frontend draws the charts by hand in SVG.
"""

import json
import mimetypes
import os
import posixpath
import sys
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from payroll_suite.compliance import (
    deadlines as all_deadlines,
    emp201 as build_emp201,
    emp501 as build_emp501,
    irp5 as build_irp5,
)
from payroll_suite.db import DEFAULT_DB, Database
from payroll_suite.engine import calculate_pay_run
from payroll_suite.models import PayRun
from payroll_suite.reports import payslips_to_rows

WEB_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web"
)


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status
        self.message = message


# ----------------------------------------------------------------------
# The API
# ----------------------------------------------------------------------
class Api:
    """Every endpoint the dashboard needs, in one place."""

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path

    def _db(self) -> Database:
        return Database(self.db_path)

    # -- reads -----------------------------------------------------------
    def overview(self) -> dict:
        db = self._db()
        runs = db.list_runs()
        periods = [r.period for r in runs]
        latest = periods[0] if periods else None

        totals = db.payroll_totals(latest) if latest else {}
        if latest:
            totals.setdefault("head_count", len(db.payslips_for_period(latest)))

        # The trend: the last twelve periods, oldest first.
        trend = []
        for period in sorted(periods)[:12]:
            period_totals = db.payroll_totals(period)
            trend.append({
                "period": period,
                "gross": period_totals.get("total_gross", 0),
                "paye": period_totals.get("total_paye", 0),
                "net": period_totals.get("total_net", 0),
                "cost": round(
                    period_totals.get("total_gross", 0)
                    + period_totals.get("total_employer_cost", 0),
                    2,
                ),
                "head_count": len(db.payslips_for_period(period)),
            })

        employees = db.list_employees()
        deadlines = [
            {
                "date": d["date"].isoformat(),
                "name": d["name"],
                "detail": d["detail"],
                "source": d["source"],
                "days": (d["date"] - date.today()).days,
            }
            for d in all_deadlines("2027")
        ]
        db.close()

        return {
            "company": "Shongwe & Co",
            "tax_year": "2027",
            "periods": sorted(periods),
            "latest_period": latest,
            "head_count": len(employees),
            "totals": totals,
            "trend": trend,
            "deadlines": [d for d in deadlines if d["days"] >= 0][:6],
            "generated": datetime.now().isoformat(timespec="seconds"),
        }

    def employees(self) -> list:
        db = self._db()
        employees = db.list_employees(active_only=False)
        db.close()
        return [
            {
                "id": e.id,
                "employee_number": e.employee_number,
                "full_name": e.full_name,
                "age": e.age,
                "role": e.notes,
                "email": e.email,
                "start_date": e.start_date.isoformat(),
                "basic_salary": e.basic_salary,
                "pension_rate": e.pension_rate,
                "pension_amount": e.pension_amount,
                "medical_members": e.medical_members,
                "medical_own": e.medical_own,
                "medical_employer": e.medical_employer,
                "commission_earner": e.commission_earner,
                "annual_leave_days": e.annual_leave_days,
                "active": e.active,
                "tax_year": e.tax_year,
            }
            for e in employees
        ]

    def payslips(self, period: str) -> list:
        db = self._db()
        payslips = db.payslips_for_period(period)
        db.close()
        return payslips_to_rows(payslips)

    def emp201(self, period: str) -> dict:
        db = self._db()
        payslips = db.payslips_for_period(period)
        db.close()
        if not payslips:
            raise ApiError(f"No payslips for {period}. Run the payroll first.")
        summary = build_emp201(payslips, period)
        summary["due_date"] = summary["due_date"].isoformat()
        return summary

    def deadlines(self, year: str) -> list:
        return [
            {
                "date": d["date"].isoformat(),
                "name": d["name"],
                "detail": d["detail"],
                "source": d["source"],
                "days": (d["date"] - date.today()).days,
            }
            for d in all_deadlines(year)
        ]

    def irp5(self, year: str) -> list:
        db = self._db()
        employees = [
            e for e in db.list_employees(active_only=False)
            if e.tax_year == str(year)
        ]
        payslips = db.list_payslips()
        db.close()
        certificates = []
        for employee in employees:
            try:
                certificates.append(build_irp5(employee, payslips))
            except ValueError:
                continue
        return certificates

    def emp501(self, year: str) -> dict:
        db = self._db()
        declarations = []
        for run in db.list_runs():
            if not run.period.startswith(str(year)[:4]):
                continue
            payslips = db.payslips_for_period(run.period)
            if payslips:
                declarations.append(build_emp201(payslips, run.period))
        employees = [
            e for e in db.list_employees(active_only=False) if e.tax_year == str(year)
        ]
        all_payslips = db.list_payslips()
        db.close()

        certificates = []
        for employee in employees:
            try:
                certificates.append(build_irp5(employee, all_payslips))
            except ValueError:
                continue
        return build_emp501(declarations, certificates)

    # -- writes ----------------------------------------------------------
    def run_payroll(self, period: str, force: bool = True) -> dict:
        db = self._db()
        try:
            parsed = datetime.strptime(period, "%Y-%m").date()
        except ValueError:
            raise ApiError(f"'{period}' is not a month. Use 2026-10.")

        employees = db.list_employees()
        if not employees:
            raise ApiError("There are no employees to pay.")

        payslips = calculate_pay_run(employees, parsed)

        run = db.get_run(period)
        if run:
            if not force:
                raise ApiError(f"There is already a run for {period}.", 409)
            db.delete_run(run)

        run = PayRun(period=period, pay_date=parsed,
                     notes=f"Run of {len(payslips)} employees")
        db.create_run(run)
        for payslip in payslips:
            payslip.run_id = run.id
        db.save_payslips(payslips)

        totals = db.payroll_totals(period)
        totals.setdefault("head_count", len(payslips))
        db.close()

        return {
            "period": period,
            "head_count": len(payslips),
            "totals": totals,
            "payslips": payslips_to_rows(payslips),
        }


# ----------------------------------------------------------------------
# The HTTP layer
# ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    api: Api = None           # set by serve()
    server_version = "PayrollSuite"

    def log_message(self, fmt, *args):
        # Quieter than the default, but still useful. The default
        # implementation passes the format string and its arguments
        # separately, so it has to be handled carefully.
        try:
            message = fmt % args
        except (TypeError, ValueError):
            message = " ".join(str(a) for a in args)
        if "/api/" in message:
            sys.stderr.write(f"  {message}\n")

    # -- helpers ---------------------------------------------------------
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str):
        if not os.path.isfile(path):
            self._send_json({"error": "Not found"}, 404)
            return
        content_type, _ = mimetypes.guess_type(path)
        with open(path, "rb") as handle:
            body = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            raise ApiError("The request body was not valid JSON.")

    # -- routing ---------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        route = posixpath.normpath(unquote(parsed.path))
        query = parse_qs(parsed.query)

        try:
            if route.startswith("/api/"):
                self._handle_api_get(route, query)
            else:
                self._handle_static(route)
        except ApiError as problem:
            self._send_json({"error": problem.message}, problem.status)
        except Exception as problem:                      # pragma: no cover
            self._send_json({"error": str(problem)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        route = posixpath.normpath(unquote(parsed.path))
        try:
            if route == "/api/run":
                payload = self._read_json()
                period = payload.get("period", "")
                result = self.api.run_payroll(
                    period, force=payload.get("force", True)
                )
                self._send_json(result, 201)
            else:
                self._send_json({"error": "Not found"}, 404)
        except ApiError as problem:
            self._send_json({"error": problem.message}, problem.status)
        except Exception as problem:                      # pragma: no cover
            self._send_json({"error": str(problem)}, 500)

    def _handle_api_get(self, route, query):
        def first(name, default=None):
            values = query.get(name)
            return values[0] if values else default

        if route == "/api/overview":
            return self._send_json(self.api.overview())
        if route == "/api/employees":
            return self._send_json(self.api.employees())
        if route == "/api/payslips":
            period = first("period")
            if not period:
                raise ApiError("A period is needed, e.g. ?period=2026-10")
            return self._send_json(self.api.payslips(period))
        if route == "/api/emp201":
            period = first("period")
            if not period:
                raise ApiError("A period is needed, e.g. ?period=2026-10")
            return self._send_json(self.api.emp201(period))
        if route == "/api/deadlines":
            return self._send_json(self.api.deadlines(first("year", "2027")))
        if route == "/api/irp5":
            return self._send_json(self.api.irp5(first("year", "2027")))
        if route == "/api/emp501":
            return self._send_json(self.api.emp501(first("year", "2027")))
        raise ApiError("Not found", 404)

    def _handle_static(self, route):
        if route in ("/", "\\"):
            route = "/index.html"
        # Keep the path inside the web folder.
        target = os.path.normpath(os.path.join(WEB_ROOT, route.lstrip("/")))
        if not target.startswith(WEB_ROOT):
            raise ApiError("Not found", 404)
        self._send_file(target)


def serve(host: str = "127.0.0.1", port: int = 8000, db_path: str = DEFAULT_DB):
    """Start the dashboard."""
    handler = type("BoundHandler", (Handler,), {"api": Api(db_path)})
    httpd = ThreadingHTTPServer((host, port), handler)

    print()
    print("  PAYROLL SUITE - DASHBOARD")
    print("  -------------------------")
    print(f"  Open      http://{host}:{port}")
    print(f"  Database  {db_path}")
    print("  Stop      Ctrl+C")
    print()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.\n")
    finally:
        httpd.server_close()
