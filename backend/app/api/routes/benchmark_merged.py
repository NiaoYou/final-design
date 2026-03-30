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


# ==============================
# evaluation（方法对比实验）只读 API
# ==============================


@router.get("/evaluation/summary")
def get_evaluation_summary():
    data = bmr.build_evaluation_summary_payload()
    if data is None:
        raise HTTPException(status_code=404, detail="evaluation_report.json 不存在，请先运行 merged pipeline 生成 evaluation 产物。")
    return data


@router.get("/evaluation/table")
def get_evaluation_table():
    rows = bmr.load_evaluation_table_rows()
    if rows is None:
        raise HTTPException(status_code=404, detail="evaluation_table.csv 不存在，请先运行 merged pipeline 生成 evaluation 产物。")
    return {"rows": rows}


@router.get("/evaluation/pca-image")
def get_evaluation_pca_image():
    p = bmr.evaluation_pca_image_path()
    if p is None:
        raise HTTPException(status_code=404, detail="pca_before_vs_after.png 不存在。")
    return FileResponse(p, media_type="image/png")


@router.get("/evaluation/pca/{method}")
def get_evaluation_method_pca(method: str):
    data = bmr.load_evaluation_method_pca(method)
    if data is None:
        raise HTTPException(status_code=404, detail=f"pca_{method}.json 不存在或方法名不合法。")
    return data


@router.get("/evaluation/files")
def list_evaluation_files():
    return {
        "files": bmr.list_evaluation_downloadable_files(),
        "download_base": "/api/benchmark/merged/evaluation/download",
    }


@router.get("/evaluation/download/{filename}")
def download_evaluation_file(filename: str):
    if filename != Path(filename).name or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名。")
    path = bmr.safe_resolve_evaluation_download(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="文件不存在或不在允许列表内。")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")
