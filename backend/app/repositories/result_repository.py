from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.result import Result


def get_or_create_result(db: Session, task_id: int) -> Result:
    result = db.query(Result).filter(Result.task_id == task_id).first()
    if result is not None:
        return result
    result = Result(task_id=task_id)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def update_result_paths(
    db: Session,
    task_id: int,
    *,
    preprocess_matrix_path: str | None = None,
    imputed_matrix_path: str | None = None,
    batch_corrected_matrix_path: str | None = None,
    pca_before_plot_path: str | None = None,
    pca_after_plot_path: str | None = None,
    pca_plot_path: str | None = None,
) -> Result:
    result = get_or_create_result(db, task_id)

    if preprocess_matrix_path is not None:
        result.preprocess_matrix_path = preprocess_matrix_path
    if imputed_matrix_path is not None:
        result.imputed_matrix_path = imputed_matrix_path
    if batch_corrected_matrix_path is not None:
        result.batch_corrected_matrix_path = batch_corrected_matrix_path
    if pca_before_plot_path is not None:
        result.pca_before_plot_path = pca_before_plot_path
    if pca_after_plot_path is not None:
        result.pca_after_plot_path = pca_after_plot_path
    if pca_plot_path is not None:
        # 简化：如果只维护一个 plot path 就填到 before/after 里，前端可自行选择
        result.pca_after_plot_path = pca_plot_path

    db.commit()
    db.refresh(result)
    return result


def update_metrics_json(
    db: Session,
    task_id: int,
    *,
    metrics: Dict[str, Any] | None = None,
    summary: Dict[str, Any] | None = None,
) -> Result:
    result = get_or_create_result(db, task_id)
    if metrics is not None:
        result.metrics_json = json.dumps(metrics, ensure_ascii=False)
    if summary is not None:
        result.summary_json = json.dumps(summary, ensure_ascii=False)
    db.commit()
    db.refresh(result)
    return result


def get_result_by_task_id(db: Session, task_id: int) -> Optional[Result]:
    return db.query(Result).filter(Result.task_id == task_id).first()

