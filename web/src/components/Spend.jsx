import React, { useState } from "react";
import { CategoryBars, MonthlyChart } from "./charts.jsx";
import { Kpi, Note, SectionHead, SortableTable } from "./ui.jsx";
import { KPI_ACCENTS, fmtMoney, monthLabel } from "../format.js";

export default function Spend({ data, evaluation }) {
  const [view, setView] = useState("chart");
  const s = evaluation.sections;
  const monthly = data.monthly;
  const rows = monthly.map((r) => {
    const net = r.income - r.spend;
    return {
      key: r.month,
      month: monthLabel(r.month),
      spend: r.spend,
      income: r.income,
      net,
      text: fmtMoney(r.spend, 2),
      text2: fmtMoney(r.income, 2),
      text3: (net >= 0 ? "+" : "-") + fmtMoney(Math.abs(net), 2),
    };
  });
  const columns = [
    { key: "month", label: "Month", nowrap: true },
    { key: "spend", label: "Spend", align: "right", render: (r) => r.text, value: (r) => r.spend },
    { key: "income", label: "Income", align: "right", render: (r) => r.text2, value: (r) => r.income },
    { key: "net", label: "Net", align: "right", render: (r) => r.text3, value: (r) => r.net },
  ];
  const totalSpend = monthly.reduce((a, r) => a + r.spend, 0);
  const totalIncome = monthly.reduce((a, r) => a + r.income, 0);
  const avg = totalSpend / 12;
  const peak = monthly.reduce((best, r) => (r.spend > best.spend ? r : best), monthly[0]);

  return (
    <section id="spend">
      <SectionHead title="Spend" hint="monthly rhythm and category mix" />
      <div className="grid kpis">
        <Kpi label="Total spend" text={fmtMoney(totalSpend, 2)} sub="12 months, transfers excluded" accent={KPI_ACCENTS[0]} />
        <Kpi label="Total income" text={fmtMoney(totalIncome, 2)} sub="salary, refunds kept as credits" accent={KPI_ACCENTS[2]} />
        <Kpi label="Avg monthly spend" text={fmtMoney(avg, 2)} sub={"peak " + monthLabel(peak.month) + " " + fmtMoney(peak.spend, 0)} accent={KPI_ACCENTS[1]} />
        <Kpi label="Uncategorized rate" text={fmtPctLocal(s.data_quality.uncategorized_rate)} sub={"rules first, model fallback rate " + fmtPctLocal(s.data_quality.fallback_rate)} accent={KPI_ACCENTS[5]} />
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, gap: 12, flexWrap: "wrap" }}>
          <h3 style={{ margin: 0 }}>Spend versus income by month</h3>
          <div className="seg">
            <button className={view === "chart" ? "on" : ""} onClick={() => setView("chart")}>Chart</button>
            <button className={view === "table" ? "on" : ""} onClick={() => setView("table")}>Table</button>
          </div>
        </div>
        {view === "chart" ? (
          <>
            <MonthlyChart monthly={monthly} />
            <div className="legend">
              <span className="item"><span className="swatch" style={{ background: "#3b82f6" }} /> Spend</span>
              <span className="item"><span className="swatch" style={{ background: "#10b981" }} /> Income</span>
              <span className="item" style={{ color: "var(--mid)", fontWeight: 500 }}>Hover a bar for exact values</span>
            </div>
          </>
        ) : (
          <SortableTable columns={columns} rows={rows} defaultSort={{ col: columns[0], asc: true }} />
        )}
        <Note>
          Month boundaries use each profile's IANA timezone — the timezone-boundary anomaly (4,505 rows) is
          only detectable when local dates, not UTC dates, drive the ledger.
        </Note>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Net spend by category — top 12</h3>
        <CategoryBars categories={data.categories} />
        <Note>
          Amounts are post-offset: refunds reduce category spend and transfers never enter a category total.
        </Note>
      </div>
    </section>
  );
}

function fmtPctLocal(v) {
  return (v * 100).toFixed(2) + "%";
}
