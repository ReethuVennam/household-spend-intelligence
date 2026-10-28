import React, { useEffect, useMemo, useRef, useState } from "react";

export function Pill({ kind = "info", children }) {
  return <span className={"pill " + kind}>{children}</span>;
}

function prefersReduced() {
  return typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function useCountUp(target, enabled = true) {
  const [value, setValue] = useState(() => (enabled && !prefersReduced() ? 0 : target));
  useEffect(() => {
    if (!enabled || prefersReduced()) {
      setValue(target);
      return;
    }
    let raf = 0;
    let start = null;
    const dur = 850;
    const step = (ts) => {
      if (start === null) start = ts;
      const p = Math.min((ts - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(p < 1 ? target * eased : target);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, enabled]);
  return value;
}

export function Kpi({ label, count, text, format, sub = "", accent = "", decimals = 0, suffix = "", mini = false }) {
  const hasCount = typeof count === "number";
  const animated = useCountUp(hasCount ? count : 0, hasCount);
  const shown = hasCount
    ? format
      ? format(animated, decimals) + suffix
      : String(animated)
    : text;
  return (
    <div className={"kpi" + (mini ? " mini" : "")} style={accent ? { "--accent": accent } : undefined}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{shown}</div>
      {sub ? <div className="kpi-sub">{sub}</div> : null}
    </div>
  );
}

export function Meter({ value }) {
  const frac = Math.max(0, Math.min(1, value));
  const color = frac >= 0.95 ? "#10b981" : frac >= 0.8 ? "#f59e0b" : "#ef4444";
  const [w, setW] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setW(frac * 100), 100);
    return () => clearTimeout(t);
  }, [frac]);
  return (
    <span className="meter">
      <span style={{ width: w + "%", background: color }} />
    </span>
  );
}

export function SectionHead({ color = "#6366f1", title, hint }) {
  return (
    <div className="sec-head">
      <span
        className="dot"
        style={{ background: color, boxShadow: "0 0 0 4px " + color + "29" }}
      />
      <h2>{title}</h2>
      {hint ? <span className="hint">{hint}</span> : null}
    </div>
  );
}

export function Note({ children }) {
  return <div className="note">{children}</div>;
}

function toSortValue(row, col) {
  if (col.sort) return col.sort(row);
  const raw = col.value ? col.value(row) : row[col.key];
  if (typeof raw === "number") return raw;
  const s = String(raw == null ? "" : raw);
  const cleaned = s.replace(/[$,%]/g, "").replace(/,/g, "").trim();
  if (cleaned.includes("/") || cleaned.includes("PASS")) return null;
  const v = parseFloat(cleaned);
  return isNaN(v) ? null : v;
}

export function SortableTable({ columns, rows, defaultSort = null }) {
  const [sort, setSort] = useState(defaultSort);
  const sorted = useMemo(() => {
    if (!sort) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const x = toSortValue(a, sort.col);
      const y = toSortValue(b, sort.col);
      if (x !== null && y !== null && typeof x === "number" && typeof y === "number") {
        return sort.asc ? x - y : y - x;
      }
      const sx = String(x == null ? sort.col.value(a) : x);
      const sy = String(y == null ? sort.col.value(b) : y);
      return sort.asc ? sx.localeCompare(sy) : sy.localeCompare(sx);
    });
    return copy;
  }, [rows, sort]);
  const click = (col) => {
    setSort((prev) =>
      prev && prev.col.key === col.key ? { col, asc: !prev.asc } : { col, asc: true }
    );
  };
  return (
    <div className="tw">
      <table className="sortable">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={col.align || ""}
                onClick={() => click(col)}
              >
                {col.label}
                <span className="arrow">
                  {sort && sort.col.key === col.key ? (sort.asc ? "▲" : "▼") : "⇅"}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={row.key != null ? row.key : i}>
              {columns.map((col) => (
                <td key={col.key} className={(col.align || "") + (col.nowrap ? " nowrap" : "")}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
