from __future__ import annotations

import math
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .analytics import build_reference_outputs
from .config import (
    CITY_CODE,
    FIRST_NAMES,
    FIXED_GENERATED_AT,
    GENERATOR_VERSION,
    INCOME_BAND_WEIGHTS,
    INCOME_BANDS,
    LAST_NAMES,
    MONTH_DAYS,
    PROJECT_VERSION,
    SCALES,
    SCHEMA_VERSION,
    SEED,
    STATES,
    TIMEZONE_WEIGHTS,
    TIMEZONES,
    YEAR,
)
from .io_utils import write_dataset
from .rules import build_category_rules
from .taxonomy import (
    AMOUNT_PARAMS,
    BUDGET_CATEGORY_SETS,
    BUDGET_SHARES,
    CATEGORIES,
    CATEGORY_MERCHANTS,
    CATEGORY_SEASONALITY,
    LEGACY_CATEGORY_ALIASES,
    MERCHANTS,
)

REVERSED_LEGACY = {v[0]: k for k, v in LEGACY_CATEGORY_ALIASES.items()}

TX_FIELDS = [
    "transaction_id",
    "user_id",
    "account_id",
    "transaction_date",
    "posted_at_utc",
    "merchant_id",
    "descriptor",
    "amount_usd",
    "currency",
    "mcc",
    "channel",
    "status",
    "refund_of_txn_id",
]

INTERNAL_FIELDS = [
    "_key",
    "_seq",
    "_source",
    "_true_category",
    "_true_treatment",
    "_expected_period",
    "_is_recurring",
    "_true_series_id",
    "_issue_type",
    "_issue_detail",
    "_refund_key",
    "_link_key",
    "_related_key",
    "_timezone",
    "local_time",
]

FILLER_MIX = {
    "GROCERY": 21.0,
    "DINING": 19.0,
    "TRANSPORT": 13.0,
    "SHOPPING": 13.0,
    "ENTERTAINMENT": 6.0,
    "HEALTH": 6.0,
    "UTILITIES": 5.0,
    "SUBSCRIPTION": 0.0,
    "TRAVEL": 4.5,
    "EDUCATION": 2.0,
    "FEES": 2.0,
    "INSURANCE": 2.0,
    "OTHER": 4.0,
    "INCOME_OTHER": 2.5,
}

DOW_WEIGHTS = {
    "GROCERY": [0.90, 0.85, 0.90, 0.95, 1.05, 1.25, 1.10],
    "DINING": [0.80, 0.80, 0.85, 0.90, 1.10, 1.35, 1.20],
    "SHOPPING": [0.90, 0.90, 0.95, 1.00, 1.05, 1.20, 1.10],
    "TRAVEL": [0.85, 0.85, 0.90, 1.00, 1.15, 1.25, 1.15],
    "ENTERTAINMENT": [0.70, 0.70, 0.75, 0.80, 1.10, 1.40, 1.30],
    "TRANSPORT": [1.15, 1.15, 1.10, 1.10, 1.05, 0.80, 0.70],
}

HOUR_WEIGHTS = {
    "DINING": ([8, 11, 12, 13, 17, 18, 19, 20, 21], [0.04, 0.09, 0.18, 0.12, 0.12, 0.16, 0.14, 0.10, 0.05]),
    "GROCERY": ([9, 10, 11, 15, 16, 17, 18, 19], [0.07, 0.12, 0.15, 0.10, 0.15, 0.18, 0.15, 0.08]),
    "TRANSPORT": ([7, 8, 9, 12, 17, 18, 19, 22], [0.12, 0.20, 0.12, 0.08, 0.16, 0.16, 0.08, 0.08]),
    "SHOPPING": ([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], [0.06, 0.08, 0.10, 0.10, 0.10, 0.10, 0.12, 0.12, 0.10, 0.07, 0.05]),
    "DEFAULT": ([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], [0.04, 0.06, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.10]),
}

SUBSCRIPTION_AMOUNTS = {
    "netflix": 15.49,
    "spotify": 11.99,
    "disney_plus": 13.99,
    "icloud": 2.99,
    "amazon_prime": 14.99,
    "nytimes": 17.00,
    "cloud_storage": 9.99,
    "kindle_unltd": 11.99,
    "gym_fit": 39.00,
}


def _round2(x: float) -> float:
    return float(round(float(x) + 1e-9, 2))


def _id_user(n: int) -> str:
    return f"USR-{n:06d}"


def _id_merchant(n: int) -> str:
    return f"MER-{n:06d}"


def _month_end(year: int, month: int) -> date:
    return date(year, month, MONTH_DAYS[month])


def _safe_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, MONTH_DAYS[month]))


def _pick_dates(rng: np.random.Generator, n: int, weights: np.ndarray, cap_doy: np.ndarray | None = None) -> np.ndarray:
    days = np.arange(365)
    probs = weights / weights.sum()
    out = rng.choice(days, size=n, p=probs)
    if cap_doy is None:
        return out
    for cap in np.unique(cap_doy):
        if cap >= 364:
            continue
        mask = cap_doy == cap
        local_days = np.arange(int(cap) + 1)
        local_probs = weights[: len(local_days)] / weights[: len(local_days)].sum()
        out[mask] = rng.choice(local_days, size=int(mask.sum()), p=local_probs)
    return out


def _descriptor_time(rng: np.random.Generator, category: str, n: int) -> list[str]:
    hours, weights = HOUR_WEIGHTS.get(category, HOUR_WEIGHTS["DEFAULT"])
    h = rng.choice(hours, size=n, p=np.array(weights) / np.sum(weights))
    minute = rng.integers(0, 60, size=n)
    second = rng.integers(0, 60, size=n)
    return [f"{int(h[i]):02d}:{int(minute[i]):02d}:{int(second[i]):02d}" for i in range(n)]


def _build_users(rng: np.random.Generator, n_profiles: int) -> tuple[pd.DataFrame, dict[str, dict]]:
    rows = []
    meta = {}
    band_idx = rng.choice(len(INCOME_BANDS), size=n_profiles, p=np.array(INCOME_BAND_WEIGHTS) / np.sum(INCOME_BAND_WEIGHTS))
    state_idx = rng.integers(0, len(STATES), size=n_profiles)
    tz_idx = rng.choice(len(TIMEZONES), size=n_profiles, p=np.array(TIMEZONE_WEIGHTS) / np.sum(TIMEZONE_WEIGHTS))
    household = rng.integers(1, 7, size=n_profiles)
    credit = np.clip(rng.normal(715, 78, size=n_profiles), 300, 850).round().astype(int)
    life = rng.choice(["active", "dormant", "closed"], size=n_profiles, p=[0.96, 0.02, 0.02])
    for i in range(n_profiles):
        uid = _id_user(i + 1)
        first = FIRST_NAMES[int(rng.integers(0, len(FIRST_NAMES)))]
        last = LAST_NAMES[int(rng.integers(0, len(LAST_NAMES)))]
        band_label, band_mid = INCOME_BANDS[int(band_idx[i])]
        annual = band_mid * float(rng.uniform(0.90, 1.10))
        state_code, city = STATES[int(state_idx[i])]
        tz = TIMEZONES[int(tz_idx[i])]
        created_day = int(rng.integers(0, 2350))
        created = date(2019, 1, 1) + timedelta(days=created_day)
        if created > date(2025, 12, 1):
            created = date(2025, 12, 1)
        if created < date(2019, 1, 1):
            created = date(2019, 1, 1)
        state = str(life[i])
        if state == "closed":
            active_end = date(YEAR, 9, 30)
        elif state == "dormant":
            active_end = date(YEAR, 8, 31)
        else:
            active_end = date(YEAR, 12, 31)
        score = int(credit[i])
        if score >= 740:
            risk = "low"
        elif score >= 660:
            risk = "medium"
        else:
            risk = "high"
        if annual >= 125000:
            segment = "premium"
        elif annual >= 75000:
            segment = "plus"
        else:
            segment = "standard"
        updated = date(YEAR, 9, 1) if state == "dormant" else (date(YEAR, 10, 2) if state == "closed" else created)
        rows.append(
            {
                "user_id": uid,
                "display_name": f"{first} {last}",
                "email": f"user{i + 1:06d}@example.test",
                "country": "US",
                "state_code": state_code,
                "city": city,
                "postal_code": f"{int(state_idx[i]) + 10}{int(rng.integers(100, 999)):03d}",
                "timezone": tz,
                "household_size": int(household[i]),
                "income_band": band_label,
                "annual_income_usd": _round2(annual),
                "credit_score": score,
                "risk_tier": risk,
                "segment": segment,
                "lifecycle_state": state,
                "created_at": f"{created.isoformat()}T08:00:00Z",
                "updated_at": f"{updated.isoformat()}T08:00:00Z",
                "effective_from": f"{created.isoformat()}T08:00:00Z",
                "effective_to": "",
                "is_synthetic": True,
                "data_origin": "synthetic_generator",
            }
        )
        meta[uid] = {
            "annual_income": annual,
            "monthly_income": annual / 12.0,
            "band_idx": int(band_idx[i]),
            "household": int(household[i]),
            "active_end": active_end,
            "timezone": tz,
            "state_code": state_code,
            "city": city,
            "lifecycle_state": state,
            "credit_score": score,
        }
    return pd.DataFrame(rows), meta


