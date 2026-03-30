from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import Column, ForeignKey, Integer, Text

from app.core.database import Base


def _dump_json(v: Optional[Dict[str, Any]]) -> Optional[str]:
    if v is None:
        return None
    return json.dumps(v, ensure_ascii=False)


class Parameters(Base):
    __tablename__ = "parameters"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)

    preprocess_config_json = Column(Text, nullable=False, default="{}")
    imputation_config_json = Column(Text, nullable=False, default="{}")
    batch_config_json = Column(Text, nullable=False, default="{}")
    analysis_config_json = Column(Text, nullable=False, default="{}")

    # 注意：这里用 Text 存 JSON，SQLite 下兼容更好。

