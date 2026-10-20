"""
cli.py - the command line application.

A real tool with real subcommands, not a menu:

    payroll-suite init                 create the database and the demo staff
    payroll-suite add-employee         add somebody to the payroll
    payroll-suite list                 who is on the payroll
    payroll-suite payrun --month 2026-10
    payroll-suite emp201 --month 2026-10
    payroll-suite irp5 --year 2027
    payroll-suite emp501 --year 2027
    payroll-suite deadlines --year 2027
    payroll-suite export --period 2026-10 --format csv
    payroll-suite serve                the dashboard on http://localhost:8000

Run `payroll-suite --help` for the full list.
"""

import argparse
import os
import sys
from datetime import date, datetime

from payroll_suite import __version__
from payroll_suite.compliance import (
    deadlines as all_deadlines,
    emp201 as build_emp201,
    emp201_due_date,
    emp501 as build_emp501,
    irp5 as build_irp5,
    upcoming,
)
from payroll_suite.db import DEFAULT_DB, Database
from payroll_suite.engine import calculate_pay_run
from payroll_suite.models import Employee, PayRun
from payroll_suite.reports import (
    heading, line, money, note, print_deadlines, print_emp201,
    print_payroll_run, print_payslip, rule, to_csv, to_json, write_file,
)
from payroll_suite.seed import seed_demo_data

PERIOD_HELP = "the payroll month, e.g. 2026-10"


def parse_period(value: str) -> date:
    """'2026-10' or '2026-10-15' -> a date."""
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%Y-%m", "%Y/%m", "%Y%m"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"'{value}' is not a month. Use the format 2026-10."
    )


def period_string(period: date) -> str:
    return period.strftime("%Y-%m")


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------
def cmd_init(args) -> int:
    db = Database(args.db)
    employees = seed_demo_data(db)
    db.close()
    heading("DATABASE READY", args.db)
    line("Employees created ......................", str(len(employees)))
    note("  Next: payroll-suite payrun --month 2026-10")
    print()
    return 0


def cmd_add_employee(args) -> int:
    db = Database(args.db)
    number = args.number or db.next_employee_number()
    employee = Employee(
        employee_number=number,
        full_name=args.name,
        age=args.age,
        start_date=parse_period(args.start),
        basic_salary=args.salary,
        id_number=args.id_number or "",
        email=args.email or "",
        tax_year=args.tax_year,
        pension_rate=args.pension_rate,
        pension_amount=args.pension_amount,
        medical_members=args.medical_members,
        medical_own=args.medical,
        medical_employer=args.medical_employer,
        commission_earner=args.commission_earner,
        annual_leave_days=args.leave_days,
    )
    db.add_employee(employee)
    db.close()
    heading("EMPLOYEE ADDED", f"{employee.employee_number} · {employee.full_name}")
    line("Gross monthly salary ..................", money(employee.basic_salary))
    line("Started ..............................", employee.start_date.isoformat())
    print()
    return 0


def cmd_list(args) -> int:
    db = Database(args.db)
    employees = db.list_employees(active_only=not args.all)
    db.close()

    heading("EMPLOYEES", f"{len(employees)} on the payroll")
    print(f"  {'NUMBER':<10}{'NAME':<26}{'AGE':>5}{'GROSS':>13}{'FROM':>13}")
    rule()
    for employee in employees:
        print(
            f"  {employee.employee_number:<10}"
            f"{employee.full_name[:25]:<26}"
            f"{employee.age:>5}"
            f"{employee.basic_salary:>13,.2f}"
            f"{employee.start_date.isoformat():>13}"
        )
    rule()
    print()
    return 0


def cmd_payrun(args) -> int:
    db = Database(args.db)
    period = parse_period(args.month)
    period_key = period_string(period)

    employees = db.list_employees()
    if not employees:
        db.close()
        note("  There are no employees yet. Run: payroll-suite init")
        return 1

    # The per-employee extras for this month come from a JSON file if
    # one is given: {"E0001": {"overtime_hours": 12, "bonus": 5000}}
    inputs = {}
    if args.inputs:
        import json
        with open(args.inputs, encoding="utf-8") as handle:
            inputs = json.load(handle)

    payslips = calculate_pay_run(employees, period, inputs)
    paid_ids = {p.employee_id for p in payslips}
    skipped = [e for e in employees if e.id not in paid_ids]

    run = db.get_run(period_key)
    if run and not args.force:
        db.close()
        note(f"  There is already a pay run for {period_key}.")
        note("  Use --force to replace it.")
        return 1
    if run:
        db.delete_run(run)

    run = PayRun(period=period_key, pay_date=period,
                 notes=f"Run of {len(payslips)} employees")
    db.create_run(run)
    for payslip in payslips:
        payslip.run_id = run.id
    db.save_payslips(payslips)

    totals = db.payroll_totals(period_key)
    totals.setdefault("head_count", len(payslips))
    db.close()

    print_payroll_run(payslips, totals)
    if args.show:
        for payslip in payslips:
            print_payslip(payslip)
    if skipped:
        note("  Not paid this month:")
        for employee in skipped:
            reason = "has not started yet" if employee.start_date > period \
                else "has left"
            note(f"    {employee.employee_number} {employee.full_name} ({reason})")
        print()
    note(f"  Saved to the database as run {period_key}.")
    print()
    return 0


