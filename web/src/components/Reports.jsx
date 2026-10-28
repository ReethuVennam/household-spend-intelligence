import React from "react";
import { SectionHead } from "./ui.jsx";

export default function Reports({ reports, manifest, seed }) {
  return (
    <section id="reports">
      <SectionHead title="Reports & artifacts" hint="every claim above is backed by a generated file" />
      <div className="reports">
        {reports.map((r) => (
          <a key={r.href} className="report" href={r.href}>
            <div className="r-title">{r.title} →</div>
            <div className="r-desc">{r.desc}</div>
          </a>
        ))}
      </div>
      <div className="footer">
        Deterministic build — seed {seed}, fixed generated timestamp, re-running{" "}
        <code>python -m src.cli all</code> reproduces byte-identical CSVs and manifest checksums
        ({Object.keys(manifest.files).length} tracked files, {Math.round(manifest.total_bytes / 1048576)} MB written).
      </div>
    </section>
  );
}
