"""
reports.py - turning the numbers into something you can read or send.

Console reports for the terminal, and CSV or JSON for the things that
have to leave the building: a declaration that gets uploaded, a
certificate that gets posted, a spreadsheet that gets emailed.
"""

import csv
import io
import json
from datetime import date, datetime
from typing import Iterable, Sequence

WIDTH = 74


def money(amount, brackets: bool = True) -> str:
    """Format a number as Rand: R 4,681.00, or (R17,820.00) if negative."""
    if brackets and amount < 0:
        return f"(R{-amount:,.2f})"
    return f"R {amount:,.2f}"


def line(label: str, amount: str = "") -> None:
    """One row: label on the left, money in a fixed column on the right."""
    print(f"  {label:<46}{amount:>26}")


def rule(char: str = "=") -> None:
    print(char * WIDTH)


def heading(title: str, subtitle: str = "") -> None:
    print()
    rule()
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    rule()


def note(text: str) -> None:
    print(f"  {text}")


# ----------------------------------------------------------------------
# Console reports
# ----------------------------------------------------------------------
def print_payslip(payslip, employee=None) -> None:
    """A single payslip, laid out like a real one."""
    heading("PAYSLIP", f"{payslip.employee_name} · {payslip.period}")
    if payslip.months_worked != 12:
        note(f"  (worked {payslip.months_worked} months of the tax year)")

    line("Basic salary ..........................", money(payslip.basic_salary))
    if payslip.overtime:
        line("Overtime ..............................", money(payslip.overtime))
    if payslip.bonus:
        line("Bonus .................................", money(payslip.bonus))
    if payslip.commission:
        line("Commission ............................", money(payslip.commission))
    if payslip.fringe_benefit:
        line("Fringe benefit ........................", money(payslip.fringe_benefit))
    if payslip.leave_pay:
        line("Leave pay .............................", money(payslip.leave_pay))
    if payslip.other_allowance:
        line("Other allowance ......................", money(payslip.other_allowance))
    rule("-")
    line("GROSS REMUNERATION .....................", money(payslip.gross_remuneration))
    rule("-")

    if payslip.pension_deduction:
        line("Retirement fund .......................", money(-payslip.pension_deduction))
    if payslip.medical_deduction:
        line("Medical scheme ........................", money(-payslip.medical_deduction))
    rule("-")
    line("Annualised remuneration ................", money(payslip.gross_annualised))
    line("Taxable income (annual) ...............", money(payslip.taxable_income))
    line("PAYE (rounded to the rand) ............", money(payslip.paye))
    line("UIF employee 1% .......................", money(payslip.uif_employee))
    rule()
    line("TOTAL DEDUCTIONS ......................", money(payslip.total_deductions))
    line("NET PAY ...............................", money(payslip.net_pay))
    rule()
    line("UIF employer 1% (business cost) .......", money(payslip.uif_employer))
    line("SDL (business cost) ...................", money(payslip.sdl))
    line("TOTAL EMPLOYER COST ..................", money(payslip.employer_cost))
    if employee is not None and employee.medical_employer:
        line("Medical contribution (business cost) ..", money(employee.medical_employer))
    rule()
    print(
        f"  Effective tax rate: {payslip.effective_rate * 100:.1f}%   "
        f"Marginal rate: {payslip.marginal_rate * 100:.0f}%"
    )
    if payslip.notes:
        note(f"  {payslip.notes}")
    print()


