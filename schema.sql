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
