from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
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


@router.get("/batch-correction/pca-after")
def get_pca_after_correction():
    data = bmr.load_pca_after_correction()
    if data is None:
        raise HTTPException(status_code=404, detail="pca_after_correction.json 不存在，请先运行 merged baseline 流程。")
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


# ==============================
# imputation 评估（Mask-then-Impute）只读 API
# ==============================

@router.get("/imputation-eval/summary")
def get_imputation_eval_summary():
    """
    读取 imputation_eval_report.json 并返回各方法的 RMSE/MAE/NRMSE 汇总。
    需先运行 merged pipeline（--run-imputation-eval）生成产物。
    """
    data = bmr.build_imputation_eval_summary_payload()
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="imputation_eval_report.json 不存在，请先运行 merged pipeline 生成填充评估产物。",
        )
    return data


@router.get("/imputation-eval/feature-rmse")
def get_imputation_eval_feature_rmse():
    """
    读取 imputation_eval_feature.json（特征级 RMSE，用于前端箱线图）。
    """
    data = bmr.load_imputation_eval_feature()
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="imputation_eval_feature.json 不存在，请先运行 merged pipeline 生成填充评估产物。",
        )
    return data


# ==============================
# 差异代谢物分析 API
# ==============================

@router.get("/diff-analysis/groups")
def get_available_groups():
    """
    返回可用于差异分析的 group_label 列表（仅 formal 样本）。
    """
    groups = bmr.load_available_groups()
    return {"groups": groups, "count": len(groups)}


@router.get("/diff-analysis/run")
def run_diff_analysis(
    group1: str = Query(..., description="对照组 group_label"),
    group2: str = Query(..., description="实验组 group_label"),
    fc_threshold: float = Query(1.0, description="|log2FC| 阈值"),
    pvalue_threshold: float = Query(0.05, description="p-value / q-value 显著性阈值"),
    use_fdr: bool = Query(True, description="True=用 q-value(FDR)，False=用原始 p-value"),
):
    """
    对指定两个 group 运行差异代谢物分析（t-test + BH-FDR + log2FC）。
    结果从磁盘缓存读取（如存在），否则实时计算并写入缓存。
    """
    try:
        result = bmr.get_or_run_diff_analysis(
            group1=group1,
            group2=group2,
            fc_threshold=fc_threshold,
            pvalue_threshold=pvalue_threshold,
            use_fdr=use_fdr,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"差异分析失败: {e}")
    return result


# ==============================
# 特征注释 API
# ==============================

@router.get("/annotation/summary")
def get_annotation_summary():
    """
    返回注释汇总统计（特征总数、有代谢物名数量、KEGG/HMDB 覆盖率）。
    若注释文件不存在，自动触发构建。
    """
    try:
        data = bmr.get_or_build_annotation()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注释构建失败: {e}")
    return {
        "available": True,
        "schema_version": data.get("schema_version"),
        "n_features": data.get("n_features"),
        "n_annotated": data.get("n_annotated"),
        "n_with_kegg": data.get("n_with_kegg"),
        "n_with_hmdb": data.get("n_with_hmdb"),
        "coverage_pct": data.get("coverage_pct"),
    }


@router.get("/annotation/features")
def get_annotation_features(
    offset: int = Query(0, ge=0, description="分页起始"),
    limit: int = Query(100, ge=1, le=500, description="每页条数，最大 500"),
    search: Optional[str] = Query(None, description="按代谢物名模糊搜索"),
):
    """
    分页返回特征注释列表（带代谢物名、HMDB/KEGG 链接）。
    支持按代谢物名搜索。
    """
    try:
        data = bmr.get_or_build_annotation()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注释构建失败: {e}")

    features = data.get("features") or []
    # 搜索过滤
    if search:
        kw = search.strip().lower()
        features = [
            f for f in features
            if kw in (f.get("metabolite_name") or "").lower()
            or kw in (f.get("formula") or "").lower()
            or any(kw in kid.lower() for kid in (f.get("kegg_ids") or []))
            or any(kw in hid.lower() for hid in (f.get("hmdb_ids") or []))
        ]

    total = len(features)
    page = features[offset: offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "features": page,
    }
