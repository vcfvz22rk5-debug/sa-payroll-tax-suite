/* ═══════════════════════════════════════════════════════════════════
   main.js — the workbook.
   ───────────────────────────────────────────────────────────────────
   The page is a spreadsheet. There is one formula bar, one open sheet,
   a row of sheet tabs and a status bar with the totals. Click any cell
   to see how it is calculated.
   ═══════════════════════════════════════════════════════════════════ */

(() => {
  "use strict";

  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  /* ── FORMATTING ───────────────────────────────────────────────── */
  const rand = (n) =>
    "R " + Number(n || 0).toLocaleString("en-ZA", {
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
  const randNeg = (n) => {
    const v = Math.abs(Number(n) || 0);
    return `(R${v.toLocaleString("en-ZA", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })})`;
  };
  const num = (n) => Number(n || 0).toLocaleString("en-Z");
  const pct = (n, dp = 1) => `${(n * 100).toFixed(dp)}%`;

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  const svgIcon = (id, cls = "ico") =>
    `<svg class="${cls}"><use href="#${id}"></use></svg>`;

  /* localStorage throws in a sandboxed iframe or when storage is
     blocked. Never let that take the whole page down with it. */
  const store = {
    get(key) {
      try { return localStorage.getItem(key); } catch { return null; }
    },
    set(key, value) {
      try { localStorage.setItem(key, value); } catch { /* ignore */ }
    },
  };

  /* The demo tab picker lives one level up so the command palette can
     open a sheet too. */
  let showSheet = null;
  let selectCell = null;

  /* The search shortcut is Ctrl+K everywhere except a Mac, where it is
     Command+K. Showing the wrong symbol is the sort of small detail
     that gives the whole page away. */
  const isMac = () => {
    const data = navigator.userAgentData;
    if (data?.platform) return /mac/i.test(data.platform);
    return /Mac|iPhone|iPad|iPod/i.test(
      navigator.platform || navigator.userAgent || ""
    );
  };

  function initShortcutHint() {
    const mac = isMac();
    const kbd = $("#cmd-kbd");
    if (kbd) kbd.textContent = mac ? "⌘K" : "Ctrl K";
    const trigger = $("#cmd-trigger");
    if (trigger) trigger.title = mac ? "Search (⌘K)" : "Search (Ctrl+K)";
  }

  /* ═══════════════════════════════════════════════════════════════
     1. THEME
     ═══════════════════════════════════════════════════════════════ */
  function initTheme() {
    const root = document.documentElement;
    const btn = $("#theme-toggle");
    const stored = store.get("portfolio-theme");

    const apply = (theme) => {
      root.setAttribute("data-theme", theme);
      if (btn) btn.setAttribute("title", theme === "dark" ? "Switch to light" : "Switch to dark");
    };

    apply(stored || (window.matchMedia?.("(prefers-color-scheme: light)").matches ? "light" : "dark"));

    btn?.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      apply(next);
      store.set("portfolio-theme", next);
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     2. THE SHEETS
     ═══════════════════════════════════════════════════════════════ */
  const SHEETS = [
    { id: "cover",    label: "Cover",    key: "1" },
    { id: "projects", label: "Projects", key: "2" },
    { id: "paye",     label: "PAYE",     key: "3" },
    { id: "vat",      label: "VAT 201",  key: "4" },
    { id: "payroll",  label: "Payroll",  key: "5" },
    { id: "case",     label: "Case",     key: "6" },
    { id: "timeline", label: "Timeline", key: "7" },
    { id: "contact",  label: "Contact",  key: "8" },
  ];

  function initSheets() {
    const sheets = $$(".sheet");
    const tabbar = $("#tabbar-sheets");
    if (!sheets.length) return;

    // The sheet tabs
    if (tabbar) {
      tabbar.innerHTML = SHEETS.map((sheet) => `
        <button class="tab" type="button" role="tab" data-sheet="${sheet.id}"
                aria-selected="false">
          <span class="tab__dot"></span>${sheet.label}
        </button>`).join("");
    }

    const tabs = tabbar ? $$(".tab", tabbar) : [];
    const statusSheet = $("#st-sheet");

    showSheet = (id, remember = true) => {
      const target = sheets.find((s) => s.dataset.sheet === id) || sheets[0];
      sheets.forEach((sheet) => {
        const on = sheet === target;
        sheet.hidden = !on;
        sheet.classList.toggle("is-active", on);
      });
      tabs.forEach((tab) => {
        const on = tab.dataset.sheet === target.dataset.sheet;
        tab.classList.toggle("is-active", on);
        tab.setAttribute("aria-selected", String(on));
        tab.tabIndex = on ? 0 : -1;
      });
      if (statusSheet) {
        const meta = SHEETS.find((s) => s.id === target.dataset.sheet);
        statusSheet.textContent = meta ? meta.label : target.dataset.sheet;
      }
      // A new sheet means a new set of cells to select from.
      selectCell?.(null);
      updateStatusBar();
      if (remember) {
        try { history.replaceState(null, "", `#${target.dataset.sheet}`); } catch { /* file:// */ }
      }
    };

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => showSheet(tab.dataset.sheet));
      tab.addEventListener("keydown", (e) => {
        const i = tabs.indexOf(tab);
        let next = null;
        if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (!next) return;
        e.preventDefault();
        showSheet(next.dataset.sheet);
        next.focus();
      });
    });

    // The cover sheet's buttons
    $$("[data-goto]").forEach((button) =>
      button.addEventListener("click", () => showSheet(button.dataset.goto))
    );

    // Ctrl+PageUp / Ctrl+PageDown, the way a spreadsheet works
    document.addEventListener("keydown", (e) => {
      if (!e.ctrlKey || (e.key !== "PageDown" && e.key !== "PageUp")) return;
      e.preventDefault();
      const current = sheets.findIndex((s) => s.classList.contains("is-active"));
      const next = (current + (e.key === "PageDown" ? 1 : -1) + sheets.length) % sheets.length;
      showSheet(sheets[next].dataset.sheet);
    });

    // Open the sheet named in the url
    const wanted = (location.hash || "").replace("#", "");
    showSheet(sheets.some((s) => s.dataset.sheet === wanted) ? wanted : "cover");
  }

  /* ═══════════════════════════════════════════════════════════════
     3. THE CELLS — pick one, read its formula
     ═══════════════════════════════════════════════════════════════ */
  /* Highlight the formula for the bar. The operators are marked FIRST,
     because marking the function names second would try to match them
     inside the tags the first step just inserted. */
  const formatFormula = (formula) =>
    esc(formula)
      .replace(/([=<>+*/%(),:-])/g, '<span class="op">$1</span>')
      .replace(/\b(MAX|MIN|ROUND|SUM|IF)\b/g, "<b>$1</b>");

  function initCells() {
    const formulaBar = $("#formula");
    const nameBox = $("#name-box");

    document.addEventListener("click", (e) => {
      const cell = e.target.closest?.("[data-formula]");
      if (!cell) {
        selectCell?.(null);
        return;
      }
      // A link inside a cell should still work.
      if (e.target.closest("a, button, input, select")) return;
      selectCell?.(cell);
    });

    // Arrow keys walk the cells of the open sheet.
    document.addEventListener("keydown", (e) => {
      if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) return;
      const tag = document.activeElement?.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;

      const cells = $$("[data-formula]", $(".sheet.is-active"));
      if (!cells.length) return;

      const current = cells.indexOf(document.querySelector("[data-formula].is-selected"));
      let next = current;
      if (e.key === "ArrowDown" || e.key === "ArrowRight") next = current + 1;
      else if (e.key === "ArrowUp" || e.key === "ArrowLeft") next = current - 1;
      if (next < 0 || next >= cells.length) return;

      e.preventDefault();
      selectCell?.(cells[next]);
      cells[next].scrollIntoView({ block: "nearest", behavior: "smooth" });
    });

    selectCell = (cell) => {
      $$("[data-formula].is-selected").forEach((el) => el.classList.remove("is-selected"));
      if (!cell) {
        if (formulaBar) {
          formulaBar.textContent = "Pick a cell to see how it is calculated.";
        }
        if (nameBox) nameBox.textContent = "A1";
        return;
      }
      cell.classList.add("is-selected");
      if (formulaBar) {
        formulaBar.innerHTML = formatFormula(cell.dataset.formula);
      }
      if (nameBox) {
        nameBox.textContent = cell.dataset.ref || "A1";
      }
    };
  }

  /* ═══════════════════════════════════════════════════════════════
     4. THE STATUS BAR — the totals of the open sheet
     ═══════════════════════════════════════════════════════════════ */
  function updateStatusBar() {
    const sumEl = $("#st-sum");
    const countEl = $("#st-count");
    const avgEl = $("#st-avg");
    const sheet = $(".sheet.is-active");
    if (!sheet) return;

    const numbers = $$("[data-num]", sheet)
      .map((el) => Number(el.dataset.num))
      .filter((n) => Number.isFinite(n));

    const sum = numbers.reduce((total, n) => total + n, 0);
    if (sumEl) sumEl.textContent = rand(sum);
    if (countEl) countEl.textContent = String(numbers.length);
    if (avgEl) {
      avgEl.textContent = numbers.length ? rand(sum / numbers.length) : "R 0.00";
    }
  }

  /* ═══════════════════════════════════════════════════════════════
     5. HERO — stats counters
     ═══════════════════════════════════════════════════════════════ */
  function renderStats() {
    const wrap = $("#hero-stats");
    if (!wrap) return;
    wrap.innerHTML = STATS.map(
      (s) => `<div>
        <dt>${esc(s.label)}</dt>
        <dd><span data-count="${s.value}">0</span>${s.suffix ? `<small>${esc(s.suffix)}</small>` : ""}</dd>
      </div>`
    ).join("");

    const targets = $$("[data-count]", wrap);
    if (!("IntersectionObserver" in window)) {
      targets.forEach((t) => (t.textContent = t.dataset.count));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          const end = Number(el.dataset.count);
          const dur = 1100;
          const start = performance.now();
          const tick = (now) => {
            const p = Math.min((now - start) / dur, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(end * eased);
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
          io.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    targets.forEach((t) => io.observe(t));
  }

  /* ═══════════════════════════════════════════════════════════════
     6. HERO — terminal animation
     ═══════════════════════════════════════════════════════════════ */
  const termRow = (label, value, cls = "t-val") => {
    const m = label.match(/^(.*?)(\s*\.*)$/);
    const head = m ? m[1] : label;
    const tail = m ? m[2] : "";
    const pad = Math.max(0, 44 - label.length);
    return `  ${head}<span class="t-dim">${tail}${" ".repeat(pad)}</span>` +
           `<span class="${cls}">${String(value).padStart(20)}</span>`;
  };
  const termRule = (ch = "=") => `<span class="t-dim">${ch.repeat(66)}</span>`;

  const TERM_LINES = [
    `<span class="t-dim">$</span> <span class="t-key">python3</span> cli.py`,
    ``,
    termRule(),
    `  <span class="t-val">SOUTH AFRICAN SALARY &amp; TAX ESTIMATE</span>`,
    `<span class="t-dim">  2027 tax year (1 Mar 2026 - 28 Feb 2027)</span>`,
    termRule(),
    termRow("Gross salary (monthly) ............", "R 30,000.00"),
    termRow("Annualised gross (x 12) ...........", "R 360,000.00"),
    termRule("-"),
    termRow("TAXABLE INCOME (annual) ...........", "R 360,000.00"),
    termRow("Tax at SARS slab rates ............", "R 73,992.00"),
    termRow("Less: primary rebate ......", "(R17,820.00)", "t-pink"),
    termRule("-"),
    termRow("ANNUAL TAX (PAYE basis) ...........", "R 56,172.00", "t-green"),
    termRow("Monthly PAYE (annual / 12) .........", "R 4,681.00", "t-green"),
    ``,
    termRow("UIF employee 1% on R17,712.00 (capped)...", "R 177.12", "t-amber"),
    termRow("UIF employer 1% (business cost) ...", "R 177.12", "t-amber"),
    termRule(),
    termRow("NET MONTHLY PAY ...................", "R 25,141.88", "t-green"),
    termRow("Total monthly deductions ..........", "R 4,858.12", "t-amber"),
    `  <span class="t-dim">Effective tax rate: 15.6%   Marginal rate (top slab): 26%</span>`,
    termRule(),
    ``,
    `  <span class="t-dim">Estimate for study/portfolio use only - not an official SARS</span>`,
    `  <span class="t-dim">payscale result. Always verify against sars.gov.za.</span>`,
    ``,
    `<span class="t-green">✔ 9 tests passed</span>  <span class="t-dim">— built from the official SARS tables</span>`,
  ];

  function initTerminal() {
    const body = $("#term-body");
    if (!body) return;
    TERM_LINES.forEach((line, i) => {
      const span = document.createElement("span");
      span.className = "t-line";
      span.style.animationDelay = `${250 + i * 80}ms`;
      span.innerHTML = line || "&nbsp;";
      body.appendChild(span);
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     7. MARQUEE
     ═══════════════════════════════════════════════════════════════ */
  function initMarquee() {
    const track = $("#marquee-track");
    if (!track) return;
    const items = MARQUEE.map((m) => `<span class="marquee__item"><i></i>${esc(m)}</span>`).join("");
    track.innerHTML = items + items;
  }

  /* ═══════════════════════════════════════════════════════════════
     8. ABOUT — focus list
     ═══════════════════════════════════════════════════════════════ */
  function renderFocus() {
    const list = $("#focus-list");
    if (!list) return;
    list.innerHTML = FOCUS.map(
      (f) => `<li>${svgIcon(f.icon)}<span>${esc(f.text)}</span></li>`
    ).join("");
  }

  /* ═══════════════════════════════════════════════════════════════
     9. PROJECTS
     ═══════════════════════════════════════════════════════════════ */
  const STATUS_LABEL = {
    live: "Live",
    "in-progress": "In progress",
    planned: "Planned",
  };

  function projectCard(p) {
    const accent = ACCENTS[p.accent] || ACCENTS.cyan;
    const badgeClass =
      p.status === "live" ? "card__badge--live"
      : p.status === "in-progress" ? "card__badge--progress"
      : "card__badge--planned";

    const links = [];
    if (p.links?.repo)  links.push(`<a class="card__link" href="${esc(p.links.repo)}" target="_blank" rel="noopener">${svgIcon("i-github")} Repo ${svgIcon("i-external")}</a>`);
    if (p.links?.demo)  links.push(`<a class="card__link card__link--accent" href="${esc(p.links.demo)}" data-goto-sheet="${esc(p.links.demo.replace("#", ""))}">${svgIcon("i-spark")} Open</a>`);
    if (p.links?.docs)  links.push(`<a class="card__link" href="${esc(p.links.docs)}" target="_blank" rel="noopener">${svgIcon("i-book")} Docs ${svgIcon("i-external")}</a>`);

    return `
      <article class="card ${p.featured ? "is-featured" : ""}" data-status="${esc(p.status)}"
               style="--icon-bg:${accent.bg};--icon-fg:${accent.fg};--icon-bd:${accent.bd};--card-grad:${accent.grad}">
        <div class="card__top">
          <span class="card__icon">${svgIcon(p.icon)}</span>
          <span class="card__badge ${badgeClass}">${esc(STATUS_LABEL[p.status] || p.status)}</span>
        </div>
        <div>
          <h3 class="card__title">${esc(p.title)}</h3>
          <p class="card__tagline">${esc(p.tagline)}</p>
        </div>
        <p class="card__desc">${esc(p.description)}</p>
        <ul class="card__points">
          ${(p.points || []).map((pt) => `<li>${svgIcon("i-check")}<span>${esc(pt)}</span></li>`).join("")}
        </ul>
        <div class="card__tags">${(p.tags || []).map((t) => `<span>${esc(t)}</span>`).join("")}</div>
        ${links.length ? `<div class="card__links">${links.join("")}</div>` : ""}
      </article>`;
  }

  function renderProjects() {
    const grid = $("#project-grid");
    if (!grid) return;
    grid.innerHTML = PROJECTS.map(projectCard).join("");

    const empty = $("#project-empty");
    $$(".filter").forEach((btn) => {
      btn.addEventListener("click", () => {
        const f = btn.dataset.filter;
        $$(".filter").forEach((b) => {
          const on = b === btn;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", String(on));
        });
        let shown = 0;
        $$(".card", grid).forEach((card) => {
          const show = f === "all" || card.dataset.status === f;
          card.classList.toggle("is-hidden", !show);
          if (show) shown++;
        });
        if (empty) empty.hidden = shown !== 0;
      });
    });

    // The "Open" buttons switch sheets rather than jump down the page.
    $$("[data-goto-sheet]").forEach((link) =>
      link.addEventListener("click", (e) => {
        e.preventDefault();
        showSheet?.(link.dataset.gotoSheet);
      })
    );
  }

  /* ═══════════════════════════════════════════════════════════════
     10. TIMELINE
     ═══════════════════════════════════════════════════════════════ */
  function renderTimeline() {
    const wrap = $("#timeline");
    if (!wrap) return;
    wrap.innerHTML = MILESTONES.map((m) => {
      const icon = m.status === "done" ? "i-check" : m.status === "active" ? "i-spark" : "i-code";
      const statusText = m.status === "done" ? "Complete" : m.status === "active" ? "In progress" : "Planned";
      return `
        <li class="tl is-${esc(m.status)}">
          <span class="tl__dot">${svgIcon(icon)}</span>
          <div class="tl__head">
            <div>
              <span class="tl__week">${esc(m.week)}</span>
              <h3 class="tl__title">${esc(m.title)}</h3>
            </div>
            <span class="tl__status">${statusText}</span>
          </div>
          <ul class="tl__items">
            ${(m.items || []).map((it) => `
              <li class="${it.done ? "done" : "todo"}">
                ${svgIcon(it.done ? "i-check" : "i-arrow")}
                <span>${esc(it.text)}</span>
              </li>`).join("")}
          </ul>
          ${m.note ? `<p class="tl__note">${esc(m.note)}</p>` : ""}
        </li>`;
    }).join("");
  }

  /* ═══════════════════════════════════════════════════════════════
     11. SKILLS
     ═══════════════════════════════════════════════════════════════ */
  function renderSkills() {
    const grid = $("#skill-grid");
    if (!grid) return;
    grid.innerHTML = SKILLS.map(
      (s) => `
      <article class="skill">
        <span class="skill__icon">${svgIcon(s.icon)}</span>
        <h3 class="skill__title">${esc(s.title)}</h3>
        <p class="skill__desc">${esc(s.desc)}</p>
        <div class="skill__list">${(s.items || []).map((i) => `<span>${esc(i)}</span>`).join("")}</div>
      </article>`
    ).join("");
  }

  /* ═══════════════════════════════════════════════════════════════
     12. CONTACT
     ═══════════════════════════════════════════════════════════════ */
  function renderContact() {
    const linkWrap = $("#contact-links");
    const email = $("#contact-email");

    if (email) {
      email.textContent = PROFILE.email;
      email.href = `mailto:${PROFILE.email}`;
    }

    if (linkWrap) {
      const links = [
        { href: PROFILE.github, icon: "i-github", label: "GitHub" },
        { href: PROFILE.linkedin, icon: "i-linkedin", label: "LinkedIn" },
        { href: `mailto:${PROFILE.email}`, icon: "i-mail", label: "Email" },
      ].filter((l) => l.href);
      linkWrap.innerHTML = links
        .map(
          (l) => `<a class="contact__link" href="${esc(l.href)}" ${
            l.href.startsWith("http") ? 'target="_blank" rel="noopener"' : ""
          }>${svgIcon(l.icon)} ${esc(l.label)}</a>`
        )
        .join("");
    }

    const copyBtn = $("#copy-email");
    const note = $("#copy-note");
    copyBtn?.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(PROFILE.email);
        if (note) note.textContent = "Copied — talk soon.";
      } catch {
        if (note) note.textContent = PROFILE.email;
      }
      setTimeout(() => { if (note) note.textContent = ""; }, 2600);
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     13. THE PAYE MODEL
     ═══════════════════════════════════════════════════════════════ */
  function initCalculator() {
    const form = $("#calc-form");
    if (!form || typeof Tax === "undefined") return;

    const salary = $("#c-salary");
    const age = $("#c-age");
    const ra = $("#c-ra");
    const medical = $("#c-medical");
    const dependants = $("#c-dependants");
    const ageNote = $("#c-age-note");
    const raHint = $("#c-ra-hint");
    const medicalNote = $("#c-medical-note");
    const yearInputs = $$('input[name="taxyear"]');

    let taxYear = "2027";

    function setYear(y) {
      taxYear = y;
      yearInputs.forEach((input) => {
        input.checked = input.value === y;
      });
    }

    yearInputs.forEach((input) =>
      input.addEventListener("change", () => {
        if (input.checked) {
          setYear(input.value);
          update();
        }
      })
    );

    function rebateLabel(a) {
      if (a >= 75) return "primary + secondary + tertiary";
      if (a >= 65) return "primary + secondary";
      return "primary rebate";
    }

    function renderSlabs(brackets, taxableIncome) {
      const wrap = $("#o-slabs");
      if (!wrap) return;

      const widths = brackets.map((b, i) => {
        if (b.to !== null) return b.to - b.from;
        const prev = brackets[i - 1];
        return prev ? prev.to - prev.from : 1;
      });
      const max = Math.max(...widths, 1);

      let activeIndex = brackets.findIndex(
        (b) => b.to === null || taxableIncome <= b.to
      );
      if (activeIndex === -1) activeIndex = brackets.length - 1;

      wrap.innerHTML = brackets
        .map((b, i) => {
          const pctWidth = Math.round(Math.sqrt(widths[i] / max) * 100);
          const isActive = i === activeIndex;
          const isPassed = taxableIncome > b.from;
          const label = b.to === null
            ? `R ${num(b.from)}+`
            : `R ${num(b.from)} – ${num(b.to)}`;
          const cls = isActive ? "is-active" : isPassed ? "is-passed" : "";
          return `
            <div class="slab ${cls}">
              <span class="slab__rate">${Math.round(b.rate * 100)}%</span>
              <span class="slab__bar"><span class="slab__fill" style="width:${pctWidth}%"></span></span>
              <span class="slab__rate">${isActive ? "◀ " : ""}${label}</span>
            </div>`;
        })
        .join("");
    }

    function update() {
      const gross = Math.max(0, Number(salary.value) || 0);
      const a = Math.min(99, Math.max(18, Number(age.value) || 30));
      const raMonthly = Math.max(0, Number(ra.value) || 0);
      const medicalMonthly = Math.max(0, Number(medical.value) || 0);
      const medicalDependants = Math.max(0, Math.round(Number(dependants.value) || 0));

      if (ageNote) ageNote.textContent = rebateLabel(a);
      if (medicalNote) {
        medicalNote.textContent = medicalMonthly > 0
          ? `${medicalDependants || 1} on scheme`
          : "not on a scheme";
      }

      let r;
      try {
        r = Tax.calculate({
          grossMonthly: gross,
          age: a,
          taxYear,
          raMonthly,
          medicalMonthly,
          medicalDependants,
        });
      } catch (err) {
        return;
      }

      // The headline
      const netEl = $("#o-net");
      if (netEl) netEl.textContent = rand(r.netMonthly);
      const netLegend = $("#o-net-legend");
      if (netLegend) netLegend.textContent = rand(r.netMonthly);

      // The bar
      const total = Math.max(r.grossMonthly, 1);
      const setW = (id, v) => { const el = $(id); if (el) el.style.width = `${(v / total) * 100}%`; };
      setW("#o-seg-tax", r.payeMonthly);
      setW("#o-seg-uif", r.uif.employee);
      setW("#o-seg-ra", r.raMonthlyAllowed);
      setW("#o-seg-net", Math.max(0, r.netMonthly));

      const setT = (id, v) => { const el = $(id); if (el) el.textContent = v; };
      setT("#o-paye", rand(r.payeMonthly));
      setT("#o-uif", rand(r.uif.employee));
      setT("#o-ra", rand(r.raMonthlyAllowed));

      // The rows, with the formula that produced each one. The cell
      // references are worked out FIRST, because the optional rows
      // (the pension, the medical credit) shift everything below them.
      const hasRa = r.raAnnual > 0;
      const hasMed = r.medicalCreditAnnual > 0;
      const ref = {};
      let next = 5;                    // B4 is the headline
      ref.gross = `B${next++}`;
      ref.annual = `B${next++}`;
      if (hasRa) ref.ra = `B${next++}`;
      ref.taxable = `B${next++}`;
      ref.slab = `B${next++}`;
      ref.rebate = `B${next++}`;
      if (hasMed) ref.medical = `B${next++}`;
      ref.annualTax = `B${next++}`;
      ref.paye = `B${next++}`;
      ref.uif = `B${next++}`;
      ref.effective = `B${next++}`;
      ref.marginal = `B${next++}`;

      // The medical scheme fees tax credit: the higher of the tabulated
      // credit and what you actually pay for your own membership, plus
      // the credit for the dependants.
      const rates = Tax.TAX_YEARS[taxYear]?.medical_credit;
      const members = Math.max(1, medicalDependants);
      let creditFormula = "=0";
      if (rates && medicalMonthly > 0) {
        const memberPart = Math.max(rates.member, medicalMonthly);
        const firstDep = members >= 2 ? rates.first_dependent : 0;
        const extra = members > 2 ? (members - 2) * rates.additional_dependent : 0;
        creditFormula = `=-(${memberPart} + ${firstDep} + ${extra}) * 12`;
      }

      const rows = [
        { label: "Gross salary (monthly)", value: rand(r.grossMonthly), num: r.grossMonthly,
          ref: ref.gross, formula: `=${Math.round(r.grossMonthly)}` },
        { label: "Annualised gross (× 12)", value: rand(r.grossAnnualised), num: r.grossAnnualised,
          ref: ref.annual, formula: `=${ref.gross}*12` },
        ...(hasRa
          ? [{ label: "Less: retirement / RA deduction", value: randNeg(r.raAnnual), num: -r.raAnnual,
               ref: ref.ra, formula: `=-${Math.round(r.raMonthlyAllowed)}*12` }]
          : []),
        { label: "Taxable income (annual)", value: rand(r.taxableIncome), num: r.taxableIncome,
          ref: ref.taxable, formula: hasRa ? `=${ref.annual}+${ref.ra}` : `=${ref.annual}` },
        { label: "Tax at SARS slab rates", value: rand(r.taxBeforeRebates), num: r.taxBeforeRebates,
          ref: ref.slab, formula: `=44118 + 26%*(${ref.taxable}-245100)   (2027, 2nd band)` },
        { label: `Less: ${r.rebateName}`, value: randNeg(r.rebate), num: -r.rebate,
          ref: ref.rebate, formula: "=-17820" },
        ...(hasMed
          ? [{ label: "Less: medical tax credit", value: randNeg(r.medicalCreditAnnual), num: -r.medicalCreditAnnual,
               ref: ref.medical, formula: creditFormula }]
          : []),
        { label: "Annual tax", value: rand(r.annualTax), num: r.annualTax,
          ref: ref.annualTax,
          formula: hasMed
            ? `=MAX(0, ${ref.slab}+${ref.rebate}+${ref.medical})`
            : `=MAX(0, ${ref.slab}+${ref.rebate})` },
        { label: "Monthly PAYE", value: rand(r.payeMonthly), num: r.payeMonthly,
          ref: ref.paye, formula: `=ROUND(${ref.annualTax}/12, 0)` },
        { label: "UIF employee 1%", value: rand(r.uif.employee), num: r.uif.employee,
          ref: ref.uif, formula: `=MIN(${ref.gross}, 17712) * 1%` },
        { label: "Effective tax rate", value: pct(r.effectiveRate), num: r.effectiveRate,
          ref: ref.effective, formula: `=${ref.annualTax}/${ref.annual}` },
        { label: "Marginal rate (top slab)", value: pct(r.marginalRate, 0), num: r.marginalRate,
          ref: ref.marginal, formula: `=${Math.round(r.marginalRate * 100)}%` },
      ];

      const rowsEl = $("#o-rows");
      if (rowsEl) {
        rowsEl.innerHTML = rows.map((row) => `
          <div class="${row.label === "Annual tax" || row.label === "Taxable income (annual)" ? "is-strong" : ""}">
            <dt>${esc(row.label)}</dt>
            <dd data-num="${row.num}" data-ref="${row.ref}" data-formula="${esc(row.formula)}">${row.value}</dd>
          </div>`).join("");
      }

      // The headline cell, which is the net pay
      if (netEl) {
        netEl.dataset.num = r.netMonthly;
        netEl.dataset.ref = "B4";
        netEl.dataset.formula = hasRa
          ? `=${ref.gross}-${ref.paye}-${ref.uif}+${ref.ra}   (gross - PAYE - UIF + pension)`
          : `=${ref.gross}-${ref.paye}-${ref.uif}   (gross - PAYE - UIF)`;
      }

      if (raHint) {
        raHint.textContent = r.raCapped
          ? `Capped by s11F: 27.5% of salary, max R350,000 a year.`
          : "Deducted before tax, capped by s11F (27.5% / R350,000).";
      }

      renderSlabs(r.brackets, r.taxableIncome);
      updateStatusBar();
      selectCell?.(document.querySelector("[data-formula].is-selected"));
    }

    [salary, age, ra, medical, dependants].forEach((el) => el?.addEventListener("input", update));
    setYear("2027");
    update();
  }

  /* ═══════════════════════════════════════════════════════════════
     14. THE VAT 201 MODEL
     ═══════════════════════════════════════════════════════════════ */
  function initVatDemo() {
    const sales = $("#v-sales");
    const purchases = $("#v-purchases");
    const turnover = $("#v-turnover");
    const yearInputs = $$('input[name="vatyear"]');
    if (!sales || typeof Vat === "undefined") return;

    let taxYear = "2027";

    function render() {
      const s = Math.max(0, Number(sales.value) || 0);
      const p = Math.max(0, Number(purchases.value) || 0);
      const r = Vat.calculateVat(s, p);

      const netEl = $("#v-net");
      const netLabel = $("#v-net-label");
      if (netEl) {
        netEl.textContent = rand(r.isRefund ? r.amountClaimable : r.amountPayable);
        netEl.dataset.num = Math.abs(r.netVat);
        netEl.dataset.ref = "B8";
        netEl.dataset.formula = "=B5-B7  (output tax - input tax)";
      }
      if (netLabel) {
        netLabel.textContent = r.isRefund
          ? "VAT to claim back from SARS"
          : "Net VAT payable to SARS";
      }

      const total = Math.max(r.outputTax, r.inputTax, 1);
      const outEl = $("#v-seg-out");
      const inEl = $("#v-seg-in");
      if (outEl) outEl.style.width = `${(r.outputTax / total) * 100}%`;
      if (inEl) inEl.style.width = `${(r.inputTax / total) * 100}%`;

      const outText = $("#v-output");
      const inText = $("#v-input");
      if (outText) outText.textContent = rand(r.outputTax);
      if (inText) inText.textContent = rand(r.inputTax);

      const rows = [
        { label: "Taxable supplies (sales)", value: rand(r.taxableSupplies), num: r.taxableSupplies,
          ref: "B4", formula: `=${Math.round(s)}` },
        { label: "Output tax @ 15%", value: rand(r.outputTax), num: r.outputTax,
          ref: "B5", formula: "=B4*15%" },
        { label: "Taxable purchases (inputs)", value: rand(r.taxablePurchases), num: r.taxablePurchases,
          ref: "B6", formula: `=${Math.round(p)}` },
        { label: "Input tax @ 15%", value: rand(r.inputTax), num: r.inputTax,
          ref: "B7", formula: "=B6*15%" },
        { label: r.isRefund ? "Net VAT (refund due to you)" : "Net VAT payable to SARS",
          value: rand(Math.abs(r.netVat)), num: Math.abs(r.netVat),
          ref: "B8", formula: "=B5-B7" },
      ];

      const rowsEl = $("#v-rows");
      if (rowsEl) {
        rowsEl.innerHTML = rows.map((row) => `
          <div class="${row.ref === "B8" ? "is-strong" : ""}">
            <dt>${esc(row.label)}</dt>
            <dd data-num="${row.num}" data-ref="${row.ref}" data-formula="${esc(row.formula)}">${row.value}</dd>
          </div>`).join("");
      }

      const periods = $("#v-periods");
      if (periods) {
        periods.innerHTML = Vat.vatPeriods(taxYear)
          .map((period) => `
            <li class="period">
              <span class="period__tag">${period.period}</span>
              <span class="period__dates">${period.label}</span>
              <span class="period__due">due <b>${Vat.fmtDate(period.dueManual)}</b></span>
            </li>`)
          .join("");
      }

      const hint = $("#v-reg-hint");
      if (hint) {
        const t = Math.max(0, Number(turnover.value) || 0);
        const status = Vat.registrationStatus(t);
        hint.textContent = `${status.status} — ${status.detail}`;
      }

      updateStatusBar();
      selectCell?.(document.querySelector("[data-formula].is-selected"));
    }

    [sales, purchases, turnover].forEach((el) => el?.addEventListener("input", render));
    yearInputs.forEach((input) =>
      input.addEventListener("change", () => {
        if (!input.checked) return;
        taxYear = input.value;
        render();
      })
    );

    render();
  }

  /* ═══════════════════════════════════════════════════════════════
     15. THE PAYROLL MODEL
     ═══════════════════════════════════════════════════════════════ */
  function initPayrollDemo() {
    const rows = $("#p-rows");
    const foot = $("#p-foot");
    const cards = $("#p-cards");
    const monthInput = $("#p-month");
    if (!rows || typeof Vat === "undefined") return;

    const payroll = Vat.runPayroll(Vat.DEMO_EMPLOYEES, "2027");

    function render() {
      const value = monthInput?.value || "2026-10";
      const [y, m] = value.split("-").map(Number);
      const year = y || 2026;
      const month = m || 10;
      const payrollMonth = new Date(year, month - 1, 1);
      const summary = Vat.emp201Summary(payroll, payrollMonth);

      rows.innerHTML = payroll.payslips
        .map((p, i) => {
          const ref = `E${i + 5}`;
          return `<tr>
            <td>${esc(p.employee_name)}<span class="ledger__role">${esc(p.employee_number)}</span></td>
            <td class="num" data-num="${p.gross_remuneration}" data-ref="B${i + 5}" data-formula="=basic + overtime + bonus + commission + fringe + leave">${rand(p.gross_remuneration)}</td>
            <td class="num" data-num="${p.paye}" data-ref="C${i + 5}" data-formula="=ROUND(MAX(0, tax on (B${i + 5}-pension)*12 - rebates - medical)/12, 0)">${rand(p.paye)}</td>
            <td class="num" data-num="${p.uif_employee}" data-ref="D${i + 5}" data-formula="=MIN(B${i + 5}, 17712) * 1%">${rand(p.uif_employee)}</td>
            <td class="num" data-num="${p.sdl}" data-ref="E${i + 5}" data-formula="=(B${i + 5} - pension) * 1%">${rand(p.sdl)}</td>
            <td class="num" data-num="${p.net_pay}" data-ref="F${i + 5}" data-formula="=B${i + 5}-C${i + 5}-D${i + 5}-pension-medical">${rand(p.net_pay)}</td>
          </tr>`;
        })
        .join("");

      const sum = (key) => payroll.payslips.reduce((t, p) => t + Number(p[key] || 0), 0);
      foot.innerHTML = `<tr>
        <td>Total</td>
        <td class="num" data-num="${sum("gross_remuneration")}" data-ref="B10" data-formula="=SUM(B5:B9)">${rand(sum("gross_remuneration"))}</td>
        <td class="num" data-num="${sum("paye")}" data-ref="C10" data-formula="=SUM(C5:C9)">${rand(sum("paye"))}</td>
        <td class="num" data-num="${sum("uif_employee")}" data-ref="D10" data-formula="=SUM(D5:D9)">${rand(sum("uif_employee"))}</td>
        <td class="num" data-num="${sum("sdl")}" data-ref="E10" data-formula="=SUM(E5:E9)">${rand(sum("sdl"))}</td>
        <td class="num" data-num="${sum("net_pay")}" data-ref="F10" data-formula="=SUM(F5:F9)">${rand(sum("net_pay"))}</td>
      </tr>`;

      cards.innerHTML = `
        <div class="pcard pcard--due">
          <span class="pcard__label"><svg class="ico"><use href="#i-clock"/></svg> EMP201 due</span>
          <span class="pcard__value">${Vat.fmtLong(summary.dueDate)}</span>
          <span class="pcard__note">Pay PAYE, UIF and SDL by the 7th — or the last business day before it.</span>
        </div>
        <div class="pcard pcard--total">
          <span class="pcard__label"><svg class="ico"><use href="#i-building"/></svg> Total to SARS</span>
          <span class="pcard__value" data-num="${summary.totalLiability}" data-ref="H4" data-formula="=C10 + D10*2 + E10  (PAYE + UIF both sides + SDL)">${rand(summary.totalLiability)}</span>
          <span class="pcard__note">PAYE ${rand(summary.paye)} · UIF ${rand(summary.uifTotal)} · SDL ${rand(summary.sdl)}</span>
        </div>
        <div class="pcard">
          <span class="pcard__label"><svg class="ico"><use href="#i-users"/></svg> Net paid out</span>
          <span class="pcard__value" data-num="${payroll.totalNet}" data-ref="F10" data-formula="=SUM(F5:F9)">${rand(payroll.totalNet)}</span>
          <span class="pcard__note">${payroll.headCount} employees · ${rand(payroll.totalGross)} in gross pay</span>
        </div>
        <div class="pcard">
          <span class="pcard__label"><svg class="ico"><use href="#i-percent"/></svg> Employer cost</span>
          <span class="pcard__value" data-num="${payroll.totalEmployerCost}" data-ref="H6" data-formula="=UIF employer + SDL">${rand(payroll.totalEmployerCost)}</span>
          <span class="pcard__note">UIF ${rand(payroll.totalUifEmployer)} + SDL ${rand(payroll.totalSdl)} on top of salary.</span>
        </div>`;

      updateStatusBar();
      selectCell?.(document.querySelector("[data-formula].is-selected"));
    }

    monthInput?.addEventListener("input", render);
    render();
  }

  /* ═══════════════════════════════════════════════════════════════
     16. COMMAND PALETTE  (Ctrl/⌘ + K)
     ═══════════════════════════════════════════════════════════════ */
  function initPalette() {
    const palette = $("#palette");
    const input = $("#palette-input");
    const list = $("#palette-list");
    if (!palette || !input || !list) return;

    const trigger = $("#cmd-trigger");
    let items = [];
    let matched = [];
    let selected = 0;

    const score = (label, query) => {
      const l = label.toLowerCase();
      if (!query) return 1;
      const index = l.indexOf(query);
      if (index === 0) return 1000;
      if (index > 0) return 700 - index;
      let at = 0, points = 0, streak = 0;
      for (const ch of query) {
        const found = l.indexOf(ch, at);
        if (found === -1) return -1;
        streak = found === at ? streak + 1 : 0;
        points += 10 + streak * 5;
        at = found + 1;
      }
      return points;
    };

    const highlight = (label, query) => {
      if (!query) return esc(label);
      const index = label.toLowerCase().indexOf(query);
      if (index === -1) return esc(label);
      return (
        esc(label.slice(0, index)) +
        `<mark>${esc(label.slice(index, index + query.length))}</mark>` +
        esc(label.slice(index + query.length))
      );
    };

    const buildItems = () => {
      const sheets = SHEETS.map((s) => ({
        label: s.label, sheet: s.id, icon: "i-grid", kind: "Sheet",
      }));
      const projects = PROJECTS.map((p) => ({
        label: p.title,
        href: p.links?.repo || "",
        icon: p.icon,
        kind: STATUS_LABEL[p.status] || "Project",
        external: true,
      }));
      const socials = [
        { label: "GitHub", href: PROFILE.github, icon: "i-github", kind: "Link" },
        { label: "Email me", href: `mailto:${PROFILE.email}`, icon: "i-mail", kind: "Link" },
      ].filter((s) => s.href);
      items = [...sheets, ...projects, ...socials];
    };

    function render(query = "") {
      const q = query.trim().toLowerCase();
      matched = items
        .map((item) => ({ item, score: Math.max(score(item.label, q), score(item.kind, q) / 2) }))
        .filter((entry) => entry.score > 0)
        .sort((a, b) => b.score - a.score)
        .map((entry) => entry.item);

      selected = 0;
      if (!matched.length) {
        list.innerHTML = `<li class="palette__empty">No matches for “${esc(query)}”</li>`;
        return;
      }
      list.innerHTML = matched
        .map(
          (i, idx) => `<li data-idx="${idx}" class="${idx === 0 ? "is-sel" : ""}">
            ${svgIcon(i.icon)}<span>${highlight(i.label, q)}</span><em>${esc(i.kind)}</em>
          </li>`
        )
        .join("");

      $$("li[data-idx]", list).forEach((li) => {
        li.addEventListener("click", () => go(matched[Number(li.dataset.idx)]));
        li.addEventListener("mousemove", () => select(Number(li.dataset.idx)));
      });
    }

    function select(idx) {
      if (!matched.length) return;
      selected = Math.max(0, Math.min(idx, matched.length - 1));
      $$("li[data-idx]", list).forEach((li) =>
        li.classList.toggle("is-sel", Number(li.dataset.idx) === selected)
      );
      const el = list.querySelector(`li[data-idx="${selected}"]`);
      el?.scrollIntoView({ block: "nearest" });
    }

    function go(item) {
      if (!item) return;
      close();
      if (item.sheet) {
        showSheet?.(item.sheet);
      } else if (item.href?.startsWith("http")) {
        window.open(item.href, "_blank", "noopener");
      } else if (item.href?.startsWith("mailto:")) {
        window.location.href = item.href;
      }
    }

    function focusables() {
      return $$(
        'a[href], button:not([disabled]), input, [tabindex]:not([tabindex="-1"])',
        palette
      ).filter((el) => el.offsetParent !== null);
    }

    function onKeydownTab(e) {
      const els = focusables();
      if (!els.length) return;
      const first = els[0];
      const last = els[els.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    let lastFocused = null;

    function open() {
      lastFocused = document.activeElement;
      buildItems();
      palette.removeAttribute("hidden");
      input.value = "";
      render("");
      setTimeout(() => input.focus(), 30);
    }
    function close() {
      if (palette.hasAttribute("hidden")) return;
      palette.setAttribute("hidden", "");
      if (lastFocused && document.contains(lastFocused)) lastFocused.focus();
      else trigger?.focus();
    }

    trigger?.addEventListener("click", open);
    $$("[data-close-palette]").forEach((el) => el.addEventListener("click", close));
    input.addEventListener("input", () => render(input.value));

    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); select(Math.min(selected + 1, matched.length - 1)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); select(Math.max(selected - 1, 0)); }
      else if (e.key === "Enter") { e.preventDefault(); list.querySelector(`li[data-idx="${selected}"]`)?.click(); }
    });

    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        palette.hasAttribute("hidden") ? open() : close();
      }
      if (e.key === "Escape" && !palette.hasAttribute("hidden")) close();
      if (e.key === "Tab" && !palette.hasAttribute("hidden")) onKeydownTab(e);
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     17. CURSOR GLOW + CARD TILT
     ═══════════════════════════════════════════════════════════════ */
  const isLite = () => document.documentElement.classList.contains("is-lite");

  function initPointerFx() {
    const glow = $(".fx__cursor");
    const fine = window.matchMedia?.("(pointer: fine)").matches;
    if (!fine) return;

    let x = window.innerWidth / 2, y = window.innerHeight / 2;
    let cx = x, cy = y, raf = null;

    window.addEventListener("mousemove", (e) => {
      if (isLite()) return;
      x = e.clientX; y = e.clientY;
      glow?.classList.add("is-on");
      if (!raf) raf = requestAnimationFrame(loop);
    });

    function loop() {
      cx += (x - cx) * 0.12;
      cy += (y - cy) * 0.12;
      if (glow) glow.style.transform = `translate(${cx}px, ${cy}px) translate(-50%, -50%)`;
      raf = Math.abs(x - cx) > 0.5 || Math.abs(y - cy) > 0.5 ? requestAnimationFrame(loop) : null;
    }

    $$(".card").forEach((card) => {
      let targetX = 0, targetY = 0, currentX = 0, currentY = 0;
      let tiltRaf = null;
      let hovering = false;

      const paint = () => {
        currentX += (targetX - currentX) * 0.14;
        currentY += (targetY - currentY) * 0.14;
        const lift = hovering ? -6 : 0;
        card.style.transform =
          `perspective(900px) rotateY(${currentX.toFixed(2)}deg) ` +
          `rotateX(${(-currentY).toFixed(2)}deg) translateY(${lift}px)`;
        tiltRaf =
          Math.abs(targetX - currentX) > 0.05 || Math.abs(targetY - currentY) > 0.05
            ? requestAnimationFrame(paint)
            : null;
      };

      const kick = () => { if (!tiltRaf) tiltRaf = requestAnimationFrame(paint); };

      card.addEventListener("mousemove", (e) => {
        if (isLite()) return;
        const r = card.getBoundingClientRect();
        targetX = ((e.clientX - r.left) / r.width - 0.5) * 7;
        targetY = ((e.clientY - r.top) / r.height - 0.5) * 7;
        hovering = true;
        card.classList.add("is-tilting");
        kick();
      });

      card.addEventListener("mouseenter", () => {
        if (isLite()) return;
        hovering = true;
        card.classList.add("is-tilting");
        kick();
      });

      card.addEventListener("mouseleave", () => {
        targetX = 0; targetY = 0; hovering = false;
        card.classList.remove("is-tilting");
        kick();
      });
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     18. PERFORMANCE MODE
     ═══════════════════════════════════════════════════════════════ */
  let toastTimer = null;
  function showToast(html) {
    const toast = $("#toast");
    if (!toast) return;
    toast.innerHTML = html;
    toast.removeAttribute("hidden");
    requestAnimationFrame(() => toast.classList.add("is-in"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove("is-in");
      setTimeout(() => toast.setAttribute("hidden", ""), 400);
    }, 5200);
  }

  function setLiteMode(on, remember = true) {
    const root = document.documentElement;
    root.classList.toggle("is-lite", on);
    if (remember) store.set("portfolio-lite", on ? "1" : "0");

    const btn = $("#lite-toggle");
    if (btn) {
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-pressed", String(on));
      btn.title = on
        ? "Performance mode on — turn the effects back on"
        : "Performance mode off — turn the effects off for smoother scrolling";
    }
  }

  function initPerformanceMode() {
    const btn = $("#lite-toggle");
    const stored = store.get("portfolio-lite");

    if (stored === "1") setLiteMode(true, false);
    if (stored === "0") setLiteMode(false, false);

    btn?.addEventListener("click", () => setLiteMode(!isLite()));
  }

  function initPerformanceWatch() {
    if (store.get("portfolio-lite") !== null) return;

    let frames = 0, slow = 0, last = 0, ticks = 0, sampling = false;

    const sample = (now) => {
      if (last) {
        frames++;
        if (now - last > 26) slow++;
      }
      last = now;
      ticks++;
      if (ticks < 180) {
        requestAnimationFrame(sample);
        return;
      }
      sampling = false;
      if (frames >= 20 && slow / frames > 0.3) {
        setLiteMode(true, false);
        showToast(
          "<b>Performance mode on.</b> The background effects were slowing " +
          "your scrolling down, so they have been switched off. Turn them " +
          "back on with the gauge in the toolbar."
        );
      }
    };

    // The sheets scroll, not the window, so listen to the container.
    const scroller = $("#sheets") || document;
    scroller.addEventListener("scroll", () => {
      if (sampling) return;
      sampling = true;
      ticks = 0; frames = 0; slow = 0; last = 0;
      requestAnimationFrame(sample);
    }, { passive: true });
  }

  /* ═══════════════════════════════════════════════════════════════
     19. BOOT
     ═══════════════════════════════════════════════════════════════ */
  function boot() {
    initTheme();
    initShortcutHint();
    initPerformanceMode();
    initSheets();
    initCells();
    renderStats();
    initTerminal();
    initMarquee();
    renderFocus();
    renderProjects();
    renderTimeline();
    renderSkills();
    renderContact();
    initCalculator();
    initVatDemo();
    initPayrollDemo();
    initPalette();
    initPointerFx();
    initPerformanceWatch();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
