from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import LabelEncoder

from app.algorithms.batch_correction.baseline_location_scale_sample import (
    per_feature_batch_location_scale_baseline,
)


METHOD_ID = "per_feature_batch_location_scale_baseline"
METHOD_DISPLAY_NAME_EN = "Per-Feature Batch Location–Scale Alignment to Global (Baseline)"
METHOD_DISPLAY_NAME_ZH = "逐特征-逐批次位置尺度对齐到全局分布（基线批次校正）"


def _align_meta(matrix: pd.DataFrame, sample_meta: pd.DataFrame) -> pd.DataFrame:
    if "merged_sample_id" in sample_meta.columns:
        return sample_meta.set_index("merged_sample_id").loc[matrix.index.astype(str)]
    if "sample_col_name" in sample_meta.columns:
        return sample_meta.set_index("sample_col_name").loc[matrix.index]
    raise ValueError("sample_meta 缺少 merged_sample_id 或 sample_col_name")


def _pca_fit_transform(X: np.ndarray, n_components: int) -> Tuple[np.ndarray, PCA]:
    pca = PCA(n_components=n_components)
    coords = pca.fit_transform(X)
    return coords, pca


def _silhouette_2d_safe(coords: np.ndarray, labels: np.ndarray) -> Optional[float]:
    """Silhouette on PC1–PC2; filter labels with count>=2; need >=2 clusters and >=3 samples."""
    if coords.shape[0] < 3 or coords.shape[1] < 2:
        return None
    labs = np.asarray(labels).astype(str)
    from collections import Counter

    cnt = Counter(labs.tolist())
    keep = np.array([cnt[x] >= 2 for x in labs])
    if keep.sum() < 3:
        return None
    coords_f = coords[keep, :2]
    labs_f = labs[keep]
    uniq = np.unique(labs_f)
    if uniq.size < 2:
        return None
    le = LabelEncoder()
    y = le.fit_transform(labs_f)
    try:
        return float(silhouette_score(coords_f, y, metric="euclidean"))
    except Exception:
        return None


def _batch_centroid_separation(coords: np.ndarray, batch_labels: np.ndarray) -> float:
    """Mean pairwise Euclidean distance between batch centroids in PC1–PC2 (higher = stronger batch separation)."""
    labs = np.asarray(batch_labels).astype(str)
    B = np.unique(labs)
    if B.size < 2:
        return 0.0
    cents = []
    for b in B:
        m = labs == b
        cslice = coords[m, :2] if coords.shape[1] > 1 else np.column_stack([coords[m, 0], np.zeros(m.sum())])
        cents.append(np.nanmean(cslice, axis=0))
    dists: List[float] = []
    for i in range(len(cents)):
        for j in range(i + 1, len(cents)):
            dists.append(float(np.linalg.norm(cents[i] - cents[j])))
    return float(np.mean(dists)) if dists else 0.0


