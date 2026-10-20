"""
tests/test_db.py - the storage layer.

The database is the part that has to survive a restart, so these tests
check that what goes in comes back out, and that a pay run can be
replaced without leaving half a month behind.

Run it with:
    python3 tests/test_db.py
"""

import os
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from payroll_suite.db import Database            # noqa: E402
from payroll_suite.engine import calculate_payslip  # noqa: E402
from payroll_suite.models import Employee, PayRun  # noqa: E402

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

    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    os.unlink(path)

    db = Database(path)

    # --- the schema is created on the first run ------------------------
    same(db.next_employee_number(), "E0001", "The first employee number is E0001")

    # --- adding and reading employees ----------------------------------
    thandi = db.add_employee(Employee(
        employee_number="E0001", full_name="Thandi Mokoena", age=34,
        start_date=date(2025, 3, 1), basic_salary=32_000,
        pension_rate=7.5, medical_members=2, medical_own=1_200,
    ))
    same(thandi.id, 1, "The first employee gets id 1")
    same(db.next_employee_number(), "E0002", "The next employee number is E0002")

    db.add_employee(Employee(
        employee_number="E0002", full_name="Sipho Ndlovu", age=26,
        start_date=date(2026, 11, 1), basic_salary=18_500,
    ))

    employees = db.list_employees()
    same(len(employees), 2, "Both employees are on the payroll")
    same(employees[0].full_name, "Sipho Ndlovu", "The list is sorted by name")

    found = db.find_employee("E0002")
    same(found.full_name, "Sipho Ndlovu", "An employee can be found by number")
    same(db.find_employee("nobody"), None, "An unknown employee returns nothing")

    # The values survive the round trip.
    reloaded = db.get_employee(thandi.id)
    close(reloaded.basic_salary, 32_000, "The salary survives the round trip")
    close(reloaded.pension_rate, 7.5, "The pension rate survives the round trip")
    same(reloaded.start_date, date(2025, 3, 1), "The start date survives the round trip")
    same(reloaded.medical_members, 2, "The medical members survive the round trip")

    # --- updating --------------------------------------------------------
    thandi.basic_salary = 36_000
    db.update_employee(thandi)
    close(db.get_employee(thandi.id).basic_salary, 36_000, "An update is saved")

    # --- deactivating ----------------------------------------------------
    db.deactivate_employee(db.get_employee(2), date(2027, 2, 28))
    same(len(db.list_employees()), 1, "A leaver is not on the active list")
    same(len(db.list_employees(active_only=False)), 2, "A leaver is still in the records")

    # --- a pay run -------------------------------------------------------
    run = db.create_run(PayRun(period="2026-11", pay_date=date(2026, 11, 30)))
    same(run.status, "draft", "A new run is a draft")
    same(len(db.list_runs()), 1, "The run is listed")

    thandi = db.get_employee(1)
    payslips = [
        calculate_payslip(thandi, date(2026, 11, 30)),
        calculate_payslip(db.get_employee(2), date(2026, 11, 30)),
    ]
    for payslip in payslips:
        payslip.run_id = run.id
    saved = db.save_payslips(payslips)
    same(saved, 2, "Both payslips are saved")

    stored = db.payslips_for_period("2026-11")
    same(len(stored), 2, "The payslips come back for the period")
    close(
        sum(p.paye for p in stored), 5_877,
        "The PAYE is stored exactly",
    )
    close(
        db.get_employee(2).basic_salary, 18_500,
        "Sipho is still on the same salary",
    )

    totals = db.payroll_totals("2026-11")
    close(totals["total_gross"], 54_500, "The gross total is correct")
    close(totals["total_paye"], 5_877, "The PAYE total is correct")
    close(totals["head_count"], 2, "The head count is correct")

    # --- replacing a run -------------------------------------------------
    db.delete_run(run)
    same(len(db.payslips_for_period("2026-11")), 0, "Deleting a run removes its payslips")
    same(len(db.list_runs()), 0, "Deleting a run removes the run")

    # --- a leaver's year end --------------------------------------------
    same(len(db.employee_payslips(1)), 0, "An employee with no runs has no payslips")

    # --- the data survives closing the database --------------------------
    db.close()
    db = Database(path)
    same(len(db.list_employees(active_only=False)), 2, "The employees are still there")
    db.close()

    os.unlink(path)
    print(f"\nAll {CHECKS} tests passed!\n")


if __name__ == "__main__":
    main()
