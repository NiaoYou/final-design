from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    task_id: int = Field(..., description="上传后返回的 task_id")
    task_name: Optional[str] = Field(None)

    preprocess_config: Dict[str, Any] = Field(default_factory=dict)
    imputation_config: Dict[str, Any] = Field(default_factory=dict)
    batch_config: Dict[str, Any] = Field(default_factory=dict)
    evaluation_config: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: int
    task_name: str
    status: str
    created_at: str
    updated_at: str
    error_message: Optional[str] = None


class EvaluationResponse(BaseModel):
    task_id: int
    pca_before: Dict[str, Any]
    pca_after: Dict[str, Any]
    pca_plot_path: str

