from __future__ import annotations

import pandas as pd

from .taxonomy import CATEGORY_BY_CODE

GLOBAL_RULES = [
    ("TRANSFER", "TRANSFER", 260, "contains", "descriptor", None),
    ("REFUND", "REFUND", 258, "contains", "descriptor", None),
    ("PAYROLL", "INCOME_SALARY", 120, "contains", "descriptor", None),
    ("DIRECT DEP", "INCOME_SALARY", 119, "contains", "descriptor", None),
    ("RENT", "HOUSING_RENT", 115, "contains", "descriptor", None),
    ("INTEREST PAYMENT", "INCOME_OTHER", 110, "contains", "descriptor", None),
    ("CASH BACK", "INCOME_OTHER", 109, "contains", "descriptor", None),
    ("OVERDRAFT", "FEES", 108, "contains", "descriptor", None),
    ("ATM FEE", "FEES", 107, "contains", "descriptor", None),
    ("SERVICE FEE", "FEES", 106, "contains", "descriptor", None),
    ("POS DEBIT", "OTHER", 20, "contains", "descriptor", None),
    ("ONLINE PURCHASE", "OTHER", 19, "contains", "descriptor", None),
]


def build_category_rules(merchants: pd.DataFrame, merchant_internal: dict[str, dict]) -> pd.DataFrame:
    by_id = {v["merchant_id"]: v for v in merchant_internal.values()}
    rows = []
    for merchant in merchants.itertuples(index=False):
        info = by_id[merchant.merchant_id]
        if info["category"] in {"TRANSFER", "REFUND"}:
            continue
        for alias in info["aliases"]:
            alias = str(alias).strip().upper()
            if not alias:
                continue
            rows.append(
                {
                    "category_code": info["category"],
                    "merchant_id": merchant.merchant_id,
                    "match_field": "descriptor",
                    "match_type": "contains",
                    "pattern": alias,
                    "priority": 100 + len(alias) + int(info.get("bias", 0)),
                    "confidence": min(0.97, 0.58 + len(alias) / 80.0),
                    "effective_from": "2025-01-01",
                    "effective_to": "",
                    "status": "active",
                }
            )
    for pattern, category, priority, match_type, field, _ in GLOBAL_RULES:
        rows.append(
            {
                "category_code": category,
                "merchant_id": "",
                "match_field": field,
                "match_type": match_type,
                "pattern": pattern,
                "priority": priority,
                "confidence": 0.99 if category in {"TRANSFER", "REFUND"} else 0.90,
                "effective_from": "2025-01-01",
                "effective_to": "",
                "status": "active",
            }
        )
    rules = pd.DataFrame(rows)
    rules = rules.sort_values(["priority", "category_code", "pattern"], ascending=[False, True, True], kind="mergesort").reset_index(drop=True)
    rules.insert(0, "rule_id", [f"RUL-{i:06d}" for i in range(1, len(rules) + 1)])
    return rules[
        [
            "rule_id",
            "category_code",
            "merchant_id",
            "match_field",
            "match_type",
            "pattern",
            "priority",
            "confidence",
            "effective_from",
            "effective_to",
            "status",
        ]
    ]


class RuleEngine:
    def __init__(self, rules: pd.DataFrame):
        active = rules[rules["status"] == "active"].copy()
        active = active.sort_values(["priority", "rule_id"], ascending=[False, True], kind="mergesort")
        self.patterns = [(str(r.pattern).upper(), str(r.category_code), str(r.rule_id), float(r.confidence)) for r in active.itertuples(index=False)]
        self.rule_count = len(self.patterns)

    def apply(self, descriptors: pd.Series, amount: pd.Series | None = None) -> pd.DataFrame:
        upper = descriptors.fillna("").astype(str).str.upper()
        n = len(upper)
        category = [None] * n
        rule_id = [""] * n
        confidence = [0.0] * n
        source = ["fallback"] * n
        remaining = pd.Series([True] * n)
        for pattern, cat, rid, conf in self.patterns:
            if not remaining.any():
                break
            mask = remaining & upper.str.contains(pattern, regex=False, na=False)
            idx = mask.to_numpy().nonzero()[0]
            if len(idx):
                for i in idx:
                    category[i] = cat
                    rule_id[i] = rid
                    confidence[i] = conf
                    source[i] = "rule"
                remaining.iloc[idx] = False
        if amount is not None:
            amt = amount.to_numpy()
            for i in range(n):
                if category[i] is None and amt[i] > 0:
                    category[i] = "INCOME_OTHER"
                    confidence[i] = 0.25
                    source[i] = "sign_fallback"
        for i in range(n):
            if category[i] is None:
                category[i] = "OTHER"
                confidence[i] = 0.20
        return pd.DataFrame(
            {
                "predicted_category_code": category,
                "rule_id": rule_id,
                "confidence": confidence,
                "decision_source": source,
            }
        )


def category_class_type(code: str) -> str:
    item = CATEGORY_BY_CODE.get(code)
    return item["type"] if item else "expense"
