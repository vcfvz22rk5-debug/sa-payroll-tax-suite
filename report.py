"""
report.py - pretty terminal reports.

One place for the formatting so that every report in the project looks
like it came out of the same printer: money on the right, dot leaders in
the middle, 66 characters wide.
"""

WIDTH = 66


def money(amount, brackets=True):
    """Format a number as Rand: R 4,681.00, or (R17,820.00) if negative."""
    if brackets and amount < 0:
        return f"(R{-amount:,.2f})"
    return f"R {amount:,.2f}"


def rule(char="="):
    """A horizontal rule across the report."""
    print(char * WIDTH)


def line(label, amount_str=""):
    """One row: label on the left, money in a fixed column on the right."""
    print(f"  {label:<44}{amount_str:>20}")


def heading(title, subtitle=None):
    """The banner at the top of a report."""
    print()
    rule()
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    rule()


def note(text):
    """A small italic-ish line at the bottom of a report."""
    print(f"  {text}")
