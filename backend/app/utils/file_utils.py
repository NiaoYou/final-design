from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import Settings


def ensure_dir(path: Path) -> None:
    os.makedirs(path, exist_ok=True)


def new_uuid_str() -> str:
    return uuid.uuid4().hex


def task_result_dir(task_id: int) -> Path:
    return Settings.RESULTS_DIR / f"task_{task_id}"


def task_temp_dir(task_id: int) -> Path:
    return Settings.TEMP_DIR / f"task_{task_id}"


def saved_upload_path(task_id: int, original_filename: str) -> Path:
    """
    上传文件统一放到 uploads/，并按 task_id 拆分文件夹便于清理。
    """

    ext = Path(original_filename).suffix
    name = Path(original_filename).stem
    return Settings.UPLOAD_DIR / f"task_{task_id}" / f"{name}_{new_uuid_str()}{ext}"


def safe_text_path(p: Optional[Path]) -> Optional[str]:
    if p is None:
        return None
    return str(p)

