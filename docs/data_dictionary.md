# Data Dictionary

Version: 2026.1  
Seed: 20261022  
Horizon: 2026-01-01 through 2026-12-31  
Currency: USD unless stated otherwise  
All date-only values use ISO `YYYY-MM-DD`; timestamps use ISO 8601 UTC with `Z`.

Legend: PK = primary key, FK = foreign key, UQ = unique constraint, REQ = required.

## Global conventions

- Signed amounts: expenses and transfer debits are negative; income, transfer credits, and refunds are positive.
- `period_month` is always `YYYY-MM` and is derived from the **local** transaction date.
- Empty optional text is exported as a blank CSV field and as `NULL` in SQL.
- Synthetic emails use the reserved `.test` domain.
- `is_active`, `is_primary`, `is_synthetic`, `online_capable`, and `subscription_capable` are booleans in CSV and `0/1` in SQL.
- All entity tables have an immutable primary key. Retained state changes are represented by new records and `entity_event`, not by overwriting prior transactions.
- Ground truth files are isolated in `dataset/ground_truth/` and must not be joined into input features.

## 1. UserProfile

Primary key: `user_id` (UQ). Cardinality: one user has 1:N accounts, budgets, transactions, detected recurring series, and insights.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| user_id | text | yes | `^USR-\d{6}$` | — | PK | Immutable, zero-padded, sequential |
| display_name | text | yes | Synthetic first + last name | — | no | Non-empty |
| email | text | yes | `userNNNNNN@example.test` | — | UQ | Reserved test domain; no real PII |
| country | text | yes | `US` | — | no | ISO country code |
| state_code | text | yes | Two-letter US state code | — | no | Member of documented state list |
| city | text | yes | Synthetic city | — | no | Non-empty |
| postal_code | text | yes | Five digits | — | no | Synthetic; not a real address |
| timezone | text | yes | IANA timezone, e.g. `America/New_York` | — | no | Must be a valid zone for local/UTC conversion |
| household_size | integer | yes | 1-6 | people | no | Range check |
| income_band | text | yes | `25k-50k`, `50k-75k`, `75k-100k`, `100k-150k`, `150k-250k` | USD/year | no | Matches annual income band |
| annual_income_usd | real | yes | >= 0 | USD/year | no | Within selected band, rounded to 2 dp |
| credit_score | integer | yes | 300-850 | score | no | Range check |
| risk_tier | text | yes | `low`, `medium`, `high` | — | no | Derived: >=740 low, 660-739 medium, <660 high |
| segment | text | yes | `standard`, `plus`, `premium` | — | no | Derived from annual income |
| lifecycle_state | text | yes | `active`, `dormant`, `closed` | — | no | Matches last entity event |
| created_at | timestamp | yes | ISO UTC | — | no | Before any account or transaction |
| updated_at | timestamp | yes | ISO UTC | — | no | >= created_at; reflects latest lifecycle action |
| effective_from | timestamp | yes | ISO UTC | — | no | Equals created_at for this snapshot |
| effective_to | timestamp | no | ISO UTC | — | no | Blank for current row; history lives in events |
| is_synthetic | boolean | yes | true | — | no | Must be true |
| data_origin | text | yes | `synthetic_generator` | — | no | Provenance tag |

## 2. Account

Primary key: `account_id` (UQ). Foreign key: `user_id` -> UserProfile. Cardinality: each account belongs to exactly one user; each user has 1:N accounts. A user has one primary checking account and may have savings and credit-card accounts.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| account_id | text | yes | `ACC-<user_id>-NN` | — | PK | Prefix exactly matches user_id; NN is 01-03 |
| user_id | text | yes | UserProfile.user_id | — | no | FK integrity |
| account_type | text | yes | `checking`, `savings`, `credit_card` | — | composite | (user_id, account_type, opened_at) UQ |
| nickname | text | yes | Synthetic label | — | no | Non-empty |
| currency | text | yes | `USD` | — | no | Must match transaction currency |
| status | text | yes | `active`, `frozen`, `closed` | — | no | Closed only after last posted transaction |
| opened_at | timestamp | yes | ISO UTC | — | composite | >= user created_at; <= first transaction |
| closed_at | timestamp | no | ISO UTC | — | no | Required when status=closed; no posted transaction after it |
| opening_balance_usd | real | yes | 0.00 for generated accounts | USD | no | Ledger opening balance |
| current_balance_usd | real | yes | Sum of posted transaction amounts | USD | no | Derived; reconciles to ledger within $0.01 |
| credit_limit_usd | real | no | Positive for credit cards; blank otherwise | USD | no | Present only for credit_card accounts |
| is_primary | boolean | yes | true for checking primary account | — | no | Exactly one true per user in this dataset |

