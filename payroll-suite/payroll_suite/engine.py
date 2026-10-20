"""
engine.py - the payroll calculation engine.

This is where the money is worked out. It is deliberately kept free of
any database or printing so it can be tested on its own.

THE INTERESTING PART: the annualised method.

Because SARS structures its tax brackets around a YEAR of income, an
employer cannot tax a month's pay on its own. The month's taxable
income is annualised, the tax is worked out on that annual figure, and
it is then divided by 12 to get the month's deduction:

    1. taxable income for the month = gross remuneration - s11F pension
    2. annualised taxable income  = that x 12
    3. tax on the annualised figure, using the slab rates
    4. less the rebates for the employee's age
    5. less the medical scheme fees tax credit
    6. monthly PAYE = that annual tax / 12, rounded to the nearest rand

It is called annualising because it smooths the tax out: a bonus in
December does not push the employee into a higher bracket for the whole
year, and a month with no overtime does not drop them into a lower one.

The consequence worth knowing about: an employee who joins in November
is taxed as if they were going to earn twelve months' salary, so the
employer over-deducts for them. That difference is picked up at the end
of the year by `reconcile_tax_year()`, which is the same "tax on a
period basis" adjustment a real payroll makes on the last payslip.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from payroll_suite.models import Employee, Payslip
from payroll_suite import tax_tables as tt

# -- the things an employer can pay in a month ----------------------------
DEFAULT_INPUTS = {
    "overtime_hours": 0.0,
    "overtime_multiplier": tt.OVERTIME_MULTIPLIER,
    "sunday_hours": 0.0,
    "public_holiday_hours": 0.0,
    "bonus": 0.0,
    "commission": 0.0,
    "fringe_benefit": 0.0,
    "leave_pay": 0.0,
    "unpaid_leave_days": 0.0,
    "other_allowance": 0.0,
    "notes": "",
}

# How many days of unpaid leave are allowed before a payslip is refused.
MAX_UNPAID_LEAVE_DAYS = 31


def _round2(value: float) -> float:
    return round(value + 1e-9, 2)


def _round_to_rand(value: float) -> float:
    """
    SARS rounds the monthly PAYE deduction to the nearest rand.

    It is a commercial rounding (half a rand goes up), not Python's
    default banker's rounding, so 24 170.50 becomes R24 171.
    """
    return float(
        Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )


def months_worked_in_year(employee: Employee, period: date) -> int:
    """
    How many months of the tax year has this employee worked by now?

    For somebody who joined in November that is 1 in November, 2 in
    December and 4 by the end of February. For a leaver it is the
    number of months up to their last day.
    """
    tax_year = int(employee.tax_year)
    year_start = date(tax_year - 1, 3, 1)     # 1 March of the year before
    year_end = date(tax_year, 2, 28)         # the end of February

    start = employee.start_date
    end = employee.end_date

    if start > year_end:
        return 0                              # has not started yet
    if end and end < year_start:
        return 0                              # left before this tax year

    # The first month of the tax year they were on the payroll.
    first_index = 1 if start <= year_start else tt.tax_month_index(start.month)

    # The last one, if they have left.
    last_index = 12
    if end and year_start < end <= year_end:
        last_index = tt.tax_month_index(end.month)

    current_index = tt.tax_month_index(period.month)
    months = min(last_index, current_index) - first_index + 1
    return max(0, min(12, months))


def calculate_overtime(basic_monthly: float, inputs: dict) -> float:
    """
    Overtime pay, the way South African law works.

    * ordinary overtime: 1.5x for the first 45 hours in a month, 2x
      for anything beyond that
    * Sunday hours: 2x
    * public holiday hours: 2x
    """
    hours = float(inputs.get("overtime_hours") or 0)
    sunday = float(inputs.get("sunday_hours") or 0)
    holiday = float(inputs.get("public_holiday_hours") or 0)
    if hours < 0 or sunday < 0 or holiday < 0:
        raise ValueError("Overtime hours cannot be negative.")
    if basic_monthly <= 0:
        return 0.0

    hourly_rate = basic_monthly / tt.MONTHLY_HOURS
    multiplier = float(inputs.get("overtime_multiplier") or tt.OVERTIME_MULTIPLIER)

    first = min(hours, tt.OVERTIME_FIRST_THRESHOLD)
    beyond = max(0.0, hours - tt.OVERTIME_FIRST_THRESHOLD)

    total = (
        first * hourly_rate * multiplier
        + beyond * hourly_rate * tt.OVERTIME_AFTER_THRESHOLD_MULTIPLIER
        + sunday * hourly_rate * tt.SUNDAY_MULTIPLIER
        + holiday * hourly_rate * tt.PUBLIC_HOLIDAY_MULTIPLIER
    )
    return _round2(total)


def calculate_pension(employee: Employee, remuneration: float) -> float:
    """
    The retirement fund deduction for the month, capped by section 11F.

    The limit is the lowest of:
      * the actual contribution
      * 27.5% of the remuneration for the month
      * R350 000 for the year, which is R29 166.67 a month
    """
    contribution = employee.basic_salary * (employee.pension_rate / 100.0) \
        + employee.pension_amount
    if contribution <= 0:
        return 0.0

    monthly_cap = min(remuneration * tt.RA_MAX_PERCENT, tt.RA_MAX_ANNUAL / 12)
    return _round2(min(contribution, monthly_cap))


def annualised_tax(
    monthly_taxable: float,
    age: int,
    tax_year: str,
    medical_credit_annual: float = 0.0,
) -> dict:
    """
    The SARS annualised calculation, step by step.

    Returns the annualised taxable income, the tax on it, and the tax
    for the month.
    """
    if monthly_taxable < 0:
        raise ValueError("Taxable income cannot be negative.")

    annualised = monthly_taxable * 12
    tax_before_rebates = tt.slab_tax(annualised, tax_year)
    rebate = tt.rebate_for(age, tax_year)
    annual_tax = max(0.0, tax_before_rebates - rebate - medical_credit_annual)

    return {
        "annualised_taxable": _round2(annualised),
        "tax_before_rebates": _round2(tax_before_rebates),
        "rebate": _round2(rebate),
        "medical_credit_annual": _round2(medical_credit_annual),
        "annual_tax": _round2(annual_tax),
        "monthly_tax": _round2(annual_tax / 12),
        "marginal_rate": tt.marginal_rate(annualised, tax_year),
    }


def reconcile_tax_year(employee: Employee, payslips: list) -> dict:
    """
    The year-end "tax on a period basis" reconciliation.

    The annualised method charges an employee as if they were going to
    earn a full year's salary. If they joined late, or left early, or
    had an unusual bonus, that is not what actually happened - and the
    employer has to work out the difference and adjust.

    This is the calculation that sits behind a negative PAYE on the
    last payslip of the year, and behind the EMP501 reconciliation.
    """
    if not payslips:
        raise ValueError("There are no payslips to reconcile.")

    gross = round(sum(p.gross_remuneration for p in payslips), 2)
    pension = round(sum(p.pension_deduction for p in payslips), 2)
    deducted = round(sum(p.paye for p in payslips), 2)

    taxable = round(max(0.0, gross - pension), 2)
    credit = round(sum(p.medical_deduction for p in payslips), 2)

    actual_annual_tax = tt.slab_tax(taxable, employee.tax_year) \
        - tt.rebate_for(employee.age, employee.tax_year) \
        - min(credit, _medical_credit_cap(payslips, employee))
    actual_annual_tax = max(0.0, actual_annual_tax)

    difference = round(actual_annual_tax - deducted, 2)

    return {
        "employee_number": employee.employee_number,
        "full_name": employee.full_name,
        "tax_year": employee.tax_year,
        "months_paid": len(payslips),
        "remuneration": gross,
        "pension": pension,
        "taxable_income": taxable,
        "actual_tax": round(actual_annual_tax, 2),
        "paye_deducted": deducted,
        # The PAYE adjustment for the last payslip. A negative number
        # means the employee was taxed too much and has to be given the
        # money back on the final payslip of the year.
        "adjustment": difference,
        "over_deducted": difference < 0,
        "under_deducted": difference > 0,
    }


def _medical_credit_cap(payslips: list, employee: Employee) -> float:
    """The medical tax credit the employee was entitled to for the year."""
    monthly = tt.medical_credit(
        employee.medical_own, employee.medical_members, employee.tax_year
    )
    return monthly * 12


def calculate_payslip(
    employee: Employee,
    period: date,
    inputs: Optional[dict] = None,
    employer_annual_payroll: float = 0.0,
) -> Payslip:
    """
    Work out one employee's payslip for one month.

    period                   : the month being paid (any day in it)
    inputs                   : the month specific items - overtime, bonus,
                               commission, fringe benefit, leave
    employer_annual_payroll  : the employer's annual remuneration, which
                               decides whether SDL is payable at all
    """
    data = dict(DEFAULT_INPUTS)
    data.update({k: v for k, v in (inputs or {}).items() if v is not None})

    months = months_worked_in_year(employee, period)
    if months == 0:
        raise ValueError(
            f"{employee.full_name} has not started by "
            f"{period.strftime('%B %Y')}."
        )

    # -- earnings --------------------------------------------------------
    unpaid_days = float(data.get("unpaid_leave_days") or 0)
    if unpaid_days < 0 or unpaid_days > MAX_UNPAID_LEAVE_DAYS:
        raise ValueError("Unpaid leave days must be between 0 and 31.")

    daily_rate = employee.basic_salary / 21.75      # average paid days a month
    unpaid_deduction = _round2(min(unpaid_days, 30) * daily_rate)
    basic = _round2(max(0.0, employee.basic_salary - unpaid_deduction))

    overtime = calculate_overtime(employee.basic_salary, data)
    bonus = _round2(float(data.get("bonus") or 0))
    commission = _round2(float(data.get("commission") or 0))
    fringe = _round2(float(data.get("fringe_benefit") or 0))
    leave_pay = _round2(float(data.get("leave_pay") or 0))
    other = _round2(float(data.get("other_allowance") or 0))

    gross = _round2(basic + overtime + bonus + commission + fringe + leave_pay + other)

    # -- deductions before tax -------------------------------------------
    pension = calculate_pension(employee, gross)
    medical_own = _round2(employee.medical_own)
    credit_monthly = (
        tt.medical_credit(employee.medical_own, employee.medical_members,
                          employee.tax_year)
        if employee.medical_own > 0 or employee.medical_members > 1
        else 0.0
    )
    credit_annual = _round2(credit_monthly * 12)

    # -- tax --------------------------------------------------------------
    # The taxable income for the month, annualised, taxed, and divided
    # by 12 again. That is the monthly PAYE.
    monthly_taxable = _round2(max(0.0, gross - pension))
    tax = annualised_tax(
        monthly_taxable, employee.age, employee.tax_year,
        medical_credit_annual=credit_annual,
    )
    paye = _round_to_rand(tax["monthly_tax"])

    # -- UIF, SDL ---------------------------------------------------------
    commission_share = (commission / gross) if gross > 0 else 0
    if employee.commission_earner and commission_share >= 0.5:
        # A commission earner whose commission is at least half of the
        # remuneration is not a UIF contributor.
        uif_base = 0.0
    else:
        uif_base = min(gross, tt.UIF_MONTHLY_THRESHOLD)
    uif_employee = _round2(uif_base * tt.UIF_EMPLOYEE_RATE)
    uif_employer = _round2(uif_base * tt.UIF_EMPLOYER_RATE)

    leviable = _round2(max(0.0, gross - pension))
    if employer_annual_payroll and employer_annual_payroll < tt.SDL_ANNUAL_PAYROLL_EXEMPTION:
        sdl = 0.0
    else:
        sdl = _round2(leviable * tt.SDL_RATE)

    total_deductions = _round2(paye + uif_employee + pension + medical_own)
    net = _round2(gross - total_deductions)
    employer_cost = _round2(uif_employer + sdl + employee.medical_employer)

    return Payslip(
        employee_id=employee.id or 0,
        employee_number=employee.employee_number,
        employee_name=employee.full_name,
        period=period.strftime("%Y-%m"),
        basic_salary=basic,
        overtime=overtime,
        bonus=bonus,
        commission=commission,
        fringe_benefit=fringe,
        leave_pay=leave_pay,
        other_allowance=other,
        gross_remuneration=gross,
        gross_annualised=tax["annualised_taxable"],
        pension_deduction=pension,
        medical_deduction=medical_own,
        taxable_income=tax["annualised_taxable"],
        annual_tax=tax["annual_tax"],
        paye=paye,
        uif_employee=uif_employee,
        uif_employer=uif_employer,
        sdl=sdl,
        total_deductions=total_deductions,
        net_pay=net,
        employer_cost=employer_cost,
        effective_rate=(
            tax["annual_tax"] / tax["annualised_taxable"]
            if tax["annualised_taxable"] else 0.0
        ),
        marginal_rate=tax["marginal_rate"],
        months_worked=months,
        notes=str(data.get("notes") or ""),
    )


def is_payable(employee: Employee, period: date) -> bool:
    """
    Should this employee be on this month's payslip?

    Someone who has not started yet, or who has already left, is not
    paid - the run simply skips them.
    """
    if employee.end_date and employee.end_date < period:
        return False
    if employee.start_date > period:
        return False
    return True


def calculate_pay_run(
    employees,
    period: date,
    inputs_by_employee=None,
) -> list:
    """
    Work out the payslips for everybody for one month.

    inputs_by_employee maps an employee id to that month's overtime,
    bonus and leave. Employees who have not started yet, or who have
    left, are skipped.
    """
    inputs_by_employee = inputs_by_employee or {}

    # The employer's annual remuneration decides the SDL exemption, and
    # it has to be worked out before the payslips.
    payable = [e for e in employees if is_payable(e, period)]
    monthly_basic = sum(max(0.0, e.basic_salary) for e in payable)
    employer_annual_payroll = monthly_basic * 12

    payslips = []
    for employee in payable:
        inputs = inputs_by_employee.get(employee.id) \
            or inputs_by_employee.get(employee.employee_number) \
            or {}
        payslips.append(
            calculate_payslip(
                employee, period, inputs, employer_annual_payroll
            )
        )
    return payslips
