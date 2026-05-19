"""Load the pipeline.yaml config. Single source of truth across modules."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = "config/pipeline.yaml"


@lru_cache(maxsize=8)
def load_config(path: str | os.PathLike = DEFAULT_CONFIG_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p.resolve()}")
    return yaml.safe_load(p.read_text(encoding="utf-8"))