## 3. Merchant

Primary key: `merchant_id` (UQ). Foreign key: `default_category_code` -> Category. Cardinality: Merchant 1:N Transaction; Merchant 1:N MerchantAlias; Merchant N:M Category through CategoryRule.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| merchant_id | text | yes | `^MER-\d{6}$` | — | PK | Immutable |
| canonical_name | text | yes | Synthetic merchant name | — | no | Non-empty |
| default_category_code | text | yes | Active Category.category_code | — | no | FK; does not by itself overwrite transaction ground truth |
| mcc | text | yes | Four-digit illustrative MCC | code | no | Non-empty |
| country | text | yes | `US` | — | no | ISO country code |
| city | text | yes | `Multiple` or city | — | no | Non-empty |
| online_capable | boolean | yes | true/false | — | no | Controls online channel probability |
| subscription_capable | boolean | yes | true/false | — | no | Identifies recurring-style merchants |
| status | text | yes | `active`, `inactive` | — | no | Active for all generated merchants |
| effective_from | date | yes | `2025-01-01` | — | no | <= transaction dates |
| effective_to | date | no | Blank for active | — | no | Required if inactive |

### 3a. MerchantAlias

Primary key: `alias_id` (UQ). Foreign key: `merchant_id` -> Merchant. Alias text is unique per merchant, not globally, because ambiguous descriptor fragments such as `AMAZON` and `UBER` are intentionally shared.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| alias_id | text | yes | `^MAL-\d{6}$` | — | PK | Immutable |
| merchant_id | text | yes | Merchant.merchant_id | — | composite | (merchant_id, alias_text) UQ |
| alias_text | text | yes | Uppercase descriptor fragment | — | composite | Non-empty; may repeat across merchants |
| is_primary | boolean | yes | true for first alias | — | no | At most one primary per merchant |
| effective_from | date | yes | ISO date | — | no | <= transaction use |
| effective_to | date | no | Blank | — | no | Optional |

## 4. Transaction

Primary key: `transaction_id` (UQ). Foreign keys: `user_id` -> UserProfile, `account_id` -> Account, `merchant_id` -> Merchant (optional for transfers), `refund_of_txn_id` -> Transaction (optional). Cardinality: each transaction belongs to one user and one account; each transaction has at most one original refund target and may be the target of 1:N refunds. Transfer relationships are N:M through TransferLink.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| transaction_id | text | yes | `TXN-2026-\d{8}` | — | PK | Sequential, contiguous, immutable |
| user_id | text | yes | UserProfile.user_id | — | no | FK; matches account owner |
| account_id | text | yes | Account.account_id | — | no | FK; account owner equals user_id |
| transaction_date | date | yes | Local date in user's timezone | — | no | >= account opened local date; <= lifecycle cutoff |
| posted_at_utc | timestamp | yes | ISO UTC converted from local date/time | — | no | May fall in a different calendar month than transaction_date |
| merchant_id | text | no | Merchant.merchant_id; blank for internal transfers | — | no | FK when present |
| descriptor | text | yes | Synthetic bank descriptor | — | no | Non-empty; not a ground-truth category field |
| amount_usd | real | yes | Nonzero signed amount, 2 dp | USD | no | Negative spend/debit, positive income/credit/refund |
| currency | text | yes | `USD` | — | no | Account currency |
| mcc | text | no | Four-digit MCC; blank for transfers | code | no | Consistent with merchant when present |
| channel | text | yes | `card`, `ach`, `online`, `pos`, `atm`, `internal` | — | no | Allowed enum |
| status | text | yes | `posted`, `pending`, `reversed` | — | no | Posted transactions participate in balances |
| refund_of_txn_id | text | no | Transaction.transaction_id | — | no | FK; original amount negative; refund date >= original; refund amount <= original absolute amount |

Business invariants:

- Transfer legs have no merchant, amount signs are opposite, dates match, and the pair nets to zero.
- Refunds are positive and may be partial.
- A transaction is never overwritten. Corrections are separate linked records.
- Exact duplicate fingerprints should not exist except where explicitly labelled.

## 5. Category

