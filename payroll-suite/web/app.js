/* ═══════════════════════════════════════════════════════════════════
   app.js — the dashboard.

   Everything the browser draws is calculated by the Python engine and
   fetched over the JSON API. The charts are hand-drawn SVG: no
   charting library, no build step.
   ═══════════════════════════════════════════════════════════════════ */

(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const money = (n) =>
    "R " + Number(n || 0).toLocaleString("en-ZA", {
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
  const moneyShort = (n) => {
    const v = Number(n || 0);
    if (v >= 1_000_000) return "R " + (v / 1_000_000).toFixed(2) + "m";
    if (v >= 1_000) return "R " + (v / 1_000).toFixed(1) + "k";
    return "R " + v.toFixed(0);
  };
  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  const state = {
    overview: null,
    employees: [],
    payslips: [],
    period: null,
    emp201: null,
    deadlines: [],
  };

  // ----------------------------------------------------------------------
  // API
  // ----------------------------------------------------------------------
  async function api(path, options) {
    const response = await fetch(path, options);
    const text = await response.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch { data = { error: text }; }
    if (!response.ok) throw new Error(data?.error || `Request failed (${response.status})`);
    return data;
  }

  function toast(message, isError = false) {
    const el = $("#toast");
    el.textContent = message;
    el.classList.toggle("is-error", isError);
    el.removeAttribute("hidden");
    requestAnimationFrame(() => el.classList.add("is-in"));
    clearTimeout(el._timer);
    el._timer = setTimeout(() => {
      el.classList.remove("is-in");
      setTimeout(() => el.setAttribute("hidden", ""), 350);
    }, 4200);
  }

  // ----------------------------------------------------------------------
  // RENDERING
  // ----------------------------------------------------------------------
  function renderKpis() {
    const o = state.overview;
    if (!o) return;
    const t = o.totals || {};
    const period = state.period;

    const gross = t.total_gross || 0;
    const employerCost = t.total_employer_cost || 0;
    const total = gross + employerCost;

    $("#kpi-cost").textContent = money(total);
    $("#kpi-cost-note").textContent = `${money(gross)} gross plus ${money(employerCost)} of employer taxes`;
    $("#kpi-paye").textContent = money(t.total_paye || 0);
    $("#kpi-net").textContent = money(t.total_net || 0);
    $("#kpi-head").textContent = String(t.head_count || 0);
    $("#kpi-head-note").textContent = period ? `Paid in ${prettyPeriod(period)}` : "No payroll run yet";
  }

  function prettyPeriod(period) {
    const [y, m] = period.split("-").map(Number);
    const names = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"];
    return `${names[m - 1]} ${y}`;
  }

  function renderChart() {
    const host = $("#chart");
    const trend = (state.overview?.trend || []).slice(-8);
    if (!trend.length) {
      host.innerHTML = `<p class="panel__sub">Run a payroll and the trend appears here.</p>`;
      return;
    }

    const W = 760, H = 300;
    const padL = 56, padR = 12, padT = 18, padB = 40;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;
    const max = Math.max(...trend.map((d) => d.cost)) * 1.12 || 1;

    const groupW = plotW / trend.length;
    const barW = Math.min(26, groupW * 0.3);
    const gap = 4;

    const y = (value) => padT + plotH - (value / max) * plotH;

    // horizontal gridlines
    let grid = "";
    for (let i = 0; i <= 4; i++) {
      const value = (max / 4) * i;
      const yy = y(value);
      grid += `<line class="chart__grid" x1="${padL}" y1="${yy}" x2="${W - padR}" y2="${yy}"/>
               <text class="chart__label" x="${padL - 10}" y="${yy + 3}" text-anchor="end">${moneyShort(value)}</text>`;
    }

    let bars = "";
    trend.forEach((d, i) => {
      const cx = padL + groupW * i + groupW / 2;
      const costH = plotH - (y(d.cost) - padT);
      const grossH = plotH - (y(d.gross) - padT);
      bars += `
        <g class="chart__bar">
          <title>${prettyPeriod(d.period)} — total cost ${money(d.cost)}, gross ${money(d.gross)}</title>
          <rect class="chart__cost" x="${cx - barW - gap / 2}" y="${y(d.cost)}" width="${barW}" height="${Math.max(0, costH)}" rx="5"/>
          <rect class="chart__gross" x="${cx + gap / 2}" y="${y(d.gross)}" width="${barW}" height="${Math.max(0, grossH)}" rx="5"/>
          <text class="chart__label" x="${cx}" y="${H - padB + 18}" text-anchor="middle">${monthLabel(d.period)}</text>
          <text class="chart__value" x="${cx}" y="${y(d.cost) - 7}" text-anchor="middle">${moneyShort(d.cost)}</text>
        </g>`;
    });

    host.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Payroll cost by month">
        <defs>
          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#67e8f9"/>
            <stop offset="100%" stop-color="#a78bfa"/>
          </linearGradient>
        </defs>
        ${grid}
        <line class="chart__axis" x1="${padL}" y1="${padT + plotH}" x2="${W - padR}" y2="${padT + plotH}"/>
        ${bars}
      </svg>`;
  }

  function monthLabel(period) {
    const [y, m] = period.split("-").map(Number);
    const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return `${names[m - 1]} ${String(y).slice(2)}`;
  }

  function renderEmp201() {
    const e = state.emp201;
    if (!e) {
      $("#e-total").textContent = "—";
      $("#e-due").textContent = "no payroll run";
      return;
    }
    $("#e-remun").textContent = money(e.total_remuneration);
    $("#e-paye").textContent = money(e.paye);
    $("#e-uif").textContent = money(e.uif_total);
    $("#e-sdl").textContent = money(e.sdl);
    $("#e-total").textContent = money(e.total_liability);
    $("#e-due").textContent = new Date(e.due_date).toLocaleDateString("en-ZA", {
      day: "2-digit", month: "long", year: "numeric",
    });
  }

  function renderDeadlines() {
    const list = $("#deadlines");
    const items = state.deadlines.filter((d) => d.days >= 0).slice(0, 6);
    if (!items.length) {
      list.innerHTML = `<li class="deadline"><span class="deadline__detail">Nothing due in the next few months.</span></li>`;
      return;
    }
    list.innerHTML = items.map((d) => {
      const when = new Date(d.date).toLocaleDateString("en-ZA", {
        day: "2-digit", month: "short", year: "numeric",
      });
      const badge = d.days === 0 ? "is-now" : d.days <= 7 ? "is-soon" : "";
      const text = d.days === 0 ? "today" : d.days === 1 ? "tomorrow" : `${d.days} days`;
      return `<li class="deadline">
        <span class="deadline__date">${esc(when)}</span>
        <span>
          <span class="deadline__name">${esc(d.name)}</span>
          <span class="deadline__detail">${esc(d.detail)}</span>
        </span>
        <span class="deadline__days ${badge}">${text}</span>
      </li>`;
    }).join("");
  }

  function renderLedger() {
    const body = $("#ledger-body");
    const foot = $("#ledger-foot");
    if (!state.payslips.length) {
      body.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--faint);padding:26px">
        No payslips for this month yet. Use “Run payroll”.</td></tr>`;
      foot.innerHTML = "";
      return;
    }

    body.innerHTML = state.payslips.map((p) => `
      <tr data-idx="${state.payslips.indexOf(p)}">
        <td>${esc(p.employee_name)}<span class="ledger__role">${esc(p.employee_number)}</span></td>
        <td class="num">${money(p.gross_remuneration)}</td>
        <td class="num">${money(p.pension_deduction)}</td>
        <td class="num">${money(p.paye)}</td>
        <td class="num">${money(p.uif_employee)}</td>
        <td class="num">${money(p.sdl)}</td>
        <td class="num">${money(p.net_pay)}</td>
      </tr>`).join("");

    const sum = (key) => state.payslips.reduce((t, p) => t + Number(p[key] || 0), 0);
    foot.innerHTML = `<tr>
      <td>Total</td>
      <td class="num">${money(sum("gross_remuneration"))}</td>
      <td class="num">${money(sum("pension_deduction"))}</td>
      <td class="num">${money(sum("paye"))}</td>
      <td class="num">${money(sum("uif_employee"))}</td>
      <td class="num">${money(sum("sdl"))}</td>
      <td class="num">${money(sum("net_pay"))}</td>
    </tr>`;

    $$("#ledger-body tr").forEach((row) => {
      row.addEventListener("click", () => openDrawer(Number(row.dataset.idx)));
    });
  }

  function renderTeam() {
    const host = $("#team");
    const payslipsByEmployee = {};
    state.payslips.forEach((p) => { payslipsByEmployee[p.employee_id] = p; });

    host.innerHTML = state.employees.map((e) => {
      const slip = payslipsByEmployee[e.id];
      const initials = e.full_name.split(" ").map((w) => w[0]).slice(0, 2).join("");
      const tags = [];
      if (e.commission_earner) tags.push("Commission earner");
      if (e.start_date > "2026-03-01") tags.push("Joined this tax year");
      if (!e.active) tags.push("Leaver");
      return `<article class="member">
        <div class="member__top">
          <span class="member__avatar">${esc(initials)}</span>
          <span>
            <span class="member__name">${esc(e.full_name)}</span>
            <span class="member__role">${esc(e.role || e.employee_number)}</span>
          </span>
        </div>
        <div class="member__stats">
          <span class="member__stat"><span>Basic</span><b>${money(e.basic_salary)}</b></span>
          <span class="member__stat"><span>Pension</span><b>${e.pension_rate ? e.pension_rate + "%" : "—"}</b></span>
          <span class="member__stat"><span>Net</span><b>${slip ? money(slip.net_pay) : "—"}</b></span>
        </div>
        ${tags.map((t) => `<span class="member__tag">${esc(t)}</span>`).join("")}
      </article>`;
    }).join("");
  }

  function openDrawer(index) {
    const p = state.payslips[index];
    if (!p) return;
    const employee = state.employees.find((e) => e.id === p.employee_id);

    const gross = p.gross_remuneration || 1;
    const seg = (value, color) =>
      `<i style="width:${(value / gross) * 100}%;background:${color}"></i>`;

    const rows = (list) => list.map(([label, value]) =>
      `<div class="slip__row"><span>${label}</span><b>${value}</b></div>`).join("");

    $("#drawer-name").textContent = p.employee_name;
    $("#drawer-meta").textContent =
      `${p.employee_number} · ${prettyPeriod(p.period)}` +
      (p.months_worked && p.months_worked !== 12 ? ` · worked ${p.months_worked} months` : "");

    $("#drawer-body").innerHTML = `
      <div class="slip__group">
        <h3>Earnings</h3>
        ${rows([
          ["Basic salary", money(p.basic_salary)],
          ...(p.overtime ? [["Overtime", money(p.overtime)]] : []),
          ...(p.bonus ? [["Bonus", money(p.bonus)]] : []),
          ...(p.commission ? [["Commission", money(p.commission)]] : []),
          ...(p.fringe_benefit ? [["Fringe benefit", money(p.fringe_benefit)]] : []),
          ...(p.leave_pay ? [["Leave pay", money(p.leave_pay)]] : []),
          ["Gross remuneration", money(p.gross_remuneration)],
        ])}
      </div>

      <div class="slip__group">
        <h3>How the gross is used</h3>
        <div class="slip__bar">
          ${seg(p.paye, "#f472b6")}
          ${seg(p.uif_employee, "#fbbf24")}
          ${seg(p.pension_deduction, "#a78bfa")}
          ${seg(p.medical_deduction, "#38bdf8")}
          ${seg(p.net_pay, "#34d399")}
        </div>
        <div class="slip__row"><span>PAYE</span><b>${money(p.paye)}</b></div>
        <div class="slip__row"><span>UIF (1%)</span><b>${money(p.uif_employee)}</b></div>
        <div class="slip__row"><span>Retirement fund</span><b>${money(p.pension_deduction)}</b></div>
        <div class="slip__row"><span>Medical scheme</span><b>${money(p.medical_deduction)}</b></div>
      </div>

      <div class="slip__group">
        <h3>The tax calculation</h3>
        ${rows([
          ["Monthly taxable income", money(p.taxable_income / 12)],
          ["Annualised (× 12)", money(p.taxable_income)],
          ["Annual tax", money(p.annual_tax)],
          ["Monthly PAYE (to the nearest rand)", money(p.paye)],
          ["Effective rate", `${(p.effective_rate * 100).toFixed(1)}%`],
          ["Marginal rate", `${(p.marginal_rate * 100).toFixed(0)}%`],
        ])}
      </div>

      <div class="slip__group">
        <h3>What it costs the business</h3>
        ${rows([
          ["UIF (employer 1%)", money(p.uif_employer)],
          ["SDL (1% of the leviable amount)", money(p.sdl)],
          ...(employee?.medical_employer ? [["Medical contribution", money(employee.medical_employer)]] : []),
        ])}
      </div>

      <div class="slip__net">
        <span>Net pay</span>
        <b>${money(p.net_pay)}</b>
      </div>`;

    $("#drawer").removeAttribute("hidden");
    $("#drawer-backdrop").removeAttribute("hidden");
  }

  function closeDrawer() {
    $("#drawer").setAttribute("hidden", "");
    $("#drawer-backdrop").setAttribute("hidden", "");
  }

  // ----------------------------------------------------------------------
  // LOADING
  // ----------------------------------------------------------------------
  function renderPeriodOptions() {
    const select = $("#period-select");
    const periods = state.overview?.periods || [];
    if (!periods.length) {
      const now = new Date();
      select.innerHTML = `<option value="${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}">This month</option>`;
      state.period = select.value;
      return;
    }
    select.innerHTML = periods.map((p) =>
      `<option value="${p}">${prettyPeriod(p)}</option>`).join("");
    state.period = periods[0];
    select.value = state.period;
  }

  async function loadPeriod(period) {
    state.period = period;
    try {
      state.payslips = await api(`/api/payslips?period=${period}`);
    } catch (error) {
      state.payslips = [];
    }
    try {
      state.emp201 = await api(`/api/emp201?period=${period}`);
    } catch (error) {
      state.emp201 = null;
    }
    renderKpis();
    renderLedger();
    renderTeam();
    renderEmp201();
  }

  async function loadAll() {
    try {
      const [overview, employees, deadlines] = await Promise.all([
        api("/api/overview"),
        api("/api/employees"),
        api("/api/deadlines?year=2027"),
      ]);
      state.overview = overview;
      state.employees = employees;
      state.deadlines = deadlines;

      $("#company-name").textContent = overview.company || "Payroll Suite";
      renderPeriodOptions();
      renderChart();
      renderDeadlines();
      await loadPeriod(state.period);
    } catch (error) {
      toast(`Could not reach the server: ${error.message}`, true);
    }
  }

  // ----------------------------------------------------------------------
  // EVENTS
  // ----------------------------------------------------------------------
  $("#period-select").addEventListener("change", (e) => loadPeriod(e.target.value));

  $("#run-btn").addEventListener("click", async () => {
    const button = $("#run-btn");
    const period = $("#period-select").value;
    button.disabled = true;
    button.textContent = "Running…";
    try {
      const result = await api("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ period, force: true }),
      });
      state.overview = await api("/api/overview");
      renderPeriodOptions();
      renderChart();
      await loadPeriod(period);
      toast(`Payroll run for ${prettyPeriod(period)}: ${result.head_count} payslips.`);
    } catch (error) {
      toast(error.message, true);
    } finally {
      button.disabled = false;
      button.innerHTML = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg> Run payroll`;
    }
  });

  $("#export-btn").addEventListener("click", () => {
    const rows = state.payslips;
    if (!rows.length) { toast("Nothing to export for this month.", true); return; }
    const keys = Object.keys(rows[0]);
    const csv = [
      keys.join(","),
      ...rows.map((row) => keys.map((k) => {
        const v = row[k];
        return typeof v === "string" && /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
      }).join(",")),
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `payslips-${state.period}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
    toast("Payslips exported.");
  });

  $("#drawer-close").addEventListener("click", closeDrawer);
  $("#drawer-backdrop").addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });

  loadAll();
})();
