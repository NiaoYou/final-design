from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    task_id: int = Field(..., description="用于后续预览/分析的任务ID")
    dataset_id: int = Field(..., description="数据集ID（与任务关联）")
    original_filename: str
    sample_count: int
    feature_count: int
    preview: List[Dict[str, Any]]


class UploadPreviewResponse(BaseModel):
    dataset_id: int
    preview: List[Dict[str, Any]]

