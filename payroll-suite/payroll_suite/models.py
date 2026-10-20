"""
models.py - the data shapes used across the suite.

Plain dataclasses with a `to_row()` / `from_row()` pair, so the same
objects can be stored in SQLite and passed around without a third
party ORM.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Any, Optional


def _as_date(value: Any) -> Optional[date]:
    if value in (None, "", "None"):
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value) in ("1", "True", "true", "yes")


@dataclass
class Employee:
    """One person on the payroll."""

    employee_number: str
    full_name: str
    age: int
    start_date: date
    basic_salary: float = 0.0            # monthly, in Rand
    id_number: str = ""
    email: str = ""
    end_date: Optional[date] = None
    tax_year: str = "2027"

    # Retirement fund: a percentage of the pensionable salary, plus a
    # fixed monthly amount. Both are capped by section 11F.
    pension_rate: float = 0.0             # e.g. 7.5 for 7.5%
    pension_amount: float = 0.0           # e.g. a fixed R1 500

    # Medical scheme
    medical_members: int = 1              # including the employee
    medical_own: float = 0.0              # what the employee pays
    medical_employer: float = 0.0         # what the employer contributes

    # A commission earner may be exempt from UIF (50% or more of the
    # remuneration is commission), and their pension works differently.
    commission_earner: bool = False

    annual_leave_days: float = 0.0
    active: bool = True
    notes: str = ""

    id: Optional[int] = field(default=None, compare=False)

    # -- storage helpers ------------------------------------------------
    COLUMNS = (
        "id", "employee_number", "full_name", "id_number", "age", "email",
        "start_date", "end_date", "tax_year", "basic_salary", "pension_rate",
        "pension_amount", "medical_members", "medical_own",
        "medical_employer", "commission_earner", "annual_leave_days",
        "active", "notes",
    )

    def to_row(self) -> dict:
        row = asdict(self)
        row["start_date"] = self.start_date.isoformat()
        row["end_date"] = self.end_date.isoformat() if self.end_date else None
        row["commission_earner"] = int(self.commission_earner)
        row["active"] = int(self.active)
        return row

    @classmethod
    def from_row(cls, row: Any) -> "Employee":
        data = dict(row)
        return cls(
            id=data.get("id"),
            employee_number=data.get("employee_number", ""),
            full_name=data.get("full_name", ""),
            id_number=data.get("id_number", "") or "",
            age=int(data.get("age") or 30),
            email=data.get("email", "") or "",
            start_date=_as_date(data.get("start_date")) or date.today(),
            end_date=_as_date(data.get("end_date")),
            tax_year=str(data.get("tax_year") or "2027"),
            basic_salary=float(data.get("basic_salary") or 0),
            pension_rate=float(data.get("pension_rate") or 0),
            pension_amount=float(data.get("pension_amount") or 0),
            medical_members=int(data.get("medical_members") or 1),
            medical_own=float(data.get("medical_own") or 0),
            medical_employer=float(data.get("medical_employer") or 0),
            commission_earner=_as_bool(data.get("commission_earner")),
            annual_leave_days=float(data.get("annual_leave_days") or 0),
            active=_as_bool(data.get("active")),
            notes=data.get("notes", "") or "",
        )

    def __str__(self) -> str:
        return f"{self.employee_number} · {self.full_name}"


@dataclass
class PayRun:
    """A payroll run for one month."""

    period: str                 # '2026-10'
    pay_date: date
    status: str = "draft"       # draft | submitted
    created_at: str = ""
    notes: str = ""
    id: Optional[int] = field(default=None, compare=False)

    COLUMNS = ("id", "period", "pay_date", "status", "created_at", "notes")

    def to_row(self) -> dict:
        row = asdict(self)
        row["pay_date"] = self.pay_date.isoformat()
        return row

    @classmethod
    def from_row(cls, row: Any) -> "PayRun":
        data = dict(row)
        return cls(
            id=data.get("id"),
            period=data.get("period", ""),
            pay_date=_as_date(data.get("pay_date")) or date.today(),
            status=data.get("status", "draft") or "draft",
            created_at=data.get("created_at", "") or "",
            notes=data.get("notes", "") or "",
        )


@dataclass
class Payslip:
    """One employee's payslip, as stored."""

    run_id: int = 0
    employee_id: int = 0
    employee_number: str = ""
    employee_name: str = ""
    period: str = ""

    basic_salary: float = 0.0
    overtime: float = 0.0
    bonus: float = 0.0
    commission: float = 0.0
    fringe_benefit: float = 0.0
    leave_pay: float = 0.0
    other_allowance: float = 0.0

    gross_remuneration: float = 0.0
    gross_annualised: float = 0.0

    pension_deduction: float = 0.0
    medical_deduction: float = 0.0

    taxable_income: float = 0.0
    annual_tax: float = 0.0
    paye: float = 0.0

    uif_employee: float = 0.0
    uif_employer: float = 0.0
    sdl: float = 0.0

    total_deductions: float = 0.0
    net_pay: float = 0.0
    employer_cost: float = 0.0
    effective_rate: float = 0.0
    marginal_rate: float = 0.0
    months_worked: int = 12
    notes: str = ""

    id: Optional[int] = field(default=None, compare=False)

    COLUMNS = (
        "id", "run_id", "employee_id", "employee_number", "employee_name",
        "period", "basic_salary", "overtime", "bonus", "commission",
        "fringe_benefit", "leave_pay", "other_allowance",
        "gross_remuneration", "gross_annualised", "pension_deduction",
        "medical_deduction", "taxable_income", "annual_tax", "paye",
        "uif_employee", "uif_employer", "sdl", "total_deductions",
        "net_pay", "employer_cost", "effective_rate", "marginal_rate",
        "months_worked", "notes",
    )

    def to_row(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Any) -> "Payslip":
        data = dict(row)
        known = {f for f in cls.__dataclass_fields__ if f in data}
        values = {k: data[k] for k in known}
        return cls(**values)
