/* ═══════════════════════════════════════════════════════════════════
   PORTFOLIO DATA
   ───────────────────────────────────────────────────────────────────
   This is the ONLY file you need to edit to add a new project.
   Everything else on the site renders from what lives here.

   HOW TO ADD A PROJECT
   1. Copy an object from PROJECTS
   2. Give it a unique `id`
   3. Fill in the fields
   4. Save — the grid, filters, search palette and counters update
      automatically.

   status must be one of:  "live" | "in-progress" | "planned"
   accent must be one of:  "brass" | "olive" | "plum" | "slate" | "terracotta"
   ═══════════════════════════════════════════════════════════════════ */


/* ── 1. IDENTITY ──────────────────────────────────────────────────
   CHANGE THESE FIRST. The email + socials are used in the contact
   section, the footer and the command palette.                    */
const PROFILE = {
  name: "Ayanda Shongwe",
  role: "BCom Accounting student & developer",
  location: "South Africa",
  email: "ayandayeshongwe@icloud.com",
  availability: "Available for internships & junior roles",
  github: "https://github.com/vcfvz22rk5-debug",
  // Leave this empty until you have a profile. The contact card and the
  // command palette both hide an empty link.
  linkedin: "",
  twitter: "",                                         // optional
};


/* ── 2. ACCENT COLOURS ────────────────────────────────────────────
   Per-card theming. Add your own by extending this object.      */
const ACCENTS = {
  brass:      { fg: "#d4a94f", bg: "rgba(212,169,79,.13)",  bd: "rgba(212,169,79,.30)" },
  olive:      { fg: "#8aa070", bg: "rgba(138,160,112,.13)", bd: "rgba(138,160,112,.30)" },
  terracotta: { fg: "#c2705a", bg: "rgba(194,112,90,.13)",  bd: "rgba(194,112,90,.30)" },
  slate:      { fg: "#86a9b5", bg: "rgba(134,169,181,.13)", bd: "rgba(134,169,181,.30)" },
  plum:       { fg: "#b08bb0", bg: "rgba(176,139,176,.13)", bd: "rgba(176,139,176,.30)" },
};


/* ── 3. PROJECTS ──────────────────────────────────────────────────
   ⭐ featured: true  →  spans two columns (use for one hero project)
   🎨 accent:          →  "brass" | "olive" | "plum" | "slate" | "terracotta"
   🔗 links:           →  { repo, demo, docs }   (use "#" to hide one)
   ─────────────────────────────────────────────────────────────── */
