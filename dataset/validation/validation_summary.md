# Validation Summary

Overall status: **PASS**

- Dataset: `dataset`
- Seed: `20261022`
- Scale: `full`
- Checks: 138 pass, 0 warn, 0 fail

| Check | Status | Expected | Actual | Note |
|---|---|---|---|---|
| user_profile.user_id unique | PASS | 0 | 0 |  |
| user_profile not empty | PASS | >0 | 1000 |  |
| account.account_id unique | PASS | 0 | 0 |  |
| account not empty | PASS | >0 | 2335 |  |
| merchant.merchant_id unique | PASS | 0 | 0 |  |
| merchant not empty | PASS | >0 | 82 |  |
| merchant_alias.alias_id unique | PASS | 0 | 0 |  |
| merchant_alias not empty | PASS | >0 | 246 |  |
| category.category_code unique | PASS | 0 | 0 |  |
| category not empty | PASS | >0 | 25 |  |
| category_alias.alias_id unique | PASS | 0 | 0 |  |
| category_alias not empty | PASS | >0 | 5 |  |
| category_rule.rule_id unique | PASS | 0 | 0 |  |
| category_rule not empty | PASS | >0 | 258 |  |
| budget.budget_id unique | PASS | 0 | 0 |  |
| budget not empty | PASS | >0 | 118784 |  |
| transaction.transaction_id unique | PASS | 0 | 0 |  |
| transaction not empty | PASS | >0 | 500000 |  |
| transfer_link.link_id unique | PASS | 0 | 0 |  |
| transfer_link not empty | PASS | >0 | 9514 |  |
| recurring_series.series_id unique | PASS | 0 | 0 |  |
| recurring_series not empty | PASS | >0 | 5609 |  |
| insight.insight_id unique | PASS | 0 | 0 |  |
| insight not empty | PASS | >0 | 59185 |  |
| entity_event.event_id unique | PASS | 0 | 0 |  |
| entity_event not empty | PASS | >0 | 3430 |  |
| FK account.user_id | PASS | 0 | 0 |  |
| FK merchant.default_category_code | PASS | 0 | 0 |  |
| FK merchant_alias.merchant_id | PASS | 0 | 0 |  |
| FK category_alias.alias_code | PASS | 0 | 0 |  |
| FK category_alias.canonical_code | PASS | 0 | 0 |  |
| FK category_rule.category_code | PASS | 0 | 0 |  |
| FK category_rule.merchant_id | PASS | 0 | 0 |  |
| FK category.parent_code | PASS | 0 | 0 |  |
| FK budget.user_id | PASS | 0 | 0 |  |
| FK budget.category_code | PASS | 0 | 0 |  |
| FK transaction.user_id | PASS | 0 | 0 |  |
| FK transaction.account_id | PASS | 0 | 0 |  |
| FK transaction.merchant_id | PASS | 0 | 0 |  |
| FK transaction.refund_of_txn_id | PASS | 0 | 0 |  |
| FK transfer_link.debit_txn_id | PASS | 0 | 0 |  |
| FK transfer_link.credit_txn_id | PASS | 0 | 0 |  |
| FK recurring_series.user_id | PASS | 0 | 0 |  |
| FK recurring_series.account_id | PASS | 0 | 0 |  |
| FK recurring_series.merchant_id | PASS | 0 | 0 |  |
| FK recurring_series.category_code | PASS | 0 | 0 |  |
| FK insight.user_id | PASS | 0 | 0 |  |
| user_id nomenclature | PASS | USR-000001 | checked all users |  |
| account_id nomenclature | PASS | ACC-<user-id>-01 | checked all accounts |  |
| transaction_id nomenclature | PASS | TXN-2026-00000001 | checked all transactions |  |
| budget_id nomenclature | PASS | BUD-<user-id>-2026-01-<category> | checked all budgets |  |
| series_id nomenclature | PASS | REC-000001 | checked detected series |  |
| transaction_id sequence | PASS | 1..N contiguous | 500000 |  |
| no ground truth columns in transaction input | PASS | [] | [] |  |
| enum user_profile.lifecycle_state | PASS | ['active', 'closed', 'dormant'] | 0 |  |
| enum user_profile.risk_tier | PASS | ['high', 'low', 'medium'] | 0 |  |
| enum user_profile.segment | PASS | ['plus', 'premium', 'standard'] | 0 |  |
| enum account.account_type | PASS | ['checking', 'credit_card', 'savings'] | 0 |  |
| enum account.status | PASS | ['active', 'closed', 'frozen'] | 0 |  |
| enum merchant.status | PASS | ['active', 'inactive'] | 0 |  |
| enum category.type | PASS | ['expense', 'income', 'refund', 'transfer'] | 0 |  |
| enum category_rule.match_type | PASS | ['contains', 'exact', 'regex'] | 0 |  |
| enum category_rule.match_field | PASS | ['descriptor', 'mcc', 'merchant'] | 0 |  |
| enum category_rule.status | PASS | ['active', 'retired'] | 0 |  |
| enum budget.status | PASS | ['active', 'closed', 'draft'] | 0 |  |
| enum transaction.channel | PASS | ['ach', 'atm', 'card', 'internal', 'online', 'pos'] | 0 |  |
| enum transaction.status | PASS | ['pending', 'posted', 'reversed'] | 0 |  |
| enum recurring_series.status | PASS | ['active', 'cancelled', 'ended', 'paused'] | 0 |  |
| enum recurring_series.cadence | PASS | ['annual', 'biweekly', 'monthly', 'quarterly', 'weekly'] | 0 |  |
| enum insight.insight_type | PASS | ['budget_variance_summary', 'data_quality_summary', 'monthly_spend_summary', 'recurring_summary'] | 0 |  |
| enum ground_truth.true_treatment | PASS | ['excluded', 'income', 'refund', 'spend', 'transfer'] | 0 |  |
| account opened after user creation | PASS | 0 | 0 |  |
| transaction posted after account open | PASS | 0 | 0 |  |
| transaction posted before account close | PASS | 0 | 0 |  |
| no activity after dormant/closed cutoff | PASS | 0 | 0 |  |
| refund date not before original | PASS | 0 | 0 |  |
| refund positive and bounded by original | PASS | 0 | 0 |  |
| transfer pairs same date and net zero | PASS | 0 | 0 |  |
| budget period aligns with year/month | PASS | 0 | 0 |  |
| budget start before end | PASS | 0 | 0 |  |
| recurring first occurrence before last | PASS | 0 | 0 |  |
| active recurring series has next date | PASS | 0 | 0 |  |
| ground-truth period uses local date | PASS | 0 | 0 |  |
| recurring posted counts reconcile | PASS | 0 | 0 |  |
| all required edge-case types present | PASS | ['budget_taxonomy_mismatch', 'recurring_series_skip', 'refund_treated_as_new_expense', 'timezone_boundary_date', 'transfer_double_count'] | [] |  |
| transfer_double_count labels match manifest | PASS | 75 | 75 |  |
| refund_treated_as_new_expense labels match manifest | PASS | 75 | 75 |  |
| timezone_boundary_date labels match manifest | PASS | 4505 | 4505 |  |
| every UTC/local month boundary case is labelled | PASS | 0 | 0 | 4506 boundary rows; 1 unlabelled. |
| timezone anomaly labels match manifest | PASS | 4505 | 4505 |  |
| recurring skip series labels match manifest | PASS | 30 | 30 |  |
| recurring skip expectations reconcile | PASS | 30 | 30 |  |
| budget mismatch labels match manifest impact | PASS | 2376 | 2376 |  |
| inactive budget categories are fully labelled | PASS | 2376 | 2376 | Intentional taxonomy mismatch cases are labelled in budget_labels.csv. |
| transfer treatment/category consistent | PASS | 19103 | 19103 |  |
| refund ground truth has positive amounts | PASS | 0 | 0 |  |
| transaction user matches account owner | PASS | 0 | 0 |  |
| refund owner matches original | PASS | 0 | 0 |  |
| refund account matches original | PASS | 0 | 0 |  |
| transfer legs have same owner | PASS | 0 | 0 |  |
| transfer legs use different accounts | PASS | 0 | 0 |  |
| recurring series owner matches account | PASS | 0 | 0 |  |
| event user references valid | PASS | 0 | 0 |  |
| event account references valid | PASS | 0 | 0 |  |
| lifecycle transition states valid | PASS | 0 | 0 |  |
| lifecycle event ordering valid | PASS | 0 | 0 |  |
| lifecycle terminal states match entities | PASS | 0 | 0 |  |
| no duplicate lifecycle event types per entity | PASS | 0 | 0 |  |
| account balances reconcile to ledger | PASS | 0 | 0 |  |
| ledger total equals sum of account balances | PASS | 25902413.44 | 25902413.44 |  |
| transaction amounts nonzero | PASS | 0 | 0 |  |
| posted transaction share | PASS | >=99% | 1.0 |  |
| decision coverage equals transactions | PASS | 500000 | 500000 |  |
| categorized coverage equals transactions | PASS | 500000 | 500000 |  |
| decision transaction uniqueness | PASS | 0 | 0 |  |
| every transaction has a decision | PASS | 0 | 0 |  |
| decision categories valid | PASS | 0 | 0 |  |
| decision confidence in [0,1] | PASS | 0 | 0 |  |
| predicted treatments valid | PASS | 0 | 0 |  |
| monthly spend reconciles to categorized ledger | PASS | 0 | 0 |  |
| every budget has comparison row | PASS | 0 | 0 |  |
| budget comparison amounts reconcile | PASS | 0 | 0 |  |
| budget comparison statuses valid | PASS | 0 | 0 |  |
| resolved budget categories are active | PASS | 0 | 0 |  |
| budget actuals reconcile to ledger | PASS | 0 | 0 |  |
| insight metrics reconcile to outputs | PASS | 0 | 0 |  |
| recurring insights reconcile to detected series | PASS | 0 | 0 |  |
| manifest seed present | PASS | int | int |  |
| manifest row count for transactions | PASS | 500000 | 500000 |  |
| manifest checksums verify | PASS | 0 | 0 | verified 47 files |
| row counts match manifest | PASS | 500000 | 500000 |  |
| ground truth covers every transaction | PASS | 500000 | 500000 |  |
| ground truth IDs valid | PASS | 0 | 0 |  |
| ground truth covers every budget | PASS | 0 | 0 |  |
| ground-truth categories valid | PASS | 0 | 0 |  |
| ground truth labels unique | PASS | 0 | 0 |  |
| no unintended exact duplicate transactions | PASS | 0 | 0 |  |
| all 12 months covered | PASS | 12 months | 12 |  |

## Known labelled exceptions

| Issue type | Rows / impact |
|---|---:|
| budget_taxonomy_mismatch | 2376 |
| recurring_series_skip | 30 |
| refund_treated_as_new_expense | 75 |
| timezone_boundary_date | 4505 |
| transfer_double_count | 75 |
