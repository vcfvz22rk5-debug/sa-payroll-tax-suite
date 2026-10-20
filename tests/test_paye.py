"""
tests/test_paye.py - proof that the maths is correct.

In software this is called "unit testing". Employers LOVE seeing tests
in a portfolio because it shows you check your own work - the same
habit that makes a good accountant.

Run it with:
    python3 tests/test_paye.py

Every check below was worked out by hand from the SARS tables.
"""

import os
import sys

# Make it possible to import the calculator files from the project folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from paye import calculate_annual_tax   # noqa: E402
from uif import calculate_uif           # noqa: E402
from tax_tables import medical_credit  # noqa: E402
from other_income import (              # noqa: E402
    interest_exemption,
    taxable_interest,
    dividends_tax,
    net_dividends,
)

CHECKS = 0


def close(actual, expected, message, tolerance=0.01):
    global CHECKS
    CHECKS += 1
    assert abs(actual - expected) <= tolerance, (
        f"FAILED: {message}\n  expected R{expected:,.2f}, got R{actual:,.2f}"
    )
    print(f"  ok - {message}")


def main():
    print("\nRunning tests...\n")

    # --- Below the threshold: no tax at all --------------------------
    # R95 750 x 18% = R17 235, minus primary rebate R17 235 = R0
    close(
        calculate_annual_tax(95_750, age=30, tax_year="2026"),
        0,
        "2026: income at the threshold pays no tax",
    )

    # R99 000 x 18% = R17 820, minus rebate R17 820 = R0
    close(
        calculate_annual_tax(99_000, age=30, tax_year="2027"),
        0,
        "2027: income at the threshold pays no tax",
    )

    # --- Mid-range salary, worked out by hand ------------------------
    # 2026: R360 000 falls in the R237 101 - R370 500 bracket
    #   tax = 42 678 + 26% x (360 000 - 237 100) = 74 632
    #   less primary rebate 17 235               = 57 397
    close(
        calculate_annual_tax(360_000, age=30, tax_year="2026"),
        57_397,
        "2026: R360 000 salary -> R57 397 tax",
    )

    # 2027: R360 000 falls in the R245 101 - R383 100 bracket
    #   tax = 44 118 + 26% x (360 000 - 245 100) = 73 992
    #   less primary rebate 17 820               = 56 172
    close(
        calculate_annual_tax(360_000, age=30, tax_year="2027"),
        56_172,
        "2027: R360 000 salary -> R56 172 tax",
    )

    # --- Age 70 gets the bigger rebate -------------------------------
    # 2026, R200 000:  18% x 200 000            = 36 000
    #   less primary 17 235 + secondary 9 444    = 26 679
    #   tax                                   =  9 321
    close(
        calculate_annual_tax(200_000, age=70, tax_year="2026"),
        9_321,
        "2026: age 70 gets primary + secondary rebates",
    )

    # --- Top bracket --------------------------------------------------
    # 2027, R2 000 000: 666 339 + 45% x (2 000 000 - 1 878 600)
    #                 = 666 339 + 54 630 = 720 969
    #   less primary rebate 17 820        = 703 149
    close(
        calculate_annual_tax(2_000_000, age=45, tax_year="2027"),
        703_149,
        "2027: top 45% bracket calculated correctly",
    )

    # --- UIF ----------------------------------------------------------
    close(
        calculate_uif(30_000)["employee"],
        177.12,
        "UIF on R30 000 is capped at R177.12",
    )
    close(
        calculate_uif(10_000)["employee"],
        100.00,
        "UIF on R10 000 is 1% = R100",
    )
    close(
        calculate_uif(30_000)["employer"],
        177.12,
        "Employer matches the UIF contribution",
    )

    # --- Medical scheme fees tax credit -------------------------------
    # 2027: R376 a month for the taxpayer, R376 for the first dependant
    # and R254 for each one after that.
    close(
        medical_credit(0, 1, "2027"), 376,
        "2027: the medical credit for the taxpayer alone",
    )
    close(
        medical_credit(0, 3, "2027"), 1_006,
        "2027: the medical credit for the taxpayer and two dependants",
    )

    # A medical credit is a rebate against the tax, so it reduces the
    # tax by the credit - but never below zero.
    # 2027, R360 000 salary -> R56 172 tax with no medical credit.
    close(
        calculate_annual_tax(360_000, age=30, tax_year="2027",
                              medical_credit_annual=0),
        56_172,
        "2027: a R360 000 salary with no medical credit",
    )
    close(
        calculate_annual_tax(360_000, age=30, tax_year="2027",
                              medical_credit_annual=4_512),
        51_660,
        "2027: the medical credit is deducted from the tax",
    )
    close(
        calculate_annual_tax(50_000, age=30, tax_year="2027",
                              medical_credit_annual=100_000),
        0,
        "2027: a big medical credit cannot push the tax below zero",
    )

    # --- Interest ------------------------------------------------------
    close(
        interest_exemption(30), 23_800,
        "Interest exemption under 65 is R23 800",
    )
    close(
        interest_exemption(70), 34_500,
        "Interest exemption at 65+ is R34 500",
    )
    close(
        taxable_interest(20_000, 30), 0,
        "Interest below the exemption is fully exempt",
    )
    close(
        taxable_interest(33_800, 30), 10_000,
        "Only the interest above the exemption is taxable",
    )
    close(
        taxable_interest(20_000, 70), 0,
        "R20 000 of interest is exempt for a 70-year-old",
    )

    # --- Dividends -----------------------------------------------------
    close(
        dividends_tax(50_000), 10_000,
        "20% dividends tax is withheld at source",
    )
    close(
        net_dividends(50_000), 40_000,
        "R50 000 of dividends leaves you with R40 000",
    )

    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
