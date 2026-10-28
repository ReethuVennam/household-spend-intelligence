from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import FIXED_GENERATED_AT


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _round(value, digits: int = 4):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return round(float(value), digits)


def _classification_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict:
    classes = sorted(set(y_true.dropna().astype(str)) | set(y_pred.dropna().astype(str)))
    rows = []
    correct = int((y_true.astype(str) == y_pred.astype(str)).sum())
    total = int(len(y_true))
    for cls in classes:
        tp = int(((y_true.astype(str) == cls) & (y_pred.astype(str) == cls)).sum())
        fp = int(((y_true.astype(str) != cls) & (y_pred.astype(str) == cls)).sum())
        fn = int(((y_true.astype(str) == cls) & (y_pred.astype(str) != cls)).sum())
        support = tp + fn
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append(
            {
                "class": cls,
                "support": support,
                "predicted": tp + fp,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
            }
        )
    supported = [r for r in rows if r["support"] > 0]
    macro = float(np.mean([r["f1"] for r in supported])) if supported else 0.0
    weighted = float(sum(r["f1"] * r["support"] for r in supported) / max(1, sum(r["support"] for r in supported)))
    return {
        "accuracy": round(correct / max(1, total), 4),
        "macro_f1": round(macro, 4),
        "weighted_f1": round(weighted, 4),
        "support": total,
        "per_class": rows,
    }


def _top_confusions(labels: pd.DataFrame, decisions: pd.DataFrame, limit: int = 15) -> list[dict]:
    merged = labels.merge(decisions[["transaction_id", "category_code"]], on="transaction_id", how="inner")
    bad = merged[merged["true_category_code"] != merged["category_code"]]
    counts = bad.groupby(["true_category_code", "category_code"]).size().reset_index(name="count")
    counts = counts.sort_values(["count", "true_category_code", "category_code"], ascending=[False, True, True], kind="mergesort").head(limit)
    return [{"true": r.true_category_code, "predicted": r.category_code, "count": int(r.count)} for r in counts.itertuples(index=False)]


def _monthly_coverage(txns: pd.DataFrame) -> list[dict]:
    monthly = txns.groupby(txns["transaction_date"].str[:7]).agg(
        transactions=("transaction_id", "count"),
        spend_gross=("amount_usd", lambda s: float(s[s < 0].abs().sum())),
        income=("amount_usd", lambda s: float(s[s > 0].sum())),
    )
    return [
        {
            "period_month": idx,
            "transactions": int(row.transactions),
            "gross_debits_usd": _round(row.spend_gross, 2),
            "credits_usd": _round(row.income, 2),
        }
        for idx, row in monthly.iterrows()
    ]


