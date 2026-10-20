/* ═══════════════════════════════════════════════════════════════════
   main.js — everything that moves.
   All content is rendered from data.js so you only edit one file.
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
  /* Negative amounts render the way a payslip does: (R17,820.00) */
  const randNeg = (n) => {
    const v = Math.abs(Number(n) || 0);
    return `(R${v.toLocaleString("en-ZA", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })})`;
  };
  const num = (n) => Number(n || 0).toLocaleString("en-ZA");
  const pct = (n, dp = 1) => `${(n * 100).toFixed(dp)}%`;

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  /* The demo tabs can be opened from the command palette as well as by
     clicking them, so the tab picker lives one level up. */
  let selectDemoTab = null;

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
     2. NAV — sticky state, active link, mobile drawer
     ═══════════════════════════════════════════════════════════════ */
  function initNav() {
    const nav = $("#nav");
    const burger = $("#burger");
    const drawer = $("#drawer");
    const links = $$(".nav__links a");

    // sticky background
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        nav?.classList.toggle("is-stuck", window.scrollY > 12);
        ticking = false;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    // mobile drawer
    const closeDrawer = () => {
      drawer?.setAttribute("hidden", "");
      burger?.classList.remove("is-open");
      burger?.setAttribute("aria-expanded", "false");
    };
    burger?.addEventListener("click", () => {
      const open = drawer?.hasAttribute("hidden");
      if (open) {
        drawer?.removeAttribute("hidden");
        burger.classList.add("is-open");
        burger.setAttribute("aria-expanded", "true");
      } else {
        closeDrawer();
      }
    });
    $$("a", drawer).forEach((a) => a.addEventListener("click", closeDrawer));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeDrawer();
    });

    // active section highlighting
    const sections = $$("main section[id]");
    const spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = entry.target.id;
          links.forEach((l) =>
            l.classList.toggle("is-active", l.getAttribute("href") === `#${id}`)
          );
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );
    sections.forEach((s) => spy.observe(s));
  }

  /* ═══════════════════════════════════════════════════════════════
     3. SCROLL REVEAL
     ═══════════════════════════════════════════════════════════════ */
  function initReveal() {
    const items = $$("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      items.forEach((i) => i.classList.add("is-in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    items.forEach((i) => io.observe(i));
  }

  /* ═══════════════════════════════════════════════════════════════
     4. HERO — stats counters
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
     5. HERO — terminal animation
     ═══════════════════════════════════════════════════════════════ */
  /* Reproduces the real cli.py report, column for column.
     Python formats each row as: 2 spaces + label padded to 44
     characters + amount right-justified in 20 characters.          */
  const termRow = (label, value, cls = "t-val") => {
    // Split the label into its text and its trailing dot leader. The dots
    // may or may not be preceded by a space, e.g. "...(capped)...".
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
     6. MARQUEE
     ═══════════════════════════════════════════════════════════════ */
  function initMarquee() {
    const track = $("#marquee-track");
    if (!track) return;
    const items = MARQUEE.map((m) => `<span class="marquee__item"><i></i>${esc(m)}</span>`).join("");
    track.innerHTML = items + items; // duplicated for a seamless loop
  }

  /* ═══════════════════════════════════════════════════════════════
     7. ABOUT — focus list
     ═══════════════════════════════════════════════════════════════ */
  function renderFocus() {
    const list = $("#focus-list");
    if (!list) return;
    list.innerHTML = FOCUS.map(
      (f) => `<li>${svgIcon(f.icon)}<span>${esc(f.text)}</span></li>`
    ).join("");
  }

  /* ═══════════════════════════════════════════════════════════════
     8. PROJECTS
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
    if (p.links?.demo)  links.push(`<a class="card__link card__link--accent" href="${esc(p.links.demo)}">${svgIcon("i-spark")} Live demo</a>`);
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

    // filters
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
  }

  /* ═══════════════════════════════════════════════════════════════
     9. TIMELINE
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
     10. SKILLS
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
     11. CONTACT
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
     12. THE LIVE TAX CALCULATOR
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

      // Width of each income band. The open-ended top band borrows the
      // width of the band below it so the bar length stays comparable.
      const widths = brackets.map((b, i) => {
        if (b.to !== null) return b.to - b.from;
        const prev = brackets[i - 1];
        return prev ? prev.to - prev.from : 1;
      });
      const max = Math.max(...widths, 1);

      // Exactly one bracket is active, and it is the same one the tax
      // engine used: the first band whose ceiling is >= the income.
      // (A simple per-row test would light up two bands whenever the
      // income landed exactly on a boundary.)
      let activeIndex = brackets.findIndex(
        (b) => b.to === null || taxableIncome <= b.to
      );
      if (activeIndex === -1) activeIndex = brackets.length - 1;

      wrap.innerHTML = brackets
        .map((b, i) => {
          // sqrt keeps the narrow low bands visible instead of vanishing
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

      // headline
      const netEl = $("#o-net");
      if (netEl) netEl.textContent = rand(r.netMonthly);
      const netLegend = $("#o-net-legend");
      if (netLegend) netLegend.textContent = rand(r.netMonthly);

      // bar
      const total = Math.max(r.grossMonthly, 1);
      const setW = (id, v) => { const el = $(id); if (el) el.style.width = `${(v / total) * 100}%`; };
      setW("#o-seg-tax", r.payeMonthly);
      setW("#o-seg-uif", r.uif.employee);
      setW("#o-seg-ra", r.raMonthlyAllowed);
      setW("#o-seg-net", Math.max(0, r.netMonthly));

      // legend
      const setT = (id, v) => { const el = $(id); if (el) el.textContent = v; };
      setT("#o-paye", rand(r.payeMonthly));
      setT("#o-uif", rand(r.uif.employee));
      setT("#o-ra", rand(r.raMonthlyAllowed));

      // rows
      const rows = $("#o-rows");
      if (rows) {
        let raRow = "";
        if (r.raAnnual > 0) {
          raRow =
            `<div><dt>Less: retirement / RA deduction</dt><dd>${randNeg(r.raAnnual)}</dd></div>`;
          if (r.raCapped) {
            raRow +=
              `<div class="is-muted"><dt>&nbsp;&nbsp;capped by s11F (27.5% / R350 000)</dt><dd></dd></div>`;
          }
        }
        rows.innerHTML = `
          <div><dt>Gross salary (monthly)</dt><dd>${rand(r.grossMonthly)}</dd></div>
          <div><dt>Annualised gross (× 12)</dt><dd>${rand(r.grossAnnual)}</dd></div>
          ${raRow}
          <div class="is-strong"><dt>Taxable income (annual)</dt><dd>${rand(r.taxableIncome)}</dd></div>
          <div><dt>Tax at SARS slab rates</dt><dd>${rand(r.taxBeforeRebates)}</dd></div>
          <div><dt>Less: ${esc(r.rebateName)}</dt><dd>${randNeg(r.rebate)}</dd></div>
          ${r.medicalCreditAnnual > 0
            ? `<div><dt>Less: medical tax credit</dt><dd>${randNeg(r.medicalCreditAnnual)}</dd></div>`
            : ""}
          <div class="is-strong"><dt>Annual tax</dt><dd>${rand(r.annualTax)}</dd></div>
          <div class="is-strong"><dt>Monthly PAYE</dt><dd>${rand(r.payeMonthly)}</dd></div>
          <div><dt>UIF employee 1%${r.uif.base < r.grossMonthly ? " (capped)" : ""}</dt><dd>${rand(r.uif.employee)}</dd></div>
          <div class="is-muted"><dt>UIF employer 1% (business cost)</dt><dd>${rand(r.uif.employer)}</dd></div>
          <div><dt>Effective tax rate</dt><dd>${pct(r.effectiveRate)}</dd></div>
          <div><dt>Marginal rate (top slab)</dt><dd>${pct(r.marginalRate, 0)}</dd></div>`;
      }

      // s11F hint
      if (raHint) {
        raHint.textContent = r.raCapped
          ? `Capped by s11F: 27.5% of salary, max R350,000 a year.`
          : "Deducted before tax, capped by s11F (27.5% / R350,000).";
      }

      renderSlabs(r.brackets, r.taxableIncome);
    }

    [salary, age, ra, medical, dependants].forEach((el) => el?.addEventListener("input", update));
    setYear("2027");
    update();
  }

  /* ═══════════════════════════════════════════════════════════════
     13. SCROLL PROGRESS
     The bar is scaled with a transform, not a width: a transform is
     handled by the compositor, while a width change asks the browser
     to lay the element out again on every frame.
     ═══════════════════════════════════════════════════════════════ */
  function initScrollProgress() {
    const bar = $("#progress-bar");
    if (!bar) return;

    let ticking = false;
    let max = 0;

    // scrollHeight is a layout read, so it is measured on resize rather
    // than on every frame of the scroll.
    const measure = () => {
      const doc = document.documentElement;
      max = doc.scrollHeight - doc.clientHeight;
    };

    const update = () => {
      const percent = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      bar.style.transform = `scaleX(${percent})`;
    };

    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => { update(); ticking = false; });
    }, { passive: true });

    window.addEventListener("resize", () => { measure(); update(); }, { passive: true });

    measure();
    update();
    // The page grows once the fonts land and the demos render.
    window.addEventListener("load", () => { measure(); update(); });
    setTimeout(() => { measure(); update(); }, 600);
  }

  /* ═══════════════════════════════════════════════════════════════
     14. PERFORMANCE MODE
     The drifting background, the frosted glass and the 3D tilt are
     decoration. On a laptop with integrated graphics they can cost
     more than the whole page is worth, so the page watches its own
     frame rate while you scroll and turns the decoration off if it
     cannot keep up. You can also switch it off by hand.
     ═══════════════════════════════════════════════════════════════ */
  const isLite = () => document.documentElement.classList.contains("is-lite");

  /* A small message at the bottom of the screen. */
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

    // "null" means the reader has never made a choice, so the page is
    // allowed to decide for itself.
    if (stored === "1") setLiteMode(true, false);
    if (stored === "0") setLiteMode(false, false);

    btn?.addEventListener("click", () => {
      setLiteMode(!isLite());
    });
  }

  function initPerformanceWatch() {
    // Only ever decide once, and only if the reader has not said
    // otherwise themselves.
    if (store.get("portfolio-lite") !== null) return;

    let scrolling = false;
    let scrollEnd = null;
    let sampling = false;
    let ticks = 0;
    let frames = 0;
    let slow = 0;
    let last = 0;

    const sample = (now) => {
      if (scrolling) {
        if (last) {
          frames++;
          if (now - last > 26) slow++;     // slower than about 38fps
        }
        last = now;
      } else {
        last = 0;
      }

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
          "back on with the gauge in the navigation bar."
        );
      }
    };

    window.addEventListener("scroll", () => {
      scrolling = true;
      clearTimeout(scrollEnd);
      scrollEnd = setTimeout(() => { scrolling = false; }, 180);

      if (!sampling) {
        sampling = true;
        ticks = 0; frames = 0; slow = 0; last = 0;
        requestAnimationFrame(sample);
      }
    }, { passive: true });
  }

  /* ═══════════════════════════════════════════════════════════════
     14. SMOOTH SCROLLING
     A short eased glide instead of the browser's default jump. It
     stops the moment the reader takes over the scroll themselves.
     ═══════════════════════════════════════════════════════════════ */
  const reducedMotion = () =>
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  /* How far below the top of the document a section should land, so the
     sticky navigation never covers the heading. */
  const navOffset = () => ($("#nav")?.offsetHeight || 72) + 16;

  let scrollToken = 0;

  function scrollToY(targetY, duration = 720) {
    const token = ++scrollToken;
    const startY = window.scrollY;
    const distance = targetY - startY;
    const root = document.documentElement;

    // The stylesheet sets `scroll-behavior: smooth`, which would fight
    // the animation below, so it is switched off for the duration.
    const previousBehaviour = root.style.scrollBehavior;
    const restore = () => { root.style.scrollBehavior = previousBehaviour; };

    if (Math.abs(distance) < 2 || reducedMotion()) {
      root.style.scrollBehavior = "auto";
      window.scrollTo(0, targetY);
      restore();
      return;
    }

    const easeInOutCubic = (t) =>
      t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

    root.style.scrollBehavior = "auto";
    const start = performance.now();
    const step = (now) => {
      if (token !== scrollToken) { restore(); return; }   // the reader interrupted us
      const t = Math.min((now - start) / duration, 1);
      window.scrollTo(0, startY + distance * easeInOutCubic(t));
      if (t < 1) requestAnimationFrame(step);
      else restore();
    };
    requestAnimationFrame(step);
  }

  function initSmoothScroll() {
    // Any manual scroll cancels the animation in progress.
    const interrupt = () => { scrollToken++; };
    ["wheel", "touchstart", "keydown"].forEach((evt) =>
      window.addEventListener(evt, interrupt, { passive: true })
    );
    document.addEventListener("click", (e) => {
      const link = e.target.closest?.('a[href^="#"]');
      if (!link) return;
      const id = link.getAttribute("href");
      if (!id || id === "#" || link.hasAttribute("data-no-scroll")) return;

      const target = document.querySelector(id);
      if (!target) return;

      e.preventDefault();
      scrollToY(target.getBoundingClientRect().top + window.scrollY - navOffset());

      // Move the keyboard focus too, so tabbing continues from the new
      // section instead of jumping back to the top of the document.
      if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
      target.focus({ preventScroll: true });

      try { history.replaceState(null, "", id); } catch { /* file:// */ }
    });
  }

  /* Scroll to a section, used by the command palette too. */
  function scrollToSection(selector) {
    const target = document.querySelector(selector);
    if (!target) return;
    scrollToY(target.getBoundingClientRect().top + window.scrollY - navOffset());
  }

  /* ═══════════════════════════════════════════════════════════════
     15. NAV INDICATOR — a pill that slides to the active link
     ═══════════════════════════════════════════════════════════════ */
  function initNavIndicator() {
    const container = $(".nav__links");
    const indicator = $("#nav-indicator");
    const links = $$(".nav__links a");
    if (!container || !indicator || !links.length) return;

    const place = (link) => {
      if (!link) { indicator.classList.remove("is-on"); return; }
      const box = container.getBoundingClientRect();
      const rect = link.getBoundingClientRect();
      indicator.style.width = `${rect.width}px`;
      indicator.style.height = `${rect.height}px`;
      indicator.style.transform = `translateX(${rect.left - box.left}px)`;
      indicator.style.top = `${rect.top - box.top}px`;
      indicator.classList.add("is-on");
    };

    const sync = () => place(links.find((l) => l.classList.contains("is-active")));

    // The active class is toggled by the scroll spy, so watch for it.
    const observer = new MutationObserver(sync);
    links.forEach((l) =>
      observer.observe(l, { attributes: true, attributeFilter: ["class"] })
    );
    window.addEventListener("resize", sync, { passive: true });
    sync();
  }

  /* ═══════════════════════════════════════════════════════════════
     16. TABS — the live demos
     ═══════════════════════════════════════════════════════════════ */
  function initTabs() {
    const tabs = $$(".demo__tab");
    if (!tabs.length) return;

    const select = (tab, moveFocus = false) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
      if (moveFocus) tab.focus();
    };

    // The command palette can open a demo tab directly.
    selectDemoTab = (name) => {
      const tab = tabs.find((t) => t.dataset.tab === name);
      if (tab) select(tab);
    };

    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => select(tab));
      tab.addEventListener("keydown", (e) => {
        let next = null;
        if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === "Home") next = tabs[0];
        else if (e.key === "End") next = tabs[tabs.length - 1];
        if (!next) return;
        e.preventDefault();
        select(next, true);
      });
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     17. THE VAT 201 DEMO
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

      // headline
      const netEl = $("#v-net");
      const netLabel = $("#v-net-label");
      if (netEl) netEl.textContent = rand(r.isRefund ? r.amountClaimable : r.amountPayable);
      if (netLabel) {
        netLabel.textContent = r.isRefund
          ? "VAT to claim back from SARS"
          : "Net VAT payable to SARS";
      }

      // bar: output tax against input tax
      const total = Math.max(r.outputTax, r.inputTax, 1);
      const outEl = $("#v-seg-out");
      const inEl = $("#v-seg-in");
      if (outEl) outEl.style.width = `${(r.outputTax / total) * 100}%`;
      if (inEl) inEl.style.width = `${(r.inputTax / total) * 100}%`;

      const outText = $("#v-output");
      const inText = $("#v-input");
      if (outText) outText.textContent = rand(r.outputTax);
      if (inText) inText.textContent = rand(r.inputTax);

      // rows
      const rows = $("#v-rows");
      if (rows) {
        rows.innerHTML = `
          <div><dt>Taxable supplies (sales)</dt><dd>${rand(r.taxableSupplies)}</dd></div>
          <div><dt>Output tax @ ${r.vatRate * 100}%</dt><dd>${rand(r.outputTax)}</dd></div>
          <div><dt>Taxable purchases (inputs)</dt><dd>${rand(r.taxablePurchases)}</dd></div>
          <div><dt>Input tax @ ${r.vatRate * 100}%</dt><dd>${rand(r.inputTax)}</dd></div>
          <div class="is-strong"><dt>${r.isRefund ? "Net VAT (refund due to you)" : "Net VAT payable to SARS"}</dt><dd>${rand(Math.abs(r.netVat))}</dd></div>`;
      }

      // the six VAT periods and their deadlines
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

      // registration check
      const hint = $("#v-reg-hint");
      if (hint) {
        const t = Math.max(0, Number(turnover.value) || 0);
        const status = Vat.registrationStatus(t);
        hint.textContent = `${status.status} — ${status.detail}`;
      }
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
     18. THE PAYROLL & EMP201 DEMO
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
        .map(
          (p) => `<tr>
            <td>${esc(p.name)}</td>
            <td class="num">${rand(p.grossMonthly)}</td>
            <td class="num">${rand(p.payeMonthly)}</td>
            <td class="num">${rand(p.uifEmployee)}</td>
            <td class="num">${rand(p.sdl)}</td>
            <td class="num">${rand(p.netMonthly)}</td>
          </tr>`
        )
        .join("");

      foot.innerHTML = `<tr>
        <td>Total</td>
        <td class="num">${rand(payroll.totalGross)}</td>
        <td class="num">${rand(payroll.totalPaye)}</td>
        <td class="num">${rand(payroll.totalUifEmployee)}</td>
        <td class="num">${rand(payroll.totalSdl)}</td>
        <td class="num">${rand(payroll.totalNet)}</td>
      </tr>`;

      cards.innerHTML = `
        <div class="pcard pcard--due">
          <span class="pcard__label"><svg class="ico"><use href="#i-clock"/></svg> EMP201 due</span>
          <span class="pcard__value">${Vat.fmtLong(summary.dueDate)}</span>
          <span class="pcard__note">Pay PAYE, UIF and SDL by the 7th — or the last business day before it.</span>
        </div>
        <div class="pcard pcard--total">
          <span class="pcard__label"><svg class="ico"><use href="#i-building"/></svg> Total to SARS</span>
          <span class="pcard__value">${rand(summary.totalLiability)}</span>
          <span class="pcard__note">PAYE ${rand(summary.paye)} · UIF ${rand(summary.uifTotal)} · SDL ${rand(summary.sdl)}</span>
        </div>
        <div class="pcard">
          <span class="pcard__label"><svg class="ico"><use href="#i-users"/></svg> Net paid out</span>
          <span class="pcard__value">${rand(payroll.totalNet)}</span>
          <span class="pcard__note">${payroll.headCount} employees · ${rand(payroll.totalGross)} in gross pay</span>
        </div>
        <div class="pcard">
          <span class="pcard__label"><svg class="ico"><use href="#i-percent"/></svg> Employer cost</span>
          <span class="pcard__value">${rand(payroll.totalEmployerCost)}</span>
          <span class="pcard__note">UIF ${rand(payroll.totalUifEmployer)} + SDL ${rand(payroll.totalSdl)} on top of salary.</span>
        </div>`;
    }

    monthInput?.addEventListener("input", render);
    render();
  }

  /* ═══════════════════════════════════════════════════════════════
     18. COMMAND PALETTE  (Ctrl/⌘ + K)
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

    const buildItems = () => {
      const sections = PALETTE_SECTIONS.map((s) => ({
        label: s.label, href: s.href, icon: "i-arrow", kind: "Section",
      }));
      const demos = (typeof PALETTE_DEMOS !== "undefined" ? PALETTE_DEMOS : []).map((d) => ({
        label: d.label, href: d.href, icon: d.icon || "i-spark",
        kind: "Live demo", tab: d.tab,
      }));
      const projects = PROJECTS.map((p) => ({
        label: p.title,
        href: p.links?.demo || p.links?.repo || "#work",
        icon: p.icon,
        kind: STATUS_LABEL[p.status] || "Project",
        external: !!(p.links?.repo && !p.links?.demo),
      }));
      const socials = [
        { label: "GitHub", href: PROFILE.github, icon: "i-github", kind: "Link" },
        { label: "LinkedIn", href: PROFILE.linkedin, icon: "i-linkedin", kind: "Link" },
        { label: "Email me", href: `mailto:${PROFILE.email}`, icon: "i-mail", kind: "Link" },
      ].filter((s) => s.href);
      items = [...sections, ...demos, ...projects, ...socials];
    };

    /* Fuzzy matching: an exact substring wins, otherwise the letters
       just have to appear in order. */
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
      if (item.href?.startsWith("http")) {
        window.open(item.href, "_blank", "noopener");
      } else if (item.href?.startsWith("mailto:")) {
        window.location.href = item.href;
      } else if (item.href) {
        scrollToSection(item.href);
        if (item.tab) selectDemoTab?.(item.tab);
      }
    }

    /* The panel is a modal dialog, so focus has to stay inside it and
       has to come back out again when it closes. */
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
      // Send focus back where it came from instead of dumping it on <body>.
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
      // Keep Tab inside the dialog while it is open.
      if (e.key === "Tab" && !palette.hasAttribute("hidden")) onKeydownTab(e);
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     19. CURSOR GLOW + CARD TILT
     ═══════════════════════════════════════════════════════════════ */
  function initPointerFx() {
    const glow = $(".fx__cursor");
    const fine = window.matchMedia?.("(pointer: fine)").matches;
    if (!fine) return;

    let x = window.innerWidth / 2, y = window.innerHeight / 2;
    let cx = x, cy = y, raf = null;

    window.addEventListener("mousemove", (e) => {
      if (isLite()) return;             // no point moving a glow nobody sees
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

    // 3D tilt on project cards. The card eases towards the pointer
    // instead of snapping to it, which is what makes it feel smooth.
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
     20. BOOT
     ═══════════════════════════════════════════════════════════════ */
  function boot() {
    initTheme();
    initPerformanceMode();
    initNav();
    initScrollProgress();
    initSmoothScroll();
    initNavIndicator();
    initReveal();
    renderStats();
    initTerminal();
    initMarquee();
    renderFocus();
    renderProjects();
    renderTimeline();
    renderSkills();
    renderContact();
    initTabs();
    initCalculator();
    initVatDemo();
    initPayrollDemo();
    initPalette();
    initPointerFx();
    initPerformanceWatch();

    const y = $("#year");
    if (y) y.textContent = new Date().getFullYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