def cmd_payslips(args) -> int:
    db = Database(args.db)
    period_key = args.period or period_string(date.today())
    payslips = db.payslips_for_period(period_key)
    if not payslips:
        db.close()
        note(f"  No payslips found for {period_key}.")
        return 1

    if args.employee:
        employee = db.find_employee(args.employee)
        if employee is None:
            db.close()
            note(f"  No employee matches '{args.employee}'.")
            return 1
        payslips = [p for p in payslips if p.employee_id == employee.id]
        if not payslips:
            db.close()
            note(f"  {employee.full_name} has no payslip in {period_key}.")
            return 1
        for payslip in payslips:
            print_payslip(payslip, employee)
    else:
        totals = db.payroll_totals(period_key)
        totals.setdefault("head_count", len(payslips))
        print_payroll_run(payslips, totals)
    db.close()
    return 0


def cmd_emp201(args) -> int:
    db = Database(args.db)
    period_key = args.month
    payslips = db.payslips_for_period(period_key)
    if not payslips:
        db.close()
        note(f"  No payslips found for {period_key}. Run a pay run first.")
        return 1
    summary = build_emp201(payslips, period_key)
    db.close()

    if args.format == "csv":
        print(to_csv([summary]))
    elif args.format == "json":
        print(to_json(summary))
    else:
        print_emp201(summary)
    return 0


def cmd_irp5(args) -> int:
    db = Database(args.db)
    employees = [
        e for e in db.list_employees(active_only=False)
        if e.tax_year == str(args.year)
    ]
    payslips = db.list_payslips()
    certificates = []
    for employee in employees:
        try:
            certificates.append(build_irp5(employee, payslips))
        except ValueError:
            continue
    db.close()

    if not certificates:
        note(f"  No IRP5 certificates could be built for {args.year}.")
        return 1

    if args.format == "json":
        print(to_json(certificates))
    elif args.format == "csv":
        print(to_csv(certificates))
    else:
        for certificate in certificates:
            heading(
                "IRP5 EMPLOYEE TAX CERTIFICATE",
                certificate["certificate_number"],
            )
            line("Employee number .......................", certificate["employee_number"])
            line("Name .................................", certificate["full_name"])
            line("ID number ............................", certificate["id_number"] or "-")
            line("Tax year ..............................", certificate["tax_year"])
            line("Months employed ......................", str(certificate["months_employed"]))
            rule("-")
            line("Remuneration ..........................", money(certificate["remuneration"]))
            line("Retirement fund deduction .............", money(-certificate["pension"]))
            line("Medical scheme deduction ..............", money(-certificate["medical"]))
            line("PAYE deducted .........................", money(certificate["paye"]))
            line("UIF deducted .........................", money(certificate["uif"]))
            line("SDL (employer) ........................", money(certificate["sdl"]))
            line("Net pay ...............................", money(certificate["net_pay"]))
            rule()
            print()
    return 0


def cmd_emp501(args) -> int:
    db = Database(args.db)
    year = str(args.year)
    declarations = []
    for run in db.list_runs():
        if not run.period.startswith(year[:4]):
            continue
        payslips = db.payslips_for_period(run.period)
        if payslips:
            declarations.append(build_emp201(payslips, run.period))

    employees = [
        e for e in db.list_employees(active_only=False) if e.tax_year == year
    ]
    all_payslips = db.list_payslips()
    certificates = []
    for employee in employees:
        try:
            certificates.append(build_irp5(employee, all_payslips))
        except ValueError:
            continue
    db.close()

    if not declarations:
        note(f"  No pay runs found for {year}.")
        return 1

    result = build_emp501(declarations, certificates)

    heading("EMP501 ANNUAL RECONCILIATION", f"Tax year {year}")
    line("EMP201 declarations ....................", str(result["declarations"]))
    line("IRP5 certificates ......................", str(result["certificates"]))
    rule("-")
    print(f"  {'':<26}{'DECLARED':>16}{'CERTIFIED':>16}{'DIFFERENCE':>16}")
    rule("-")
    for key in ("remuneration", "paye", "uif", "sdl"):
        print(
            f"  {key.capitalize():<26}"
            f"{result['declared'][key]:>16,.2f}"
            f"{result['certified'][key]:>16,.2f}"
            f"{result['difference'][key]:>16,.2f}"
        )
    rule()
    if result["in_balance"]:
        note("  IN BALANCE - the declarations agree with the certificates.")
    else:
        note("  NOT IN BALANCE - explain the difference before you submit.")
    print()
    return 0


