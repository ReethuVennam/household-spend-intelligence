from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.cli import _compare_manifests
from src.config import SCALES, SEED
from src.generator import generate_dataset
from src.metrics import run_evaluation
from src.validation import run_validation

REQUIRED_ISSUES = {
    "transfer_double_count",
    "refund_treated_as_new_expense",
    "recurring_series_skip",
    "timezone_boundary_date",
    "budget_taxonomy_mismatch",
}

PRIMARY_KEYS = {
    "user_profile": "user_id",
    "account": "account_id",
    "merchant": "merchant_id",
    "merchant_alias": "alias_id",
    "category": "category_code",
    "category_alias": "alias_id",
    "category_rule": "rule_id",
    "budget": "budget_id",
    "transaction": "transaction_id",
    "transfer_link": "link_id",
    "recurring_series": "series_id",
    "insight": "insight_id",
    "entity_event": "event_id",
}

GROUND_TRUTH_LEAK_COLUMNS = {
    "true_category_code",
    "true_treatment",
    "true_series_id",
    "expected_period",
    "issue_type",
    "issue_detail",
    "is_recurring",
    "related_transaction_id",
}


def _csv(ds: Path, name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ds / "data" / f"{name}.csv", **kwargs)


def test_scale_volume_and_seed(mini_dataset: Path, manifest: dict):
    expected = SCALES["mini"]
    assert manifest["seed"] == SEED
    assert manifest["counts"]["profiles"] == expected["profiles"]
    assert manifest["counts"]["transactions"] == expected["transactions"]
    assert manifest["scale"] == "mini"


def test_id_formats_follow_conventions(mini_dataset: Path):
    users = _csv(mini_dataset, "user_profile")["user_id"]
    assert users.str.fullmatch(r"USR-\d{6}").all()
    accounts = _csv(mini_dataset, "account")["account_id"]
    assert accounts.str.fullmatch(r"ACC-USR-\d{6}-\d{2}").all()
    txns = _csv(mini_dataset, "transaction", usecols=["transaction_id"])
    assert txns["transaction_id"].str.fullmatch(r"TXN-2026-\d{8}").all()
    budgets = _csv(mini_dataset, "budget")["budget_id"]
    assert budgets.str.fullmatch(r"BUD-USR-\d{6}-2026-\d{2}-[A-Z_]+").all()
    series = _csv(mini_dataset, "recurring_series")["series_id"]
    assert series.str.fullmatch(r"REC-\d{6}").all()


def test_primary_key_uniqueness(mini_dataset: Path):
    for table, key in PRIMARY_KEYS.items():
        path = mini_dataset / "data" / f"{table}.csv"
        assert path.exists(), f"missing export for {table}"
        col = pd.read_csv(path, usecols=[key])[key]
        assert col.notna().all(), f"{table}.{key} contains nulls"
        assert col.is_unique, f"{table}.{key} not unique"


def test_foreign_keys_resolve_to_parents(mini_dataset: Path):
    users = set(_csv(mini_dataset, "user_profile", usecols=["user_id"])["user_id"])
    accounts = set(_csv(mini_dataset, "account", usecols=["account_id"])["account_id"])
    categories = set(_csv(mini_dataset, "category", usecols=["category_code"])["category_code"])
    txns = _csv(mini_dataset, "transaction", usecols=["transaction_id", "user_id", "account_id"])
    assert set(txns["user_id"]) <= users
    assert set(txns["account_id"]) <= accounts
    acct_users = set(_csv(mini_dataset, "account", usecols=["user_id"])["user_id"])
    assert acct_users <= users
    budgets = _csv(mini_dataset, "budget", usecols=["user_id", "category_code"])
    assert set(budgets["user_id"]) <= users
    assert set(budgets["category_code"]) <= categories
    rec = _csv(mini_dataset, "recurring_series", usecols=["user_id", "account_id"])
    assert set(rec["user_id"]) <= users
    assert set(rec["account_id"]) <= accounts
    insights = _csv(mini_dataset, "insight", usecols=["user_id"])
    assert set(insights["user_id"]) <= users
    links = _csv(mini_dataset, "transfer_link", usecols=["debit_txn_id", "credit_txn_id"])
    txn_ids = set(txns["transaction_id"])
    assert set(links["debit_txn_id"]) <= txn_ids
    assert set(links["credit_txn_id"]) <= txn_ids


def test_transaction_dates_within_year(mini_dataset: Path):
    dates = pd.to_datetime(_csv(mini_dataset, "transaction", usecols=["transaction_date"])["transaction_date"])
    assert (dates.dt.year == 2026).all()
    budgets = _csv(mini_dataset, "budget", usecols=["period_start", "period_end"])
    starts = pd.to_datetime(budgets["period_start"])
    ends = pd.to_datetime(budgets["period_end"])
    assert (starts.dt.year == 2026).all()
    assert (ends >= starts).all()