def _plot_four_panel(
    coords_bef: np.ndarray,
    coords_aft: np.ndarray,
    meta: pd.DataFrame,
    out_path: Path,
) -> None:
    batch = meta["batch_id"].astype(str).values
    grp = meta["group_label"].astype(str).values

    def _xy(coords: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        x = coords[:, 0]
        y = coords[:, 1] if coords.shape[1] > 1 else np.zeros_like(x)
        return x, y

    def _draw(ax, coords, labels, title: str, max_legend: int = 12) -> None:
        uniq = list(dict.fromkeys(labels.tolist()))
        cmap = plt.cm.get_cmap("tab20", max(len(uniq), 1))
        shown = uniq[:max_legend]
        x, y = _xy(coords)
        for i, g in enumerate(shown):
            mask = labels == g
            ax.scatter(x[mask], y[mask], s=10, alpha=0.75, label=str(g)[:32], color=cmap(i))
        if len(uniq) > max_legend:
            ax.scatter([], [], c="0.5", label=f"... (+{len(uniq)-max_legend})")
        ax.set_title(title)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2" if coords.shape[1] > 1 else "0")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=120)
    _draw(axes[0, 0], coords_bef, batch, "Before baseline — colored by batch_id")
    _draw(axes[0, 1], coords_bef, grp, "Before baseline — colored by group_label", max_legend=10)
    _draw(axes[1, 0], coords_aft, batch, "After baseline — colored by batch_id")
    _draw(axes[1, 1], coords_aft, grp, "After baseline — colored by group_label", max_legend=10)
    for ax in axes.ravel():
        ax.legend(loc="best", fontsize=6, ncol=1)
    fig.suptitle(
        "PCA before vs after baseline batch correction\n"
        f"({METHOD_ID}; not strict ComBat — see batch_correction_method_report.json)",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def run_baseline_batch_correction_merged_pipeline(
    *,
    benchmark_merged_dir: Path,
    pipeline_dir: Path,
    n_pca_components: int = 2,
    input_matrix_filename: str = "imputed_sample_by_feature.csv",
) -> Dict[str, Any]:
    """
    读取 merged 流程产物，在 **imputed** 矩阵上执行 baseline 批次校正（推荐）。
    若需从原始 merged 强度矩阵运行，可将 input_matrix_filename 设为 merged_sample_by_feature.csv
    （需自行保证与 sample_meta 行对齐）。
    """
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    matrix_path = pipeline_dir / input_matrix_filename
    if not matrix_path.is_file():
        raise FileNotFoundError(f"缺少输入矩阵: {matrix_path}")

    X_df = pd.read_csv(matrix_path, index_col=0)
    X_df.index = X_df.index.astype(str)
    X = X_df.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)

    sample_meta = pd.read_csv(benchmark_merged_dir / "merged_sample_meta.csv")
    meta = _align_meta(X_df, sample_meta)
    batch_ids = meta["batch_id"].astype(str).values

    unique_batches = np.unique(batch_ids)
    if unique_batches.size < 2:
        raise ValueError("baseline 批次校正需要至少 2 个 batch_id。")

    X_corr = per_feature_batch_location_scale_baseline(X, batch_ids, eps=1e-8)
    corrected_df = pd.DataFrame(X_corr, index=X_df.index, columns=X_df.columns)
    corrected_path = pipeline_dir / "batch_corrected_sample_by_feature.csv"
    corrected_df.to_csv(corrected_path, index=True)

    n_comp = min(int(n_pca_components), X.shape[0] - 1, X.shape[1])
    n_comp = max(n_comp, 1)

    coords_bef, pca_bef = _pca_fit_transform(np.nan_to_num(X, nan=0.0), n_comp)
    coords_aft, pca_aft = _pca_fit_transform(np.nan_to_num(X_corr, nan=0.0), n_comp)

    pca_after_payload = {
        "method": METHOD_ID,
        "n_components": int(n_comp),
        "explained_variance_ratio": pca_aft.explained_variance_ratio_.tolist(),
        "coords": coords_aft.tolist(),
        "sample_index": corrected_df.index.tolist(),
    }
    with (pipeline_dir / "pca_after_correction.json").open("w", encoding="utf-8") as f:
        json.dump(pca_after_payload, f, ensure_ascii=False, indent=2)

    _plot_four_panel(coords_bef, coords_aft, meta, pipeline_dir / "pca_before_vs_after_batch_correction.png")

    sil_batch_bef = _silhouette_2d_safe(coords_bef, batch_ids)
    sil_batch_aft = _silhouette_2d_safe(coords_aft, batch_ids)
    grp = meta["group_label"].astype(str).values
    sil_grp_bef = _silhouette_2d_safe(coords_bef, grp)
    sil_grp_aft = _silhouette_2d_safe(coords_aft, grp)

    sep_bef = _batch_centroid_separation(coords_bef, batch_ids)
    sep_aft = _batch_centroid_separation(coords_aft, batch_ids)

    delta_batch_sil = (
        (sil_batch_aft - sil_batch_bef) if (sil_batch_bef is not None and sil_batch_aft is not None) else None
    )
    delta_grp_sil = (
        (sil_grp_aft - sil_grp_bef) if (sil_grp_bef is not None and sil_grp_aft is not None) else None
    )

    # 质心距离：校正后各 batch 在 PC1–PC2 的中心应更接近（越小越“混合”）
    mixing_improved_by_centroid = None
    if sep_bef > 1e-6:
        mixing_improved_by_centroid = bool(sep_aft < sep_bef * 0.15)

    # silhouette 会在“校正前后各自单独做 PCA”时受子空间旋转影响，可能与质心距离不完全同向
    mixing_improved_by_silhouette = None
    if delta_batch_sil is not None:
        mixing_improved_by_silhouette = bool(delta_batch_sil < 0)

    mixing_improved = mixing_improved_by_centroid
    mixing_notes: List[str] = []
    if (
        mixing_improved_by_centroid is True
        and mixing_improved_by_silhouette is False
        and delta_batch_sil is not None
    ):
        mixing_notes.append(
            "batch_id 的 silhouette 在‘校正前后各自 PCA’下可能上升，但 batch 质心距离已显著下降；"
            "建议以质心距离 + 可视化为主判据。"
        )

    group_overdistorted = None
    if delta_grp_sil is not None:
        # 生物分组可分离性若大幅下降，视为可能过度校正信号（启发式阈值）
        group_overdistorted = bool(delta_grp_sil < -0.05)

    metrics: Dict[str, Any] = {
        "baseline_method_id": METHOD_ID,
        "strict_combat": {"status": "not_implemented", "note": "严格 ComBat（empirical Bayes + 设计矩阵等）尚未实现。"},
        "pca_components": int(n_comp),
        "explained_variance_ratio_before_pc": pca_bef.explained_variance_ratio_.tolist(),
        "explained_variance_ratio_after_pc": pca_aft.explained_variance_ratio_.tolist(),
        "silhouette_batch_id_pc12_before": sil_batch_bef,
        "silhouette_batch_id_pc12_after": sil_batch_aft,
        "delta_silhouette_batch_id": delta_batch_sil,
        "interpretation_batch_silhouette": (
            "在 PC1–PC2 上，batch_id 的 silhouette 越低通常表示 batch 间重叠越多（混合越好）。"
            "若校正后该值下降，通常表示 batch 分离减弱。"
        ),
        "silhouette_group_label_pc12_before": sil_grp_bef,
        "silhouette_group_label_pc12_after": sil_grp_aft,
        "delta_silhouette_group_label": delta_grp_sil,
        "interpretation_group_silhouette": (
            "group_label 的 silhouette 大幅下降可能意味着生物学结构被削弱；轻微变化较常见。"
        ),
        "batch_centroid_separation_pc12_before": sep_bef,
        "batch_centroid_separation_pc12_after": sep_aft,
        "delta_batch_centroid_separation": sep_aft - sep_bef,
        "heuristic_mixing_improved_by_centroid": mixing_improved_by_centroid,
        "heuristic_mixing_improved_by_silhouette": mixing_improved_by_silhouette,
        "heuristic_mixing_improved": mixing_improved,
        "heuristic_mixing_notes": mixing_notes,
        "heuristic_group_overdistorted": group_overdistorted,
        "baseline_suitability_summary": (
            "本基线适合作为可复现的 **非 ComBat** 对照：实现简单、假设清晰。"
            "若 batch 效应近似为逐特征位置/尺度差异，可能有效；若生物学与批次混杂，可能过校正。"
        ),
    }
    with (pipeline_dir / "batch_correction_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    method_report: Dict[str, Any] = {
        "inputs": {
            "benchmark_merged_dir": str(benchmark_merged_dir),
            "merged_sample_meta_csv": str(benchmark_merged_dir / "merged_sample_meta.csv"),
            "merged_feature_meta_csv": str(benchmark_merged_dir / "merged_feature_meta.csv"),
            "pipeline_matrix_csv": str(matrix_path),
        },
        "strict_combat": {
            "status": "not_implemented",
            "missing_for_strict_combat": [
                "empirical Bayes shrinkage（ComBat 核心）",
                "显式生物学设计矩阵 / 协变量（如疾病、性别等）建模",
                "与 sva::ComBat 或 neuroCombat 等参考实现一致的参数与数值对齐验证",
                "可选：对已知 QC / 非生物学样本的显式处理策略",
            ],
        },
        "baseline_batch_correction": {
            "status": "implemented",
            "method_id": METHOD_ID,
            "method_display_name_en": METHOD_DISPLAY_NAME_EN,
            "method_display_name_zh": METHOD_DISPLAY_NAME_ZH,
            "what_it_is": (
                "对每个代谢特征（列），在每个 batch 内估计均值与标准差，"
                "将该 batch 内样本映射到“全局均值/全局标准差”尺度上，"
                "从而使各 batch 在该特征上的边缘分布更接近。"
            ),
            "what_it_is_not": [
                "不是 strict ComBat / empirical Bayes ComBat",
                "不是 removeBatchEffect(limma) 的完整等价物",
                "不是基于线性混合模型或深度学习的批次校正",
            ],
            "assumptions": [
                "batch 效应主要体现为逐特征的 location / scale 差异",
                "各 batch 内样本量足以稳定估计 batch 内方差（本数据每 batch 245）",
            ],
            "limitations": [
                "忽略生物学协变量：若分组与批次相关，可能削弱真实生物学信号",
                "独立逐特征处理，不考虑特征间相关结构",
                "对非高斯、重尾或强非线性 batch 效应可能不足",
            ],
            "implementation": {
                "module": "app.algorithms.batch_correction.baseline_location_scale_sample",
                "function": "per_feature_batch_location_scale_baseline",
                "input_matrix_file": str(matrix_path.name),
                "eps_std_floor": 1e-8,
            },
        },
        "outputs": {
            "batch_corrected_sample_by_feature_csv": str(corrected_path),
            "batch_correction_metrics_json": str(pipeline_dir / "batch_correction_metrics.json"),
            "pca_before_vs_after_png": str(pipeline_dir / "pca_before_vs_after_batch_correction.png"),
            "pca_after_correction_json": str(pipeline_dir / "pca_after_correction.json"),
        },
    }
    with (pipeline_dir / "batch_correction_method_report.json").open("w", encoding="utf-8") as f:
        json.dump(method_report, f, ensure_ascii=False, indent=2)

    return {
        "batch_corrected_matrix_path": str(corrected_path),
        "batch_correction_method_report_path": str(pipeline_dir / "batch_correction_method_report.json"),
        "batch_correction_metrics_path": str(pipeline_dir / "batch_correction_metrics.json"),
        "pca_before_vs_after_path": str(pipeline_dir / "pca_before_vs_after_batch_correction.png"),
        "pca_after_correction_path": str(pipeline_dir / "pca_after_correction.json"),
        "metrics": metrics,
    }