def _build_accounts(
    rng: np.random.Generator,
    users: pd.DataFrame,
    user_meta: dict[str, dict],
) -> tuple[pd.DataFrame, dict[str, dict]]:
    rows = []
    accounts: dict[str, dict] = {}
    for user in users.itertuples(index=False):
        uid = user.user_id
        meta = user_meta[uid]
        created = date.fromisoformat(user.created_at[:10])
        base_open = created + timedelta(days=int(rng.integers(30, 240)))
        if base_open > date(2025, 11, 1):
            base_open = date(2025, 11, 1)
        checking_id = f"ACC-{uid}-01"
        closed_at = ""
        status = "active"
        if meta["lifecycle_state"] == "closed":
            status = "closed"
            closed_at = f"{YEAR}-10-02T00:00:00Z"
        rows.append(
            {
                "account_id": checking_id,
                "user_id": uid,
                "account_type": "checking",
                "nickname": "Everyday Checking",
                "currency": "USD",
                "status": status,
                "opened_at": f"{base_open.isoformat()}T09:00:00Z",
                "closed_at": closed_at,
                "opening_balance_usd": 0.0,
                "current_balance_usd": 0.0,
                "credit_limit_usd": "",
                "is_primary": True,
            }
        )
        accounts[uid] = {
            "checking": checking_id,
            "savings": "",
            "credit": "",
            "savings_open": None,
            "credit_open": None,
            "closed_at": closed_at,
            "active_end": meta["active_end"],
        }
        if rng.random() < 0.65:
            savings_open = base_open + timedelta(days=int(rng.integers(60, 900)))
            if savings_open > date(2025, 12, 1):
                savings_open = date(2025, 12, 1)
        else:
            pick = rng.random()
            savings_open = date(YEAR, 6, 1) if pick < 0.58 else date(YEAR, 9, 1)
        if savings_open > meta["active_end"]:
            savings_open = meta["active_end"] - timedelta(days=20)
        savings_id = f"ACC-{uid}-02"
        rows.append(
            {
                "account_id": savings_id,
                "user_id": uid,
                "account_type": "savings",
                "nickname": "Savings",
                "currency": "USD",
                "status": "closed" if meta["lifecycle_state"] == "closed" else "active",
                "opened_at": f"{savings_open.isoformat()}T09:00:00Z",
                "closed_at": closed_at,
                "opening_balance_usd": 0.0,
                "current_balance_usd": 0.0,
                "credit_limit_usd": "",
                "is_primary": False,
            }
        )
        accounts[uid]["savings"] = savings_id
        accounts[uid]["savings_open"] = savings_open
        if rng.random() < 0.32:
            credit_open = base_open + timedelta(days=int(rng.integers(100, 1200)))
            if credit_open > date(2025, 10, 1):
                credit_open = date(2025, 10, 1)
            credit_id = f"ACC-{uid}-03"
            limit = float(rng.choice([1000, 2000, 3000, 5000, 8000, 12000]))
            rows.append(
                {
                    "account_id": credit_id,
                    "user_id": uid,
                    "account_type": "credit_card",
                    "nickname": "Rewards Card",
                    "currency": "USD",
                    "status": "closed" if meta["lifecycle_state"] == "closed" else "active",
                    "opened_at": f"{credit_open.isoformat()}T09:00:00Z",
                    "closed_at": closed_at,
                    "opening_balance_usd": 0.0,
                    "current_balance_usd": 0.0,
                    "credit_limit_usd": limit,
                    "is_primary": False,
                }
            )
            accounts[uid]["credit"] = credit_id
            accounts[uid]["credit_open"] = credit_open
    return pd.DataFrame(rows), accounts


def _build_merchants(rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict]]:
    rows = []
    alias_rows = []
    internal = {}
    alias_seq = 1
    for i, item in enumerate(MERCHANTS):
        mid = _id_merchant(i + 1)
        aliases = list(dict.fromkeys(item["aliases"]))
        variants = set()
        for alias in aliases:
            variants.add(alias)
            variants.add(f"{alias} #{int(rng.integers(100, 999)):03d}")
            variants.add(f"{alias} {CITY_CODE[STATES[int(rng.integers(0, len(STATES)))][0]]}")
            if item["online"] > 0:
                variants.add(f"{alias}.COM")
                variants.add(f"{alias} ONLINE")
        variants = sorted(variants)
        internal[item["key"]] = {
            "merchant_id": mid,
            "name": item["name"],
            "category": item["category"],
            "aliases": aliases,
            "variants": variants,
            "mcc": item["mcc"],
            "online": item["online"],
            "subscription": item["subscription"],
            "weight": item["weight"],
            "bias": item["bias"],
        }
        rows.append(
            {
                "merchant_id": mid,
                "canonical_name": item["name"],
                "default_category_code": item["category"],
                "mcc": item["mcc"],
                "country": "US",
                "city": "Multiple",
                "online_capable": item["online"] > 0,
                "subscription_capable": item["subscription"],
                "status": "active",
                "effective_from": "2025-01-01",
                "effective_to": "",
            }
        )
        for j, alias in enumerate(aliases):
            alias_rows.append(
                {
                    "alias_id": f"MAL-{alias_seq:06d}",
                    "merchant_id": mid,
                    "alias_text": alias,
                    "is_primary": j == 0,
                    "effective_from": "2025-01-01",
                    "effective_to": "",
                }
            )
            alias_seq += 1
    return pd.DataFrame(rows), pd.DataFrame(alias_rows), internal


def _build_categories() -> tuple[pd.DataFrame, pd.DataFrame]:
    cats = pd.DataFrame(CATEGORIES)
    cats = cats.rename(columns={"parent": "parent_code", "budgetable": "is_budgetable", "active": "is_active"})
    cats.insert(0, "category_code", cats.pop("code"))
    cats["taxonomy_version"] = "2026.1"
    cats["effective_from"] = "2025-01-01"
    cats["effective_to"] = np.where(cats["is_active"], "", "2025-12-31")
    cats = cats[
        [
            "category_code",
            "name",
            "type",
            "parent_code",
            "is_budgetable",
            "is_active",
            "taxonomy_version",
            "effective_from",
            "effective_to",
        ]
    ]
    alias_rows = []
    for i, (legacy, (canonical, reason)) in enumerate(LEGACY_CATEGORY_ALIASES.items(), start=1):
        alias_rows.append(
            {
                "alias_id": f"CAT-{i:06d}",
                "alias_code": legacy,
                "canonical_code": canonical,
                "effective_from": "2026-01-01",
                "effective_to": "",
                "status": "deprecated",
                "reason": reason,
            }
        )
    return cats, pd.DataFrame(alias_rows)