def run_evaluation(dataset_dir: str | Path = "dataset") -> dict:
    root = Path(dataset_dir)
    labels = _read(root / "ground_truth" / "transaction_labels.csv")
    budget_labels = _read(root / "ground_truth" / "budget_labels.csv")
    series_labels = _read(root / "ground_truth" / "recurring_series_labels.csv")
    expectations = _read(root / "ground_truth" / "recurring_expectations.csv")
    anomalies = _read(root / "ground_truth" / "anomaly_manifest.csv")
    txns = _read(root / "data" / "transaction.csv")
    budgets = _read(root / "data" / "budget.csv")
    detected = _read(root / "outputs" / "recurring_series.csv")
    decisions = _read(root / "outputs" / "categorization_decisions.csv")
    categorized = _read(root / "outputs" / "categorized_transactions.csv")
    budget_compare = _read(root / "outputs" / "budget_comparison.csv")
    monthly_spend = _read(root / "outputs" / "monthly_spend.csv")
    manifest = json.loads((root / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    validation_path = root / "validation" / "validation_summary.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else None

    joined = labels.merge(decisions[["transaction_id", "category_code", "predicted_treatment", "confidence", "decision_source"]], on="transaction_id", how="left")
    joined = joined.merge(txns[["transaction_id", "transaction_date", "posted_at_utc", "amount_usd", "descriptor", "merchant_id"]], on="transaction_id", how="left")
    joined["true_treatment"] = joined["true_treatment"].fillna("")
    joined["predicted_treatment"] = joined["predicted_treatment"].fillna("")

    category_metrics = _classification_metrics(joined["true_category_code"], joined["category_code"])
    category_metrics["coverage"] = _round(joined["category_code"].notna().mean(), 4)
    category_metrics["top_confusions"] = _top_confusions(labels, decisions)
    treatment_metrics = _classification_metrics(joined["true_treatment"], joined["predicted_treatment"])
    fallback_rate = float(joined["decision_source"].fillna("").eq("fallback").mean())
    other_rate = float(joined["category_code"].fillna("").eq("OTHER").mean())
    local_month = joined["transaction_date"].str[:7]
    utc_month = joined["posted_at_utc"].str[:7]
    expected_month = joined["expected_period"]
    boundary_mask = local_month != utc_month
    period_metrics = {
        "local_month_accuracy": _round((local_month == expected_month).mean(), 4),
        "utc_month_accuracy": _round((utc_month == expected_month).mean(), 4),
        "boundary_cases": int(boundary_mask.sum()),
        "boundary_share": _round(boundary_mask.mean(), 6),
    }

    distribution = {
        "transaction_category_counts": {str(k): int(v) for k, v in labels["true_category_code"].value_counts().sort_index().items()},
        "treatment_counts": {str(k): int(v) for k, v in labels["true_treatment"].value_counts().sort_index().items()},
        "issue_counts": {str(k): int(v) for k, v in labels["issue_type"].fillna("none").value_counts().sort_index().items()},
        "amount_usd": {
            "mean": _round(txns["amount_usd"].mean(), 2),
            "median": _round(txns["amount_usd"].median(), 2),
            "p05": _round(txns["amount_usd"].quantile(0.05), 2),
            "p95": _round(txns["amount_usd"].quantile(0.95), 2),
        },
        "monthly": _monthly_coverage(txns),
    }

    transfer_ids = set(labels.loc[labels["true_category_code"] == "TRANSFER", "transaction_id"])
    refund_ids = set(labels.loc[labels["true_treatment"] == "refund", "transaction_id"])
    transfer_amount = float(txns.set_index("transaction_id").loc[list(transfer_ids), "amount_usd"].abs().sum()) if transfer_ids else 0.0
    refund_amount = float(txns.set_index("transaction_id").loc[list(refund_ids), "amount_usd"].sum()) if refund_ids else 0.0
    strict_spend = float(categorized["spend_amount_usd"].sum())
    naive_overstatement = transfer_amount + 2.0 * refund_amount
    transfer_refund = {
        "transfer_transactions": len(transfer_ids),
        "transfer_absolute_amount_usd": _round(transfer_amount, 2),
        "refund_transactions": len(refund_ids),
        "refund_credit_amount_usd": _round(refund_amount, 2),
        "strict_net_spend_usd": _round(strict_spend, 2),
        "naive_spend_overstatement_usd": _round(naive_overstatement, 2),
        "naive_double_counted_transfer_usd": _round(transfer_amount, 2),
        "naive_refund_expense_effect_usd": _round(2.0 * refund_amount, 2),
        "transfers_handled_as_transfer": int(joined.loc[joined["true_category_code"] == "TRANSFER", "predicted_treatment"].eq("transfer").sum()),
        "refunds_handled_as_refund": int(joined.loc[joined["true_treatment"] == "refund", "predicted_treatment"].eq("refund").sum()),
    }

    anomaly_rows = []
    for issue in ["transfer_double_count", "refund_treated_as_new_expense", "timezone_boundary_date"]:
        item = joined[joined["issue_type"].fillna("") == issue]
        anomaly_rows.append(
            {
                "issue_type": issue,
                "labelled_rows": int(len(item)),
                "predicted_treatment_consistent": int((item["predicted_treatment"] == item["true_treatment"]).sum()),
                "predicted_category_consistent": int((item["category_code"] == item["true_category_code"]).sum()),
                "absolute_amount_usd": _round(item["amount_usd"].abs().sum(), 2),
            }
        )
    skip_gt = series_labels[series_labels["issue_type"].fillna("") == "recurring_series_skip"]
    skip_detected = set(detected.loc[detected["missed_occurrences"] > 0, "user_id"].astype(str) + "|" + detected.loc[detected["missed_occurrences"] > 0, "merchant_id"].astype(str))
    skip_keys = set(skip_gt["user_id"].astype(str) + "|" + skip_gt["merchant_id"].astype(str))
    skip_recall = _round(len(skip_keys & skip_detected) / len(skip_keys), 4) if skip_keys else None
    anomaly_rows.append(
        {
            "issue_type": "recurring_series_skip",
            "labelled_series": int(len(skip_gt)),
            "skip_flags_found": int(len(skip_keys & skip_detected)),
            "skip_recall": skip_recall,
        }
    )
    budget_mismatch = int(budget_labels["issue_type"].fillna("").eq("budget_taxonomy_mismatch").sum())
    resolved = int(budget_compare["resolution_source"].eq("alias").sum())
    unresolved = int(budget_compare["resolution_source"].eq("unresolved").sum())
    anomaly_rows.append(
        {
            "issue_type": "budget_taxonomy_mismatch",
            "labelled_rows": budget_mismatch,
            "resolved_rows": resolved,
            "unresolved_rows": unresolved,
            "resolution_rate": _round(resolved / budget_mismatch, 4) if budget_mismatch else None,
            "budget_amount_affected_usd": _round(budget_labels.loc[budget_labels["issue_type"].fillna("") == "budget_taxonomy_mismatch", "budget_amount_usd"].sum(), 2),
        }
    )
    exception_metrics = {
        "by_issue_type": anomaly_rows,
        "manifest_required_types": int(anomalies["issue_type"].nunique()),
    }

    gt_key = series_labels.assign(key=series_labels["user_id"].astype(str) + "|" + series_labels["merchant_id"].astype(str))
    det_key = detected.assign(key=detected["user_id"].astype(str) + "|" + detected["merchant_id"].astype(str))
    gt_key = gt_key.drop_duplicates("key", keep="first")
    det_key = det_key.drop_duplicates("key", keep="first")
    detectable = gt_key[gt_key["posted_occurrences"] >= 3]
    matched_keys = set(gt_key["key"]) & set(det_key["key"])
    false_positive = det_key[~det_key["key"].isin(set(gt_key["key"]))]
    false_negative = detectable[~detectable["key"].isin(set(det_key["key"]))]
    precision = len(matched_keys) / max(1, len(det_key))
    recall = len(matched_keys) / max(1, len(detectable))
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    matched_gt = gt_key[gt_key["key"].isin(matched_keys)]
    matched_det = det_key[det_key["key"].isin(matched_keys)].merge(
        gt_key[["key", "true_series_id", "category_code", "expected_amount_usd", "next_expected_date", "status"]],
        on="key",
        suffixes=("_det", "_gt"),
        how="left",
    )
    category_match = float((matched_det["category_code_det"] == matched_det["category_code_gt"]).mean()) if len(matched_det) else None
    amount_ape = ((matched_det["expected_amount_usd_det"] - matched_det["expected_amount_usd_gt"]).abs() / matched_det["expected_amount_usd_gt"].abs()).replace([np.inf, -np.inf], np.nan)
    amount_mape = float(amount_ape.mean()) if amount_ape.notna().any() else None
    date_errors = []
    for row in matched_det.itertuples(index=False):
        if isinstance(row.next_expected_date_gt, str) and row.next_expected_date_gt:
            try:
                d1 = pd.Timestamp(row.next_expected_date_det)
                d2 = pd.Timestamp(row.next_expected_date_gt)
                date_errors.append(abs((d1 - d2).days))
            except Exception:
                pass
    skip_series = set(skip_gt["user_id"].astype(str) + "|" + skip_gt["merchant_id"].astype(str))
    matched_skip = matched_det[matched_det["key"].isin(skip_series)]
    skip_detected_count = int((matched_skip["missed_occurrences"] > 0).sum())
    matched_non_skip = matched_det[~matched_det["key"].isin(skip_series)]
    false_skip_flags = int((matched_non_skip["missed_occurrences"] > 0).sum())
    expected_posted = expectations[expectations["outcome"] == "posted"]
    coverage_support = 0
    if len(matched_det):
        for row in matched_det.itertuples(index=False):
            subset = expected_posted[(expected_posted["true_series_id"] == row.true_series_id) & (expected_posted["occurrence_date"] >= row.first_occurrence) & (expected_posted["occurrence_date"] <= row.last_occurrence)]
            coverage_support += len(subset)
    occurrence_coverage = _round(coverage_support / max(1, len(expected_posted)), 4)
    recurring_metrics = {
        "ground_truth_series": int(len(gt_key)),
        "detectable_series": int(len(detectable)),
        "detected_series": int(len(det_key)),
        "matched_series": int(len(matched_keys)),
        "precision": _round(precision, 4),
        "recall": _round(recall, 4),
        "f1": _round(f1, 4),
        "false_positives": int(len(false_positive)),
        "false_negatives": int(len(false_negative)),
        "category_accuracy_matched": _round(category_match, 4) if category_match is not None else None,
        "amount_mape_matched": _round(amount_mape, 4) if amount_mape is not None else None,
        "next_date_median_abs_error_days": _round(np.median(date_errors), 2) if date_errors else None,
        "next_date_compared": len(date_errors),
        "skip_series": int(len(skip_series)),
        "skip_series_flagged": skip_detected_count,
        "skip_recall": _round(skip_detected_count / len(skip_series), 4) if skip_series else None,
        "skip_false_positives": false_skip_flags,
        "skip_precision": _round(skip_detected_count / max(1, skip_detected_count + false_skip_flags), 4),
        "gt_occurrence_support": occurrence_coverage,
    }

    budget_joined = budget_compare.merge(
        budget_labels[["budget_id", "resolved_category_code", "issue_type", "stored_category_code"]],
        on="budget_id",
        how="left",
        suffixes=("_out", "_gt"),
    )
    mismatch = budget_joined[budget_joined["issue_type"].fillna("") == "budget_taxonomy_mismatch"]
    resolution_accuracy = float((mismatch["resolved_category_code_out"] == mismatch["resolved_category_code_gt"]).mean()) if len(mismatch) else None
    budget_metrics = {
        "budget_rows": int(len(budgets)),
        "comparison_rows": int(len(budget_compare)),
        "resolution_accuracy": _round(resolution_accuracy, 4) if resolution_accuracy is not None else None,
        "resolved_alias_rows": int(budget_compare["resolution_source"].eq("alias").sum()),
        "unresolved_rows": int(budget_compare["resolution_source"].eq("unresolved").sum()),
        "status_counts": {str(k): int(v) for k, v in budget_compare["status"].value_counts().sort_index().items()},
        "budget_total_usd": _round(budget_compare["budget_amount_usd"].sum(), 2),
        "actual_total_usd": _round(budget_compare["actual_spend_usd"].sum(), 2),
        "variance_total_usd": _round(budget_compare["variance_usd"].sum(), 2),
        "over_budget_rows": int((budget_compare["status"] == "over").sum()),
        "naive_mismatch_false_under_rows": int(len(mismatch)),
        "naive_mismatch_budget_affected_usd": _round(mismatch["budget_amount_usd"].sum(), 2),
    }

    ledger_total = float(txns["amount_usd"].sum())
    categorized_total = float(categorized["spend_amount_usd"].sum())
    monthly_total = float(monthly_spend["spend_usd"].sum())
    reconciliation = {
        "ledger_net_total_usd": _round(ledger_total, 2),
        "strict_net_spend_usd": _round(categorized_total, 2),
        "monthly_spend_total_usd": _round(monthly_total, 2),
        "strict_vs_monthly_delta_usd": _round(categorized_total - monthly_total, 2),
        "account_balance_total_usd": _round(float(_read(root / "data" / "account.csv")["current_balance_usd"].sum()), 2),
        "ledger_vs_balance_delta_usd": _round(ledger_total - float(_read(root / "data" / "account.csv")["current_balance_usd"].sum()), 2),
        "rows": int(len(txns)),
        "months": int(txns["transaction_date"].str[:7].nunique()),
        "profiles": int(manifest["counts"]["profiles"]),
    }

    exception_scores = []
    tr = next(x for x in anomaly_rows if x["issue_type"] == "transfer_double_count")
    rr = next(x for x in anomaly_rows if x["issue_type"] == "refund_treated_as_new_expense")
    tz = next(x for x in anomaly_rows if x["issue_type"] == "timezone_boundary_date")
    bm = next(x for x in anomaly_rows if x["issue_type"] == "budget_taxonomy_mismatch")
    exception_scores.extend(
        [
            tr["predicted_treatment_consistent"] / max(1, tr["labelled_rows"]),
            rr["predicted_treatment_consistent"] / max(1, rr["labelled_rows"]),
            period_metrics["local_month_accuracy"],
            skip_recall if skip_recall is not None else 0.0,
            bm["resolution_rate"] if bm["resolution_rate"] is not None else 0.0,
        ]
    )
    exception_handling_score = _round(float(np.mean(exception_scores)), 4)
    data_quality = {
        "fallback_rate": _round(fallback_rate, 4),
        "uncategorized_rate": _round(other_rate, 4),
        "mean_confidence": _round(joined["confidence"].mean(), 4),
        "unique_merchants": int(txns["merchant_id"].dropna().nunique()),
        "descriptor_variants": int(txns["descriptor"].nunique()),
    }

    report = {
        "dataset": str(root),
        "seed": manifest["seed"],
        "scale": manifest["scale"],
        "generated_at": manifest["generated_at"],
        "evaluated_at": FIXED_GENERATED_AT,
        "validation_status": validation["status"] if validation else None,
        "validation_checks": validation["counts"] if validation else None,
        "sections": {
            "categorization": category_metrics,
            "treatment": treatment_metrics,
            "period_assignment": period_metrics,
            "transfer_and_refund": transfer_refund,
            "exceptions": exception_metrics,
            "exception_handling_score": exception_handling_score,
            "recurring_detection": recurring_metrics,
            "budget_comparison": budget_metrics,
            "reconciliation": reconciliation,
            "data_quality": data_quality,
            "distributions": distribution,
        },
        "notes": [
            "The pipeline never reads ground_truth/. It is joined only in this evaluation step.",
            "Strict net spend excludes transfers, offsets refunds, and assigns periods from local transaction dates.",
            "Naive overstatement is a diagnostic: both transfer legs and refunds are treated as new spending.",
            "Recurring detection uses monthly gap and amount stability; labels are generated independently from the detector.",
            "Budget resolution maps deprecated taxonomy codes through category_alias before comparison.",
            "A boundary-case row that also carries a primary refund/transfer anomaly keeps that primary transaction label; all boundary rows still have ground-truth labels.",
        ],
    }
    out_dir = root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "evaluation_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out_dir / "evaluation_report.md").write_text(_evaluation_markdown(report), encoding="utf-8")
    return report


def _evaluation_markdown(report: dict) -> str:
    s = report["sections"]
    c = s["categorization"]
    t = s["treatment"]
    p = s["period_assignment"]
    tr = s["transfer_and_refund"]
    rec = s["recurring_detection"]
    b = s["budget_comparison"]
    r = s["reconciliation"]
    d = s["data_quality"]
    skip_rec = f"{rec['skip_recall']:.2%}" if rec["skip_recall"] is not None else "n/a"
    resolution = f"{b['resolution_accuracy']:.2%}" if b["resolution_accuracy"] is not None else "n/a"
    lines = [
        "# Evaluation Report",
        "",
        f"Seed `{report['seed']}` | scale `{report['scale']}` | validation `{report['validation_status']}`",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Categorization accuracy | {c['accuracy']:.2%} |",
        f"| Categorization macro F1 | {c['macro_f1']:.4f} |",
        f"| Treatment accuracy | {t['accuracy']:.2%} |",
        f"| Local-period accuracy | {p['local_month_accuracy']:.2%} |",
        f"| UTC-period baseline | {p['utc_month_accuracy']:.2%} |",
        f"| Recurring precision | {rec['precision']:.2%} |",
        f"| Recurring recall | {rec['recall']:.2%} |",
        f"| Recurring F1 | {rec['f1']:.4f} |",
        f"| Recurring skip recall | {skip_rec} |",
        f"| Budget taxonomy resolution | {resolution} |",
        f"| Exception handling score | {s['exception_handling_score']:.4f} |",
        f"| Fallback rate | {d['fallback_rate']:.2%} |",
        f"| Uncategorized rate | {d['uncategorized_rate']:.2%} |",
        "",
        "## 1. Categorization",
        "",
        f"Accuracy **{c['accuracy']:.2%}**, macro F1 **{c['macro_f1']:.4f}**, weighted F1 **{c['weighted_f1']:.4f}** over {c['support']:,} labelled transactions.",
        "",
        "| Class | Support | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in c["per_class"]:
        if row["support"]:
            lines.append(f"| {row['class']} | {row['support']} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} |")
    lines += ["", "Top confusions:", "", "| True | Predicted | Count |", "|---|---|---:|"]
    for row in c["top_confusions"]:
        lines.append(f"| {row['true']} | {row['predicted']} | {row['count']} |")
    lines += [
        "",
        "## 2. Transfers, refunds, and period assignment",
        "",
        f"- Transfer transactions: **{tr['transfer_transactions']:,}** (absolute amount **${tr['transfer_absolute_amount_usd']:,.2f}**)",
        f"- Refund transactions: **{tr['refund_transactions']:,}** (credit amount **${tr['refund_credit_amount_usd']:,.2f}**)",
        f"- Strict net spend: **${tr['strict_net_spend_usd']:,.2f}**",
        f"- Naive overstatement if transfer legs and refunds are treated as new spend: **${tr['naive_spend_overstatement_usd']:,.2f}**",
        f"- Transfers handled as transfers: **{tr['transfers_handled_as_transfer']:,}**",
        f"- Refunds handled as refunds: **{tr['refunds_handled_as_refund']:,}**",
        f"- UTC/local month boundary cases: **{p['boundary_cases']:,}**; local-period accuracy **{p['local_month_accuracy']:.2%}**, UTC baseline **{p['utc_month_accuracy']:.2%}**.",
        "",
        "## 3. Recurring detection",
        "",
        f"Ground truth series **{rec['ground_truth_series']:,}**, detectable **{rec['detectable_series']:,}**, detected **{rec['detected_series']:,}**, matched **{rec['matched_series']:,}**.",
        "",
        f"Precision **{rec['precision']:.2%}**, recall **{rec['recall']:.2%}**, F1 **{rec['f1']:.4f}**, false positives **{rec['false_positives']:,}**, false negatives **{rec['false_negatives']:,}**.",
        "",
        f"- Category accuracy on matched series: **{rec['category_accuracy_matched'] if rec['category_accuracy_matched'] is not None else 'n/a'}**",
        f"- Expected-amount MAPE: **{rec['amount_mape_matched'] if rec['amount_mape_matched'] is not None else 'n/a'}**",
        f"- Next-date median absolute error: **{rec['next_date_median_abs_error_days'] if rec['next_date_median_abs_error_days'] is not None else 'n/a'} days**",
        f"- Skipped-series recall: **{skip_rec}** ({rec['skip_series_flagged']}/{rec['skip_series']})",
        f"- Skipped-series precision: **{rec['skip_precision']:.2%}** (false skip flags {rec['skip_false_positives']})",
        f"- Ground-truth posted-occurrence support: **{rec['gt_occurrence_support']:.2%}**",
        "",
        "## 4. Budget comparison",
        "",
        f"- Budgets: **{b['budget_rows']:,}**; comparison rows: **{b['comparison_rows']:,}**",
        f"- Total budget: **${b['budget_total_usd']:,.2f}**; actual: **${b['actual_total_usd']:,.2f}**; variance: **${b['variance_total_usd']:,.2f}**",
        f"- Status counts: **{b['status_counts']}**",
        f"- Taxonomy-mismatch resolution accuracy: **{resolution}**",
        f"- Naive direct joins that would falsely appear under budget: **{b['naive_mismatch_false_under_rows']:,}** rows / **${b['naive_mismatch_budget_affected_usd']:,.2f}**",
        "",
        "## 5. Reconciliation",
        "",
        f"- Ledger net total: **${r['ledger_net_total_usd']:,.2f}**",
        f"- Account balance total: **${r['account_balance_total_usd']:,.2f}** (delta ${r['ledger_vs_balance_delta_usd']:,.2f})",
        f"- Strict spend via categorized ledger: **${r['strict_net_spend_usd']:,.2f}**",
        f"- Monthly spend rollup: **${r['monthly_spend_total_usd']:,.2f}** (delta ${r['strict_vs_monthly_delta_usd']:,.2f})",
        f"- Rows: **{r['rows']:,}**, profiles: **{r['profiles']:,}**, months: **{r['months']}**",
        "",
        "## 6. Labelled exceptions",
        "",
        "| Issue | Labelled | Treatment consistent | Category consistent | Amount |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in s["exceptions"]["by_issue_type"]:
        if "predicted_treatment_consistent" in row:
            lines.append(f"| {row['issue_type']} | {row['labelled_rows']} | {row['predicted_treatment_consistent']} | {row['predicted_category_consistent']} | ${row['absolute_amount_usd']:,.2f} |")
        elif row["issue_type"] == "recurring_series_skip":
            lines.append(f"| {row['issue_type']} | series {row['labelled_series']} | flags {row['skip_flags_found']} | skip recall {row['skip_recall']} | - |")
        else:
            lines.append(f"| {row['issue_type']} | {row['labelled_rows']} | resolved {row['resolved_rows']} | unresolved {row['unresolved_rows']} | ${row['budget_amount_affected_usd']:,.2f} |")
    lines += [
        "",
        "## 7. Distributions",
        "",
        "| Month | Transactions | Gross debits | Credits |",
        "|---|---:|---:|---:|",
    ]
    for row in s["distributions"]["monthly"]:
        lines.append(f"| {row['period_month']} | {row['transactions']:,} | ${row['gross_debits_usd']:,.2f} | ${row['credits_usd']:,.2f} |")
    dist = s["distributions"]
    lines += [
        "",
        "### Amount distribution",
        "",
        "| Statistic | Signed amount (USD) |",
        "|---|---:|",
        f"| Mean | {dist['amount_usd']['mean']:,.2f} |",
        f"| Median | {dist['amount_usd']['median']:,.2f} |",
        f"| P05 | {dist['amount_usd']['p05']:,.2f} |",
        f"| P95 | {dist['amount_usd']['p95']:,.2f} |",
        "",
        "### True category distribution",
        "",
        "| Category | Transactions |",
        "|---|---:|",
    ]
    for key, value in dist["transaction_category_counts"].items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "### Treatment distribution",
        "",
        "| Treatment | Transactions |",
        "|---|---:|",
    ]
    for key, value in dist["treatment_counts"].items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "### Ground-truth issue distribution",
        "",
        "| Issue type | Transactions |",
        "|---|---:|",
    ]
    for key, value in dist["issue_counts"].items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "---",
        "",
        "Notes:",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)
