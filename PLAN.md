# Project roadmap — 3 to 4 weeks

**Goal:** a polished, documented portfolio project that proves both
accounting knowledge and coding ability.

> The roadmap grew into three projects: the employee calculator, the
> employer-side VAT & payroll tool, and the **payroll suite** — a full
> payroll and SARS compliance system in `payroll-suite/`.

## Week 1 — Core PAYE engine ✅ (built 20 October 2026)

- [x] SARS 2026 & 2027 tax tables loaded (`tax_tables.py`)
- [x] Progressive slab-rate calculation
- [x] Primary/secondary/tertiary rebates by age
- [x] Monthly PAYE (annual ÷ 12)
- [x] UIF 1% + 1% with R17,712 earnings cap
- [x] Retirement/RA deduction with s11F limit (27.5% / R350,000)
- [x] Interactive terminal programme (`cli.py`)
- [x] Automated tests, all passing (`tests/test_paye.py`)
- [x] README with sample output

**Learned:** variables, functions, dictionaries, lists, loops, conditionals,
`try/except`, writing tests.

## Week 2 — More tax rules ✅

- [x] Medical tax credits (R376 pm first two members, R254 pm after — 2027)
- [x] Interest exemption (R23,800 under 65 / R34,500 65+)
- [x] Dividend exemption and 20% dividends withholding tax
- [x] Annual vs monthly PAYE: compared with the SARS payscale method
- [ ] Second income source / provisional tax (IRP6) estimate
- [x] Grew the test suite (21 checks in `tests/test_paye.py`)

## Week 3 — VAT & employer side ✅

- [x] VAT calculator: output VAT, input VAT, net VAT payable (15%)
- [x] VAT201 period summary (bi-monthly, with the real due dates)
- [x] EMP201 monthly employer declaration summary
- [x] Batch mode: calculate salaries for a list of employees (CSV)
- [x] Example data: a mini "payroll for 5 employees" demo
- [x] SDL at 1% of the leviable amount, with the R500 000 exemption
- [x] Interactive employer programme (`cli_employer.py`)

## Week 4 — Polish & publish

- [x] Clean up and comment all code for other people to read
- [x] Shared report formatting (`report.py`)
- [x] Full README: what it does, how to run it, the assumptions it makes
- [ ] Put it on GitHub (employers will look at this)
- [x] Portfolio website — a home for every project I build
      (`portfolio/` — static HTML/CSS/JS, no build step, deploys free to
      GitHub Pages)
- [x] Live browser version of the PAYE engine, running on the portfolio site
      (`portfolio/assets/js/tax.js` — same SARS tables, same maths, and it
      ships its own self-test: open the console and run `Tax.selfTest()`)
- [x] Live browser version of the VAT & payroll engine
      (`portfolio/assets/js/vat.js` — `Vat.selfTest()`)
- [x] Tabbed live demos: PAYE, VAT 201 and a payroll run on one page
- [x] Smoother site: custom eased scrolling, a scroll progress bar, a
      sliding nav indicator, fuzzy command-palette search
- [x] A performance mode that measures its own frame rate and switches the
      decoration off when the machine cannot keep up
- [ ] Optional: a short LinkedIn post explaining the project

## Later — the portfolio site

- [x] Add the VAT / payroll project to the portfolio as it ships
- [x] Add the payroll suite, with a case study section explaining the design
- [ ] Write a short case study for each project card
- [ ] A custom domain
- [ ] Screenshots of the terminal tool for the project cards

## Definition of done

- [x] A stranger can run it in under 5 minutes following the README
- [x] All tests pass (262 checks across four suites)
- [x] Every calculation traceable to a SARS source
- [x] Live demo you can show in an interview
