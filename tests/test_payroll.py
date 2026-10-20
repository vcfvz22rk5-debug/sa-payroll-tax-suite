"""
tests/test_payroll.py - proof that the employer-side engine is correct.

Every number below was worked out by hand from the SARS tables:
  * PAYE comes from the progressive slab rates and the age rebates
  * UIF is 1% each side, capped at R17 712 a month
  * SDL is 1% of the leviable amount, and employers with an annual
    payroll below R500 000 are exempt
  * the medical scheme fees tax credit is a rebate against the tax
  * the EMP201 is due by the 7th of the month that follows

Run it with:
    python3 tests/test_payroll.py
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from payroll import (                     # noqa: E402
    calculate_payslip,
    calculate_sdl,
    run_payroll,
    emp201_summary,
    emp201_due_date,
    load_employees,
    allowance_for_retirement,
)
from tax_tables import medical_credit     # noqa: E402

CHECKS = 0
DEMO_CSV = os.path.join(
    os.path.dirname(__file__), "..", "data", "employees.csv"
)


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


def main():
    global CHECKS
    print("\nRunning tests...\n")

    # --- Section 11F: the retirement deduction limit -------------------
    allowed, cap = allowance_for_retirement(360_000, 3_000)
    close(allowed, 36_000, "A R3 000 pension is fully allowed on a R360 000 salary")
    close(cap, 99_000, "The s11F cap is 27.5% of R360 000")

    allowed, cap = allowance_for_retirement(1_800_000, 40_000)
    close(cap, 350_000, "The s11F cap never exceeds R350 000")
    close(
        allowed, 350_000,
        "A R40 000 monthly pension is capped at R350 000 a year",
    )

    # --- SDL -----------------------------------------------------------
    close(calculate_sdl(10_000, 600_000), 100, "SDL is 1% of the leviable amount")
    close(
        calculate_sdl(10_000, 400_000), 0,
        "Employers below R500 000 a year pay no SDL",
    )
    close(
        calculate_sdl(10_000, 500_000), 100,
        "An annual payroll of exactly R500 000 still pays SDL",
    )

    # --- The medical scheme fees tax credit ---------------------------
    close(medical_credit(0, 1, "2027"), 376, "2027: the taxpayer alone gets R376")
    close(medical_credit(0, 2, "2027"), 752, "2027: the taxpayer and a spouse get R752")
    close(
        medical_credit(0, 3, "2027"), 1_006,
        "2027: a third dependant adds R254",
    )
    close(
        medical_credit(0, 5, "2027"), 1_514,
        "2027: two more dependants add R254 each",
    )
    close(medical_credit(0, 1, "2026"), 364, "2026: the taxpayer alone gets R364")
    close(medical_credit(0, 2, "2026"), 728, "2026: the taxpayer and a spouse get R728")
    close(
        medical_credit(500, 1, "2027"), 500,
        "You keep the higher of the tabulated credit and what you pay",
    )

    # --- One payslip, worked out by hand -------------------------------
    # Thandi: R32 000 a month, 34, R1 500 pension, medical R1 200 (2 on scheme)
    #   taxable income   384 000 - 18 000       = 366 000
    #   tax before rebates  44 118 + 26% x (366 000 - 245 100) = 75 552
    #   less primary rebate 17 820 and the medical credit 18 912  = 38 820
    #   monthly PAYE       38 820 / 12                            = 3 235.00
    #   UIF                capped at 17 712 x 1%                   = 177.12
    #   retirement         18 000 a year / 12                      = 1 500.00
    #   net                32 000 - 3 235 - 177.12 - 1 500       = 27 087.88
    payslip = calculate_payslip({
        "name": "Thandi Mokoena",
        "gross_monthly": 32_000,
        "age": 34,
        "ra_monthly": 1_500,
        "medical_monthly": 1_200,
        "medical_dependants": 2,
    }, "2027")

    close(payslip["gross_annual"], 384_000, "Annualised gross is 12 x the monthly pay")
    close(payslip["ra_allowed_annual"], 18_000, "The pension deduction is allowed in full")
    close(payslip["taxable_income"], 366_000, "Taxable income is after the pension")
    close(payslip["medical_credit_annual"], 18_912, "The medical credit is R1 576 a month")
    close(payslip["annual_tax"], 38_820, "The annual tax includes the medical credit")
    close(payslip["paye_monthly"], 3_235, "Monthly PAYE is the annual tax over 12")
    close(payslip["uif_employee"], 177.12, "UIF is capped at R177.12")
    close(payslip["uif_employer"], 177.12, "The employer matches the UIF")
    close(
        payslip["sdl"], 0,
        "A one-person business under R500 000 a year pays no SDL",
    )
    close(payslip["net_monthly"], 27_087.88, "The net monthly pay is correct")
    close(
        payslip["total_deductions"], 4_912.12,
        "The deductions are PAYE, UIF and the retirement contribution",
    )

    # The same employee in a company whose payroll is over R500 000
    in_team = calculate_payslip({
        "name": "Thandi Mokoena",
        "gross_monthly": 32_000,
        "age": 34,
        "ra_monthly": 1_500,
        "medical_monthly": 1_200,
        "medical_dependants": 2,
    }, "2027", annual_payroll=2_664_000)
    close(
        in_team["sdl"], 305,
        "SDL is 1% of the R30 500 leviable amount in a bigger company",
    )

    # A person on their own, below the SDL exemption
    solo = calculate_payslip({
        "name": "Johan van Wyk",
        "gross_monthly": 14_500,
        "age": 58,
    }, "2027")
    close(solo["paye_monthly"], 1_125, "R14 500 a month -> R1 125 PAYE")
    close(solo["uif_employee"], 145, "UIF below the ceiling is 1% of the salary")
    close(solo["sdl"], 0, "A one-person business under R500 000 pays no SDL")
    close(solo["net_monthly"], 13_230, "The net monthly pay is correct")

    # --- A whole payroll run -------------------------------------------
    employees = load_employees(DEMO_CSV)
    same(len(employees), 5, "The demo CSV has five employees")
    same(employees[0]["name"], "Thandi Mokoena", "The first employee is read correctly")
    close(employees[0]["gross_monthly"], 32_000, "The gross salary is read correctly")
    same(employees[0]["medical_dependants"], 2, "The dependant count is read correctly")
    close(employees[1]["ra_monthly"], 0, "A missing optional column defaults to zero")

    payroll = run_payroll(employees, "2027")
    same(payroll["head_count"], 5, "The payroll run has five payslips")
    close(payroll["total_gross"], 222_000, "Total gross monthly pay is correct")
    close(payroll["annual_payroll"], 2_664_000, "The annual payroll total is correct")
    close(payroll["total_paye"], 41_511.08, "The total PAYE withheld is correct")
    close(payroll["total_uif_employee"], 853.48, "The total UIF is correct")
    close(payroll["total_sdl"], 2_125, "SDL is charged because the payroll is over R500 000")
    close(payroll["total_net"], 170_135.44, "The total net pay is correct")
    close(
        payroll["total_employer_cost"], 2_978.48,
        "The employer's extra cost is UIF plus SDL",
    )

    # Sipho's medical scheme changes his PAYE:
    #   tax before rebates  18% x 222 000        = 39 960
    #   less primary rebate 17 820 and the medical credit 9 600 = 12 540
    #   monthly PAYE        12 540 / 12          = 1 045.00
    sipho = payroll["payslips"][1]
    close(sipho["medical_credit_annual"], 9_600, "Sipho's medical credit is R800 a month")
    close(sipho["paye_monthly"], 1_045, "Sipho's PAYE is after the medical credit")
    close(sipho["net_monthly"], 17_277.88, "Sipho's net monthly pay is correct")

    # --- The EMP201 -----------------------------------------------------
    summary = emp201_summary(payroll, date(2026, 10, 1))
    same(summary["head_count"], 5, "The EMP201 covers every employee")
    close(summary["total_remuneration"], 222_000, "The EMP201 total remuneration")
    close(summary["paye"], 41_511.08, "The EMP201 PAYE total")
    close(summary["uif_total"], 1_706.96, "The EMP201 UIF total (both sides)")
    close(summary["sdl"], 2_125, "The EMP201 SDL total")
    close(
        summary["total_liability"], 45_343.04,
        "The EMP201 total liability is PAYE + UIF + SDL",
    )

    # 7 November 2026 is a Saturday, so the deadline moves back a day.
    same(
        emp201_due_date(date(2026, 10, 1)), date(2026, 11, 6),
        "An EMP201 due on a Saturday moves to the Friday before",
    )
    same(
        emp201_due_date(date(2026, 3, 1)), date(2026, 4, 7),
        "An EMP201 for March is due on 7 April",
    )

    # --- Bad CSV --------------------------------------------------------
    try:
        load_employees(os.path.join(os.path.dirname(__file__), "test_payroll.py"))
        raise AssertionError("FAILED: a CSV without the right headers should fail")
    except ValueError:
        CHECKS += 1
        print("  ok - a CSV with the wrong columns is rejected")

    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
