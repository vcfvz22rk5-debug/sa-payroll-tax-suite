"""
compliance.py - the employer's SARS obligations.

This is the part a small business actually gets into trouble with: not
the arithmetic, but the forms and the deadlines.

  EMP201  - the monthly declaration: PAYE, UIF and SDL for the month,
            paid over by the 7th of the month that follows.
  EMP501  - the annual employer reconciliation: the EMP201 declarations
            for the year, checked against the IRP5 certificates issued.
  IRP5    - the employee's tax certificate, issued at the end of the
            year of assessment.
  DEADLINES - the employer's calendar for the year.

Sources:
  https://www.sars.gov.za/types-of-tax/pay-as-you-earn/completing-the-monthly-employer-declaration-emp201/
  https://www.sars.gov.za/guide-to-the-employer-reconciliation-process/
"""

import calendar
from datetime import date, timedelta
from typing import Iterable, Optional

from payroll_suite import tax_tables as tt

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# The number of paid days in a month, used to work out a daily rate.
PAID_DAYS_PER_MONTH = 21.75


def _last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def _previous_business_day(day: date) -> date:
    while _is_weekend(day):
        day -= timedelta(days=1)
    return day


def _last_business_day(year: int, month: int) -> date:
    day = _last_day_of_month(year, month)
    return _previous_business_day(date(year, month, day))


# ----------------------------------------------------------------------
# EMP201 - the monthly declaration
# ----------------------------------------------------------------------
def emp201_due_date(period: str) -> date:
    """
    When the EMP201 for a month is due.

    The declaration and the payment are due within 7 days after the end
    of the month. If the 7th falls on a weekend or public holiday, the
    last business day before it is used instead.
    """
    year, month = (int(part) for part in period.split("-")[:2])
    if month == 12:
        year, month = year + 1, 1
    else:
        month += 1
    due = date(year, month, tt.EMP201_DUE_DAY)
    return _previous_business_day(due)


def emp201(payslips: Iterable, period: str) -> dict:
    """
    The monthly employer declaration, in summary form.

    The EMP201 declares the total payment and how it is split between
    PAYE, SDL and UIF.
    """
    payslips = list(payslips)
    if not payslips:
        raise ValueError(f"No payslips were found for {period}.")

    def total(key):
        return round(sum(getattr(p, key) for p in payslips), 2)

    paye = total("paye")
    uif_employee = total("uif_employee")
    uif_employer = total("uif_employer")
    sdl = total("sdl")
    gross = total("gross_remuneration")

    return {
        "period": period,
        "head_count": len(payslips),
        "total_remuneration": gross,
        "paye": paye,
        "uif_employee": uif_employee,
        "uif_employer": uif_employer,
        "uif_total": round(uif_employee + uif_employer, 2),
        "sdl": sdl,
        "total_liability": round(paye + uif_employee + uif_employer + sdl, 2),
        "total_net_paid": total("net_pay"),
        "total_pension": total("pension_deduction"),
        "total_employer_cost": total("employer_cost"),
        "due_date": emp201_due_date(period),
    }


# ----------------------------------------------------------------------
# IRP5 - the employee's tax certificate
# ----------------------------------------------------------------------
def irp5(employee, payslips: Iterable) -> dict:
    """
    An IRP5-style certificate for one employee for one tax year.

    The real IRP5 is a SARS form with dozens of codes. This is the
    part that matters: what was paid, what was deducted, and what the
    tax came to.
    """
    # Match on the employee number, which is always known, and fall back
    # to the database id.
    payslips = [
        p for p in payslips
        if p.employee_number == employee.employee_number
        or (employee.id and p.employee_id == employee.id)
    ]
    if not payslips:
        raise ValueError(
            f"{employee.full_name} has no payslips for this tax year."
        )

    def total(key):
        return round(sum(getattr(p, key) for p in payslips), 2)

    return {
        "employee_number": employee.employee_number,
        "full_name": employee.full_name,
        "id_number": employee.id_number,
        "age": employee.age,
        "tax_year": employee.tax_year,
        "start_date": employee.start_date.isoformat(),
        "end_date": employee.end_date.isoformat() if employee.end_date else "",
        "months_employed": len(payslips),
        "remuneration": total("gross_remuneration"),
        "pension": total("pension_deduction"),
        "medical": total("medical_deduction"),
        "taxable_income": total("taxable_income"),
        "paye": total("paye"),
        "uif": total("uif_employee"),
        "sdl": total("sdl"),
        "net_pay": total("net_pay"),
        "certificate_number": f"IRP5-{employee.employee_number}-{employee.tax_year}",
    }


