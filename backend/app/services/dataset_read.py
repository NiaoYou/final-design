"""
dataset_read.py
通用多数据集只读服务。

支持的数据集:
  - benchmark  →  data/processed/benchmark_merged/   （原有数据集，直接复用 benchmark_merged_read）
  - amide      →  data/processed/amide/
  - bioheart   →  data/processed/bioheart/
  - mi         →  data/processed/mi/

对于 benchmark 以外的数据集，本模块参照 benchmark_merged_read 的结构，
从对应目录下的相同格式文件中读取数据，返回相同的数据结构，使路由层可以
无差别地处理所有数据集。
"""
from __future__ import annotations

import json
import logging
import re
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.core.config import Settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 数据集元信息注册表
# ──────────────────────────────────────────────────────────────────────────────

DATASET_META: Dict[str, Dict[str, str]] = {
    "benchmark": {
        "label": "Benchmark 数据集",
        "description": "7批次跨批次合并基准数据集（1715 样本，1180 特征）",
        "dir": "benchmark_merged",   # 相对于 PROCESSED_DIR
    },
    "bioheart": {
        "label": "BioHeart 数据集",
        "description": "心脏生物标志物代谢组学数据集（~1300 样本，56 代谢物，15 批次）",
        "dir": "bioheart",
    },
    "amide": {
        "label": "AMIDE 数据集",
        "description": "代谢组学数据集（~598 样本，6462 代谢特征，3 批次）",
        "dir": "amide",
    },
    "mi": {
        "label": "MI（心肌梗死）数据集",
        "description": "心肌梗死预后代谢组学数据集（~902 样本，15 代谢物，2 批次）",
        "dir": "mi",
    },
}

VALID_DATASETS = frozenset(DATASET_META.keys())

# 安全字符校验
_DATASET_SAFE_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_dataset(dataset: str) -> str:
    """校验数据集名称合法性，返回规范化后的名称。"""
    ds = (dataset or "").strip().lower()
    if not ds or ds not in VALID_DATASETS:
        raise ValueError(f"不支持的数据集: {dataset!r}，可选: {sorted(VALID_DATASETS)}")
    return ds


# ──────────────────────────────────────────────────────────────────────────────
# 目录定位
# ──────────────────────────────────────────────────────────────────────────────

def dataset_root(dataset: str) -> Path:
    """返回数据集的根目录（包含 merge_report.json 等文件）。"""
    ds = validate_dataset(dataset)
    return Settings.PROCESSED_DIR / DATASET_META[ds]["dir"]


def dataset_pipeline_dir(dataset: str) -> Path:
    return dataset_root(dataset) / "_pipeline"


def dataset_evaluation_dir(dataset: str) -> Path:
    return dataset_pipeline_dir(dataset) / "evaluation"


# ──────────────────────────────────────────────────────────────────────────────
# 通用文件读取
# ──────────────────────────────────────────────────────────────────────────────

def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("读取 JSON 失败: %s，原因: %s: %s", path, type(e).__name__, e)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 数据加载函数（与 benchmark_merged_read 接口一致）
# ──────────────────────────────────────────────────────────────────────────────

def load_merge_report(dataset: str) -> Optional[Dict[str, Any]]:
    return read_json(dataset_root(dataset) / "merge_report.json")


def load_batch_correction_method_report(dataset: str) -> Optional[Dict[str, Any]]:
    return read_json(dataset_pipeline_dir(dataset) / "batch_correction_method_report.json")


def load_batch_correction_metrics(dataset: str) -> Optional[Dict[str, Any]]:
    return read_json(dataset_pipeline_dir(dataset) / "batch_correction_metrics.json")


def load_pca_after_correction(dataset: str) -> Optional[Dict[str, Any]]:
    return read_json(dataset_pipeline_dir(dataset) / "pca_after_correction.json")


def pca_plot_path(dataset: str) -> Optional[Path]:
    p = dataset_pipeline_dir(dataset) / "pca_before_vs_after_batch_correction.png"
    return p if p.is_file() else None


# ──────────────────────────────────────────────────────────────────────────────
# 汇总 Payload 构建（与 benchmark_merged_read.build_summary_payload 同接口）
# ──────────────────────────────────────────────────────────────────────────────

