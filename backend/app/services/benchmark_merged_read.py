from __future__ import annotations

import json
import re
import csv
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import Settings


def merged_root() -> Path:
    return Settings.PROCESSED_DIR / "benchmark_merged"


def pipeline_dir() -> Path:
    return merged_root() / "_pipeline"


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_merge_report() -> Optional[Dict[str, Any]]:
    return read_json(merged_root() / "merge_report.json")


def load_batch_correction_method_report() -> Optional[Dict[str, Any]]:
    return read_json(pipeline_dir() / "batch_correction_method_report.json")


def load_batch_correction_metrics() -> Optional[Dict[str, Any]]:
    return read_json(pipeline_dir() / "batch_correction_metrics.json")


# 下载文件用途说明（按文件名索引；不向页面注入指标数值，仅说明文件角色）
FILE_PURPOSE_ZH: Dict[str, str] = {
    "merge_report.json": "跨 Batch 合并摘要：样本/特征数、merge_strategy、缺失率、各 batch 计数等（来源：merge_report.json）。",
    "batch_corrected_sample_by_feature.csv": "baseline 批次校正后的样本×特征数值矩阵，供复现或下游统计（来源：_pipeline/）。",
    "batch_correction_method_report.json": "方法声明与实现细节：baseline 与 strict_combat 区分、假设与局限（来源：_pipeline/）。",
    "batch_correction_metrics.json": "校正前后 PCA 相关指标、质心距离、silhouette、启发式结论（来源：_pipeline/）。",
    "pca_after_correction.json": "校正后 PCA 坐标与解释方差比（来源：_pipeline/）。",
    "pca_before_vs_after_batch_correction.png": "校正前/后 PCA 四宫格图（batch_id 与 group_label 着色）（来源：_pipeline/）。",
}


def system_capabilities_bullets() -> List[str]:
    """页面顶部能力说明（产品能力概括，不替代报告中的数值）。"""
    return [
        "支持多 sheet 原始 Excel（injections / intensities / ions / annotation）导入与解析。",
        "支持跨 batch 合并（ionIdx 对齐），生成 benchmark_merged 标准中间文件。",
        "支持可复现的 baseline 批次校正（per_feature_batch_location_scale_baseline），并产出报告与矩阵。",
        "strict ComBat（empirical Bayes 等）尚未在本项目中实现；请勿与 baseline 混称。",
    ]


