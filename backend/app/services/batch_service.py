from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.algorithms.batch_correction.combat import run_combat_safe
from app.repositories.dataset_repository import get_dataset_by_task_id
from app.repositories.task_repository import update_task_status
from app.utils.dataframe_utils import extract_sample_metadata, read_long_dataframe
from app.utils.file_utils import ensure_dir, task_temp_dir


def _baseline_location_scale(matrix: pd.DataFrame, batch_labels: np.ndarray) -> pd.DataFrame:
    """
    逐特征-逐批次位置-尺度对齐（baseline）。
    matrix: sample × feature
    """
    from app.algorithms.batch_correction.baseline_location_scale_sample import (
        per_feature_batch_location_scale_baseline,
    )

    X = matrix.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    X_corr = per_feature_batch_location_scale_baseline(X, batch_labels, eps=1e-8)
    return pd.DataFrame(X_corr, index=matrix.index, columns=matrix.columns)


def run_batch_correction(
    db: Session,
    *,
    task_id: int,
    batch_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    通用任务链批次校正接口（用于"单次上传任务"流程）。
    支持 method: 'combat'（strict ComBat via pyComBat）或 'baseline'。
    """
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

    if method == "combat":
        corrected, err = run_combat_safe(matrix, batch_labels)
        if corrected is None:
            raise RuntimeError(f"ComBat 校正失败: {err}")
    elif method == "baseline":
        corrected = _baseline_location_scale(matrix, batch_labels)
    else:
        raise ValueError(f"不支持的批次校正方法: {method}。支持: combat, baseline")

    out_path = temp_dir / f"{task_id}_batch_corrected.csv"
    ensure_dir(out_path.parent)
    corrected.to_csv(out_path)

    update_task_status(db, task_id, status="batch_done")
    return {"batch_corrected_matrix_path": str(out_path), "method": method}


def run_batch_correction_matrix(
    *,
    matrix: pd.DataFrame,
    sample_meta: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: Path,
    covariate_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    矩阵级批次校正服务（用于 benchmark_merged pipeline）。

    支持的 method（config["method"]）：
      - "combat"   : 严格 ComBat（pyComBat 经验 Bayes 实现）
      - "baseline" : per-feature location-scale 基线对齐

    matrix: sample × feature（数值矩阵，已完成缺失值填充）
    sample_meta: 必须包含 batch_id 字段（及 merged_sample_id 或 sample_col_name 作为主键）
    covariate_df: 可选生物学协变量（sample × cov），仅 combat 方法使用
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_field = str(config.get("batch_id_field", "batch_id"))
    if batch_field not in sample_meta.columns:
        report = {"status": "skipped", "reason": f"sample_meta 缺少字段 {batch_field}"}
        report_path = output_dir / "batch_correct_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"batch_correct_report_path": str(report_path), **report}

    # 对齐样本顺序
    if "merged_sample_id" in sample_meta.columns:
        meta = sample_meta.set_index("merged_sample_id").loc[matrix.index.astype(str)]
    elif "sample_col_name" in sample_meta.columns:
        meta = sample_meta.set_index("sample_col_name").loc[matrix.index]
    else:
        meta = sample_meta

    batch_labels = meta[batch_field].astype(str).to_numpy()
    unique_batches = np.unique(batch_labels)
    samples_per_batch = {str(b): int((batch_labels == b).sum()) for b in unique_batches}

    method = str(config.get("method", "combat")).lower()
    parametric = bool(config.get("parametric", True))

    readiness = {
        "n_batches": int(unique_batches.size),
        "batch_ids": unique_batches.tolist(),
        "samples_per_batch": samples_per_batch,
        "min_samples_per_batch": int(min(samples_per_batch.values())) if samples_per_batch else 0,
        "method_requested": method,
        "combat_implemented_in_repo": True,
    }

    if unique_batches.size < 2:
        report = {
            "status": "skipped",
            "reason": f"batch_id 只有 {unique_batches.size} 个，不足以进行批次效应校正。",
            **readiness,
        }
        report_path = output_dir / "batch_correct_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"batch_correct_report_path": str(report_path), **report}

    # ---- 执行校正 ----
    if method == "combat":
        corrected, err = run_combat_safe(
            matrix,
            batch_labels,
            covariate_df=covariate_df,
            parametric=parametric,
        )
        if corrected is None:
            # ComBat 失败时回退到 baseline，并在报告中说明
            corrected = _baseline_location_scale(matrix, batch_labels)
            status = "fallback_to_baseline"
            reason = f"ComBat 运行失败（{err}），已自动回退到 baseline 方法。"
        else:
            status = "success"
            reason = f"strict ComBat（neuroCombat，Johnson et al. 2007）成功运行，参数模式: {'parametric' if parametric else 'non-parametric'}。"
    elif method == "baseline":
        corrected = _baseline_location_scale(matrix, batch_labels)
        status = "success"
        reason = "baseline（per-feature location-scale）校正完成。"
    else:
        report = {
            "status": "error",
            "reason": f"不支持的方法: {method}。支持: combat, baseline",
            **readiness,
        }
        report_path = output_dir / "batch_correct_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"batch_correct_report_path": str(report_path), **report}

    # 保存校正后矩阵
    corrected_path = output_dir / "batch_corrected_sample_by_feature.csv"
    corrected.to_csv(corrected_path, index=True)

    report = {
        "status": status,
        "reason": reason,
        "method": method,
        "parametric": parametric,
        "corrected_matrix_path": str(corrected_path),
        **readiness,
    }
    report_path = output_dir / "batch_correct_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    readiness_path = output_dir / "batch_correction_readiness.json"
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "batch_correct_report_path": str(report_path),
        "batch_correction_readiness_path": str(readiness_path),
        "corrected_matrix_path": str(corrected_path),
        **report,
    }
