from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.dataset import Dataset


def create_dataset(
    db: Session,
    *,
    task_id: int,
    original_filename: str,
    sample_count: int,
    feature_count: int,
    feature_column: str,
    sample_column: str,
    value_column: str,
    batch_column: str,
    group_column: str,
    data_format: str,
    stored_path: Optional[str],
) -> Dataset:
    dataset = Dataset(
        task_id=task_id,
        original_filename=original_filename,
        sample_count=sample_count,
        feature_count=feature_count,
        feature_column=feature_column,
        sample_column=sample_column,
        value_column=value_column,
        batch_column=batch_column,
        group_column=group_column,
        data_format=data_format,
        stored_path=stored_path,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_by_task_id(db: Session, task_id: int) -> Dataset:
    ds = db.query(Dataset).filter(Dataset.task_id == task_id).first()
    if ds is None:
        raise ValueError(f"Dataset 不存在: task_id={task_id}")
    return ds

