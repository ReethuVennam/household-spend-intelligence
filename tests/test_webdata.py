from __future__ import annotations

import json
from pathlib import Path

from src.metrics import run_evaluation
from src.validation import run_validation
from src.webdata import build_web_data

EXPECTED_KEYS = {
    "manifest",
    "validation",
    "evaluation",
    "monthly",
    "categories",
    "budget",
    "recurring",
    "anomalies",
    "explorer",
    "reports",
}


def test_webdata_payload_builds(mini_dataset: Path, tmp_path: Path):
    if not (mini_dataset / "outputs" / "evaluation_report.json").exists():
        run_validation(mini_dataset)
        run_evaluation(mini_dataset)
    out = build_web_data(str(mini_dataset), tmp_path / "data.json")
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert EXPECTED_KEYS <= set(payload)
    assert payload["validation"]["status"] == "PASS"
    assert payload["validation"]["counts"]["fail"] == 0
    assert len(payload["monthly"]) >= 1
    months = [row["month"] for row in payload["monthly"]]
    assert months == sorted(months), "monthly rows must be in chronological order"
    assert len(payload["anomalies"]) == 5
    statuses = payload["budget"]["statuses"]
    assert sum(s["rows"] for s in statuses) == payload["budget"]["rows"] > 0
    assert {"under", "near", "over"} <= {s["status"] for s in statuses}
    assert payload["recurring"]["total_detected"] >= 1
    assert len(payload["reports"]) >= 5
    assert all(r["href"].startswith("../../") for r in payload["reports"])
    assert payload["explorer"] == [], "explorer sample is optional and absent for temp datasets"
