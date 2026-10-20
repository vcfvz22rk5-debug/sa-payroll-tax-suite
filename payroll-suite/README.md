# Payroll Suite

A payroll and SARS compliance system for a small South African business.

It calculates payslips the way a real payroll does, keeps everything in
a database, produces the SARS forms an employer actually has to file, and
comes with a dashboard you can look at.

**Pure standard library.** No `pip install`, no Flask, no Node, no build
step. Clone it, run it, and it works.

```bash
python3 -m payroll_suite.cli init      # create the database and the demo staff
python3 -m payroll_suite.cli payrun --month 2026-10
python3 -m payroll_suite.cli serve      # the dashboard on http://localhost:8000
```

---

## What it does

### The payroll run

A payslip for every employee, every month, with the things that make a
real payslip complicated:

| | |
|---|---|
| **Earnings** | basic salary, overtime, bonuses, commission, fringe benefits, leave pay, other allowances |
| **Overtime** | 1.5x for the first 45 hours a month, 2x beyond that, 2x for Sundays and public holidays |
| **Unpaid leave** | comes off the basic salary at the daily rate |
| **Retirement fund** | capped by section 11F: 27.5% of the remuneration, never more than R350 000 a year |
| **Medical scheme** | the medical tax credit is a rebate against the tax, not a deduction |
| **UIF** | 1% each side, capped at R17 712 a month, and commission earners are excluded |
| **SDL** | 1% of the leviable amount, and employers under R500 000 a year pay none |

### The tax — the annualised method

Because SARS's brackets are built around a *year* of income, a month
cannot be taxed on its own. This is what the engine does:

```
1. taxable income for the month = gross remuneration - the s11F pension
2. annualised taxable income    = that x 12
3. tax at the SARS slab rates
4. less the rebates for the employee's age
5. less the medical scheme fees tax credit
6. monthly PAYE                 = that tax / 12, rounded to the nearest rand
```

It is called annualising because it smooths the tax: a December bonus
does not push somebody into a higher bracket for the whole year, and a
month without overtime does not drop them into a lower one.

The consequence worth knowing: somebody who joins in November is taxed as
if they were going to earn a full year's salary, so the employer
over-deducts for them. That difference is picked up at the end of the
year by the **year-end reconciliation**, which is the same "tax on a
period basis" adjustment a real payroll makes on the last payslip.

```bash
# What the employee was actually taxed for the year, against what was taken
python3 -m payroll_suite.cli irp5 --year 2027
```

### The compliance side

| Form | What it is | When |
|---|---|---|
| **EMP201** | the monthly declaration: PAYE, UIF and SDL | by the 7th of the month that follows |
| **EMP501** | the annual reconciliation: the EMP201s against the IRP5 certificates | April to May |
| **IRP5** | the employee's tax certificate for the year | within 60 days of the year end |
| **Calendar** | every deadline: EMP201, VAT201, IRP5, EMP501, provisional tax | — |

The deadlines know about weekends. If the 7th of the month falls on a
Saturday, the deadline is the Friday before.

---

## The commands

```bash
payroll-suite init                          # database + demo staff
payroll-suite add-employee --name "..." --age 34 --salary 32000
payroll-suite list                          # who is on the payroll
payroll-suite payrun --month 2026-10        # run the payroll
payroll-suite payslips --period 2026-10     # the payslips
payroll-suite emp201 --month 2026-10        # the monthly declaration
payroll-suite irp5 --year 2027              # the tax certificates
payroll-suite emp501 --year 2027            # the annual reconciliation
payroll-suite deadlines --year 2027          # the employer's calendar
payroll-suite export --period 2026-10 --format csv --output out.csv
payroll-suite serve                         # the dashboard
```

Every command takes `--format csv` or `----format json` where it makes
sense, so the output can go straight into a spreadsheet or an upload.

Without installing it, run the same commands with:

```bash
python3 -m payroll_suite.cli <command>
```

---

## The dashboard

`payroll-suite serve` starts a small web server — the standard
library's `http.server`, nothing else — and opens on
<http://localhost:8000>.

It shows:

- the **cost to company** for the month, and how it is split
- a **chart** of the payroll cost month by month, drawn as hand-made SVG
- the **EMP201** summary and the date it is due
- the **next deadlines** on the calendar
- every **payslip**, with a drawer that opens the full calculation
- the **team**, with what each person costs to employ

The API it is built on:

