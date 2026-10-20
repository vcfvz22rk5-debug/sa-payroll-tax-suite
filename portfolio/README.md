# Portfolio — Ayanda Shongwe

A personal portfolio site where all my projects live. Static HTML, CSS and
vanilla JavaScript — no build step, no dependencies, no `npm install`.

**The site is a spreadsheet.** There is one formula bar across the top, one
sheet open at a time, a row of sheet tabs underneath and a status bar with
the totals along the bottom. Click any cell and the formula bar shows you
how that number was worked out — in accounting terms, not code.

---

## Run it

Any static file server works. From this folder:

```bash
# Python (already installed on most systems)
python3 -m http.server 8000

# then open
# http://localhost:8000
```

You can also just double-click `index.html` — it works straight off the
filesystem, no server required.

---

## Adding a project

**Everything on this site is driven by `assets/js/data.js`.** You never need
to touch the HTML or CSS to add a project.

1. Open `assets/js/data.js`
2. Copy an object from the `PROJECTS` array
3. Give it a unique `id`, fill in the fields, save
4. The grid, the filters, the command palette and the counters all update
   automatically

```js
{
  id: "my-new-project",          // unique
  featured: false,               // true = spans two columns
  accent: "cyan",                // cyan | violet | pink | green | amber
  icon: "i-code",                // any id from the icon sprite in index.html
  status: "live",                // live | in-progress | planned
  year: "2026",
  title: "My New Project",
  tagline: "One line that sells it",
  description: "A paragraph or two about what it does and why it matters.",
  points: [
    "What it does",
    "What makes it interesting",
    "Proof it actually works",
  ],
  tags: ["Python", "CLI"],
  links: {
    repo:  "https://github.com/you/project",   // "" to hide the button
    demo:  "#demo",                            // "" to hide the button
    docs:  "",                                 // "" to hide the button
  },
}
```

The same file also holds your identity (`PROFILE`), the hero counters
(`STATS`), the about list (`FOCUS`), the build timeline (`MILESTONES`), the
skills grid (`SKILLS`), the scrolling ticker (`MARQUEE`) and the command
palette index (`PALETTE_SECTIONS` and `PALETTE_DEMOS`).

---

## The other project in the repository

The payroll suite lives one folder up, in `../payroll-suite/`. It is the
flagship project on this site — a payroll and SARS compliance system with a
SQLite database, a JSON API and a dashboard, written in the Python standard
library alone.

```bash
cd ../payroll-suite
python3 -m payroll_suite.cli init
python3 -m payroll_suite.cli serve     # http://localhost:8000
python3 tests/run_all.py               # 148 checks
```

---

## Things to change first

| What | Where |
|---|---|
| Your name, email, GitHub, LinkedIn | `assets/js/data.js` → `PROFILE` |
| Your real email address | `PROFILE.email` — already set to `ayandayeshongwe@icloud.com` |
| Your GitHub URL | `PROFILE.github` — already set |
| Your LinkedIn URL | `PROFILE.linkedin` — leave it as `""` until you have a profile. The contact card and the command palette both hide an empty link, so nothing broken shows up. |
| Repo links on each project card | `PROJECTS[].links.repo` |
| The hero headline and intro | `index.html` → the `<h1>` and `<p class="hero__lead">` |
| The about paragraphs | `index.html` → `.about__text` |
| The page title and meta description | `index.html` → `<head>` |

### Icons

The site uses an inline SVG sprite at the top of `index.html`. To add one,
drop a `<symbol id="i-youricon" viewBox="0 0 24 24">…</symbol>` into the
sprite, then reference it with `icon: "i-youricon"`.

Available now: `i-calculator`, `i-receipt`, `i-chart`, `i-code`, `i-book`,
`i-rocket`, `i-check`, `i-arrow`, `i-arrow-up`, `i-external`, `i-github`,
`i-linkedin`, `i-mail`, `i-moon`, `i-sun`, `i-search`, `i-close`,
`i-terminal`, `i-spark`, `i-percent`, `i-users`, `i-building`, `i-calendar`,
`i-clock`, `i-shield`.

### The social preview image

`assets/img/og-image.png` is the picture LinkedIn/X/WhatsApp show when
someone shares a link to the site. It is generated, not hand-drawn:

```bash
python3 tools/make-og-image.py
```

The script uses only the Python standard library (no Pillow needed) — it
rasterises the "AS" monogram as anti-aliased gradient strokes and writes the
PNG. Run it again if you change the monogram or the colours.

The monogram appears in three places and all three use the same letterforms:
`assets/img/favicon.svg`, the brand mark in `index.html`, and the OG image.

---

## The live demos

The "Live demo" section is one card with three tabs. Each one runs a real
calculation in the browser — the exact same logic as the Python project.

