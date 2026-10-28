# Decisions, Rules, and Metric Definitions

## Core design decisions

1. **Synthetic only.** No external data is used. Public schema conventions inspired field names only. This avoids licensing, privacy, and redistribution risk.
2. **Master data first.** Categories and their parent groups, users, accounts, merchants, aliases, and rules are created before budgets, transactions, transfer links, detected series, insights, and lifecycle events.
3. **Signed ledger.** Expenses and transfer debits are negative. Income, transfer credits, and refunds are positive. Every derived metric uses signed amounts and documented treatment.
4. **Local-date accounting.** `transaction_date` is local to the user's IANA timezone. `posted_at_utc` is the converted UTC timestamp. Budget and insight periods use local dates. This is why UTC month can differ from the assigned period.
5. **No history overwrite.** Refunds, transfers, and duplicate transfer debits are distinct rows. Lifecycle changes are in `entity_event`. Account balances are derived from posted ledger rows.
6. **Labels from rules, not random assignment.** True transaction categories come from the merchant's canonical category and transaction context (refund, transfer, refund inheritance). Ambiguous descriptors are deliberate but the truth is still deterministic.
7. **Ground truth is isolated.** The pipeline reads only `data/`. Evaluation and validation may read `ground_truth/` after the pipeline run.
8. **Detected recurring series are an output, not an input.** True recurring plans live in ground truth. `recurring_series.csv` is created from transaction patterns, so recurring evaluation is not circular.
9. **Budget mismatch is injected at the data layer.** Deprecated codes remain FK-valid because legacy categories are retained. The solution must resolve them through `category_alias`.
10. **Deterministic output.** Seed `20261022`, fixed generated timestamps, fixed gzip mtime, sorted writes, and stable merge order.

## Category rule strategy

Rules apply in descending priority. A rule matches when its descriptor pattern appears in the uppercase descriptor. Ties break by `rule_id`. Global transfer and refund rules have the highest priority so a merchant alias cannot override those treatments.

Ambiguity is intentional:

- `UBER` is shared by Uber trips (transport) and Uber Eats (dining).
- `AMAZON` is shared by Amazon Marketplace (shopping) and Amazon Prime (subscription).
- Two percent of filler descriptors are replaced with generic fragments such as `POS DEBIT 8812` or `WEB PMT 90210`, producing fallback and misclassification cases.
- Refund anomalies use purchase-like descriptors and often lack an original link.

The detector uses only descriptor, amount sign, and master data. It never reads labels.

## Treatment rules

| Condition | Predicted treatment | Strict spend contribution |
|---|---|---|
| Predicted category type is transfer | transfer | 0 |
| Amount > 0 and predicted category type is income | income | 0 |
| Amount > 0 and predicted category type is not income | refund | negative absolute amount |
| Amount < 0 and predicted category type is income | income | 0 |
| Amount < 0 otherwise | spend | positive absolute amount |

Refund offset category: original predicted category when `refund_of_txn_id` is present; otherwise the merchant's default category; otherwise `OTHER`.

## Anomaly handling

### Transfer double counting

Normal transfers are two linked legs. A labelled extra debit copies a transfer leg and is not linked. Both the proper legs and the duplicate are predicted as transfers, so strict treatment excludes them. The naive diagnostic sums the absolute values of both transfer legs, which is the double-count failure mode.

### Refund treated as new expense

Normal refunds start with `REFUND` and link to the original. Labelled anomaly refunds are positive, use purchase-like descriptors, and frequently have no original link. Sign plus expense-merchant context identifies them as refunds. Strict net spend subtracts them; naive logic would add them as new spending.

### Recurring series skips incorrectly

A labelled series omits one expected monthly occurrence. Ground truth records the skipped expectation. The detector reports `missed_occurrences` when the gap exceeds 45 days. Evaluation measures skip recall by matching user and merchant.

### Timezone boundary

Every transaction whose local month differs from its UTC posting month is labelled, including deliberately late-night month-end rows and naturally occurring boundary rows. If such a row also has a primary injected anomaly, that primary label wins and the row remains labelled in the anomaly manifest. Local-date period accuracy should be 100%; UTC month assignment is measured as the baseline.

### Budget taxonomy mismatch

A labelled percentage of budgets use deprecated codes (`FOOD`, `TRANSPORTATION`, `SUBSCRIPTIONS`, `UTIL`, `MISC`). This is FK-valid because legacy categories remain in the taxonomy. Strict comparison resolves through `category_alias`; naive direct joins see zero actual spend and falsely classify the budget as under.

