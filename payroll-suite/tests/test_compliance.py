"""
tests/test_compliance.py - the SARS forms and the calendar.

The EMP201, the EMP501, the IRP5 and the deadlines are the parts an
employer actually gets in trouble with, so each one is checked against
a hand-worked figure.

Run it with:
    python3 tests/test_compliance.py
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from payroll_suite.compliance import (       # noqa: E402
    deadlines,
    emp201,
    emp201_due_date,
    emp501,
    irp5,
    upcoming,
)
from payroll_suite.engine import calculate_payslip  # noqa: E402
from payroll_suite.models import Employee     # noqa: E402

CHECKS = 0


def same(actual, expected, message):
    global CHECKS
    CHECKS += 1
    assert actual == expected, (
        f"FAILED: {message}\n  expected {expected!r}, got {actual!r}"
    )
    print(f"  ok - {message}")


def close(actual, expected, message, tolerance=0.01):
    global CHECKS
    CHECKS += 1
    assert abs(actual - expected) <= tolerance, (
        f"FAILED: {message}\n  expected {expected:,.2f}, got {actual:,.2f}"
    )
    print(f"  ok - {message}")


def main():
    global CHECKS
    print("\nRunning tests...\n")

    # --- the EMP201 due date -------------------------------------------
    same(emp201_due_date("2026-10"), date(2026, 11, 6),
         "An October payroll is due on 6 November (the 7th is a Saturday)")
    same(emp201_due_date("2026-11"), date(2026, 12, 7),
         "A November payroll is due on 7 December")
    same(emp201_due_date("2026-12"), date(2027, 1, 7),
         "A December payroll is due on 7 January")
    same(emp201_due_date("2026-09"), date(2026, 10, 7),
         "A September payroll is due on 7 October")

    # --- the EMP201 ----------------------------------------------------
    thandi = Employee(
        employee_number="E0001", full_name="Thandi Mokoena", age=34,
        start_date=date(2025, 3, 1), basic_salary=32_000,
        pension_rate=7.5, medical_members=2, medical_own=1_200,
    )
    johan = Employee(
        employee_number="E0004", full_name="Johan van Wyk", age=58,
        start_date=date(2023, 3, 1), basic_salary=14_500,
    )
    payslips = [
        calculate_payslip(thandi, date(2026, 11, 30)),
        calculate_payslip(johan, date(2026, 11, 30)),
    ]
    summary = emp201(payslips, "2026-11")
    same(summary["head_count"], 2, "The EMP201 covers both employees")
    close(summary["total_remuneration"], 46_500, "The total remuneration is right")
    close(summary["paye"], 4_126, "The PAYE total is right")
    close(summary["uif_employee"], 322.12, "The employee UIF is right")
    close(summary["uif_employer"], 322.12, "The employer UIF is right")
    close(summary["sdl"], 441, "The SDL is 1% of the leviable amounts")
    close(
        summary["total_liability"], 5_211.24,
        "The total liability is PAYE + UIF + SDL",
    )
    same(summary["due_date"], date(2026, 12, 7), "The due date is right")

    # --- the IRP5 -------------------------------------------------------
    certificate = irp5(thandi, payslips)
    same(certificate["employee_number"], "E0001", "The certificate has the number")
    same(certificate["months_employed"], 1, "The certificate counts the months")
    close(certificate["remuneration"], 32_000, "The certificate has the remuneration")
    close(certificate["paye"], 3_001, "The certificate has the PAYE")
    close(certificate["net_pay"], 25_221.88, "The certificate has the net pay")
    same(
        certificate["certificate_number"], "IRP5-E0001-2027",
        "The certificate is numbered",
    )

    # --- the EMP501 ------------------------------------------------------
    declarations = [
        emp201(payslips, "2026-10"),
        emp201(payslips, "2026-11"),
    ]
    certificates = [certificate, irp5(johan, payslips)]
    result = emp501(declarations, certificates)
    same(result["declarations"], 2, "Two declarations were reconciled")
    same(result["certificates"], 2, "Two certificates were reconciled")
    close(result["declared"]["paye"], 8_252, "The declared PAYE total")
    close(result["certified"]["paye"], 4_126, "The certified PAYE total")
    close(
        result["difference"]["paye"], -4_126,
        "The difference is what is left to explain",
    )
    same(result["in_balance"], False, "A difference means it is not in balance")

    # When the certificates match the declarations it balances.
    balanced = emp501([emp201(payslips, "2026-11")], certificates)
    same(balanced["in_balance"], True, "One month of both balances")
    close(balanced["difference"]["paye"], 0, "There is no difference")

    # --- the calendar ----------------------------------------------------
    items = deadlines("2027")
    same(len(items) > 25, True, "The calendar has a full year of deadlines")

    names = [item["name"] for item in items]
    same(any("EMP201" in n for n in names), True, "The calendar has the EMP201s")
    same(any("VAT201" in n for n in names), True, "The calendar has the VAT201s")
    same(any("IRP5" in n for n in names), True, "The calendar has the IRP5s")
    same(any("EMP501" in n for n in names), True, "The calendar has the EMP501")
    same(any("Provisional tax" in n for n in names), True,
         "The calendar has the provisional tax")

    # The dates are in order.
    ordered = all(
        items[i]["date"] <= items[i + 1]["date"] for i in range(len(items) - 1)
    )
    same(ordered, True, "The calendar is in date order")

    # The first EMP201 of the year is the 7th of April 2026.
    emp201_dates = [i["date"] for i in items if "EMP201" in i["name"]]
    same(emp201_dates[0], date(2026, 4, 7),
         "The first EMP201 of the tax year is 7 April 2026")
    same(len(emp201_dates), 12, "There are twelve EMP201s in a tax year")

    # The first VAT201 of the year is 25 May 2026.
    vat_manual = [
        i["date"] for i in items
        if "VAT201" in i["name"] and "manual" in i["name"]
    ]
    same(vat_manual[0], date(2026, 5, 25),
         "The first manual VAT201 is 25 May 2026")
    same(len(vat_manual), 6, "There are six manual VAT201s in a tax year")

    # The IRP5 certificates are due within 60 days of the year end.
    irp5_items = [i for i in items if "IRP5" in i["name"]]
    same(irp5_items[0]["date"], date(2027, 4, 29),
         "The IRP5 certificates are due on 29 April 2027")

    # --- what is coming up -----------------------------------------------
    soon = upcoming("2027", days=60, today=date(2026, 3, 1))
    same(len(soon) > 0, True, "There are deadlines in the next 60 days")
    same(all(item["date"] >= date(2026, 3, 1) for item in soon), True,
         "Only the future deadlines are returned")
    same(soon[0]["date"], date(2026, 4, 7),
         "The first deadline is the April EMP201")

    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