const PROJECTS = [
  {
    id: "payroll-suite",
    featured: true,
    accent: "brass",
    icon: "i-building",
    status: "live",
    year: "2026",
    title: "Payroll Suite",
    tagline: "A payroll and SARS compliance system, in pure Python",
    description:
      "The employer's half of tax, done properly. Payslips with overtime, bonuses, commission and leave; the SARS annualised method for the tax; the EMP201, EMP501 and IRP5 forms; a deadline calendar that knows the 7th is sometimes a Saturday; a SQLite database; and a dashboard that draws the numbers. No pip install, no framework, no build step.",
    points: [
      "The SARS annualised method - the tax on a month, worked out on a year",
      "Year-end reconciliation: what the employee was really taxed, and what to give back",
      "Section 11F, overtime at 1.5x and 2x, UIF caps, SDL exemptions and commission earners",
      "EMP201, EMP501, IRP5 certificates and a full deadline calendar",
      "A SQLite database and a JSON API behind a hand-drawn dashboard",
      "148 checks in the test suite, every figure worked out by hand",
    ],
    tags: ["Python 3", "SQLite", "HTTP API", "Vanilla JS", "Payroll", "EMP201"],
    links: {
      repo: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite/tree/main/payroll-suite",
      demo: "#case",
      docs: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite/blob/main/payroll-suite/README.md",
    },
  },

  {
    id: "paye-calculator",
    accent: "olive",
    icon: "i-calculator",
    status: "live",
    year: "2026",
    title: "SA Salary & Tax Calculator",
    tagline: "PAYE, UIF & net pay from official SARS tables",
    description:
      "A command-line tool that does what every South African employee does by hand every month: work out your PAYE, your UIF and your actual take-home pay. Built on the official SARS tax tables for the 2026 and 2027 tax years, with rebates applied by age, and retirement contributions capped by section 11F.",
    points: [
      "Progressive slab rates straight from SARS, for 2026 & 2027",
      "Primary / secondary / tertiary rebates applied by age",
      "UIF employee and employer split, capped at the R17,712 threshold",
      "Section 11F limit: 27.5% of salary, max R350,000 a year",
      "Medical scheme fees tax credit, interest exemption and dividends tax",
      "21 hand-calculated unit tests that prove the maths matches SARS",
    ],
    tags: ["Python 3", "CLI", "unittest", "SARS Tax Tables", "Payroll"],
    links: {
      repo: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite",
      demo: "#paye",
      docs: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite#readme",
    },
  },

  {
    id: "paye-web",
    accent: "plum",
    icon: "i-code",
    status: "live",
    year: "2026",
    title: "PAYE Engine for the Browser",
    tagline: "The same tax logic, zero installation",
    description:
      "The Python engine rewritten in vanilla JavaScript so the calculation runs entirely on the client. No build step, no server, no dependencies - and it ships as this website, so you can poke at it right now.",
    points: [
      "Pure JavaScript port of the Python calculation engine",
      "Live income-breakdown visualisation as you type",
      "Shows which tax slab your salary falls into",
      "Works offline, on any device, with no install",
    ],
    tags: ["JavaScript", "Vanilla", "CSS Grid", "No Build Step"],
    links: {
      repo: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite",
      demo: "#paye",
      docs: "",
    },
  },

  {
    id: "vat-payroll",
    accent: "slate",
    icon: "i-receipt",
    status: "live",
    year: "2026",
    title: "VAT 201 & Payroll Suite",
    tagline: "The employer's side of the story",
    description:
      "The other half of tax: what a business owes SARS. A VAT engine with the bi-monthly VAT201 periods and their deadlines, SDL, and a batch payroll that reads a whole team from a CSV and produces the monthly EMP201 declaration.",
    points: [
      "Output tax less input tax at 15%, and the 2026 registration thresholds",
      "The six bi-monthly VAT periods, each with its real due date",
      "Batch payroll for a list of employees, read from a CSV file",
      "SDL at 1% of the leviable amount, with the R500 000 exemption",
      "EMP201 summary: PAYE, UIF and SDL, due by the 7th of the month",
      "54 hand-calculated checks in the test suite",
    ],
    tags: ["Python 3", "CSV", "VAT201", "EMP201", "SDL", "Payroll"],
    links: {
      repo: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite",
      demo: "#vat",
      docs: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite#readme",
    },
  },

  {
    id: "tax-rules",
    accent: "terracotta",
    icon: "i-book",
    status: "live",
    year: "2026",
    title: "Medical Credits, Interest & Dividends",
    tagline: "The rules that hide in the small print",
    description:
      "The remaining income-tax rules, layered onto the core engine: the medical scheme fees tax credit, the interest exemption and the 20% dividends withholding tax - each one tested against a hand-worked figure.",
    points: [
      "Medical tax credits: R376 pm for the first two members, R254 after (2027)",
      "Interest exemption: R23 800 under 65, R34 500 at 65+",
      "Dividends exemption and the 20% withholding tax",
      "Every figure traceable back to a SARS source",
    ],
    tags: ["Python 3", "SARS Rules", "Tax Credits", "Testing"],
    links: {
      repo: "https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite",
      demo: "#paye",
      docs: "",
    },
  },

  {
    id: "provisional-tax",
    accent: "olive",
    icon: "i-chart",
    status: "planned",
    year: "2027",
    title: "Provisional Tax & IRP6 Estimator",
    tagline: "For tax years when the form lands",
    description:
      "An IRP6-style estimate for taxpayers who don't have an employer to deduct PAYE for them - freelancers, side hustles and second income sources - comparing the two provisional tax payments against the final liability.",
    points: [
      "IRP6-style provisional tax estimate",
      "Second income source handling",
      "Provisional tax: the first and second payments, and the penalty for paying late",
      "Compared against the final tax liability for the year",
    ],
    tags: ["Python 3", "IRP6", "Provisional Tax", "SARS"],
    links: { repo: "", demo: "", docs: "" },
  },
];