Primary key: `category_code` (UQ). Self-referencing hierarchy via `parent_code`. Cardinality: Category 1:N CategoryRule, Budget, Merchant defaults; Category N:M UserProfile through Budget; Category N:M Transaction through decision history.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| category_code | text | yes | Uppercase identifier, e.g. `GROCERY` | — | PK | Immutable |
| name | text | yes | Human-readable name | — | no | Non-empty |
| type | text | yes | `expense`, `income`, `transfer`, `refund` | — | no | Drives treatment fallback |
| parent_code | text | no | Category.category_code | — | no | FK; root groups `INCOME` and `HOUSING` exist |
| is_budgetable | boolean | yes | true/false | — | no | Budgets only reference budgetable categories |
| is_active | boolean | yes | true/false | — | no | Legacy codes are false and have effective_to 2025-12-31 |
| taxonomy_version | text | yes | `2026.1` | — | no | Version tag |
| effective_from | date | yes | `2025-01-01` | — | no | <= use date |
| effective_to | date | no | `2025-12-31` for deprecated codes; blank otherwise | — | no | >= effective_from |

Active taxonomy includes `INCOME_SALARY`, `INCOME_OTHER`, `HOUSING_RENT`, `UTILITIES`, `GROCERY`, `DINING`, `TRANSPORT`, `SUBSCRIPTION`, `SHOPPING`, `HEALTH`, `ENTERTAINMENT`, `TRAVEL`, `INSURANCE`, `EDUCATION`, `FEES`, `TRANSFER`, `REFUND`, `OTHER`, plus root groups `INCOME` and `HOUSING`. Deprecated codes `FOOD`, `TRANSPORTATION`, `SUBSCRIPTIONS`, `UTIL`, and `MISC` remain in the table so historical budgets can be stored with FK integrity.

### 5a. CategoryAlias

Primary key: `alias_id` (UQ). Foreign key: `canonical_code` -> Category. Cardinality: N:1 Category.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| alias_id | text | yes | `^CAT-\d{6}$` | — | PK | Immutable |
| alias_code | text | yes | Deprecated code | — | composite | (alias_code, effective_from) UQ |
| canonical_code | text | yes | Active category code | — | no | FK |
| effective_from | date | yes | `2026-01-01` | — | no | <= budget resolution date |
| effective_to | date | no | Blank | — | no | Optional |
| status | text | yes | `deprecated`, `merged`, `renamed` | — | no | Allowed enum |
| reason | text | yes | Human-readable migration reason | — | no | Non-empty |

### 5b. CategoryRule

Primary key: `rule_id` (UQ). Foreign keys: `category_code` -> Category, `merchant_id` -> Merchant (optional). Cardinality: Merchant N:M Category through rules; each rule maps one category.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| rule_id | text | yes | `^RUL-\d{6}$` | — | PK | Immutable |
| category_code | text | yes | Category.category_code | — | no | FK; active category |
| merchant_id | text | no | Merchant.merchant_id | — | no | FK; optional for global rules |
| match_field | text | yes | `descriptor`, `mcc`, `merchant` | — | no | Allowed enum |
| match_type | text | yes | `exact`, `contains`, `regex` | — | no | Allowed enum |
| pattern | text | yes | Uppercase descriptor fragment or pattern | — | composite | (category_code, merchant_id, pattern, effective_from) UQ |
| priority | integer | yes | Higher wins | rank | no | Nonnegative; deterministic tie-break by rule_id |
| confidence | real | yes | 0.0-1.0 | probability | no | Range check |
| effective_from | date | yes | ISO date | — | no | <= transaction date |
| effective_to | date | no | Blank | — | no | Optional |
| status | text | yes | `active`, `retired` | — | no | Only active rules apply |

## 6. Budget

Primary key: `budget_id` (UQ). Foreign keys: `user_id` -> UserProfile, `category_code` -> Category. Cardinality: this is the N:M bridge between UserProfile and Category, carrying `year`, `month`, amount, and status. A user can have many category budgets per month.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| budget_id | text | yes | `BUD-<user_id>-YYYY-MM-<category_code>` | — | PK | Exact user, year, month, stored category |
| user_id | text | yes | UserProfile.user_id | — | composite | FK; (user_id, year, month, category_code, version) UQ |
| year | integer | yes | 2026 | year | composite | Horizon year |
| month | integer | yes | 1-12 | month | composite | Period month |
| category_code | text | yes | Category.category_code; may be a labelled deprecated code | — | composite | FK; deprecated codes are intentional exceptions |
| budget_amount_usd | real | yes | > 0, rounded to 5 USD | USD/month | no | Range check |
| currency | text | yes | `USD` | — | no | — |
| period_start | date | yes | First day of month | — | no | Matches year/month |
| period_end | date | yes | Last day of month | — | no | >= period_start |
| status | text | yes | `draft`, `active`, `closed` | — | no | Active for the 2026 planning snapshot |
| version | integer | yes | 1 | — | composite | Part of natural uniqueness |
| created_at | timestamp | yes | ISO UTC | — | no | Before period_start |
| updated_at | timestamp | yes | ISO UTC | — | no | >= created_at |

