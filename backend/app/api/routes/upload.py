from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.repositories.dataset_repository import get_dataset_by_task_id
from app.services.file_service import create_task_and_dataset_from_upload
from app.utils.dataframe_utils import df_to_preview_records, read_long_dataframe
from app.schemas.upload import UploadPreviewResponse, UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
def upload_dataset(
    file: UploadFile = File(...),
    task_name: Optional[str] = Form(None),
    data_format: str = Form("long"),
    feature_column: str = Form(..., description="long 格式：特征列名"),
    sample_column: str = Form(..., description="long 格式：样本列名"),
    value_column: str = Form(..., description="long 格式：数值列名"),
    batch_column: str = Form(..., description="long 格式：批次列名"),
    group_column: str = Form(..., description="long 格式：分组列名"),
    db: Session = Depends(get_db_dep),
) -> UploadResponse:
    try:
        out = create_task_and_dataset_from_upload(
            db,
            upload_file=file,
            task_name=task_name,
            data_format=data_format,
            feature_column=feature_column,
            sample_column=sample_column,
            value_column=value_column,
            batch_column=batch_column,
            group_column=group_column,
        )
        return UploadResponse(**out)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets/{task_id}/preview", response_model=UploadPreviewResponse)
def preview_dataset(
    task_id: int,
    db: Session = Depends(get_db_dep),
) -> UploadPreviewResponse:
    try:
        ds = get_dataset_by_task_id(db, task_id)
        df_long = read_long_dataframe(str(ds.stored_path), data_format=ds.data_format)
        preview = df_to_preview_records(df_long, limit=20)
        return UploadPreviewResponse(dataset_id=ds.id, preview=preview)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

