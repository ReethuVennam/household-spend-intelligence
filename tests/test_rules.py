from __future__ import annotations

import pandas as pd

from src.metrics import _classification_metrics
from src.rules import RuleEngine, build_category_rules, category_class_type
from src.taxonomy import CATEGORY_BY_CODE, LEGACY_CATEGORY_ALIASES, is_active_category


def _engine(rows) -> RuleEngine:
    rules = pd.DataFrame(
        rows,
        columns=["rule_id", "category_code", "pattern", "priority", "confidence", "status"],
    )
    return RuleEngine(rules)


def _apply(engine: RuleEngine, descriptor: str, amount: float = -10.0) -> pd.DataFrame:
    out = engine.apply(pd.Series([descriptor]), amount=pd.Series([amount]))
    return out.iloc[0]


def test_higher_priority_rule_wins():
    engine = _engine(
        [
            ("RUL-000001", "DINING", "COFFEE", 100, 0.90, "active"),
            ("RUL-000002", "TRANSFER", "TRANSFER", 260, 0.99, "active"),
        ]
    )
    row = _apply(engine, "COFFEE TRANSFER TO SAVINGS")
    assert row["predicted_category_code"] == "TRANSFER"
    assert row["rule_id"] == "RUL-000002"
    assert row["decision_source"] == "rule"


def test_merchant_alias_rule_matches_descriptor():
    engine = _engine([("RUL-000001", "DINING", "STARBUCKS", 120, 0.95, "active")])
    row = _apply(engine, "STARBUCKS #4567 SEATTLE WA")
    assert row["predicted_category_code"] == "DINING"
    assert row["decision_source"] == "rule"
    assert row["confidence"] == 0.95


def test_inactive_rules_are_ignored():
    engine = _engine([("RUL-000001", "TRAVEL", "HOTEL", 500, 0.99, "inactive")])
    row = _apply(engine, "HOTEL MARRIOTT STAY")
    assert row["predicted_category_code"] == "OTHER"
    assert row["decision_source"] == "fallback"


def test_unmatched_negative_falls_back_to_other():
    engine = _engine([("RUL-000001", "DINING", "COFFEE", 100, 0.90, "active")])
    row = _apply(engine, "UNRECOGNIZED MERCHANT XYZ")
    assert row["predicted_category_code"] == "OTHER"
    assert row["decision_source"] == "fallback"
    assert row["confidence"] == 0.20


def test_unmatched_positive_amount_sign_fallback():
    engine = _engine([("RUL-000001", "DINING", "COFFEE", 100, 0.90, "active")])
    row = _apply(engine, "UNRECOGNIZED CREDIT", amount=250.0)
    assert row["predicted_category_code"] == "INCOME_OTHER"
    assert row["decision_source"] == "sign_fallback"


def test_first_match_in_priority_order_is_final():
    engine = _engine(
        [
            ("RUL-000001", "SHOPPING", "AMZN", 300, 0.95, "active"),
            ("RUL-000002", "SUBSCRIPTION", "AMZN", 150, 0.90, "active"),
        ]
    )
    row = _apply(engine, "AMZN MKTPLACE ORDER")
    assert row["predicted_category_code"] == "SHOPPING"
    assert row["rule_id"] == "RUL-000001"


def test_build_category_rules_sequential_ids_and_sorted_priority():
    merchants = pd.DataFrame(
        [
            {"merchant_id": "MER-000001", "name": "Starbucks"},
            {"merchant_id": "MER-000002", "name": "Landlord"},
        ]
    )
    internal = {
        "starbucks": {"merchant_id": "MER-000001", "category": "DINING", "aliases": ["STARBUCKS"]},
        "landlord": {"merchant_id": "MER-000002", "category": "HOUSING_RENT", "aliases": ["SUNSET PROPERTY MGMT"]},
    }
    rules = build_category_rules(merchants, internal)
    assert list(rules["rule_id"]) == [f"RUL-{i:06d}" for i in range(1, len(rules) + 1)]
    assert rules["priority"].is_monotonic_decreasing
    assert rules["pattern"].str.upper().tolist() == rules["pattern"].tolist()
    merchant_transfer = rules[(rules["category_code"] == "TRANSFER") & (rules["merchant_id"] != "")]
    assert merchant_transfer.empty


def test_legacy_budget_codes_resolve_to_active_categories():
    for legacy, (target, _note) in LEGACY_CATEGORY_ALIASES.items():
        assert legacy in CATEGORY_BY_CODE
        assert not is_active_category(legacy)
        assert target in CATEGORY_BY_CODE
        assert is_active_category(target)


def test_category_class_type():
    assert category_class_type("INCOME_SALARY") == "income"
    assert category_class_type("HOUSING_RENT") == "expense"
    assert category_class_type("NOT_A_REAL_CODE") == "expense"


def test_classification_metrics_perfect_prediction():
    y = pd.Series(["A", "B", "A", "C"])
    result = _classification_metrics(y, y.copy())
    assert result["accuracy"] == 1.0
    assert result["macro_f1"] == 1.0


def test_classification_metrics_partial_prediction():
    y_true = pd.Series(["A", "A", "B", "B"])
    y_pred = pd.Series(["A", "B", "B", "B"])
    result = _classification_metrics(y_true, y_pred)
    assert result["accuracy"] == 0.75
    assert 0.0 <= result["macro_f1"] < 1.0
