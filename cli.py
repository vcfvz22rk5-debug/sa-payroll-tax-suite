"""
cli.py - the part you actually SEE and use.

"cli" means Command Line Interface: the program asks you questions in
the terminal and prints a payslip-style report.

Run it with:
    python3 tax_calculator/cli.py
"""

from config import (
    DEFAULT_TAX_YEAR,
    RA_MAX_PERCENT_OF_SALARY,
    RA_MAX_ANNUAL_AMOUNT,
)
from tax_tables import get_tax_year, marginal_rate, medical_credit
from paye import calculate_annual_tax, calculate_paye_monthly, effective_rate
from report import money as r, line, rule, heading, note
from uif import calculate_uif

MONTHS = 12


def ask_amount(question):
    """Ask for a number, but be friendly about R signs, spaces and commas."""
    raw = input(question)
    cleaned = raw.replace("R", "").replace(",", "").replace(" ", "")
    if cleaned == "":
        return 0.0
    return float(cleaned)


def ask_integer(question):
    while True:
        try:
            return int(input(question).strip())
        except ValueError:
            print("  Please enter a whole number (e.g. 30).")


def allowance_for_retirement(gross_annual, monthly_contribution):
    """
    How much of the pension/RA contribution is allowed as a tax deduction.
    Section 11F: the LOWEST of the actual contribution, 27.5% of salary,
    or R350 000 a year.
    """
    annual_contribution = monthly_contribution * MONTHS
    cap = min(gross_annual * RA_MAX_PERCENT_OF_SALARY, RA_MAX_ANNUAL_AMOUNT)
    return min(annual_contribution, cap), cap


def print_report(data):
    """Print the results in a neat payslip-style layout."""

    heading("SOUTH AFRICAN SALARY & TAX ESTIMATE", data["label"])
    line("Gross salary (monthly) ............", r(data["gross_monthly"]))
    line(f"Annualised gross (x {MONTHS}) ...........", r(data["gross_annual"]))
    if data["ra_annual"] > 0:
        line("Less: retirement/RA deduction .....", r(-data["ra_annual"]))
        if data["ra_annual"] < data["ra_asked_annual"]:
            line("   (capped at 27.5% of salary / R350 000 - s11F)", "")
    rule("-")
    line("TAXABLE INCOME (annual) ...........", r(data["taxable_income"]))
    line("Tax at SARS slab rates ............", r(data["tax_before_rebates"]))
    line(f"Less: {data['rebate_name']} ......", r(-data["rebate"]))
    if data["medical_credit_annual"] > 0:
        line("Less: medical tax credit .........", r(-data["medical_credit_annual"]))
    rule("-")
    line("ANNUAL TAX (PAYE basis) ...........", r(data["annual_tax"]))
    line(f"Monthly PAYE (annual / {MONTHS}) .........", r(data["paye_monthly"]))
    print()
    capped = " (capped)" if data["gross_monthly"] > data["uif_base"] else ""
    line(
        f"UIF employee 1% on {r(data['uif_base'], brackets=False)}{capped}...",
        r(data["uif_employee"]),
    )
    line("UIF employer 1% (business cost) ...", r(data["uif_employer"]))
    rule("-")
    line("MONTHLY DEDUCTIONS", "")
    if data["ra_monthly_allowed"] > 0:
        line("Retirement / RA .....................", r(-data["ra_monthly_allowed"]))
    line("PAYE ................................", r(-data["paye_monthly"]))
    line("UIF employee 1% ....................", r(-data["uif_employee"]))
    rule()
    line("NET MONTHLY PAY ...................", r(data["net_monthly"]))
    line("Total monthly deductions ..........", r(data["total_deductions"]))
    print(
        f"  Effective tax rate: {data['effective'] * 100:.1f}%   "
        f"Marginal rate (top slab): {data['marginal'] * 100:.0f}%"
    )
    rule()
    note("Estimate for study/portfolio use only - not an official SARS")
    note("payscale result. Always verify against sars.gov.za.")
    print()


