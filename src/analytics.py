from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .config import FIXED_GENERATED_AT, FORMULA_VERSION
from .rules import RuleEngine
from .taxonomy import CATEGORY_BY_CODE, LEGACY_CATEGORY_ALIASES

INSIGHT_HEADERS = [
    "insight_id",
    "user_id",
    "period_month",
    "insight_type",
    "metric_name",
    "metric_value",
    "currency",
    "details_json",
    "source_txn_count",
    "formula_version",
    "generated_at",
    "status",
]

BUDGET_COMPARISON_HEADERS = [
    "budget_id",
    "user_id",
    "period_month",
    "stored_category_code",
    "resolved_category_code",
    "resolution_source",
    "resolution_note",
    "budget_amount_usd",
    "actual_spend_usd",
    "variance_usd",
    "usage_pct",
    "status",
]

DECISION_HEADERS = [
    "decision_id",
    "transaction_id",
    "category_code",
    "rule_id",
    "confidence",
    "decision_source",
    "predicted_treatment",
    "decided_at",
    "model_version",
]

RECURRING_HEADERS = [
    "series_id",
    "user_id",
    "account_id",
    "merchant_id",
    "category_code",
    "cadence",
    "expected_amount_usd",
    "first_occurrence",
    "last_occurrence",
    "occurrence_count",
    "missed_occurrences",
    "next_expected_date",
    "status",
    "confidence",
    "detection_method",
    "detected_at",
]


def _category_type(code: str) -> str:
    item = CATEGORY_BY_CODE.get(code)
    return item["type"] if item else "expense"