/* ── 4. HERO STATS ────────────────────────────────────────────────
   `suffix` is optional. Values animate up when the page loads.    */
const STATS = [
  { value: 5,   label: "Projects live",    suffix: ""  },
  { value: 262, label: "Tests passing",    suffix: ""  },
  { value: 2,   label: "SARS tax years",   suffix: ""  },
];


/* ── 5. "WHAT I'M WORKING ON" LIST ─────────────────────────────── */
const FOCUS = [
  { icon: "i-receipt",   text: "Payroll & PAYE logic that matches SARS, not guesswork" },
  { icon: "i-building",  text: "The employer's side too — VAT201, SDL, UIF and the EMP201" },
  { icon: "i-code",      text: "Python on the backend, vanilla JS on the front" },
  { icon: "i-check",     text: "Test-driven — 262 checks, every figure worked out by hand" },
  { icon: "i-book",      text: "Writing it all down so a stranger can run it" },
];


/* ── 6. BUILD TIMELINE ───────────────────────────────────────────
   status: "done" | "active" | "todo"                            */
const MILESTONES = [
  {
    week: "Week 01",
    title: "Core PAYE engine",
    status: "done",
    items: [
      { done: true,  text: "SARS 2026 & 2027 tax tables loaded" },
      { done: true,  text: "Progressive slab-rate calculation" },
      { done: true,  text: "Primary, secondary & tertiary rebates by age" },
      { done: true,  text: "Monthly PAYE (annual \u00f7 12)" },
      { done: true,  text: "UIF 1% + 1% with the R17,712 earnings cap" },
      { done: true,  text: "Section 11F retirement deduction limit" },
      { done: true,  text: "Interactive terminal programme" },
      { done: true,  text: "9 automated tests, all passing" },
    ],
    note: "Learned: variables, functions, dictionaries, lists, loops, conditionals, try/except, writing tests.",
  },
  {
    week: "Week 02",
    title: "More tax rules",
    status: "done",
    items: [
      { done: true,  text: "Medical tax credits (R376 pm for the first two members, R254 after)" },
      { done: true,  text: "Interest exemption (R23 800 under 65 / R34 500 at 65+)" },
      { done: true,  text: "Dividend exemption and 20% dividends withholding tax" },
      { done: true,  text: "Annual vs monthly PAYE, checked against the SARS payscale method" },
      { done: true,  text: "The test suite grew from 9 checks to 21" },
      { done: false, text: "Second income source / provisional tax (IRP6) estimate" },
    ],
    note: "Learned: rebates stack on top of each other, exemptions and credits are different things, and the order you apply them in changes the answer.",
  },
  {
    week: "Week 03",
    title: "VAT & the employer side",
    status: "done",
    items: [
      { done: true,  text: "VAT calculator: output VAT, input VAT, net VAT payable (15%)" },
      { done: true,  text: "VAT201 period summary (bi-monthly, with the real due dates)" },
      { done: true,  text: "EMP201 monthly employer declaration summary" },
      { done: true,  text: "Batch mode: calculate salaries for a list of employees (CSV)" },
      { done: true,  text: "Example data: a mini 'payroll for 5 employees' demo" },
      { done: true,  text: "SDL at 1% of the leviable amount, with the R500 000 exemption" },
    ],
    note: "Learned: the employer's obligations are a different set of rules from the employee's, and the deadlines matter as much as the numbers.",
  },
  {
    week: "Week 04",
    title: "Polish & publish",
    status: "active",
    items: [
      { done: true,  text: "Clean up and comment all code for other people to read" },
      { done: false, text: "Full README: screenshots, what I learned, how it maps to my degree" },
      { done: false, text: "Put it on GitHub \u2014 employers will look at this" },
      { done: true,  text: "This portfolio site, with live browser demos of both engines" },
      { done: true,  text: "Smooth scrolling, a scroll progress bar and tabbed live demos" },
      { done: false, text: "A short LinkedIn post explaining the project" },
    ],
    note: "Current focus \u2014 getting the README and the screenshots right, then publishing.",
  },
  {
    week: "Week 05",
    title: "The payroll suite",
    status: "done",
    items: [
      { done: true,  text: "The SARS annualised method for the monthly PAYE" },
      { done: true,  text: "Overtime at 1.5x and 2x, bonuses, commission, leave" },
      { done: true,  text: "A SQLite database with a schema and migrations" },
      { done: true,  text: "EMP201, EMP501 and IRP5 certificates" },
      { done: true,  text: "A deadline calendar that knows about weekends" },
      { done: true,  text: "The year-end tax reconciliation" },
      { done: true,  text: "A JSON API and a dashboard, in the standard library" },
      { done: true,  text: "148 checks in the test suite" },
    ],
    note: "Learned: annualising the tax, keeping the engine away from the database, and that a deadline is a business rule rather than a date.",
  },
];


