import React from "react";

const NAV = [
  ["overview", "Overview"],
  ["spend", "Spend"],
  ["budgets", "Budgets"],
  ["recurring", "Recurring"],
  ["exceptions", "Exceptions"],
  ["explorer", "Data Explorer"],
  ["reports", "Reports"],
];

function SunIcon() {
  return (
    <svg className="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
    </svg>
  );
}

function MoonIcon() {
  return <svg className="icon-moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" /></svg>;
}

export default function Header({ manifest, validation, active, onToggleTheme, onNav }) {
  const counts = validation.counts;
  const badge = (v) => String(v);
  return (
    <header>
      <div className="wrap">
        <div className="head-top">
          <div>
            <h1>Household Spend Intelligence</h1>
            <div className="tagline">
              Deterministic synthetic spend ledger — generation, rule-based categorization,
              treatment hygiene, recurring detection, budget comparison, validation and
              evaluation against held-out ground truth.
            </div>
            <div className="badges">
              <span className="badge">seed {badge(manifest.seed)}</span>
              <span className="badge">scale {badge(manifest.scale)}</span>
              <span className="badge">year {badge(manifest.year)}</span>
              <span className="badge">{manifest.transactions.toLocaleString("en-US")} txns</span>
              <span className="badge">{manifest.profiles.toLocaleString("en-US")} profiles</span>
              <span className="badge">fixed timestamp {badge(manifest.generated_at.replace("T", " ").replace(":00Z", " UTC"))}</span>
            </div>
          </div>
          <div className="head-right">
            <button className="theme-btn" onClick={onToggleTheme} aria-label="Toggle colour theme" title="Toggle light / dark theme">
              <SunIcon />
              <MoonIcon />
            </button>
            <div className="status-box">
              <div className="s-label">Validation</div>
              <div className="s-value">{validation.status}</div>
              <div className="s-sub">
                {counts.pass}/{counts.pass + counts.warn + counts.fail} checks · {counts.warn} warnings
              </div>
            </div>
          </div>
        </div>
        <nav>
          {NAV.map(([id, label]) => (
            <a
              key={id}
              href={"#" + id}
              className={active === id ? "active" : ""}
              onClick={() => onNav(id)}
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
