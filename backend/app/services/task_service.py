from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.parameters import Parameters
from app.repositories.dataset_repository import get_dataset_by_task_id
from app.repositories.task_repository import get_task, update_task_status


def set_task_configs(
    db: Session,
    *,
    task_id: int,
    preprocess_config: Dict[str, Any],
    imputation_config: Dict[str, Any],
    batch_config: Dict[str, Any],
    evaluation_config: Dict[str, Any],
) -> Parameters:
    # 确认任务/数据集存在
    get_dataset_by_task_id(db, task_id)

    params = db.query(Parameters).filter(Parameters.task_id == task_id).first()
    if params is None:
        params = Parameters(task_id=task_id)
        db.add(params)

    params.preprocess_config_json = json.dumps(preprocess_config, ensure_ascii=False)
    params.imputation_config_json = json.dumps(imputation_config, ensure_ascii=False)
    params.batch_config_json = json.dumps(batch_config, ensure_ascii=False)
    params.analysis_config_json = json.dumps(evaluation_config, ensure_ascii=False)

    db.commit()
    db.refresh(params)
    update_task_status(db, task_id, status="configured")
    return params


def update_task_status_safe(
    db: Session,
    *,
    task_id: int,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    update_task_status(db, task_id, status=status, error_message=error_message)


def get_task_configs(db: Session, task_id: int) -> Dict[str, Any]:
    params = db.query(Parameters).filter(Parameters.task_id == task_id).first()
    if params is None:
        return {
            "preprocess_config": {},
            "imputation_config": {},
            "batch_config": {},
            "evaluation_config": {},
        }

    return {
        "preprocess_config": json.loads(params.preprocess_config_json or "{}"),
        "imputation_config": json.loads(params.imputation_config_json or "{}"),
        "batch_config": json.loads(params.batch_config_json or "{}"),
        "evaluation_config": json.loads(params.analysis_config_json or "{}"),
    }

