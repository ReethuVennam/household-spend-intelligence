from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    ACCOUNT_STATES,
    ACCOUNT_TYPES,
    BUDGET_STATES,
    CATEGORY_TYPES,
    CHANNELS,
    INSIGHT_TYPES,
    SERIES_STATES,
    TREATMENTS,
    TRANSACTION_STATES,
    USER_STATES,
)


def _read(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


def _ids(df: pd.DataFrame, col: str):
    return set(df[col].dropna().astype(str))


def _missing(parent: set[str], child: pd.Series) -> int:
    values = child.dropna().astype(str)
    values = values[values != ""]
    return int((~values.isin(parent)).sum())


def _check(checks: list[dict], name: str, passed: bool, expected=None, actual=None, note: str = "", severity: str = "FAIL") -> None:
    status = "PASS" if passed else severity
    item = {"check": name, "status": status, "note": note}
    if expected is not None:
        item["expected"] = expected
    if actual is not None:
        item["actual"] = actual
    checks.append(item)


def _table_checks(tables: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    pk_map = {
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
    for table, pk in pk_map.items():
        df = tables[table]
        dup = int(df[pk].duplicated().sum())
        _check(checks, f"{table}.{pk} unique", dup == 0, 0, dup)
        _check(checks, f"{table} not empty", len(df) > 0, ">0", len(df), severity="WARN")

    users = _ids(tables["user_profile"], "user_id")
    accounts = _ids(tables["account"], "account_id")
    merchants = _ids(tables["merchant"], "merchant_id")
    categories = _ids(tables["category"], "category_code")
    rules = _ids(tables["category_rule"], "rule_id")
    transactions = _ids(tables["transaction"], "transaction_id")
    budgets = _ids(tables["budget"], "budget_id")

    fk_checks = [
        ("account.user_id", users, tables["account"]["user_id"]),
        ("merchant.default_category_code", categories, tables["merchant"]["default_category_code"]),
        ("merchant_alias.merchant_id", merchants, tables["merchant_alias"]["merchant_id"]),
        ("category_alias.alias_code", categories, tables["category_alias"]["alias_code"]),
        ("category_alias.canonical_code", categories, tables["category_alias"]["canonical_code"]),
        ("category_rule.category_code", categories, tables["category_rule"]["category_code"]),
        ("category_rule.merchant_id", merchants, tables["category_rule"]["merchant_id"]),
        ("category.parent_code", categories, tables["category"]["parent_code"]),
        ("budget.user_id", users, tables["budget"]["user_id"]),
        ("budget.category_code", categories, tables["budget"]["category_code"]),
        ("transaction.user_id", users, tables["transaction"]["user_id"]),
        ("transaction.account_id", accounts, tables["transaction"]["account_id"]),
        ("transaction.merchant_id", merchants, tables["transaction"]["merchant_id"]),
        ("transaction.refund_of_txn_id", transactions, tables["transaction"]["refund_of_txn_id"]),
        ("transfer_link.debit_txn_id", transactions, tables["transfer_link"]["debit_txn_id"]),
        ("transfer_link.credit_txn_id", transactions, tables["transfer_link"]["credit_txn_id"]),
        ("recurring_series.user_id", users, tables["recurring_series"]["user_id"]),
        ("recurring_series.account_id", accounts, tables["recurring_series"]["account_id"]),
        ("recurring_series.merchant_id", merchants, tables["recurring_series"]["merchant_id"]),
        ("recurring_series.category_code", categories, tables["recurring_series"]["category_code"]),
        ("insight.user_id", users, tables["insight"]["user_id"]),
    ]
    for name, parent, child in fk_checks:
        missing = _missing(parent, child)
        _check(checks, f"FK {name}", missing == 0, 0, missing)

    decision_path = None
    _ = categories, rules, budgets

    user_pattern = re.compile(r"^USR-\d{6}$")
    account_pattern = re.compile(r"^ACC-USR-\d{6}-\d{2}$")
    txn_pattern = re.compile(r"^TXN-2026-\d{8}$")
    budget_pattern = re.compile(r"^BUD-USR-\d{6}-2026-\d{2}-[A-Z_]+$")
    series_pattern = re.compile(r"^REC-\d{6}$")
    _check(checks, "user_id nomenclature", bool(tables["user_profile"]["user_id"].map(lambda x: bool(user_pattern.match(str(x)))).all()), "USR-000001", "checked all users")
    account_ok = tables["account"].apply(lambda r: bool(account_pattern.match(str(r.account_id))) and str(r.account_id).startswith(f"ACC-{r.user_id}-"), axis=1).all()
    _check(checks, "account_id nomenclature", bool(account_ok), "ACC-<user-id>-01", "checked all accounts")
    txn_ok = bool(tables["transaction"]["transaction_id"].map(lambda x: bool(txn_pattern.match(str(x)))).all())
    _check(checks, "transaction_id nomenclature", txn_ok, "TXN-2026-00000001", "checked all transactions")
    budget_ok = bool(tables["budget"]["budget_id"].map(lambda x: bool(budget_pattern.match(str(x)))).all())
    _check(checks, "budget_id nomenclature", budget_ok, "BUD-<user-id>-2026-01-<category>", "checked all budgets")
    series_ok = bool(tables["recurring_series"]["series_id"].map(lambda x: bool(series_pattern.match(str(x)))).all())
    _check(checks, "series_id nomenclature", series_ok, "REC-000001", "checked detected series")

    suffixes = tables["transaction"]["transaction_id"].str.extract(r"TXN-2026-(\d{8})")[0].astype(int).to_numpy()
    expected_suffix = np.arange(1, len(suffixes) + 1)
    _check(checks, "transaction_id sequence", bool(np.array_equal(np.sort(suffixes), expected_suffix)), "1..N contiguous", int(suffixes.max()) if len(suffixes) else 0)

    txn_cols = set(tables["transaction"].columns)
    leakage = sorted([c for c in txn_cols if any(token in c.lower() for token in ["true_", "ground", "issue", "label"])])
    _check(checks, "no ground truth columns in transaction input", len(leakage) == 0, [], leakage)


def _enum_checks(tables: dict[str, pd.DataFrame], gt: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    checks_to_do = [
        ("user_profile.lifecycle_state", tables["user_profile"]["lifecycle_state"], set(USER_STATES)),
        ("user_profile.risk_tier", tables["user_profile"]["risk_tier"], {"low", "medium", "high"}),
        ("user_profile.segment", tables["user_profile"]["segment"], {"standard", "plus", "premium"}),
        ("account.account_type", tables["account"]["account_type"], set(ACCOUNT_TYPES)),
        ("account.status", tables["account"]["status"], set(ACCOUNT_STATES)),
        ("merchant.status", tables["merchant"]["status"], {"active", "inactive"}),
        ("category.type", tables["category"]["type"], set(CATEGORY_TYPES)),
        ("category_rule.match_type", tables["category_rule"]["match_type"], {"exact", "contains", "regex"}),
        ("category_rule.match_field", tables["category_rule"]["match_field"], {"descriptor", "mcc", "merchant"}),
        ("category_rule.status", tables["category_rule"]["status"], {"active", "retired"}),
        ("budget.status", tables["budget"]["status"], set(BUDGET_STATES)),
        ("transaction.channel", tables["transaction"]["channel"], set(CHANNELS)),
        ("transaction.status", tables["transaction"]["status"], set(TRANSACTION_STATES)),
        ("recurring_series.status", tables["recurring_series"]["status"], set(SERIES_STATES)),
        ("recurring_series.cadence", tables["recurring_series"]["cadence"], {"weekly", "biweekly", "monthly", "quarterly", "annual"}),
        ("insight.insight_type", tables["insight"]["insight_type"], set(INSIGHT_TYPES)),
        ("ground_truth.true_treatment", gt["transaction_labels"]["true_treatment"], set(TREATMENTS)),
    ]
    for name, series, allowed in checks_to_do:
        bad = int((~series.dropna().astype(str).isin(allowed)).sum())
        _check(checks, f"enum {name}", bad == 0, sorted(allowed), bad)


def _date_checks(tables: dict[str, pd.DataFrame], gt: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    users = tables["user_profile"].copy()
    accounts = tables["account"].copy()
    txns = tables["transaction"].copy()
    budgets = tables["budget"].copy()
    series = tables["recurring_series"].copy()
    links = tables["transfer_link"].copy()

    users["created_ts"] = pd.to_datetime(users["created_at"], utc=True, errors="coerce")
    accounts["opened_ts"] = pd.to_datetime(accounts["opened_at"], utc=True, errors="coerce")
    accounts["closed_ts"] = pd.to_datetime(accounts["closed_at"], utc=True, errors="coerce")
    txns["posted_ts"] = pd.to_datetime(txns["posted_at_utc"], utc=True, errors="coerce")
    txns["local_date"] = pd.to_datetime(txns["transaction_date"], errors="coerce")
    merged = accounts.merge(users[["user_id", "created_ts"]], on="user_id", how="left")
    bad = int((merged["opened_ts"] < merged["created_ts"]).sum())
    _check(checks, "account opened after user creation", bad == 0, 0, bad)

    merged_tx = txns.merge(accounts[["account_id", "opened_ts", "closed_ts"]], on="account_id", how="left")
    bad_open = int((merged_tx["posted_ts"] < merged_tx["opened_ts"]).sum())
    _check(checks, "transaction posted after account open", bad_open == 0, 0, bad_open)
    closed = merged_tx["closed_ts"].notna()
    bad_closed = int((merged_tx.loc[closed, "posted_ts"] > merged_tx.loc[closed, "closed_ts"]).sum())
    _check(checks, "transaction posted before account close", bad_closed == 0, 0, bad_closed)

    local_cap = users[["user_id", "lifecycle_state"]].copy()
    local_cap["cap"] = np.where(local_cap["lifecycle_state"] == "closed", "2026-09-30", np.where(local_cap["lifecycle_state"] == "dormant", "2026-08-31", "2026-12-31"))
    cap_map = dict(zip(local_cap["user_id"], local_cap["cap"]))
    txns["cap"] = txns["user_id"].map(cap_map)
    late_lifecycle = int((txns["transaction_date"].astype(str) > txns["cap"]).sum())
    _check(checks, "no activity after dormant/closed cutoff", late_lifecycle == 0, 0, late_lifecycle)

    refunds = txns[txns["refund_of_txn_id"].notna()][["transaction_id", "refund_of_txn_id", "transaction_date", "amount_usd"]]
    originals = txns[["transaction_id", "transaction_date", "amount_usd"]].rename(columns={"transaction_id": "refund_of_txn_id", "transaction_date": "original_date", "amount_usd": "original_amount"})
    ref = refunds.merge(originals, on="refund_of_txn_id", how="left")
    bad_refund_date = int((ref["transaction_date"] < ref["original_date"]).sum())
    bad_refund_amount = int(((ref["amount_usd"] <= 0) | (ref["amount_usd"] > ref["original_amount"].abs() + 0.011) | (ref["original_amount"] >= 0)).sum())
    _check(checks, "refund date not before original", bad_refund_date == 0, 0, bad_refund_date)
    _check(checks, "refund positive and bounded by original", bad_refund_amount == 0, 0, bad_refund_amount)

    pair = links.merge(txns[["transaction_id", "transaction_date", "amount_usd"]], left_on="debit_txn_id", right_on="transaction_id", how="left").rename(columns={"transaction_date": "debit_date", "amount_usd": "debit_amount"})
    pair = pair.merge(txns[["transaction_id", "transaction_date", "amount_usd"]], left_on="credit_txn_id", right_on="transaction_id", how="left").rename(columns={"transaction_date": "credit_date", "amount_usd": "credit_amount"})
    pair["net"] = (pair["debit_amount"] + pair["credit_amount"]).round(2)
    bad_pair = int(((pair["net"].abs() > 0.011) | (pair["debit_date"] != pair["credit_date"])).sum())
    _check(checks, "transfer pairs same date and net zero", bad_pair == 0, 0, bad_pair)

    period_bad = int((budgets["period_start"].str[:7] != (budgets["year"].astype(str) + "-" + budgets["month"].astype(str).str.zfill(2))).sum())
    _check(checks, "budget period aligns with year/month", period_bad == 0, 0, period_bad)
    budget_order = int((budgets["period_start"] > budgets["period_end"]).sum())
    _check(checks, "budget start before end", budget_order == 0, 0, budget_order)

    series_bad = int((series["first_occurrence"] > series["last_occurrence"]).sum())
    _check(checks, "recurring first occurrence before last", series_bad == 0, 0, series_bad)
    series_next_bad = int(((series["status"] == "active") & (series["next_expected_date"].fillna("") == "")).sum())
    _check(checks, "active recurring series has next date", series_next_bad == 0, 0, series_next_bad)

    labels = gt["transaction_labels"]
    label_period = txns[["transaction_id", "transaction_date"]].merge(labels[["transaction_id", "expected_period"]], on="transaction_id", how="inner")
    expected_bad = int((label_period["transaction_date"].str[:7] != label_period["expected_period"]).sum())
    _check(checks, "ground-truth period uses local date", expected_bad == 0, 0, expected_bad)

    labels["is_recurring_int"] = labels["is_recurring"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    recurring_series = gt["recurring_series_labels"]
    posted = labels[labels["is_recurring_int"] == 1].groupby("true_series_id").size().rename("actual_posted")
    expected_posted = recurring_series.set_index("true_series_id")["posted_occurrences"]
    joined = pd.concat([posted, expected_posted], axis=1).fillna(0)
    bad_posted = int((joined["actual_posted"] != joined["posted_occurrences"]).sum())
    _check(checks, "recurring posted counts reconcile", bad_posted == 0, 0, bad_posted)


def _anomaly_checks(tables: dict[str, pd.DataFrame], gt: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    labels = gt["transaction_labels"]
    manifest = gt["anomaly_manifest"]
    budget_labels = gt["budget_labels"]
    series_labels = gt["recurring_series_labels"]
    expectations = gt["recurring_expectations"]

    required = {
        "transfer_double_count",
        "refund_treated_as_new_expense",
        "recurring_series_skip",
        "timezone_boundary_date",
        "budget_taxonomy_mismatch",
    }
    present = set(manifest["issue_type"].dropna().astype(str))
    missing = sorted(required - present)
    _check(checks, "all required edge-case types present", not missing, sorted(required), missing)

    def match_transaction_issue(issue: str) -> tuple[bool, int, int]:
        label_ids = set(labels.loc[labels["issue_type"].fillna("") == issue, "transaction_id"])
        manifest_ids = set(manifest.loc[(manifest["issue_type"] == issue) & (manifest["entity_type"] == "transaction"), "entity_id"])
        return label_ids == manifest_ids, len(label_ids), len(manifest_ids)

    for issue in ["transfer_double_count", "refund_treated_as_new_expense", "timezone_boundary_date"]:
        ok, label_count, manifest_count = match_transaction_issue(issue)
        _check(checks, f"{issue} labels match manifest", ok, label_count, manifest_count)

    tz_mismatch = tables["transaction"].assign(local_month=tables["transaction"]["transaction_date"].str[:7], utc_month=tables["transaction"]["posted_at_utc"].str[:7])
    tz_count = int((tz_mismatch["local_month"] != tz_mismatch["utc_month"]).sum())
    boundary = tz_mismatch[tz_mismatch["local_month"] != tz_mismatch["utc_month"]].merge(
        labels[["transaction_id", "issue_type"]], on="transaction_id", how="left"
    )
    unlabelled_boundary = int(boundary["issue_type"].fillna("").eq("").sum())
    _check(checks, "every UTC/local month boundary case is labelled", unlabelled_boundary == 0, 0, unlabelled_boundary, f"{tz_count} boundary rows; {int(not unlabelled_boundary)} unlabelled.")
    tz_labels = int(labels["issue_type"].fillna("").eq("timezone_boundary_date").sum())
    _check(checks, "timezone anomaly labels match manifest", tz_labels == int(manifest.loc[manifest["issue_type"] == "timezone_boundary_date", "impact_count"].sum()), int(manifest.loc[manifest["issue_type"] == "timezone_boundary_date", "impact_count"].sum()), tz_labels)

    skip_series = set(series_labels.loc[series_labels["issue_type"].fillna("") == "recurring_series_skip", "true_series_id"])
    skip_manifest = set(manifest.loc[manifest["issue_type"] == "recurring_series_skip", "entity_id"])
    _check(checks, "recurring skip series labels match manifest", skip_series == skip_manifest, len(skip_series), len(skip_manifest))
    skipped_expectations = int(expectations["outcome"].eq("skipped").sum())
    skipped_gt = int(series_labels["skipped_occurrences"].sum())
    _check(checks, "recurring skip expectations reconcile", skipped_expectations == skipped_gt, skipped_gt, skipped_expectations)

    budget_mismatch = int(budget_labels["issue_type"].fillna("").eq("budget_taxonomy_mismatch").sum())
    budget_manifest = manifest.loc[manifest["issue_type"] == "budget_taxonomy_mismatch", "impact_count"].sum()
    _check(checks, "budget mismatch labels match manifest impact", budget_mismatch == int(budget_manifest), int(budget_manifest), budget_mismatch)

    inactive_budget = tables["budget"].merge(tables["category"][["category_code", "is_active"]], on="category_code", how="left")
    inactive_count = int((~inactive_budget["is_active"].astype(bool)).sum())
    _check(checks, "inactive budget categories are fully labelled", inactive_count == budget_mismatch, budget_mismatch, inactive_count, "Intentional taxonomy mismatch cases are labelled in budget_labels.csv.")

    transfer_labels = int(labels["true_treatment"].eq("transfer").sum())
    transfer_categories = int(labels["true_category_code"].eq("TRANSFER").sum())
    _check(checks, "transfer treatment/category consistent", transfer_labels == transfer_categories, transfer_categories, transfer_labels)
    refund_labels = labels[labels["true_treatment"] == "refund"]
    refund_amounts = tables["transaction"].set_index("transaction_id").loc[refund_labels["transaction_id"], "amount_usd"]
    bad_refund_sign = int((refund_amounts <= 0).sum())
    _check(checks, "refund ground truth has positive amounts", bad_refund_sign == 0, 0, bad_refund_sign)


def _relationship_checks(tables: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    txns = tables["transaction"]
    accounts = tables["account"][["account_id", "user_id"]]
    merged = txns.merge(accounts, on="account_id", how="left", suffixes=("", "_account"))
    mismatch = int((merged["user_id"].astype(str) != merged["user_id_account"].astype(str)).sum())
    _check(checks, "transaction user matches account owner", mismatch == 0, 0, mismatch)

    refunds = txns[txns["refund_of_txn_id"].notna()][["transaction_id", "refund_of_txn_id", "user_id", "account_id"]]
    original = txns[["transaction_id", "user_id", "account_id"]].rename(columns={"transaction_id": "refund_of_txn_id", "user_id": "original_user", "account_id": "original_account"})
    ref = refunds.merge(original, on="refund_of_txn_id", how="left")
    bad_user = int((ref["user_id"].astype(str) != ref["original_user"].astype(str)).sum())
    bad_account = int((ref["account_id"].astype(str) != ref["original_account"].astype(str)).sum())
    _check(checks, "refund owner matches original", bad_user == 0, 0, bad_user)
    _check(checks, "refund account matches original", bad_account == 0, 0, bad_account)

    links = tables["transfer_link"][["link_id", "debit_txn_id", "credit_txn_id"]]
    pair = links.merge(txns[["transaction_id", "user_id", "account_id"]], left_on="debit_txn_id", right_on="transaction_id", how="left").rename(columns={"user_id": "debit_user", "account_id": "debit_account"})
    pair = pair.merge(txns[["transaction_id", "user_id", "account_id"]], left_on="credit_txn_id", right_on="transaction_id", how="left").rename(columns={"user_id": "credit_user", "account_id": "credit_account"})
    bad_pair_owner = int((pair["debit_user"].astype(str) != pair["credit_user"].astype(str)).sum())
    same_account = int((pair["debit_account"].astype(str) == pair["credit_account"].astype(str)).sum())
    _check(checks, "transfer legs have same owner", bad_pair_owner == 0, 0, bad_pair_owner)
    _check(checks, "transfer legs use different accounts", same_account == 0, 0, same_account)

    series = tables["recurring_series"].merge(accounts, on="account_id", how="left", suffixes=("", "_account"))
    bad_series = int((series["user_id"].astype(str) != series["user_id_account"].astype(str)).sum())
    _check(checks, "recurring series owner matches account", bad_series == 0, 0, bad_series)


def _event_checks(tables: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    events = tables["entity_event"].copy()
    events["event_ts"] = pd.to_datetime(events["event_at"], utc=True, errors="coerce")
    users = tables["user_profile"][["user_id", "lifecycle_state", "created_at"]].copy()
    accounts = tables["account"][["account_id", "status", "opened_at"]].copy()
    users["created_ts"] = pd.to_datetime(users["created_at"], utc=True, errors="coerce")
    accounts["opened_ts"] = pd.to_datetime(accounts["opened_at"], utc=True, errors="coerce")
    user_ids = set(users["user_id"])
    account_ids = set(accounts["account_id"])
    user_events = events[events["entity_type"] == "user_profile"]
    account_events = events[events["entity_type"] == "account"]
    _check(checks, "event user references valid", int((~user_events["entity_id"].astype(str).isin(user_ids)).sum()) == 0, 0, int((~user_events["entity_id"].astype(str).isin(user_ids)).sum()))
    _check(checks, "event account references valid", int((~account_events["entity_id"].astype(str).isin(account_ids)).sum()) == 0, 0, int((~account_events["entity_id"].astype(str).isin(account_ids)).sum()))
    user_state = dict(zip(users["user_id"], users["lifecycle_state"]))
    account_state = dict(zip(accounts["account_id"], accounts["status"]))
    created_ts = dict(zip(users["user_id"], users["created_ts"]))
    opened_ts = dict(zip(accounts["account_id"], accounts["opened_ts"]))
    transition_bad = 0
    order_bad = 0
    terminal_bad = 0
    for entity_id, group in user_events.groupby("entity_id", sort=False):
        group = group.sort_values(["event_ts", "event_id"], kind="mergesort")
        if len(group) == 0 or group.iloc[0]["event_type"] != "CREATED":
            transition_bad += 1
            continue
        state = "active"
        last_ts = created_ts.get(entity_id)
        for pos, row in enumerate(group.itertuples(index=False)):
            if last_ts is not None and row.event_ts < last_ts:
                order_bad += 1
            last_ts = row.event_ts
            if row.event_type == "CREATED":
                if row.to_state != "active":
                    transition_bad += 1
                state = row.to_state
            elif row.event_type == "DORMANT":
                if state != "active" or row.to_state != "dormant":
                    transition_bad += 1
                state = "dormant"
            elif row.event_type == "CLOSED":
                if state != "active" or row.to_state != "closed":
                    transition_bad += 1
                state = "closed"
            else:
                transition_bad += 1
            if state == "closed" and pos != len(group) - 1:
                terminal_bad += 1
        if state != user_state.get(entity_id):
            terminal_bad += 1
    for entity_id, group in account_events.groupby("entity_id", sort=False):
        group = group.sort_values(["event_ts", "event_id"], kind="mergesort")
        if len(group) == 0 or group.iloc[0]["event_type"] != "OPENED":
            transition_bad += 1
            continue
        state = "active"
        last_ts = opened_ts.get(entity_id)
        for pos, row in enumerate(group.itertuples(index=False)):
            if last_ts is not None and row.event_ts < last_ts:
                order_bad += 1
            last_ts = row.event_ts
            if row.event_type == "OPENED":
                if row.to_state != "active":
                    transition_bad += 1
                state = row.to_state
            elif row.event_type == "CLOSED":
                if state != "active" or row.to_state != "closed":
                    transition_bad += 1
                state = "closed"
            else:
                transition_bad += 1
            if state == "closed" and pos != len(group) - 1:
                terminal_bad += 1
        if state != account_state.get(entity_id):
            terminal_bad += 1
    _check(checks, "lifecycle transition states valid", transition_bad == 0, 0, transition_bad)
    _check(checks, "lifecycle event ordering valid", order_bad == 0, 0, order_bad)
    _check(checks, "lifecycle terminal states match entities", terminal_bad == 0, 0, terminal_bad)
    duplicate_events = int(events.duplicated(["entity_type", "entity_id", "event_type"]).sum())
    _check(checks, "no duplicate lifecycle event types per entity", duplicate_events == 0, 0, duplicate_events)


def _ledger_checks(tables: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    txns = tables["transaction"]
    accounts = tables["account"]
    posted = txns[txns["status"] == "posted"]
    balances = posted.groupby("account_id", sort=False)["amount_usd"].sum().round(2)
    expected = accounts.set_index("account_id")["current_balance_usd"].round(2)
    joined = pd.concat([balances, expected], axis=1).fillna(0.0)
    joined.columns = ["ledger", "stored"]
    diff = (joined["ledger"] - joined["stored"]).abs()
    bad = int((diff > 0.011).sum())
    _check(checks, "account balances reconcile to ledger", bad == 0, 0, bad)
    ledger_total = round(float(posted["amount_usd"].sum()), 2)
    stored_total = round(float(accounts["current_balance_usd"].sum()), 2)
    _check(checks, "ledger total equals sum of account balances", abs(ledger_total - stored_total) <= 0.011, stored_total, ledger_total)
    _check(checks, "transaction amounts nonzero", int((txns["amount_usd"] == 0).sum()) == 0, 0, int((txns["amount_usd"] == 0).sum()))
    _check(checks, "posted transaction share", float((txns["status"] == "posted").mean()) >= 0.99, ">=99%", round(float((txns["status"] == "posted").mean()), 4), severity="WARN")


def _output_checks(dataset_dir: Path, tables: dict[str, pd.DataFrame], gt: dict[str, pd.DataFrame], checks: list[dict]) -> None:
    out = dataset_dir / "outputs"
    decisions = _read(out / "categorization_decisions.csv")
    categorized = _read(out / "categorized_transactions.csv")
    monthly = _read(out / "monthly_spend.csv")
    budget_compare = _read(out / "budget_comparison.csv")
    recurring = _read(out / "recurring_series.csv")
    insights = _read(out / "insights.csv") if (out / "insights.csv").exists() else tables["insight"]

    txns = tables["transaction"]
    _check(checks, "decision coverage equals transactions", len(decisions) == len(txns), len(txns), len(decisions))
    _check(checks, "categorized coverage equals transactions", len(categorized) == len(txns), len(txns), len(categorized))
    _check(checks, "decision transaction uniqueness", decisions["transaction_id"].duplicated().sum() == 0, 0, int(decisions["transaction_id"].duplicated().sum()))
    missing_decisions = len(set(txns["transaction_id"]) - set(decisions["transaction_id"]))
    _check(checks, "every transaction has a decision", missing_decisions == 0, 0, missing_decisions)

    categories = _ids(tables["category"], "category_code")
    bad_cat = _missing(categories, decisions["category_code"])
    _check(checks, "decision categories valid", bad_cat == 0, 0, bad_cat)
    conf_bad = int(((decisions["confidence"] < 0) | (decisions["confidence"] > 1)).sum())
    _check(checks, "decision confidence in [0,1]", conf_bad == 0, 0, conf_bad)
    treat_bad = int((~decisions["predicted_treatment"].isin(["spend", "income", "transfer", "refund"])).sum())
    _check(checks, "predicted treatments valid", treat_bad == 0, 0, treat_bad)

    recalc = categorized.copy()
    recalc["period_month"] = recalc["transaction_date"].str[:7]
    recalc["income_amount"] = np.where(recalc["predicted_treatment"] == "income", recalc["amount_usd"], 0.0)
    recalc_month = (
        recalc.groupby(["user_id", "period_month"], sort=False)
        .agg(
            spend_usd=("spend_amount_usd", "sum"),
            income_usd=("income_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            refund_count=("predicted_treatment", lambda s: int((s == "refund").sum())),
            transfer_count=("predicted_treatment", lambda s: int((s == "transfer").sum())),
        )
        .reset_index()
    )
    merged = monthly.merge(recalc_month, on=["user_id", "period_month"], how="outer", suffixes=("_out", "_calc"), indicator=True)
    mismatch = int((merged["_merge"] != "both").sum())
    numeric_bad = 0
    for col in ["spend_usd", "income_usd", "transaction_count", "refund_count", "transfer_count"]:
        numeric_bad += int((merged[f"{col}_out"].fillna(0) - merged[f"{col}_calc"].fillna(0)).abs().gt(0.011).sum())
    _check(checks, "monthly spend reconciles to categorized ledger", mismatch == 0 and numeric_bad == 0, 0, mismatch + numeric_bad)

    budget_missing = len(set(tables["budget"]["budget_id"]) - set(budget_compare["budget_id"]))
    _check(checks, "every budget has comparison row", budget_missing == 0, 0, budget_missing)
    bc = budget_compare.merge(tables["budget"][["budget_id", "budget_amount_usd"]], on="budget_id", suffixes=("_out", "_src"), how="left")
    amount_bad = int((bc["budget_amount_usd_out"] - bc["budget_amount_usd_src"]).abs().gt(0.011).sum())
    _check(checks, "budget comparison amounts reconcile", amount_bad == 0, 0, amount_bad)
    status_bad = int((~budget_compare["status"].isin(["under", "near", "over"])).sum())
    _check(checks, "budget comparison statuses valid", status_bad == 0, 0, status_bad)
    resolved_active = budget_compare.merge(tables["category"][["category_code", "is_active"]], left_on="resolved_category_code", right_on="category_code", how="left")
    unresolved_active = int((~resolved_active["is_active"].fillna(False).astype(bool)).sum())
    _check(checks, "resolved budget categories are active", unresolved_active == 0, 0, unresolved_active)

    actual = categorized.copy()
    actual["period_month"] = actual["transaction_date"].str[:7]
    actual = actual[actual["predicted_treatment"].isin(["spend", "refund"])]
    actual_groups = (
        actual.groupby(["user_id", "period_month", "offset_category_code"], sort=False)["spend_amount_usd"]
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={"offset_category_code": "resolved_category_code", "spend_amount_usd": "actual_calc"})
    )
    joined = budget_compare.merge(actual_groups, on=["user_id", "period_month", "resolved_category_code"], how="left")
    actual_bad = int((joined["actual_spend_usd"].fillna(0) - joined["actual_calc"].fillna(0)).abs().gt(0.011).sum())
    _check(checks, "budget actuals reconcile to ledger", actual_bad == 0, 0, actual_bad)

    insight_bad = 0
    net = monthly.set_index(["user_id", "period_month"])["spend_usd"]
    for row in insights.itertuples(index=False):
        details = json.loads(row.details_json)
        key = (row.user_id, row.period_month)
        if row.insight_type == "monthly_spend_summary" and row.metric_name == "net_spend_usd":
            if abs(float(row.metric_value) - float(net.get(key, 0.0))) > 0.011:
                insight_bad += 1
        if row.insight_type == "budget_variance_summary":
            expected_value = float(details.get("budget_total_usd", 0.0)) - float(details.get("actual_budgeted_spend_usd", 0.0))
            if abs(float(row.metric_value) - expected_value) > 0.011:
                insight_bad += 1
    _check(checks, "insight metrics reconcile to outputs", insight_bad == 0, 0, insight_bad)

    rec_count = recurring.groupby("user_id").size()
    recurring_insight_bad = 0
    for row in insights.itertuples(index=False):
        if row.insight_type == "recurring_summary":
            if int(row.metric_value) != int(rec_count.get(row.user_id, 0)):
                recurring_insight_bad += 1
    _check(checks, "recurring insights reconcile to detected series", recurring_insight_bad == 0, 0, recurring_insight_bad)


def _manifest_checks(dataset_dir: Path, checks: list[dict]) -> None:
    import hashlib

    manifest = json.loads((dataset_dir / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    _check(checks, "manifest seed present", isinstance(manifest.get("seed"), int), "int", type(manifest.get("seed")).__name__)
    _check(checks, "manifest row count for transactions", manifest["counts"]["transactions"] == manifest["transactions"], manifest["transactions"], manifest["counts"]["transactions"])
    hash_bad = 0
    checked = 0
    for rel, info in manifest["files"].items():
        if not rel.endswith((".csv", ".json", ".gz", ".sql", ".md")):
            continue
        path = dataset_dir / rel
        if not path.exists():
            hash_bad += 1
            continue
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        checked += 1
        if h.hexdigest() != info["sha256"]:
            hash_bad += 1
    _check(checks, "manifest checksums verify", hash_bad == 0, 0, hash_bad, f"verified {checked} files")


def _summary_markdown(summary: dict) -> str:
    lines = [
        "# Validation Summary",
        "",
        f"Overall status: **{summary['status']}**",
        "",
        f"- Dataset: `{summary['dataset']}`",
        f"- Seed: `{summary['seed']}`",
        f"- Scale: `{summary['scale']}`",
        f"- Checks: {summary['counts']['pass']} pass, {summary['counts']['warn']} warn, {summary['counts']['fail']} fail",
        "",
        "| Check | Status | Expected | Actual | Note |",
        "|---|---|---|---|---|",
    ]
    for item in summary["checks"]:
        lines.append(
            f"| {item['check']} | {item['status']} | {item.get('expected', '')} | {item.get('actual', '')} | {item.get('note', '')} |"
        )
    lines.append("")
    lines.append("## Known labelled exceptions")
    lines.append("")
    lines.append("| Issue type | Rows / impact |")
    lines.append("|---|---:|")
    for key, value in summary["known_exceptions"].items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    return "\n".join(lines)


def run_validation(dataset_dir: str | Path = "dataset") -> dict:
    root = Path(dataset_dir)
    manifest = json.loads((root / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    tables = {
        "user_profile": _read(root / "data" / "user_profile.csv"),
        "account": _read(root / "data" / "account.csv"),
        "merchant": _read(root / "data" / "merchant.csv"),
        "merchant_alias": _read(root / "data" / "merchant_alias.csv"),
        "category": _read(root / "data" / "category.csv"),
        "category_alias": _read(root / "data" / "category_alias.csv"),
        "category_rule": _read(root / "data" / "category_rule.csv"),
        "budget": _read(root / "data" / "budget.csv"),
        "transaction": _read(root / "data" / "transaction.csv"),
        "transfer_link": _read(root / "data" / "transfer_link.csv"),
        "recurring_series": _read(root / "data" / "recurring_series.csv"),
        "insight": _read(root / "data" / "insight.csv"),
        "entity_event": _read(root / "data" / "entity_event.csv"),
    }
    gt = {
        "transaction_labels": _read(root / "ground_truth" / "transaction_labels.csv"),
        "recurring_series_labels": _read(root / "ground_truth" / "recurring_series_labels.csv"),
        "recurring_expectations": _read(root / "ground_truth" / "recurring_expectations.csv"),
        "budget_labels": _read(root / "ground_truth" / "budget_labels.csv"),
        "anomaly_manifest": _read(root / "ground_truth" / "anomaly_manifest.csv"),
    }
    checks: list[dict] = []
    _table_checks(tables, checks)
    _enum_checks(tables, gt, checks)
    _date_checks(tables, gt, checks)
    _anomaly_checks(tables, gt, checks)
    _relationship_checks(tables, checks)
    _event_checks(tables, checks)
    _ledger_checks(tables, checks)
    _output_checks(root, tables, gt, checks)
    _manifest_checks(root, checks)

    _check(checks, "row counts match manifest", len(tables["transaction"]) == manifest["counts"]["transactions"], manifest["counts"]["transactions"], len(tables["transaction"]))
    _check(checks, "ground truth covers every transaction", len(gt["transaction_labels"]) == len(tables["transaction"]), len(tables["transaction"]), len(gt["transaction_labels"]))
    gt_txn_missing = len(set(tables["transaction"]["transaction_id"]) - set(gt["transaction_labels"]["transaction_id"]))
    _check(checks, "ground truth IDs valid", gt_txn_missing == 0, 0, gt_txn_missing)
    gt_budget_missing = len(set(tables["budget"]["budget_id"]) - set(gt["budget_labels"]["budget_id"]))
    _check(checks, "ground truth covers every budget", gt_budget_missing == 0, 0, gt_budget_missing)
    labels = gt["transaction_labels"]
    _check(checks, "ground-truth categories valid", _missing(_ids(tables["category"], "category_code"), labels["true_category_code"]) == 0, 0, _missing(_ids(tables["category"], "category_code"), labels["true_category_code"]))
    _check(checks, "ground truth labels unique", labels["transaction_id"].duplicated().sum() == 0, 0, int(labels["transaction_id"].duplicated().sum()))

    duplicate_fp = int(tables["transaction"].duplicated(["user_id", "account_id", "transaction_date", "posted_at_utc", "amount_usd", "descriptor"]).sum())
    _check(checks, "no unintended exact duplicate transactions", duplicate_fp == 0, 0, duplicate_fp)

    _check(checks, "all 12 months covered", sorted(tables["transaction"]["transaction_date"].str[:7].unique().tolist()) == [f"2026-{m:02d}" for m in range(1, 13)], "12 months", len(tables["transaction"]["transaction_date"].str[:7].unique()))

    counts = {"pass": sum(c["status"] == "PASS" for c in checks), "warn": sum(c["status"] == "WARN" for c in checks), "fail": sum(c["status"] == "FAIL" for c in checks)}
    status = "FAIL" if counts["fail"] else ("PASS_WITH_WARNINGS" if counts["warn"] else "PASS")
    known = {}
    if len(gt["anomaly_manifest"]):
        known = {str(k): int(v) for k, v in gt["anomaly_manifest"].groupby("issue_type")["impact_count"].sum().sort_index().items()}
    summary = {
        "dataset": str(root),
        "seed": manifest["seed"],
        "scale": manifest["scale"],
        "generated_at": manifest["generated_at"],
        "status": status,
        "counts": counts,
        "known_exceptions": known,
        "row_counts": {name: int(len(df)) for name, df in tables.items()},
        "checks": checks,
    }
    val_dir = root / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)
    (val_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (val_dir / "validation_summary.md").write_text(_summary_markdown(summary), encoding="utf-8")
    return summary
