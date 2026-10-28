from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

STATUS_COLORS = {"under": "#10b981", "near": "#f59e0b", "over": "#ef4444"}


def _read(root: Path, rel: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(root / rel, **kwargs)


def build_web_data(dataset_dir: str = "dataset", out_path: str | Path | None = None) -> Path:
    root = Path(dataset_dir)
    manifest = json.loads((root / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    evaluation = json.loads((root / "outputs" / "evaluation_report.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "validation" / "validation_summary.json").read_text(encoding="utf-8"))

    monthly = _read(root, "outputs/monthly_spend.csv")
    budgets = _read(root, "outputs/budget_comparison.csv")
    recurring = _read(root, "outputs/recurring_series.csv")
    anomalies = _read(root, "ground_truth/anomaly_manifest.csv")
    cat = _read(
        root,
        "outputs/categorized_transactions.csv",
        usecols=["offset_category_code", "spend_amount_usd"],
    )
    explorer_path = root.parent / "samples" / "explorer_sample.csv"
    explorer = pd.read_csv(explorer_path) if explorer_path.exists() else None

    mon = (
        monthly.groupby("period_month", sort=True, as_index=False)
        .agg(spend=("spend_usd", "sum"), income=("income_usd", "sum"))
    )
    monthly_rows = [
        {"month": str(r["month"]), "spend": round(float(r["spend"]), 2), "income": round(float(r["income"]), 2)}
        for r in mon.rename(columns={"period_month": "month"}).to_dict("records")
    ]

    by_cat = (
        cat[cat["spend_amount_usd"] != 0]
        .groupby("offset_category_code", sort=True)["spend_amount_usd"]
        .sum()
        .sort_values(ascending=False, kind="mergesort")
        .head(12)
    )
    category_rows = [{"code": str(k), "spend": round(float(v), 2)} for k, v in by_cat.items()]

    status_counts = budgets["status"].value_counts().to_dict()
    over = budgets.loc[budgets["status"] == "over"].sort_values("variance_usd", kind="mergesort").head(10)
    budget_data = {
        "rows": int(len(budgets)),
        "statuses": [
            {"status": k, "rows": int(v), "color": STATUS_COLORS.get(k, "#94a3b8")}
            for k, v in sorted(status_counts.items(), key=lambda kv: -kv[1])
        ],
        "total": round(float(budgets["budget_amount_usd"].sum()), 2),
        "actual": round(float(budgets["actual_spend_usd"].sum()), 2),
        "variance": round(float(budgets["variance_usd"].sum()), 2),
        "top_over": [
            {
                "user": str(r["user_id"]),
                "month": str(r["period_month"]),
                "category": str(r["resolved_category_code"]),
                "budget": round(float(r["budget_amount_usd"]), 2),
                "actual": round(float(r["actual_spend_usd"]), 2),
                "variance": round(float(r["variance_usd"]), 2),
                "usage": round(float(r["usage_pct"]), 1),
            }
            for r in over.to_dict("records")
        ],
    }

    rec_status = recurring["status"].value_counts().to_dict()
    recurring_data = {
        "statuses": [{"status": k, "series": int(v)} for k, v in sorted(rec_status.items())],
        "top_categories": [
            {"code": str(k), "series": int(v)}
            for k, v in recurring["category_code"].value_counts().head(8).items()
        ],
        "missed": int((recurring["missed_occurrences"] > 0).sum()),
        "expected_total": round(float(recurring["expected_amount_usd"].sum()), 2),
        "total_detected": int(len(recurring)),
    }

    anomaly_rows = (
        anomalies.groupby("issue_type", sort=True, as_index=False)
        .agg(
            cases=("anomaly_id", "count"),
            impact=("impact_count", "sum"),
            severity=("severity", "first"),
            behavior=("observed_behavior", "first"),
            resolution=("expected_resolution", "first"),
        )
        .sort_values("impact", ascending=False, kind="mergesort")
    )
    anomaly_list = [
        {
            "issue": str(r["issue_type"]),
            "cases": int(r["cases"]),
            "impact": int(r["impact"]),
            "severity": str(r["severity"]),
            "behavior": str(r["behavior"]),
            "resolution": str(r["resolution"]),
        }
        for r in anomaly_rows.to_dict("records")
    ]

    explorer_list = []
    if explorer is not None:
        for r in explorer.to_dict("records"):
            confidence = r["confidence"]
            explorer_list.append(
                {
                    "id": str(r["transaction_id"]),
                    "d": str(r["transaction_date"]),
                    "u": str(r["user_id"]),
                    "x": str(r["descriptor"]),
                    "a": round(float(r["amount_usd"]), 2),
                    "p": str(r["predicted_category_code"]),
                    "t": str(r["true_category_code"]),
                    "c": round(float(confidence), 3) if pd.notna(confidence) else None,
                    "i": str(r["issue_type"]) if pd.notna(r["issue_type"]) else "none",
                }
            )

    reports = [
        {"href": "../../dataset/validation/validation_summary.md", "title": "Validation summary",
         "desc": f"{validation['counts']['pass']} checks with expected outcomes, reconciliation, and known exceptions"},
        {"href": "../../dataset/outputs/evaluation_report.md", "title": "Evaluation report",
         "desc": "Metrics against ground truth: per-class scores, confusions and distributions"},
        {"href": "../../dataset/outputs/reproducibility_report.md", "title": "Reproducibility report",
         "desc": "Two fixed-seed runs compared row counts and SHA-256 checksums"},
        {"href": "../../dataset/metadata/manifest.json", "title": "Manifest",
         "desc": "Per-file row counts, byte sizes and SHA-256 checksums"},
        {"href": "../../dataset/metadata/source_manifest.json", "title": "Source manifest",
         "desc": "Data provenance, fields, transformations and licensing note"},
        {"href": "../../docs/data_dictionary.md", "title": "Data dictionary",
         "desc": "Full field-level documentation for every export"},
        {"href": "../../schema.sql", "title": "Database schema",
         "desc": "DDL with primary keys, foreign keys, enums and indexes"},
        {"href": "../../README.md", "title": "Project README",
         "desc": "Workflow, business rules, exception handling and metrics"},
    ]

    payload = {
        "manifest": manifest,
        "validation": validation,
        "evaluation": evaluation,
        "monthly": monthly_rows,
        "categories": category_rows,
        "budget": budget_data,
        "recurring": recurring_data,
        "anomalies": anomaly_list,
        "explorer": explorer_list,
        "reports": reports,
    }

    out = Path(out_path) if out_path is not None else (root.parent / "web" / "src" / "data.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=True), encoding="utf-8")
    return out
