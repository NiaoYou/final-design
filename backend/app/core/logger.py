from __future__ import annotations

import logging
import sys

from app.core.config import Settings


def setup_logging() -> None:
    level = getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

