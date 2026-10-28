from __future__ import annotations

import gzip
import hashlib
import json
import platform
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .config import GENERATOR_VERSION, PROJECT_VERSION, SCHEMA_VERSION


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE category (
    category_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('expense','income','transfer','refund')),
    parent_code TEXT REFERENCES category(category_code),
    is_budgetable INTEGER NOT NULL CHECK (is_budgetable IN (0,1)),
    is_active INTEGER NOT NULL CHECK (is_active IN (0,1)),
    taxonomy_version TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT
);

CREATE TABLE user_profile (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    state_code TEXT NOT NULL,
    city TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    timezone TEXT NOT NULL,
    household_size INTEGER NOT NULL CHECK (household_size BETWEEN 1 AND 10),
    income_band TEXT NOT NULL,
    annual_income_usd REAL NOT NULL CHECK (annual_income_usd >= 0),
    credit_score INTEGER NOT NULL CHECK (credit_score BETWEEN 300 AND 850),
    risk_tier TEXT NOT NULL CHECK (risk_tier IN ('low','medium','high')),
    segment TEXT NOT NULL CHECK (segment IN ('standard','plus','premium')),
    lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('active','dormant','closed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_synthetic INTEGER NOT NULL CHECK (is_synthetic = 1),
    data_origin TEXT NOT NULL
);

CREATE TABLE account (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profile(user_id),
    account_type TEXT NOT NULL CHECK (account_type IN ('checking','savings','credit_card')),
    nickname TEXT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active','frozen','closed')),
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    opening_balance_usd REAL NOT NULL,
    current_balance_usd REAL NOT NULL,
    credit_limit_usd REAL,
    is_primary INTEGER NOT NULL CHECK (is_primary IN (0,1)),
    UNIQUE (user_id, account_type, opened_at)
);

CREATE TABLE merchant (
    merchant_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    default_category_code TEXT NOT NULL REFERENCES category(category_code),
    mcc TEXT,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    online_capable INTEGER NOT NULL CHECK (online_capable IN (0,1)),
    subscription_capable INTEGER NOT NULL CHECK (subscription_capable IN (0,1)),
    status TEXT NOT NULL CHECK (status IN ('active','inactive')),
    effective_from TEXT NOT NULL,
    effective_to TEXT
);

CREATE TABLE merchant_alias (
    alias_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchant(merchant_id),
    alias_text TEXT NOT NULL,
    is_primary INTEGER NOT NULL CHECK (is_primary IN (0,1)),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    UNIQUE (merchant_id, alias_text)
);

CREATE TABLE category_alias (
    alias_id TEXT PRIMARY KEY,
    alias_code TEXT NOT NULL REFERENCES category(category_code),
    canonical_code TEXT NOT NULL REFERENCES category(category_code),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL CHECK (status IN ('deprecated','merged','renamed')),
    reason TEXT NOT NULL,
    UNIQUE (alias_code, effective_from)
);

CREATE TABLE category_rule (
    rule_id TEXT PRIMARY KEY,
    category_code TEXT NOT NULL REFERENCES category(category_code),
    merchant_id TEXT REFERENCES merchant(merchant_id),
    match_field TEXT NOT NULL CHECK (match_field IN ('descriptor','mcc','merchant')),
    match_type TEXT NOT NULL CHECK (match_type IN ('exact','contains','regex')),
    pattern TEXT NOT NULL,
    priority INTEGER NOT NULL,
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL CHECK (status IN ('active','retired')),
    UNIQUE (category_code, merchant_id, pattern, effective_from)
);

CREATE TABLE budget (
    budget_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profile(user_id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    category_code TEXT NOT NULL REFERENCES category(category_code),
    budget_amount_usd REAL NOT NULL CHECK (budget_amount_usd > 0),
    currency TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft','active','closed')),
    version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (user_id, year, month, category_code, version)
);

CREATE TABLE "transaction" (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profile(user_id),
    account_id TEXT NOT NULL REFERENCES account(account_id),
    transaction_date TEXT NOT NULL,
    posted_at_utc TEXT NOT NULL,
    merchant_id TEXT REFERENCES merchant(merchant_id),
    descriptor TEXT NOT NULL,
    amount_usd REAL NOT NULL CHECK (amount_usd <> 0),
    currency TEXT NOT NULL,
    mcc TEXT,
    channel TEXT NOT NULL CHECK (channel IN ('card','ach','online','pos','atm','internal')),
    status TEXT NOT NULL CHECK (status IN ('posted','pending','reversed')),
    refund_of_txn_id TEXT REFERENCES "transaction"(transaction_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE transfer_link (
    link_id TEXT PRIMARY KEY,
    debit_txn_id TEXT NOT NULL REFERENCES "transaction"(transaction_id),
    credit_txn_id TEXT NOT NULL REFERENCES "transaction"(transaction_id),
    link_type TEXT NOT NULL,
    linked_amount_usd REAL NOT NULL CHECK (linked_amount_usd > 0),
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    UNIQUE (debit_txn_id),
    UNIQUE (credit_txn_id)
);

CREATE TABLE transaction_category_decision (
    decision_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES "transaction"(transaction_id),
    category_code TEXT NOT NULL REFERENCES category(category_code),
    rule_id TEXT REFERENCES category_rule(rule_id),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    decision_source TEXT NOT NULL,
    predicted_treatment TEXT NOT NULL CHECK (predicted_treatment IN ('spend','income','transfer','refund')),
    decided_at TEXT NOT NULL,
    model_version TEXT NOT NULL
);

CREATE TABLE recurring_series (
    series_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profile(user_id),
    account_id TEXT NOT NULL REFERENCES account(account_id),
    merchant_id TEXT NOT NULL REFERENCES merchant(merchant_id),
    category_code TEXT NOT NULL REFERENCES category(category_code),
    cadence TEXT NOT NULL CHECK (cadence IN ('weekly','biweekly','monthly','quarterly','annual')),
    expected_amount_usd REAL NOT NULL,
    first_occurrence TEXT NOT NULL,
    last_occurrence TEXT NOT NULL,
    occurrence_count INTEGER NOT NULL,
    missed_occurrences INTEGER NOT NULL,
    next_expected_date TEXT,
    status TEXT NOT NULL CHECK (status IN ('active','paused','cancelled','ended')),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    detection_method TEXT NOT NULL,
    detected_at TEXT NOT NULL
);

CREATE TABLE insight (
    insight_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profile(user_id),
    period_month TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    currency TEXT NOT NULL,
    details_json TEXT NOT NULL,
    source_txn_count INTEGER NOT NULL,
    formula_version TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE entity_event (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_at TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    reason TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX idx_account_user ON account(user_id);
CREATE INDEX idx_transaction_user_date ON "transaction"(user_id, transaction_date);
CREATE INDEX idx_transaction_account ON "transaction"(account_id);
CREATE INDEX idx_transaction_merchant ON "transaction"(merchant_id);
CREATE INDEX idx_transaction_refund ON "transaction"(refund_of_txn_id);
CREATE INDEX idx_budget_user_period ON budget(user_id, year, month);
CREATE INDEX idx_rule_category ON category_rule(category_code);
CREATE INDEX idx_insight_user_period ON insight(user_id, period_month);
CREATE INDEX idx_event_entity ON entity_event(entity_type, entity_id);
"""

GROUND_TRUTH_SCHEMA_SQL = """
CREATE TABLE transaction_labels (
    transaction_id TEXT PRIMARY KEY,
    true_category_code TEXT NOT NULL,
    true_treatment TEXT NOT NULL,
    expected_period TEXT NOT NULL,
    is_recurring INTEGER NOT NULL,
    true_series_id TEXT,
    issue_type TEXT,
    issue_detail TEXT,
    related_transaction_id TEXT
);

CREATE TABLE recurring_series_labels (
    true_series_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    merchant_key TEXT NOT NULL,
    category_code TEXT NOT NULL,
    cadence TEXT NOT NULL,
    expected_amount_usd REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    planned_occurrences INTEGER NOT NULL,
    posted_occurrences INTEGER NOT NULL,
    skipped_occurrences INTEGER NOT NULL,
    next_expected_date TEXT,
    status TEXT NOT NULL,
    issue_type TEXT,
    issue_detail TEXT
);

CREATE TABLE recurring_expectations (
    true_series_id TEXT NOT NULL,
    occurrence_date TEXT NOT NULL,
    expected_amount_usd REAL NOT NULL,
    outcome TEXT NOT NULL,
    reason TEXT,
    PRIMARY KEY (true_series_id, occurrence_date)
);

CREATE TABLE budget_labels (
    budget_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    period_month TEXT NOT NULL,
    stored_category_code TEXT NOT NULL,
    resolved_category_code TEXT NOT NULL,
    resolution_source TEXT NOT NULL,
    budget_amount_usd REAL NOT NULL,
    issue_type TEXT,
    expected_action TEXT
);

CREATE TABLE anomaly_manifest (
    anomaly_id TEXT PRIMARY KEY,
    issue_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    related_entity_id TEXT,
    observed_behavior TEXT NOT NULL,
    expected_resolution TEXT NOT NULL,
    impact_count INTEGER NOT NULL,
    severity TEXT NOT NULL
);
"""

INSERT_ORDER = [
    "category",
    "user_profile",
    "account",
    "merchant",
    "merchant_alias",
    "category_alias",
    "category_rule",
    "budget",
    "transaction",
    "transfer_link",
    "recurring_series",
    "insight",
    "entity_event",
]

GROUND_TRUTH_INSERT_ORDER = [
    "transaction_labels",
    "recurring_series_labels",
    "recurring_expectations",
    "budget_labels",
    "anomaly_manifest",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def _write_json_array(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = df.to_json(orient="records", date_format="iso", double_precision=10)
    path.write_text(text, encoding="utf-8")


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return str(value)


def _write_jsonl_gz(df: pd.DataFrame, path: Path, chunk_size: int = 10000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0) as gz:
            for start in range(0, len(df), chunk_size):
                chunk = df.iloc[start : start + chunk_size]
                for record in chunk.to_dict(orient="records"):
                    gz.write((json.dumps(record, default=_json_default, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))


def _sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (float, np.floating)):
        if pd.isna(value):
            return "NULL"
        return f"{float(value):.10g}"
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    if isinstance(value, (np.bool_, bool)):
        return "1" if bool(value) else "0"
    text = str(value)
    if text == "":
        return "NULL"
    return "'" + text.replace("'", "''") + "'"


def _write_seed_sql(df: pd.DataFrame, table: str, path_handle, chunk_size: int = 500) -> None:
    if df.empty:
        return
    columns = list(df.columns)
    column_sql = ", ".join(columns)
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start : start + chunk_size]
        values = []
        for row in chunk.itertuples(index=False, name=None):
            values.append("(" + ", ".join(_sql_literal(v) for v in row) + ")")
        table_sql = '"transaction"' if table == "transaction" else table
        path_handle.write(f"INSERT INTO {table_sql} ({column_sql}) VALUES\n")
        path_handle.write(",\n".join(values))
        path_handle.write(";\n")


def _write_sql(tables: dict[str, pd.DataFrame], ground_truth: dict[str, pd.DataFrame], sql_dir: Path) -> None:
    sql_dir.mkdir(parents=True, exist_ok=True)
    (sql_dir / "schema.sql").write_text(SCHEMA_SQL.strip() + "\n", encoding="utf-8")
    (sql_dir / "ground_truth_schema.sql").write_text(GROUND_TRUTH_SCHEMA_SQL.strip() + "\n", encoding="utf-8")
    with open(sql_dir / "seed.sql", "w", encoding="utf-8", newline="\n") as f:
        f.write("PRAGMA foreign_keys = ON;\nBEGIN;\nPRAGMA defer_foreign_keys = ON;\n")
        for table in INSERT_ORDER:
            _write_seed_sql(tables[table], table, f)
        f.write("COMMIT;\n")
    with open(sql_dir / "seed_ground_truth.sql", "w", encoding="utf-8", newline="\n") as f:
        f.write("BEGIN;\n")
        for table in GROUND_TRUTH_INSERT_ORDER:
            _write_seed_sql(ground_truth[table], table, f)
        f.write("COMMIT;\n")


def _dataset_readme(metadata: dict) -> str:
    counts = metadata["counts"]
    anomaly_counts = metadata.get("anomaly_impact_counts", metadata.get("anomaly_counts", {}))
    anomaly_text = "\n".join(f"| {k} | {v} |" for k, v in anomaly_counts.items()) or "| none | 0 |"
    return f"""# Generated Dataset

Seed: `{metadata['seed']}`  
Scale: `{metadata['scale']}`  
Generated at: `{metadata['generated_at']}`  
Schema version: `{SCHEMA_VERSION}`  
Generator version: `{GENERATOR_VERSION}`  
Project version: `{PROJECT_VERSION}`

## Counts

| Entity | Rows |
|---|---:|
| UserProfile | {counts['profiles']} |
| Account | {counts['accounts']} |
| Merchant | {counts['merchants']} |
| Category | {counts['categories']} |
| CategoryRule | {counts['category_rules']} |
| Budget | {counts['budgets']} |
| Transaction | {counts['transactions']} |
| TransferLink | {counts['transfer_links']} |
| RecurringSeries (detected) | {counts['recurring_series']} |
| Insight | {counts['insights']} |
| EntityEvent | {counts['events']} |

## Labelled exceptions

| Issue type | Rows / impact |
|---|---:|
{anomaly_text}

Ground truth is isolated under `ground_truth/` and is never joined into input features.

## Layout

- `data/` CSV entity exports
- `data/json/` JSON and JSONL.GZ exports
- `data/sql/` SQLite-compatible DDL and seed inserts
- `ground_truth/` labels and anomaly manifest
- `outputs/` reference solution outputs
- `metadata/` manifest and provenance
- `validation/` validation output
"""


def write_dataset(
    out_path: Path,
    tables: dict[str, pd.DataFrame],
    ground_truth: dict[str, pd.DataFrame],
    outputs: dict[str, pd.DataFrame],
    metadata: dict,
    formats: tuple[str, ...] = ("csv", "json", "sql"),
    write_manifest: bool = True,
) -> dict:
    files: dict[str, dict] = {}

    def record(path: Path, rows: int, fmt: str) -> None:
        rel = str(path.relative_to(out_path)).replace("\\", "/")
        files[rel] = {
            "format": fmt,
            "rows": int(rows),
            "bytes": int(path.stat().st_size),
            "sha256": _sha256(path),
        }

    for name, df in tables.items():
        path = out_path / "data" / f"{name}.csv"
        _write_csv(df, path)
        record(path, len(df), "csv")
    for name, df in ground_truth.items():
        path = out_path / "ground_truth" / f"{name}.csv"
        _write_csv(df, path)
        record(path, len(df), "csv")
    for name, df in outputs.items():
        path = out_path / "outputs" / f"{name}.csv"
        _write_csv(df, path)
        record(path, len(df), "csv")

    if "json" in formats:
        large_json = {"transaction", "budget", "insight"}
        for name, df in tables.items():
            if name in large_json:
                path = out_path / "data" / "json" / f"{name}.jsonl.gz"
                _write_jsonl_gz(df, path)
            else:
                path = out_path / "data" / "json" / f"{name}.json"
                _write_json_array(df, path)
            record(path, len(df), "json")
        large_gt = {"transaction_labels", "recurring_expectations", "budget_labels"}
        for name, df in ground_truth.items():
            if name in large_gt:
                path = out_path / "ground_truth" / f"{name}.jsonl.gz"
                _write_jsonl_gz(df, path)
            else:
                path = out_path / "ground_truth" / f"{name}.json"
                _write_json_array(df, path)
            record(path, len(df), "json")

    if "sql" in formats:
        _write_sql(tables, ground_truth, out_path / "data" / "sql")
        for name in ["schema.sql", "ground_truth_schema.sql"]:
            path = out_path / "data" / "sql" / name
            record(path, 0, "sql")
        path = out_path / "data" / "sql" / "seed.sql"
        record(path, int(sum(len(tables[t]) for t in INSERT_ORDER)), "sql")
        path = out_path / "data" / "sql" / "seed_ground_truth.sql"
        record(path, int(sum(len(ground_truth[t]) for t in GROUND_TRUTH_INSERT_ORDER)), "sql")

    (out_path / "README.md").write_text(_dataset_readme(metadata), encoding="utf-8")
    files["README.md"] = {
        "format": "markdown",
        "rows": 0,
        "bytes": int((out_path / "README.md").stat().st_size),
        "sha256": _sha256(out_path / "README.md"),
    }

    source_manifest = {
        "external_data_used": False,
        "provenance": "All records are synthetic and generated deterministically from a fixed seed. No personal, confidential, scraped, or externally licensed data is included.",
        "source_references": [
            {
                "name": "Public banking and budgeting schema conventions",
                "url": None,
                "dataset_version": None,
                "retrieved_at": None,
                "license": None,
                "usage": "Schema inspiration only; no source records copied.",
            }
        ],
        "libraries": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "generated_at": metadata["generated_at"],
        "seed": metadata["seed"],
        "license_note": "Synthetic output produced for this project. Do not represent it as real customer data.",
    }
    source_path = out_path / "metadata" / "source_manifest.json"
    source_path.write_text(json.dumps(source_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files[str(source_path.relative_to(out_path)).replace("\\", "/")] = {
        "format": "json",
        "rows": 0,
        "bytes": int(source_path.stat().st_size),
        "sha256": _sha256(source_path),
    }

    manifest = dict(metadata)
    manifest["files"] = dict(sorted(files.items()))
    manifest["total_bytes"] = int(sum(v["bytes"] for v in files.values()))
    manifest_path = out_path / "metadata" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
