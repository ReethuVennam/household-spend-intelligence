# Generated Dataset

Seed: `20261022`  
Scale: `full`  
Generated at: `2027-01-15T00:00:00Z`  
Schema version: `1.0.0`  
Generator version: `1.0.0`  
Project version: `1.0.0`

## Counts

| Entity | Rows |
|---|---:|
| UserProfile | 1000 |
| Account | 2335 |
| Merchant | 82 |
| Category | 25 |
| CategoryRule | 258 |
| Budget | 118784 |
| Transaction | 500000 |
| TransferLink | 9514 |
| RecurringSeries (detected) | 5609 |
| Insight | 59185 |
| EntityEvent | 3430 |

## Labelled exceptions

| Issue type | Rows / impact |
|---|---:|
| budget_taxonomy_mismatch | 2376 |
| recurring_series_skip | 30 |
| refund_treated_as_new_expense | 75 |
| timezone_boundary_date | 4505 |
| transfer_double_count | 75 |

Ground truth is isolated under `ground_truth/` and is never joined into input features.

## Layout

- `data/` CSV entity exports
- `data/json/` JSON and JSONL.GZ exports
- `data/sql/` SQLite-compatible DDL and seed inserts
- `ground_truth/` labels and anomaly manifest
- `outputs/` reference solution outputs
- `metadata/` manifest and provenance
- `validation/` validation output
