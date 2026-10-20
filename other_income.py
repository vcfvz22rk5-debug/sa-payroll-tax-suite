"""
other_income.py - interest and dividends.

These two types of income do not behave like a salary at all, and the
rules are the ones people mix up most often:

  INTEREST  - the first R23 800 a year (R34 500 if you are 65 or older)
              of South African interest is EXEMPT from normal income tax.
              Only the amount above the exemption is taxable.

  DIVIDENDS - dividends received from a South African company are exempt
              from normal income tax, but a FINAL dividends tax of 20%
              is withheld at source by the company paying the dividend.
              That is your final tax on the dividend - you do not pay
              income tax on it afterwards.

Source: https://www.sars.gov.za/tax-rates/income-tax/interest-and-dividends/
"""

from config import (
    INTEREST_EXEMPTION_UNDER_65,
    INTEREST_EXEMPTION_65_PLUS,
    DIVIDENDS_TAX_RATE,
)


def interest_exemption(age=30):
    """The annual interest exemption for this taxpayer."""
    if age < 0 or age > 130:
        raise ValueError("Please enter a realistic age (0 - 130).")
    if age >= 65:
        return INTEREST_EXEMPTION_65_PLUS
    return INTEREST_EXEMPTION_UNDER_65


def taxable_interest(interest, age=30):
    """
    How much of the interest ends up in your normal income tax return.

    The exemption is used up first, then everything above it is taxable.
    """
    if interest < 0:
        raise ValueError("Interest cannot be negative.")
    return max(0.0, interest - interest_exemption(age))


def dividends_tax(dividends):
    """
    The dividends tax withheld from a South African dividend.

    This is a FINAL tax: 20% is taken off at source and that is the end
    of it for the taxpayer.
    """
    if dividends < 0:
        raise ValueError("Dividends cannot be negative.")
    return round(dividends * DIVIDENDS_TAX_RATE, 2)


def net_dividends(dividends):
    """What actually lands in your bank account after the withholding."""
    if dividends < 0:
        raise ValueError("Dividends cannot be negative.")
    return round(dividends - dividends_tax(dividends), 2)