A small percentage of rows intentionally store deprecated category codes. These rows are PK-valid and FK-valid; the mismatch is labelled in `ground_truth/budget_labels.csv`.

## 7. TransferLink

Primary key: `link_id` (UQ). Foreign keys: `debit_txn_id` and `credit_txn_id` -> Transaction. Cardinality: N:M bridge between two transaction postings; each transaction participates in at most one link.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| link_id | text | yes | `^TLK-\d{6}$` | — | PK | Immutable |
| debit_txn_id | text | yes | Transaction.transaction_id | — | UQ | FK; amount negative; account checking |
| credit_txn_id | text | yes | Transaction.transaction_id | — | UQ | FK; amount positive; account savings |
| link_type | text | yes | `internal_savings` | — | no | Allowed value |
| linked_amount_usd | real | yes | > 0 | USD | no | Equals absolute value of both legs |
| created_at | timestamp | yes | ISO UTC | — | no | Traceability |
| status | text | yes | `posted` | — | no | Matches legs |

## 8. RecurringSeries (derived entity)

Primary key: `series_id` (UQ). Foreign keys: `user_id`, `account_id`, `merchant_id`, `category_code`. Cardinality: User 1:N series; Merchant 1:N series; Account 1:N series. This entity is created by the recurring detector, not seeded from ground truth.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| series_id | text | yes | `^REC-\d{6}$` | — | PK | Detected series IDs |
| user_id | text | yes | UserProfile.user_id | — | no | FK |
| account_id | text | yes | Account.account_id | — | no | FK; mode account among occurrences |
| merchant_id | text | yes | Merchant.merchant_id | — | no | FK |
| category_code | text | yes | Predicted Category.category_code | — | no | FK |
| cadence | text | yes | `monthly` in this dataset | — | no | Allowed cadence enum |
| expected_amount_usd | real | yes | Median absolute occurrence amount | USD | no | > 0 |
| first_occurrence | date | yes | ISO date | — | no | <= last_occurrence |
| last_occurrence | date | yes | ISO date | — | no | >= first_occurrence |
| occurrence_count | integer | yes | >= 3 | count | no | Monthly pattern requirement |
| missed_occurrences | integer | yes | >= 0 | count | no | Number of 45+ day gaps detected |
| next_expected_date | date | no | ISO date | — | no | Required when status=active |
| status | text | yes | `active`, `paused`, `cancelled`, `ended` | — | no | Allowed enum |
| confidence | real | yes | 0.0-1.0 | probability | no | Range check |
| detection_method | text | yes | `monthly_gap_amount_stability_v1` | — | no | Method trace |
| detected_at | timestamp | yes | ISO UTC | — | no | Fixed generated-at timestamp |

## 9. Insight

Primary key: `insight_id` (UQ). Foreign key: `user_id` -> UserProfile. Cardinality: User 1:N insights. One row per user, month, insight type, and metric.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| insight_id | text | yes | `^INS-\d{6}$` | — | PK | Immutable |
| user_id | text | yes | UserProfile.user_id | — | no | FK |
| period_month | text | yes | `YYYY-MM` | — | no | Local calendar month |
| insight_type | text | yes | `monthly_spend_summary`, `budget_variance_summary`, `recurring_summary`, `data_quality_summary` | — | no | Allowed enum |
| metric_name | text | yes | e.g. `net_spend_usd`, `net_savings_usd`, `budget_variance_usd`, `recurring_series_count`, `uncategorized_rate` | mixed | no | Type-specific |
| metric_value | real | yes | Finite number | mixed | no | Must reconcile to documented formula |
| currency | text | yes | `USD` for money metrics; `USD` label retained for rates | — | no | — |
| details_json | text | yes | Compact JSON object | — | no | Valid JSON; includes source components |
| source_txn_count | integer | yes | >= 0 | count | no | Number of transactions underpinning the insight |
| formula_version | text | yes | `2026.1` | — | no | Traceable formula version |
| generated_at | timestamp | yes | ISO UTC | — | no | Fixed generated-at timestamp |
| status | text | yes | `generated` | — | no | Allowed value |

