"""
payroll.py - the employer's side: payslips, a payroll run, and the
monthly EMP201 declaration.

This is the other half of the story. paye.py works out what ONE employee
owes. This file works out what the EMPLOYER owes:

  * a payslip for every employee (PAYE, UIF, retirement, net pay)
  * the total cost of the payroll to the business (employer UIF + SDL)
  * the EMP201 summary that gets paid over to SARS

Sources:
  EMP201 / SDL  - https://www.sars.gov.za/types-of-tax/pay-as-you-earn/
  SDL           - https://www.sars.gov.za/tax-rates/other-taxes/
"""

import csv
from datetime import date, timedelta

from config import (
    DEFAULT_TAX_YEAR,
    SDL_RATE,
    SDL_ANNUAL_PAYROLL_EXEMPTION,
    EMP201_DUE_DAY,
    RA_MAX_PERCENT_OF_SALARY,
    RA_MAX_ANNUAL_AMOUNT,
)
from paye import calculate_annual_tax
from tax_tables import medical_credit
from uif import calculate_uif

MONTHS = 12


# ----------------------------------------------------------------------
# ALLOWABLE DEDUCTIONS
# ----------------------------------------------------------------------
def allowance_for_retirement(gross_annual, monthly_contribution):
    """
    How much of the pension/RA contribution is allowed as a tax deduction.

    Section 11F: the LOWEST of the actual contribution, 27.5% of salary,
    or R350 000 a year.
    """
    annual_contribution = monthly_contribution * MONTHS
    cap = min(gross_annual * RA_MAX_PERCENT_OF_SALARY, RA_MAX_ANNUAL_AMOUNT)
    return round(min(annual_contribution, cap), 2), round(cap, 2)


# ----------------------------------------------------------------------
# SDL
# ----------------------------------------------------------------------
def calculate_sdl(leviable_amount, annual_payroll):
    """
    The Skills Development Levy for one month.

    SDL is 1% of the leviable amount (remuneration AFTER the allowable
    deductions). It is a BUSINESS COST - it may not be taken off the
    employee's salary.

    Employers whose total annual remuneration is below R500 000 are
    exempt from paying SDL altogether.
    """
    if leviable_amount < 0:
        raise ValueError("The leviable amount cannot be negative.")
    if annual_payroll < 0:
        raise ValueError("The annual payroll cannot be negative.")

    if annual_payroll < SDL_ANNUAL_PAYROLL_EXEMPTION:
        return 0.0
    return round(leviable_amount * SDL_RATE, 2)