def build_key_metric_cards(metrics: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """关键指标对比卡片数据，字段值全部来自 batch_correction_metrics.json。"""
    if not metrics:
        return []
    return [
        {
            "kind": "compare",
            "id": "centroid",
            "title": "batch_centroid_separation_pc12",
            "before": metrics.get("batch_centroid_separation_pc12_before"),
            "after": metrics.get("batch_centroid_separation_pc12_after"),
            "delta": metrics.get("delta_batch_centroid_separation"),
        },
        {
            "kind": "compare",
            "id": "sil_batch",
            "title": "silhouette(batch_id)",
            "before": metrics.get("silhouette_batch_id_pc12_before"),
            "after": metrics.get("silhouette_batch_id_pc12_after"),
            "delta": metrics.get("delta_silhouette_batch_id"),
        },
        {
            "kind": "compare",
            "id": "sil_group",
            "title": "silhouette(group_label)",
            "before": metrics.get("silhouette_group_label_pc12_before"),
            "after": metrics.get("silhouette_group_label_pc12_after"),
            "delta": metrics.get("delta_silhouette_group_label"),
        },
        {
            "kind": "scalar",
            "id": "mix_centroid",
            "title": "heuristic_mixing_improved_by_centroid",
            "value": metrics.get("heuristic_mixing_improved_by_centroid"),
        },
        {
            "kind": "scalar",
            "id": "group_distort",
            "title": "heuristic_group_overdistorted",
            "value": metrics.get("heuristic_group_overdistorted"),
        },
    ]


def build_interpretation_from_reports(
    metrics: Optional[Dict[str, Any]],
    report: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    根据 batch_correction_metrics.json 与 batch_correction_method_report.json 自动生成结果解释文案。
    句子中引用的数值与布尔值均来自上述 JSON，不手填指标。
    """
    out: Dict[str, Any] = {
        "available": bool(metrics),
        "mixing_paragraph": "",
        "group_paragraph": "",
        "method_paragraph": "",
        "notes_from_metrics": [],
    }
    if not metrics:
        return out

    out["notes_from_metrics"] = list(metrics.get("heuristic_mixing_notes") or [])

    sep_b = metrics.get("batch_centroid_separation_pc12_before")
    sep_a = metrics.get("batch_centroid_separation_pc12_after")
    dsep = metrics.get("delta_batch_centroid_separation")
    hmi_c = metrics.get("heuristic_mixing_improved_by_centroid")
    hmi_s = metrics.get("heuristic_mixing_improved_by_silhouette")

    mix_parts: List[str] = [
        f"依据 metrics 中 batch_centroid_separation_pc12：校正前为 {sep_b!r}，校正后为 {sep_a!r}，"
        f"delta_batch_centroid_separation={dsep!r}。"
    ]
    if hmi_c is True:
        mix_parts.append("heuristic_mixing_improved_by_centroid 为 true：以 batch 质心距离为判据时，倾向于认为 batch 混合（重叠）改善。")
    elif hmi_c is False:
        mix_parts.append("heuristic_mixing_improved_by_centroid 为 false：以质心距离为判据时未标记为改善（若与 silhouette 不一致，见 metrics 内 heuristic_mixing_notes）。")
    else:
        mix_parts.append("heuristic_mixing_improved_by_centroid 缺失。")
    if hmi_s is not None:
        mix_parts.append(f"heuristic_mixing_improved_by_silhouette 为 {hmi_s!r}（校正前后各自 PCA，子空间可能旋转，仅作辅助）。")
    out["mixing_paragraph"] = " ".join(mix_parts)

    sg_b = metrics.get("silhouette_group_label_pc12_before")
    sg_a = metrics.get("silhouette_group_label_pc12_after")
    dsg = metrics.get("delta_silhouette_group_label")
    hgo = metrics.get("heuristic_group_overdistorted")

    grp_parts: List[str] = [
        f"依据 metrics 中 silhouette(group_label)（PC1–PC2）：校正前 {sg_b!r}，校正后 {sg_a!r}，"
        f"delta_silhouette_group_label={dsg!r}。"
    ]
    if hgo is True:
        grp_parts.append("heuristic_group_overdistorted 为 true：启发式认为分组可分离性可能明显下降，需结合生物学设计谨慎解读。")
    elif hgo is False:
        grp_parts.append("heuristic_group_overdistorted 为 false：未触发“分组结构明显受损”的启发式阈值。")
    else:
        grp_parts.append("heuristic_group_overdistorted 缺失。")
    out["group_paragraph"] = " ".join(grp_parts)

    if report:
        bc = report.get("baseline_batch_correction") or {}
        mid = bc.get("method_id")
        sc = (report.get("strict_combat") or {}).get("status")
        out["method_paragraph"] = (
            f"batch_correction_method_report.json 记载：baseline 方法 method_id={mid!r}；"
            f"strict_combat.status={sc!r}。"
            " 因此当前页面展示的是 **baseline** 可复现校正，**不是** strict ComBat。"
        )
    else:
        out["method_paragraph"] = "未找到 batch_correction_method_report.json，无法从报告引用 method_id 与 strict_combat 状态。"

    return out


def build_summary_payload() -> Dict[str, Any]:
    """
    合并 merge_report 与展示页需要的派生字段（数值均来自文件，不手填）。
    """
    mr = load_merge_report() or {}
    out: Dict[str, Any] = {
        "available": bool(mr),
        "merged_sample_count": mr.get("merged_sample_count"),
        "merged_feature_count": mr.get("merged_feature_count"),
        "merge_strategy": mr.get("merge_strategy"),
        "missing_ratio_after_merge": mr.get("missing_ratio_after_merge"),
        "batch_count": len(mr.get("batch_id_unique_values") or []),
        "batch_id_unique_values": mr.get("batch_id_unique_values"),
        "raw_merge_report": mr,
    }
    return out


DOWNLOAD_ALLOWLIST = frozenset(
    {
        "batch_corrected_sample_by_feature.csv",
        "batch_correction_method_report.json",
        "batch_correction_metrics.json",
        "pca_after_correction.json",
        "merge_report.json",
        "pca_before_vs_after_batch_correction.png",
    }
)


def list_downloadable_files() -> List[Dict[str, Any]]:
    pdir = pipeline_dir()
    mroot = merged_root()
    items: List[Dict[str, Any]] = []
    for name in sorted(DOWNLOAD_ALLOWLIST):
        if name == "merge_report.json":
            path = mroot / name
        elif name == "pca_before_vs_after_batch_correction.png":
            path = pdir / name
        else:
            path = pdir / name
        if path.is_file():
            items.append(
                {
                    "name": name,
                    "size_bytes": path.stat().st_size,
                    "download_path": name,
                    "purpose": FILE_PURPOSE_ZH.get(name, "见文件名与项目文档。"),
                }
            )
    return items


def safe_resolve_download(name: str) -> Optional[Path]:
    if name not in DOWNLOAD_ALLOWLIST:
        return None
    if name == "merge_report.json":
        path = merged_root() / name
    else:
        path = pipeline_dir() / name
    try:
        rp = path.resolve()
    except OSError:
        return None
    if not rp.is_file():
        return None
    allowed_parents = {merged_root().resolve(), pipeline_dir().resolve()}
    if rp.parent.resolve() not in allowed_parents:
        return None
    return path


def pca_plot_path() -> Optional[Path]:
    p = pipeline_dir() / "pca_before_vs_after_batch_correction.png"
    return p if p.is_file() else None


def load_pca_after_correction() -> Optional[Dict[str, Any]]:
    """加载校正后的 PCA 数据（坐标与解释方差比）。"""
    return read_json(pipeline_dir() / "pca_after_correction.json")


# ==============================
# evaluation（方法对比实验）只读
# ==============================


def evaluation_dir() -> Path:
    return pipeline_dir() / "evaluation"


def load_evaluation_report() -> Optional[Dict[str, Any]]:
    return read_json(evaluation_dir() / "evaluation_report.json")


def load_evaluation_table_rows() -> Optional[List[Dict[str, Any]]]:
    """
    读取 evaluation_table.csv 为行列表（字段均为字符串/可空）。
    注意：这是“展示用只读接口”，不在后端做复杂类型推断。
    """
    p = evaluation_dir() / "evaluation_table.csv"
    if not p.is_file():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [dict(r) for r in reader]
    except Exception:
        return None


def evaluation_pca_image_path() -> Optional[Path]:
    p = evaluation_dir() / "pca_before_vs_after.png"
    return p if p.is_file() else None


_METHOD_SAFE_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


# evaluation 下载清单（不影响 baseline DOWNLOAD_ALLOWLIST）
EVALUATION_DOWNLOAD_ALLOWLIST = frozenset(
    {
        "evaluation_report.json",
        "evaluation_table.csv",
        "pca_before_vs_after.png",
        "pca_mean.json",
        "pca_median.json",
        "pca_knn.json",
        "pca_baseline.json",
        "pca_combat.json",
    }
)

EVALUATION_FILE_PURPOSE_ZH: Dict[str, str] = {
    "evaluation_report.json": "方法对比实验总报告：包含各方法指标与 display_name（combat-like 为简化对齐方法，并非 strict ComBat）。",
    "evaluation_table.csv": "方法对比表（每种方法一行）：silhouette 与 batch centroid distance 等。",
    "pca_before_vs_after.png": "方法对比实验：before/after PCA 四宫格对比图。",
    "pca_mean.json": "mean 填充后的 PCA 坐标与解释方差比（展示用）。",
    "pca_median.json": "median 填充后的 PCA 坐标与解释方差比（展示用）。",
    "pca_knn.json": "knn 填充后的 PCA 坐标与解释方差比（展示用）。",
    "pca_baseline.json": "baseline 校正后的 PCA 坐标与解释方差比（展示用）。",
    "pca_combat.json": "ComBat（neuroCombat 经验 Bayes）PCA 坐标与解释方差比（Johnson et al., 2007）。",
}


def list_evaluation_downloadable_files() -> List[Dict[str, Any]]:
    edir = evaluation_dir()
    items: List[Dict[str, Any]] = []
    for name in sorted(EVALUATION_DOWNLOAD_ALLOWLIST):
        path = edir / name
        if path.is_file():
            items.append(
                {
                    "name": name,
                    "size_bytes": path.stat().st_size,
                    "download_path": name,
                    "purpose": EVALUATION_FILE_PURPOSE_ZH.get(name, "evaluation 产物文件。"),
                }
            )
    return items


def safe_resolve_evaluation_download(name: str) -> Optional[Path]:
    if name not in EVALUATION_DOWNLOAD_ALLOWLIST:
        return None
    path = evaluation_dir() / name
    try:
        rp = path.resolve()
    except OSError:
        return None
    if not rp.is_file():
        return None
    allowed_parent = evaluation_dir().resolve()
    if rp.parent.resolve() != allowed_parent:
        return None
    return path


def _normalize_eval_method(method: str, report: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    兼容前端传入 display_name，例如 combat-like → combat（内部文件名）。
    同时做最小安全过滤，避免路径穿越。
    """
    m = (method or "").strip()
    if m == "combat-like":
        m = "combat"
    if not m or not _METHOD_SAFE_RE.match(m):
        return None
    if report:
        methods = set((report.get("methods_order") or []) + list((report.get("methods") or {}).keys()))
        if methods and m not in methods:
            return None
    return m


def load_evaluation_method_pca(method: str) -> Optional[Dict[str, Any]]:
    rep = load_evaluation_report()
    m = _normalize_eval_method(method, rep)
    if m is None:
        return None
    return read_json(evaluation_dir() / f"pca_{m}.json")


def build_evaluation_summary_payload() -> Optional[Dict[str, Any]]:
    rep = load_evaluation_report()
    if not rep:
        return None
    return {
        "available": True,
        "schema_version": rep.get("schema_version"),
        "methods_order": rep.get("methods_order") or [],
        "methods_display_order": rep.get("methods_display_order") or [],
        "methods_display_names": (rep.get("inputs") or {}).get("methods_display_names") or {},
        "before_method_for_plot": (rep.get("inputs") or {}).get("before_method_for_plot"),
        "after_method_for_plot": (rep.get("inputs") or {}).get("after_method_for_plot"),
        "before_method_for_plot_display": (rep.get("inputs") or {}).get("before_method_for_plot_display"),
        "after_method_for_plot_display": (rep.get("inputs") or {}).get("after_method_for_plot_display"),
        "note": "方法对比实验为展示用评估产物；combat 为 neuroCombat 经验 Bayes 实现（Johnson et al., 2007）。",
    }


# ==============================
# imputation 评估（Mask-then-Impute）只读
# ==============================

def imputation_eval_dir() -> Path:
    return pipeline_dir() / "imputation_eval"


def load_imputation_eval_report() -> Optional[Dict[str, Any]]:
    return read_json(imputation_eval_dir() / "imputation_eval_report.json")


def load_imputation_eval_feature() -> Optional[Dict[str, Any]]:
    return read_json(imputation_eval_dir() / "imputation_eval_feature.json")


def build_imputation_eval_summary_payload() -> Optional[Dict[str, Any]]:
    rep = load_imputation_eval_report()
    if not rep:
        return None
    methods = rep.get("methods") or {}
    ranking = rep.get("ranking_by_rmse") or []
    return {
        "available": True,
        "schema_version": rep.get("schema_version"),
        "config": rep.get("config") or {},
        "elapsed_seconds": rep.get("elapsed_seconds"),
        "best_method": rep.get("best_method"),
        "ranking_by_rmse": ranking,
        "methods": {
            m: {
                "method": v.get("method", m),
                "rmse_mean":  v.get("rmse_mean"),
                "rmse_std":   v.get("rmse_std"),
                "mae_mean":   v.get("mae_mean"),
                "mae_std":    v.get("mae_std"),
                "nrmse_mean": v.get("nrmse_mean"),
                "nrmse_std":  v.get("nrmse_std"),
            }
            for m, v in methods.items()
        },
        "notes": rep.get("notes") or [],
    }


# ==============================
# 差异代谢物分析 只读 / 计算入口
# ==============================

def diff_analysis_dir() -> Path:
    return pipeline_dir() / "diff_analysis"


def load_available_groups() -> List[str]:
    """
    从 merged_sample_meta.csv 中读取 formal 样本（sample_type='formal_or_unknown'）
    的 group_label 列表，按频次降序返回。
    """
    meta_path = merged_root() / "merged_sample_meta.csv"
    if not meta_path.is_file():
        return []
    try:
        meta = pd.read_csv(meta_path)
        # 优先取 formal_or_unknown，如无则取全部
        if "sample_type" in meta.columns:
            formal = meta[meta["sample_type"] == "formal_or_unknown"]
        else:
            formal = meta
        if "group_label" not in formal.columns:
            return []
        counts = formal["group_label"].value_counts()
        return counts.index.astype(str).tolist()
    except Exception:
        return []


def _diff_cache_path(group1: str, group2: str) -> Path:
    """差异分析结果缓存文件路径（以 group 名生成安全文件名）。"""
    safe_g1 = re.sub(r"[^\w\-]", "_", group1)
    safe_g2 = re.sub(r"[^\w\-]", "_", group2)
    return diff_analysis_dir() / f"diff_{safe_g1}_vs_{safe_g2}.json"


def get_or_run_diff_analysis(
    group1: str,
    group2: str,
    fc_threshold: float = 1.0,
    pvalue_threshold: float = 0.05,
    use_fdr: bool = True,
) -> Dict[str, Any]:
    """
    优先从磁盘缓存读取差异分析结果；若缓存不存在，实时运行并写入缓存。
    缓存键 = (group1, group2, fc_threshold, pvalue_threshold, use_fdr)。
    """
    cache_path = _diff_cache_path(group1, group2)

    # 读缓存（验证关键参数是否匹配）
    if cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                cached.get("group1") == group1
                and cached.get("group2") == group2
                and abs(cached.get("fc_threshold", -999) - fc_threshold) < 1e-9
                and abs(cached.get("pvalue_threshold", -999) - pvalue_threshold) < 1e-9
                and cached.get("use_fdr") == use_fdr
            ):
                return cached
        except Exception:
            pass

    # 缓存未命中 → 实时计算
    from app.services.differential_analysis_service import run_differential_analysis_for_benchmark

    result = run_differential_analysis_for_benchmark(
        benchmark_merged_dir=merged_root(),
        pipeline_dir=pipeline_dir(),
        group1=group1,
        group2=group2,
        fc_threshold=fc_threshold,
        pvalue_threshold=pvalue_threshold,
        use_fdr=use_fdr,
    )
    return result


# ==============================
# 特征注释 只读 / 构建入口
# ==============================

def load_annotation_data() -> Optional[Dict[str, Any]]:
    """读取 _pipeline/annotated_feature_meta.json（注释结果缓存）。"""
    p = pipeline_dir() / "annotated_feature_meta.json"
    return read_json(p)


def get_or_build_annotation() -> Dict[str, Any]:
    """
    优先从磁盘读注释缓存；若不存在则实时构建并写入。
    """
    cached = load_annotation_data()
    if cached:
        return cached

    from app.services.annotation_service import build_feature_annotation
    return build_feature_annotation(
        benchmark_merged_dir=merged_root(),
        pipeline_dir=pipeline_dir(),
    )


def get_annotation_lookup() -> Dict[str, Dict[str, Any]]:
    """
    返回 {feature_col → annotation_dict} 查找表，
    供差异分析结果富化代谢物名时使用。
    """
    from app.services.annotation_service import build_annotation_lookup
    return build_annotation_lookup(pipeline_dir())


def build_annotation_summary_payload() -> Optional[Dict[str, Any]]:
    """返回注释汇总（不含 features 列表，减小 payload 体积）。"""
    data = load_annotation_data()
    if not data:
        return None
    return {
        "available": True,
        "schema_version": data.get("schema_version"),
        "n_features": data.get("n_features"),
        "n_annotated": data.get("n_annotated"),
        "n_with_kegg": data.get("n_with_kegg"),
        "n_with_hmdb": data.get("n_with_hmdb"),
        "coverage_pct": data.get("coverage_pct"),
    }
