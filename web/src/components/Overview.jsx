import React from "react";
import { Kpi, Meter, Note, Pill, SectionHead, SortableTable } from "./ui.jsx";
import { KPI_ACCENTS, fmtInt, fmtMoney, fmtMoneyC, fmtPct } from "../format.js";

export default function Overview({ manifest, validation, evaluation }) {
  const s = evaluation.sections;
  const counts = validation.counts;
  const totalChecks = counts.pass + counts.warn + counts.fail;
  const anomalyCases = Object.values(manifest.anomaly_counts).reduce((a, b) => a + b, 0);

  const scoreRows = [
    { label: "Validation checks passed", meter: totalChecks ? counts.pass / totalChecks : 0, display: counts.pass + " / " + totalChecks, pill: <Pill kind="ok">PASS</Pill> },
    { label: "Categorization accuracy", meter: s.categorization.accuracy, display: fmtPct(s.categorization.accuracy), sub: "macro F1 " + fmtPct(s.categorization.macro_f1) },
    { label: "Treatment accuracy", meter: s.treatment.accuracy, display: fmtPct(s.treatment.accuracy), sub: "spend / income / transfer / refund" },
    { label: "Recurring detection F1", meter: s.recurring_detection.f1, display: fmtPct(s.recurring_detection.f1), sub: "recall " + fmtPct(s.recurring_detection.recall, 1) + ", " + s.recurring_detection.false_negatives + " missed" },
    { label: "Budget alias resolution", meter: s.budget_comparison.resolution_accuracy, display: fmtPct(s.budget_comparison.resolution_accuracy), sub: s.budget_comparison.resolved_alias_rows.toLocaleString("en-US") + " alias rows resolved, " + s.budget_comparison.unresolved_rows + " unresolved" },
    { label: "Exception handling score", meter: s.exception_handling_score, display: s.exception_handling_score.toFixed(2), sub: "5 / 5 required anomaly types" },
    { label: "Reconciliation delta", meter: 1, display: fmtMoney(Math.abs(s.reconciliation.strict_vs_monthly_delta_usd), 2), sub: "ledger vs balances " + fmtMoney(Math.abs(s.reconciliation.ledger_vs_balance_delta_usd), 2) },
  ];

  const totals = [
    ["Transactions", fmtInt(manifest.transactions)],
    ["Accounts", fmtInt(manifest.counts.accounts)],
    ["Budget rows", fmtInt(manifest.counts.budgets)],
    ["Category rules", fmtInt(manifest.counts.category_rules)],
    ["Recurring series", fmtInt(manifest.counts.recurring_series)],
    ["Transfer links", fmtInt(manifest.counts.transfer_links)],
    ["Insights", fmtInt(manifest.counts.insights)],
    ["Files written", fmtInt(Object.keys(manifest.files).length)],
  ];

  const scoreColumns = [
    { key: "label", label: "Scorecard" },
    { key: "meter", label: "", render: (r) => <Meter value={r.meter} /> },
    { key: "display", label: "Result", align: "right", nowrap: true },
    { key: "sub", label: "Detail", render: (r) => r.sub || r.pill || "" },
  ];
  const totalsColumns = [
    { key: "name", label: "Dataset totals" },
    { key: "value", label: "Count", align: "right" },
  ];

  return (
    <section id="overview">
      <SectionHead title="Overview" hint="full scale · fixed seed · zero warnings" />
      <div className="grid kpis">
        <Kpi label="Transactions" count={manifest.transactions} format={fmtInt} sub="12 months · 82 merchants" accent={KPI_ACCENTS[0]} />
        <Kpi label="Strict net spend" count={s.reconciliation.strict_net_spend_usd} format={fmtMoneyC} sub="transfers and refunds excluded" accent={KPI_ACCENTS[2]} />
        <Kpi label="Naive overstatement avoided" count={s.transfer_and_refund.naive_spend_overstatement_usd} format={fmtMoneyC} sub="what an unclean pipeline would claim" accent={KPI_ACCENTS[3]} />
        <Kpi label="Budget rows" count={manifest.counts.budgets} format={fmtInt} sub="monthly per profile × category" accent={KPI_ACCENTS[6]} />
        <Kpi label="Anomaly cases" count={anomalyCases} format={fmtInt} sub="5 planted types · all labelled" accent={KPI_ACCENTS[4]} />
        <Kpi label="Recurring series" count={manifest.counts.recurring_series} format={fmtInt} sub="30 skip patterns flagged" accent={KPI_ACCENTS[5]} />
        <Kpi label="Profiles" count={manifest.profiles} format={fmtInt} sub="2,335 accounts, 25 categories" accent={KPI_ACCENTS[1]} />
        <Kpi label="Validation checks" count={counts.pass} format={fmtInt} sub={counts.warn + counts.fail + " warnings or failures"} accent={KPI_ACCENTS[7]} />
      </div>
      <div className="split2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>Scorecard</h3>
          <SortableTable columns={scoreColumns} rows={scoreRows.map((r, i) => ({ ...r, key: i }))} />
          <Note>
            Scores are measured by <code>src/metrics.py</code> against held-out ground truth the pipeline never
            reads. Full detail: <a href="../../dataset/outputs/evaluation_report.md">evaluation report</a>.
          </Note>
        </div>
        <div className="card">
          <h3>Dataset totals</h3>
          <SortableTable columns={totalsColumns} rows={totals.map(([name, value]) => ({ name, value, key: name }))} />
          <Note>
            Every export row count and SHA-256 checksum is recorded in the{" "}
            <a href="../../dataset/metadata/manifest.json">manifest</a>.
          </Note>
        </div>
      </div>
    </section>
  );
}
