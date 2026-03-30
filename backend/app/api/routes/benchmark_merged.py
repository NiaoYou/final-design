from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import benchmark_merged_read as bmr

router = APIRouter(prefix="/api/benchmark/merged", tags=["benchmark_merged"])


@router.get("/summary")
def get_merged_summary():
    return bmr.build_summary_payload()


@router.get("/batch-correction/report")
def get_batch_correction_report():
    data = bmr.load_batch_correction_method_report()
    if data is None:
        raise HTTPException(status_code=404, detail="batch_correction_method_report.json 不存在，请先运行 merged baseline 流程。")
    return data


@router.get("/batch-correction/metrics")
def get_batch_correction_metrics():
    data = bmr.load_batch_correction_metrics()
    if data is None:
        raise HTTPException(status_code=404, detail="batch_correction_metrics.json 不存在，请先运行 merged baseline 流程。")
    return data


@router.get("/files")
def list_merged_files():
    return {"files": bmr.list_downloadable_files(), "download_base": "/api/benchmark/merged/download"}


@router.get("/download/{filename}")
def download_merged_file(filename: str):
    if filename != Path(filename).name or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名。")
    path = bmr.safe_resolve_download(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="文件不存在或不在允许列表内。")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.get("/assets/pca_before_vs_after.png")
def serve_pca_plot():
    p = bmr.pca_plot_path()
    if p is None:
        raise HTTPException(status_code=404, detail="pca_before_vs_after_batch_correction.png 不存在。")
    return FileResponse(p, media_type="image/png")
