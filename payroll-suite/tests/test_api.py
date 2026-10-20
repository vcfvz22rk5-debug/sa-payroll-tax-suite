"""
tests/test_api.py - the JSON API behind the dashboard.

The server is started on a random port, the endpoints are called with
the standard library's urllib, and the answers are checked.

Run it with:
    python3 tests/test_api.py
"""

import json
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from datetime import date
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from payroll_suite.db import Database        # noqa: E402
from payroll_suite.seed import seed_demo_data  # noqa: E402
from payroll_suite.server import Api, Handler  # noqa: E402

CHECKS = 0


def same(actual, expected, message):
    global CHECKS
    CHECKS += 1
    assert actual == expected, (
        f"FAILED: {message}\n  expected {expected!r}, got {actual!r}"
    )
    print(f"  ok - {message}")


def close(actual, expected, message, tolerance=0.01):
    global CHECKS
    CHECKS += 1
    assert abs(actual - expected) <= tolerance, (
        f"FAILED: {message}\n  expected {expected:,.2f}, got {actual:,.2f}"
    )
    print(f"  ok - {message}")


def get(base, path):
    with urllib.request.urlopen(f"{base}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post(base, path, payload):
    request = urllib.request.Request(
        f"{base}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    global CHECKS
    print("\nRunning tests...\n")

    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    os.unlink(path)

    db = Database(path)
    seed_demo_data(db)
    db.close()

    handler = type("BoundHandler", (Handler,), {
        "api": Api(path),
        "log_message": lambda self, fmt, *args: None,   # keep the output clean
    })
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        # --- the overview ------------------------------------------------
        overview = get(base, "/api/overview")
        same(overview["head_count"], 6, "The overview counts the team")
        same(overview["tax_year"], "2027", "The overview knows the tax year")
        same(isinstance(overview["deadlines"], list), True,
             "The overview has the deadlines")

        # --- the employees ------------------------------------------------
        employees = get(base, "/api/employees")
        same(len(employees), 6, "The employee list has everybody")
        same(employees[0]["employee_number"], "E0003",
             "The employees are sorted by name")
        same(employees[0]["full_name"], "Fatima Adams", "The first one is Fatima")

        # --- running a payroll -------------------------------------------
        result = post(base, "/api/run", {"period": "2026-10", "force": True})
        same(result["period"], "2026-10", "The run is for October")
        same(result["head_count"], 5, "Sipho has not started yet, so five are paid")
        close(result["totals"]["total_paye"], 45_613, "The PAYE total is right")

        # --- the payslips -------------------------------------------------
        payslips = get(base, "/api/payslips?period=2026-10")
        same(len(payslips), 5, "There are five payslips for October")
        same("paye" in payslips[0], True, "A payslip has the PAYE on it")

        # --- the EMP201 ----------------------------------------------------
        summary = get(base, "/api/emp201?period=2026-10")
        close(summary["total_liability"], 49_661.46, "The EMP201 liability is right")
        same(summary["due_date"], "2026-11-06",
             "The EMP201 is due on 6 November (the 7th is a Saturday)")

        # --- a period with no payroll --------------------------------------
        same(get(base, "/api/payslips?period=2099-01"), [],
             "A period with no payslips comes back empty")
        try:
            get(base, "/api/emp201?period=2099-01")
            same(True, False, "An EMP201 for a period with no payslips is an error")
        except urllib.error.HTTPError as error:
            same(error.code, 400, "An EMP201 with no payslips is a 400")

        # --- the deadlines --------------------------------------------------
        deadlines = get(base, "/api/deadlines?year=2027")
        same(len(deadlines) > 25, True, "The calendar has a full year")
        same("date" in deadlines[0], True, "A deadline has a date")

        # --- a bad route -----------------------------------------------------
        try:
            get(base, "/api/nonsense")
            same(True, False, "An unknown route is an error")
        except urllib.error.HTTPError as error:
            same(error.code, 404, "An unknown route is a 404")

        # --- the overview picks up the new run --------------------------------
        overview = get(base, "/api/overview")
        same(overview["latest_period"], "2026-10", "The latest run is October")
        same(len(overview["trend"]), 1, "The trend has one point")
        close(overview["trend"][0]["gross"], 248_500, "The trend gross is right")

        # --- the IRP5 certificates --------------------------------------------
        post(base, "/api/run", {"period": "2026-11", "force": True})
        certificates = get(base, "/api/irp5?year=2027")
        same(len(certificates) >= 1, True, "There are IRP5 certificates")

    finally:
        server.shutdown()
        server.server_close()
        os.unlink(path)

    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
