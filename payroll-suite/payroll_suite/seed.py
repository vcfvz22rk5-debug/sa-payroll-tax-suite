"""
seed.py - the demo staff.

Six people who between them cover every case the engine has to handle:
a long-serving employee, someone who joined in the middle of the tax
year (where the annualised method matters), a pensioner, a commission
earner and a boss on a high salary.
"""

from datetime import date

from payroll_suite.db import Database
from payroll_suite.models import Employee

DEMO_EMPLOYEES = [
    {
        "employee_number": "E0001",
        "full_name": "Thandi Mokoena",
        "id_number": "880101 0108 7",
        "age": 34,
        "email": "thandi@shongwe-cc.co.za",
        "start_date": date(2025, 3, 1),
        "basic_salary": 32_000.0,
        "pension_rate": 7.5,
        "pension_amount": 0.0,
        "medical_members": 2,
        "medical_own": 1_200.0,
        "medical_employer": 1_450.0,
        "annual_leave_days": 15,
        "notes": "Operations manager",
    },
    {
        "employee_number": "E0002",
        "full_name": "Sipho Ndlovu",
        "id_number": "011203 0409 2",
        "age": 26,
        "email": "sipho@shongwe-cc.co.za",
        # Joined in the middle of the 2027 tax year, so the annualised
        # method kicks in.
        "start_date": date(2026, 11, 1),
        "basic_salary": 18_500.0,
        "pension_rate": 0.0,
        "pension_amount": 0.0,
        "medical_members": 1,
        "medical_own": 800.0,
        "medical_employer": 850.0,
        "annual_leave_days": 15,
        "notes": "Junior developer",
    },
    {
        "employee_number": "E0003",
        "full_name": "Fatima Adams",
        "id_number": "900312 0101 3",
        "age": 39,
        "email": "fatima@shongwe-cc.co.za",
        "start_date": date(2024, 3, 1),
        "basic_salary": 62_000.0,
        "pension_rate": 10.0,
        "pension_amount": 1_000.0,
        "medical_members": 4,
        "medical_own": 1_800.0,
        "medical_employer": 2_100.0,
        "annual_leave_days": 20,
        "notes": "Financial manager",
    },
    {
        "employee_number": "E0004",
        "full_name": "Johan van Wyk",
        "id_number": "700115 0307 1",
        "age": 58,
        "email": "johan@shongwe-cc.co.za",
        "start_date": date(2023, 3, 1),
        "basic_salary": 14_500.0,
        "pension_rate": 0.0,
        "pension_amount": 0.0,
        "medical_members": 1,
        "medical_own": 0.0,
        "medical_employer": 0.0,
        "annual_leave_days": 15,
        "notes": "Store assistant",
    },
    {
        "employee_number": "E0005",
        "full_name": "Nomsa Dlamini",
        "id_number": "550220 0206 4",
        "age": 68,
        "email": "nomsa@shongwe-cc.co.za",
        "start_date": date(2020, 3, 1),
        "basic_salary": 95_000.0,
        "pension_rate": 5.0,
        "pension_amount": 0.0,
        "medical_members": 2,
        "medical_own": 1_500.0,
        "medical_employer": 1_700.0,
        "annual_leave_days": 20,
        "notes": "Non-executive director",
    },
    {
        "employee_number": "E0006",
        "full_name": "Lerato Nkosi",
        "id_number": "990625 0104 8",
        "age": 31,
        "email": "lerato@shongwe-cc.co.za",
        "start_date": date(2026, 9, 1),
        "basic_salary": 45_000.0,
        "pension_rate": 0.0,
        "pension_amount": 0.0,
        "medical_members": 3,
        "medical_own": 1_450.0,
        "medical_employer": 1_600.0,
        "commission_earner": True,
        "annual_leave_days": 15,
        "notes": "Sales consultant, commission earner",
    },
]


def seed_demo_data(db: Database) -> list:
    """
    Fill an empty database with the demo staff.

    Existing employees are left alone, so running this twice does not
    create duplicates.
    """
    existing = {e.employee_number for e in db.list_employees(active_only=False)}
    created = []
    for data in DEMO_EMPLOYEES:
        if data["employee_number"] in existing:
            continue
        created.append(db.add_employee(Employee(**data)))
    return created
