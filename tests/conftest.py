from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import SEED
from src.generator import generate_dataset


@pytest.fixture(scope="session")
def mini_dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = Path(tmp_path_factory.mktemp("mini"))
    generate_dataset(scale="mini", seed=SEED, out_dir=out, formats=("csv",))
    return out


@pytest.fixture(scope="session")
def manifest(mini_dataset: Path) -> dict:
    return json.loads((mini_dataset / "metadata" / "manifest.json").read_text(encoding="utf-8"))