| Endpoint | Returns |
|---|---|
| `GET /api/overview` | the KPIs, the trend and the deadlines |
| `GET /api/employees` | everybody on the payroll |
| `GET /api/payslips?period=2026-10` | the payslips for a month |
| `GET /api/emp201?period=2026-10` | the monthly declaration |
| `GET /api/deadlines?year=2027` | the calendar |
| `GET /api/irp5?year=2027` | the tax certificates |
| `GET /api/emp501?year=2027` | the annual reconciliation |
| `POST /api/run` | runs the payroll for a month |

---

## The data

Everything lives in one SQLite file (`data/payroll.db`), so the system
can be copied onto a USB stick and still have the employees, the
payslips and the declarations.

```
employees     the staff
pay_runs      one row per payroll month
payslips      one row per employee per month
meta          the schema version
```

The schema is created on first run and stamped with a version, so an old
database keeps working when the code moves on.

---

## Project structure

```
payroll-suite/
├── payroll_suite/
│   ├── tax_tables.py   the SARS rates, in one place
│   ├── engine.py       the calculation engine - no database, no printing
│   ├── models.py       the dataclasses
│   ├── db.py           the SQLite layer
│   ├── compliance.py   EMP201, EMP501, IRP5 and the calendar
│   ├── reports.py      console reports, CSV and JSON exports
│   ├── server.py       the dashboard's web server and JSON API
│   ├── seed.py         the demo staff
│   └── cli.py          the command line application
├── web/                the dashboard (HTML, CSS and vanilla JS)
├── tests/              148 checks
├── data/               the SQLite file
└── pyproject.toml
```

The engine does not know about the database or about printing. That is
what makes it easy to test: 58 of the checks are the engine alone.

---

## The tests

```bash
python3 tests/run_all.py
```

| Suite | Checks | What it covers |
|---|---|---|
| `test_engine.py` | 58 | the tax, the pension cap, overtime, leave, the year-end reconciliation |
| `test_db.py` | 27 | storing and finding things, and surviving a restart |
| `test_compliance.py` | 41 | the EMP201, the IRP5, the EMP501 and the calendar |
| `test_api.py` | 22 | the JSON API, end to end over HTTP |

Every figure was worked out by hand from the SARS tables.

---

## The assumptions

Real payroll is more complicated than any study project can be. These
are the places where this one simplifies, and they are all deliberate:

- **The employer's medical contribution is not taxed as a fringe
  benefit.** It is treated as a tax-free benefit, which is what happens
  in practice for the majority of employees.
- **Travel allowances** are not modelled. The 80% business travel rule
  would be the first thing to add.
- **There is no public holiday calendar.** The deadlines know about
  weekends, but not about public holidays.
- **A bonus is taxed in the month it is paid**, on the annualised
  method. A proper system spreads a bonus over the year to avoid the
  bracket spike.
- **The year-end reconciliation** is calculated, but nothing puts the
  adjustment on a payslip for you yet.
- **SDL is calculated on the leviable amount** but the employer's
  annual payroll is taken from the payroll run rather than from a
  forecast of the next twelve months.

---

## Hosting it for free

The dashboard is a WSGI application, so it runs on any Python host. Point
the host at:

```python
from payroll_suite.wsgi import application
```

Set the database path with the `PAYROLL_DB` environment variable (or the
`PAYROLL_DB` variable in the host's settings) so it points at a folder
that persists.

**PythonAnywhere** is the easiest free option: Manual configuration →
Python 3.11 → set the working directory → paste the import above into the
WSGI file → Reload.

**Render** works too: build `pip install -e .`, start
`gunicorn payroll_suite.wsgi:application` (the `Procfile` already says so).
The free tier sleeps when idle and its filesystem is ephemeral, so the
database is rebuilt on every deploy.

More detail, and a checklist for the website, in
[`../DEPLOY.md`](../DEPLOY.md).

---

## Sources

- [SARS — Rates of tax for individuals](https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/)
- [SARS — EMP201](https://www.sars.gov.za/types-of-tax/pay-as-you-earn/completing-the-monthly-employer-declaration-emp201/)
- [SARS — Employer reconciliation](https://www.sars.gov.za/guide-to-the-employer-reconciliation-process/)
- [SARS — UIF](https://www.sars.gov.za/types-of-tax/unemployment-insurance-fund/)
- [SARS — SDL](https://www.sars.gov.za/tax-rates/other-taxes/)
- [SARS — VAT](https://www.sars.gov.za/types-of-tax/value-added-tax/)

---

## Disclaimer

This is a study project, **not a payroll system you can trust with
someone's salary**. It has not been through the kind of testing, legal
review and edge-case handling that a real product needs. Always check
the numbers against SARS and against a real payroll before using
anything here.

---

*Built by Ayanda Shongwe — BCom Accounting student, South Africa*