def cmd_deadlines(args) -> int:
    items = all_deadlines(str(args.year))
    if args.upcoming:
        items = upcoming(str(args.year), days=args.upcoming)
    if args.format == "json":
        print(to_json(items))
    elif args.format == "csv":
        print(to_csv([
            {
                "date": i["date"].isoformat(),
                "name": i["name"],
                "detail": i["detail"],
                "source": i["source"],
            }
            for i in items
        ]))
    else:
        print_deadlines(items)
    return 0


def cmd_export(args) -> int:
    db = Database(args.db)
    period_key = args.period
    payslips = db.payslips_for_period(period_key)
    db.close()

    if not payslips:
        note(f"  No payslips found for {period_key}.")
        return 1

    from payroll_suite.reports import payslips_to_rows
    rows = payslips_to_rows(payslips)
    content = to_csv(rows) if args.format == "csv" else to_json(rows)

    if args.output:
        write_file(args.output, content)
        heading("EXPORTED", args.output)
        line("Rows .................................", str(len(rows)))
        print()
    else:
        print(content)
    return 0


def cmd_serve(args) -> int:
    from payroll_suite.server import serve
    serve(host=args.host, port=args.port, db_path=args.db)
    return 0


# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="payroll-suite",
        description="A small-business payroll and SARS compliance system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  payroll-suite init
  payroll-suite add-employee --name "Thandi Mokoena" --age 34 --salary 32000
  payroll-suite payrun --month 2026-10
  payroll-suite emp201 --month 2026-10
  payroll-suite deadlines --year 2027 --upcoming 30
  payroll-suite serve
""",
    )
    parser.add_argument("--version", action="version", version=f"payroll-suite {__version__}")
    parser.add_argument(
        "--db", default=DEFAULT_DB,
        help="path to the SQLite database (default: %(default)s)",
    )

    sub = parser.add_subparsers(dest="command", metavar="command")

    p = sub.add_parser("init", help="create the database and the demo staff")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add-employee", help="add somebody to the payroll")
    p.add_argument("--name", required=True)
    p.add_argument("--age", type=int, required=True)
    p.add_argument("--salary", type=float, required=True, help="gross monthly salary")
    p.add_argument("--start", default=f"{date.today().year}-03-01", help="start date")
    p.add_argument("--number", help="employee number (default: the next one)")
    p.add_argument("--id-number", dest="id_number")
    p.add_argument("--email")
    p.add_argument("--tax-year", dest="tax_year", default="2027")
    p.add_argument("--pension-rate", dest="pension_rate", type=float, default=0.0,
                   help="percent of the pensionable salary")
    p.add_argument("--pension-amount", dest="pension_amount", type=float, default=0.0)
    p.add_argument("--medical-members", dest="medical_members", type=int, default=1)
    p.add_argument("--medical", type=float, default=0.0,
                   help="the employee's own monthly contribution")
    p.add_argument("--medical-employer", dest="medical_employer", type=float, default=0.0)
    p.add_argument("--commission-earner", dest="commission_earner", action="store_true")
    p.add_argument("--leave-days", dest="leave_days", type=float, default=0.0)
    p.set_defaults(func=cmd_add_employee)

    p = sub.add_parser("list", help="who is on the payroll")
    p.add_argument("--all", action="store_true", help="include leavers")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("payrun", help="run the payroll for a month")
    p.add_argument("--month", required=True, help=PERIOD_HELP)
    p.add_argument("--inputs", help="a JSON file of overtime, bonuses and leave")
    p.add_argument("--show", action="store_true", help="print every payslip")
    p.add_argument("--force", action="store_true", help="replace an existing run")
    p.set_defaults(func=cmd_payrun)

    p = sub.add_parser("payslips", help="the payslips for a month")
    p.add_argument("--period", help=PERIOD_HELP)
    p.add_argument("--employee", help="employee number or name")
    p.set_defaults(func=cmd_payslips)

    p = sub.add_parser("emp201", help="the monthly employer declaration")
    p.add_argument("--month", required=True, help=PERIOD_HELP)
    p.add_argument("--format", choices=["text", "csv", "json"], default="text")
    p.set_defaults(func=cmd_emp201)

    p = sub.add_parser("irp5", help="employee tax certificates for a year")
    p.add_argument("--year", required=True)
    p.add_argument("--format", choices=["text", "csv", "json"], default="text")
    p.set_defaults(func=cmd_irp5)

    p = sub.add_parser("emp501", help="the annual employer reconciliation")
    p.add_argument("--year", required=True)
    p.set_defaults(func=cmd_emp501)

    p = sub.add_parser("deadlines", help="the employer's SARS calendar")
    p.add_argument("--year", default="2027")
    p.add_argument("--upcoming", type=int, metavar="DAYS",
                   help="only the deadlines in the next few days")
    p.add_argument("--format", choices=["text", "csv", "json"], default="text")
    p.set_defaults(func=cmd_deadlines)

    p = sub.add_parser("export", help="export the payslips")
    p.add_argument("--period", required=True, help=PERIOD_HELP)
    p.add_argument("--format", choices=["csv", "json"], default="csv")
    p.add_argument("--output", "-o", help="write to a file instead of the screen")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("serve", help="run the dashboard")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except ValueError as problem:
        note(f"  {problem}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
