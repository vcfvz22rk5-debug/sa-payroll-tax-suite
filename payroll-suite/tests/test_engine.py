"""
tests/test_engine.py - the calculation engine.

Every figure below was worked out by hand from the SARS tables, using
the annualised method a real payroll uses:

    monthly taxable income x 12  ->  slab rates  ->  less rebates
    ->  less the medical tax credit  ->  / 12  ->  monthly PAYE

Run it with:
    python3 tests/test_engine.py
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from payroll_suite.engine import (          # noqa: E402
    annualised_tax,
    calculate_overtime,
    calculate_payslip,
    calculate_pension,
    is_payable,
    months_worked_in_year,
    reconcile_tax_year,
)
from payroll_suite.models import Employee     # noqa: E402
from payroll_suite.tax_tables import (       # noqa: E402
    medical_credit,
    tax_month_index,
)

CHECKS = 0


def close(actual, expected, message, tolerance=0.01):
    global CHECKS
    CHECKS += 1
    assert abs(actual - expected) <= tolerance, (
        f"FAILED: {message}\n  expected {expected:,.2f}, got {actual:,.2f}"
    )
    print(f"  ok - {message}")


def same(actual, expected, message):
    global CHECKS
    CHECKS += 1
    assert actual == expected, (
        f"FAILED: {message}\n  expected {expected!r}, got {actual!r}"
    )
    print(f"  ok - {message}")


def employee(**overrides) -> Employee:
    data = {
        "employee_number": "E0001",
        "full_name": "Test Employee",
        "age": 34,
        "start_date": date(2025, 3, 1),
        "basic_salary": 32_000.0,
        "tax_year": "2027",
    }
    data.update(overrides)
    return Employee(**data)


def main():
    global CHECKS
    print("\nRunning tests...\n")

    # --- the tax year runs March to February ---------------------------
    same(tax_month_index(3), 1, "March is month 1 of the tax year")
    same(tax_month_index(12), 10, "December is month 10 of the tax year")
    same(tax_month_index(1), 11, "January is month 11 of the tax year")
    same(tax_month_index(2), 12, "February is month 12 of the tax year")

    # --- the medical scheme fees tax credit ---------------------------
    close(medical_credit(0, 1, "2027"), 376, "2027: the taxpayer alone gets R376")
    close(medical_credit(0, 2, "2027"), 752, "2027: the taxpayer and a spouse get R752")
    close(medical_credit(0, 3, "2027"), 1_006, "2027: a third dependant adds R254")
    close(medical_credit(0, 4, "2027"), 1_260, "2027: a fourth dependant adds R254")
    close(medical_credit(0, 1, "2026"), 364, "2026: the taxpayer alone gets R364")
    close(medical_credit(0, 2, "2026"), 728, "2026: the taxpayer and a spouse get R728")
    close(
        medical_credit(500, 1, "2027"), 500,
        "You keep the higher of the tabulated credit and what you pay",
    )

    # --- the annualised tax -------------------------------------------
    # R29 600 a month x 12 = R355 200
    #   tax  = 44 118 + 26% x (355 200 - 245 100) = 72 744
    #   less the primary rebate 17 820                       = 54 924
    #   less the medical credit 18 912                       = 36 012
    #   monthly PAYE = 36 012 / 12                            = 3 001
    tax = annualised_tax(29_600, 34, "2027", medical_credit_annual=18_912)
    close(tax["annualised_taxable"], 355_200, "The taxable income is annualised")
    close(tax["tax_before_rebates"], 72_744, "The slab tax is correct")
    close(tax["rebate"], 17_820, "The primary rebate is applied")
    close(tax["annual_tax"], 36_012, "The medical credit comes off the tax")
    close(tax["monthly_tax"], 3_001, "The annual tax is divided by 12")
    close(tax["marginal_rate"], 0.26, "The marginal rate is the top slab")

    # A 68-year-old gets the secondary rebate as well.
    tax = annualised_tax(90_250, 68, "2027", medical_credit_annual=22_512)
    close(tax["rebate"], 27_585, "At 65+ the secondary rebate is added")
    close(tax["annual_tax"], 290_046, "The tax for a 68-year-old is correct")

    # --- section 11F: the pension cap ---------------------------------
    close(
        calculate_pension(employee(basic_salary=32_000, pension_rate=7.5), 32_000),
        2_400, "7.5% of R32 000 is R2 400",
    )
    close(
        calculate_pension(employee(basic_salary=100_000, pension_rate=50), 100_000),
        27_500, "The pension is capped at 27.5% of the remuneration",
    )
    close(
        calculate_pension(employee(basic_salary=120_000, pension_rate=50), 120_000),
        29_166.67, "The pension is capped at R350 000 a year",
    )
    close(
        calculate_pension(employee(basic_salary=32_000, pension_rate=0), 32_000),
        0, "No pension means no deduction",
    )

    # --- overtime ------------------------------------------------------
    # R30 000 a month over 195 hours is R153.85 an hour
    close(
        calculate_overtime(30_000, {"overtime_hours": 10}),
        2_307.69, "10 ordinary hours at 1.5x",
    )
    close(
        calculate_overtime(30_000, {"overtime_hours": 50}),
        11_923.08, "The first 45 hours are at 1.5x and the rest at 2x",
    )
    close(
        calculate_overtime(30_000, {"sunday_hours": 8}),
        2_461.54, "Sunday hours are at 2x",
    )
    close(
        calculate_overtime(30_000, {"public_holiday_hours": 8}),
        2_461.54, "Public holiday hours are at 2x",
    )
    close(calculate_overtime(30_000, {}), 0, "No overtime, no pay")

    # --- a full payslip -------------------------------------------------
    thandi = employee(
        full_name="Thandi Mokoena", age=34, basic_salary=32_000,
        pension_rate=7.5, medical_members=2, medical_own=1_200,
    )
    slip = calculate_payslip(thandi, date(2026, 10, 31))
    close(slip.gross_remuneration, 32_000, "Thandi's gross is R32 000")
    close(slip.pension_deduction, 2_400, "Thandi's pension is R2 400")
    close(slip.taxable_income, 355_200, "Thandi's taxable income is annualised")
    close(slip.annual_tax, 36_012, "Thandi's annual tax is R36 012")
    close(slip.paye, 3_001, "Thandi's PAYE is R3 001")
    close(slip.uif_employee, 177.12, "Thandi's UIF is capped at R177.12")
    close(slip.sdl, 296, "Thandi's SDL is 1% of R29 600")
    close(slip.net_pay, 25_221.88, "Thandi takes home R25 221.88")
    close(
        slip.months_worked, 8,
        "Thandi has worked eight months of the tax year by October",
    )

    # A pensioner gets the bigger rebate.
    nomsa = employee(
        full_name="Nomsa Dlamini", age=68, basic_salary=95_000,
        pension_rate=5, medical_members=2, medical_own=1_500,
    )
    slip = calculate_payslip(nomsa, date(2026, 10, 31))
    close(slip.paye, 24_171, "Nomsa's PAYE is R24 171")
    close(slip.sdl, 902.50, "Nomsa's SDL is 1% of R90 250")
    close(slip.net_pay, 64_401.88, "Nomsa takes home R64 401.88")

    # Somebody on a small salary.
    johan = employee(
        full_name="Johan van Wyk", age=58, basic_salary=14_500,
    )
    slip = calculate_payslip(johan, date(2026, 10, 31))
    close(slip.paye, 1_125, "Johan pays R1 125")
    close(slip.uif_employee, 145, "Johan is below the UIF ceiling")
    close(slip.net_pay, 13_230, "Johan takes home R13 230")

    # --- bonuses, commission and leave ---------------------------------
    slip = calculate_payslip(
        johan, date(2026, 10, 31),
        {"bonus": 10_000, "leave_pay": 2_000, "other_allowance": 500},
    )
    close(slip.gross_remuneration, 27_000, "The bonus and leave are added to the gross")
    close(slip.bonus, 10_000, "The bonus is on the payslip")

    slip = calculate_payslip(
        johan, date(2026, 10, 31), {"unpaid_leave_days": 5},
    )
    close(
        slip.gross_remuneration, 11_166.67,
        "Five days of unpaid leave comes off the basic salary",
    )

    # A commission earner with mostly commission is not a UIF contributor.
    slip = calculate_payslip(
        employee(basic_salary=10_000, commission_earner=True),
        date(2026, 10, 31), {"commission": 40_000},
    )
    close(slip.uif_employee, 0, "A commission earner is not a UIF contributor")

    # --- who is on the payroll ------------------------------------------
    newcomer = employee(
        employee_number="E0002", full_name="Sipho Ndlovu",
        start_date=date(2026, 11, 1), basic_salary=18_500,
        medical_members=1, medical_own=800,
    )
    same(months_worked_in_year(newcomer, date(2026, 10, 31)), 0,
         "Sipho has not started by October")
    same(months_worked_in_year(newcomer, date(2026, 11, 30)), 1,
         "Sipho has worked one month by November")
    same(months_worked_in_year(newcomer, date(2027, 2, 28)), 4,
         "Sipho has worked four months by February")
    same(months_worked_in_year(thandi, date(2027, 2, 28)), 12,
         "Thandi has worked the whole tax year by February")
    same(is_payable(newcomer, date(2026, 10, 31)), False,
         "Sipho is not payable in October")
    same(is_payable(newcomer, date(2026, 11, 30)), True,
         "Sipho is payable in November")

    # --- the year end reconciliation ------------------------------------
    # Sipho joined in November, so the annualised method taxed him as if
    # he was going to earn a full year. His real liability is nil, so
    # the employer has to give R4 180 back.
    slips = [
        calculate_payslip(newcomer, date(2026, month, 28))
        for month in (11, 12)
    ] + [
        calculate_payslip(newcomer, date(2027, month, 28))
        for month in (1, 2)
    ]
    close(sum(s.paye for s in slips), 4_180, "Sipho paid R1 045 a month")
    result = reconcile_tax_year(newcomer, slips)
    close(result["remuneration"], 74_000, "Sipho earned R74 000 in the year")
    close(result["actual_tax"], 0, "Sipho's real tax for the year is nil")
    close(
        result["adjustment"], -4_180,
        "The employer has to give R4 180 back on the last payslip",
    )
    same(result["over_deducted"], True, "The reconciliation spots the over-deduction")

    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
