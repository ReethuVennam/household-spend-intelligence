import React, { useMemo, useState } from "react";
import { Note, Pill, SectionHead } from "./ui.jsx";
import { ISSUE_PILL, fmtMoney } from "../format.js";

const ISSUE_LABELS = [
  ["all", "All issues"],
  ["none", "No issue (normal rows)"],
  ["transfer_double_count", "Transfer double count"],
  ["timezone_boundary_date", "Timezone boundary date"],
  ["refund_treated_as_new_expense", "Refund as new expense"],
];

export default function Explorer({ explorer }) {
  const [query, setQuery] = useState("");
  const [issue, setIssue] = useState("all");
  const [mismatchOnly, setMismatchOnly] = useState(false);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return explorer.filter((r) => {
      if (issue !== "all") {
        const effective = r.i === "none" ? "none" : r.i;
        if (effective !== issue) return false;
      }
      if (mismatchOnly && r.p === r.t) return false;
      if (q) {
        const hay = (r.x + " " + r.u + " " + r.id + " " + r.p + " " + r.t + " " + r.i).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [explorer, query, issue, mismatchOnly]);

  const mismatches = rows.filter((r) => r.p !== r.t).length;

  return (
    <section id="explorer">
      <SectionHead title="Data Explorer" hint="labelled sample with ground truth — compare what the pipeline predicted" />
      <div className="card">
        <div className="controls">
          <input
            type="search"
            placeholder="Search descriptor, user, id…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search transactions"
          />
          <select value={issue} onChange={(e) => setIssue(e.target.value)} aria-label="Filter by issue type">
            {ISSUE_LABELS.map(([v, label]) => (
              <option key={v} value={v}>{label}</option>
            ))}
          </select>
          <label>
            <input
              type="checkbox"
              checked={mismatchOnly}
              onChange={(e) => setMismatchOnly(e.target.checked)}
            />
            Mismatches only
          </label>
          <span className="count-note">
            {rows.length.toLocaleString("en-US")} rows · {mismatches.toLocaleString("en-US")} category mismatches
          </span>
        </div>
        <div className="ex-scroll">
          <table>
            <thead>
              <tr>
                <th>Transaction</th>
                <th>Date</th>
                <th>Profile</th>
                <th>Descriptor</th>
                <th className="right">Amount</th>
                <th>Predicted</th>
                <th>Ground truth</th>
                <th className="right">Confidence</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: "center", color: "var(--mid)", padding: "26px" }}>
                    No transactions match these filters.
                  </td>
                </tr>
              ) : (
                rows.map((r) => {
                  const mismatch = r.p !== r.t;
                  const issueKind = r.i === "none" ? null : ISSUE_PILL[r.i] || "muted";
                  return (
                    <tr key={r.id}>
                      <td className="nowrap" style={{ fontFamily: "ui-monospace,monospace", fontSize: 12 }}>{r.id}</td>
                      <td className="nowrap">{r.d}</td>
                      <td className="nowrap">{r.u}</td>
                      <td>{r.x}</td>
                      <td className="right" style={{ fontVariantNumeric: "tabular-nums" }}>{fmtMoney(r.a, 2)}</td>
                      <td><Pill kind="info">{r.p}</Pill></td>
                      <td><Pill kind={mismatch ? "bad" : "ok"}>{r.t}</Pill></td>
                      <td className="right" style={{ fontVariantNumeric: "tabular-nums" }}>
                        {r.c == null ? "—" : r.c.toFixed(3)}
                      </td>
                      <td className="nowrap">
                        {issueKind ? <Pill kind={issueKind}>{r.i}</Pill> : mismatch ? <Pill kind="warn">uncertain</Pill> : <span style={{ color: "var(--mid)" }}>—</span>}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <Note>
          540-row slice of the full set: every planted anomaly class plus 73 deliberate category mismatches.
          Predictions come from <code>outputs/categorized_transactions.csv</code>; ground truth from{" "}
          <code>transaction_labels.csv</code> — joined here only, never in production code paths.
        </Note>
      </div>
    </section>
  );
}
