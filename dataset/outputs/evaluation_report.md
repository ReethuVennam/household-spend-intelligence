# Evaluation Report

Seed `20261022` | scale `full` | validation `PASS`

## Headline metrics

| Metric | Value |
|---|---:|
| Categorization accuracy | 95.12% |
| Categorization macro F1 | 0.9647 |
| Treatment accuracy | 99.96% |
| Local-period accuracy | 100.00% |
| UTC-period baseline | 99.10% |
| Recurring precision | 93.58% |
| Recurring recall | 100.00% |
| Recurring F1 | 0.9668 |
| Recurring skip recall | 100.00% |
| Budget taxonomy resolution | 100.00% |
| Exception handling score | 1.0000 |
| Fallback rate | 0.00% |
| Uncategorized rate | 4.92% |

## 1. Categorization

Accuracy **95.12%**, macro F1 **0.9647**, weighted F1 **0.9521** over 500,000 labelled transactions.

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| DINING | 78832 | 0.8934 | 0.9788 | 0.9342 |
| EDUCATION | 8325 | 1.0000 | 0.9792 | 0.9895 |
| ENTERTAINMENT | 25052 | 0.9998 | 0.9790 | 0.9893 |
| FEES | 8315 | 0.9998 | 0.9778 | 0.9886 |
| GROCERY | 87332 | 0.9997 | 0.9802 | 0.9899 |
| HEALTH | 29113 | 0.9999 | 0.9840 | 0.9918 |
| HOUSING_RENT | 9485 | 1.0000 | 1.0000 | 1.0000 |
| INCOME_OTHER | 10423 | 1.0000 | 0.9810 | 0.9904 |
| INCOME_SALARY | 10471 | 1.0000 | 1.0000 | 1.0000 |
| INSURANCE | 8357 | 0.9996 | 0.9809 | 0.9902 |
| OTHER | 16645 | 0.6760 | 1.0000 | 0.8067 |
| REFUND | 6075 | 1.0000 | 0.9877 | 0.9938 |
| SHOPPING | 53939 | 0.9997 | 0.8479 | 0.9176 |
| SUBSCRIPTION | 34559 | 0.8279 | 1.0000 | 0.9059 |
| TRANSFER | 19103 | 1.0000 | 1.0000 | 1.0000 |
| TRANSPORT | 54356 | 0.9999 | 0.8110 | 0.8956 |
| TRAVEL | 18669 | 0.9998 | 0.9828 | 0.9912 |
| UTILITIES | 20949 | 0.9999 | 0.9787 | 0.9891 |

Top confusions:

| True | Predicted | Count |
|---|---|---:|
| TRANSPORT | DINING | 9193 |
| SHOPPING | SUBSCRIPTION | 7181 |
| GROCERY | OTHER | 1727 |
| DINING | OTHER | 1671 |
| TRANSPORT | OTHER | 1079 |
| SHOPPING | OTHER | 1022 |
| ENTERTAINMENT | OTHER | 526 |
| HEALTH | OTHER | 467 |
| UTILITIES | OTHER | 447 |
| TRAVEL | OTHER | 321 |
| INCOME_OTHER | OTHER | 198 |
| FEES | OTHER | 185 |
| EDUCATION | OTHER | 173 |
| INSURANCE | OTHER | 160 |
| REFUND | GROCERY | 23 |

## 2. Transfers, refunds, and period assignment

- Transfer transactions: **19,103** (absolute amount **$15,206,047.00**)
- Refund transactions: **6,075** (credit amount **$458,093.04**)
- Strict net spend: **$54,015,523.30**
- Naive overstatement if transfer legs and refunds are treated as new spend: **$16,122,233.08**
- Transfers handled as transfers: **19,103**
- Refunds handled as refunds: **6,075**
- UTC/local month boundary cases: **4,506**; local-period accuracy **100.00%**, UTC baseline **99.10%**.

## 3. Recurring detection

Ground truth series **5,253**, detectable **5,249**, detected **5,609**, matched **5,249**.

Precision **93.58%**, recall **100.00%**, F1 **0.9668**, false positives **360**, false negatives **0**.

- Category accuracy on matched series: **1.0**
- Expected-amount MAPE: **0.0003**
- Next-date median absolute error: **0.0 days**
- Skipped-series recall: **100.00%** (30/30)
- Skipped-series precision: **100.00%** (false skip flags 0)
- Ground-truth posted-occurrence support: **99.99%**

## 4. Budget comparison