# ----------------------------------------------------------------------
# EMP501 - the annual reconciliation
# ----------------------------------------------------------------------
def emp501(declarations: Iterable[dict], certificates: Iterable[dict]) -> dict:
    """
    The annual employer reconciliation.

    The point of the EMP501 is to prove that what was declared on the
    EMP201 declarations for the year is the same as what the IRP5
    certificates say was paid to the employees. Any difference has to be
    explained.
    """
    declarations = list(declarations)
    certificates = list(certificates)

    # The EMP501 checks the employee's side of the tax against the
    # certificates. The employer's own UIF is not on an IRP5, so it is
    # left out of the comparison.
    declared = {
        "paye": round(sum(d["paye"] for d in declarations), 2),
        "uif": round(sum(d["uif_employee"] for d in declarations), 2),
        "sdl": round(sum(d["sdl"] for d in declarations), 2),
        "remuneration": round(sum(d["total_remuneration"] for d in declarations), 2),
    }
    certified = {
        "paye": round(sum(c["paye"] for c in certificates), 2),
        "uif": round(sum(c["uif"] for c in certificates), 2),
        "sdl": round(sum(c["sdl"] for c in certificates), 2),
        "remuneration": round(sum(c["remuneration"] for c in certificates), 2),
    }

    difference = {
        key: round(certified[key] - declared[key], 2) for key in declared
    }

    return {
        "declarations": len(declarations),
        "certificates": len(certificates),
        "declared": declared,
        "certified": certified,
        "difference": difference,
        "in_balance": all(abs(v) < 0.01 for v in difference.values()),
    }


# ----------------------------------------------------------------------
# The employer's calendar
# ----------------------------------------------------------------------
def deadlines(tax_year: str = "2027") -> list:
    """
    Every SARS deadline an employer has to meet in a tax year.

    Each entry has a date, a name, what it is for and where the rule
    comes from.
    """
    year = int(tax_year)
    start = year - 1                     # the tax year starts in March
    items = []

    # EMP201 - every month, the 7th of the month that follows.
    for offset in range(12):
        month = (3 + offset - 1) % 12 + 1
        period_year = start if month >= 3 else year
        period = f"{period_year}-{month:02d}"
        items.append({
            "date": emp201_due_date(period),
            "name": "EMP201 monthly declaration",
            "detail": f"PAYE, UIF and SDL for {MONTH_NAMES[month - 1]} "
                      f"{period_year}",
            "period": period,
            "source": "SARS EMP201",
        })

    # VAT201 - every two months, in the month after the period.
    months = [3, 5, 7, 9, 11, 1]
    for index, month in enumerate(months, start=1):
        if month == 1:
            period_start = date(year, 1, 1)
            period_end = date(year, 2, _last_day_of_month(year, 2))
            due_year, due_month = year, 3
        else:
            period_start = date(start, month, 1)
            period_end = date(start, month + 1, _last_day_of_month(start, month + 1))
            due_month = month + 2
            due_year = start
            if due_month > 12:
                due_month -= 12
                due_year += 1
        manual = date(due_year, due_month, tt.VAT_MANUAL_DUE_DAY)
        items.append({
            "date": _previous_business_day(manual),
            "name": f"VAT201 period {index} (manual submission)",
            "detail": f"VAT for {period_start.strftime('%d %b')} to "
                      f"{period_end.strftime('%d %b %Y')}",
            "period": f"P{index}",
            "source": "SARS VAT201",
        })
        items.append({
            "date": _last_business_day(due_year, due_month),
            "name": f"VAT201 period {index} (eFiling submission)",
            "detail": f"VAT for {period_start.strftime('%d %b')} to "
                      f"{period_end.strftime('%d %b %Y')}",
            "period": f"P{index}",
            "source": "SARS VAT201",
        })

    # IRP5 certificates - within 60 days of the end of the year.
    year_end = date(year, 2, _last_day_of_month(year, 2))
    items.append({
        "date": year_end + timedelta(days=60),
        "name": "IRP5 tax certificates",
        "detail": "Employee tax certificates for the year of assessment",
        "period": str(year),
        "source": "SARS Guide for Employers",
    })

    # EMP501 - the annual reconciliation window.
    items.append({
        "date": date(year, 5, 31),
        "name": "EMP501 annual reconciliation",
        "detail": "Reconcile the EMP201 declarations with the IRP5 certificates",
        "period": str(year),
        "source": "SARS Employer Reconciliation",
    })

    # Provisional tax for a natural person (IRP6).
    items.append({
        "date": date(start, 8, 31),
        "name": "Provisional tax (IRP6) - first payment",
        "detail": "For a natural person without an employer",
        "period": str(year),
        "source": "SARS Provisional Tax",
    })
    items.append({
        "date": date(year, 1, 31),
        "name": "Provisional tax (IRP6) - second payment",
        "detail": "For a natural person without an employer",
        "period": str(year),
        "source": "SARS Provisional Tax",
    })

    items.sort(key=lambda item: item["date"])
    return items


def upcoming(tax_year: str = "2027", days: int = 30, today: Optional[date] = None) -> list:
    """The deadlines in the next few days."""
    today = today or date.today()
    limit = today + timedelta(days=days)
    return [d for d in deadlines(tax_year) if today <= d["date"] <= limit]