def apply_categorization(transactions: pd.DataFrame, rules: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = RuleEngine(rules)
    result = engine.apply(transactions["descriptor"], transactions["amount_usd"])
    working = transactions.copy()
    working["predicted_category_code"] = result["predicted_category_code"].to_numpy()
    working["rule_id"] = result["rule_id"].to_numpy()
    working["confidence"] = result["confidence"].to_numpy()
    working["decision_source"] = result["decision_source"].to_numpy()
    working["category_type"] = working["predicted_category_code"].map(lambda c: _category_type(c))

    amount = working["amount_usd"].to_numpy()
    ptype = working["category_type"].to_numpy()
    treatment = np.where(
        ptype == "transfer",
        "transfer",
        np.where(amount > 0, np.where(ptype == "income", "income", "refund"), np.where(ptype == "income", "income", "spend")),
    )
    working["predicted_treatment"] = treatment

    decisions = pd.DataFrame(
        {
            "transaction_id": working["transaction_id"],
            "category_code": working["predicted_category_code"],
            "rule_id": working["rule_id"],
            "confidence": working["confidence"],
            "decision_source": working["decision_source"],
            "predicted_treatment": working["predicted_treatment"],
            "decided_at": FIXED_GENERATED_AT,
            "model_version": "rules-v1",
        }
    )
    decisions.insert(0, "decision_id", [f"DCS-{i:08d}" for i in range(1, len(decisions) + 1)])
    return working, decisions[DECISION_HEADERS]


def _offset_categories(working: pd.DataFrame, merchants: pd.DataFrame) -> pd.Series:
    pred_by_txn = working.set_index("transaction_id")["predicted_category_code"]
    default_by_merchant = merchants.set_index("merchant_id")["default_category_code"]
    refund_mask = working["predicted_treatment"].eq("refund")
    linked = working["refund_of_txn_id"].map(pred_by_txn)
    merchant_default = working["merchant_id"].map(default_by_merchant)
    offset = working["predicted_category_code"].where(~refund_mask, linked)
    offset = offset.where(~(refund_mask & offset.isna()), merchant_default)
    return offset.fillna("OTHER")


def build_spend_ledger(working: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame:
    ledger = working.copy()
    ledger["offset_category_code"] = _offset_categories(ledger, merchants)
    amount = ledger["amount_usd"].to_numpy()
    treatment = ledger["predicted_treatment"].to_numpy()
    spend = np.where(treatment == "spend", np.abs(amount), np.where(treatment == "refund", -np.abs(amount), 0.0))
    ledger["spend_amount_usd"] = np.round(spend, 2)
    ledger["period_month"] = ledger["transaction_date"].str[:7]
    return ledger


def resolve_budget_categories(budgets: pd.DataFrame) -> pd.DataFrame:
    resolved = budgets.copy()
    active_codes = {c for c, item in CATEGORY_BY_CODE.items() if item["active"]}
    category, source, note = [], [], []
    for code in resolved["category_code"]:
        if code in active_codes:
            category.append(code)
            source.append("direct")
            note.append("")
        elif code in LEGACY_CATEGORY_ALIASES:
            target, reason = LEGACY_CATEGORY_ALIASES[code]
            category.append(target)
            source.append("alias")
            note.append(reason)
        else:
            category.append("OTHER")
            source.append("unresolved")
            note.append("Unknown category code mapped to OTHER for comparison.")
    resolved["resolved_category_code"] = category
    resolved["resolution_source"] = source
    resolved["resolution_note"] = note
    return resolved


def build_budget_comparison(ledger: pd.DataFrame, budgets: pd.DataFrame) -> pd.DataFrame:
    resolved = resolve_budget_categories(budgets)
    actual = (
        ledger[ledger["predicted_treatment"].isin(["spend", "refund"])]
        .groupby(["user_id", "period_month", "offset_category_code"], sort=False)["spend_amount_usd"]
        .sum()
        .reset_index()
    )
    actual = actual.rename(columns={"offset_category_code": "resolved_category_code", "spend_amount_usd": "actual_spend_usd"})
    resolved["period_month"] = resolved["year"].astype(str) + "-" + resolved["month"].astype(int).astype(str).str.zfill(2)
    keys = ["user_id", "period_month", "resolved_category_code"]
    merged = resolved.merge(actual, on=keys, how="left")
    merged["actual_spend_usd"] = merged["actual_spend_usd"].fillna(0.0).round(2)
    merged["budget_amount_usd"] = merged["budget_amount_usd"].round(2)
    merged["variance_usd"] = (merged["budget_amount_usd"] - merged["actual_spend_usd"]).round(2)
    merged["usage_pct"] = np.where(
        merged["budget_amount_usd"] > 0,
        (merged["actual_spend_usd"] / merged["budget_amount_usd"] * 100.0).round(2),
        np.nan,
    )
    merged["status"] = np.where(
        merged["actual_spend_usd"] > merged["budget_amount_usd"],
        "over",
        np.where(merged["actual_spend_usd"] >= merged["budget_amount_usd"] * 0.9, "near", "under"),
    )
    merged = merged.rename(
        columns={
            "category_code": "stored_category_code",
            "budget_amount": "budget_amount_usd",
        }
    )
    merged["period_month"] = (
        merged["year"].astype(str) + "-" + merged["month"].astype(int).astype(str).str.zfill(2)
    )
    output = merged[
        [
            "budget_id",
            "user_id",
            "period_month",
            "stored_category_code",
            "resolved_category_code",
            "resolution_source",
            "resolution_note",
            "budget_amount_usd",
            "actual_spend_usd",
            "variance_usd",
            "usage_pct",
            "status",
        ]
    ].copy()
    output = output.sort_values(["user_id", "period_month", "resolved_category_code"], kind="mergesort").reset_index(drop=True)
    return output[BUDGET_COMPARISON_HEADERS]


def detect_recurring(ledger: pd.DataFrame) -> pd.DataFrame:
    candidates = ledger[
        (ledger["status"] == "posted")
        & ledger["merchant_id"].fillna("").ne("")
        & ledger["predicted_treatment"].isin(["spend", "income"])
        & (ledger["amount_usd"].abs() > 0)
    ].copy()
    candidates["sign"] = np.where(candidates["amount_usd"] > 0, "credit", "debit")
    candidates["date"] = pd.to_datetime(candidates["transaction_date"])
    rows = []
    for (user_id, merchant_id, sign), group in candidates.groupby(["user_id", "merchant_id", "sign"], sort=False):
        if len(group) < 3:
            continue
        group = group.sort_values("date", kind="mergesort")
        distinct_months = group["date"].dt.to_period("M").nunique()
        if distinct_months < 3:
            continue
        dates = group["date"].dt.date.tolist()
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        if not gaps:
            continue
        median_gap = float(np.median(gaps))
        if not (25 <= median_gap <= 35):
            continue
        amounts = group["amount_usd"].abs().to_numpy()
        mean_amount = float(amounts.mean())
        if mean_amount <= 0:
            continue
        cv = float(amounts.std(ddof=0) / mean_amount)
        if cv > 0.22:
            continue
        missed = sum(1 for g in gaps if g > 45)
        last_date = dates[-1]
        next_date = last_date + timedelta(days=int(round(median_gap)))
        if last_date < date(2026, 10, 1) and missed > 0:
            state = "ended"
        elif next_date > date(2027, 2, 15):
            state = "ended"
        else:
            state = "active"
        category = group["predicted_category_code"].mode().iloc[0]
        account = group["account_id"].mode().iloc[0]
        confidence = min(0.99, 0.55 + 0.05 * distinct_months + (0.14 if cv < 0.05 else 0.06))
        rows.append(
            {
                "user_id": user_id,
                "account_id": account,
                "merchant_id": merchant_id,
                "category_code": category,
                "cadence": "monthly",
                "expected_amount_usd": round(float(np.median(amounts)), 2),
                "first_occurrence": dates[0].strftime("%Y-%m-%d"),
                "last_occurrence": last_date.strftime("%Y-%m-%d"),
                "occurrence_count": int(len(group)),
                "missed_occurrences": int(missed),
                "next_expected_date": next_date.strftime("%Y-%m-%d"),
                "status": state,
                "confidence": round(confidence, 3),
                "detection_method": "monthly_gap_amount_stability_v1",
                "detected_at": FIXED_GENERATED_AT,
            }
        )
    series = pd.DataFrame(rows)
    if series.empty:
        series = pd.DataFrame(columns=RECURRING_HEADERS[1:])
    series = series.sort_values(["user_id", "merchant_id", "account_id"], kind="mergesort").reset_index(drop=True)
    series.insert(0, "series_id", [f"REC-{i:06d}" for i in range(1, len(series) + 1)])
    return series[RECURRING_HEADERS]


def build_insights(
    ledger: pd.DataFrame,
    budget_comparison: pd.DataFrame,
    recurring_series: pd.DataFrame,
) -> pd.DataFrame:
    ledger = ledger.copy()
    ledger["period_month"] = ledger["transaction_date"].str[:7]
    ledger["income_amount"] = np.where(ledger["predicted_treatment"] == "income", ledger["amount_usd"], 0.0)
    ledger["refund_flag"] = (ledger["predicted_treatment"] == "refund").astype(int)
    ledger["transfer_flag"] = (ledger["predicted_treatment"] == "transfer").astype(int)
    ledger["fallback_flag"] = (ledger["decision_source"] == "fallback").astype(int)
    ledger["uncategorized_flag"] = (ledger["predicted_category_code"] == "OTHER").astype(int)
    monthly = (
        ledger.groupby(["user_id", "period_month"], sort=False)
        .agg(
            txn_count=("transaction_id", "count"),
            spend_total=("spend_amount_usd", "sum"),
            income_total=("income_amount", "sum"),
            refund_count=("refund_flag", "sum"),
            transfer_count=("transfer_flag", "sum"),
            fallback_count=("fallback_flag", "sum"),
            uncategorized_count=("uncategorized_flag", "sum"),
        )
        .reset_index()
    )
    spend_only = ledger[ledger["predicted_treatment"] == "spend"]
    top = (
        spend_only.groupby(["user_id", "period_month", "predicted_category_code"], sort=False)["spend_amount_usd"]
        .sum()
        .reset_index()
        .sort_values(["user_id", "period_month", "spend_amount_usd"], ascending=[True, True, False], kind="mergesort")
        .drop_duplicates(["user_id", "period_month"])
        .rename(columns={"predicted_category_code": "top_category", "spend_amount_usd": "top_category_spend"})
    )
    monthly = monthly.merge(top[["user_id", "period_month", "top_category", "top_category_spend"]], on=["user_id", "period_month"], how="left")
    budget_monthly = (
        budget_comparison.groupby(["user_id", "period_month"], sort=False)
        .agg(
            budget_total=("budget_amount_usd", "sum"),
            budget_actual=("actual_spend_usd", "sum"),
            over_budget_count=("status", lambda s: int((s == "over").sum())),
            near_budget_count=("status", lambda s: int((s == "near").sum())),
        )
        .reset_index()
    )
    monthly = monthly.merge(budget_monthly, on=["user_id", "period_month"], how="left")
    recurring_counts = recurring_series.groupby("user_id", sort=False).size().rename("recurring_count").reset_index()
    recurring_amounts = recurring_series.groupby("user_id", sort=False)["expected_amount_usd"].sum().rename("recurring_monthly").reset_index()
    monthly = monthly.merge(recurring_counts, on="user_id", how="left").merge(recurring_amounts, on="user_id", how="left")
    monthly = monthly.sort_values(["user_id", "period_month"], kind="mergesort").reset_index(drop=True)

    rows = []
    for row in monthly.itertuples(index=False):
        txn_count = int(row.txn_count)
        spend_total = round(float(row.spend_total), 2)
        income_total = round(float(row.income_total), 2)
        net = round(income_total - spend_total, 2)
        top_category = "" if pd.isna(row.top_category) else str(row.top_category)
        top_spend = 0.0 if pd.isna(row.top_category_spend) else round(float(row.top_category_spend), 2)
        budget_total = 0.0 if pd.isna(row.budget_total) else round(float(row.budget_total), 2)
        budget_actual = 0.0 if pd.isna(row.budget_actual) else round(float(row.budget_actual), 2)
        over_count = 0 if pd.isna(row.over_budget_count) else int(row.over_budget_count)
        near_count = 0 if pd.isna(row.near_budget_count) else int(row.near_budget_count)
        recurring_count = 0 if pd.isna(row.recurring_count) else int(row.recurring_count)
        recurring_monthly = 0.0 if pd.isna(row.recurring_monthly) else round(float(row.recurring_monthly), 2)
        uncategorized_rate = round(float(row.uncategorized_count) / txn_count, 4) if txn_count else 0.0
        fallback_rate = round(float(row.fallback_count) / txn_count, 4) if txn_count else 0.0
        rows.append(
            {
                "user_id": row.user_id,
                "period_month": row.period_month,
                "insight_type": "monthly_spend_summary",
                "metric_name": "net_spend_usd",
                "metric_value": spend_total,
                "details": {"top_category": top_category, "top_category_spend_usd": top_spend, "txn_count": txn_count},
            }
        )
        rows.append(
            {
                "user_id": row.user_id,
                "period_month": row.period_month,
                "insight_type": "monthly_spend_summary",
                "metric_name": "net_savings_usd",
                "metric_value": net,
                "details": {"income_usd": income_total, "spend_usd": spend_total, "txn_count": txn_count},
            }
        )
        rows.append(
            {
                "user_id": row.user_id,
                "period_month": row.period_month,
                "insight_type": "budget_variance_summary",
                "metric_name": "budget_variance_usd",
                "metric_value": round(budget_total - budget_actual, 2),
                "details": {
                    "budget_total_usd": budget_total,
                    "actual_budgeted_spend_usd": budget_actual,
                    "over_budget_categories": over_count,
                    "near_budget_categories": near_count,
                    "txn_count": txn_count,
                },
            }
        )
        rows.append(
            {
                "user_id": row.user_id,
                "period_month": row.period_month,
                "insight_type": "recurring_summary",
                "metric_name": "recurring_series_count",
                "metric_value": recurring_count,
                "details": {"expected_monthly_recurring_usd": recurring_monthly, "txn_count": txn_count},
            }
        )
        rows.append(
            {
                "user_id": row.user_id,
                "period_month": row.period_month,
                "insight_type": "data_quality_summary",
                "metric_name": "uncategorized_rate",
                "metric_value": uncategorized_rate,
                "details": {
                    "fallback_rate": fallback_rate,
                    "refund_transactions": int(row.refund_count),
                    "transfer_transactions": int(row.transfer_count),
                    "txn_count": txn_count,
                },
            }
        )
    insights = pd.DataFrame(rows)
    insights = insights.sort_values(["user_id", "period_month", "insight_type", "metric_name"], kind="mergesort").reset_index(drop=True)
    insights["insight_id"] = [f"INS-{i:06d}" for i in range(1, len(insights) + 1)]
    insights["currency"] = "USD"
    insights["details_json"] = insights["details"].map(lambda d: json.dumps(d, sort_keys=True, separators=(",", ":")))
    insights["source_txn_count"] = insights["details"].map(lambda d: int(d.get("txn_count", 0)))
    insights["formula_version"] = FORMULA_VERSION
    insights["generated_at"] = FIXED_GENERATED_AT
    insights["status"] = "generated"
    return insights[INSIGHT_HEADERS]


def build_reference_outputs(
    transactions: pd.DataFrame,
    rules: pd.DataFrame,
    merchants: pd.DataFrame,
    budgets: pd.DataFrame,
    users: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    working, decisions = apply_categorization(transactions, rules)
    ledger = build_spend_ledger(working, merchants)
    recurring = detect_recurring(ledger)
    budget_comparison = build_budget_comparison(ledger, budgets)
    insights = build_insights(ledger, budget_comparison, recurring)
    ledger["income_amount"] = np.where(ledger["predicted_treatment"] == "income", ledger["amount_usd"], 0.0)
    ledger["refund_flag"] = (ledger["predicted_treatment"] == "refund").astype(int)
    ledger["transfer_flag"] = (ledger["predicted_treatment"] == "transfer").astype(int)
    monthly_spend = (
        ledger.assign(period_month=ledger["transaction_date"].str[:7])
        .groupby(["user_id", "period_month"], sort=False)
        .agg(
            spend_usd=("spend_amount_usd", "sum"),
            income_usd=("income_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            refund_count=("refund_flag", "sum"),
            transfer_count=("transfer_flag", "sum"),
        )
        .reset_index()
        .sort_values(["user_id", "period_month"], kind="mergesort")
        .reset_index(drop=True)
    )
    monthly_spend["spend_usd"] = monthly_spend["spend_usd"].round(2)
    monthly_spend["income_usd"] = monthly_spend["income_usd"].round(2)
    categorized = ledger[
        [
            "transaction_id",
            "user_id",
            "account_id",
            "transaction_date",
            "posted_at_utc",
            "descriptor",
            "amount_usd",
            "predicted_category_code",
            "rule_id",
            "confidence",
            "decision_source",
            "predicted_treatment",
            "offset_category_code",
            "spend_amount_usd",
        ]
    ].copy()
    return {
        "working": working,
        "ledger": ledger,
        "decisions": decisions,
        "categorized_transactions": categorized,
        "recurring_series": recurring,
        "budget_comparison": budget_comparison,
        "insights": insights,
        "monthly_spend": monthly_spend,
    }