## 10. EntityEvent

Primary key: `event_id` (UQ). Polymorphic reference to user or account entities; entity existence is validated by `entity_type`. Cardinality: entity 1:N events. This table preserves lifecycle history.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| event_id | text | yes | `^EVT-\d{6}$` | — | PK | Immutable |
| entity_type | text | yes | `user_profile`, `account` | — | no | Must exist in entity registry |
| entity_id | text | yes | Corroborating user or account ID | — | no | Exists for entity_type |
| event_type | text | yes | `CREATED`, `OPENED`, `DORMANT`, `CLOSED` | — | no | Allowed transition |
| event_at | timestamp | yes | ISO UTC | — | no | Ordered per entity |
| from_state | text | no | `active`, `dormant`, `closed`, blank for creation | — | no | Valid previous state |
| to_state | text | yes | `active`, `dormant`, `closed` | — | no | Matches lifecycle target |
| reason | text | yes | Human-readable reason | — | no | Non-empty |
| source | text | yes | `synthetic_generator` | — | no | Provenance |

## 11. TransactionCategoryDecision (bridge, output)

Primary key: `decision_id` (UQ). Foreign keys: `transaction_id` -> Transaction, `category_code` -> Category, `rule_id` -> CategoryRule (optional). Cardinality: N:M history bridge between Transaction and Category; this snapshot stores one current decision per transaction, and the schema supports future history through new decision rows.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| decision_id | text | yes | `^DCS-\d{8}$` | — | PK | Immutable |
| transaction_id | text | yes | Transaction.transaction_id | — | current snapshot | FK |
| category_code | text | yes | Category.category_code | — | no | FK; predicted, not ground truth |
| rule_id | text | no | CategoryRule.rule_id | — | no | FK; blank for fallback |
| confidence | real | yes | 0.0-1.0 | probability | no | Range check |
| decision_source | text | yes | `rule`, `fallback`, `sign_fallback` | — | no | Trace of decision path |
| predicted_treatment | text | yes | `spend`, `income`, `transfer`, `refund` | — | no | Derived from category type and sign |
| decided_at | timestamp | yes | ISO UTC | — | no | Fixed generated-at timestamp |
| model_version | text | yes | `rules-v1` | — | no | Version tag |

## 12. Ground truth

All ground-truth files are separate from input features.

### 12a. transaction_labels

Primary key: `transaction_id` (UQ). One row per transaction.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| transaction_id | text | yes | Transaction.transaction_id | — | PK | Covers every transaction exactly once |
| true_category_code | text | yes | Category.category_code | — | no | Generated from merchant/context, not rules |
| true_treatment | text | yes | `spend`, `income`, `transfer`, `refund`, `excluded` | — | no | Allowed enum |
| expected_period | text | yes | `YYYY-MM` from local date | — | no | Equals transaction_date[:7] |
| is_recurring | boolean | yes | true/false | — | no | True only for injected series occurrences |
| true_series_id | text | no | `TRU-*` | — | no | Present for recurring occurrences |
| issue_type | text | no | Five documented anomaly types or blank | — | no | Matches anomaly manifest |
| issue_detail | text | no | Human-readable detail | — | no | Required when issue_type present |
| related_transaction_id | text | no | Related transaction ID | — | no | Original refund or opposite transfer leg |

### 12b. recurring_series_labels

Primary key: `true_series_id` (UQ). Generated from the injection plan, independent of detection.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| true_series_id | text | yes | `^TRU-\d{6}$` | — | PK | Immutable |
| user_id | text | yes | UserProfile.user_id | — | no | Source user |
| account_id | text | yes | Account.account_id | — | no | Source account |
| merchant_id | text | yes | Merchant.merchant_id | — | no | Source merchant |
| merchant_key | text | yes | Internal merchant key | — | no | Trace only |
| category_code | text | yes | Category.category_code | — | no | True category |
| cadence | text | yes | `monthly` | — | no | — |
| expected_amount_usd | real | yes | > 0 | USD | no | Base expected amount |
| start_date | date | yes | ISO date | — | no | <= end_date |
| end_date | date | yes | ISO date | — | no | Last posted or planned date |
| planned_occurrences | integer | yes | >= 1 | count | no | Months in active range |
| posted_occurrences | integer | yes | >= 0 | count | no | Rows in transaction_labels with is_recurring |
| skipped_occurrences | integer | yes | 0 or 1 | count | no | Injected skip |
| next_expected_date | date | no | ISO date | — | no | Required for active series |
| status | text | yes | `active`, `cancelled` | — | no | Injection lifecycle |
| issue_type | text | no | `recurring_series_skip` or blank | — | no | Series-level label |
| issue_detail | text | no | Human-readable detail | — | no | Required when issue present |

