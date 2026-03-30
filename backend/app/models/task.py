from __future__ import annotations

import datetime as dt

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False, default="")
    status = Column(String(64), nullable=False, default="uploaded")

    created_at = Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow,
    )

    # 上传文件的物理路径
    file_path = Column(Text, nullable=True)
    # 该任务的结果目录路径
    result_path = Column(Text, nullable=True)

    error_message = Column(Text, nullable=True)