/* ── 7. SKILLS ─────────────────────────────────────────────────── */
const SKILLS = [
  {
    icon: "i-code",
    title: "Languages",
    desc: "The tools I actually reach for.",
    items: ["Python 3", "JavaScript", "SQL", "HTML", "CSS", "Bash"],
  },
  {
    icon: "i-calculator",
    title: "Accounting & Tax",
    desc: "The domain knowledge that makes the code correct.",
    items: ["PAYE", "UIF", "Progressive slabs", "Rebates", "Section 11F", "VAT", "SDL", "EMP201"],
  },
  {
    icon: "i-chart",
    title: "Financial Modelling",
    desc: "Turning rules into numbers people trust.",
    items: ["Payroll modelling", "Pension maths", "Effective vs marginal rate", "Batch runs", "Forecasting"],
  },
  {
    icon: "i-check",
    title: "Engineering",
    desc: "How I make sure it still works tomorrow.",
    items: ["262 unit tests", "SQLite", "Git & GitHub", "Clean code", "Documentation", "Code review"],
  },
  {
    icon: "i-spark",
    title: "Front-end",
    desc: "Interfaces that feel good and read clearly.",
    items: ["Vanilla JS", "SVG charts", "CSS Grid", "Smooth scroll", "Accessibility"],
  },
  {
    icon: "i-book",
    title: "Domain",
    desc: "Context that comes from studying the subject.",
    items: ["SA payroll", "SARS tax years", "BCom Accounting", "Financial reporting"],
  },
];


/* ── 8. SCROLLING MARQUEE ──────────────────────────────────────── */
const MARQUEE = [
  "Python", "SARS Tax Tables", "PAYE", "UIF", "JavaScript",
  "Unit Testing", "HTML & CSS", "Git", "Financial Modelling",
  "Payroll", "Vanilla JS", "Documentation", "VAT 201", "EMP201",
  "SDL", "Batch Payroll", "CSV", "SQLite", "IRP5", "Annualised Tax",
];


/* ── 9. COMMAND PALETTE INDEX ──────────────────────────────────── */
const PALETTE_SECTIONS = [
  { label: "Home",         href: "#home" },
  { label: "About",        href: "#about" },
  { label: "Selected work", href: "#work" },
  { label: "Live demos",   href: "#demo" },
  { label: "Case study",   href: "#case-study" },
  { label: "The journey",  href: "#journey" },
  { label: "Toolkit",      href: "#stack" },
  { label: "Contact",      href: "#contact" },
];

/* The three live demos. `tab` switches the demo tab open when the
   reader picks it from the command palette. */
const PALETTE_DEMOS = [
  { label: "PAYE calculator",   href: "#demo", tab: "paye",    icon: "i-calculator" },
  { label: "VAT 201 calculator", href: "#demo", tab: "vat",     icon: "i-percent" },
  { label: "Payroll & EMP201",   href: "#demo", tab: "payroll", icon: "i-users" },
];
