"""
cli_employer.py - the employer-side tool you actually SEE and use.

Where cli.py answers "what is MY take-home pay?", this answers the
questions a business asks:

  1. VAT calculator      - output tax, input tax, what to pay SARS
  2. VAT201 summary      - the period, the numbers, the deadline
  3. VAT registration    - do I have to be registered?
  4. One payslip         - the same engine as cli.py, employer view
  5. Batch payroll       - run a whole team from a CSV file
  6. EMP201 summary      - what to pay over to SARS by the 7th

Run it with:
    python3 cli_employer.py
"""

import os
from datetime import date

from config import DEFAULT_TAX_YEAR, VAT_RATE
from payroll import (
    calculate_payslip,
    run_payroll,
    emp201_summary,
    load_employees,
    REQUIRED_CSV_COLUMNS,
    OPTIONAL_CSV_COLUMNS,
)
from report import money, line, rule, heading, note
from tax_tables import get_tax_year
from vat import (
    calculate_vat,
    vat_periods,
    vat201_summary,
    registration_status,
    vat_category,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_CSV = os.path.join(HERE, "data", "employees.csv")


# ----------------------------------------------------------------------
# INPUT HELPERS
# ----------------------------------------------------------------------
def ask_amount(question, default=None):
    """Ask for a number, but be friendly about R signs, spaces and commas."""
    raw = input(question).strip()
    if raw == "" and default is not None:
        return float(default)
    cleaned = raw.replace("R", "").replace(",", "").replace(" ", "")
    if cleaned == "":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        print("  Please enter a number, for example 25000.")
        return ask_amount(question, default)


def ask_integer(question, default=None):
    raw = input(question).strip()
    if raw == "" and default is not None:
        return int(default)
    try:
        return int(float(raw))
    except ValueError:
        print("  Please enter a whole number (e.g. 30).")
        return ask_integer(question, default)


def ask_choice(question, options, default=None):
    """Ask the user to pick one of a numbered list of options."""
    for number, (key, description) in enumerate(options, start=1):
        print(f"    {number}. {description}")
    while True:
        raw = input(question).strip()
        if raw == "" and default is not None:
            return default
        try:
            choice = int(raw)
        except ValueError:
            print("  Please enter a number from the list.")
            continue
        if 1 <= choice <= len(options):
            return options[choice - 1][0]
        print("  That number is not on the list.")


# ----------------------------------------------------------------------
# 1. VAT CALCULATOR
# ----------------------------------------------------------------------
def do_vat_calculator():
    print("\n  VAT CALCULATOR")
    print("  -------------")
    print(f"  Standard rate: {VAT_RATE * 100:.0f}%")

    sales = ask_amount("\n  Value of your sales for the period (no VAT): ")
    purchases = ask_amount("  Value of your purchases you can claim (no VAT): ")

    result = calculate_vat(sales, purchases)

    heading(
        "VAT SUMMARY",
        f"{result['taxable_supplies']:,.2f} of supplies | "
        f"{result['taxable_purchases']:,.2f} of purchases",
    )
    line("Sales (taxable supplies) .............", money(result["taxable_supplies"]))
    line(f"Output VAT @ {result['vat_rate'] * 100:.0f}% ................", money(result["output_tax"]))
    line("Purchases (taxable inputs) ...........", money(result["taxable_purchases"]))
    line(f"Input VAT @ {result['vat_rate'] * 100:.0f}% .................", money(result["input_tax"]))
    rule("-")
    if result["is_refund"]:
        line("NET VAT (refund due to you) ...........", money(result["amount_claimable"]))
        print("  You overpaid VAT - claim it back from SARS.")
    else:
        line("NET VAT PAYABLE TO SARS ..............", money(result["amount_payable"]))
        print("  Include this amount on your VAT201 return.")
    rule()
    print()


# ----------------------------------------------------------------------
# 2. VAT201 SUMMARY
# ----------------------------------------------------------------------
def do_vat201():
    print("\n  VAT201 PERIOD SUMMARY")
    print("  --------------------")
    tax_year = ask_choice(
        "  Which tax year? ",
        [("2026", "2026 tax year (1 Mar 2025 - 28 Feb 2026)"),
         ("2027", "2027 tax year (1 Mar 2026 - 28 Feb 2027)")],
        default=DEFAULT_TAX_YEAR,
    )
    periods = vat_periods(tax_year)
    print()
    for period in periods:
        print(f"    {period['period']}. {period['label']}  -> due {period['due_month']}")

    number = ask_integer("\n  Which period number? ", default=1)
    output_tax = ask_amount("  Output tax for the period (R): ")
    input_tax = ask_amount("  Input tax for the period (R): ")

    summary = vat201_summary(tax_year, number, output_tax, input_tax)
    period = summary["period"]

    heading(
        f"VAT201 SUMMARY - {period['period']}",
        f"{period['label']} | {summary['status']}",
    )
    line("Output tax (supplies) ..................", money(summary["output_tax"]))
    line("Less: input tax (purchases) ............", money(-summary["input_tax"]))
    rule("-")
    if summary["is_refund"]:
        line("AMOUNT TO CLAIM BACK ...................", money(summary["amount_claimable"]))
    else:
        line("AMOUNT PAYABLE TO SARS ................", money(summary["amount_payable"]))
    rule()
    line("Period ends ............................", period["end"].strftime("%d %B %Y"))
    line("Manual return due by ...................", period["due_manual"].strftime("%d %B %Y"))
    line("eFiling return due by ..................", period["due_efiling"].strftime("%d %B %Y"))
    rule()
    note("Verify every figure against SARS before you file.")
    print()


# ----------------------------------------------------------------------
# 3. REGISTRATION CHECK
# ----------------------------------------------------------------------
def do_registration():
    print("\n  VAT REGISTRATION CHECK")
    print("  ----------------------")
    supplies = ask_amount("\n  Your total taxable supplies for 12 months (R): ")
    status = registration_status(supplies)
    category = vat_category(supplies)

    heading("VAT REGISTRATION", f"Taxable supplies: R{supplies:,.0f}")
    line("Status .................................", status["status"])
    line("VAT period category ....................", category)
    rule()
    print(f"  {status['detail']}")
    rule()
    print()


# ----------------------------------------------------------------------
# 4. ONE PAYSLIP
# ----------------------------------------------------------------------
def do_payslip():
    print("\n  ONE PAYSLIP (employer view)")
    print("  ----------------------------")
    name = input("  Employee name: ").strip() or "Unnamed"
    gross = ask_amount("  Gross monthly salary (R): ")
    age = ask_integer("  Age at 28 February: ", default=30)
    tax_year = ask_choice(
        "  Tax year? ",
        [("2026", "2026"), ("2027", "2027")],
        default=DEFAULT_TAX_YEAR,
    )
    ra = ask_amount("  Monthly pension/RA contribution (0 if none): ")
    medical = ask_amount("  Your own monthly medical scheme contribution (0 if none): ")
    dependants = 0
    if medical > 0:
        dependants = ask_integer("  How many people are on the scheme (incl. you)? ", default=1)

    payslip = calculate_payslip({
        "name": name,
        "gross_monthly": gross,
        "age": age,
        "ra_monthly": ra,
        "medical_monthly": medical,
        "medical_dependants": dependants,
    }, tax_year)

    heading(
        "PAYSLIP",
        f"{payslip['name']} | {get_tax_year(tax_year)['label']}",
    )
    line("Gross salary (monthly) ................", money(payslip["gross_monthly"]))
    if payslip["ra_allowed_annual"] > 0:
        line("Less: retirement/RA deduction .........", money(-payslip["ra_allowed_annual"]))
        if payslip["ra_capped"]:
            line("   (capped at 27.5% / R350 000 - s11F)", "")
    rule("-")
    line("Taxable income (annual) ...............", money(payslip["taxable_income"]))
    line("Annual tax .............................", money(payslip["annual_tax"]))
    line("Monthly PAYE ...........................", money(payslip["paye_monthly"]))
    if payslip["medical_credit_annual"] > 0:
        line("Medical tax credit (per year) .........", money(payslip["medical_credit_annual"]))
    rule()
    line("UIF employee (1%) ......................", money(payslip["uif_employee"]))
    line("UIF employer (1% - business cost) ......", money(payslip["uif_employer"]))
    line("SDL (1% of leviable - business cost) ...", money(payslip["sdl"]))
    rule("-")
    line("MONTHLY DEDUCTIONS", "")
    if payslip["ra_monthly_allowed"] > 0:
        line("Retirement / RA .......................", money(-payslip["ra_monthly_allowed"]))
    line("PAYE ..................................", money(-payslip["paye_monthly"]))
    line("UIF employee 1% ........................", money(-payslip["uif_employee"]))
    rule()
    line("NET MONTHLY PAY ........................", money(payslip["net_monthly"]))
    line("Total deductions (employee) ............", money(payslip["total_deductions"]))
    print(
        f"  Effective tax rate: {payslip['effective_rate'] * 100:.1f}%"
        f"   Employer cost this month: {money(payslip['employer_cost'])}"
    )
    rule()
    print()


# ----------------------------------------------------------------------
# 5. BATCH PAYROLL
# ----------------------------------------------------------------------
def do_batch():
    print("\n  BATCH PAYROLL (from a CSV file)")
    print("  --------------------------------")
    print(f"  Required columns : {', '.join(REQUIRED_CSV_COLUMNS)}")
    print(f"  Optional columns : {', '.join(OPTIONAL_CSV_COLUMNS)}")
    print(f"  Demo file        : {DEMO_CSV}")
    path = input("\n  CSV file path (blank for the demo file): ").strip()
    if not path:
        path = DEMO_CSV
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(HERE, path)

    try:
        employees = load_employees(path)
    except (OSError, ValueError) as problem:
        print(f"  Could not read that file: {problem}")
        return

    tax_year = ask_choice(
        "  Tax year? ",
        [("2026", "2026"), ("2027", "2027")],
        default=DEFAULT_TAX_YEAR,
    )

    payroll = run_payroll(employees, tax_year)

    heading(
        "PAYROLL RUN",
        f"{payroll['head_count']} employees | {get_tax_year(tax_year)['label']}",
    )
    print(f"  {'NAME':<20}{'GROSS':>13}{'PAYE':>12}{'UIF':>10}{'SDL':>10}{'NET':>13}")
    rule()
    for payslip in payroll["payslips"]:
        name = payslip["name"][:19]
        print(
            f"  {name:<20}"
            f"{payslip['gross_monthly']:>13,.2f}"
            f"{payslip['paye_monthly']:>12,.2f}"
            f"{payslip['uif_employee']:>10,.2f}"
            f"{payslip['sdl']:>10,.2f}"
            f"{payslip['net_monthly']:>13,.2f}"
        )
    rule()
    line("Total gross ............................", money(payroll["total_gross"]))
    line("Total PAYE withheld ....................", money(payroll["total_paye"]))
    line("Total UIF (employee) ...................", money(payroll["total_uif_employee"]))
    line("Total UIF (employer) ...................", money(payroll["total_uif_employer"]))
    line("Total SDL (employer cost) ..............", money(payroll["total_sdl"]))
    line("Total NET paid to employees ............", money(payroll["total_net"]))
    rule()
    print()


# ----------------------------------------------------------------------
# 6. EMP201 SUMMARY
# ----------------------------------------------------------------------
def do_emp201():
    print("\n  EMP201 MONTHLY DECLARATION SUMMARY")
    print("  -----------------------------------")
    path = input("  CSV file path (blank for the demo file): ").strip() or DEMO_CSV
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(HERE, path)

    try:
        employees = load_employees(path)
    except (OSError, ValueError) as problem:
        print(f"  Could not read that file: {problem}")
        return

    tax_year = ask_choice(
        "  Tax year? ",
        [("2026", "2026"), ("2027", "2027")],
        default=DEFAULT_TAX_YEAR,
    )
    payroll = run_payroll(employees, tax_year)

    year = ask_integer("  Payroll month - year (e.g. 2026): ", default=2026)
    month = ask_integer("  Payroll month - number (1-12): ", default=10)

    summary = emp201_summary(payroll, date(year, month, 1))

    heading(
        "EMP201 SUMMARY",
        f"Payroll month: {date(year, month, 1).strftime('%B %Y')} | "
        f"{summary['head_count']} employees",
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


# ----------------------------------------------------------------------
# THE MENU
# ----------------------------------------------------------------------
MENU = [
    ("vat", "VAT calculator - output tax, input tax, net VAT"),
    ("vat201", "VAT201 period summary - the numbers and the deadline"),
    ("reg", "VAT registration check - must I register?"),
    ("payslip", "One payslip - the employer view"),
    ("batch", "Batch payroll - run a whole team from a CSV"),
    ("emp201", "EMP201 summary - what to pay SARS by the 7th"),
    ("quit", "Quit"),
]

ACTIONS = {
    "vat": do_vat_calculator,
    "vat201": do_vat201,
    "reg": do_registration,
    "payslip": do_payslip,
    "batch": do_batch,
    "emp201": do_emp201,
}


def main():
    print("\n  SOUTH AFRICAN VAT 201 & PAYROLL SUITE")
    print("  -------------------------------------")
    print("  The employer side of tax: VAT, SDL, UIF and the EMP201.")

    while True:
        print("\n  What would you like to do?")
        for number, (_, description) in enumerate(MENU, start=1):
            print(f"    {number}. {description}")
        try:
            choice = input("  Choose (1-7): ").strip()
        except EOFError:
            print("\n  Goodbye.\n")
            return

        try:
            key = MENU[int(choice) - 1][0]
        except (ValueError, IndexError):
            print("  Please enter a number from 1 to 7.")
            continue

        if key == "quit":
            print("\n  Goodbye.\n")
            return

        try:
            ACTIONS[key]()
        except (ValueError, OSError) as problem:
            print(f"  Something went wrong: {problem}")
        except EOFError:
            # Ctrl-D or a piped input that ran out.
            print("\n  Goodbye.\n")
            return


if __name__ == "__main__":
    main()
