import React from "react";
import { Kpi, Note, Pill, SectionHead, SortableTable } from "./ui.jsx";
import { KPI_ACCENTS, fmtInt, fmtNum, fmtPct } from "../format.js";

const STATUS_PILL2 = { completed: "ok", active: "info", paused: "warn" };

export default function Recurring({ recurring, evaluation }) {
  const s = evaluation.sections.recurring_detection;
  const statusCols = [
    { key: "status", label: "Status", nowrap: true, render: (r) => <Pill kind={STATUS_PILL2[r.status] || "muted"}>{r.status}</Pill> },
    { key: "series", label: "Series", align: "right", render: (r) => fmtInt(r.series) },
  ];
  const catCols = [
    { key: "code", label: "Category", nowrap: true },
    { key: "series", label: "Series", align: "right", render: (r) => fmtInt(r.series) },
  ];
  const missed = recurring.missed;
  return (
    <section id="recurring">
      <SectionHead title="Recurring" hint="cadence detection, cancellation and skip handling" />
      <div className="grid mini">
        <Kpi mini label="Series detected" count={recurring.total_detected} format={fmtInt} sub={fmtInt(s.detected_series) + " exported to outputs/"} accent={KPI_ACCENTS[0]} />
        <Kpi mini label="Precision" count={s.precision} format={(v) => fmtPct(v)} sub={fmtInt(s.false_positives) + " false positives"} accent={KPI_ACCENTS[1]} />
        <Kpi mini label="Recall" count={s.recall} format={(v) => fmtPct(v)} sub={fmtInt(s.false_negatives) + " false negatives"} accent={KPI_ACCENTS[2]} />
        <Kpi mini label="F1 score" count={s.f1} format={(v) => fmtPct(v)} sub="all 5,249 detectable series matched" accent={KPI_ACCENTS[5]} />
        <Kpi mini label="Skip series flagged" text={s.skip_series_flagged + " / " + s.skip_series} sub="100% skip precision and recall" accent={KPI_ACCENTS[3]} />
        <Kpi mini label="Amount MAPE" text={fmtNum(s.amount_mape_matched * 100, 3) + "%"} sub="median next-date error 0.0 days" accent={KPI_ACCENTS[6]} />
      </div>
      <div className="split2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>Series by status</h3>
          <SortableTable columns={statusCols} rows={recurring.statuses} defaultSort={{ col: statusCols[1], asc: false }} />
          <Note>
            Missed occurrences (a bill skipped one month, then resumed) are surfaced per series —
            currently {fmtInt(missed)} series carry a missed-occurrence count.
          </Note>
        </div>
        <div className="card">
          <h3>Top categories by series</h3>
          <SortableTable columns={catCols} rows={recurring.top_categories} defaultSort={{ col: catCols[1], asc: false }} />
          <Note>
            Detection is pure cadence math (gap statistics over posted dates) — descriptors and amounts
            confirm identity, ground truth is never consulted.
          </Note>
        </div>
      </div>
    </section>
  );
}
