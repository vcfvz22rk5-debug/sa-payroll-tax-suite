"""
vat.py - Value-Added Tax: the 15% engine and a VAT201 period summary.

This is the EMPLOYER'S side of tax. Where paye.py answers "how much tax
does this employee pay?", this file answers "how much VAT does this
business pay SARS, and when is it due?"

The VAT rules in one paragraph:
  * A registered vendor charges 15% VAT on taxable supplies (sales).
  * A vendor claims back the 15% VAT on qualifying purchases (inputs).
  * If output tax > input tax, you PAY the difference to SARS.
  * If input tax > output tax, you CLAIM the difference back.
  * Most vendors file a VAT201 every two months, and it is due in the
    month after the period ends.

Source: https://www.sars.gov.za/types-of-tax/value-added-tax/
"""

import calendar
from datetime import date

from config import (
    VAT_RATE,
    VAT_COMPULSORY_THRESHOLD,
    VAT_VOLUNTARY_THRESHOLD,
    VAT_CATEGORY_C_THRESHOLD,
    VAT_MANUAL_DUE_DAY,
)

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ----------------------------------------------------------------------
# THE CALCULATION
# ----------------------------------------------------------------------
def calculate_vat(taxable_supplies, taxable_purchases, vat_rate=VAT_RATE):
    """
    Work out the VAT for one VAT period.

    taxable_supplies  : value of your sales that carried VAT (no VAT)
    taxable_purchases : value of your purchases that carried VAT that
                        you can claim back (no VAT)

    Returns a dictionary with the output tax, the input tax and what
    the net result is: money to pay SARS, or money to claim back.
    """
    if taxable_supplies < 0:
        raise ValueError("Taxable supplies cannot be negative.")
    if taxable_purchases < 0:
        raise ValueError("Taxable purchases cannot be negative.")

    output_tax = round(taxable_supplies * vat_rate, 2)
    input_tax = round(taxable_purchases * vat_rate, 2)
    net = round(output_tax - input_tax, 2)

    return {
        "taxable_supplies": round(taxable_supplies, 2),
        "taxable_purchases": round(taxable_purchases, 2),
        "vat_rate": vat_rate,
        "output_tax": output_tax,
        "input_tax": input_tax,
        "net_vat": net,
        # Positive net = pay SARS. Negative net = claim it back.
        "amount_payable": max(0.0, net),
        "amount_claimable": max(0.0, -net),
        "is_refund": net < 0,
    }


# ----------------------------------------------------------------------
# THE VAT PERIODS
# ----------------------------------------------------------------------
def _last_day_of_month(year, month):
    return calendar.monthrange(year, month)[1]


def _last_business_day(year, month):
    """
    The last weekday of the month.

    Public holidays are not built in (the tool does not have a South
    African public-holiday calendar), so over a long weekend the real
    deadline can be a day or two earlier. The date returned is the
    weekend-adjusted deadline that SARS quotes.
    """
    day = _last_day_of_month(year, month)
    while date(year, month, day).weekday() >= 5:   # 5 = Saturday, 6 = Sunday
        day -= 1
    return date(year, month, day)


def _add_months(year, month, count):
    """Move a year/month pair forward (or back) by a number of months."""
    total = year * 12 + (month - 1) + count
    return total // 12, total % 12 + 1