def _build_series(
    rng: np.random.Generator,
    users: pd.DataFrame,
    user_meta: dict[str, dict],
    accounts: dict[str, dict],
    merchant_internal: dict[str, dict],
    n_skips: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    series: list[dict] = []
    series_seq = 1
    salary_keys = [k for k in ["acme_corp", "globex_llc", "initech", "umbrella"]]
    rent_keys = ["harbor_property", "oakwood_apts", "skyline_rentals"]
    sub_keys = ["netflix", "spotify", "disney_plus", "icloud", "amazon_prime", "nytimes", "cloud_storage", "kindle_unltd", "gym_fit"]
    for user in users.itertuples(index=False):
        uid = user.user_id
        meta = user_meta[uid]
        end_month = meta["active_end"].month
        acc = accounts[uid]
        if end_month < 1:
            continue
        if rng.random() < 0.90:
            key = str(rng.choice(salary_keys))
            amount = meta["monthly_income"] * float(rng.uniform(0.94, 1.04))
            day = int(rng.integers(25, 29))
            raise_flag = rng.random() < 0.14
            series.append(
                {
                    "true_series_id": f"TRU-{series_seq:06d}",
                    "user_id": uid,
                    "account_id": acc["checking"],
                    "merchant_key": key,
                    "merchant_id": merchant_internal[key]["merchant_id"],
                    "category_code": "INCOME_SALARY",
                    "amount": amount,
                    "day": day,
                    "start_month": 1,
                    "end_month": end_month,
                    "status": "active" if end_month == 12 else "cancelled",
                    "raise_flag": raise_flag,
                    "descriptor": f"{merchant_internal[key]['aliases'][0]} PPD {series_seq:06d}",
                    "hour": 6,
                    "minute": int(rng.integers(0, 60)),
                    "skip_month": None,
                    "issue_type": "",
                    "issue_detail": "",
                }
            )
            series_seq += 1
        if rng.random() < 0.80:
            key = str(rng.choice(rent_keys))
            amount = meta["monthly_income"] * float(rng.uniform(0.20, 0.30))
            day = int(rng.integers(1, 6))
            series.append(
                {
                    "true_series_id": f"TRU-{series_seq:06d}",
                    "user_id": uid,
                    "account_id": acc["checking"],
                    "merchant_key": key,
                    "merchant_id": merchant_internal[key]["merchant_id"],
                    "category_code": "HOUSING_RENT",
                    "amount": amount,
                    "day": day,
                    "start_month": 1,
                    "end_month": end_month,
                    "status": "active" if end_month == 12 else "cancelled",
                    "raise_flag": False,
                    "descriptor": f"{merchant_internal[key]['aliases'][0]} {series_seq:06d}",
                    "hour": 7,
                    "minute": int(rng.integers(0, 60)),
                    "skip_month": None,
                    "issue_type": "",
                    "issue_detail": "",
                }
            )
            series_seq += 1
        n_subs = int(rng.integers(2, 6))
        chosen = list(rng.choice(sub_keys, size=min(n_subs, len(sub_keys)), replace=False))
        for key in chosen:
            base = SUBSCRIPTION_AMOUNTS[key]
            amount = base * float(rng.uniform(0.95, 1.05))
            day = int(rng.integers(1, 29))
            start_month = 1 if rng.random() < 0.88 else int(rng.integers(2, 9))
            if start_month > end_month:
                start_month = 1
            cancelled = rng.random() < 0.13
            end_sub = end_month if not cancelled else max(start_month + 2, int(rng.integers(5, 12)))
            end_sub = min(end_sub, end_month)
            status = "cancelled" if end_sub < 12 else ("active" if end_month == 12 else "cancelled")
            category = "HEALTH" if key == "gym_fit" else "SUBSCRIPTION"
            series.append(
                {
                    "true_series_id": f"TRU-{series_seq:06d}",
                    "user_id": uid,
                    "account_id": acc["checking"],
                    "merchant_key": key,
                    "merchant_id": merchant_internal[key]["merchant_id"],
                    "category_code": category,
                    "amount": amount,
                    "day": day,
                    "start_month": start_month,
                    "end_month": end_sub,
                    "status": status,
                    "raise_flag": False,
                    "descriptor": f"{merchant_internal[key]['aliases'][0]} {series_seq:06d}",
                    "hour": 2,
                    "minute": int(rng.integers(0, 60)),
                    "skip_month": None,
                    "issue_type": "",
                    "issue_detail": "",
                }
            )
            series_seq += 1

    eligible = [i for i, s in enumerate(series) if s["end_month"] - s["start_month"] >= 8]
    skip_indices = []
    if eligible and n_skips > 0:
        skip_indices = list(rng.choice(eligible, size=min(n_skips, len(eligible)), replace=False))
    for i in skip_indices:
        s = series[i]
        lo = max(s["start_month"] + 2, 3)
        hi = max(lo, s["end_month"] - 2)
        s["skip_month"] = int(rng.integers(lo, hi + 1))
        s["issue_type"] = "recurring_series_skip"
        s["issue_detail"] = f"Injected missing occurrence in {YEAR}-{s['skip_month']:02d}."

    tx_rows: list[dict] = []
    gt_series: list[dict] = []
    expectations: list[dict] = []
    anomalies: list[dict] = []
    seq = 0
    for s in series:
        posted_dates = []
        for month in range(s["start_month"], s["end_month"] + 1):
            expected_date = _safe_day(YEAR, month, s["day"])
            amount = s["amount"]
            if s["raise_flag"] and month >= 7:
                amount *= 1.03
            amount = _round2(amount)
            if s["skip_month"] == month:
                expectations.append(
                    {
                        "true_series_id": s["true_series_id"],
                        "occurrence_date": expected_date.isoformat(),
                        "expected_amount_usd": amount,
                        "outcome": "skipped",
                        "reason": "injected_recurring_skip",
                    }
                )
                continue
            posted_dates.append(expected_date)
            seq += 1
            signed = amount if s["category_code"] == "INCOME_SALARY" else -amount
            tx_rows.append(
                {
                    "_key": f"REC{seq:08d}",
                    "_seq": seq,
                    "_source": "recurring",
                    "_true_category": s["category_code"],
                    "_true_treatment": "income" if signed > 0 else "spend",
                    "_expected_period": expected_date.strftime("%Y-%m"),
                    "_is_recurring": True,
                    "_true_series_id": s["true_series_id"],
                    "_issue_type": "",
                    "_issue_detail": "",
                    "_refund_key": "",
                    "_link_key": "",
                    "_related_key": "",
                    "_timezone": user_meta[s["user_id"]]["timezone"],
                    "user_id": s["user_id"],
                    "account_id": s["account_id"],
                    "merchant_id": s["merchant_id"],
                    "descriptor": s["descriptor"],
                    "amount_usd": _round2(signed),
                    "currency": "USD",
                    "mcc": merchant_internal[s["merchant_key"]]["mcc"],
                    "channel": "ach" if s["category_code"] in {"INCOME_SALARY", "HOUSING_RENT"} else "online",
                    "status": "posted",
                    "transaction_date": expected_date.isoformat(),
                    "local_time": f"{s['hour']:02d}:{s['minute']:02d}:00",
                }
            )
            expectations.append(
                {
                    "true_series_id": s["true_series_id"],
                    "occurrence_date": expected_date.isoformat(),
                    "expected_amount_usd": amount,
                    "outcome": "posted",
                    "reason": "",
                }
            )
        first = posted_dates[0] if posted_dates else _safe_day(YEAR, s["start_month"], s["day"])
        last = posted_dates[-1] if posted_dates else first
        next_date = ""
        if s["status"] == "active":
            if last.month < 12:
                next_date = _safe_day(YEAR, last.month + 1, s["day"]).isoformat()
            else:
                next_date = _safe_day(YEAR + 1, 1, s["day"]).isoformat()
        gt_series.append(
            {
                "true_series_id": s["true_series_id"],
                "user_id": s["user_id"],
                "account_id": s["account_id"],
                "merchant_id": s["merchant_id"],
                "merchant_key": s["merchant_key"],
                "category_code": s["category_code"],
                "cadence": "monthly",
                "expected_amount_usd": _round2(s["amount"]),
                "start_date": first.isoformat(),
                "end_date": last.isoformat(),
                "planned_occurrences": s["end_month"] - s["start_month"] + 1,
                "posted_occurrences": len(posted_dates),
                "skipped_occurrences": 1 if s["skip_month"] is not None else 0,
                "next_expected_date": next_date,
                "status": s["status"],
                "issue_type": s["issue_type"],
                "issue_detail": s["issue_detail"],
            }
        )
        if s["skip_month"] is not None:
            anomalies.append(
                {
                    "issue_type": "recurring_series_skip",
                    "entity_type": "recurring_series",
                    "entity_id": s["true_series_id"],
                    "related_entity_id": s["merchant_id"],
                    "observed_behavior": f"Expected monthly occurrence missing in {YEAR}-{s['skip_month']:02d}.",
                    "expected_resolution": "Use gap detection and report the missing occurrence; do not silently shift the series.",
                    "impact_count": 1,
                    "severity": "medium",
                }
            )
    return tx_rows, gt_series, expectations, anomalies


def _build_budgets(
    rng: np.random.Generator,
    users: pd.DataFrame,
    user_meta: dict[str, dict],
    gt_series: list[dict],
    n_mismatch: int,
) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    rent_users = {row["user_id"] for row in gt_series if row["category_code"] == "HOUSING_RENT"}
    rows = []
    for user in users.itertuples(index=False):
        uid = user.user_id
        meta = user_meta[uid]
        end_month = meta["active_end"].month
        base_set = BUDGET_CATEGORY_SETS[int(uid[-6:]) % len(BUDGET_CATEGORY_SETS)]
        categories = list(base_set)
        if uid not in rent_users and "HOUSING_RENT" in categories:
            categories.remove("HOUSING_RENT")
        for month in range(1, end_month + 1):
            for category in categories:
                share = BUDGET_SHARES[category]
                amount = meta["monthly_income"] * share * float(rng.uniform(0.86, 1.14))
                amount = max(5.0, round(amount / 5.0) * 5.0)
                bid = f"BUD-{uid}-{YEAR}-{month:02d}-{category}"
                rows.append(
                    {
                        "budget_id": bid,
                        "user_id": uid,
                        "year": YEAR,
                        "month": month,
                        "category_code": category,
                        "budget_amount_usd": _round2(amount),
                        "currency": "USD",
                        "period_start": date(YEAR, month, 1).isoformat(),
                        "period_end": _month_end(YEAR, month).isoformat(),
                        "status": "active",
                        "version": 1,
                        "created_at": "2025-12-20T00:00:00Z",
                        "updated_at": f"{YEAR}-{month:02d}-01T00:00:00Z",
                    }
                )
    budgets = pd.DataFrame(rows)
    eligible = budgets.index[budgets["category_code"].isin(REVERSED_LEGACY)].to_numpy()
    selected = []
    if len(eligible) and n_mismatch > 0:
        selected = list(rng.choice(eligible, size=min(n_mismatch, len(eligible)), replace=False))
    for idx in selected:
        canonical = budgets.at[idx, "category_code"]
        legacy = REVERSED_LEGACY[canonical]
        budgets.at[idx, "category_code"] = legacy
        budgets.at[idx, "budget_id"] = f"BUD-{budgets.at[idx, 'user_id']}-{YEAR}-{int(budgets.at[idx, 'month']):02d}-{legacy}"
    labels = []
    anomalies = []
    mismatch_count = 0
    for row in budgets.itertuples(index=False):
        if row.category_code in LEGACY_CATEGORY_ALIASES:
            target, reason = LEGACY_CATEGORY_ALIASES[row.category_code]
            issue = "budget_taxonomy_mismatch"
            resolution = "alias"
            expected = f"Resolve {row.category_code} to {target} before budget comparison."
            mismatch_count += 1
        else:
            target = row.category_code
            reason = ""
            issue = ""
            resolution = "direct"
            expected = ""
        labels.append(
            {
                "budget_id": row.budget_id,
                "user_id": row.user_id,
                "period_month": f"{YEAR}-{int(row.month):02d}",
                "stored_category_code": row.category_code,
                "resolved_category_code": target,
                "resolution_source": resolution,
                "budget_amount_usd": row.budget_amount_usd,
                "issue_type": issue,
                "expected_action": expected,
            }
        )
    if mismatch_count:
        examples = [b for b in budgets["category_code"].tolist() if b in LEGACY_CATEGORY_ALIASES][:10]
        anomalies.append(
            {
                "issue_type": "budget_taxonomy_mismatch",
                "entity_type": "budget",
                "entity_id": "multiple",
                "related_entity_id": ",".join(sorted(set(examples))),
                "observed_behavior": f"{mismatch_count} budget rows use deprecated category codes.",
                "expected_resolution": "Map deprecated codes through category_alias before comparing actuals.",
                "impact_count": mismatch_count,
                "severity": "medium",
            }
        )
    return budgets, labels, anomalies


def _build_transfers(
    rng: np.random.Generator,
    users: pd.DataFrame,
    user_meta: dict[str, dict],
    accounts: dict[str, dict],
    n_duplicates: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    rows: list[dict] = []
    links: list[dict] = []
    anomalies: list[dict] = []
    link_seq = 0
    seq = 0
    debit_keys = []
    for user in users.itertuples(index=False):
        uid = user.user_id
        meta = user_meta[uid]
        acc = accounts[uid]
        savings = acc["savings"]
        savings_open = acc["savings_open"]
        active_end = meta["active_end"]
        if not savings or not savings_open:
            continue
        for month in range(1, active_end.month + 1):
            if date(YEAR, month, 1) < date(savings_open.year, savings_open.month, 1):
                continue
            n_pairs = int(rng.choice([0, 1, 2, 3], p=[0.28, 0.48, 0.19, 0.05]))
            for _ in range(n_pairs):
                first_day = savings_open.day if (YEAR == savings_open.year and month == savings_open.month) else 1
                last_day = MONTH_DAYS[month]
                if month == active_end.month:
                    last_day = min(last_day, active_end.day)
                if last_day < first_day:
                    continue
                day = int(rng.integers(first_day, last_day + 1))
                txn_date = date(YEAR, month, day)
                if txn_date > active_end:
                    continue
                amount = round(float(rng.uniform(100, 1500)), 2)
                link_seq += 1
                ref = f"{link_seq:06d}"
                debit_key = f"TRF{link_seq:06d}A"
                credit_key = f"TRF{link_seq:06d}B"
                debit_hour = int(rng.integers(7, 22))
                credit_minute = int(rng.integers(0, 60))
                seq += 2
                rows.append(
                    {
                        "_key": debit_key,
                        "_seq": seq - 1,
                        "_source": "transfer",
                        "_true_category": "TRANSFER",
                        "_true_treatment": "transfer",
                        "_expected_period": txn_date.strftime("%Y-%m"),
                        "_is_recurring": False,
                        "_true_series_id": "",
                        "_issue_type": "",
                        "_issue_detail": "",
                        "_refund_key": "",
                        "_link_key": f"LNK{link_seq:06d}",
                        "_related_key": credit_key,
                        "_timezone": meta["timezone"],
                        "user_id": uid,
                        "account_id": acc["checking"],
                        "merchant_id": "",
                        "descriptor": f"ONLINE TRANSFER TO SAVINGS REF {ref}",
                        "amount_usd": -amount,
                        "currency": "USD",
                        "mcc": "",
                        "channel": "internal",
                        "status": "posted",
                        "transaction_date": txn_date.isoformat(),
                        "local_time": f"{debit_hour:02d}:{credit_minute:02d}:00",
                    }
                )
                rows.append(
                    {
                        "_key": credit_key,
                        "_seq": seq,
                        "_source": "transfer",
                        "_true_category": "TRANSFER",
                        "_true_treatment": "transfer",
                        "_expected_period": txn_date.strftime("%Y-%m"),
                        "_is_recurring": False,
                        "_true_series_id": "",
                        "_issue_type": "",
                        "_issue_detail": "",
                        "_refund_key": "",
                        "_link_key": f"LNK{link_seq:06d}",
                        "_related_key": debit_key,
                        "_timezone": meta["timezone"],
                        "user_id": uid,
                        "account_id": savings,
                        "merchant_id": "",
                        "descriptor": f"TRANSFER FROM CHECKING REF {ref}",
                        "amount_usd": amount,
                        "currency": "USD",
                        "mcc": "",
                        "channel": "internal",
                        "status": "posted",
                        "transaction_date": txn_date.isoformat(),
                        "local_time": f"{debit_hour:02d}:{credit_minute:02d}:00",
                    }
                )
                links.append(
                    {
                        "pair_key": f"LNK{link_seq:06d}",
                        "debit_key": debit_key,
                        "credit_key": credit_key,
                        "link_type": "internal_savings",
                        "linked_amount_usd": amount,
                        "created_at": FIXED_GENERATED_AT,
                        "status": "posted",
                    }
                )
                debit_keys.append((debit_key, uid, acc["checking"], amount, txn_date, meta["timezone"], link_seq))
    if debit_keys and n_duplicates > 0:
        chosen = rng.choice(len(debit_keys), size=min(n_duplicates, len(debit_keys)), replace=False)
        for idx in chosen:
            debit_key, uid, checking, amount, txn_date, tz, link_no = debit_keys[int(idx)]
            dup_date = txn_date + timedelta(days=1)
            if dup_date > user_meta[uid]["active_end"]:
                dup_date = txn_date
            seq += 1
            key = f"DUP{seq:08d}"
            rows.append(
                {
                    "_key": key,
                    "_seq": seq,
                    "_source": "anomaly",
                    "_true_category": "TRANSFER",
                    "_true_treatment": "transfer",
                    "_expected_period": dup_date.strftime("%Y-%m"),
                    "_is_recurring": False,
                    "_true_series_id": "",
                    "_issue_type": "transfer_double_count",
                    "_issue_detail": f"Transfer leg duplicated as a standalone debit; pair link LNK{link_no:06d}.",
                    "_refund_key": "",
                    "_link_key": "",
                    "_related_key": debit_key,
                    "_timezone": tz,
                    "user_id": uid,
                    "account_id": checking,
                    "merchant_id": "",
                    "descriptor": "ONLINE TRANSFER TO SAVINGS",
                    "amount_usd": -amount,
                    "currency": "USD",
                    "mcc": "",
                    "channel": "internal",
                    "status": "posted",
                    "transaction_date": dup_date.isoformat(),
                    "local_time": "12:00:00",
                }
            )
            anomalies.append(
                {
                    "issue_type": "transfer_double_count",
                    "entity_type": "transaction",
                    "entity_id": key,
                    "related_entity_id": debit_key,
                    "observed_behavior": "Unlinked duplicate of an internal transfer debit appears as spending.",
                    "expected_resolution": "Exclude internal transfer legs and linked duplicates from spend and budget actuals.",
                    "impact_count": 1,
                    "severity": "high",
                }
            )
    return rows, links, anomalies


def _build_filler(
    rng: np.random.Generator,
    filler_count: int,
    users: pd.DataFrame,
    user_meta: dict[str, dict],
    accounts: dict[str, dict],
    merchant_internal: dict[str, dict],
    start_seq: int,
) -> pd.DataFrame:
    user_ids = users["user_id"].to_numpy()
    n_users = len(user_ids)
    cap_doy = np.array(
        [
            (meta["active_end"] - date(YEAR, 1, 1)).days
            for meta in (user_meta[uid] for uid in user_ids)
        ]
    )
    scale = np.array(
        [
            0.78 + 0.11 * user_meta[uid]["band_idx"] + 0.025 * user_meta[uid]["household"]
            for uid in user_ids
        ]
    )
    checking = np.array([accounts[uid]["checking"] for uid in user_ids])
    credit_ids = np.array([accounts[uid]["credit"] for uid in user_ids])
    has_credit = np.array([bool(x) for x in credit_ids])
    timezone_by_user = np.array([user_meta[uid]["timezone"] for uid in user_ids])
    category_weights = np.array([FILLER_MIX[c] for c in FILLER_MIX])
    category_weights = category_weights / category_weights.sum()
    counts = rng.multinomial(filler_count, category_weights)
    day_weights_base = np.ones(365)
    frames = []
    seq = start_seq
    for category, n in zip(FILLER_MIX.keys(), counts):
        n = int(n)
        if n <= 0:
            continue
        user_idx = rng.integers(0, n_users, size=n)
        month_factor = np.ones(365)
        season = CATEGORY_SEASONALITY.get(category)
        dow = DOW_WEIGHTS.get(category, [1, 1, 1, 1, 1, 1, 1])
        if season:
            for m in range(1, 13):
                lo = date(YEAR, m, 1).timetuple().tm_yday - 1
                hi = date(YEAR, m, MONTH_DAYS[m]).timetuple().tm_yday
                month_factor[lo:hi] = season[m - 1]
        weekday = np.array([date(YEAR, 1, 1).weekday()] * 365)
        for d in range(365):
            weekday[d] = (date(YEAR, 1, 1) + timedelta(days=d)).weekday()
        dow_factor = np.array([dow[int(w)] for w in weekday])
        doy = _pick_dates(rng, n, day_weights_base * month_factor * dow_factor, cap_doy[user_idx])
        dates = np.array([date(YEAR, 1, 1) + timedelta(days=int(d)) for d in doy])
        months = np.array([d.month for d in dates])
        median, sigma, low, high = AMOUNT_PARAMS[category]
        amounts = rng.lognormal(mean=math.log(median), sigma=sigma, size=n)
        amounts = amounts * scale[user_idx]
        amounts = amounts * np.array([season[m - 1] if season else 1.0 for m in months])
        amounts = np.clip(amounts, low, high)
        amounts = np.round(amounts, 2)
        if category != "INCOME_OTHER":
            amounts = -amounts
        merchants = CATEGORY_MERCHANTS.get(category, [])
        if not merchants:
            continue
        keys = [m["key"] for m in merchants if not m.get("subscription", False)]
        if not keys:
            continue
        w = np.array([merchant_internal[k]["weight"] for k in keys])
        w = w / w.sum()
        midx = rng.choice(len(keys), size=n, p=w)
        merchant_ids = np.array([merchant_internal[keys[int(i)]]["merchant_id"] for i in midx])
        mccs = np.array([merchant_internal[keys[int(i)]]["mcc"] for i in midx])
        descriptors = np.empty(n, dtype=object)
        for mi in np.unique(midx):
            mask = midx == mi
            variants = merchant_internal[keys[int(mi)]]["variants"]
            picks = rng.integers(0, len(variants), size=int(mask.sum()))
            descriptors[mask] = [variants[int(p)] for p in picks]
        hour_list = _descriptor_time(rng, category, n)
        online_p = np.array([merchant_internal[keys[int(i)]]["online"] for i in midx])
        online_draw = rng.random(n)
        if category == "INCOME_OTHER":
            channel = np.array(["ach"] * n, dtype=object)
        elif category == "FEES":
            channel = np.where(online_draw < online_p, "online", "atm")
        elif category == "UTILITIES":
            channel = np.where(online_draw < online_p, "online", "ach")
        else:
            channel = np.where(online_draw < online_p, "online", "pos")
        use_credit = (rng.random(n) < 0.28) & has_credit[user_idx]
        account_ids = np.where(use_credit, credit_ids[user_idx], checking[user_idx])
        seqs = np.arange(seq + 1, seq + n + 1)
        seq += n
        frame = pd.DataFrame(
            {
                "_key": [f"FIL{int(s):08d}" for s in seqs],
                "_seq": seqs,
                "_source": "filler",
                "_true_category": category,
                "_true_treatment": "income" if category == "INCOME_OTHER" else "spend",
                "_expected_period": [d.strftime("%Y-%m") for d in dates],
                "_is_recurring": False,
                "_true_series_id": "",
                "_issue_type": "",
                "_issue_detail": "",
                "_refund_key": "",
                "_link_key": "",
                "_related_key": "",
                "_timezone": timezone_by_user[user_idx],
                "user_id": user_ids[user_idx],
                "account_id": account_ids,
                "merchant_id": merchant_ids,
                "descriptor": descriptors,
                "amount_usd": amounts,
                "currency": "USD",
                "mcc": mccs,
                "channel": channel,
                "status": "posted",
                "transaction_date": [d.isoformat() for d in dates],
                "local_time": hour_list,
            }
        )
        frames.append(frame)
    if not frames:
        raise ValueError("filler_count must be greater than zero")
    result = pd.concat(frames, ignore_index=True)
    override_n = max(1, int(round(len(result) * 0.02)))
    override_idx = rng.choice(len(result), size=min(override_n, len(result)), replace=False)
    generic = np.array(["POS DEBIT 8812", "ONLINE PURCHASE 4471", "WEB PMT 90210", "SQ *MARKET 771"])
    result.loc[override_idx, "descriptor"] = generic[rng.integers(0, len(generic), size=len(override_idx))]
    return result


def _inject_timezone_cases(
    rng: np.random.Generator,
    filler: pd.DataFrame,
    user_meta: dict[str, dict],
    count: int,
    start_key: int,
) -> tuple[pd.DataFrame, list[dict]]:
    candidates = filler.index[(filler["amount_usd"] < 0) & (filler["_source"] == "filler")].to_numpy()
    anomalies = []
    if len(candidates) == 0 or count <= 0:
        return filler, anomalies
    chosen = rng.choice(candidates, size=min(count, len(candidates)), replace=False)
    for idx in chosen:
        uid = filler.at[idx, "user_id"]
        active_end = user_meta[uid]["active_end"]
        max_month = min(active_end.month, 10)
        month = int(rng.integers(3, max_month + 1))
        local_date = _month_end(YEAR, month)
        time_str = f"{int(rng.integers(23, 24)):02d}:{int(rng.integers(35, 60)):02d}:00"
        filler.at[idx, "transaction_date"] = local_date.isoformat()
        filler.at[idx, "local_time"] = time_str
        filler.at[idx, "_expected_period"] = local_date.strftime("%Y-%m")
        filler.at[idx, "_issue_type"] = "timezone_boundary_date"
        filler.at[idx, "_issue_detail"] = (
            f"Local date {local_date.isoformat()} {time_str} lies at month end; UTC posting falls in the next month."
        )
        key = filler.at[idx, "_key"]
        anomalies.append(
            {
                "issue_type": "timezone_boundary_date",
                "entity_type": "transaction",
                "entity_id": key,
                "related_entity_id": filler.at[idx, "user_id"],
                "observed_behavior": "UTC posted_at month differs from the local transaction month.",
                "expected_resolution": "Assign budget and insight periods from the local transaction date, not raw UTC.",
                "impact_count": 1,
                "severity": "medium",
            }
        )
    return filler, anomalies


def _build_refunds(
    rng: np.random.Generator,
    filler: pd.DataFrame,
    user_meta: dict[str, dict],
    n_normal: int,
    n_anomaly: int,
    start_seq: int,
) -> tuple[pd.DataFrame, list[dict]]:
    cutoff_by_user = filler["user_id"].map(
        lambda uid: (user_meta[uid]["active_end"] - timedelta(days=2)).isoformat()
    )
    candidates = filler.index[
        (filler["amount_usd"] < 0)
        & (filler["_source"] == "filler")
        & (filler["transaction_date"] <= f"{YEAR}-12-10")
        & (filler["transaction_date"] <= cutoff_by_user)
    ].to_numpy()
    if len(candidates) == 0:
        return pd.DataFrame(), []
    total_needed = min(n_normal + n_anomaly, len(candidates))
    chosen = rng.choice(candidates, size=total_needed, replace=False)
    rows = []
    anomalies = []
    seq = start_seq
    for j, idx in enumerate(chosen):
        original = filler.loc[idx]
        uid = original["user_id"]
        active_end = user_meta[uid]["active_end"]
        original_date = date.fromisoformat(original["transaction_date"])
        gap = int(rng.integers(1, 46))
        refund_date = original_date + timedelta(days=gap)
        if refund_date > active_end:
            refund_date = active_end
        anomaly = j >= n_normal
        factor = 1.0 if rng.random() < 0.7 else float(rng.uniform(0.20, 0.85))
        amount = _round2(abs(float(original["amount_usd"])) * factor)
        if anomaly:
            descriptor = str(original["descriptor"])
            if rng.random() < 0.5:
                descriptor = descriptor + " CREDIT"
            link = str(original["_key"]) if rng.random() < 0.40 else ""
            issue = "refund_treated_as_new_expense"
            detail = "Refund credited without a clear refund marker; naive logic counts it as new spend."
        else:
            descriptor = "REFUND " + str(original["descriptor"])[:48]
            link = str(original["_key"])
            issue = ""
            detail = ""
        hour = int(rng.integers(8, 21))
        minute = int(rng.integers(0, 60))
        seq += 1
        key = f"RFD{seq:08d}"
        rows.append(
            {
                "_key": key,
                "_seq": seq,
                "_source": "refund_anomaly" if anomaly else "refund",
                "_true_category": "REFUND",
                "_true_treatment": "refund",
                "_expected_period": refund_date.strftime("%Y-%m"),
                "_is_recurring": False,
                "_true_series_id": "",
                "_issue_type": issue,
                "_issue_detail": detail,
                "_refund_key": link,
                "_link_key": "",
                "_related_key": str(original["_key"]),
                "_timezone": original["_timezone"],
                "user_id": uid,
                "account_id": original["account_id"],
                "merchant_id": original["merchant_id"],
                "descriptor": descriptor,
                "amount_usd": amount,
                "currency": "USD",
                "mcc": original["mcc"],
                "channel": original["channel"],
                "status": "posted",
                "transaction_date": refund_date.isoformat(),
                "local_time": f"{hour:02d}:{minute:02d}:00",
            }
        )
        if anomaly:
            anomalies.append(
                {
                    "issue_type": "refund_treated_as_new_expense",
                    "entity_type": "transaction",
                    "entity_id": key,
                    "related_entity_id": str(original["_key"]),
                    "observed_behavior": "Positive refund credit resembles a purchase descriptor and lacks a refund link.",
                    "expected_resolution": "Treat positive credits in expense categories as refunds and offset the original category.",
                    "impact_count": 1,
                    "severity": "high",
                }
            )
    return pd.DataFrame(rows), anomalies


def _attach_times(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    local = pd.to_datetime(result["transaction_date"] + " " + result["local_time"])
    utc_values = pd.Series(index=result.index, dtype="object")
    for tz_name in sorted(result["_timezone"].unique()):
        mask = result["_timezone"] == tz_name
        converted = (
            local[mask]
            .dt.tz_localize(tz_name, ambiguous=True, nonexistent="shift_forward")
            .dt.tz_convert("UTC")
        )
        utc_values.loc[mask] = converted.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result["posted_at_utc"] = utc_values
    return result


def _assign_ids(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["posted_at_utc", "user_id", "_seq"], kind="mergesort").reset_index(drop=True)
    df["transaction_id"] = [f"TXN-{YEAR}-{i:08d}" for i in range(1, len(df) + 1)]
    return df


def _build_events(users: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for user in users.itertuples(index=False):
        rows.append(
            {
                "entity_type": "user_profile",
                "entity_id": user.user_id,
                "event_type": "CREATED",
                "event_at": user.created_at,
                "from_state": "",
                "to_state": "active",
                "reason": "Synthetic profile onboarding",
                "source": "synthetic_generator",
            }
        )
        if user.lifecycle_state == "dormant":
            rows.append(
                {
                    "entity_type": "user_profile",
                    "entity_id": user.user_id,
                    "event_type": "DORMANT",
                    "event_at": f"{YEAR}-09-01T00:00:00Z",
                    "from_state": "active",
                    "to_state": "dormant",
                    "reason": "No account activity for 30 days",
                    "source": "synthetic_generator",
                }
            )
        elif user.lifecycle_state == "closed":
            rows.append(
                {
                    "entity_type": "user_profile",
                    "entity_id": user.user_id,
                    "event_type": "CLOSED",
                    "event_at": f"{YEAR}-10-02T00:00:00Z",
                    "from_state": "active",
                    "to_state": "closed",
                    "reason": "Customer requested account closure",
                    "source": "synthetic_generator",
                }
            )
    for account in accounts.itertuples(index=False):
        rows.append(
            {
                "entity_type": "account",
                "entity_id": account.account_id,
                "event_type": "OPENED",
                "event_at": account.opened_at,
                "from_state": "",
                "to_state": "active",
                "reason": "Synthetic account opening",
                "source": "synthetic_generator",
            }
        )
        if account.status == "closed":
            rows.append(
                {
                    "entity_type": "account",
                    "entity_id": account.account_id,
                    "event_type": "CLOSED",
                    "event_at": f"{YEAR}-10-02T00:00:00Z",
                    "from_state": "active",
                    "to_state": "closed",
                    "reason": "Owner profile closed",
                    "source": "synthetic_generator",
                }
            )
    events = pd.DataFrame(rows)
    events = events.sort_values(["event_at", "entity_type", "entity_id", "event_type"], kind="mergesort").reset_index(drop=True)
    events.insert(0, "event_id", [f"EVT-{i:06d}" for i in range(1, len(events) + 1)])
    return events


def _build_labels_and_manifest(
    txn_internal: pd.DataFrame,
    link_map: dict[str, str],
    gt_series: list[dict],
    gt_expectations: list[dict],
    anomalies_raw: list[dict],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    key_to_id = dict(zip(txn_internal["_key"], txn_internal["transaction_id"]))
    labels = []
    tx_ids = txn_internal["transaction_id"].tolist()
    true_cats = txn_internal["_true_category"].tolist()
    true_treat = txn_internal["_true_treatment"].tolist()
    expected = txn_internal["_expected_period"].tolist()
    recurring = txn_internal["_is_recurring"].tolist()
    true_series = txn_internal["_true_series_id"].tolist()
    issues = txn_internal["_issue_type"].tolist()
    details = txn_internal["_issue_detail"].tolist()
    related_keys = txn_internal["_related_key"].fillna("").tolist()
    refund_keys = txn_internal["_refund_key"].fillna("").tolist()
    for i, tx_id in enumerate(tx_ids):
        if true_treat[i] == "transfer" and related_keys[i]:
            related = key_to_id.get(related_keys[i], "")
        elif true_treat[i] == "refund" and refund_keys[i]:
            related = key_to_id.get(refund_keys[i], "")
        elif issues[i] == "transfer_double_count" and related_keys[i]:
            related = key_to_id.get(related_keys[i], "")
        else:
            related = ""
        labels.append(
            {
                "transaction_id": tx_id,
                "true_category_code": true_cats[i],
                "true_treatment": true_treat[i],
                "expected_period": expected[i],
                "is_recurring": bool(recurring[i]),
                "true_series_id": true_series[i],
                "issue_type": issues[i],
                "issue_detail": details[i],
                "related_transaction_id": related,
            }
        )
    label_df = pd.DataFrame(labels)
    anomaly_rows = []
    for anomaly in anomalies_raw:
        item = dict(anomaly)
        if item["entity_type"] == "transaction":
            entity_key = item["entity_id"]
            item["entity_id"] = key_to_id.get(entity_key, entity_key)
            related_key = item.get("related_entity_id", "")
            if related_key in key_to_id:
                item["related_entity_id"] = key_to_id[related_key]
            elif related_key in link_map:
                item["related_entity_id"] = link_map[related_key]
        anomaly_rows.append(item)
    anomaly_df = pd.DataFrame(anomaly_rows)
    if len(anomaly_df):
        anomaly_df.insert(0, "anomaly_id", [f"ANM-{i:06d}" for i in range(1, len(anomaly_df) + 1)])
        anomaly_df = anomaly_df[
            [
                "anomaly_id",
                "issue_type",
                "entity_type",
                "entity_id",
                "related_entity_id",
                "observed_behavior",
                "expected_resolution",
                "impact_count",
                "severity",
            ]
        ]
    else:
        anomaly_df = pd.DataFrame(columns=["anomaly_id", "issue_type", "entity_type", "entity_id", "related_entity_id", "observed_behavior", "expected_resolution", "impact_count", "severity"])
    series_df = pd.DataFrame(gt_series)
    expectations_df = pd.DataFrame(gt_expectations)
    return label_df, anomaly_df, series_df, expectations_df, anomaly_rows


def generate_dataset(
    scale: str = "full",
    seed: int = SEED,
    out_dir: str | Path | None = None,
    profiles: int | None = None,
    transactions: int | None = None,
    formats: tuple[str, ...] = ("csv", "json", "sql"),
    write_manifest: bool = True,
) -> dict:
    if scale not in SCALES:
        raise ValueError(f"Unknown scale: {scale}")
    n_profiles = int(profiles if profiles is not None else SCALES[scale]["profiles"])
    n_transactions = int(transactions if transactions is not None else SCALES[scale]["transactions"])
    if n_profiles < 1 or n_transactions < 100:
        raise ValueError("profiles must be >=1 and transactions >=100")
    rng = np.random.default_rng(seed)
    random.seed(seed)
    out_path = Path(out_dir) if out_dir is not None else Path("dataset")
    for sub in ["data", "data/json", "data/sql", "ground_truth", "outputs", "metadata", "validation"]:
        (out_path / sub).mkdir(parents=True, exist_ok=True)

    users, user_meta = _build_users(rng, n_profiles)
    accounts, account_map = _build_accounts(rng, users, user_meta)
    merchants, merchant_aliases, merchant_internal = _build_merchants(rng)
    categories, category_aliases = _build_categories()
    rules = build_category_rules(merchants, merchant_internal)

    n_skips = max(1, int(round(n_profiles * 0.03)))
    recurring_tx, gt_series, gt_expectations, series_anomalies = _build_series(
        rng, users, user_meta, account_map, merchant_internal, n_skips
    )
    n_budgets = 0
    budget_probe = _build_budgets(rng, users, user_meta, gt_series, 0)[0]
    n_budgets = len(budget_probe)
    n_budget_mismatch = max(1, int(round(n_budgets * 0.02)))
    budgets, budget_labels, budget_anomalies = _build_budgets(
        rng, users, user_meta, gt_series, n_budget_mismatch
    )

    n_duplicates = max(1, int(round(n_transactions * 0.00015)))
    transfer_tx, transfer_links, transfer_anomalies = _build_transfers(
        rng, users, user_meta, account_map, n_duplicates
    )
    n_normal_refunds = max(2, int(round(n_transactions * 0.012)))
    n_anomaly_refunds = max(1, int(round(n_transactions * 0.00015)))
    n_timezone = max(1, int(round(n_transactions * 0.00012)))
    filler_count = n_transactions - len(recurring_tx) - len(transfer_tx) - n_normal_refunds - n_anomaly_refunds
    if filler_count < 100:
        raise ValueError("Transaction target is too small for the configured recurring/refund volume.")
    filler = _build_filler(
        rng,
        filler_count,
        users,
        user_meta,
        account_map,
        merchant_internal,
        start_seq=len(recurring_tx) + len(transfer_tx) + 10,
    )
    filler, timezone_anomalies = _inject_timezone_cases(
        rng, filler, user_meta, n_timezone, start_key=1
    )
    refunds, refund_anomalies = _build_refunds(
        rng,
        filler,
        user_meta,
        n_normal_refunds,
        n_anomaly_refunds,
        start_seq=len(recurring_tx) + len(transfer_tx) + len(filler) + 20,
    )
    refunds = refunds.reset_index(drop=True)
    remaining = n_transactions - (len(recurring_tx) + len(transfer_tx) + len(filler) + len(refunds))
    if remaining > 0:
        extra = _build_filler(
            rng,
            remaining,
            users,
            user_meta,
            account_map,
            merchant_internal,
            start_seq=len(recurring_tx) + len(transfer_tx) + len(filler) + len(refunds) + 100,
        )
        filler = pd.concat([filler, extra], ignore_index=True)
    elif remaining < 0:
        raise ValueError(f"Overshot transaction target by {-remaining}")

    txn = pd.concat(
        [pd.DataFrame(recurring_tx), pd.DataFrame(transfer_tx), filler, refunds],
        ignore_index=True,
        sort=False,
    )
    txn = _attach_times(txn)
    missing_time = txn["posted_at_utc"].isna().sum()
    if missing_time:
        raise ValueError(f"Failed to compute posted_at_utc for {missing_time} rows")
    txn = _assign_ids(txn)
    natural_tz_anomalies = []
    tz_mismatch = txn["_expected_period"] != txn["posted_at_utc"].str[:7]
    for idx in txn.index[tz_mismatch & txn["_issue_type"].fillna("").eq("")]:
        utc_month = txn.at[idx, "posted_at_utc"][:7]
        txn.at[idx, "_issue_type"] = "timezone_boundary_date"
        txn.at[idx, "_issue_detail"] = (
            f"Local month {txn.at[idx, '_expected_period']} differs from UTC posting month {utc_month}."
        )
        natural_tz_anomalies.append(
            {
                "issue_type": "timezone_boundary_date",
                "entity_type": "transaction",
                "entity_id": txn.at[idx, "_key"],
                "related_entity_id": txn.at[idx, "user_id"],
                "observed_behavior": "UTC posted_at month differs from the local transaction month.",
                "expected_resolution": "Assign budget and insight periods from the local transaction date, not raw UTC.",
                "impact_count": 1,
                "severity": "medium",
            }
        )
    timezone_anomalies = timezone_anomalies + natural_tz_anomalies
    key_to_id = dict(zip(txn["_key"], txn["transaction_id"]))
    txn["refund_of_txn_id"] = txn["_refund_key"].map(key_to_id).fillna("")
    txn["merchant_id"] = txn["merchant_id"].fillna("")
    txn["mcc"] = txn["mcc"].fillna("")
    tx_out = txn[TX_FIELDS].copy()
    tx_out = tx_out.sort_values("transaction_id", kind="mergesort").reset_index(drop=True)

    link_rows = []
    link_map = {row["pair_key"]: "" for row in transfer_links}
    for i, link in enumerate(sorted(transfer_links, key=lambda x: x["debit_key"]), start=1):
        debit_id = key_to_id.get(link["debit_key"], "")
        credit_id = key_to_id.get(link["credit_key"], "")
        link_id = f"TLK-{i:06d}"
        link_map[link["pair_key"]] = link_id
        link_rows.append(
            {
                "link_id": link_id,
                "debit_txn_id": debit_id,
                "credit_txn_id": credit_id,
                "link_type": link["link_type"],
                "linked_amount_usd": link["linked_amount_usd"],
                "created_at": link["created_at"],
                "status": link["status"],
            }
        )
    transfer_link_df = pd.DataFrame(link_rows)

    balance = tx_out.groupby("account_id", sort=False)["amount_usd"].sum().round(2)
    accounts["current_balance_usd"] = accounts["account_id"].map(balance).fillna(0.0).round(2)
    accounts["credit_limit_usd"] = accounts["credit_limit_usd"].fillna("")

    label_df, anomaly_df, series_labels_df, expectations_df, _ = _build_labels_and_manifest(
        txn, link_map, gt_series, gt_expectations, series_anomalies + transfer_anomalies + timezone_anomalies + refund_anomalies + budget_anomalies
    )

    reference = build_reference_outputs(tx_out, rules, merchants, budgets, users)
    recurring_series = reference["recurring_series"]
    budget_comparison = reference["budget_comparison"]
    insights = reference["insights"]
    monthly_spend = reference["monthly_spend"]
    decisions = reference["decisions"]
    categorized = reference["categorized_transactions"]
    events = _build_events(users, accounts)

    series_labels = series_labels_df.copy()
    series_labels = series_labels.sort_values("true_series_id", kind="mergesort").reset_index(drop=True)
    expectations_df = expectations_df.sort_values(["true_series_id", "occurrence_date"], kind="mergesort").reset_index(drop=True)
    budget_labels_df = pd.DataFrame(budget_labels).sort_values("budget_id", kind="mergesort").reset_index(drop=True)

    tables = {
        "user_profile": users,
        "account": accounts,
        "merchant": merchants,
        "merchant_alias": merchant_aliases,
        "category": categories,
        "category_alias": category_aliases,
        "category_rule": rules,
        "budget": budgets,
        "transaction": tx_out,
        "transfer_link": transfer_link_df,
        "recurring_series": recurring_series,
        "insight": insights,
        "entity_event": events,
    }
    ground_truth = {
        "transaction_labels": label_df,
        "recurring_series_labels": series_labels,
        "recurring_expectations": expectations_df,
        "budget_labels": budget_labels_df,
        "anomaly_manifest": anomaly_df,
    }
    outputs = {
        "categorization_decisions": decisions,
        "categorized_transactions": categorized,
        "budget_comparison": budget_comparison,
        "monthly_spend": monthly_spend,
        "recurring_series": recurring_series,
    }
    metadata = {
        "seed": seed,
        "scale": scale,
        "profiles": n_profiles,
        "transactions": int(len(tx_out)),
        "transaction_target": n_transactions,
        "year": YEAR,
        "generated_at": FIXED_GENERATED_AT,
        "project_version": PROJECT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "formats": list(formats),
        "counts": {
            "profiles": int(len(users)),
            "accounts": int(len(accounts)),
            "merchants": int(len(merchants)),
            "categories": int(len(categories)),
            "category_rules": int(len(rules)),
            "budgets": int(len(budgets)),
            "transactions": int(len(tx_out)),
            "transfer_links": int(len(transfer_link_df)),
            "recurring_series": int(len(recurring_series)),
            "insights": int(len(insights)),
            "events": int(len(events)),
        },
        "anomaly_counts": {
            str(k): int(v) for k, v in anomaly_df["issue_type"].value_counts().sort_index().items()
        } if len(anomaly_df) else {},
        "anomaly_impact_counts": {
            str(k): int(v) for k, v in anomaly_df.groupby("issue_type")["impact_count"].sum().sort_index().items()
        } if len(anomaly_df) else {},
        "files": {},
    }
    manifest = write_dataset(
        out_path=out_path,
        tables=tables,
        ground_truth=ground_truth,
        outputs=outputs,
        metadata=metadata,
        formats=formats,
        write_manifest=write_manifest,
    )
    return {
        "tables": tables,
        "ground_truth": ground_truth,
        "outputs": outputs,
        "manifest": manifest,
        "labels": label_df,
        "budget_labels": budget_labels_df,
        "anomalies": anomaly_df,
    }
