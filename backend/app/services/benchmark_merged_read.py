from __future__ import annotations

import json
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
