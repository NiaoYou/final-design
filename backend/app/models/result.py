from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import Column, ForeignKey, Integer, Text

from app.core.database import Base


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, unique=True)

    preprocess_matrix_path = Column(Text, nullable=True)
    imputed_matrix_path = Column(Text, nullable=True)
    batch_corrected_matrix_path = Column(Text, nullable=True)

    # PCA 结果
    pca_before_plot_path = Column(Text, nullable=True)
    pca_after_plot_path = Column(Text, nullable=True)

    # 以 JSON 字符串形式保存指标/坐标，避免额外的文件协议耦合
    metrics_json = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)

