# South African Salary, Tax & Payroll Suite

Three tools in one repository, built as a portfolio project that combines
**accounting knowledge** with **practical coding skills**.

| Project | What it is | Run it with |
|---|---|---|
| [`payroll-suite/`](payroll-suite/) | **The flagship.** A payroll and SARS compliance system: payslips, the EMP201, IRP5 certificates, a SQLite database and a dashboard — pure standard library | `cd payroll-suite && python3 -m payroll_suite.cli serve` |
| `cli.py` | What **one employee** pays: PAYE, UIF, net pay | `python3 cli.py` |
| `cli_employer.py` | What a **business** owes SARS: VAT, SDL, UIF, the EMP201 | `python3 cli_employer.py` |

> 💻 **Portfolio:** these projects are featured on my portfolio site, which
> also has live browser versions of the engines.
> See [`portfolio/`](portfolio/) — or open `portfolio/index.html` directly.

---

## The payroll suite (the big one)

A payroll system for a small South African business, written with nothing
but the Python standard library.

```bash
cd payroll-suite
python3 -m payroll_suite.cli init          # database + demo staff
python3 -m payroll_suite.cli payrun --month 2026-10
python3 -m payroll_suite.cli emp201 --month 2026-10
python3 -m payroll_suite.cli serve          # dashboard on localhost:8000
```

- **The SARS annualised method** — the month's taxable income is annualised,
  taxed, and divided by twelve, the way a real payroll does it
- **A year-end reconciliation** that works out what an employee was really
  taxed for the year and what the employer owes them back
- Overtime at 1.5x and 2x, bonuses, commission, fringe benefits and leave
- Section 11F pension caps, UIF ceilings, SDL exemptions, commission earners
- **EMP201, EMP501 and IRP5** certificates, and a deadline calendar that
  knows the 7th of the month is sometimes a Saturday
- A **SQLite database**, a **JSON API** and a dashboard with hand-drawn SVG charts
- **148 checks** in the test suite

Full details in [`payroll-suite/README.md`](payroll-suite/README.md).

---

## The employee tool

- Calculates annual income tax using SARS progressive slab rates
  (2026 and 2027 tax years)
- Applies primary, secondary (65+) and tertiary (75+) rebates
- Applies the **medical scheme fees tax credit** (a rebate against the tax)
- Works out monthly PAYE (annual tax ÷ 12)
- Calculates UIF — 1% employee + 1% employer, correctly capped at
  R17,712 monthly earnings
- Applies retirement/RA deductions with the section 11F limit
  (27.5% of salary, max R350,000 per year)
- Shows **effective tax rate** and **marginal (top slab) rate**
- Prints a clean payslip-style report

## What the employer tool does

- **VAT**: output tax less input tax at 15%, and whether you are
  registered (compulsory above R2.3m, voluntary above R120,000)
- **VAT201**: the six bi-monthly periods, each with its real due date
  (the 25th, or the last business day of the following month on eFiling)
- **SDL**: 1% of the leviable amount, with the R500,000 annual-payroll
  exemption
- **Batch payroll**: reads a whole team from a CSV and produces a
  payslip for each one
- **EMP201**: the monthly declaration — PAYE, UIF and SDL — and the
  date it is due by (the 7th, or the last business day before it)

## And a small module for interest & dividends

`other_income.py` handles the two bits of income that behave differently:

- the **interest exemption** (R23,800 under 65 / R34,500 at 65+)
- the **20% dividends withholding tax**

---

## Sample output

```
==================================================================
  SOUTH AFRICAN SALARY & TAX ESTIMATE
  2027 tax year (1 Mar 2026 - 28 Feb 2027)
==================================================================
  Gross salary (monthly) ............          R 30,000.00
  Annualised gross (x 12) ...........         R 360,000.00
  Less: retirement/RA deduction .....       (R18,000.00)
------------------------------------------------------------------
  TAXABLE INCOME (annual) ...........         R 342,000.00
  Tax at SARS slab rates ............          R 69,312.00
  Less: primary rebate ......                 (R17,820.00)
  Less: medical tax credit .........          (R18,912.00)
------------------------------------------------------------------
  ANNUAL TAX (PAYE basis) ...........          R 32,580.00
  Monthly PAYE (annual / 12) .........          R 2,715.00

  UIF employee 1% on R17,712.00 (capped)...      R 177.12
  UIF employer 1% (business cost) ...           R 177.12
------------------------------------------------------------------
  MONTHLY DEDUCTIONS
  Retirement / RA .....................       (R1,500.00)
  PAYE ................................       (R2,715.00)
  UIF employee 1% ....................          (R177.12)
==================================================================
  NET MONTHLY PAY ...................         R 25,607.88
  Total monthly deductions ..........          R 4,392.12
  Effective tax rate: 9.0%   Marginal rate (top slab): 26%
==================================================================
```

