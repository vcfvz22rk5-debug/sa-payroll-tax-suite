"""
payroll_suite — a small-business payroll and SARS compliance system.

Pure standard library: no pip install, no framework, no build step.
"""

__version__ = "1.0.0"

from payroll_suite.models import Employee, PayRun, Payslip  # noqa: F401
from payroll_suite.engine import (  # noqa: F401
    calculate_payslip,
    calculate_pay_run,
    annualised_tax,
)

__all__ = [
    "Employee",
    "PayRun",
    "Payslip",
    "calculate_payslip",
    "calculate_pay_run",
    "annualised_tax",
]