## Derived metrics

### Categorization

- Accuracy = correct predicted category / labelled transactions.
- Macro F1 = unweighted mean F1 across classes with positive support.
- Weighted F1 = support-weighted mean F1.
- Fallback rate = decisions with `decision_source=fallback` / transactions.
- Uncategorized rate = predicted `OTHER` / transactions.

### Period assignment

- Local accuracy = expected local month equals assigned local month.
- UTC baseline = expected local month equals raw UTC month.

### Transfer/refund impact

- Transfer absolute amount = sum of absolute amounts of true-transfer rows.
- Refund credit amount = sum of positive true-refund amounts.
- Strict net spend = sum of strict spend contributions.
- Naive overstatement = transfer absolute amount + 2 x refund credit amount. This reflects both transfer legs counted and refunds added instead of offset.
- Naive transfer double count = transfer absolute amount.
- Naive refund expense effect = 2 x refund credit amount.

### Recurring detection

- Precision = matched detected series / detected series.
- Recall = matched detected series / detectable ground-truth series (posted occurrences at least 3).
- F1 = harmonic mean.
- Amount MAPE = mean absolute percentage error of expected amount for matched series.
- Next-date error = absolute days between detected and true next expected date for matched active series.
- Skip recall = labelled skip series flagged by detector / labelled skip series.
- Posted-occurrence support = ground-truth posted occurrences inside a matched detected series window / all ground-truth posted occurrences.

Detector parameters:

- Group by user, merchant, and debit/credit direction.
- At least 3 distinct months.
- Median gap 25-35 days.
- Amount coefficient of variation at most 0.22.
- Missed occurrence if a gap exceeds 45 days.
- Expected amount = median absolute amount.
- Next expected date = last occurrence + rounded median gap.
- Status = ended if last occurrence is before October and a miss exists, otherwise active.

### Budget comparison

- Actual spend uses predicted categories and strict refund offsets.
- Variance = budget - actual.
- Usage = actual / budget x 100.
- Status: `over` if actual > budget; `near` if actual >= 90% of budget; otherwise `under`.
- Resolution accuracy = mismatch budgets resolved to the ground-truth canonical category / mismatch budgets.
- Naive mismatch false-under count = mismatch rows that a direct stored-code join would value at zero actual spend.

### Reconciliation

- Account balance = opening balance + sum of posted transaction amounts, rounded to 2 dp.
- Ledger balance = sum of all posted transaction amounts.
- Monthly spend rollup must equal strict spend grouped by user and local month.
- Insight metrics must equal the corresponding monthly spend, budget variance, and recurring counts.

### Exception handling score

Unweighted mean of:

1. Transfer duplicate treatment consistency.
2. Refund anomaly treatment consistency.
3. Local-month period accuracy.
4. Recurring skip recall.
5. Budget mismatch resolution rate.

## Acceptance mapping

| Requirement | Implementation |
|---|---|
| Master data before dependent data | Generator order and FK-valid SQL insert order |
| Signed ledger and merchant descriptors | Transaction schema and amount generator |
| Category taxonomy and mapping rules | Category, CategoryAlias, CategoryRule |
| Monthly budgets | Budget bridge entity |
| Recurring salary, rent, subscriptions | Series injection and detected recurring output |
| Derived insights | Insight table from strict ledger |
| No history overwrite | Separate transfer/refund rows and entity events |
| Primary and foreign keys | schema.sql and validation FK checks |
| Bridge tables | Budget, TransferLink, TransactionCategoryDecision |
| Deterministic IDs | ID formatters and contiguous transaction sequence |
| 1,000 users / 500,000 transactions | `--scale full` |
| Merchant aliases | MerchantAlias |
| Refunds, transfers, recurring bills | Treatment and link tables |
| Seasonal spending | Monthly seasonal multipliers by category |
| Ambiguous categories | Shared aliases and generic descriptors |
| Fixed seed and scale parameter | Seed 20261022, mini/starter/full |
| Five labelled edge cases | Injectors and ground truth |
| Derived values | Account balances, treatments, budget comparison, insights |
| Separate ground truth | `dataset/ground_truth/` |
| Validation | `validation_summary.json` and `.md` |
| CSV/JSON/SQL | All three formats |
| README, schema, dictionary, manifest | Root docs and dataset metadata |
| Reproducibility | `reproduce` command and report |
| Lawful provenance | Synthetic only, source manifest |