def print_payroll_run(payslips: Sequence, totals: dict) -> None:
    """The summary of a whole payroll run."""
    heading("PAYROLL RUN", f"{totals.get('head_count', len(payslips))} employees")
    print(f"  {'EMPLOYEE':<20}{'GROSS':>12}{'PAYE':>12}{'UIF':>9}{'SDL':>9}{'NET':>13}")
    rule()
    for payslip in payslips:
        name = payslip.employee_name[:19]
        print(
            f"  {name:<20}"
            f"{payslip.gross_remuneration:>12,.2f}"
            f"{payslip.paye:>12,.2f}"
            f"{payslip.uif_employee:>9,.2f}"
            f"{payslip.sdl:>9,.2f}"
            f"{payslip.net_pay:>13,.2f}"
        )
    rule()
    line("Total gross ............................", money(totals.get("total_gross", 0)))
    line("Total PAYE withheld ....................", money(totals.get("total_paye", 0)))
    line("Total UIF (employee) ...................", money(totals.get("total_uif_employee", 0)))
    line("Total UIF (employer) ...................", money(totals.get("total_uif_employer", 0)))
    line("Total SDL (employer cost) ..............", money(totals.get("total_sdl", 0)))
    line("Total NET paid to employees ............", money(totals.get("total_net", 0)))
    rule()
    print()


def print_emp201(summary: dict) -> None:
    heading(
        "EMP201 MONTHLY DECLARATION",
        f"Payroll month: {summary['period']} · {summary['head_count']} employees",
    )
    line("Total remuneration .....................", money(summary["total_remuneration"]))
    rule("-")
    line("PAYE ...................................", money(summary["paye"]))
    line("UIF (employee + employer) ..............", money(summary["uif_total"]))
    line("SDL ....................................", money(summary["sdl"]))
    rule("-")
    line("TOTAL TO PAY SARS ......................", money(summary["total_liability"]))
    line("Due by .................................", summary["due_date"].strftime("%d %B %Y"))
    rule()
    note("If the 7th is a weekend or public holiday, pay the last business day before.")
    print()


def print_deadlines(items: Iterable) -> None:
    heading("SARS DEADLINES", "The employer's calendar")
    for item in items:
        days = (item["date"] - date.today()).days
        when = item["date"].strftime("%d %b %Y")
        if days == 0:
            countdown = "  <- TODAY"
        elif days == 1:
            countdown = "  <- tomorrow"
        elif days > 1:
            countdown = f"  (in {days} days)"
        else:
            countdown = ""
        print(f"  {when}  {item['name']}{countdown}")
        print(f"             {item['detail']}")
    rule()
    print()


# ----------------------------------------------------------------------
# Exports
# ----------------------------------------------------------------------
PAYSLIP_COLUMNS = [
    ("employee_number", "Employee number"),
    ("employee_name", "Employee"),
    ("period", "Period"),
    ("basic_salary", "Basic"),
    ("overtime", "Overtime"),
    ("bonus", "Bonus"),
    ("commission", "Commission"),
    ("fringe_benefit", "Fringe benefit"),
    ("leave_pay", "Leave pay"),
    ("other_allowance", "Other"),
    ("gross_remuneration", "Gross remuneration"),
    ("gross_annualised", "Annualised remuneration"),
    ("pension_deduction", "Retirement fund"),
    ("medical_deduction", "Medical"),
    ("taxable_income", "Taxable income"),
    ("annual_tax", "Annual tax"),
    ("paye", "PAYE"),
    ("uif_employee", "UIF employee"),
    ("uif_employer", "UIF employer"),
    ("sdl", "SDL"),
    ("total_deductions", "Total deductions"),
    ("net_pay", "Net pay"),
    ("employer_cost", "Employer cost"),
    ("effective_rate", "Effective rate"),
    ("marginal_rate", "Marginal rate"),
    ("months_worked", "Months worked"),
]


def payslips_to_rows(payslips: Iterable) -> list:
    """Turn payslips into plain dictionaries, ready for CSV or JSON."""
    rows = []
    for payslip in payslips:
        row = {}
        for key, _ in PAYSLIP_COLUMNS:
            row[key] = getattr(payslip, key)
        rows.append(row)
    return rows


def to_csv(rows: Sequence[dict], columns=None) -> str:
    """Render rows as CSV text."""
    if not rows:
        return ""
    if columns is None:
        columns = list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def to_json(data) -> str:
    """Render data as pretty JSON, with the dates written properly."""
    return json.dumps(data, indent=2, default=_json_default, sort_keys=False)


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path