def build_summary_payload(dataset: str) -> Dict[str, Any]:
    mr = load_merge_report(dataset) or {}
    meta_info = DATASET_META.get(validate_dataset(dataset), {})
    out: Dict[str, Any] = {
        "dataset": dataset,
        "dataset_label": meta_info.get("label", dataset),
        "dataset_description": meta_info.get("description", ""),
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


def build_key_metric_cards(dataset: str) -> List[Dict[str, Any]]:
    metrics = load_batch_correction_metrics(dataset)
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


def build_interpretation_from_reports(dataset: str) -> Dict[str, Any]:
    metrics = load_batch_correction_metrics(dataset)
    report = load_batch_correction_method_report(dataset)

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

    mix_parts = [
        f"依据 batch_centroid_separation_pc12：校正前 {sep_b!r}，校正后 {sep_a!r}，delta={dsep!r}。"
    ]
    if hmi_c is True:
        mix_parts.append("heuristic_mixing_improved_by_centroid=true：以质心距离为判据，batch 混合改善。")
    elif hmi_c is False:
        mix_parts.append("heuristic_mixing_improved_by_centroid=false：以质心距离为判据未标记改善。")
    if hmi_s is not None:
        mix_parts.append(f"heuristic_mixing_improved_by_silhouette={hmi_s!r}。")
    out["mixing_paragraph"] = " ".join(mix_parts)

    sg_b = metrics.get("silhouette_group_label_pc12_before")
    sg_a = metrics.get("silhouette_group_label_pc12_after")
    dsg = metrics.get("delta_silhouette_group_label")
    hgo = metrics.get("heuristic_group_overdistorted")
    grp_parts = [
        f"silhouette(group_label)：校正前 {sg_b!r}，校正后 {sg_a!r}，delta={dsg!r}。"
    ]
    if hgo is True:
        grp_parts.append("heuristic_group_overdistorted=true：分组可分离性可能下降。")
    elif hgo is False:
        grp_parts.append("heuristic_group_overdistorted=false：分组结构未受明显影响。")
    out["group_paragraph"] = " ".join(grp_parts)

    if report:
        bc = report.get("baseline_batch_correction") or {}
        mid = bc.get("method_id")
        sc = (report.get("strict_combat") or {}).get("status")
        out["method_paragraph"] = (
            f"baseline 方法 method_id={mid!r}；strict_combat.status={sc!r}。"
        )
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 下载文件管理
# ──────────────────────────────────────────────────────────────────────────────

DOWNLOAD_ALLOWLIST = frozenset({
    "batch_corrected_sample_by_feature.csv",
    "batch_correction_method_report.json",
    "batch_correction_metrics.json",
    "pca_after_correction.json",
    "merge_report.json",
    "pca_before_vs_after_batch_correction.png",
})

FILE_PURPOSE_ZH: Dict[str, str] = {
    "merge_report.json": "数据集摘要：样本/特征数、批次等信息。",
    "batch_corrected_sample_by_feature.csv": "baseline 批次校正后的样本×特征数值矩阵。",
    "batch_correction_method_report.json": "方法声明与实现细节（baseline 批次校正）。",
    "batch_correction_metrics.json": "校正前后 PCA 相关指标、质心距离、silhouette。",
    "pca_after_correction.json": "校正后 PCA 坐标与解释方差比。",
    "pca_before_vs_after_batch_correction.png": "校正前/后 PCA 四宫格图。",
}


def list_downloadable_files(dataset: str) -> List[Dict[str, Any]]:
    pdir = dataset_pipeline_dir(dataset)
    mroot = dataset_root(dataset)
    items: List[Dict[str, Any]] = []
    for name in sorted(DOWNLOAD_ALLOWLIST):
        path = mroot / name if name == "merge_report.json" else pdir / name
        if path.is_file():
            items.append({
                "name": name,
                "size_bytes": path.stat().st_size,
                "download_path": name,
                "purpose": FILE_PURPOSE_ZH.get(name, ""),
            })
    return items


def safe_resolve_download(dataset: str, name: str) -> Optional[Path]:
    if name not in DOWNLOAD_ALLOWLIST:
        return None
    mroot = dataset_root(dataset)
    pdir = dataset_pipeline_dir(dataset)
    path = mroot / name if name == "merge_report.json" else pdir / name
    try:
        rp = path.resolve()
    except OSError:
        return None
    if not rp.is_file():
        return None
    allowed_parents = {mroot.resolve(), pdir.resolve()}
    if rp.parent.resolve() not in allowed_parents:
        return None
    return path


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation（方法对比）
# ──────────────────────────────────────────────────────────────────────────────

EVALUATION_DOWNLOAD_ALLOWLIST = frozenset({
    "evaluation_report.json",
    "evaluation_table.csv",
    "pca_before_vs_after.png",
    "pca_mean.json",
    "pca_baseline.json",
})

EVALUATION_FILE_PURPOSE_ZH: Dict[str, str] = {
    "evaluation_report.json": "方法对比实验总报告。",
    "evaluation_table.csv": "方法对比表（每种方法一行）。",
    "pca_before_vs_after.png": "方法对比 PCA 图。",
    "pca_mean.json": "mean 填充后的 PCA 坐标（展示用）。",
    "pca_baseline.json": "baseline 校正后的 PCA 坐标（展示用）。",
}

_METHOD_SAFE_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def load_evaluation_report(dataset: str) -> Optional[Dict[str, Any]]:
    return read_json(dataset_evaluation_dir(dataset) / "evaluation_report.json")


def load_evaluation_table_rows(dataset: str) -> Optional[List[Dict[str, Any]]]:
    p = dataset_evaluation_dir(dataset) / "evaluation_table.csv"
    if not p.is_file():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [dict(r) for r in reader]
    except Exception as e:
        logger.warning("读取 evaluation_table.csv 失败: %s: %s", type(e).__name__, e)
        return None


def evaluation_pca_image_path(dataset: str) -> Optional[Path]:
    p = dataset_evaluation_dir(dataset) / "pca_before_vs_after.png"
    return p if p.is_file() else None


def _normalize_eval_method(dataset: str, method: str) -> Optional[str]:
    m = (method or "").strip()
    if m == "combat-like":
        m = "combat"
    if not m or not _METHOD_SAFE_RE.match(m):
        return None
    report = load_evaluation_report(dataset)
    if report:
        methods = set(
            (report.get("methods_order") or []) +
            list((report.get("methods") or {}).keys())
        )
        if methods and m not in methods:
            return None
    return m


def load_evaluation_method_pca(dataset: str, method: str) -> Optional[Dict[str, Any]]:
    m = _normalize_eval_method(dataset, method)
    if m is None:
        return None
    return read_json(dataset_evaluation_dir(dataset) / f"pca_{m}.json")


def build_evaluation_summary_payload(dataset: str) -> Optional[Dict[str, Any]]:
    rep = load_evaluation_report(dataset)
    if not rep:
        return None
    return {
        "available": True,
        "dataset": dataset,
        "schema_version": rep.get("schema_version"),
        "methods_order": rep.get("methods_order") or [],
        "methods_display_order": rep.get("methods_display_order") or [],
        "methods_display_names": (rep.get("inputs") or {}).get("methods_display_names") or {},
        "before_method_for_plot": (rep.get("inputs") or {}).get("before_method_for_plot"),
        "after_method_for_plot": (rep.get("inputs") or {}).get("after_method_for_plot"),
        "before_method_for_plot_display": (rep.get("inputs") or {}).get("before_method_for_plot_display"),
        "after_method_for_plot_display": (rep.get("inputs") or {}).get("after_method_for_plot_display"),
        "note": f"方法对比实验评估产物（{dataset}）。",
    }


def list_evaluation_downloadable_files(dataset: str) -> List[Dict[str, Any]]:
    edir = dataset_evaluation_dir(dataset)
    items: List[Dict[str, Any]] = []
    for name in sorted(EVALUATION_DOWNLOAD_ALLOWLIST):
        path = edir / name
        if path.is_file():
            items.append({
                "name": name,
                "size_bytes": path.stat().st_size,
                "download_path": name,
                "purpose": EVALUATION_FILE_PURPOSE_ZH.get(name, "evaluation 产物文件。"),
            })
    return items


def safe_resolve_evaluation_download(dataset: str, name: str) -> Optional[Path]:
    if name not in EVALUATION_DOWNLOAD_ALLOWLIST:
        return None
    path = dataset_evaluation_dir(dataset) / name
    try:
        rp = path.resolve()
    except OSError:
        return None
    if not rp.is_file():
        return None
    if rp.parent.resolve() != dataset_evaluation_dir(dataset).resolve():
        return None
    return path


# ──────────────────────────────────────────────────────────────────────────────
# 差异分析 groups（从 merged_sample_meta.csv 读取）
# ──────────────────────────────────────────────────────────────────────────────

def load_available_groups(dataset: str) -> List[str]:
    meta_path = dataset_root(dataset) / "merged_sample_meta.csv"
    if not meta_path.is_file():
        return []
    try:
        meta = pd.read_csv(meta_path)
        if "sample_type" in meta.columns:
            formal = meta[meta["sample_type"] == "formal_or_unknown"]
        else:
            formal = meta
        col = "group_label" if "group_label" in formal.columns else (
            "group" if "group" in formal.columns else None
        )
        if col is None:
            return []
        counts = formal[col].value_counts()
        return counts.index.astype(str).tolist()
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────────────────────
# 数据集列表（供前端选择器使用）
# ──────────────────────────────────────────────────────────────────────────────

def list_available_datasets() -> List[Dict[str, Any]]:
    """返回所有已注册数据集的状态列表。"""
    result = []
    for ds_name, meta in DATASET_META.items():
        root = Settings.PROCESSED_DIR / meta["dir"]
        has_data = (root / "merge_report.json").is_file()
        has_pipeline = (root / "_pipeline" / "batch_correction_metrics.json").is_file()
        result.append({
            "id": ds_name,
            "label": meta["label"],
            "description": meta["description"],
            "available": has_data,
            "pipeline_ready": has_pipeline,
        })
    return result
