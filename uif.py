"""
uif.py - UIF (Unemployment Insurance Fund) contributions.

Rules:
  * Employee pays 1% of salary.
  * Employer matches with another 1% (it is a REAL cost to the business -
    worth remembering in an interview!).
  * Only salary up to UIF_MONTHLY_THRESHOLD counts.
"""

from config import (
    UIF_MONTHLY_THRESHOLD,
    UIF_EMPLOYEE_RATE,
    UIF_EMPLOYER_RATE,
)


def calculate_uif(gross_monthly):
    """
    Return the UIF for one month as a dictionary:
      {"employee": ..., "employer": ..., "base": ...}
    """
    if gross_monthly < 0:
        raise ValueError("Salary cannot be negative.")

    # The 1% only applies to salary up to the ceiling
    base = min(gross_monthly, UIF_MONTHLY_THRESHOLD)

    return {
        "base": base,
        "employee": round(base * UIF_EMPLOYEE_RATE, 2),
        "employer": round(base * UIF_EMPLOYER_RATE, 2),
    }