def main():
    print("\n  SOUTH AFRICAN SALARY & TAX CALCULATOR (PAYE, UIF & net pay)")
    print("  ----------------------------------------------------------")

    gross_monthly = ask_amount("\n  Gross monthly salary (e.g. 25000): ")
    age = ask_integer("  Your age at 28 February of that tax year: ")

    while True:
        choice = input(
            f"  Tax year - 2026 or 2027 [default {DEFAULT_TAX_YEAR}]: "
        ).strip()
        tax_year = choice if choice else DEFAULT_TAX_YEAR
        try:
            table = get_tax_year(tax_year)  # clear error if invalid
            break
        except ValueError as problem:
            print(f"  {problem}")

    ra_monthly = ask_amount(
        "  Monthly pension/RA contribution (0 if none): "
    )

    medical_monthly = ask_amount(
        "  Your own monthly medical scheme contribution (0 if none): "
    )
    medical_dependants = 0
    if medical_monthly > 0:
        medical_dependants = ask_integer(
            "  How many people are on the scheme, including you? "
        )

    gross_annual = gross_monthly * MONTHS
    ra_annual_allowed, ra_cap = allowance_for_retirement(gross_annual, ra_monthly)
    taxable_income = gross_annual - ra_annual_allowed

    # The medical scheme fees tax credit is a rebate against the tax.
    credit_monthly = 0.0
    if medical_monthly > 0 and medical_dependants > 0:
        credit_monthly = medical_credit(
            medical_monthly, medical_dependants, tax_year
        )
    medical_credit_annual = credit_monthly * MONTHS

    age_key = "primary" if age < 65 else ("secondary" if age < 75 else "tertiary")
    rebate_names = {
        "primary": "primary rebate",
        "secondary": "primary + secondary rebate",
        "tertiary": "primary + secondary + tertiary rebate",
    }
    rebate = table["rebates"]["primary"]
    if age >= 65:
        rebate += table["rebates"]["secondary"]
    if age >= 75:
        rebate += table["rebates"]["tertiary"]

    annual_tax = calculate_annual_tax(
        taxable_income, age, tax_year, medical_credit_annual=medical_credit_annual
    )
    paye_monthly = calculate_paye_monthly(annual_tax)
    uif = calculate_uif(gross_monthly)
    ra_monthly_allowed = ra_annual_allowed / MONTHS
    total_deductions = paye_monthly + uif["employee"] + ra_monthly_allowed
    net_monthly = gross_monthly - total_deductions

    # Tax BEFORE rebates (to show the slab tax on the report).
    # Easiest way: apply the SARS table straight to taxable income.
    tax_before_rebates = 0.0
    for bracket in table["brackets"]:
        top = bracket["to"]
        if top is None or taxable_income <= top:
            tax_before_rebates = (
                bracket["base_tax"]
                + bracket["rate"] * (taxable_income - bracket["from"])
            )
            break

    print_report(
        {
            "label": table["label"],
            "gross_monthly": gross_monthly,
            "gross_annual": gross_annual,
            "ra_annual": ra_annual_allowed,
            "ra_asked_annual": ra_monthly * MONTHS,
            "taxable_income": taxable_income,
            "tax_before_rebates": tax_before_rebates,
            "rebate": rebate,
            "rebate_name": rebate_names[age_key],
            "medical_credit_annual": medical_credit_annual,
            "ra_monthly_allowed": ra_monthly_allowed,
            "annual_tax": annual_tax,
            "paye_monthly": paye_monthly,
            "uif_base": uif["base"],
            "uif_employee": uif["employee"],
            "uif_employer": uif["employer"],
            "net_monthly": net_monthly,
            "total_deductions": total_deductions,
            "effective": effective_rate(annual_tax, gross_annual),
            "marginal": marginal_rate(taxable_income, tax_year),
        }
    )


if __name__ == "__main__":
    main()
