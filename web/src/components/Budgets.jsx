import React from "react";
import { Donut } from "./charts.jsx";
import { Kpi, Meter, Note, Pill, SectionHead, SortableTable } from "./ui.jsx";
import { KPI_ACCENTS, fmtInt, fmtMoney } from "../format.js";

export default function Budgets({ budget, evaluation }) {
  const s = evaluation.sections.budget_comparison;
  const overCols = [
    { key: "user", label: "Profile", nowrap: true },
    { key: "month", label: "Month", nowrap: true },
    { key: "category", label: "Category", nowrap: true },
    { key: "budget", label: "Budget", align: "right", render: (r) => fmtMoney(r.budget, 0) },
    { key: "actual", label: "Actual", align: "right", render: (r) => fmtMoney(r.actual, 0) },
    { key: "variance", label: "Variance", align: "right", render: (r) => <Pill kind="bad">{"-" + fmtMoney(r.variance, 0)}</Pill> },
    { key: "usage", label: "Usage", align: "right", nowrap: true, render: (r) => (<><Meter value={r.usage / 100} /> {r.usage.toFixed(1)}%</>) },
  ];
  const statusRows = budget.statuses.map((st) => ({
    key: st.status,
    status: st.status,
    rows: st.rows,
    color: st.color,
    share: st.rows / budget.rows,
  }));
  return (
    <section id="budgets">
      <SectionHead title="Budgets" hint="monthly comparison with alias-aware category resolution" />
      <div className="grid mini">
        <Kpi mini label="Budget total" text={fmtMoney(budget.total, 2)} sub={fmtInt(s.budget_rows) + " rows"} accent={KPI_ACCENTS[5]} />
        <Kpi mini label="Actual spend" text={fmtMoney(budget.actual, 2)} sub="post-offset, per resolved category" accent={KPI_ACCENTS[2]} />
        <Kpi mini label="Remaining budget" text={fmtMoney(budget.variance, 2)} sub="budget minus actual, all rows" accent={KPI_ACCENTS[3]} />
        <Kpi mini label="Over budget rows" count={s.over_budget_rows} format={fmtInt} sub={fmtPct(s.over_budget_rows / s.budget_rows) + " of rows"} accent={KPI_ACCENTS[4]} />
        <Kpi mini label="Alias rows resolved" count={s.resolved_alias_rows} format={fmtInt} sub="budget taxonomy mismatches fixed" accent={KPI_ACCENTS[0]} />
        <Kpi mini label="Unresolved rows" count={s.unresolved_rows} format={fmtInt} sub="fallback would have hidden misses" accent={KPI_ACCENTS[6]} />
      </div>
      <div className="split" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>Budget status distribution</h3>
          <div className="donut-wrap">
            <Donut items={budget.statuses} />
          </div>
          <div className="status-list">
            {statusRows.map((r) => (
              <div className="status-row" key={r.status}>
                <span className="left">
                  <span className="swatch" style={{ background: r.color }} />
                  {r.status.charAt(0).toUpperCase() + r.status.slice(1)}
                </span>
                <span className="num">
                  {fmtInt(r.rows)} <span style={{ color: "var(--mid)", fontWeight: 600 }}>({(r.share * 100).toFixed(1)}%)</span>
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3>Worst over-budget rows — top 10</h3>
          <SortableTable
            columns={overCols}
            rows={budget.top_over.map((r, i) => ({ ...r, key: r.user + r.month + r.category + i }))}
            defaultSort={{ col: overCols[5], asc: false }}
          />
          <Note>
            Without alias resolution, {s.naive_mismatch_false_under_rows.toLocaleString("en-US")} rows would have
            been mis-scored as under budget (affecting {fmtMoney(s.naive_mismatch_budget_affected_usd)} of budget)
            because the budget used a taxonomy alias the pipeline had not mapped.
          </Note>
        </div>
      </div>
    </section>
  );
}

function fmtPct(v) {
  return (v * 100).toFixed(1) + "%";
}
