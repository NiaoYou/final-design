from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.repositories.task_repository import get_task, list_tasks
from app.schemas.task import EvaluationResponse, TaskCreateRequest, TaskResponse
from app.services.batch_service import run_batch_correction
from app.services.evaluation_service import run_evaluation
from app.services.imputation_service import run_imputation
from app.services.preprocess_service import run_preprocess
from app.services.task_service import get_task_configs, set_task_configs
from app.repositories.task_repository import update_task_status

router = APIRouter()


@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db_dep)) -> list[TaskResponse]:
    tasks = list_tasks(db)
    return [
        TaskResponse(
            id=t.id,
            task_name=t.task_name,
            status=t.status,
            created_at=str(t.created_at),
            updated_at=str(t.updated_at),
            error_message=t.error_message,
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_detail(task_id: int, db: Session = Depends(get_db_dep)) -> TaskResponse:
    try:
        t = get_task(db, task_id)
        return TaskResponse(
            id=t.id,
            task_name=t.task_name,
            status=t.status,
            created_at=str(t.created_at),
            updated_at=str(t.updated_at),
            error_message=t.error_message,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks", response_model=TaskResponse)
def create_task_configs(req: TaskCreateRequest, db: Session = Depends(get_db_dep)) -> TaskResponse:
    try:
        set_task_configs(
            db,
            task_id=req.task_id,
            preprocess_config=req.preprocess_config,
            imputation_config=req.imputation_config,
            batch_config=req.batch_config,
            evaluation_config=req.evaluation_config,
        )
        t = get_task(db, req.task_id)
        return TaskResponse(
            id=t.id,
            task_name=t.task_name,
            status=t.status,
            created_at=str(t.created_at),
            updated_at=str(t.updated_at),
            error_message=t.error_message,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/preprocess")
def run_preprocess_endpoint(task_id: int, db: Session = Depends(get_db_dep)) -> Dict[str, Any]:
    try:
        configs = get_task_configs(db, task_id)
        preprocess_config = configs["preprocess_config"]
        return run_preprocess(db, task_id=task_id, preprocess_config=preprocess_config)
    except Exception as e:
        update_task_status(db, task_id, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/impute")
def run_impute_endpoint(task_id: int, db: Session = Depends(get_db_dep)) -> Dict[str, Any]:
    try:
        configs = get_task_configs(db, task_id)
        imputation_config = configs["imputation_config"]
        return run_imputation(db, task_id=task_id, imputation_config=imputation_config)
    except Exception as e:
        update_task_status(db, task_id, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/batch-correct")
def run_batch_endpoint(task_id: int, db: Session = Depends(get_db_dep)) -> Dict[str, Any]:
    try:
        configs = get_task_configs(db, task_id)
        batch_config = configs["batch_config"]
        return run_batch_correction(db, task_id=task_id, batch_config=batch_config)
    except Exception as e:
        update_task_status(db, task_id, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/evaluation", response_model=EvaluationResponse)
def evaluation_endpoint(task_id: int, db: Session = Depends(get_db_dep)) -> EvaluationResponse:
    try:
        configs = get_task_configs(db, task_id)
        evaluation_config = configs["evaluation_config"]
        out = run_evaluation(db, task_id=task_id, evaluation_config=evaluation_config)
        return EvaluationResponse(**out)
    except Exception as e:
        update_task_status(db, task_id, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