- Budgets: **118,784**; comparison rows: **118,784**
- Total budget: **$56,369,145.00**; actual: **$46,580,210.96**; variance: **$9,788,934.04**
- Status counts: **{'near': 5105, 'over': 28286, 'under': 85393}**
- Taxonomy-mismatch resolution accuracy: **100.00%**
- Naive direct joins that would falsely appear under budget: **2,376** rows / **$1,137,710.00**

## 5. Reconciliation

- Ledger net total: **$25,902,413.44**
- Account balance total: **$25,902,413.44** (delta $0.00)
- Strict spend via categorized ledger: **$54,015,523.30**
- Monthly spend rollup: **$54,015,523.30** (delta $0.00)
- Rows: **500,000**, profiles: **1,000**, months: **12**

## 6. Labelled exceptions

| Issue | Labelled | Treatment consistent | Category consistent | Amount |
|---|---:|---:|---:|---:|
| transfer_double_count | 75 | 75 | 75 | $60,119.94 |
| refund_treated_as_new_expense | 75 | 75 | 0 | $4,682.45 |
| timezone_boundary_date | 4505 | 4503 | 4256 | $536,125.43 |
| recurring_series_skip | series 30 | flags 30 | skip recall 1.0 | - |
| budget_taxonomy_mismatch | 2376 | resolved 2376 | unresolved 0 | $1,137,710.00 |

## 7. Distributions

| Month | Transactions | Gross debits | Credits |
|---|---:|---:|---:|
| 2026-01 | 39,829 | $4,269,109.85 | $7,216,993.64 |
| 2026-02 | 36,195 | $3,866,426.40 | $7,246,512.48 |
| 2026-03 | 40,678 | $4,474,039.71 | $7,326,996.20 |
| 2026-04 | 41,164 | $4,720,023.96 | $7,278,747.18 |
| 2026-05 | 43,021 | $5,215,849.62 | $7,351,844.56 |
| 2026-06 | 42,641 | $5,982,870.98 | $7,523,193.07 |
| 2026-07 | 44,252 | $6,566,864.34 | $7,489,963.69 |
| 2026-08 | 44,664 | $6,380,620.39 | $7,555,318.71 |
| 2026-09 | 40,144 | $4,887,389.81 | $7,369,981.68 |
| 2026-10 | 40,821 | $4,878,437.50 | $7,245,596.72 |
| 2026-11 | 41,551 | $5,024,777.91 | $7,252,953.91 |
| 2026-12 | 45,040 | $5,961,273.29 | $7,271,995.36 |

### Amount distribution

| Statistic | Signed amount (USD) |
|---|---:|
| Mean | 51.80 |
| Median | -39.71 |
| P05 | -560.73 |
| P95 | 342.02 |

### True category distribution

| Category | Transactions |
|---|---:|
| DINING | 78,832 |
| EDUCATION | 8,325 |
| ENTERTAINMENT | 25,052 |
| FEES | 8,315 |
| GROCERY | 87,332 |
| HEALTH | 29,113 |
| HOUSING_RENT | 9,485 |
| INCOME_OTHER | 10,423 |
| INCOME_SALARY | 10,471 |
| INSURANCE | 8,357 |
| OTHER | 16,645 |
| REFUND | 6,075 |
| SHOPPING | 53,939 |
| SUBSCRIPTION | 34,559 |
| TRANSFER | 19,103 |
| TRANSPORT | 54,356 |
| TRAVEL | 18,669 |
| UTILITIES | 20,949 |

### Treatment distribution

| Treatment | Transactions |
|---|---:|
| income | 20,894 |
| refund | 6,075 |
| spend | 453,928 |
| transfer | 19,103 |

### Ground-truth issue distribution

| Issue type | Transactions |
|---|---:|
| none | 495,345 |
| refund_treated_as_new_expense | 75 |
| timezone_boundary_date | 4,505 |
| transfer_double_count | 75 |

---

Notes:
- The pipeline never reads ground_truth/. It is joined only in this evaluation step.
- Strict net spend excludes transfers, offsets refunds, and assigns periods from local transaction dates.
- Naive overstatement is a diagnostic: both transfer legs and refunds are treated as new spending.
- Recurring detection uses monthly gap and amount stability; labels are generated independently from the detector.
- Budget resolution maps deprecated taxonomy codes through category_alias before comparison.
- A boundary-case row that also carries a primary refund/transfer anomaly keeps that primary transaction label; all boundary rows still have ground-truth labels.
