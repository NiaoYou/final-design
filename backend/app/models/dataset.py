from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)

    # 上传后生成数据集，任务配置时会绑定
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)

    original_filename = Column(String(512), nullable=False)
    sample_count = Column(Integer, nullable=False, default=0)
    feature_count = Column(Integer, nullable=False, default=0)

    # 数据列名配置（long format）
    feature_column = Column(String(128), nullable=False)
    sample_column = Column(String(128), nullable=False)
    value_column = Column(String(128), nullable=False)

    batch_column = Column(String(128), nullable=False)
    group_column = Column(String(128), nullable=False)

    data_format = Column(String(32), nullable=False, default="long")

    # 保存后的数据文件路径（原始上传文件路径也可用，但这里便于后续处理）
    stored_path = Column(Text, nullable=True)

