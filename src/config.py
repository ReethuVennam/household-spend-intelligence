from __future__ import annotations

from pathlib import Path

SEED = 20261022
YEAR = 2026
MONTHS = list(range(1, 13))
PROJECT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
GENERATOR_VERSION = "1.0.0"
FIXED_GENERATED_AT = "2027-01-15T00:00:00Z"
FIXED_EVENT_AT = "2026-12-31T23:59:59Z"
FORMULA_VERSION = "2026.1"

SCALES: dict[str, dict[str, int]] = {
    "mini": {"profiles": 20, "transactions": 2000},
    "starter": {"profiles": 100, "transactions": 50000},
    "full": {"profiles": 1000, "transactions": 500000},
}

MONTH_DAYS = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}

MONTH_LABELS = {m: f"{YEAR}-{m:02d}" for m in MONTHS}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = PROJECT_ROOT / "dataset"

USER_STATES = ["active", "dormant", "closed"]
ACCOUNT_TYPES = ["checking", "savings", "credit_card"]
ACCOUNT_STATES = ["active", "frozen", "closed"]
TRANSACTION_STATES = ["posted", "pending", "reversed"]
CATEGORY_TYPES = ["expense", "income", "transfer", "refund"]
CHANNELS = ["card", "ach", "online", "pos", "atm", "internal"]
BUDGET_STATES = ["draft", "active", "closed"]
SERIES_STATES = ["active", "paused", "cancelled", "ended"]
INSIGHT_TYPES = [
    "monthly_spend_summary",
    "budget_variance_summary",
    "recurring_summary",
    "data_quality_summary",
]
TREATMENTS = ["spend", "income", "transfer", "refund", "excluded"]

INCOME_BANDS = [
    ("25k-50k", 37500.0),
    ("50k-75k", 62500.0),
    ("75k-100k", 87500.0),
    ("100k-150k", 125000.0),
    ("150k-250k", 200000.0),
]
INCOME_BAND_WEIGHTS = [0.15, 0.30, 0.30, 0.20, 0.05]

RISK_TIERS = ["low", "medium", "high"]
SEGMENTS = ["standard", "plus", "premium"]
TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Phoenix",
    "America/Anchorage",
    "Pacific/Honolulu",
]
TIMEZONE_WEIGHTS = [0.24, 0.20, 0.10, 0.22, 0.07, 0.03, 0.04]
STATES = [
    ("NY", "New York"), ("CA", "Los Angeles"), ("IL", "Chicago"),
    ("TX", "Austin"), ("WA", "Seattle"), ("CO", "Denver"),
    ("AZ", "Phoenix"), ("FL", "Miami"), ("MA", "Boston"),
    ("OR", "Portland"), ("GA", "Atlanta"), ("NC", "Charlotte"),
]
FIRST_NAMES = [
    "Avery", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Cameron",
    "Drew", "Quinn", "Skyler", "Parker", "Reese", "Rowan", "Sage", "Emerson",
    "Hayden", "Kendall", "Marlow", "Blake", "Dakota", "Elliot", "Finley", "Harper",
    "Indigo", "Jesse", "Kai", "Lane", "Micah", "Noor", "Oakley", "Peyton",
    "Remy", "Shiloh", "Tatum", "Val", "Wren", "Zion", "Arden", "Bay",
]
LAST_NAMES = [
    "Chen", "Patel", "Nguyen", "Garcia", "Kim", "Johnson", "Brown", "Davis",
    "Martinez", "Wilson", "Anderson", "Thomas", "Moore", "Jackson", "White",
    "Harris", "Clark", "Lewis", "Walker", "Hall", "Young", "King", "Wright",
    "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Nelson", "Carter",
    "Mitchell", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans",
    "Edwards", "Collins",
]

CITY_CODE = {
    "NY": "NYC", "CA": "LAX", "IL": "CHI", "TX": "AUS", "WA": "SEA",
    "CO": "DEN", "AZ": "PHX", "FL": "MIA", "MA": "BOS", "OR": "PDX",
    "GA": "ATL", "NC": "CLT",
}

SEVERITY_ORDER = {"PASS": 0, "WARN": 1, "FAIL": 2}
