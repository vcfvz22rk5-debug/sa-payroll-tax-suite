"""
config.py - the "settings" file for the calculator.

Every number that might change from year to year, or that comes from
outside SARS (like UIF), lives HERE so you ever only update ONE place.

Sources (checked 20 October 2026):
  UIF  - https://www.sars.gov.za/types-of-tax/unemployment-insurance-fund/
  SDL  - https://www.sars.gov.za/tax-rates/other-taxes/
  VAT  - https://www.sars.gov.za/types-of-tax/value-added-tax/
  s11F - Income Tax Act 58 of 1962, section 11F
"""

# ----------------------------------------------------------------------
# UIF (Unemployment Insurance Fund)
# Source: UIF Act / Department of Employment and Labour
#
# The employer deducts 1% from the employee and adds 1% of its own.
# The 1% is only calculated on salary up to the monthly threshold below,
# so the most an employee can pay is 1% x threshold = R177.12.
#
# IMPORTANT: This ceiling is updated by the Minister from time to time.
# Check the current figure at https://www.uif.gov.za/ before relying on
# this calculator for real payroll work.
# ----------------------------------------------------------------------
UIF_MONTHLY_THRESHOLD = 17_712.00   # max monthly salary UIF is calculated on
UIF_EMPLOYEE_RATE = 0.01            # 1% deducted from the employee
UIF_EMPLOYER_RATE = 0.01            # 1% contributed by the employer

# ----------------------------------------------------------------------
# SDL (Skills Development Levy)
# Source: Skills Development Levies Act / SARS
#
# The levy is a BUSINESS cost - the employer may not deduct it from the
# employee's salary. It is 1% of the leviable amount, which is
# remuneration AFTER the allowable deductions (pension, RAF, donations).
#
# Employers with a total annual remuneration below R500 000 are exempt.
# ----------------------------------------------------------------------
SDL_RATE = 0.01                     # 1% of the leviable amount
SDL_ANNUAL_PAYROLL_EXEMPTION = 500_000.00   # annual payroll below this = no SDL

# ----------------------------------------------------------------------
# Value-Added Tax (VAT)
# Source: https://www.sars.gov.za/types-of-tax/value-added-tax/
#
# The standard rate is 15%. Registration thresholds were raised in the
# 2026 Budget with effect from 1 April 2026:
#   compulsory  R1 000 000  ->  R2 300 000 per annum
#   voluntary   R50 000    ->  R120 000 per annum
# ----------------------------------------------------------------------
VAT_RATE = 0.15                              # standard rate
VAT_COMPULSORY_THRESHOLD = 2_300_000.00      # must register above this turnover
VAT_VOLUNTARY_THRESHOLD = 120_000.00         # may register voluntarily above this
VAT_CATEGORY_C_THRESHOLD = 30_000_000.00     # above this: monthly VAT periods

# A VAT201 for a bi-monthly period is due on the 25th of the month that
# follows the period end (manual submission). Filed and paid on eFiling
# it is due on the last business day of that same month.
VAT_MANUAL_DUE_DAY = 25

# ----------------------------------------------------------------------
# Employment taxes are declared monthly on the EMP201 and paid over by
# the 7th of the month that follows. If the 7th falls on a weekend or
# public holiday, the last business day before it is used instead.
# ----------------------------------------------------------------------
EMP201_DUE_DAY = 7

# ----------------------------------------------------------------------
# Retirement fund deductions (section 11F of the Income Tax Act)
# Money you put into a pension/provident fund or retirement annuity is
# deducted from your income BEFORE tax - but only up to these limits.
# ----------------------------------------------------------------------
RA_MAX_PERCENT_OF_SALARY = 0.275    # 27.5% of remuneration
RA_MAX_ANNUAL_AMOUNT = 350_000.00   # and never more than R350 000 per year

# ----------------------------------------------------------------------
# Interest & dividends
# Source: https://www.sars.gov.za/tax-rates/income-tax/interest-and-dividends/
# ----------------------------------------------------------------------
INTEREST_EXEMPTION_UNDER_65 = 23_800.00   # per annum, South African interest
INTEREST_EXEMPTION_65_PLUS = 34_500.00    # per annum, 65 and older
DIVIDENDS_TAX_RATE = 0.20                # final tax withheld at source

# Which tax year to use if the user does not pick one
DEFAULT_TAX_YEAR = "2027"