| Tab | What it does | Engine |
|---|---|---|
| **PAYE calculator** | Net pay, PAYE, UIF, the tax slab you fall into, the medical tax credit | `assets/js/tax.js` |
| **VAT 201** | Output tax vs input tax, the six bi-monthly VAT periods and their due dates, the registration check | `assets/js/vat.js` |
| **Payroll & EMP201** | A five-employee payroll run, the totals, and the EMP201 deadline for any month you pick | `assets/js/vat.js` |

**They have their own test suites.** Open the browser console on the site
and run:

```js
Tax.selfTest()   // 12 checks — the PAYE engine
Vat.selfTest()   // 19 checks — VAT, SDL, payslips and the EMP201
```

They run the same hand-checked cases as `tests/test_paye.py`,
`tests/test_vat.py` and `tests/test_payroll.py` in the Python project and
print a pass/fail line for each. If you change the tax tables, run these —
and run the Python tests too.
**When SARS changes the numbers, change them in both places:**

| | Python | JavaScript |
|---|---|---|
| Tax tables & medical credits | `tax_tables.py` | `assets/js/tax.js` → `TAX_YEARS` |
| UIF, SDL & s11F limits | `config.py` | `assets/js/tax.js` + `assets/js/vat.js` → the config blocks |
| VAT thresholds | `config.py` | `assets/js/vat.js` → the config block |

---

## Deploying to GitHub Pages (free)

The site is pure static files, so GitHub Pages is the easiest way to put
it online — free, no card, and every push updates the site.

It is already deployed:

**https://vcfvz22rk5-debug.github.io/sa-payroll-tax-suite/**

The repository has a workflow, `.github/workflows/pages.yml`, that
publishes this folder whenever anything in it changes. You can watch it
under **Actions** in the repository, and re-run it from there if you
ever need to.

The full walkthrough, including a custom domain and how to host the
payroll app, is in [`../DEPLOY.md`](../DEPLOY.md).

Because the site uses relative paths for everything, it also works from
the root of a repository, from a sub-folder, or from any static host
(Netlify, Cloudflare Pages, Vercel) without changing a line.

---

## Structure

```
portfolio/
├── index.html                 the whole page structure
├── assets/
│   ├── css/styles.css         every style, organised in 22 numbered sections
│   ├── js/
│   │   ├── data.js            ← all your content lives here
│   │   ├── tax.js             the PAYE engine + its self-test
│   │   ├── vat.js             the VAT, payroll & EMP201 engine + its self-test
│   │   └── main.js            rendering and interactions
│   └── img/
│       ├── favicon.svg
│       └── og-image.png       the social preview image
├── tools/
│   └── make-og-image.py       regenerates og-image.png
└── README.md
```

### What each section does

| File | Job |
|---|---|
| `data.js` | Content. Projects, skills, timeline, identity, stats. |
| `tax.js` | The SARS tax engine, ported from Python. Self-testing. |
| `vat.js` | The employer-side engine — VAT, SDL, payslips, the EMP201. Self-testing. |
| `main.js` | Renders `data.js` into the page, plus theme, filters, palette, the three demos, scrolling and animation. |

---

## Features

- **It is a spreadsheet.** A formula bar, sheet tabs, a status bar with live
  SUM / COUNT / AVERAGE, and a name box that shows the cell you have
  selected. Click any number and the formula bar shows the working:
  `=MAX(0, 44118 + 26%*(342000-245100) - 17820 - 18912) / 12`.
- **Dark-first design** with a graph-paper grid, frosted glass cards and a
  grain overlay. Light theme included — the toggle in the toolbar
  remembers your choice.
- **Command palette** — press `Ctrl/⌘ + K` to jump to any sheet, project
  or link. It does fuzzy matching, so "vt" finds "VAT 201".
- **Filterable project grid** — live / in progress / planned.
- **Three live models** — PAYE, VAT 201 and a payroll run, all calculated in
  the browser, with income-breakdown bars, a tax-slab visualiser and the
  real VAT/EMP201 deadlines.
- **A case study** for the flagship project: the problem, the design
  decisions that mattered, and a diagram of how the code fits together.
- **Keyboard driven** — `Ctrl+PageUp` / `Ctrl+PageDown` changes sheet, the
  arrow keys walk the cells of the open sheet, `Ctrl+K` searches.
- **Performance mode** — the page measures its own frame rate while you
  scroll and turns the decoration off if it cannot keep up. You can also
  switch it by hand with the gauge in the toolbar.
- **Responsive** from 320px up.
- **Accessible** — semantic landmarks, skip link, visible focus rings,
  labelled inputs, and `aria-live` on the copy-to-clipboard confirmation.
- **Respects `prefers-reduced-motion`** — animations switch off for anyone
  who asks the OS for them.
- **Works without JavaScript** — the content is still in the page; JS only
  adds the interactive layers.

---

## Browser support

Modern browsers (Chrome, Edge, Firefox, Safari, 2022+). The site uses
`backdrop-filter`, CSS `mask`, custom properties, `IntersectionObserver`
and `MutationObserver` — all widely supported today. Older browsers get a
plainer but perfectly readable page.

---

*Built by hand. No frameworks, no tracking, no cookies.*
