from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """
    使用环境变量覆盖默认值，避免引入额外依赖。
    """

    # backend/app/core/config.py -> backend/
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    DATA_DIR: Path = BASE_DIR / "data"

    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    RESULTS_DIR: Path = DATA_DIR / "results"
    TEMP_DIR: Path = DATA_DIR / "temp"

    DB_PATH: Path = DATA_DIR / "app.sqlite3"

    UPLOAD_MAX_BYTES: int = int(os.getenv("UPLOAD_MAX_BYTES", str(50 * 1024 * 1024)))  # 50MB

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

