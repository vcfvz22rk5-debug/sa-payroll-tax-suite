"""
paye.py - the calculation engine: annual tax and monthly PAYE.

The SARS logic, in accounting terms:
  1. Start with taxable income for the YEAR.
  2. Apply the progressive slab rates       -> "tax before rebates".
  3. Subtract the rebates for the age group -> "annual tax".
  4. Monthly PAYE = annual tax / 12.

Note: a real employer uses the SARS payscale (which does a slightly
smarter "annualised" calculation month by month). For a full-year,
constant salary the two agree, which is why this method is used here.
"""

from tax_tables import get_tax_year, marginal_rate


def calculate_annual_tax(taxable_income, age=30, tax_year="2027",
                         medical_credit_annual=0.0):
    """
    Work out the total tax for the YEAR.

    taxable_income       : annual income after allowable deductions (e.g. RA)
    age                  : age at 28 February of that tax year (SARS rule)
    tax_year             : "2026" or "2027"
    medical_credit_annual: the medical scheme fees tax credit for the year,
                            already worked out by medical_credit() in
                            tax_tables.py. 0 if the taxpayer is not on a
                            medical scheme.
    """
    if taxable_income < 0:
        raise ValueError("Taxable income cannot be negative.")
    if age < 0 or age > 130:
        raise ValueError("Please enter a realistic age (0 - 130).")
    if medical_credit_annual < 0:
        raise ValueError("The medical tax credit cannot be negative.")

    table = get_tax_year(tax_year)

    # --- STEP 1: slab ("progressive") tax -----------------------------
    tax_before_rebates = 0.0
    for bracket in table["brackets"]:
        top = bracket["to"]
        # The last bracket has top = None (meaning "and above")
        if top is None or taxable_income <= top:
            tax_before_rebates = (
                bracket["base_tax"]
                + bracket["rate"] * (taxable_income - bracket["from"])
            )
            break

    # --- STEP 2: rebates, which depend on age -------------------------
    rebate = table["rebates"]["primary"]          # everyone gets this
    if age >= 65:
        rebate += table["rebates"]["secondary"]   # 65 and older
    if age >= 75:
        rebate += table["rebates"]["tertiary"]    # 75 and older

    # --- STEP 3: the medical tax credit is also a rebate --------------
    # It is deducted from the tax AFTER the age rebates, and it can
    # never push the tax below zero.
    rebate += medical_credit_annual

    # Tax can never be negative (if income is below the threshold the
    # rebate simply wipes the tax out to zero).
    return max(0.0, tax_before_rebates - rebate)


def calculate_paye_monthly(annual_tax):
    """Employers deduct PAYE monthly = annual tax divided by 12."""
    return annual_tax / 12.0


def effective_rate(annual_tax, annual_gross):
    """The % of your TOTAL income that goes to tax (accountants like this)."""
    if annual_gross <= 0:
        return 0.0
    return annual_tax / annual_gross
