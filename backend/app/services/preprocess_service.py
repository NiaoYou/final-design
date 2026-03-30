from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import get_dataset_by_task_id
from app.repositories.task_repository import update_task_status
from app.utils.dataframe_utils import read_long_dataframe, to_feature_sample_matrix
from app.utils.file_utils import ensure_dir, task_temp_dir


def run_preprocess(
    db: Session,
    *,
    task_id: int,
    preprocess_config: Dict[str, Any],
) -> Dict[str, Any]:
    dataset = get_dataset_by_task_id(db, task_id)
    df_long = read_long_dataframe(str(dataset.stored_path), data_format=dataset.data_format)

    matrix, feature_names = to_feature_sample_matrix(
        df_long,
        feature_column=dataset.feature_column,
        sample_column=dataset.sample_column,
        value_column=dataset.value_column,
    )

    # 缺失率统计
    missing_rate = matrix.isna().mean(axis=1).to_numpy()

    max_missing_rate = float(preprocess_config.get("max_missing_rate", 0.5))
    keep_mask = missing_rate <= max_missing_rate
    if keep_mask.sum() <= 1:
        raise ValueError("特征过滤后剩余特征过少，请调小过滤阈值。")

    matrix = matrix.loc[matrix.index[keep_mask]]

    # log 变换
    log_transform = bool(preprocess_config.get("log_transform", True))
    if log_transform:
        matrix = np.log1p(matrix)

    # 标准化
    normalization = str(preprocess_config.get("normalization", "standardize"))
    if normalization == "standardize":
        means = matrix.mean(axis=1)
        stds = matrix.std(axis=1, ddof=0).replace(0, np.nan)
        matrix = (matrix.sub(means, axis=0)).div(stds, axis=0)

    temp_dir = task_temp_dir(task_id)
    ensure_dir(temp_dir)
    out_path = temp_dir / f"{task_id}_preprocessed.csv"
    # index=feature, columns=sample
    matrix.to_csv(out_path)

    update_task_status(db, task_id, status="preprocess_done")

    return {
        "preprocess_matrix_path": str(out_path),
        "kept_feature_count": int(matrix.shape[0]),
        "discarded_feature_count": int(len(feature_names) - matrix.shape[0]),
    }


def run_preprocess_matrix(
    *,
    sample_by_feature: pd.DataFrame,
    sample_meta: pd.DataFrame,
    feature_meta: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """
    matrix format:
    - sample_by_feature: sample x feature
    - sample_meta: 行与 sample_by_feature 的 index 对齐：
      优先使用 merged_sample_id（跨 batch 合并）；否则使用 sample_col_name
    - feature_meta: feature 注释（当前用于 metadata 保存，不强依赖列结构）
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1) 数值检查：强制转成 float（无法解析将变为 NaN）
    X = sample_by_feature.copy()
    X = X.apply(pd.to_numeric, errors="coerce")

    sample_count_before = int(X.shape[0])
    feature_count_before = int(X.shape[1])
    missing_ratio_before = float(np.isnan(X.to_numpy(dtype=float)).mean()) if feature_count_before > 0 else 1.0

    # 2) 可选：按 sample_type 过滤样本
    include = config.get("sample_type_include")
    exclude = config.get("sample_type_exclude")
    meta = sample_meta.copy()
    if "merged_sample_id" in meta.columns:
        meta = meta.set_index("merged_sample_id").loc[X.index.astype(str)]
    elif "sample_col_name" in meta.columns:
        meta = meta.set_index("sample_col_name").loc[X.index]
    else:
        raise ValueError("sample_meta 缺少 merged_sample_id 或 sample_col_name，无法对齐 matrix 行。")

    if include is not None:
        keep_mask = meta["sample_type"].astype(str).isin([str(v) for v in include])
        keep_samples = meta.index[keep_mask].tolist()
        X = X.loc[keep_samples]
        meta = meta.loc[keep_samples]
    elif exclude is not None:
        keep_mask = ~meta["sample_type"].astype(str).isin([str(v) for v in exclude])
        keep_samples = meta.index[keep_mask].tolist()
        X = X.loc[keep_samples]
        meta = meta.loc[keep_samples]

    sample_count_after_filter = int(X.shape[0])

    # 3) 可选：log 变换
    if bool(config.get("log_transform", False)):
        X = np.log1p(X)

    # 4) 缺失值统计/特征过滤（可选）
    max_feature_missing_rate = config.get("max_feature_missing_rate", 0.5)
    if max_feature_missing_rate is not None:
        missing_per_feature = np.isnan(X.to_numpy(dtype=float)).mean(axis=0) if X.shape[1] > 0 else np.array([])
        keep_features = [c for c, mr in zip(X.columns.tolist(), missing_per_feature.tolist()) if mr <= float(max_feature_missing_rate)]
        if len(keep_features) <= 1:
            raise ValueError("特征过滤后剩余特征过少，请调小 max_feature_missing_rate。")
        X = X.loc[:, keep_features]

    feature_count_after_filter = int(X.shape[1])

    # 5) 标准化/归一化
    normalization = str(config.get("normalization", "standardize")).lower()
    if normalization == "standardize":
        means = X.mean(axis=0)
        stds = X.std(axis=0, ddof=0).replace(0, 1.0)
        X = (X - means) / stds
    elif normalization in {"minmax", "normalize"}:
        mins = X.min(axis=0)
        maxs = X.max(axis=0)
        denom = (maxs - mins).replace(0, 1.0)
        X = (X - mins) / denom
    elif normalization in {"none", "no", "null"}:
        pass
    else:
        raise ValueError(f"不支持的 normalization: {normalization}")

    missing_ratio_after = float(np.isnan(X.to_numpy(dtype=float)).mean()) if X.shape[1] > 0 else 1.0

    preprocessed_path = output_dir / "preprocessed_sample_by_feature.csv"
    X.to_csv(preprocessed_path, index=True)

    report_path = output_dir / "preprocess_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "sample_count_before": sample_count_before,
                "sample_count_after_filter": sample_count_after_filter,
                "feature_count_before": feature_count_before,
                "feature_count_after_filter": feature_count_after_filter,
                "missing_ratio_before": missing_ratio_before,
                "missing_ratio_after": missing_ratio_after,
                "used_config": {
                    "normalization": normalization,
                    "log_transform": bool(config.get("log_transform", False)),
                    "max_feature_missing_rate": config.get("max_feature_missing_rate", 0.5),
                    "sample_type_include": include,
                    "sample_type_exclude": exclude,
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "preprocessed_matrix_path": str(preprocessed_path),
        "preprocess_report_path": str(report_path),
        "kept_feature_count": feature_count_after_filter,
        "sample_count": sample_count_after_filter,
    }