def test_signed_amounts_and_treatment_enums(mini_dataset: Path):
    txns = _csv(mini_dataset, "transaction", usecols=["amount_usd"])
    assert (txns["amount_usd"] < 0).any(), "expected negative expense amounts"
    assert (txns["amount_usd"] > 0).any(), "expected positive income/refund amounts"
    out = mini_dataset / "outputs" / "categorized_transactions.csv"
    treatments = set(pd.read_csv(out, usecols=["predicted_treatment"])["predicted_treatment"])
    assert treatments <= {"spend", "income", "transfer", "refund"}
    assert {"spend", "income"} <= treatments


def test_validation_passes(mini_dataset: Path):
    summary = run_validation(mini_dataset)
    assert summary["status"] == "PASS"
    assert summary["counts"]["fail"] == 0
    assert summary["counts"]["warn"] == 0
    assert summary["counts"]["pass"] >= 100


def test_all_five_edge_cases_labelled(mini_dataset: Path):
    manifest = pd.read_csv(mini_dataset / "ground_truth" / "anomaly_manifest.csv")
    issues = set(manifest["issue_type"])
    assert issues == REQUIRED_ISSUES, f"unexpected issue types: {issues}"
    for issue in REQUIRED_ISSUES:
        rows = manifest[manifest["issue_type"] == issue]
        assert len(rows) >= 1, f"{issue} has no labelled cases"
        assert (rows["impact_count"] >= 1).all(), f"{issue} impact_count must be >= 1"
        assert rows["expected_resolution"].str.len().gt(0).all(), f"{issue} missing expected resolution"


def test_ground_truth_isolated_from_pipeline_features(mini_dataset: Path):
    categorized = pd.read_csv(mini_dataset / "outputs" / "categorized_transactions.csv", nrows=0)
    leaked = set(categorized.columns) & GROUND_TRUTH_LEAK_COLUMNS
    assert not leaked, f"ground truth leaked into pipeline output: {leaked}"
    data_files = [p.name for p in (mini_dataset / "data").rglob("*") if p.is_file()]
    leaked_files = [n for n in data_files if "truth" in n.lower() or "label" in n.lower()]
    assert not leaked_files, f"ground truth files stored with pipeline data: {leaked_files}"
    labels = pd.read_csv(mini_dataset / "ground_truth" / "transaction_labels.csv")
    assert set(labels.columns) >= {"transaction_id", "true_category_code", "issue_type"}


def test_budget_values_derived_from_sources(mini_dataset: Path):
    cmp = pd.read_csv(mini_dataset / "outputs" / "budget_comparison.csv")
    assert set(cmp["status"]) <= {"under", "near", "over"}
    recomputed = cmp["budget_amount_usd"] - cmp["actual_spend_usd"]
    assert (recomputed - cmp["variance_usd"]).abs().max() <= 0.01
    positive = cmp["budget_amount_usd"] > 0
    usage = cmp.loc[positive, "actual_spend_usd"] / cmp.loc[positive, "budget_amount_usd"] * 100
    assert (usage - cmp.loc[positive, "usage_pct"]).abs().max() <= 0.1
    assert (cmp["stored_category_code"] != cmp["resolved_category_code"]).any(), "alias resolution path not exercised"


def test_recurring_labels_and_detector_output_present(mini_dataset: Path):
    labels = pd.read_csv(mini_dataset / "ground_truth" / "recurring_series_labels.csv")
    detected = pd.read_csv(mini_dataset / "outputs" / "recurring_series.csv")
    assert len(labels) >= 1
    assert len(detected) >= 1
    assert detected["series_id"].str.fullmatch(r"REC-\d{6}").all()
    assert detected["series_id"].is_unique


def test_evaluation_metrics_are_computable(mini_dataset: Path):
    report = run_evaluation(mini_dataset)
    sections = report["sections"]
    assert report["validation_status"] == "PASS"
    accuracy = sections["categorization"]["accuracy"]
    assert 0.9 <= accuracy <= 1.0
    assert sections["treatment"]["accuracy"] >= 0.95
    f1 = sections["recurring_detection"]["f1"]
    assert 0.0 <= f1 <= 1.0
    assert sections["recurring_detection"]["skip_recall"] >= 0.99
    assert sections["exception_handling_score"] >= 0.99
    assert sections["budget_comparison"]["resolution_accuracy"] == 1.0
    assert (mini_dataset / "outputs" / "evaluation_report.json").exists()
    assert (mini_dataset / "outputs" / "evaluation_report.md").exists()


def test_determinism_same_seed_same_checksums(mini_dataset: Path, manifest: dict, tmp_path: Path):
    fresh = tmp_path / "fresh"
    generate_dataset(scale="mini", seed=SEED, out_dir=fresh, formats=("csv",))
    fresh_manifest = json.loads((fresh / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    comparison = _compare_manifests(manifest, fresh_manifest)
    assert comparison["status"] == "PASS", comparison["mismatches"][:5]
    assert comparison["files_matching"] == comparison["files_compared"] > 0
    assert not comparison["count_mismatches"]
