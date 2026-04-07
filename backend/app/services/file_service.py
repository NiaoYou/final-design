from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import create_dataset
from app.repositories.task_repository import create_task, update_task_status
from app.utils.dataframe_utils import (
    df_to_preview_records,
    extract_sample_metadata,
    read_long_dataframe,
    to_feature_sample_matrix,
)
from app.utils.file_utils import ensure_dir, saved_upload_path, task_result_dir


def _guess_task_name(original_filename: str) -> str:
    stem = Path(original_filename).stem
    return stem[:80] if stem else "Metabolomics Task"


def save_upload_file(upload_file: UploadFile, target_path: Path) -> None:
    ensure_dir(target_path.parent)
    with target_path.open("wb") as f:
        # UploadFile.file is a SpooledTemporaryFile; read() 兼容大文件但这里 MVP 简化
        f.write(upload_file.file.read())


def create_task_and_dataset_from_upload(
    db: Session,
    *,
    upload_file: UploadFile,
    task_name: Optional[str],
    feature_column: str,
    sample_column: str,
    value_column: str,
    batch_column: str,
    group_column: str,
    data_format: str = "long",
) -> Dict[str, Any]:
    original_filename = upload_file.filename or "uploaded_file"

    task = create_task(
        db,
        task_name=task_name or _guess_task_name(original_filename),
        status="uploaded",
        file_path="",
        result_path="",
    )

    # 生成物理路径并更新 task
    upload_path = saved_upload_path(task.id, original_filename)
    result_dir = task_result_dir(task.id)
    ensure_dir(result_dir)

    task.file_path = str(upload_path)
    task.result_path = str(result_dir)
    db.commit()
    db.refresh(task)

    save_upload_file(upload_file, upload_path)

    # 解析 long 表并计算统计信息
    df_long = read_long_dataframe(str(upload_path), data_format=data_format)

    # 基础校验：列是否存在
    required_cols = {feature_column, sample_column, value_column, batch_column, group_column}
    missing = required_cols - set(df_long.columns)
    if missing:
        raise ValueError(f"上传数据缺少必要列: {sorted(missing)}")

    matrix, feature_names = to_feature_sample_matrix(
        df_long,
        feature_column=feature_column,
        sample_column=sample_column,
        value_column=value_column,
    )

    batch_labels, group_labels = extract_sample_metadata(
        df_long,
        sample_column=sample_column,
        batch_column=batch_column,
        group_column=group_column,
        matrix_columns=matrix.columns.tolist(),
    )

    preview_df = df_long.head(20)
    preview_records = preview_df.to_dict(orient="records")

    dataset = create_dataset(
        db,
        task_id=task.id,
        original_filename=original_filename,
        sample_count=int(matrix.shape[1]),
        feature_count=int(matrix.shape[0]),
        feature_column=feature_column,
        sample_column=sample_column,
        value_column=value_column,
        batch_column=batch_column,
        group_column=group_column,
        data_format=data_format,
        stored_path=str(upload_path),
    )

    return {
        "task_id": task.id,
        "dataset_id": dataset.id,
        "original_filename": original_filename,
        "preview": preview_records,
        "sample_count": int(matrix.shape[1]),
        "feature_count": int(matrix.shape[0]),
    }

