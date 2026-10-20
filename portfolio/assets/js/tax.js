/* ═══════════════════════════════════════════════════════════════════
   tax.js — the PAYE engine, ported from the Python project
   ───────────────────────────────────────────────────────────────────
   This is a faithful JavaScript translation of:
     tax_tables.py  (data only)
     paye.py        (slab tax + rebates)
     uif.py         (UIF employee / employer)
     config.py      (UIF ceiling, s11F limits)

   Source: https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/

   If you change the numbers here, change them in the Python project
   too — and add a test on both sides.
   ═══════════════════════════════════════════════════════════════════ */

const Tax = (() => {
  "use strict";

  /* ── SARS TAX TABLES (data only) ───────────────────────────────── */
  const TAX_YEARS = {
    "2026": {
      label: "2026 tax year (1 Mar 2025 - 28 Feb 2026)",
      brackets: [
        { from: 0,         to: 237_100,   rate: 0.18, base_tax: 0 },
        { from: 237_100,   to: 370_500,   rate: 0.26, base_tax: 42_678 },
        { from: 370_500,   to: 512_800,   rate: 0.31, base_tax: 77_362 },
        { from: 512_800,   to: 673_000,   rate: 0.36, base_tax: 121_475 },
        { from: 673_000,   to: 857_900,   rate: 0.39, base_tax: 179_147 },
        { from: 857_900,   to: 1_817_000, rate: 0.41, base_tax: 251_258 },
        { from: 1_817_000, to: null,      rate: 0.45, base_tax: 644_489 },
      ],
      rebates: { primary: 17_235, secondary: 9_444, tertiary: 3_145 },
      // Medical scheme fees tax credit, per month.
      medical_credit: { member: 364, first_dependent: 364, additional_dependent: 246 },
    },
    "2027": {
      label: "2027 tax year (1 Mar 2026 - 28 Feb 2027)",
      brackets: [
        { from: 0,         to: 245_100,   rate: 0.18, base_tax: 0 },
        { from: 245_100,   to: 383_100,   rate: 0.26, base_tax: 44_118 },
        { from: 383_100,   to: 530_200,   rate: 0.31, base_tax: 79_998 },
        { from: 530_200,   to: 695_800,   rate: 0.36, base_tax: 125_599 },
        { from: 695_800,   to: 887_000,   rate: 0.39, base_tax: 185_215 },
        { from: 887_000,   to: 1_878_600, rate: 0.41, base_tax: 259_783 },
        { from: 1_878_600, to: null,      rate: 0.45, base_tax: 666_339 },
      ],
      rebates: { primary: 17_820, secondary: 9_765, tertiary: 3_249 },
      medical_credit: { member: 376, first_dependent: 376, additional_dependent: 254 },
    },
  };

  /* ── CONFIG ────────────────────────────────────────────────────── */
  const UIF_MONTHLY_THRESHOLD = 17_712.00;
  const UIF_EMPLOYEE_RATE = 0.01;
  const UIF_EMPLOYER_RATE = 0.01;
  const RA_MAX_PERCENT_OF_SALARY = 0.275;
  const RA_MAX_ANNUAL_AMOUNT = 350_000.00;
  const MONTHS = 12;

  /* ── HELPERS ───────────────────────────────────────────────────── */
  const r2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;
  const clamp = (n, lo, hi) => Math.min(Math.max(n, lo), hi);

  function getTaxYear(year) {
    const key = String(year).trim();
    if (!TAX_YEARS[key]) {
      throw new Error(`Unknown tax year "${year}". Choose one of: ${Object.keys(TAX_YEARS).join(", ")}`);
    }
    return TAX_YEARS[key];
  }

  /* ── CORE CALCULATIONS (mirror paye.py / uif.py) ───────────────── */
  function slabTax(taxableIncome, year) {
    const table = getTaxYear(year);
    for (const b of table.brackets) {
      if (b.to === null || taxableIncome <= b.to) {
        return {
          amount: b.base_tax + b.rate * (taxableIncome - b.from),
          bracket: b,
        };
      }
    }
    const last = table.brackets[table.brackets.length - 1];
    return { amount: last.base_tax + last.rate * (taxableIncome - last.from), bracket: last };
  }

  function rebateFor(age, year) {
    const table = getTaxYear(year);
    let rebate = table.rebates.primary;
    if (age >= 65) rebate += table.rebates.secondary;
    if (age >= 75) rebate += table.rebates.tertiary;
    return rebate;
  }

  function rebateName(age) {
    if (age >= 75) return "primary + secondary + tertiary rebate";
    if (age >= 65) return "primary + secondary rebate";
    return "primary rebate";
  }

  /**
   * The medical scheme fees tax credit for one month.
   * It is a REBATE against the tax, and it is the higher of the
   * tabulated credit and what you actually pay for your own membership.
   * dependants = how many people are on the scheme, including you.
   */
  function medicalCredit(monthlyCredit, dependants, year) {
    const table = getTaxYear(year);
    const rates = table.medical_credit;
    if (monthlyCredit < 0) throw new Error("The medical credit cannot be negative.");
    if (dependants < 1) throw new Error("There has to be at least one member on the scheme.");

    let credit = Math.max(rates.member, monthlyCredit);
    if (dependants >= 2) credit += rates.first_dependent;
    if (dependants > 2) credit += (dependants - 2) * rates.additional_dependent;
    return credit;
  }

  function calculateAnnualTax(taxableIncome, age = 30, year = "2027", medicalCreditAnnual = 0) {
    if (taxableIncome < 0) throw new Error("Taxable income cannot be negative.");
    if (age < 0 || age > 130) throw new Error("Please enter a realistic age (0 - 130).");
    if (medicalCreditAnnual < 0) throw new Error("The medical tax credit cannot be negative.");
    const before = slabTax(taxableIncome, year).amount;
    return Math.max(0, before - rebateFor(age, year) - medicalCreditAnnual);
  }

  function calculateUIF(grossMonthly) {
    if (grossMonthly < 0) throw new Error("Salary cannot be negative.");
    const base = Math.min(grossMonthly, UIF_MONTHLY_THRESHOLD);
    return {
      base: r2(base),
      employee: r2(base * UIF_EMPLOYEE_RATE),
      employer: r2(base * UIF_EMPLOYER_RATE),
    };
  }

  /** Section 11F: lowest of the actual contribution, 27.5% of salary, or R350 000. */
  function allowanceForRetirement(grossAnnual, monthlyContribution) {
    const annualContribution = monthlyContribution * MONTHS;
    const cap = Math.min(grossAnnual * RA_MAX_PERCENT_OF_SALARY, RA_MAX_ANNUAL_AMOUNT);
    return { allowed: r2(Math.min(annualContribution, cap)), cap: r2(cap) };
  }

  function marginalRate(taxableIncome, year) {
    const table = getTaxYear(year);
    for (const b of table.brackets) {
      if (b.to === null || taxableIncome <= b.to) return b.rate;
    }
    return table.brackets[table.brackets.length - 1].rate;
  }

  /**
   * The whole calculation in one call — this is what the UI consumes.
   * Mirrors the report printed by cli.py.
   */
  function calculate({ grossMonthly, age = 30, taxYear = "2027", raMonthly = 0,
                       medicalMonthly = 0, medicalDependants = 0 }) {
    const gross = clamp(Number(grossMonthly) || 0, 0, 99_999_999);
    const table = getTaxYear(taxYear);

    const grossAnnual = r2(gross * MONTHS);
    const ra = allowanceForRetirement(grossAnnual, Math.max(0, Number(raMonthly) || 0));
    const taxableIncome = r2(grossAnnual - ra.allowed);

    // The medical scheme fees tax credit is a rebate against the tax.
    const creditMonthly =
      medicalMonthly > 0 && medicalDependants > 0
        ? r2(medicalCredit(medicalMonthly, medicalDependants, taxYear))
        : 0;
    const creditAnnual = r2(creditMonthly * MONTHS);

    const slab = slabTax(taxableIncome, taxYear);
    const taxBeforeRebates = r2(slab.amount);
    const rebate = rebateFor(age, taxYear);
    const annualTax = r2(Math.max(0, taxBeforeRebates - rebate - creditAnnual));
    const payeMonthly = r2(annualTax / MONTHS);

    const uif = calculateUIF(gross);
    const raMonthlyAllowed = r2(ra.allowed / MONTHS);

    const totalDeductions = r2(payeMonthly + uif.employee + raMonthlyAllowed);
    const netMonthly = r2(gross - totalDeductions);

    return {
      label: table.label,
      grossMonthly: gross,
      grossAnnual,
      raAnnual: ra.allowed,
      raCap: ra.cap,
      raMonthlyAllowed,
      raCapped: ra.allowed < r2(raMonthly * MONTHS),
      taxableIncome,
      taxBeforeRebates,
      rebate,
      rebateName: rebateName(age),
      medicalCreditMonthly: creditMonthly,
      medicalCreditAnnual: creditAnnual,
      annualTax,
      payeMonthly,
      uif,
      netMonthly,
      totalDeductions,
      effectiveRate: grossAnnual > 0 ? annualTax / grossAnnual : 0,
      marginalRate: marginalRate(taxableIncome, taxYear),
      bracket: slab.bracket,
      brackets: table.brackets,
    };
  }

  /* ── SELF TEST ───────────────────────────────────────────────────
     The same hand-checked cases as tests/test_paye.py.
     Open the browser console and run Tax.selfTest() to confirm the
     JavaScript port still agrees with the Python.                 */
  function selfTest() {
    const cases = [
      ["2026: income at the threshold pays no tax", () => calculateAnnualTax(95_750, 30, "2026"), 0],
      ["2027: income at the threshold pays no tax", () => calculateAnnualTax(99_000, 30, "2027"), 0],
      ["2026: R360 000 salary -> R57 397 tax",      () => calculateAnnualTax(360_000, 30, "2026"), 57_397],
      ["2027: R360 000 salary -> R56 172 tax",      () => calculateAnnualTax(360_000, 30, "2027"), 56_172],
      ["2026: age 70 gets primary + secondary",     () => calculateAnnualTax(200_000, 70, "2026"), 9_321],
      ["2027: top 45% bracket",                     () => calculateAnnualTax(2_000_000, 45, "2027"), 703_149],
      ["UIF on R30 000 is capped at R177.12",       () => calculateUIF(30_000).employee, 177.12],
      ["UIF on R10 000 is 1% = R100",               () => calculateUIF(10_000).employee, 100.00],
      ["Employer matches the UIF contribution",     () => calculateUIF(30_000).employer, 177.12],
      ["2027: medical credit for the taxpayer",      () => medicalCredit(0, 1, "2027"), 376],
      ["2027: medical credit for two members",      () => medicalCredit(0, 2, "2027"), 752],
      ["2027: medical credit cuts the tax",         () => calculateAnnualTax(360_000, 30, "2027", 4_512), 51_660],
    ];

    let passed = 0;
    for (const [name, fn, expected] of cases) {
      const actual = fn();
      const ok = Math.abs(actual - expected) <= 0.01;
      console.log(`${ok ? "  ok -" : "  FAIL -"} ${name}`);
      if (ok) passed++;
      else console.log(`         expected R${expected.toLocaleString("en-ZA", { minimumFractionDigits: 2 })}, got R${actual.toLocaleString("en-ZA", { minimumFractionDigits: 2 })}`);
    }
    console.log(`\n${passed}/${cases.length} checks passed.\n`);
    return passed === cases.length;
  }

  return {
    TAX_YEARS, getTaxYear, slabTax, rebateFor, rebateName, medicalCredit,
    calculateAnnualTax, calculateUIF, allowanceForRetirement,
    marginalRate, calculate, selfTest,
  };
})();