And the employer side:

```
==================================================================
  PAYROLL RUN
  5 employees | 2027 tax year (1 Mar 2026 - 28 Feb 2027)
==================================================================
  NAME                        GROSS        PAYE       UIF       SDL          NET
==================================================================
  Thandi Mokoena          32,000.00    3,235.00    177.12    305.00    27,087.88
  Sipho Ndlovu            18,500.00    1,045.00    177.12    185.00    17,277.88
  Fatima Adams            62,000.00   11,662.08    177.12    590.00    47,160.80
  Johan van Wyk           14,500.00    1,125.00    145.00    145.00    13,230.00
  Nomsa Dlamini           95,000.00   24,444.00    177.12    900.00    65,378.88
==================================================================
  Total gross ............................            R 222,000.00
  Total PAYE withheld ....................             R 41,511.08
  Total UIF (employee) ...................                R 853.48
  Total UIF (employer) ...................                R 853.48
  Total SDL (employer cost) ..............              R 2,125.00
  Total NET paid to employees ............            R 170,135.44
==================================================================
```

## How to run it

You need Python 3 (free from [python.org](https://python.org)).

```bash
# 1. Calculate some tax
python3 cli.py

# 2. Run the employer-side tool
python3 cli_employer.py

# 3. Run the test suite (proves the maths matches SARS figures)
python3 tests/test_paye.py
python3 tests/test_vat.py
python3 tests/test_payroll.py

# 4. The payroll suite's own tests
cd payroll-suite && python3 tests/run_all.py
```

## Project structure

```
sa-salary-tax-calculator/
├── payroll-suite/          the payroll & compliance system (see its own README)
├── config.py               Settings: UIF ceiling/rates, SDL, VAT thresholds, s11F limits
├── tax_tables.py           SARS data only: brackets, rates, rebates and medical credits
├── paye.py                 The engine: slab tax, rebates, medical credit, monthly PAYE
├── uif.py                  UIF employee + employer contributions with the earnings cap
├── other_income.py         Interest exemption and the dividends withholding tax
├── vat.py                  The 15% engine, the VAT201 periods and their deadlines
├── payroll.py              Payslips, a batch payroll run from CSV, SDL and the EMP201
├── report.py               The shared terminal report formatting
├── cli.py                  The interactive employee programme you see and use
├── cli_employer.py         The interactive employer programme (VAT, payroll, EMP201)
├── data/employees.csv      The five-employee demo payroll
├── tests/                  114 hand-calculated checks that prove the maths
└── portfolio/              The portfolio website
```

## The CSV format

`data/employees.csv` is the demo payroll. Only three columns are
required — `name`, `gross_monthly`, `age`:

```csv
name,gross_monthly,age,ra_monthly,medical_monthly,medical_dependants
Thandi Mokoena,32000,34,1500,1200,2
```

- `ra_monthly` — your own pension or provident fund contribution
- `medical_monthly` — your own medical scheme contribution
- `medical_dependants` — how many people are on the scheme, including you

## Data sources

- [SARS — Rates of tax for individuals](https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/)
- [SARS — Interest and dividends](https://www.sars.gov.za/tax-rates/income-tax/interest-and-dividends/)
- [SARS — Value-Added Tax](https://www.sars.gov.za/types-of-tax/value-added-tax/) (thresholds raised 1 April 2026)
- [SARS — Other taxes (SDL)](https://www.sars.gov.za/tax-rates/other-taxes/)
- [SARS — EMP201](https://www.sars.gov.za/types-of-tax/pay-as-you-earn/completing-the-monthly-employer-declaration-emp201/)
- UIF earnings threshold (`config.py`) — confirm at [uif.gov.za](https://www.uif.gov.za/)

## Disclaimer

This is a study/portfolio tool, **not an official SARS payscale**. Real payroll
uses the SARS payscale with its own rounding and annualisation rules, and the
tool has no public-holiday calendar. Always verify results against
sars.gov.za.

---

*Built by [Your Name] — BCom Accounting student, South Africa*
