"""
tax_tables.py - the SARS rates, in one place.

A copy of the tables used by the sibling tax-calculator project, kept
here so this suite stands on its own: clone this folder, run it, and
nothing else is needed.

Sources (checked 20 October 2026):
  https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/
  https://www.sars.gov.za/tax-rates/income-tax/interest-and-dividends/
"""

TAX_YEARS = {
    "2026": {
        "label": "2026 tax year (1 Mar 2025 - 28 Feb 2026)",
        "brackets": [
            {"from": 0,         "to": 237_100,   "rate": 0.18, "base_tax": 0},
            {"from": 237_100,   "to": 370_500,   "rate": 0.26, "base_tax": 42_678},
            {"from": 370_500,   "to": 512_800,   "rate": 0.31, "base_tax": 77_362},
            {"from": 512_800,   "to": 673_000,   "rate": 0.36, "base_tax": 121_475},
            {"from": 673_000,   "to": 857_900,   "rate": 0.39, "base_tax": 179_147},
            {"from": 857_900,   "to": 1_817_000, "rate": 0.41, "base_tax": 251_258},
            {"from": 1_817_000, "to": None,      "rate": 0.45, "base_tax": 644_489},
        ],
        "rebates": {"primary": 17_235, "secondary": 9_444, "tertiary": 3_145},
        "medical_credit": {
            "member": 364, "first_dependent": 364, "additional_dependent": 246,
        },
    },
    "2027": {
        "label": "2027 tax year (1 Mar 2026 - 28 Feb 2027)",
        "brackets": [
            {"from": 0,         "to": 245_100,   "rate": 0.18, "base_tax": 0},
            {"from": 245_100,   "to": 383_100,   "rate": 0.26, "base_tax": 44_118},
            {"from": 383_100,   "to": 530_200,   "rate": 0.31, "base_tax": 79_998},
            {"from": 530_200,   "to": 695_800,   "rate": 0.36, "base_tax": 125_599},
            {"from": 695_800,   "to": 887_000,   "rate": 0.39, "base_tax": 185_215},
            {"from": 887_000,   "to": 1_878_600, "rate": 0.41, "base_tax": 259_783},
            {"from": 1_878_600, "to": None,      "rate": 0.45, "base_tax": 666_339},
        ],
        "rebates": {"primary": 17_820, "secondary": 9_765, "tertiary": 3_249},
        "medical_credit": {
            "member": 376, "first_dependent": 376, "additional_dependent": 254,
        },
    },
}

# -- the rates that are not income tax ------------------------------------
UIF_MONTHLY_THRESHOLD = 17_712.00    # max monthly remuneration for UIF
UIF_EMPLOYEE_RATE = 0.01
UIF_EMPLOYER_RATE = 0.01

SDL_RATE = 0.01                       # 1% of the leviable amount
SDL_ANNUAL_PAYROLL_EXEMPTION = 500_000.00

RA_MAX_PERCENT = 0.275                # section 11F: 27.5% of remuneration
RA_MAX_ANNUAL = 350_000.00            # and never more than R350 000 a year

INTEREST_EXEMPTION_UNDER_65 = 23_800.00
INTEREST_EXEMPTION_65_PLUS = 34_500.00
DIVIDENDS_TAX_RATE = 0.20

# -- the employer's calendar ----------------------------------------------
EMP201_DUE_DAY = 7                    # the 7th of the month that follows
VAT_RATE = 0.15
VAT_MANUAL_DUE_DAY = 25               # manual VAT201 submissions
VAT_COMPULSORY_THRESHOLD = 2_300_000.00
VAT_VOLUNTARY_THRESHOLD = 120_000.00

# -- working time ---------------------------------------------------------
# A 45 hour week, which is the standard in South Africa.
WEEKLY_HOURS = 45
MONTHLY_HOURS = round(WEEKLY_HOURS * 52 / 12)     # 195 hours
OVERTIME_FIRST_THRESHOLD = 45         # hours per month at 1.5x
OVERTIME_MULTIPLIER = 1.5
OVERTIME_AFTER_THRESHOLD_MULTIPLIER = 2.0
SUNDAY_MULTIPLIER = 2.0
PUBLIC_HOLIDAY_MULTIPLIER = 2.0

DEFAULT_TAX_YEAR = "2027"


def get_tax_year(tax_year):
    key = str(tax_year).strip()
    if key not in TAX_YEARS:
        raise ValueError(
            f"Unknown tax year {tax_year!r}. Choose one of: "
            f"{', '.join(TAX_YEARS)}"
        )
    return TAX_YEARS[key]


def tax_month_index(month: int) -> int:
    """Which month of the tax year is this calendar month? (March is 1.)"""
    if not 1 <= month <= 12:
        raise ValueError("A month must be between 1 and 12.")
    return ((month - 3) % 12) + 1


def rebate_for(age: int, tax_year: str) -> float:
    table = get_tax_year(tax_year)
    rebate = table["rebates"]["primary"]
    if age >= 65:
        rebate += table["rebates"]["secondary"]
    if age >= 75:
        rebate += table["rebates"]["tertiary"]
    return rebate


def rebate_name(age: int) -> str:
    if age >= 75:
        return "primary + secondary + tertiary rebate"
    if age >= 65:
        return "primary + secondary rebate"
    return "primary rebate"


def slab_tax(taxable_income: float, tax_year: str) -> float:
    """The tax on an annual income, before any rebates."""
    table = get_tax_year(tax_year)
    if taxable_income < 0:
        raise ValueError("Taxable income cannot be negative.")
    for bracket in table["brackets"]:
        top = bracket["to"]
        if top is None or taxable_income <= top:
            return (
                bracket["base_tax"]
                + bracket["rate"] * (taxable_income - bracket["from"])
            )
    last = table["brackets"][-1]
    return last["base_tax"] + last["rate"] * (taxable_income - last["from"])


def marginal_rate(taxable_income: float, tax_year: str) -> float:
    """The rate applied to the last rand you earn."""
    table = get_tax_year(tax_year)
    for bracket in table["brackets"]:
        top = bracket["to"]
        if top is None or taxable_income <= top:
            return bracket["rate"]
    return table["brackets"][-1]["rate"]


def medical_credit(monthly_credit: float, members: int, tax_year: str) -> float:
    """
    The medical scheme fees tax credit for one month.

    It is a REBATE against the tax, and it is the higher of the
    tabulated credit and what the employee actually pays for their own
    membership. `members` counts everyone on the scheme, including the
    employee.
    """
    table = get_tax_year(tax_year)
    rates = table["medical_credit"]
    if monthly_credit < 0:
        raise ValueError("The medical credit cannot be negative.")
    if members < 1:
        raise ValueError("There has to be at least one member on the scheme.")

    credit = max(rates["member"], monthly_credit)
    if members >= 2:
        credit += rates["first_dependent"]
    if members > 2:
        credit += (members - 2) * rates["additional_dependent"]
    return credit
