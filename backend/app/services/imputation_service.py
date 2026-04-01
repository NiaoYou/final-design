from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import get_dataset_by_task_id
from app.repositories.task_repository import update_task_status
from app.utils.file_utils import ensure_dir, task_temp_dir


def run_imputation(
    db: Session,
    *,
    task_id: int,
    imputation_config: Dict[str, Any],
) -> Dict[str, Any]:
    dataset = get_dataset_by_task_id(db, task_id)
    temp_dir = task_temp_dir(task_id)
    preprocessed_path = temp_dir / f"{task_id}_preprocessed.csv"
    if not preprocessed_path.exists():
        raise FileNotFoundError("缺少预处理矩阵，请先调用 preprocess。")

    matrix = pd.read_csv(preprocessed_path, index_col=0)

    method = str(imputation_config.get("method", "mean")).lower()
    if method in {"mean", "median"}:
        # 每个特征（行）用自身在样本维度上的统计量填充
        matrix = matrix.apply(
            lambda row: row.fillna(row.mean() if method == "mean" else row.median()),
            axis=1,
        )
    elif method == "knn":
        k = int(imputation_config.get("knn_k", 5))
        # sklearn 以"行=样本、列=特征"的方式工作，因此需要转置
        # matrix 格式为 feature×sample，转置后 n_rows=样本数，需保证 k < n_samples
        n_samples = matrix.shape[1]
        k = min(k, max(1, n_samples - 1))
        X = matrix.to_numpy().T
        imputer = KNNImputer(n_neighbors=k)
        X_filled = imputer.fit_transform(X)
        matrix = pd.DataFrame(X_filled.T, index=matrix.index, columns=matrix.columns)
    else:
        raise ValueError(f"不支持的填充方法: {method}")

    out_path = temp_dir / f"{task_id}_imputed.csv"
    matrix.to_csv(out_path)

    update_task_status(db, task_id, status="impute_done")
    return {"imputed_matrix_path": str(out_path)}


def run_imputation_matrix(
    *,
    matrix: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """
    matrix format:
    - matrix: sample x feature
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    X = matrix.copy().apply(pd.to_numeric, errors="coerce")
    n_samples, n_features = int(X.shape[0]), int(X.shape[1])
    if n_features <= 0 or n_samples <= 0:
        raise ValueError("imputation: matrix 为空或维度非法。")

    missing_ratio_before = float(np.isnan(X.to_numpy(dtype=float)).mean())

    method = str(config.get("method", "mean")).lower()
    if method in {"mean", "median"}:
        arr = X.to_numpy(dtype=float)
        if method == "mean":
            fills = np.nanmean(arr, axis=0)
        else:
            fills = np.nanmedian(arr, axis=0)
        # 全缺失特征会导致 fills 为 nan
        fills = np.nan_to_num(fills, nan=0.0)
        filled = np.where(np.isnan(arr), fills, arr)
        X_filled = pd.DataFrame(filled, index=X.index, columns=X.columns)
    elif method == "knn":
        k = int(config.get("knn_k", 5))
        if n_samples < 2:
            raise ValueError("knn imputation 至少需要 2 个样本。")
        k = min(k, n_samples - 1)
        from sklearn.impute import KNNImputer

        imputer = KNNImputer(n_neighbors=k)
        arr = X.to_numpy(dtype=float)
        filled = imputer.fit_transform(arr)
        X_filled = pd.DataFrame(filled, index=X.index, columns=X.columns)
    else:
        raise ValueError(f"不支持的填充方法: {method}")

    missing_ratio_after = float(np.isnan(X_filled.to_numpy(dtype=float)).mean())

    imputed_path = output_dir / "imputed_sample_by_feature.csv"
    X_filled.to_csv(imputed_path, index=True)

    report_path = output_dir / "imputation_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "method": method,
                "knn_k": config.get("knn_k", None),
                "n_samples": n_samples,
                "n_features": n_features,
                "missing_ratio_before": missing_ratio_before,
                "missing_ratio_after": missing_ratio_after,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "imputed_matrix_path": str(imputed_path),
        "imputation_report_path": str(report_path),
        "missing_ratio_before": missing_ratio_before,
        "missing_ratio_after": missing_ratio_after,
        "method": method,
    }