# ----------------------------------------------------------------------
# ONE PAYSLIP
# ----------------------------------------------------------------------
def calculate_payslip(employee, tax_year=DEFAULT_TAX_YEAR,
                      annual_payroll=None):
    """
    Work out one employee's payslip for one month.

    employee = {
        "name":               "Thandi Mokoena",
        "gross_monthly":      32000,
        "age":                34,
        "ra_monthly":         1500,   # optional, default 0
        "medical_monthly":    1200,   # optional, default 0
        "medical_dependants": 2,      # optional, default 0
    }

    annual_payroll : the EMPLOYER's total annual remuneration. It
                     decides whether the company pays SDL at all
                     (employers below R500 000 a year are exempt). If
                     you leave it out, the employee's own salary is
                     used - which is the right answer for a one-person
                     business.
    """
    name = employee.get("name", "Unnamed")
    gross_monthly = float(employee.get("gross_monthly", 0) or 0)
    age = int(employee.get("age", 30) or 0)
    ra_monthly = float(employee.get("ra_monthly", 0) or 0)
    medical_monthly = float(employee.get("medical_monthly", 0) or 0)
    medical_dependants = int(employee.get("medical_dependants", 0) or 0)

    if gross_monthly < 0:
        raise ValueError(f"{name}: gross salary cannot be negative.")
    if medical_dependants < 0:
        raise ValueError(f"{name}: the number of dependants cannot be negative.")

    gross_annual = round(gross_monthly * MONTHS, 2)

    # Allowable deduction: the pension/RA contribution
    ra_allowed, ra_cap = allowance_for_retirement(gross_annual, ra_monthly)

    # Taxable income after the allowable deduction
    taxable_income = round(gross_annual - ra_allowed, 2)

    # Medical scheme fees tax credit (a rebate, applied to the tax)
    credit_monthly = medical_credit(
        medical_monthly, medical_dependants, tax_year
    ) if medical_monthly > 0 else 0.0
    credit_annual = round(credit_monthly * MONTHS, 2)

    annual_tax = calculate_annual_tax(
        taxable_income, age, tax_year, medical_credit_annual=credit_annual
    )
    paye_monthly = round(annual_tax / MONTHS, 2)

    uif = calculate_uif(gross_monthly)

    # SDL is 1% of remuneration after the allowable deductions.
    leviable = round(gross_monthly - ra_allowed / MONTHS, 2)
    if annual_payroll is None:
        annual_payroll = gross_annual
    sdl = calculate_sdl(leviable, annual_payroll)

    # A payslip deducts the retirement contribution, the PAYE and the
    # UIF from the gross. What is left is what lands in the bank.
    ra_monthly_allowed = round(ra_allowed / MONTHS, 2)
    employee_deductions = round(
        paye_monthly + uif["employee"] + ra_monthly_allowed, 2
    )
    net_monthly = round(gross_monthly - employee_deductions, 2)

    return {
        "name": name,
        "tax_year": tax_year,
        "gross_monthly": gross_monthly,
        "gross_annual": gross_annual,
        "ra_monthly": ra_monthly,
        "ra_allowed_annual": ra_allowed,
        "ra_cap_annual": ra_cap,
        "ra_capped": ra_allowed < round(ra_monthly * MONTHS, 2),
        "ra_monthly_allowed": ra_monthly_allowed,
        "taxable_income": taxable_income,
        "medical_credit_monthly": round(credit_monthly, 2),
        "medical_credit_annual": credit_annual,
        "annual_tax": round(annual_tax, 2),
        "paye_monthly": paye_monthly,
        "uif_base": uif["base"],
        "uif_employee": uif["employee"],
        "uif_employer": uif["employer"],
        "sdl": sdl,
        "leviable_amount": leviable,
        "total_deductions": employee_deductions,
        "net_monthly": net_monthly,
        "employer_cost": round(uif["employer"] + sdl, 2),
        "effective_rate": (
            annual_tax / gross_annual if gross_annual > 0 else 0.0
        ),
    }


# ----------------------------------------------------------------------
# A PAYROLL RUN
# ----------------------------------------------------------------------
def run_payroll(employees, tax_year=DEFAULT_TAX_YEAR):
    """
    Run a whole payroll and add it up.

    Returns the list of payslips plus the totals the business cares
    about: the total net pay it paid out, the total tax it withheld,
    and the total cost of employing the team.
    """
    # The employer's total annual remuneration decides whether SDL is
    # payable at all, so it is worked out BEFORE the payslips.
    annual_payroll = round(
        sum(float(e.get("gross_monthly", 0) or 0) * MONTHS for e in employees), 2
    )
    payslips = [
        calculate_payslip(e, tax_year, annual_payroll) for e in employees
    ]

    return {
        "tax_year": tax_year,
        "payslips": payslips,
        "head_count": len(payslips),
        "total_gross": round(sum(p["gross_monthly"] for p in payslips), 2),
        "total_paye": round(sum(p["paye_monthly"] for p in payslips), 2),
        "total_uif_employee": round(
            sum(p["uif_employee"] for p in payslips), 2
        ),
        "total_uif_employer": round(
            sum(p["uif_employer"] for p in payslips), 2
        ),
        "total_sdl": round(sum(p["sdl"] for p in payslips), 2),
        "total_net": round(sum(p["net_monthly"] for p in payslips), 2),
        "total_employer_cost": round(
            sum(p["employer_cost"] for p in payslips), 2
        ),
        "annual_payroll": annual_payroll,
    }


# ----------------------------------------------------------------------
# THE EMP201
# ----------------------------------------------------------------------
def emp201_due_date(payroll_month):
    """
    When the EMP201 is due.

    The declaration and the payment are due within 7 days after the end
    of the month the amounts were deducted in - so if the 7th falls on
    a weekend or public holiday, the last business day before it is used.
    """
    year = payroll_month.year
    month = payroll_month.month
    if month == 12:
        year, month = year + 1, 1
    else:
        month += 1

    due = date(year, month, EMP201_DUE_DAY)
    while due.weekday() >= 5:
        due -= timedelta(days=1)
    return due


