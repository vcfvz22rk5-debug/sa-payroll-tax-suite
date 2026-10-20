"""
tax_tables.py - all the SARS rates, brackets and rebates.

This file is DATA ONLY (no calculations happen here).

Source (checked 20 October 2026):
  https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/

Two tax years are included:
  "2026" = 1 March 2025 - 28 February 2026   (year just ended)
  "2027" = 1 March 2026 - 28 February 2027   (current year)
"""

TAX_YEARS = {
    # ------------------------------------------------------------------
    # 2026 TAX YEAR: brackets unchanged from the 2024 and 2025 years
    # (SARS: "12 March 2025 - No changes")
    # ------------------------------------------------------------------
    "2026": {
        "label": "2026 tax year (1 Mar 2025 - 28 Feb 2026)",
        # How to read a bracket, using SARS wording:
        #   "R42 678 + 26% of taxable income above R237 100"
        #   from     = 237 100  (the "above" amount)
        #   rate     = 0.26
        #   base_tax = 42 678   (tax already earned on everything below)
        # The tax formula for this bracket is:
        #   tax = base_tax + rate * (taxable income - from)
        "brackets": [
            {"from": 0,         "to": 237_100,   "rate": 0.18, "base_tax": 0},
            {"from": 237_100,   "to": 370_500,   "rate": 0.26, "base_tax": 42_678},
            {"from": 370_500,   "to": 512_800,   "rate": 0.31, "base_tax": 77_362},
            {"from": 512_800,   "to": 673_000,   "rate": 0.36, "base_tax": 121_475},
            {"from": 673_000,   "to": 857_900,   "rate": 0.39, "base_tax": 179_147},
            {"from": 857_900,   "to": 1_817_000, "rate": 0.41, "base_tax": 251_258},
            {"from": 1_817_000, "to": None,      "rate": 0.45, "base_tax": 644_489},
        ],
        # Rebates are deducted AFTER the slab tax (they are a credit
        # against the tax, not an exemption from income).
        # The secondary and tertiary amounts are ADDITIONS to the primary.
        #   under 65 -> primary only
        #   65-74    -> primary + secondary
        #   75+      -> primary + secondary + tertiary
        "rebates": {"primary": 17_235, "secondary": 9_444, "tertiary": 3_145},
        # Medical scheme fees tax credit, per month (section 6 of the
        # Income Tax Act). "member" is the taxpayer, "first_dependent"
        # is the spouse, "additional_dependent" is every dependant
        # after the first one.
        "medical_credit": {
            "member": 364,
            "first_dependent": 364,
            "additional_dependent": 246,
        },
    },
    # ------------------------------------------------------------------
    # 2027 TAX YEAR: new brackets announced 25 February 2026
    # ------------------------------------------------------------------
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
            "member": 376,
            "first_dependent": 376,
            "additional_dependent": 254,
        },
    },
}


def get_tax_year(tax_year):
    """Return the SARS table for a tax year (e.g. get_tax_year("2027"))."""
    key = str(tax_year).strip()
    if key not in TAX_YEARS:
        raise ValueError(
            f"Unknown tax year {tax_year!r}. Choose one of: {', '.join(TAX_YEARS)}"
        )
    return TAX_YEARS[key]


def marginal_rate(taxable_income, tax_year):
    """The tax rate applied to the LAST rand you earn (your top slab)."""
    table = get_tax_year(tax_year)
    for bracket in table["brackets"]:
        top = bracket["to"]
        if top is None or taxable_income <= top:
            return bracket["rate"]
    return table["brackets"][-1]["rate"]  # safety net (never really reached)


def medical_credit(monthly_credit, dependants, tax_year):
    """
    The medical scheme fees tax credit for one month.

    The credit is a REBATE, not a deduction from income: it reduces the
    tax you pay, and it is the HIGHER of
        (a) the tabulated credit for the members of the scheme, and
        (b) the actual contribution you paid.

    monthly_credit : what YOU pay per month for YOUR OWN membership
    dependants     : how many people are on the scheme, including you
    """
    table = get_tax_year(tax_year)
    rates = table["medical_credit"]

    if monthly_credit < 0:
        raise ValueError("The medical credit cannot be negative.")
    if dependants < 1:
        raise ValueError("There has to be at least one member on the scheme.")

    # Your own membership: the tabulated amount, or what you actually
    # pay if that is more.
    credit = max(rates["member"], monthly_credit)

    # The spouse is the "first dependent", everyone after that is an
    # "additional dependent". Their own contributions are assumed to be
    # at the tabulated amount, because we are not told what they pay.
    if dependants >= 2:
        credit += rates["first_dependent"]
    if dependants > 2:
        credit += (dependants - 2) * rates["additional_dependent"]

    return credit

