"""
db.py - the SQLite layer.

The whole system stores its state in one SQLite file, so the suite can
be copied onto a USB stick and still have the employees, the payslips
and the declarations. There is no server to install and no service to
restart.

The schema is created on first run and migrated afterwards, so an old
database keeps working when the code moves on.
"""

import os
import sqlite3
from datetime import date, datetime
from typing import Iterable, Optional

from payroll_suite.models import Employee, PayRun, Payslip

SCHEMA_VERSION = 1

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "payroll.db",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS employees (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number    TEXT    NOT NULL UNIQUE,
    full_name          TEXT    NOT NULL,
    id_number          TEXT    DEFAULT '',
    age                INTEGER NOT NULL DEFAULT 30,
    email              TEXT    DEFAULT '',
    start_date         TEXT    NOT NULL,
    end_date           TEXT,
    tax_year           TEXT    NOT NULL DEFAULT '2027',
    basic_salary       REAL    NOT NULL DEFAULT 0,
    pension_rate       REAL    NOT NULL DEFAULT 0,
    pension_amount     REAL    NOT NULL DEFAULT 0,
    medical_members    INTEGER NOT NULL DEFAULT 1,
    medical_own        REAL    NOT NULL DEFAULT 0,
    medical_employer   REAL    NOT NULL DEFAULT 0,
    commission_earner  INTEGER NOT NULL DEFAULT 0,
    annual_leave_days  REAL    NOT NULL DEFAULT 0,
    active             INTEGER NOT NULL DEFAULT 1,
    notes              TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pay_runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    period     TEXT NOT NULL UNIQUE,
    pay_date   TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT '',
    notes      TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS payslips (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id             INTEGER NOT NULL REFERENCES pay_runs(id) ON DELETE CASCADE,
    employee_id        INTEGER NOT NULL REFERENCES employees(id),
    employee_number    TEXT,
    employee_name      TEXT,
    period             TEXT,
    basic_salary       REAL DEFAULT 0,
    overtime           REAL DEFAULT 0,
    bonus              REAL DEFAULT 0,
    commission         REAL DEFAULT 0,
    fringe_benefit     REAL DEFAULT 0,
    leave_pay          REAL DEFAULT 0,
    other_allowance    REAL DEFAULT 0,
    gross_remuneration REAL DEFAULT 0,
    gross_annualised  REAL DEFAULT 0,
    pension_deduction  REAL DEFAULT 0,
    medical_deduction  REAL DEFAULT 0,
    taxable_income     REAL DEFAULT 0,
    annual_tax         REAL DEFAULT 0,
    paye               REAL DEFAULT 0,
    uif_employee       REAL DEFAULT 0,
    uif_employer       REAL DEFAULT 0,
    sdl                REAL DEFAULT 0,
    total_deductions   REAL DEFAULT 0,
    net_pay            REAL DEFAULT 0,
    employer_cost      REAL DEFAULT 0,
    effective_rate     REAL DEFAULT 0,
    marginal_rate      REAL DEFAULT 0,
    months_worked      INTEGER DEFAULT 12,
    notes              TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_payslips_run  ON payslips(run_id);
CREATE INDEX IF NOT EXISTS idx_payslips_emp  ON payslips(employee_id);
CREATE INDEX IF NOT EXISTS idx_payslips_per  ON payslips(period);
"""


class Database:
    """
    A thin wrapper around a SQLite connection.

    Every method returns plain Python objects (dataclasses or dicts), so
    the rest of the suite never has to think about SQL.
    """

    def __init__(self, path: str = DEFAULT_DB):
        self.path = path
        if path != ":memory:":
            folder = os.path.dirname(os.path.abspath(path))
            os.makedirs(folder, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_schema()

    # -- lifecycle -------------------------------------------------------
    def init_schema(self) -> None:
        """Create the tables if they are not there, and stamp the version."""
        self.conn.executescript(SCHEMA)
        row = self.conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- employees -------------------------------------------------------
    def add_employee(self, employee: Employee) -> Employee:
        row = employee.to_row()
        row.pop("id", None)
        keys = ", ".join(row)
        marks = ", ".join("?" for _ in row)
        cursor = self.conn.execute(
            f"INSERT INTO employees ({keys}) VALUES ({marks})", tuple(row.values())
        )
        self.conn.commit()
        employee.id = cursor.lastrowid
        return employee

    def update_employee(self, employee: Employee) -> Employee:
        row = employee.to_row()
        employee_id = row.pop("id")
        assignments = ", ".join(f"{k} = ?" for k in row)
        self.conn.execute(
            f"UPDATE employees SET {assignments} WHERE id = ?",
            (*row.values(), employee_id),
        )
        self.conn.commit()
        return employee

    def get_employee(self, employee_id: int) -> Optional[Employee]:
        row = self.conn.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        return Employee.from_row(row) if row else None

    def find_employee(self, key: str) -> Optional[Employee]:
        """Look an employee up by their number, name or id number."""
        row = self.conn.execute(
            "SELECT * FROM employees WHERE employee_number = ? OR id_number = ? "
            "OR full_name = ? LIMIT 1",
            (key, key, key),
        ).fetchone()
        return Employee.from_row(row) if row else None

    def list_employees(self, active_only: bool = True) -> list:
        sql = "SELECT * FROM employees"
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY full_name"
        return [Employee.from_row(r) for r in self.conn.execute(sql)]

    def deactivate_employee(self, employee: Employee, end_date: date) -> None:
        self.conn.execute(
            "UPDATE employees SET active = 0, end_date = ? WHERE id = ?",
            (end_date.isoformat(), employee.id),
        )
        self.conn.commit()

    def next_employee_number(self) -> str:
        """The next free employee number, e.g. E0007."""
        row = self.conn.execute(
            "SELECT employee_number FROM employees ORDER BY id DESC LIMIT 1"
        ).fetchone()
        last = 0
        if row:
            digits = "".join(ch for ch in row["employee_number"] if ch.isdigit())
            last = int(digits) if digits else 0
        return f"E{last + 1:04d}"

    # -- pay runs --------------------------------------------------------
    def create_run(self, run: PayRun) -> PayRun:
        if not run.created_at:
            run.created_at = datetime.now().isoformat(timespec="seconds")
        row = run.to_row()
        row.pop("id", None)
        keys = ", ".join(row)
        marks = ", ".join("?" for _ in row)
        cursor = self.conn.execute(
            f"INSERT INTO pay_runs ({keys}) VALUES ({marks})", tuple(row.values())
        )
        self.conn.commit()
        run.id = cursor.lastrowid
        return run

    def get_run(self, period: str) -> Optional[PayRun]:
        row = self.conn.execute(
            "SELECT * FROM pay_runs WHERE period = ?", (period,)
        ).fetchone()
        return PayRun.from_row(row) if row else None

    def list_runs(self) -> list:
        return [
            PayRun.from_row(r)
            for r in self.conn.execute("SELECT * FROM pay_runs ORDER BY period DESC")
        ]

    def set_run_status(self, run: PayRun, status: str) -> None:
        run.status = status
        self.conn.execute(
            "UPDATE pay_runs SET status = ? WHERE id = ?", (status, run.id)
        )
        self.conn.commit()

    def delete_run(self, run: PayRun) -> None:
        self.conn.execute("DELETE FROM payslips WHERE run_id = ?", (run.id,))
        self.conn.execute("DELETE FROM pay_runs WHERE id = ?", (run.id,))
        self.conn.commit()

    # -- payslips --------------------------------------------------------
    def save_payslips(self, payslips: Iterable[Payslip]) -> int:
        rows = [p.to_row() for p in payslips]
        for row in rows:
            row.pop("id", None)
        if not rows:
            return 0
        keys = ", ".join(rows[0])
        marks = ", ".join("?" for _ in rows[0])
        self.conn.executemany(
            f"INSERT INTO payslips ({keys}) VALUES ({marks})",
            [tuple(r.values()) for r in rows],
        )
        self.conn.commit()
        return len(rows)

    def list_payslips(self, period: Optional[str] = None) -> list:
        if period:
            rows = self.conn.execute(
                "SELECT * FROM payslips WHERE period = ? ORDER BY employee_name",
                (period,),
            )
        else:
            rows = self.conn.execute(
                "SELECT * FROM payslips ORDER BY period DESC, employee_name"
            )
        return [Payslip.from_row(r) for r in rows]

    def payslips_for_period(self, period: str) -> list:
        return self.list_payslips(period)

    def employee_payslips(self, employee_id: int) -> list:
        rows = self.conn.execute(
            "SELECT * FROM payslips WHERE employee_id = ? ORDER BY period",
            (employee_id,),
        )
        return [Payslip.from_row(r) for r in rows]

    # -- reporting helpers ----------------------------------------------
    def payroll_totals(self, period: str) -> dict:
        """The headline numbers for one period."""
        row = self.conn.execute(
            """
            SELECT COUNT(*)            AS head_count,
                   SUM(gross_remuneration) AS total_gross,
                   SUM(paye)            AS total_paye,
                   SUM(uif_employee)    AS total_uif_employee,
                   SUM(uif_employer)    AS total_uif_employer,
                   SUM(sdl)             AS total_sdl,
                   SUM(net_pay)         AS total_net,
                   SUM(pension_deduction) AS total_pension,
                   SUM(employer_cost)   AS total_employer_cost
            FROM payslips WHERE period = ?
            """,
            (period,),
        ).fetchone()
        return {k: (row[k] or 0) for k in row.keys()}

    def annual_payroll_for_period(self, period: str) -> float:
        """The employer's annual remuneration, used for the SDL exemption."""
        row = self.conn.execute(
            "SELECT SUM(basic_salary) AS total FROM payslips WHERE period = ?",
            (period,),
        ).fetchone()
        monthly = row["total"] or 0.0
        return monthly * 12
