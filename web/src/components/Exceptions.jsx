import React from "react";
import { Kpi, Note, Pill, SectionHead, SortableTable } from "./ui.jsx";
import { ISSUE_PILL, KPI_ACCENTS, SEVERITY_PILL, fmtInt } from "../format.js";

export default function Exceptions({ anomalies, evaluation }) {
  const s = evaluation.sections;
  const required = s.exceptions.manifest_required_types;
  const cols = [
    {
      key: "issue",
      label: "Anomaly type",
      nowrap: true,
      render: (r) => <Pill kind={ISSUE_PILL[r.issue] || "muted"}>{r.issue}</Pill>,
    },
    { key: "cases", label: "Cases", align: "right", render: (r) => fmtInt(r.cases) },
    { key: "impact", label: "Rows impacted", align: "right", render: (r) => fmtInt(r.impact) },
    {
      key: "severity",
      label: "Severity",
      nowrap: true,
      render: (r) => <Pill kind={SEVERITY_PILL[r.severity] || "muted"}>{r.severity}</Pill>,
    },
    { key: "behavior", label: "Naive behaviour", render: (r) => r.behavior },
    { key: "resolution", label: "Expected resolution", render: (r) => r.resolution },
  ];
  const totalCases = anomalies.reduce((a, r) => a + r.cases, 0);
  const totalImpact = anomalies.reduce((a, r) => a + r.impact, 0);
  return (
    <section id="exceptions">
      <SectionHead title="Exceptions" hint="five planted anomalies, all detected and correctly handled" />
      <div className="grid mini">
        <Kpi mini label="Anomaly types" count={required} format={fmtInt} sub="all present in the manifest" accent={KPI_ACCENTS[0]} />
        <Kpi mini label="Labelled cases" count={totalCases} format={fmtInt} sub="in ground_truth/ only" accent={KPI_ACCENTS[1]} />
        <Kpi mini label="Rows impacted" count={totalImpact} format={fmtInt} sub="transactions and budget rows" accent={KPI_ACCENTS[4]} />
        <Kpi mini label="Handling score" count={s.exception_handling_score} format={(v) => v.toFixed(2)} sub="every case resolved as specified" accent={KPI_ACCENTS[2]} />
        <Kpi mini label="Transfers excluded" count={s.transfer_and_refund.transfer_transactions} format={fmtInt} sub={fmtInt(s.transfer_and_refund.transfers_handled_as_transfer) + " handled as transfer"} accent={KPI_ACCENTS[6]} />
        <Kpi mini label="Refunds netted" count={s.transfer_and_refund.refund_transactions} format={fmtInt} sub="no refund counted as new spend" accent={KPI_ACCENTS[5]} />
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Anomaly manifest</h3>
        <SortableTable
          columns={cols}
          rows={anomalies.map((r, i) => ({ ...r, key: r.issue }))}
          defaultSort={{ col: cols[2], asc: false }}
        />
        <Note>
          Ground truth lives only in <code>dataset/ground_truth/</code> and is joined by <code>src/metrics.py</code> at
          evaluation time — the generator, categorizer, recurring detector and budget engine never read it.
        </Note>
      </div>
    </section>
  );
}
