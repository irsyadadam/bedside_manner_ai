"""Per-phase logging: stdout + logs/<phase>_<UTC-timestamp>.log."""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


def setup_logging(
    phase: str,
    level: str = "INFO",
    logs_dir: str | Path = "logs",
) -> Path:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = Path(logs_dir) / f"{phase}_{ts}.log"

    fmt = "%(asctime)s %(levelname)-7s %(name)s :: %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )
    # Tame noisy 3rd-party loggers.
    for noisy in ("urllib3", "requests", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return log_path
