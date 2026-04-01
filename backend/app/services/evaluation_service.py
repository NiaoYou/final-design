from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib

matplotlib.use("Agg")  # 无 GUI 环境绘图

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import get_dataset_by_task_id
from app.repositories.result_repository import update_metrics_json, update_result_paths
from app.repositories.task_repository import update_task_status
from app.utils.dataframe_utils import extract_sample_metadata, read_long_dataframe
from app.utils.file_utils import ensure_dir, task_result_dir, task_temp_dir


def _run_pca(matrix: pd.DataFrame, n_components: int) -> Dict[str, Any]:
    """
    matrix: feature x sample
    PCA: 默认要求 samples x features，所以需要转置。
    """

    X = matrix.to_numpy(dtype=float).T  # samples x features
    pca = PCA(n_components=n_components)
    coords = pca.fit_transform(X)
    return {
        "n_components": n_components,
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "coords": coords.tolist(),
    }


def run_evaluation(
    db: Session,
    *,
    task_id: int,
    evaluation_config: Dict[str, Any],
) -> Dict[str, Any]:
    dataset = get_dataset_by_task_id(db, task_id)

    temp_dir = task_temp_dir(task_id)
    imputed_path = temp_dir / f"{task_id}_imputed.csv"
    corrected_path = temp_dir / f"{task_id}_batch_corrected.csv"
    if not imputed_path.exists():
        raise FileNotFoundError("缺少 imputed 矩阵，请先调用 impute。")
    if not corrected_path.exists():
        raise FileNotFoundError("缺少 batch_corrected 矩阵，请先调用 batch-correct。")

    imputed = pd.read_csv(imputed_path, index_col=0)
    corrected = pd.read_csv(corrected_path, index_col=0)

    df_long = read_long_dataframe(str(dataset.stored_path), data_format=dataset.data_format)
    batch_labels, group_labels = extract_sample_metadata(
        df_long,
        sample_column=dataset.sample_column,
        batch_column=dataset.batch_column,
        group_column=dataset.group_column,
        matrix_columns=imputed.columns.tolist(),
    )

    n_components = int(evaluation_config.get("n_components", 2))
    pca_before = _run_pca(imputed, n_components=n_components)
    pca_after = _run_pca(corrected, n_components=n_components)

    # 只用前 2 个维度画散点图（n_components=1 时退化）
    pc1_idx, pc2_idx = 0, 1 if n_components > 1 else 0
    coords_before = np.array(pca_before["coords"])
    coords_after = np.array(pca_after["coords"])

    plot_dir = task_result_dir(task_id)
    ensure_dir(plot_dir)
    plot_path = plot_dir / f"{task_id}_pca.png"

    # 生成一张对比图：左(before)右(after)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=120)
    for ax_i, ax in enumerate(axes):
        coords = coords_before if ax_i == 0 else coords_after
        x = coords[:, pc1_idx]
        y = coords[:, pc2_idx]

        unique_groups = list(dict.fromkeys(group_labels.tolist()))
        for g in unique_groups:
            mask = group_labels == g
            ax.scatter(x[mask], y[mask], s=18, label=str(g), alpha=0.8)
        ax.set_title("PCA Before Batch Correction" if ax_i == 0 else "PCA After Batch Correction")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")

    # 避免图例太拥挤：只取前 10 个
    handles, labels = axes[0].get_legend_handles_labels()
    if len(handles) > 0:
        axes[0].legend(handles[:10], labels[:10], loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(plot_path)
    plt.close(fig)

    update_result_paths(
        db,
        task_id,
        pca_before_plot_path=str(plot_path),
        pca_after_plot_path=str(plot_path),
    )
    update_metrics_json(
        db,
        task_id,
        metrics={
            "pca_before_explained_variance_ratio": pca_before["explained_variance_ratio"],
            "pca_after_explained_variance_ratio": pca_after["explained_variance_ratio"],
        },
    )

    update_task_status(db, task_id, status="evaluation_done")
    return {
        "task_id": task_id,
        "pca_before": pca_before,
        "pca_after": pca_after,
        "pca_plot_path": str(plot_path),
    }


def run_evaluation_matrix(
    *,
    matrix_before: pd.DataFrame,
    matrix_after: Optional[pd.DataFrame],
    sample_meta: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """
    matrix format:
    - matrix_before: sample x feature
    - matrix_after: sample x feature (可选；若为 None，则用 before 代替，但在报告里会标注）
    - sample_meta: 包含 sample_col_name +（用于上色的字段，如 group_label/sample_type/batch_id）
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if matrix_before.shape[0] < 2:
        raise ValueError("evaluation: sample 数至少需要 2。")
    if matrix_before.shape[1] < 2:
        raise ValueError("evaluation: feature 数至少需要 2。")

    if "merged_sample_id" in sample_meta.columns:
        meta_aligned = sample_meta.set_index("merged_sample_id").loc[matrix_before.index.astype(str)]
    elif "sample_col_name" in sample_meta.columns:
        meta_aligned = sample_meta.set_index("sample_col_name").loc[matrix_before.index]
    else:
        raise ValueError("evaluation: sample_meta 缺少 merged_sample_id 或 sample_col_name。")

    color_by = str(config.get("color_by", "group_label"))
    if color_by not in meta_aligned.columns:
        color_by = "group_label" if "group_label" in meta_aligned.columns else meta_aligned.columns[0]

    groups = meta_aligned[color_by].astype(str).values

    n_components_req = int(config.get("n_components", 2))
    n_components = min(n_components_req, matrix_before.shape[0] - 1, matrix_before.shape[1])
    if n_components < 2:
        # PCA 降维到 1 维时也做，但图只能用 PC1
        n_components = 1

    def _run_pca_sample_feature(X: pd.DataFrame, n_comp: int) -> Dict[str, Any]:
        x = X.to_numpy(dtype=float)
        pca = PCA(n_components=n_comp)
        coords = pca.fit_transform(x).tolist()
        return {
            "n_components": n_comp,
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "coords": coords,
        }

    pca_before = _run_pca_sample_feature(matrix_before, n_comp=n_components)

    used_placeholder_after = False
    if matrix_after is None:
        pca_after = pca_before
        used_placeholder_after = True
    else:
        pca_after = _run_pca_sample_feature(matrix_after, n_comp=n_components)

    # 生成 PCA 图（2D：PC1/PC2；若 n_components==1，则 PC2 使用 0）
    coords_before = pca_before["coords"]
    coords_after = pca_after["coords"]
    coords_before = pd.DataFrame(coords_before)
    coords_after = pd.DataFrame(coords_after)

    pc1_before = coords_before[0].to_numpy()
    pc2_before = coords_before[1].to_numpy() if n_components > 1 else np.zeros_like(pc1_before)
    pc1_after = coords_after[0].to_numpy()
    pc2_after = coords_after[1].to_numpy() if n_components > 1 else np.zeros_like(pc1_after)

    unique_groups = list(dict.fromkeys(groups.tolist()))
    # group 太多会导致 legend 爆炸：这里做“前 12 个+others”
    top_groups = unique_groups[:12]
    group_to_bucket = {g: g for g in top_groups}
    bucketed_groups = [g if g in group_to_bucket else "others" for g in groups]
    unique_bucketed = list(dict.fromkeys(bucketed_groups))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=120)
    color_map = matplotlib.colormaps.get_cmap("tab20").resampled(max(len(unique_bucketed), 1))
    for ax_i, ax in enumerate(axes):
        x = pc1_before if ax_i == 0 else pc1_after
        y = pc2_before if ax_i == 0 else pc2_after
        for idx_g, g in enumerate(unique_bucketed):
            mask = np.array(bucketed_groups) == g
            ax.scatter(x[mask], y[mask], s=18, alpha=0.85, label=str(g), color=color_map(idx_g))
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2" if n_components > 1 else "0")
        ax.set_title("PCA Before" if ax_i == 0 else "PCA After")

    axes[0].legend(loc="best", fontsize=8, ncol=1)
    fig.tight_layout()
    plot_path = output_dir / "pca.png"
    fig.savefig(plot_path)
    plt.close(fig)

    pca_before_path = output_dir / "pca_before.json"
    pca_after_path = output_dir / "pca_after.json"
    with pca_before_path.open("w", encoding="utf-8") as f:
        json.dump(pca_before, f, ensure_ascii=False, indent=2)
    with pca_after_path.open("w", encoding="utf-8") as f:
        json.dump(pca_after, f, ensure_ascii=False, indent=2)

    explained_before = pca_before["explained_variance_ratio"]
    explained_after = pca_after["explained_variance_ratio"]
    total_before = float(np.sum(explained_before))
    total_after = float(np.sum(explained_after))

    metrics = {
        "n_components": n_components,
        "explained_variance_ratio_before": explained_before,
        "explained_variance_ratio_after": explained_after,
        "explained_variance_total_before": total_before,
        "explained_variance_total_after": total_after,
        "color_by": color_by,
        "placeholder_after_used": used_placeholder_after,
    }

    metrics_path = output_dir / "pca_metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return {
        "pca_before": pca_before,
        "pca_after": pca_after,
        "pca_plot_path": str(plot_path),
        "pca_before_path": str(pca_before_path),
        "pca_after_path": str(pca_after_path),
        "pca_metrics_path": str(metrics_path),
        **metrics,
    }


def run_cross_batch_pre_correction_evaluation(
    *,
    matrix: pd.DataFrame,
    sample_meta: pd.DataFrame,
    output_dir: Path,
    n_components: int = 2,
) -> Dict[str, Any]:
    """
    跨 batch 场景：在**尚未做严格 ComBat** 的前提下，输出校正前评估：
    - 同一 PCA 坐标下，按 batch_id 与 group_label 分别着色
    - 输出 batch_correction_readiness 摘要（诚实标注：严格 ComBat 未实现）
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if "merged_sample_id" in sample_meta.columns:
        meta = sample_meta.set_index("merged_sample_id").loc[matrix.index.astype(str)]
    elif "sample_col_name" in sample_meta.columns:
        meta = sample_meta.set_index("sample_col_name").loc[matrix.index]
    else:
        raise ValueError("pre_correction evaluation: sample_meta 缺少 merged_sample_id 或 sample_col_name")

    for col in ("batch_id", "group_label"):
        if col not in meta.columns:
            raise ValueError(f"pre_correction evaluation: sample_meta 缺少 {col}")

    X = matrix.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    n_comp = min(int(n_components), matrix.shape[0] - 1, matrix.shape[1])
    if n_comp < 1:
        raise ValueError("pre_correction evaluation: 无法做 PCA（维度不足）。")

    pca = PCA(n_components=n_comp)
    coords = pca.fit_transform(X)
    pca_payload = {
        "n_components": n_comp,
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "coords": coords.tolist(),
    }
    with (output_dir / "pca_pre_correction_coords.json").open("w", encoding="utf-8") as f:
        json.dump(pca_payload, f, ensure_ascii=False, indent=2)

    pc1 = coords[:, 0]
    pc2 = coords[:, 1] if n_comp > 1 else np.zeros_like(pc1)

    def _scatter_category(ax, labels: np.ndarray, title: str) -> None:
        uniq = list(dict.fromkeys(labels.tolist()))
        cmap = matplotlib.colormaps.get_cmap("tab20").resampled(max(len(uniq), 1))
        for i, g in enumerate(uniq[:25]):
            mask = labels == g
            ax.scatter(pc1[mask], pc2[mask], s=14, alpha=0.85, label=str(g)[:40], color=cmap(i))
        if len(uniq) > 25:
            ax.scatter([], [], label=f"... (+{len(uniq)-25} groups)", color="0.5")
        ax.set_title(title)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2" if n_comp > 1 else "0")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=120)
    _scatter_category(axes[0], meta["batch_id"].astype(str).values, "PCA colored by batch_id (pre-correction)")
    _scatter_category(axes[1], meta["group_label"].astype(str).values, "PCA colored by group_label (pre-correction)")
    axes[0].legend(loc="best", fontsize=7)
    axes[1].legend(loc="best", fontsize=7)
    fig.tight_layout()
    pre_plot = output_dir / "pca_pre_correction_batch_vs_group.png"
    fig.savefig(pre_plot)
    plt.close(fig)

    batch_ids = sorted(pd.unique(meta["batch_id"].astype(str)).tolist())
    spp = meta.groupby("batch_id").size().to_dict()
    spp = {str(k): int(v) for k, v in spp.items()}

    readiness = {
        "strict_combat_implemented_in_repo": False,
        "n_batches": len(batch_ids),
        "batch_ids": batch_ids,
        "samples_per_batch": spp,
        "min_samples_per_batch": int(min(spp.values())) if spp else 0,
        "can_run_real_combat_from_data_alone": len(batch_ids) >= 2 and (min(spp.values()) >= 2 if spp else False),
        "notes": [
            "本评估图为校正前（pre-correction）PCA，用于观察 batch 与生物学分组在 PC 空间中的分布。",
            "严格 ComBat 仍未实现：即使 readiness 为真，也需要后续接入算法与实验设计矩阵。",
        ],
    }
    readiness_path = output_dir / "pre_correction_readiness.json"
    with readiness_path.open("w", encoding="utf-8") as f:
        json.dump(readiness, f, ensure_ascii=False, indent=2)

    summary_path = output_dir / "pre_correction_evaluation_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "explained_variance_ratio_pc12": pca.explained_variance_ratio_[:2].tolist()
                if len(pca.explained_variance_ratio_) >= 2
                else pca.explained_variance_ratio_.tolist(),
                "plot_path": str(pre_plot),
                "coords_path": str(output_dir / "pca_pre_correction_coords.json"),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "pca_pre_correction_plot_path": str(pre_plot),
        "pca_pre_correction_coords_path": str(output_dir / "pca_pre_correction_coords.json"),
        "pre_correction_readiness_path": str(readiness_path),
        "pre_correction_evaluation_summary_path": str(summary_path),
        "batch_correction_readiness": readiness,
    }


# ==============================
# 统一评估模块（方法对比）
# ==============================

def _align_sample_meta_for_matrix(matrix: pd.DataFrame, sample_meta: pd.DataFrame) -> pd.DataFrame:
    """
    对齐 sample_meta 到 matrix 的行顺序（matrix: sample x feature）。
    支持 merged_sample_id / sample_col_name 两种主键。
    """
    if "merged_sample_id" in sample_meta.columns:
        return sample_meta.set_index("merged_sample_id").loc[matrix.index.astype(str)]
    if "sample_col_name" in sample_meta.columns:
        return sample_meta.set_index("sample_col_name").loc[matrix.index]
    raise ValueError("evaluation_compare: sample_meta 缺少 merged_sample_id 或 sample_col_name。")


def _pca_2d_payload(matrix: pd.DataFrame, n_components: int = 2) -> Dict[str, Any]:
    """
    PCA 降维到 2D（用于可视化与指标计算）。
    matrix: sample x feature
    """
    if matrix.shape[0] < 2:
        raise ValueError("evaluation_compare: 样本数至少需要 2。")
    if matrix.shape[1] < 2:
        raise ValueError("evaluation_compare: 特征数至少需要 2。")

    X = matrix.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    X = np.nan_to_num(X, nan=0.0)
    n_comp = min(int(n_components), matrix.shape[0] - 1, matrix.shape[1])
    n_comp = max(n_comp, 1)
    pca = PCA(n_components=n_comp)
    coords = pca.fit_transform(X)
    # 坚持输出至少 PC1/PC2（n_comp==1 时 PC2 用 0）
    pc1 = coords[:, 0]
    pc2 = coords[:, 1] if n_comp > 1 else np.zeros_like(pc1)
    coords_2d = np.column_stack([pc1, pc2])
    return {
        "n_components": int(n_comp),
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "coords": coords_2d.tolist(),
    }


def _silhouette_safe(coords_2d: np.ndarray, labels: np.ndarray) -> Optional[float]:
    """
    silhouette_score（PC1–PC2 上）。
    - 过滤掉计数 < 2 的类别（避免 silhouette 报错）
    - 要求：>= 3 个样本、>= 2 个类别
    """
    coords = np.asarray(coords_2d, dtype=float)
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
    if np.unique(labs_f).size < 2:
        return None
    le = LabelEncoder()
    y = le.fit_transform(labs_f)
    try:
        return float(silhouette_score(coords_f, y, metric="euclidean"))
    except Exception:
        return None


def _mean_pairwise_centroid_distance(coords_2d: np.ndarray, batch_labels: np.ndarray) -> float:
    """
    batch centroid distance：不同 batch 的中心点在 PC1–PC2 上的平均两两欧氏距离（越大表示 batch 分离越明显）。
    """
    coords = np.asarray(coords_2d, dtype=float)
    labs = np.asarray(batch_labels).astype(str)
    uniq = np.unique(labs)
    if uniq.size < 2:
        return 0.0
    cents: list[np.ndarray] = []
    for b in uniq:
        m = labs == b
        if m.sum() == 0:
            continue
        cents.append(np.nanmean(coords[m, :2], axis=0))
    dists: list[float] = []
    for i in range(len(cents)):
        for j in range(i + 1, len(cents)):
            dists.append(float(np.linalg.norm(cents[i] - cents[j])))
    return float(np.mean(dists)) if dists else 0.0


def _plot_before_after_four_panel(
    *,
    before_coords: np.ndarray,
    after_coords: np.ndarray,
    meta: pd.DataFrame,
    before_title: str,
    after_title: str,
    out_path: Path,
) -> None:
    """
    PCA 对比图（2x2）：
    - before: batch_id / group_label
    - after : batch_id / group_label
    """
    batch = meta["batch_id"].astype(str).values
    grp = meta["group_label"].astype(str).values

    def _xy(coords: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x = coords[:, 0]
        y = coords[:, 1] if coords.shape[1] > 1 else np.zeros_like(x)
        return x, y

    def _draw(ax, coords: np.ndarray, labels: np.ndarray, title: str, max_legend: int = 12) -> None:
        uniq = list(dict.fromkeys(labels.tolist()))
        cmap = matplotlib.colormaps.get_cmap("tab20").resampled(max(len(uniq), 1))
        shown = uniq[:max_legend]
        x, y = _xy(coords)
        for i, g in enumerate(shown):
            mask = labels == g
            ax.scatter(x[mask], y[mask], s=10, alpha=0.75, label=str(g)[:32], color=cmap(i))
        if len(uniq) > max_legend:
            ax.scatter([], [], c="0.5", label=f"... (+{len(uniq)-max_legend})")
        ax.set_title(title)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=120)
    _draw(axes[0, 0], before_coords, batch, f"{before_title} — colored by batch_id")
    _draw(axes[0, 1], before_coords, grp, f"{before_title} — colored by group_label", max_legend=10)
    _draw(axes[1, 0], after_coords, batch, f"{after_title} — colored by batch_id")
    _draw(axes[1, 1], after_coords, grp, f"{after_title} — colored by group_label", max_legend=10)
    for ax in axes.ravel():
        ax.legend(loc="best", fontsize=6, ncol=1)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def run_preprocess_method_comparison_evaluation(
    *,
    matrices_by_method: Dict[str, pd.DataFrame],
    sample_meta: pd.DataFrame,
    output_dir: Path,
    n_components: int = 2,
    before_method: Optional[str] = None,
    after_method: Optional[str] = None,
) -> Dict[str, Any]:
    """
    评估模块：对不同处理方法的结果做统一对比。

    输入：
    - matrices_by_method: {method_name: matrix}，matrix 为 sample x feature
      典型方法：mean / median / knn / baseline
    - sample_meta：必须包含 batch_id 与 group_label（以及 merged_sample_id 或 sample_col_name 作为主键）

    输出：
    - evaluation_report.json：统一结构（包含每种方法的指标与 PCA 信息）
    - evaluation_table.csv：每种方法一行（便于论文表格/答辩截图）
    - pca_before_vs_after.png：选择一个 before 与 after 的 PCA 四宫格对比图（batch_id / group_label）
    """
    if not matrices_by_method:
        raise ValueError("evaluation_compare: matrices_by_method 不能为空。")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 选择 before/after 用于图对比：默认 before=第一个非 baseline；after=baseline（若存在）
    methods = list(matrices_by_method.keys())
    default_before = next((m for m in methods if m.lower() != "baseline"), methods[0])
    default_after = "baseline" if any(m.lower() == "baseline" for m in methods) else default_before
    m_before = before_method or default_before
    m_after = after_method or default_after
    if m_before not in matrices_by_method:
        raise ValueError(f"evaluation_compare: before_method 不存在: {m_before}")
    if m_after not in matrices_by_method:
        raise ValueError(f"evaluation_compare: after_method 不存在: {m_after}")

    # 统一对齐：以 before 的样本顺序为基准；要求其它方法至少包含同样的 index（可多不可少）
    base_idx = matrices_by_method[m_before].index.astype(str)
    aligned_mats: Dict[str, pd.DataFrame] = {}
    for name, mat in matrices_by_method.items():
        m = mat.copy()
        m.index = m.index.astype(str)
        if not set(base_idx).issubset(set(m.index.astype(str))):
            raise ValueError(f"evaluation_compare: 方法 {name} 的 matrix 样本与 base 不一致（缺少样本）。")
        aligned_mats[name] = m.loc[base_idx]

    meta = _align_sample_meta_for_matrix(aligned_mats[m_before], sample_meta)
    for col in ("batch_id", "group_label"):
        if col not in meta.columns:
            raise ValueError(f"evaluation_compare: sample_meta 缺少 {col}")

    batch_labels = meta["batch_id"].astype(str).values
    group_labels = meta["group_label"].astype(str).values

    per_method: Dict[str, Any] = {}
    table_rows: list[dict[str, Any]] = []

    def _display_name(method_internal: str) -> str:
        # 对外命名收紧：避免误解为标准 ComBat 已实现
        return "combat-like" if method_internal.lower() == "combat" else method_internal

    for name, mat in aligned_mats.items():
        display = _display_name(name)
        pca = _pca_2d_payload(mat, n_components=n_components)
        coords_2d = np.asarray(pca["coords"], dtype=float)

        sil_batch = _silhouette_safe(coords_2d, batch_labels)
        sil_group = _silhouette_safe(coords_2d, group_labels)
        centroid_dist = _mean_pairwise_centroid_distance(coords_2d, batch_labels)

        per_method[name] = {
            "method": display,
            "method_internal": name,
            "display_name": display,
            "n_samples": int(mat.shape[0]),
            "n_features": int(mat.shape[1]),
            "pca": pca,
            "metrics": {
                "silhouette_batch_id_pc12": sil_batch,
                "silhouette_group_label_pc12": sil_group,
                "batch_centroid_separation_pc12": centroid_dist,
            },
        }

        # 每种方法保存 PCA 坐标 JSON（便于前端/后续扩展）
        pca_path = output_dir / f"pca_{name}.json"
        with pca_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "method": name,
                    "n_components": per_method[name]["pca"]["n_components"],
                    "explained_variance_ratio": per_method[name]["pca"]["explained_variance_ratio"],
                    "coords": per_method[name]["pca"]["coords"],
                    "sample_index": aligned_mats[name].index.astype(str).tolist(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        per_method[name]["pca_json_path"] = str(pca_path)

        table_rows.append(
            {
                "method": display,
                "method_internal": name,
                "n_samples": int(mat.shape[0]),
                "n_features": int(mat.shape[1]),
                "silhouette_batch_id_pc12": sil_batch,
                "silhouette_group_label_pc12": sil_group,
                "batch_centroid_separation_pc12": centroid_dist,
            }
        )

    # 写 evaluation_table.csv
    table_df = pd.DataFrame(table_rows).sort_values(by="method")
    table_path = output_dir / "evaluation_table.csv"
    table_df.to_csv(table_path, index=False, encoding="utf-8")

    # PCA 对比图（before vs after）
    before_coords = np.asarray(per_method[m_before]["pca"]["coords"], dtype=float)
    after_coords = np.asarray(per_method[m_after]["pca"]["coords"], dtype=float)
    plot_path = output_dir / "pca_before_vs_after.png"
    _plot_before_after_four_panel(
        before_coords=before_coords,
        after_coords=after_coords,
        meta=meta,
        before_title=f"Before ({m_before})",
        after_title=f"After ({m_after})",
        out_path=plot_path,
    )

    report = {
        "schema_version": "evaluation_report_v1",
        "n_methods": int(len(per_method)),
        # methods_order 为“内部 key 顺序”（便于程序稳定引用）；对外展示请用 methods_display_order / display_name
        "methods_order": sorted(per_method.keys()),
        "methods_display_order": [_display_name(k) for k in sorted(per_method.keys())],
        "inputs": {
            "methods": sorted(per_method.keys()),
            "methods_display_names": {k: _display_name(k) for k in sorted(per_method.keys())},
            "n_components": int(n_components),
            "before_method_for_plot": m_before,
            "after_method_for_plot": m_after,
            "before_method_for_plot_display": _display_name(m_before),
            "after_method_for_plot_display": _display_name(m_after),
        },
        "outputs": {
            "evaluation_report_json": "evaluation_report.json",
            "evaluation_table_csv": "evaluation_table.csv",
            "pca_before_vs_after_png": "pca_before_vs_after.png",
        },
        "methods": per_method,
        "notes": [
            "指标计算在 PC1–PC2 上完成（用于统一可视化与对比）。",
            "silhouette 会过滤样本数不足的类别（count<2）并在不满足条件时返回 null。",
            "batch_centroid_separation_pc12 为不同 batch 在 PC1–PC2 上的中心点平均两两距离（越大表示 batch 分离越明显）。",
            "命名约定：对外展示中 'combat-like' 表示简化的按 batch 位置-尺度对齐方法，并非标准 strict ComBat（经验 Bayes）实现。",
        ],
    }
    report_path = output_dir / "evaluation_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return {
        "evaluation_report_path": str(report_path),
        "evaluation_table_path": str(table_path),
        "pca_before_vs_after_path": str(plot_path),
        "before_method": m_before,
        "after_method": m_after,
        "methods": sorted(per_method.keys()),
    }

