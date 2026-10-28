import React, { useState } from "react";
import { axisMoney, fmtMoneyC, monthShort, niceMax } from "../format.js";

function Tip({ tip }) {
  if (!tip) return null;
  return (
    <div className="chart-tip" style={{ left: tip.x + 16 + "px", top: tip.y - 12 + "px" }}>
      {tip.text}
    </div>
  );
}

export function MonthlyChart({ monthly }) {
  const [tip, setTip] = useState(null);
  const w = 840, h = 330;
  const left = 70, right = 18, top = 20, bottom = 52;
  const pw = w - left - right, ph = h - top - bottom;
  const ymax = niceMax(Math.max(...monthly.map((r) => Math.max(r.spend, r.income))) * 1.05);
  const slot = pw / monthly.length;
  const bw = slot * 0.3;
  const show = (e, text) => setTip({ text, x: e.clientX, y: e.clientY });
  const move = (e) => setTip((t) => (t ? { ...t, x: e.clientX, y: e.clientY } : t));
  const bars = [];
  const ticks = [];
  for (let i = 0; i < 5; i++) {
    const frac = i / 4;
    const y = top + ph * (1 - frac);
    ticks.push(
      <g key={"t" + i}>
        <line x1={left} y1={y} x2={left + pw} y2={y} style={{ stroke: "currentColor", opacity: 0.13 }} />
        <text x={left - 9} y={y + 4} textAnchor="end" fontSize="11" fill="currentColor" opacity=".55">
          {axisMoney(ymax * frac)}
        </text>
      </g>
    );
  }
  monthly.forEach((r, idx) => {
    const cx = left + slot * idx + slot / 2;
    const hs = ph * (r.spend / ymax);
    const hi = ph * (r.income / ymax);
    const label = monthShort(r.month);
    const spendTip = label + " " + r.month.slice(0, 4) + ": spend " + fmtMoneyC(r.spend) + " / income " + fmtMoneyC(r.income);
    const incomeTip = label + " " + r.month.slice(0, 4) + ": income " + fmtMoneyC(r.income) + " / spend " + fmtMoneyC(r.spend);
    bars.push(
      <rect
        key={"s" + idx}
        x={cx - bw - 2}
        y={top + ph - hs}
        width={bw}
        height={hs}
        fill="url(#gs)"
        rx="4"
        onMouseEnter={(e) => show(e, spendTip)}
        onMouseMove={move}
        onMouseLeave={() => setTip(null)}
      />
    );
    bars.push(
      <rect
        key={"i" + idx}
        x={cx + 2}
        y={top + ph - hi}
        width={bw}
        height={hi}
        fill="url(#gi)"
        rx="4"
        onMouseEnter={(e) => show(e, incomeTip)}
        onMouseMove={move}
        onMouseLeave={() => setTip(null)}
      />
    );
    bars.push(
      <text key={"l" + idx} x={cx} y={top + ph + 19} textAnchor="middle" fontSize="11.5" fontWeight="600" fill="currentColor" opacity=".65">
        {label}
      </text>
    );
  });
  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label="Monthly spend versus income">
        <defs>
          <linearGradient id="gs" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
          <linearGradient id="gi" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
        </defs>
        {ticks}
        {bars}
        <line x1={left} y1={top + ph} x2={left + pw} y2={top + ph} style={{ stroke: "currentColor", opacity: 0.3 }} />
      </svg>
      <Tip tip={tip} />
    </div>
  );
}

const PALETTE = ["#6366f1", "#3b82f6", "#0ea5e9", "#14b8a6", "#10b981", "#84cc16", "#f59e0b", "#f97316",
  "#ef4444", "#ec4899", "#8b5cf6", "#64748b"];

export function CategoryBars({ categories }) {
  const [tip, setTip] = useState(null);
  const w = 840;
  const labelW = 160, valueW = 100, rh = 34;
  const h = categories.length * rh + 14;
  const vmax = Math.max(...categories.map((c) => c.spend)) || 1;
  const barArea = w - labelW - valueW - 20;
  const show = (e, text) => setTip({ text, x: e.clientX, y: e.clientY });
  const move = (e) => setTip((t) => (t ? { ...t, x: e.clientX, y: e.clientY } : t));
  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label="Spend by category">
        {categories.map((c, i) => {
          const y = 7 + i * rh;
          const bw = barArea * (c.spend / vmax);
          const tipText = c.code + ": " + fmtMoneyC(c.spend) + " net spend";
          return (
            <g key={c.code}>
              <text x={labelW - 12} y={y + 19} textAnchor="end" fontSize="12.5" fontWeight="600" fill="currentColor">
                {c.code}
              </text>
              <rect x={labelW} y={y + 5} width={barArea} height={20} rx="10" style={{ fill: "currentColor", opacity: 0.07 }} />
              <rect
                x={labelW}
                y={y + 5}
                width={Math.max(bw, 3)}
                height={20}
                fill={PALETTE[i % PALETTE.length]}
                rx="10"
                onMouseEnter={(e) => show(e, tipText)}
                onMouseMove={move}
                onMouseLeave={() => setTip(null)}
              />
              <text x={labelW + barArea + 10} y={y + 19} textAnchor="end" fontSize="12.5" fontWeight="700" fill="currentColor">
                {fmtMoneyC(c.spend)}
              </text>
            </g>
          );
        })}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}

export function Donut({ items }) {
  const [hover, setHover] = useState(-1);
  const size = 210;
  const r = 74, sw = 34;
  const c = size / 2;
  const total = items.reduce((s, it) => s + it.rows, 0) || 1;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  const segments = items.map((item, i) => {
    const seg = circ * (item.rows / total);
    const el = (
      <circle
        key={item.status}
        cx={c}
        cy={c}
        r={r}
        fill="none"
        stroke={item.color}
        strokeWidth={sw}
        strokeDasharray={`${Math.max(seg - 2, 0)} ${Math.max(circ - seg + 2, 0)}`}
        strokeDashoffset={-offset}
        strokeLinecap="butt"
        transform={`rotate(-90 ${c} ${c})`}
        onMouseEnter={() => setHover(i)}
        onMouseLeave={() => setHover(-1)}
      >
        <title>{item.status}: {item.rows.toLocaleString("en-US")} rows</title>
      </circle>
    );
    offset += seg;
    return el;
  });
  const center = hover >= 0 ? items[hover].rows.toLocaleString("en-US") : total.toLocaleString("en-US");
  const centerLabel = hover >= 0 ? items[hover].status.toUpperCase() : "BUDGET ROWS";
  return (
    <svg viewBox={`0 0 ${size} ${size}`} width="210" height="210" role="img" aria-label="Budget status distribution">
      <circle cx={c} cy={c} r={r} fill="none" style={{ stroke: "currentColor", opacity: 0.07 }} strokeWidth={sw} />
      {segments}
      <text x={c} y={c - 4} textAnchor="middle" fontSize="30" fontWeight="800" fill="currentColor">
        {center}
      </text>
      <text x={c} y={c + 18} textAnchor="middle" fontSize="11.5" fontWeight="600" fill="currentColor" opacity=".55">
        {centerLabel}
      </text>
    </svg>
  );
}
