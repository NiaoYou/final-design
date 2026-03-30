from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import get_dataset_by_task_id
from app.repositories.task_repository import update_task_status
from app.utils.dataframe_utils import extract_sample_metadata, read_long_dataframe
from app.utils.file_utils import ensure_dir, task_temp_dir


def _combat_like_correction(matrix: pd.DataFrame, batch_labels: np.ndarray) -> pd.DataFrame:
    """
    简化版批次校正：
    - 对每个特征、每个批次，先标准化到“该批次自身均值/方差”
    - 再映射回全局均值/方差

    注意：这不是标准 ComBat 实现，但适合作为 MVP 可运行占位逻辑。
    """

    X = matrix.to_numpy(dtype=float)
    overall_mean = np.nanmean(X, axis=1, keepdims=True)
    overall_std = np.nanstd(X, axis=1, keepdims=True, ddof=0)
    overall_std = np.where(overall_std == 0, 1.0, overall_std)

    corrected = X.copy()
    unique_batches = np.unique(batch_labels)
    for b in unique_batches:
        idx = batch_labels == b
        if idx.sum() == 0:
            continue
        batch_mean = np.nanmean(X[:, idx], axis=1, keepdims=True)
        batch_std = np.nanstd(X[:, idx], axis=1, keepdims=True, ddof=0)
        batch_std = np.where(batch_std == 0, 1.0, batch_std)
        corrected[:, idx] = (X[:, idx] - batch_mean) / batch_std * overall_std + overall_mean

    return pd.DataFrame(corrected, index=matrix.index, columns=matrix.columns)


def run_batch_correction(
    db: Session,
    *,
    task_id: int,
    batch_config: Dict[str, Any],
) -> Dict[str, Any]:
    dataset = get_dataset_by_task_id(db, task_id)

    temp_dir = task_temp_dir(task_id)
    imputed_path = temp_dir / f"{task_id}_imputed.csv"
    if not imputed_path.exists():
        raise FileNotFoundError("缺少 imputed 矩阵，请先调用 impute。")

    matrix = pd.read_csv(imputed_path, index_col=0)

    df_long = read_long_dataframe(str(dataset.stored_path), data_format=dataset.data_format)
    batch_labels, group_labels = extract_sample_metadata(
        df_long,
        sample_column=dataset.sample_column,
        batch_column=dataset.batch_column,
        group_column=dataset.group_column,
        matrix_columns=matrix.columns.tolist(),
    )

    method = str(batch_config.get("method", "combat")).lower()
    if method != "combat":
        raise ValueError("MVP 目前仅支持 method='combat'（简化实现）。")

    corrected = _combat_like_correction(matrix, batch_labels=batch_labels)

    out_path = temp_dir / f"{task_id}_batch_corrected.csv"
    ensure_dir(out_path.parent)
    corrected.to_csv(out_path)

    update_task_status(db, task_id, status="batch_done")
    return {"batch_corrected_matrix_path": str(out_path)}


def run_batch_correction_matrix(
    *,
    matrix: pd.DataFrame,
    sample_meta: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """
    matrix format:
    - matrix: sample x feature (数值矩阵)
    - sample_meta: 包含 batch_id，用于判定是否有足够 batch 做校正

    诚实说明：**严格 ComBat（Bioconductor 语义）尚未在本仓库实现**。
    本函数仅做 batch 条件检查、样本数统计与可读报告，不输出“已完成 ComBat 校正”的矩阵。
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_field = str(config.get("batch_id_field", "batch_id"))
    if batch_field not in sample_meta.columns:
        report = {"status": "skipped", "reason": f"sample_meta 缺少字段 {batch_field}"}
        report_path = output_dir / "batch_correct_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"batch_correct_report_path": str(report_path), **report}

    # 对齐样本顺序（跨 batch 合并使用 merged_sample_id）
    if "merged_sample_id" in sample_meta.columns:
        meta = sample_meta.set_index("merged_sample_id").loc[matrix.index.astype(str)]
    elif "sample_col_name" in sample_meta.columns:
        meta = sample_meta.set_index("sample_col_name").loc[matrix.index]
    else:
        meta = sample_meta

    batch_ids = meta[batch_field].dropna().astype(str).unique().tolist()
    method = str(config.get("method", "combat")).lower()

    samples_per_batch = meta.groupby(batch_field).size().to_dict()
    samples_per_batch = {str(k): int(v) for k, v in samples_per_batch.items()}

    readiness = {
        "n_batches": len(batch_ids),
        "batch_ids": batch_ids,
        "samples_per_batch": samples_per_batch,
        "min_samples_per_batch": int(min(samples_per_batch.values())) if samples_per_batch else 0,
        "strict_combat_implemented_in_repo": False,
        "can_run_real_combat_from_data_alone": len(batch_ids) >= 2 and min(samples_per_batch.values()) >= 2
        if samples_per_batch
        else False,
        "blockers": [],
    }
    if len(batch_ids) < 2:
        readiness["blockers"].append("batch_id 唯一值少于 2，无法做跨批次校正。")
    if readiness["min_samples_per_batch"] < 2:
        readiness["blockers"].append("存在样本数 <2 的 batch，ComBat 等模型通常不稳定或需特殊处理。")

    if len(batch_ids) < 2:
        report = {
            "status": "skipped",
            "reason": f"batch_id 只有 1 个（{batch_ids[0]}），不足以进行批次效应校正。",
            "batch_id_count": len(batch_ids),
            "batch_ids": batch_ids,
            "batch_correction_readiness": readiness,
            "strict_combat_implemented": False,
        }
    else:
        # 多 batch：数据上已具备“尝试校正”的条件，但严格 ComBat 仍未实现
        report = {
            "status": "not_implemented",
            "reason": (
                "已检测到多个 batch_id，具备跨批次校正的数据结构；"
                "但本仓库尚未实现严格 ComBat（及协变量/设计矩阵等完整流程），"
                "因此不会生成已 ComBat 校正的输出矩阵。"
            ),
            "batch_id_count": len(batch_ids),
            "batch_ids": batch_ids,
            "method_requested": method,
            "batch_correction_readiness": readiness,
            "strict_combat_implemented": False,
        }

    report_path = output_dir / "batch_correct_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    readiness_path = output_dir / "batch_correction_readiness.json"
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "batch_correct_report_path": str(report_path),
        "batch_correction_readiness_path": str(readiness_path),
        **report,
    }

