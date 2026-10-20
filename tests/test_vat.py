"""
tests/test_vat.py - proof that the VAT engine is correct.

Every number below was worked out by hand from the SARS rules:
  * VAT is 15% on taxable supplies
  * input tax is 15% of the purchases you can claim back
  * a vendor with taxable supplies above R2 300 000 must register
    (raised from R1 000 000 on 1 April 2026)
  * a VAT201 for a bi-monthly period is due in the month after the
    period ends

Run it with:
    python3 tests/test_vat.py
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vat import (                      # noqa: E402
    calculate_vat,
    vat_periods,
    vat201_summary,
    registration_status,
    vat_category,
)

CHECKS = 0


def close(actual, expected, message, tolerance=0.01):
    global CHECKS
    CHECKS += 1
    assert abs(actual - expected) <= tolerance, (
        f"FAILED: {message}\n  expected {expected:,.2f}, got {actual:,.2f}"
    )
    print(f"  ok - {message}")


def is_true(actual, message):
    global CHECKS
    CHECKS += 1
    assert actual, f"FAILED: {message}"
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

    # --- The 15% calculation ------------------------------------------
    result = calculate_vat(100_000, 0)
    close(result["output_tax"], 15_000, "R100 000 of sales -> R15 000 output VAT")
    close(result["input_tax"], 0, "No purchases -> no input VAT")
    close(result["net_vat"], 15_000, "Output tax with no input tax is payable")
    close(result["amount_payable"], 15_000, "R15 000 payable to SARS")
    close(result["amount_claimable"], 0, "Nothing to claim back")

    result = calculate_vat(100_000, 40_000)
    close(result["output_tax"], 15_000, "R100 000 of sales -> R15 000 output VAT")
    close(result["input_tax"], 6_000, "R40 000 of purchases -> R6 000 input VAT")
    close(result["net_vat"], 9_000, "Net VAT to pay is R9 000")
    close(result["amount_payable"], 9_000, "R9 000 payable to SARS")

    # Input tax bigger than output tax = a refund
    result = calculate_vat(50_000, 80_000)
    close(result["net_vat"], -4_500, "Input tax above output tax is a negative net")
    close(result["amount_claimable"], 4_500, "R4 500 to claim back from SARS")
    close(result["amount_payable"], 0, "Nothing payable when you are owed money")
    is_true(result["is_refund"], "The result is flagged as a refund")

    # Rounding: 15% of R33.33 is R5.00 (5.0 exactly), of R1 111.11 is R166.67
    close(calculate_vat(1_111.11, 0)["output_tax"], 166.67, "Output VAT is rounded to cents")

    # --- Bad input ----------------------------------------------------
    try:
        calculate_vat(-1, 0)
        raise AssertionError("FAILED: negative supplies should raise an error")
    except ValueError:
        CHECKS += 1
        print("  ok - negative supplies are rejected")

    # --- The VAT periods ----------------------------------------------
    periods = vat_periods("2027")
    same(len(periods), 6, "There are six bi-monthly VAT periods in a tax year")

    first = periods[0]
    same(first["start"], date(2026, 3, 1), "2027 P1 starts on 1 March 2026")
    same(first["end"], date(2026, 4, 30), "2027 P1 ends on 30 April 2026")
    same(first["due_month"], "May 2026", "2027 P1 is due in May 2026")

    last = periods[5]
    same(last["start"], date(2027, 1, 1), "2027 P6 starts on 1 January 2027")
    same(last["end"], date(2027, 2, 28), "2027 P6 ends on 28 February 2027")
    same(last["due_month"], "March 2027", "2027 P6 is due in March 2027")

    # The 2026 tax year ends in February 2026
    periods_2026 = vat_periods("2026")
    same(periods_2026[0]["start"], date(2025, 3, 1), "2026 P1 starts on 1 March 2025")
    same(periods_2026[5]["end"], date(2026, 2, 28), "2026 P6 ends on 28 February 2026")
    same(periods_2026[5]["due_month"], "March 2026", "2026 P6 is due in March 2026")

    # --- The VAT201 summary -------------------------------------------
    summary = vat201_summary("2027", 1, 15_000, 6_000)
    close(summary["net_vat"], 9_000, "VAT201: R15 000 less R6 000 = R9 000")
    same(summary["status"], "Payment due", "VAT201 with a positive net is a payment")
    same(summary["period"]["period"], "P1", "The summary keeps the period details")

    refund = vat201_summary("2027", 1, 5_000, 9_000)
    same(refund["status"], "Refund due", "VAT201 with a negative net is a refund")
    close(refund["amount_claimable"], 4_000, "VAT201 refund of R4 000")

    try:
        vat201_summary("2027", 9, 1_000, 0)
        raise AssertionError("FAILED: an unknown period should raise an error")
    except ValueError:
        CHECKS += 1
        print("  ok - an unknown VAT period is rejected")

    # --- Registration --------------------------------------------------
    status = registration_status(2_500_000)
    is_true(status["must_register"], "Above R2.3m you must register for VAT")
    same(status["status"], "Compulsory registration", "The status says compulsory")

    status = registration_status(500_000)
    is_true(not status["must_register"], "Below R2.3m registration is not compulsory")
    same(
        status["status"],
        "Voluntary registration available",
        "Above R120 000 you may register voluntarily",
    )

    status = registration_status(50_000)
    same(status["status"], "Not required", "Below R120 000 you do not need to register")

    # --- Category ------------------------------------------------------
    same(vat_category(35_000_000), "C", "Above R30m you file every month")
    same(vat_category(1_000_000), "A/B", "Below R30m you file every two months")

    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