def emp201_summary(payroll, payroll_month=None):
    """
    The monthly employer declaration, in summary form.

    The EMP201 declares the total payment and how it is split between
    PAYE, SDL and UIF.
    """
    payslips = payroll["payslips"] if isinstance(payroll, dict) else payroll

    paye = round(sum(p["paye_monthly"] for p in payslips), 2)
    uif_employee = round(sum(p["uif_employee"] for p in payslips), 2)
    uif_employer = round(sum(p["uif_employer"] for p in payslips), 2)
    sdl = round(sum(p["sdl"] for p in payslips), 2)

    total = round(paye + uif_employee + uif_employer + sdl, 2)

    summary = {
        "head_count": len(payslips),
        "total_remuneration": round(
            sum(p["gross_monthly"] for p in payslips), 2
        ),
        "paye": paye,
        "uif_employee": uif_employee,
        "uif_employer": uif_employer,
        "uif_total": round(uif_employee + uif_employer, 2),
        "sdl": sdl,
        "total_liability": total,
        "total_net_paid": round(sum(p["net_monthly"] for p in payslips), 2),
    }

    if payroll_month is not None:
        summary["payroll_month"] = payroll_month
        summary["due_date"] = emp201_due_date(payroll_month)

    return summary


# ----------------------------------------------------------------------
# BATCH MODE (CSV)
# ----------------------------------------------------------------------
REQUIRED_CSV_COLUMNS = ("name", "gross_monthly", "age")
OPTIONAL_CSV_COLUMNS = (
    "ra_monthly", "medical_monthly", "medical_dependants",
)


def load_employees(path):
    """
    Read a list of employees from a CSV file.

    The header row must contain at least: name, gross_monthly, age.
    The optional columns are: ra_monthly, medical_monthly and
    medical_dependants.
    """
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("That CSV file is empty.")

        headers = {h.strip().lower() for h in reader.fieldnames if h}
        missing = [c for c in REQUIRED_CSV_COLUMNS if c not in headers]
        if missing:
            raise ValueError(
                "The CSV file is missing these columns: "
                f"{', '.join(missing)}. Expected at least: "
                f"{', '.join(REQUIRED_CSV_COLUMNS)}."
            )

        employees = []
        for line_number, row in enumerate(reader, start=2):
            clean = {
                (k.strip().lower() if k else k): v
                for k, v in row.items() if k
            }
            if not any((v or "").strip() for v in clean.values()):
                continue    # skip blank lines
            try:
                employees.append(_row_to_employee(clean, line_number))
            except ValueError as problem:
                raise ValueError(f"Row {line_number}: {problem}") from problem

    if not employees:
        raise ValueError("No employee rows were found in that CSV file.")
    return employees


def _row_to_employee(row, line_number=0):
    """Turn one CSV row into an employee dictionary."""
    try:
        gross = float(str(row.get("gross_monthly", "0")).replace("R", "")
                      .replace(",", "").replace(" ", "") or 0)
    except ValueError:
        raise ValueError(
            f"'{row.get('gross_monthly')}' is not a valid gross salary."
        ) from None
    try:
        age = int(float(row.get("age", "30") or 30))
    except ValueError:
        raise ValueError(f"'{row.get('age')}' is not a valid age.") from None

    def optional_float(key):
        raw = str(row.get(key, "0") or 0).replace("R", "").replace(",", "")
        raw = raw.replace(" ", "")
        if not raw:
            return 0.0
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"'{row.get(key)}' is not a valid number.") from None

    def optional_int(key):
        raw = str(row.get(key, "0") or 0).replace(" ", "")
        if not raw:
            return 0
        try:
            return int(float(raw))
        except ValueError:
            raise ValueError(f"'{row.get(key)}' is not a valid number.") from None

    return {
        "name": (row.get("name") or f"Employee {line_number}").strip(),
        "gross_monthly": gross,
        "age": age,
        "ra_monthly": optional_float("ra_monthly"),
        "medical_monthly": optional_float("medical_monthly"),
        "medical_dependants": optional_int("medical_dependants"),
    }
