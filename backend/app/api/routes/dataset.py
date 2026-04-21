"""
dataset.py
多数据集通用 API 路由。

prefix: /api/dataset/{dataset}
支持的 dataset: benchmark | amide | bioheart | mi

对于 benchmark，大部分接口直接代理到已有的 benchmark_merged_read 逻辑；
对于其他数据集，使用 dataset_read 服务。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.services import dataset_read as dr

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

# ──────────────────────────────────────────────────────────────────────────────
# 数据集列表（无需 dataset 参数）
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/list")
def list_datasets():
    """返回所有已注册数据集及其可用状态。"""
    return {"datasets": dr.list_available_datasets()}


# ──────────────────────────────────────────────────────────────────────────────
# 以下接口均以 dataset 为路径参数
# ──────────────────────────────────────────────────────────────────────────────

def _validate(dataset: str) -> str:
    try:
        return dr.validate_dataset(dataset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{dataset}/summary")
def get_dataset_summary(dataset: str):
    """返回数据集基本摘要（样本数、特征数、批次列表等）。"""
    ds = _validate(dataset)
    # benchmark 特殊处理：代理到 benchmark_merged_read
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        return bmr.build_summary_payload()
    return dr.build_summary_payload(ds)


@router.get("/{dataset}/batch-correction/report")
def get_batch_correction_report(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        data = bmr.load_batch_correction_method_report()
    else:
        data = dr.load_batch_correction_method_report(ds)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"batch_correction_method_report.json 不存在（{ds}），请先运行 pipeline 脚本。"
        )
    return data


@router.get("/{dataset}/batch-correction/metrics")
def get_batch_correction_metrics(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        data = bmr.load_batch_correction_metrics()
    else:
        data = dr.load_batch_correction_metrics(ds)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"batch_correction_metrics.json 不存在（{ds}），请先运行 pipeline 脚本。"
        )
    return data


@router.get("/{dataset}/batch-correction/pca-after")
def get_pca_after_correction(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        data = bmr.load_pca_after_correction()
    else:
        data = dr.load_pca_after_correction(ds)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"pca_after_correction.json 不存在（{ds}），请先运行 pipeline 脚本。"
        )
    return data


@router.get("/{dataset}/files")
def list_dataset_files(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        files = bmr.list_downloadable_files()
        return {"files": files, "download_base": f"/api/dataset/{ds}/download"}
    files = dr.list_downloadable_files(ds)
    return {"files": files, "download_base": f"/api/dataset/{ds}/download"}


@router.get("/{dataset}/download/{filename}")
def download_dataset_file(dataset: str, filename: str):
    if filename != Path(filename).name or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名。")
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        path = bmr.safe_resolve_download(filename)
    else:
        path = dr.safe_resolve_download(ds, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="文件不存在或不在允许列表内。")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.get("/{dataset}/assets/pca_before_vs_after.png")
def serve_pca_plot(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        p = bmr.pca_plot_path()
    else:
        p = dr.pca_plot_path(ds)
    if p is None:
        raise HTTPException(status_code=404, detail="pca_before_vs_after_batch_correction.png 不存在。")
    return FileResponse(p, media_type="image/png")


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation（方法对比）
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/{dataset}/evaluation/summary")
def get_evaluation_summary(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        data = bmr.build_evaluation_summary_payload()
    else:
        data = dr.build_evaluation_summary_payload(ds)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"evaluation_report.json 不存在（{ds}），请先运行 pipeline 脚本生成 evaluation 产物。"
        )
    return data


@router.get("/{dataset}/evaluation/table")
def get_evaluation_table(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        rows = bmr.load_evaluation_table_rows()
    else:
        rows = dr.load_evaluation_table_rows(ds)
    if rows is None:
        raise HTTPException(
            status_code=404,
            detail=f"evaluation_table.csv 不存在（{ds}）。"
        )
    return {"rows": rows}


@router.get("/{dataset}/evaluation/pca-image")
def get_evaluation_pca_image(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        p = bmr.evaluation_pca_image_path()
    else:
        p = dr.evaluation_pca_image_path(ds)
    if p is None:
        raise HTTPException(status_code=404, detail="evaluation pca 图不存在。")
    return FileResponse(p, media_type="image/png")


@router.get("/{dataset}/evaluation/pca/{method}")
def get_evaluation_method_pca(dataset: str, method: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        data = bmr.load_evaluation_method_pca(method)
    else:
        data = dr.load_evaluation_method_pca(ds, method)
    if data is None:
        raise HTTPException(status_code=404, detail=f"pca_{method}.json 不存在或方法名不合法。")
    return data


@router.get("/{dataset}/evaluation/files")
def list_evaluation_files(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        files = bmr.list_evaluation_downloadable_files()
    else:
        files = dr.list_evaluation_downloadable_files(ds)
    return {
        "files": files,
        "download_base": f"/api/dataset/{ds}/evaluation/download",
    }


@router.get("/{dataset}/evaluation/download/{filename}")
def download_evaluation_file(dataset: str, filename: str):
    if filename != Path(filename).name or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名。")
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        path = bmr.safe_resolve_evaluation_download(filename)
    else:
        path = dr.safe_resolve_evaluation_download(ds, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="文件不存在或不在允许列表内。")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


# ──────────────────────────────────────────────────────────────────────────────
# 差异分析
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/{dataset}/diff-analysis/groups")
def get_available_groups(dataset: str):
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        groups = bmr.load_available_groups()
    else:
        groups = dr.load_available_groups(ds)
    return {"groups": groups, "count": len(groups)}


@router.get("/{dataset}/diff-analysis/run")
def run_diff_analysis(
    dataset: str,
    group1: str = Query(..., description="对照组 group_label"),
    group2: str = Query(..., description="实验组 group_label"),
    fc_threshold: float = Query(1.0, ge=0.0, le=20.0, description="|log2FC| 阈值"),
    pvalue_threshold: float = Query(0.05, gt=0.0, le=1.0, description="显著性阈值"),
    use_fdr: bool = Query(True, description="True=FDR，False=原始 p-value"),
):
    """对指定数据集的两组样本运行差异代谢物分析。"""
    ds = _validate(dataset)
    g1 = group1.strip()
    g2 = group2.strip()
    if not g1 or not g2:
        raise HTTPException(status_code=400, detail="group1 和 group2 不能为空。")
    if g1 == g2:
        raise HTTPException(status_code=400, detail="group1 与 group2 不能相同。")

    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        try:
            result = bmr.get_or_run_diff_analysis(
                group1=g1, group2=g2,
                fc_threshold=fc_threshold,
                pvalue_threshold=pvalue_threshold,
                use_fdr=use_fdr,
            )
        except (FileNotFoundError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"差异分析失败: {e}")
        return result

    # 非 benchmark 数据集的差异分析
    from app.services.differential_analysis_service import run_differential_analysis_for_dataset
    try:
        result = run_differential_analysis_for_dataset(
            dataset_dir=dr.dataset_root(ds),
            pipeline_dir=dr.dataset_pipeline_dir(ds),
            group1=g1,
            group2=g2,
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


# ──────────────────────────────────────────────────────────────────────────────
# 特征注释（Annotation）
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/{dataset}/annotation/summary")
def get_annotation_summary(dataset: str):
    """返回数据集特征注释汇总（代谢物名称/HMDB/KEGG 覆盖率）。"""
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        try:
            data = bmr.get_or_build_annotation()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"注释构建失败: {e}")
        n_features = data.get("n_features") or 0
        n_annotated = data.get("n_annotated") or 0
        coverage_pct = round(n_annotated / n_features * 100, 1) if n_features else 0.0
        return {
            "available": True,
            "n_features": n_features,
            "n_annotated": n_annotated,
            "n_with_kegg": data.get("n_with_kegg"),
            "n_with_hmdb": data.get("n_with_hmdb"),
            "coverage_pct": data.get("coverage_pct", coverage_pct),
        }
    # 非 benchmark：直接读取预建的 annotated_feature_meta.json
    ann_path = dr.dataset_pipeline_dir(ds) / "annotated_feature_meta.json"
    if not ann_path.is_file():
        raise HTTPException(status_code=404, detail="annotated_feature_meta.json 不存在，请先运行 build_named_dataset_annotation.py。")
    import json
    ann = json.loads(ann_path.read_text(encoding="utf-8"))
    n_features = ann.get("n_features") or 0
    n_annotated = ann.get("n_annotated") or 0
    n_with_kegg = ann.get("n_with_kegg") or 0
    # 计算 n_with_hmdb 和 coverage_pct（JSON 中可能缺失）
    features_list = ann.get("features") or []
    n_with_hmdb = ann.get("n_with_hmdb") or sum(
        1 for f in features_list if f.get("hmdb_ids")
    )
    coverage_pct = round(n_annotated / n_features * 100, 1) if n_features else 0.0
    return {
        "available": True,
        "n_features": n_features,
        "n_annotated": n_annotated,
        "n_with_kegg": n_with_kegg,
        "n_with_hmdb": n_with_hmdb,
        "coverage_pct": coverage_pct,
        "annotation_source": ann.get("annotation_source"),
    }


@router.get("/{dataset}/annotation/features")
def get_annotation_features(
    dataset: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
):
    """分页返回特征注释列表（代谢物名、HMDB/KEGG 链接）。"""
    ds = _validate(dataset)
    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        try:
            data = bmr.get_or_build_annotation()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"注释构建失败: {e}")
        features = data.get("features") or []
    else:
        ann_path = dr.dataset_pipeline_dir(ds) / "annotated_feature_meta.json"
        if not ann_path.is_file():
            raise HTTPException(status_code=404, detail="annotated_feature_meta.json 不存在。")
        import json
        ann = json.loads(ann_path.read_text(encoding="utf-8"))
        features = ann.get("features") or []

    if search:
        kw = search.strip().lower()
        features = [
            f for f in features
            if kw in (f.get("metabolite_name") or f.get("feature") or f.get("feature_col") or "").lower()
            or kw in (f.get("formula") or "").lower()
            or any(kw in k.lower() for k in (f.get("kegg_ids") or []))
            or any(kw in h.lower() for h in (f.get("hmdb_ids") or []))
        ]

    total = len(features)
    return {"total": total, "offset": offset, "limit": limit, "features": features[offset: offset + limit]}


# ──────────────────────────────────────────────────────────────────────────────
# 通路富集分析（KEGG Pathway Enrichment）
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/{dataset}/pathway-enrichment")
def get_pathway_enrichment(
    dataset: str,
    group1: str = Query(..., description="对照组 group_label"),
    group2: str = Query(..., description="实验组 group_label"),
    fc_threshold: float = Query(1.0, ge=0.0, le=20.0),
    pvalue_threshold: float = Query(0.05, gt=0.0, le=1.0),
    use_fdr: bool = Query(True),
    top_n: int = Query(20, ge=5, le=50),
):
    """执行 KEGG 通路富集分析（支持 benchmark / bioheart / mi）。"""
    ds = _validate(dataset)
    g1 = group1.strip()
    g2 = group2.strip()
    if not g1 or not g2:
        raise HTTPException(status_code=400, detail="group1 和 group2 不能为空。")
    if g1 == g2:
        raise HTTPException(status_code=400, detail="group1 与 group2 不能相同。")

    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        from app.services.pathway_enrichment_service import get_or_run_pathway_enrichment
        try:
            result = get_or_run_pathway_enrichment(
                pipeline_dir=bmr.pipeline_dir(),
                benchmark_merged_dir=bmr.merged_root(),
                group1=g1, group2=g2,
                fc_threshold=fc_threshold,
                pvalue_threshold=pvalue_threshold,
                use_fdr=use_fdr, top_n=top_n,
            )
        except (FileNotFoundError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"通路富集失败: {e}")
        return result

    # 非 benchmark：使用 dataset 专用的注释文件做富集
    from app.services.pathway_enrichment_service import get_or_run_pathway_enrichment_for_dataset
    try:
        result = get_or_run_pathway_enrichment_for_dataset(
            pipeline_dir=dr.dataset_pipeline_dir(ds),
            dataset_dir=dr.dataset_root(ds),
            group1=g1, group2=g2,
            fc_threshold=fc_threshold,
            pvalue_threshold=pvalue_threshold,
            use_fdr=use_fdr, top_n=top_n,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"通路富集失败: {e}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# MetaKG 知识图谱子图
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/{dataset}/metakg-subgraph")
def get_metakg_subgraph(
    dataset: str,
    node_types: Optional[str] = Query(None, description="逗号分隔节点类型，如 Compound,Pathway"),
    relation_types: Optional[str] = Query(None, description="逗号分隔关系类型"),
    seed_only: bool = Query(False),
):
    """返回 MetaKG 子图（节点+边），供前端 ECharts force-graph 可视化。"""
    ds = _validate(dataset)

    if ds == "benchmark":
        from app.services import benchmark_merged_read as bmr
        sg_path = bmr.pipeline_dir() / "metakg_subgraph.json"
    else:
        sg_path = dr.dataset_pipeline_dir(ds) / "metakg_subgraph.json"

    if not sg_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"metakg_subgraph.json 不存在（{ds}），请先运行 build_metakg_subgraph_dataset.py。"
        )

    import json
    try:
        data = json.loads(sg_path.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="metakg_subgraph.json 读取失败。")

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    original_seed_ids = {n["id"] for n in nodes if n.get("is_seed")}

    if node_types:
        allowed_types = {t.strip() for t in node_types.split(",") if t.strip()}
        nodes = [n for n in nodes if n.get("type") in allowed_types]
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["head"] in node_ids and e["tail"] in node_ids]

    if relation_types:
        allowed_rels = {r.strip() for r in relation_types.split(",") if r.strip()}
        edges = [e for e in edges if e.get("relation") in allowed_rels]
        edge_node_ids = {e["head"] for e in edges} | {e["tail"] for e in edges}
        keep_ids = edge_node_ids | original_seed_ids
        nodes = [n for n in nodes if n["id"] in keep_ids]

    if seed_only:
        seed_ids = original_seed_ids
        edges = [e for e in edges if e["head"] in seed_ids or e["tail"] in seed_ids]
        neighbor_ids = {e["head"] for e in edges} | {e["tail"] for e in edges} | seed_ids
        nodes = [n for n in nodes if n["id"] in neighbor_ids]

    return {
        "meta": data.get("meta", {}),
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