### 12c. recurring_expectations

Composite primary key: (`true_series_id`, `occurrence_date`). One row per planned occurrence, including skipped occurrences.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| true_series_id | text | yes | recurring_series_labels.true_series_id | — | composite | FK to labels |
| occurrence_date | date | yes | ISO date | — | composite | Within series range |
| expected_amount_usd | real | yes | > 0 | USD | no | Matches occurrence plan |
| outcome | text | yes | `posted`, `skipped` | — | no | Allowed enum |
| reason | text | no | `injected_recurring_skip` or blank | — | no | Required for skipped |

### 12d. budget_labels

Primary key: `budget_id` (UQ). One row per budget.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| budget_id | text | yes | Budget.budget_id | — | PK | Covers every budget |
| user_id | text | yes | UserProfile.user_id | — | no | — |
| period_month | text | yes | `YYYY-MM` | — | no | — |
| stored_category_code | text | yes | Category.category_code as stored in budget | — | no | May be deprecated |
| resolved_category_code | text | yes | Active category after alias mapping | — | no | — |
| resolution_source | text | yes | `direct`, `alias` | — | no | — |
| budget_amount_usd | real | yes | > 0 | USD | no | Matches budget row |
| issue_type | text | no | `budget_taxonomy_mismatch` or blank | — | no | Required for deprecated stored codes |
| expected_action | text | no | Human-readable resolution | — | no | Required when issue present |

### 12e. anomaly_manifest

Primary key: `anomaly_id` (UQ). Summarizes every deliberate or observed exception.

| Field | Type | Req | Allowed values / format | Units | Unique | Validation |
|---|---|---|---|---|---|---|
| anomaly_id | text | yes | `^ANM-\d{6}$` | — | PK | Immutable |
| issue_type | text | yes | Five documented anomaly types | — | no | All required types present |
| entity_type | text | yes | `transaction`, `recurring_series`, `budget` | — | no | Allowed |
| entity_id | text | yes | ID in the corresponding entity | — | no | Exists |
| related_entity_id | text | no | Related transaction/user/merchant/etc. | — | no | Optional trace |
| observed_behavior | text | yes | Human-readable defect description | — | no | Non-empty |
| expected_resolution | text | yes | Business rule to apply | — | no | Non-empty |
| impact_count | integer | yes | >= 1 | rows | no | Matches labels or budget count |
| severity | text | yes | `low`, `medium`, `high` | — | no | Allowed |

## 13. Reference solution outputs

| File | Grain | Key fields | Purpose |
|---|---|---|---|
| `outputs/categorization_decisions.csv` | transaction | decision_id, transaction_id, category_code, rule_id, confidence | Decision trace |
| `outputs/categorized_transactions.csv` | transaction | transaction_id, predicted_category_code, predicted_treatment, offset_category_code, spend_amount_usd | Strict ledger |
| `outputs/monthly_spend.csv` | user-month | user_id, period_month, spend_usd, income_usd | Aggregation |
| `outputs/budget_comparison.csv` | budget | budget_id, resolved_category_code, actual_spend_usd, variance_usd, status | Budget vs actual |
| `outputs/recurring_series.csv` | detected series | series_id, user_id, merchant_id, next_expected_date, confidence | Recurring mapping |
| `data/insight.csv` | user-month-type-metric | insight_id, metric_name, metric_value, details_json | Derived insights |

Formulas:

- Strict spend for a spend transaction = `abs(amount_usd)`.
- Strict spend for a refund = `-abs(amount_usd)`, attributed to the original category when linked, otherwise to the merchant default category.
- Transfers, income, and excluded rows contribute 0 to strict spend.
- Budget variance = `budget_amount_usd - actual_spend_usd`.
- Usage percent = `actual_spend_usd / budget_amount_usd * 100`.
- Status = `over` if actual > budget; `near` if actual >= 90% of budget; otherwise `under`.
- Net spend insight = sum of strict spend for the user-month.
- Net savings insight = income minus net spend.
- Recurring count insight = detected series count for the user.