def vat_periods(tax_year="2027"):
    """
    The six bi-monthly VAT periods for a tax year, with their due dates.

    A tax year ends in February, so a vendor with a February year-end
    has these periods:
        1 Mar - 30 Apr,  1 May - 30 Jun,  1 Jul - 31 Aug,
        1 Sep - 31 Oct,  1 Nov - 31 Dec,  1 Jan - end Feb

    Each period is due in the month that follows it:
        * manual submission/payment -> the 25th
        * filed and paid on eFiling   -> the last business day
    """
    year = int(tax_year)
    base_year = year - 1          # the year the tax year starts in

    periods = []
    for index, start_month in enumerate([3, 5, 7, 9, 11], start=1):
        start = date(base_year, start_month, 1)
        end_month = start_month + 1
        end = date(base_year, end_month, _last_day_of_month(base_year, end_month))
        periods.append((index, start, end))

    # The sixth period runs from January to the end of February.
    start = date(year, 1, 1)
    end = date(year, 2, _last_day_of_month(year, 2))
    periods.append((6, start, end))

    result = []
    for number, start, end in periods:
        due_year, due_month = _add_months(end.year, end.month, 1)
        manual_due = date(due_year, due_month, VAT_MANUAL_DUE_DAY)
        # If the 25th is a weekend, SARS moves it back to the previous
        # business day.
        while manual_due.weekday() >= 5:
            manual_due = date(manual_due.year, manual_due.month,
                              manual_due.day - 1)
        result.append({
            "number": number,
            "start": start,
            "end": end,
            "label": f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}",
            "period": f"P{number}",
            "due_month": f"{MONTH_NAMES[due_month - 1]} {due_year}",
            "due_manual": manual_due,
            "due_efiling": _last_business_day(due_year, due_month),
        })
    return result


def vat201_summary(tax_year, period_number, output_tax, input_tax):
    """
    A VAT201-style summary for one period.

    This is the shape of the numbers that go on the real VAT201 return,
    plus the deadline you have to meet.
    """
    periods = {p["number"]: p for p in vat_periods(tax_year)}
    if period_number not in periods:
        raise ValueError(
            f"Unknown VAT period {period_number!r}. Choose one of: "
            f"{', '.join(str(n) for n in sorted(periods))}"
        )

    period = periods[period_number]
    net = round(output_tax - input_tax, 2)

    return {
        "tax_year": tax_year,
        "period": period,
        "output_tax": round(output_tax, 2),
        "input_tax": round(input_tax, 2),
        "net_vat": net,
        "amount_payable": max(0.0, net),
        "amount_claimable": max(0.0, -net),
        "is_refund": net < 0,
        "status": "Refund due" if net < 0 else "Payment due",
    }


# ----------------------------------------------------------------------
# REGISTRATION
# ----------------------------------------------------------------------
def registration_status(taxable_supplies):
    """
    Do you have to be registered for VAT?

    From 1 April 2026 the compulsory threshold was raised from
    R1 000 000 to R2 300 000, and the voluntary threshold from
    R50 000 to R120 000.
    """
    if taxable_supplies < 0:
        raise ValueError("Taxable supplies cannot be negative.")

    if taxable_supplies > VAT_COMPULSORY_THRESHOLD:
        return {
            "must_register": True,
            "status": "Compulsory registration",
            "detail": (
                f"Taxable supplies of R{taxable_supplies:,.0f} are above the "
                f"R{VAT_COMPULSORY_THRESHOLD:,.0f} threshold, so you must be "
                "registered for VAT."
            ),
        }
    if taxable_supplies > VAT_VOLUNTARY_THRESHOLD:
        return {
            "must_register": False,
            "status": "Voluntary registration available",
            "detail": (
                f"Taxable supplies of R{taxable_supplies:,.0f} are above the "
                f"R{VAT_VOLUNTARY_THRESHOLD:,.0f} voluntary threshold but below "
                f"the compulsory R{VAT_COMPULSORY_THRESHOLD:,.0f}, so you may "
                "register voluntarily."
            ),
        }
    return {
        "must_register": False,
        "status": "Not required",
        "detail": (
            f"Taxable supplies of R{taxable_supplies:,.0f} are below the "
            f"R{VAT_VOLUNTARY_THRESHOLD:,.0f} voluntary threshold."
        ),
    }


def vat_category(taxable_supplies):
    """
    Which VAT period applies to you?

    Category C vendors (taxable supplies above R30 million a year) file
    a VAT201 every month. Everybody else files every two months.
    """
    if taxable_supplies > VAT_CATEGORY_C_THRESHOLD:
        return "C"
    return "A/B"
