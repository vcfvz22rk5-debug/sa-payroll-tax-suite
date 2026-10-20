/* ═══════════════════════════════════════════════════════════════════
   vat.js — the employer-side engine, ported to the browser
   ───────────────────────────────────────────────────────────────────
   A faithful JavaScript translation of:
     vat.py        (the 15% engine, VAT201 periods, registration)
     payroll.py    (payslips, the payroll run, the EMP201)
     config.py     (the SDL, UIF and VAT thresholds)

   Sources:
     VAT    - https://www.sars.gov.za/types-of-tax/value-added-tax/
     EMP201 - https://www.sars.gov.za/types-of-tax/pay-as-you-earn/
     SDL    - https://www.sars.gov.za/tax-rates/other-taxes/

   If you change the numbers here, change them in the Python project
   too — and add a test on both sides.
   ═══════════════════════════════════════════════════════════════════ */

const Vat = (() => {
  "use strict";

  /* ── CONFIG ──────────────────────────────────────────────────────── */
  const VAT_RATE = 0.15;
  const VAT_COMPULSORY_THRESHOLD = 2_300_000.00;
  const VAT_VOLUNTARY_THRESHOLD = 120_000.00;
  const VAT_CATEGORY_C_THRESHOLD = 30_000_000.00;
  const VAT_MANUAL_DUE_DAY = 25;

  const SDL_RATE = 0.01;
  const SDL_ANNUAL_PAYROLL_EXEMPTION = 500_000.00;

  const UIF_MONTHLY_THRESHOLD = 17_712.00;
  const UIF_RATE = 0.01;
  const EMP201_DUE_DAY = 7;

  const MONTHS = 12;

  /* ── HELPERS ────────────────────────────────────────────────────── */
  const r2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;
  const clamp = (n, lo, hi) => Math.min(Math.max(n, lo), hi);
  const isWeekend = (d) => d.getDay() === 0 || d.getDay() === 6;

  const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  const MONTH_SHORT = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];

  const pad = (n) => String(n).padStart(2, "0");
  const fmtDate = (d) => `${pad(d.getDate())} ${MONTH_SHORT[d.getMonth()]} ${d.getFullYear()}`;
  const fmtLong = (d) => `${d.getDate()} ${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}`;

  const lastDayOfMonth = (year, month) => new Date(year, month + 1, 0).getDate();

  /* ── THE VAT CALCULATION ────────────────────────────────────────── */
  function calculateVat(taxableSupplies, taxablePurchases, rate = VAT_RATE) {
    if (taxableSupplies < 0) throw new Error("Taxable supplies cannot be negative.");
    if (taxablePurchases < 0) throw new Error("Taxable purchases cannot be negative.");

    const outputTax = r2(taxableSupplies * rate);
    const inputTax = r2(taxablePurchases * rate);
    const net = r2(outputTax - inputTax);

    return {
      taxableSupplies: r2(taxableSupplies),
      taxablePurchases: r2(taxablePurchases),
      vatRate: rate,
      outputTax,
      inputTax,
      netVat: net,
      amountPayable: Math.max(0, net),
      amountClaimable: Math.max(0, -net),
      isRefund: net < 0,
    };
  }

  /* ── THE VAT PERIODS ────────────────────────────────────────────── */
  function lastBusinessDay(year, month) {
    let day = lastDayOfMonth(year, month);
    while (isWeekend(new Date(year, month, day))) day -= 1;
    return new Date(year, month, day);
  }

  function addMonths(year, month, count) {
    const total = year * 12 + month + count;
    return { year: Math.floor(total / 12), month: total % 12 };
  }

  function vatPeriods(taxYear = "2027") {
    const year = parseInt(taxYear, 10);
    const base = year - 1;
    const periods = [];

    const push = (number, start, end) => {
      const due = addMonths(end.getFullYear(), end.getMonth(), 1);
      let manual = new Date(due.year, due.month, VAT_MANUAL_DUE_DAY);
      while (isWeekend(manual)) manual = new Date(manual.getFullYear(), manual.getMonth(), manual.getDate() - 1);
      periods.push({
        number,
        period: `P${number}`,
        start,
        end,
        label: `${fmtDate(start)} - ${fmtDate(end)}`,
        dueMonth: `${MONTH_NAMES[due.month]} ${due.year}`,
        dueManual: manual,
        dueEfiling: lastBusinessDay(due.year, due.month),
      });
    };

    [3, 5, 7, 9, 11].forEach((month, i) => {
      const start = new Date(base, month - 1, 1);
      const end = new Date(base, month, lastDayOfMonth(base, month));
      push(i + 1, start, end);
    });

    push(6, new Date(year, 0, 1), new Date(year, 1, lastDayOfMonth(year, 1)));

    return periods;
  }

  /* ── REGISTRATION ───────────────────────────────────────────────── */
  function registrationStatus(taxableSupplies) {
    if (taxableSupplies < 0) throw new Error("Taxable supplies cannot be negative.");
    const money = (n) => `R${n.toLocaleString("en-ZA")}`;

    if (taxableSupplies > VAT_COMPULSORY_THRESHOLD) {
      return {
        mustRegister: true,
        status: "Compulsory registration",
        detail:
          `Taxable supplies of ${money(taxableSupplies)} are above the ` +
          `${money(VAT_COMPULSORY_THRESHOLD)} threshold, so you must be registered for VAT.`,
      };
    }
    if (taxableSupplies > VAT_VOLUNTARY_THRESHOLD) {
      return {
        mustRegister: false,
        status: "Voluntary registration available",
        detail:
          `Taxable supplies of ${money(taxableSupplies)} are above the ` +
          `${money(VAT_VOLUNTARY_THRESHOLD)} voluntary threshold but below the compulsory ` +
          `${money(VAT_COMPULSORY_THRESHOLD)}, so you may register voluntarily.`,
      };
    }
    return {
      mustRegister: false,
      status: "Not required",
      detail:
        `Taxable supplies of ${money(taxableSupplies)} are below the ` +
        `${money(VAT_VOLUNTARY_THRESHOLD)} voluntary threshold.`,
    };
  }

  const vatCategory = (supplies) =>
    supplies > VAT_CATEGORY_C_THRESHOLD ? "C" : "A/B";

  /* ── SDL ────────────────────────────────────────────────────────── */
  function calculateSdl(leviableAmount, annualPayroll) {
    if (leviableAmount < 0) throw new Error("The leviable amount cannot be negative.");
    if (annualPayroll < 0) throw new Error("The annual payroll cannot be negative.");
    if (annualPayroll < SDL_ANNUAL_PAYROLL_EXEMPTION) return 0;
    return r2(leviableAmount * SDL_RATE);
  }

  /* ── ONE PAYSLIP ────────────────────────────────────────────────── */
  function calculatePayslip(employee, taxYear = "2027", annualPayroll = null) {
    const name = employee.name || "Unnamed";
    const grossMonthly = Math.max(0, Number(employee.grossMonthly) || 0);
    const age = Number(employee.age) || 30;
    const raMonthly = Math.max(0, Number(employee.raMonthly) || 0);
    const medicalMonthly = Math.max(0, Number(employee.medicalMonthly) || 0);
    const medicalDependants = Math.max(0, Number(employee.medicalDependants) || 0);

    const grossAnnual = r2(grossMonthly * MONTHS);

    // Section 11F: the lowest of the actual contribution, 27.5% of
    // salary, or R350 000 a year.
    const raCap = Math.min(grossAnnual * 0.275, 350_000);
    const raAllowed = r2(Math.min(raMonthly * MONTHS, raCap));
    const taxableIncome = r2(grossAnnual - raAllowed);

    // The medical scheme fees tax credit (a rebate against the tax).
    const rates = Tax.TAX_YEARS[taxYear]?.medical_credit;
    let creditMonthly = 0;
    if (rates && medicalMonthly > 0 && medicalDependants > 0) {
      creditMonthly = Math.max(rates.member, medicalMonthly);
      if (medicalDependants >= 2) creditMonthly += rates.first_dependent;
      if (medicalDependants > 2) creditMonthly += (medicalDependants - 2) * rates.additional_dependent;
    }
    const creditAnnual = r2(creditMonthly * MONTHS);

    const annualTax = r2(
      Tax.calculateAnnualTax(taxableIncome, age, taxYear, creditAnnual)
    );
    const payeMonthly = r2(annualTax / MONTHS);

    const uifBase = Math.min(grossMonthly, UIF_MONTHLY_THRESHOLD);
    const uifEmployee = r2(uifBase * UIF_RATE);
    const uifEmployer = r2(uifBase * UIF_RATE);

    const leviable = r2(grossMonthly - raAllowed / MONTHS);
    const sdl = calculateSdl(leviable, annualPayroll ?? grossAnnual);

    const totalDeductions = r2(payeMonthly + uifEmployee + r2(raAllowed / MONTHS));

    return {
      name,
      taxYear,
      grossMonthly,
      grossAnnual,
      raMonthly,
      raAllowedAnnual: raAllowed,
      raCapAnnual: r2(raCap),
      raCapped: raAllowed < r2(raMonthly * MONTHS),
      raMonthlyAllowed: r2(raAllowed / MONTHS),
      taxableIncome,
      medicalCreditMonthly: r2(creditMonthly),
      medicalCreditAnnual: creditAnnual,
      annualTax,
      payeMonthly,
      uifBase: r2(uifBase),
      uifEmployee,
      uifEmployer,
      sdl,
      leviableAmount: leviable,
      totalDeductions,
      netMonthly: r2(grossMonthly - totalDeductions),
      employerCost: r2(uifEmployer + sdl),
      effectiveRate: grossAnnual > 0 ? annualTax / grossAnnual : 0,
    };
  }

  /* ── A PAYROLL RUN ──────────────────────────────────────────────── */
  function runPayroll(employees, taxYear = "2027") {
    const annualPayroll = r2(
      employees.reduce((sum, e) => sum + (Number(e.grossMonthly) || 0) * MONTHS, 0)
    );
    const payslips = employees.map((e) => calculatePayslip(e, taxYear, annualPayroll));
    const sum = (key) => r2(payslips.reduce((t, p) => t + p[key], 0));

    return {
      taxYear,
      payslips,
      headCount: payslips.length,
      totalGross: sum("grossMonthly"),
      totalPaye: sum("payeMonthly"),
      totalUifEmployee: sum("uifEmployee"),
      totalUifEmployer: sum("uifEmployer"),
      totalSdl: sum("sdl"),
      totalNet: sum("netMonthly"),
      totalEmployerCost: sum("employerCost"),
      annualPayroll,
    };
  }

  /* ── THE EMP201 ─────────────────────────────────────────────────── */
  function emp201DueDate(payrollMonth) {
    const d = payrollMonth instanceof Date ? payrollMonth : new Date(payrollMonth);
    const next = addMonths(d.getFullYear(), d.getMonth(), 1);
    let due = new Date(next.year, next.month, EMP201_DUE_DAY);
    while (isWeekend(due)) {
      due = new Date(due.getFullYear(), due.getMonth(), due.getDate() - 1);
    }
    return due;
  }

  function emp201Summary(payroll, payrollMonth = null) {
    const payslips = payroll.payslips || payroll;
    const sum = (key) => r2(payslips.reduce((t, p) => t + p[key], 0));

    const summary = {
      headCount: payslips.length,
      totalRemuneration: sum("grossMonthly"),
      paye: sum("payeMonthly"),
      uifEmployee: sum("uifEmployee"),
      uifEmployer: sum("uifEmployer"),
      uifTotal: r2(sum("uifEmployee") + sum("uifEmployer")),
      sdl: sum("sdl"),
      totalNetPaid: sum("netMonthly"),
    };
    summary.totalLiability = r2(summary.paye + summary.uifTotal + summary.sdl);

    if (payrollMonth) {
      summary.payrollMonth = payrollMonth;
      summary.dueDate = emp201DueDate(payrollMonth);
    }
    return summary;
  }

  /* ── THE DEMO PAYROLL ─────────────────────────────────────────────
     The same five employees as data/employees.csv in the Python
     project, so the browser and the terminal agree.                */
  const DEMO_EMPLOYEES = [
    { name: "Thandi Mokoena", grossMonthly: 32000, age: 34, raMonthly: 1500, medicalMonthly: 1200, medicalDependants: 2 },
    { name: "Sipho Ndlovu",    grossMonthly: 18500, age: 26, raMonthly: 0,    medicalMonthly: 800,  medicalDependants: 1 },
    { name: "Fatima Adams",   grossMonthly: 62000, age: 39, raMonthly: 3000, medicalMonthly: 1800, medicalDependants: 4 },
    { name: "Johan van Wyk",  grossMonthly: 14500, age: 58, raMonthly: 0,    medicalMonthly: 0,    medicalDependants: 0 },
    { name: "Nomsa Dlamini",  grossMonthly: 95000, age: 68, raMonthly: 5000, medicalMonthly: 1500, medicalDependants: 1 },
  ];

  /* ── SELF TEST ───────────────────────────────────────────────────
     The same hand-checked cases as tests/test_vat.py and
     tests/test_payroll.py. Open the console and run Vat.selfTest(). */
  function selfTest() {
    const cases = [
      ["VAT: R100 000 of sales -> R15 000 output tax",
        () => calculateVat(100_000, 0).outputTax, 15_000],
      ["VAT: R40 000 of purchases -> R6 000 input tax",
        () => calculateVat(100_000, 40_000).inputTax, 6_000],
      ["VAT: R9 000 payable to SARS",
        () => calculateVat(100_000, 40_000).amountPayable, 9_000],
      ["VAT: R4 500 to claim back when inputs exceed output",
        () => calculateVat(50_000, 80_000).amountClaimable, 4_500],
      ["VAT: six bi-monthly periods in a tax year",
        () => vatPeriods("2027").length, 6],
      ["VAT: 2027 P1 runs 1 Mar 2026 to 30 Apr 2026",
        () => fmtDate(vatPeriods("2027")[0].start), "01 Mar 2026"],
      ["VAT: 2027 P6 is due in March 2027",
        () => vatPeriods("2027")[5].dueMonth, "March 2027"],
      ["VAT: above R2.3m you must register",
        () => registrationStatus(2_500_000).mustRegister, true],
      ["VAT: above R120 000 you may register voluntarily",
        () => registrationStatus(500_000).status, "Voluntary registration available"],
      ["SDL: 1% of the leviable amount",
        () => calculateSdl(10_000, 600_000), 100],
      ["SDL: no SDL below a R500 000 annual payroll",
        () => calculateSdl(10_000, 400_000), 0],
      ["Payslip: Thandi's monthly PAYE",
        () => calculatePayslip(DEMO_EMPLOYEES[0], "2027", 2_664_000).payeMonthly, 3_235],
      ["Payslip: Thandi's net monthly pay",
        () => calculatePayslip(DEMO_EMPLOYEES[0], "2027", 2_664_000).netMonthly, 27_087.88],
      ["Payslip: Johan's PAYE on R14 500",
        () => calculatePayslip(DEMO_EMPLOYEES[3], "2027").payeMonthly, 1_125],
      ["Payroll: five employees in the demo data",
        () => runPayroll(DEMO_EMPLOYEES, "2027").headCount, 5],
      ["Payroll: total PAYE withheld is R41 511.08",
        () => runPayroll(DEMO_EMPLOYEES, "2027").totalPaye, 41_511.08],
      ["Payroll: total net paid is R170 135.44",
        () => runPayroll(DEMO_EMPLOYEES, "2027").totalNet, 170_135.44],
      ["EMP201: total liability is PAYE + UIF + SDL",
        () => emp201Summary(runPayroll(DEMO_EMPLOYEES, "2027")).totalLiability, 45_343.04],
      ["EMP201: an October payroll is due on 6 Nov 2026 (7th = Saturday)",
        () => fmtDate(emp201DueDate(new Date(2026, 9, 1))), "06 Nov 2026"],
    ];

    let passed = 0;
    for (const [name, fn, expected] of cases) {
      const actual = fn();
      const ok = Math.abs(actual - expected) <= 0.01;
      console.log(`${ok ? "  ok -" : "  FAIL -"} ${name}`);
      if (ok) passed++;
      else console.log(`         expected ${expected}, got ${actual}`);
    }
    console.log(`\n${passed}/${cases.length} checks passed.\n`);
    return passed === cases.length;
  }

  return {
    VAT_RATE, VAT_COMPULSORY_THRESHOLD, VAT_VOLUNTARY_THRESHOLD,
    SDL_RATE, SDL_ANNUAL_PAYROLL_EXEMPTION, UIF_MONTHLY_THRESHOLD,
    calculateVat, vatPeriods, registrationStatus, vatCategory,
    calculateSdl, calculatePayslip, runPayroll, emp201Summary, emp201DueDate,
    DEMO_EMPLOYEES, fmtDate, fmtLong, selfTest,
  };
})();
