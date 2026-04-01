from __future__ import annotations

import datetime as dt

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> dt.datetime:
    """返回当前 UTC 时间（兼容 Python 3.12+ 废弃 utcnow）。"""
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False, default="")
    status = Column(String(64), nullable=False, default="uploaded")

    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # 上传文件的物理路径
    file_path = Column(Text, nullable=True)
    # 该任务的结果目录路径
    result_path = Column(Text, nullable=True)

    error_message = Column(Text, nullable=True)

