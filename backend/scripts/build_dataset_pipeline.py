"""
build_dataset_pipeline.py
为 amide / bioheart / mi 数据集生成与 benchmark_merged 格式一致的 _pipeline 产物。

用法:
    python scripts/build_dataset_pipeline.py --dataset bioheart
    python scripts/build_dataset_pipeline.py --dataset amide
    python scripts/build_dataset_pipeline.py --dataset mi
    python scripts/build_dataset_pipeline.py --dataset all

输出目录（相对于 backend/data/processed/）:
    <dataset_name>/
    ├── merge_report.json
    ├── merged_sample_meta.csv
    ├── merged_sample_by_feature.csv
    └── _pipeline/
        ├── batch_correction_method_report.json
        ├── batch_correction_metrics.json
        ├── batch_corrected_sample_by_feature.csv
        ├── pca_after_correction.json
        ├── pca_before_vs_after_batch_correction.png
        └── evaluation/
            ├── evaluation_report.json
            ├── evaluation_table.csv
            └── pca_*.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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

# ---- 项目根路径配置 ----
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"

# ---- 数据源路径 ----
DATA_SOURCE_DIR = Path("/Users/gaoyunduan/Downloads/data")

DATASET_CONFIGS: Dict[str, Dict[str, Any]] = {
    "bioheart": {
        "csv": DATA_SOURCE_DIR / "bioheart" / "bioheart.csv",
        "label": "BioHeart 数据集",
        "description": "BioHeart 心脏生物标志物代谢组学数据集（1300 样本，56 代谢物，15 批次）",
        "qc_group": "QC",  # QC 样本组名，None 表示无 QC
    },
    "amide": {
        "csv": DATA_SOURCE_DIR / "amide" / "amide.csv",
        "label": "AMIDE 数据集",
        "description": "AMIDE 代谢组学数据集（598 样本，6462 代谢特征，3 批次）",
        "qc_group": "QC",
    },
    "mi": {
        "csv": DATA_SOURCE_DIR / "mi" / "mi.csv",
        "label": "MI（心肌梗死）数据集",
        "description": "MI 心肌梗死预后代谢组学数据集（902 样本，15 代谢物，2 批次）",
        "qc_group": None,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # 统一列名小写（容错）
    cols = df.columns.tolist()
    rename = {}
    for c in cols:
        cl = c.lower()
        if cl == "sample" and c != "sample":
            rename[c] = "sample"
        elif cl == "group" and c != "group":
            rename[c] = "group"
        elif cl == "batch" and c != "batch":
            rename[c] = "batch"
    if rename:
        df = df.rename(columns=rename)
    return df


def _feature_cols(df: pd.DataFrame) -> List[str]:
    """返回特征列（排除 sample/group/batch/injection_order 等元信息列）。"""
    meta_cols = {"sample", "group", "batch", "injection_order", "replicate_group"}
    return [c for c in df.columns if c.lower() not in meta_cols]


def _pca_2d(X: np.ndarray) -> Tuple[np.ndarray, PCA]:
    n_comp = min(2, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_comp)
    coords = pca.fit_transform(X)
    if coords.shape[1] < 2:
        coords = np.hstack([coords, np.zeros((coords.shape[0], 1))])
    return coords, pca


def _silhouette_safe(coords: np.ndarray, labels: np.ndarray) -> Optional[float]:
    labs = np.asarray(labels).astype(str)
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


def _centroid_separation(coords: np.ndarray, labels: np.ndarray) -> float:
    labs = np.asarray(labels).astype(str)
    B = np.unique(labs)
    if B.size < 2:
        return 0.0
    cents = [np.mean(coords[labs == b, :2], axis=0) for b in B]
    dists = [float(np.linalg.norm(cents[i] - cents[j]))
             for i in range(len(cents)) for j in range(i + 1, len(cents))]
    return float(np.mean(dists)) if dists else 0.0


def _per_feature_baseline_correction(X: pd.DataFrame, batch_labels: np.ndarray) -> pd.DataFrame:
    """
    逐特征-逐批次位置尺度对齐到全局（与 benchmark_merged 的 baseline 方法一致）。
    """
    X_corr = X.copy()
    global_means = X.mean(axis=0)
    global_stds = X.std(axis=0).replace(0, 1)
    for b in np.unique(batch_labels):
        mask = batch_labels == b
        batch_means = X.loc[mask].mean(axis=0)
        batch_stds = X.loc[mask].std(axis=0).replace(0, 1)
        X_corr.loc[mask] = (X.loc[mask] - batch_means) / batch_stds * global_stds + global_means
    return X_corr


def _draw_four_panel(
    coords_bef: np.ndarray,
    coords_aft: np.ndarray,
    batch_labels: np.ndarray,
    group_labels: np.ndarray,
    out_path: Path,
    dataset_label: str,
) -> None:
    def _draw(ax, coords, labels, title, max_legend=15):
        uniq = list(dict.fromkeys(labels.tolist()))
        cmap = matplotlib.colormaps.get_cmap("tab20").resampled(max(len(uniq), 1))
        for i, g in enumerate(uniq[:max_legend]):
            mask = labels == g
            ax.scatter(coords[mask, 0], coords[mask, 1], s=10, alpha=0.75,
                       label=str(g)[:32], color=cmap(i % 20))
        if len(uniq) > max_legend:
            ax.scatter([], [], c="0.5", label=f"... (+{len(uniq)-max_legend})")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.legend(loc="best", fontsize=6, ncol=1)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=120)
    _draw(axes[0, 0], coords_bef, batch_labels, "Before correction — by batch")
    _draw(axes[0, 1], coords_bef, group_labels, "Before correction — by group")
    _draw(axes[1, 0], coords_aft, batch_labels, "After correction — by batch")
    _draw(axes[1, 1], coords_aft, group_labels, "After correction — by group")
    fig.suptitle(
        f"PCA before vs after baseline batch correction\n({dataset_label})",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _pca_to_json(coords: np.ndarray, pca_obj: PCA, meta_df: pd.DataFrame) -> Dict[str, Any]:
    """将 PCA 坐标转为前端 EV 图所需的 JSON 格式。"""
    evr = pca_obj.explained_variance_ratio_.tolist()
    points = []
    for i, (pc1, pc2) in enumerate(zip(coords[:, 0], coords[:, 1])):
        row = meta_df.iloc[i]
        points.append({
            "sample": str(row.get("sample", i)),
            "group": str(row.get("group", "")),
            "batch": str(row.get("batch", "")),
            "pc1": float(pc1),
            "pc2": float(pc2),
        })
    return {
        "explained_variance_ratio": evr,
        "pc_labels": [f"PC1 ({evr[0]:.1%})", f"PC2 ({evr[1]:.1%})" if len(evr) > 1 else "PC2"],
        "points": points,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 主处理函数
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset_pipeline(dataset_name: str) -> None:
    cfg = DATASET_CONFIGS[dataset_name]
    csv_path: Path = cfg["csv"]
    dataset_label: str = cfg["label"]
    qc_group: Optional[str] = cfg["qc_group"]

    print(f"\n{'='*60}")
    print(f"处理数据集: {dataset_label}")
    print(f"源文件: {csv_path}")

    if not csv_path.exists():
        print(f"[错误] 数据文件不存在: {csv_path}")
        return

    # ---- 输出目录 ----
    out_dir = PROCESSED_DIR / dataset_name
    pipeline_dir = out_dir / "_pipeline"
    eval_dir = pipeline_dir / "evaluation"
    for d in [out_dir, pipeline_dir, eval_dir]:
        d.mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {out_dir}")

    # ---- 读取数据 ----
    df = _load_csv(csv_path)
    feat_cols = _feature_cols(df)
    print(f"总样本数: {len(df)}, 特征数: {len(feat_cols)}")
    print(f"groups: {df['group'].unique().tolist()}")
    print(f"batches: {sorted(df['batch'].unique().tolist())}")

    # ---- 生成 merged_sample_meta.csv ----
    meta = df[["sample", "group", "batch"]].copy()
    meta = meta.rename(columns={"sample": "sample_col_name", "group": "group_label", "batch": "batch_id"})
    meta["merged_sample_id"] = [f"{dataset_name}::{i}" for i in range(len(meta))]
    # 标记 QC 样本
    if qc_group:
        meta["sample_type"] = meta["group_label"].apply(
            lambda g: "qc" if str(g) == qc_group else "formal_or_unknown"
        )
    else:
        meta["sample_type"] = "formal_or_unknown"
    meta.to_csv(out_dir / "merged_sample_meta.csv", index=False)

    # ---- 生成 merged_sample_by_feature.csv ----
    feat_df = df[feat_cols].copy()
    feat_df.index = meta["merged_sample_id"].values
    feat_df.index.name = "merged_sample_id"
    feat_df.to_csv(out_dir / "merged_sample_by_feature.csv")

    # ---- 生成 merge_report.json ----
    batch_counts = df["batch"].value_counts().to_dict()
    group_counts = df["group"].value_counts().to_dict()
    missing_ratio = float(df[feat_cols].isna().sum().sum() / (len(df) * len(feat_cols)))
    merge_report = {
        "merged_batch_count": df["batch"].nunique(),
        "merged_sample_count": len(df),
        "merged_feature_count": len(feat_cols),
        "feature_alignment_key": "column_name",
        "merge_strategy": "single_file",
        "per_batch_sample_count": {str(k): int(v) for k, v in batch_counts.items()},
        "missing_ratio_after_merge": missing_ratio,
        "batch_id_unique_values": [str(b) for b in sorted(df["batch"].unique())],
        "sample_type_counts": {
            "formal_or_unknown": int((meta["sample_type"] == "formal_or_unknown").sum()),
            "qc": int((meta["sample_type"] == "qc").sum()),
        },
        "group_label_counts": {str(k): int(v) for k, v in group_counts.items()},
        "dataset_label": dataset_label,
        "description": cfg["description"],
        "notes": [
            f"数据集: {dataset_name}",
            f"源文件: {csv_path.name}",
        ],
    }
    (out_dir / "merge_report.json").write_text(
        json.dumps(merge_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] merge_report.json 已生成")

    # ---- 特征矩阵准备（去除 QC 样本做校正和 PCA，但保留 QC 在 meta 里）----
    X_all = feat_df.fillna(0.0)
    batch_all = meta["batch_id"].astype(str).values
    group_all = meta["group_label"].astype(str).values

    # 用所有样本（含 QC）做 PCA（与 benchmark 一致）
    X_arr = X_all.values.astype(float)

    # ---- PCA before ----
    coords_bef, pca_bef = _pca_2d(X_arr)
    pca_bef_json = _pca_to_json(coords_bef, pca_bef, meta)
    (pipeline_dir / "pca_before.json").write_text(
        json.dumps(pca_bef_json, ensure_ascii=False), encoding="utf-8"
    )

    # ---- 批次校正 ----
    X_corr = _per_feature_baseline_correction(X_all, batch_all)
    X_corr_arr = X_corr.values.astype(float)
    X_corr.to_csv(pipeline_dir / "batch_corrected_sample_by_feature.csv")
    print(f"[OK] batch_corrected_sample_by_feature.csv 已生成")

    # ---- PCA after ----
    coords_aft, pca_aft = _pca_2d(X_corr_arr)
    pca_aft_json = _pca_to_json(coords_aft, pca_aft, meta)
    (pipeline_dir / "pca_after_correction.json").write_text(
        json.dumps(pca_aft_json, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] pca_after_correction.json 已生成")

    # ---- 批次校正指标 ----
    sil_batch_bef = _silhouette_safe(coords_bef, batch_all)
    sil_batch_aft = _silhouette_safe(coords_aft, batch_all)
    sil_group_bef = _silhouette_safe(coords_bef, group_all)
    sil_group_aft = _silhouette_safe(coords_aft, group_all)
    cent_bef = _centroid_separation(coords_bef, batch_all)
    cent_aft = _centroid_separation(coords_aft, batch_all)

    delta_sil_batch = (sil_batch_aft - sil_batch_bef) if (sil_batch_bef is not None and sil_batch_aft is not None) else None
    delta_sil_group = (sil_group_aft - sil_group_bef) if (sil_group_bef is not None and sil_group_aft is not None) else None
    delta_cent = cent_aft - cent_bef
    mixing_improved = delta_cent < 0

    evr_bef = pca_bef.explained_variance_ratio_.tolist()
    evr_aft = pca_aft.explained_variance_ratio_.tolist()

    metrics_json = {
        "baseline_method_id": "per_feature_batch_location_scale_baseline",
        "strict_combat": {"status": "not_implemented", "note": "strict ComBat 尚未实现。"},
        "pca_components": 2,
        "explained_variance_ratio_before_pc": evr_bef,
        "explained_variance_ratio_after_pc": evr_aft,
        "silhouette_batch_id_pc12_before": sil_batch_bef,
        "silhouette_batch_id_pc12_after": sil_batch_aft,
        "delta_silhouette_batch_id": delta_sil_batch,
        "silhouette_group_label_pc12_before": sil_group_bef,
        "silhouette_group_label_pc12_after": sil_group_aft,
        "delta_silhouette_group_label": delta_sil_group,
        "batch_centroid_separation_pc12_before": cent_bef,
        "batch_centroid_separation_pc12_after": cent_aft,
        "delta_batch_centroid_separation": delta_cent,
        "heuristic_mixing_improved_by_centroid": mixing_improved,
        "heuristic_mixing_improved_by_silhouette": (delta_sil_batch < 0) if delta_sil_batch is not None else None,
        "heuristic_mixing_improved": mixing_improved,
        "heuristic_mixing_notes": [
            "以 batch 质心距离为主判据评估批次混合改善情况。"
        ],
        "heuristic_group_overdistorted": False if delta_sil_group is None else (delta_sil_group < -0.1),
        "baseline_suitability_summary": "逐特征位置尺度对齐到全局分布（baseline）。",
    }
    (pipeline_dir / "batch_correction_metrics.json").write_text(
        json.dumps(metrics_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] batch_correction_metrics.json 已生成")
    print(f"  batch centroid: {cent_bef:.4f} → {cent_aft:.4f}  mixing_improved={mixing_improved}")
    if sil_batch_bef is not None:
        print(f"  silhouette(batch): {sil_batch_bef:.4f} → {sil_batch_aft:.4f}")

    # ---- batch_correction_method_report.json ----
    method_report = {
        "schema_version": "1.0",
        "baseline_batch_correction": {
            "method_id": "per_feature_batch_location_scale_baseline",
            "method_display_name": "Per-Feature Batch Location–Scale Alignment to Global (Baseline)",
            "assumptions": [
                "批次效应近似为逐特征位置与尺度偏移",
                "各批次内样本分布近似正态",
            ],
            "limitations": [
                "不处理批次×生物学交互效应",
                "不等同于 empirical Bayes ComBat",
            ],
        },
        "strict_combat": {
            "status": "not_implemented",
            "note": "strict ComBat（empirical Bayes）尚未在本项目中实现。",
        },
        "dataset": dataset_name,
        "dataset_label": dataset_label,
    }
    (pipeline_dir / "batch_correction_method_report.json").write_text(
        json.dumps(method_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] batch_correction_method_report.json 已生成")

    # ---- PCA 四宫格图 ----
    _draw_four_panel(
        coords_bef, coords_aft,
        batch_all, group_all,
        pipeline_dir / "pca_before_vs_after_batch_correction.png",
        dataset_label=dataset_label,
    )
    print(f"[OK] pca_before_vs_after_batch_correction.png 已生成")

    # ---- evaluation（方法对比）产物 ----
    _build_evaluation(
        X_all=X_all,
        X_baseline=X_corr,
        meta=meta,
        eval_dir=eval_dir,
        dataset_label=dataset_label,
    )

    print(f"\n[完成] {dataset_label} pipeline 产物已写入: {out_dir}")


def _build_evaluation(
    X_all: pd.DataFrame,
    X_baseline: pd.DataFrame,
    meta: pd.DataFrame,
    eval_dir: Path,
    dataset_label: str,
) -> None:
    """生成方法对比 evaluation 产物（与 benchmark evaluation 格式一致）。"""
    batch_labels = meta["batch_id"].astype(str).values
    group_labels = meta["group_label"].astype(str).values

    methods_data = {}
    pca_jsons = {}

    # before（不校正）
    X_before_arr = X_all.fillna(0.0).values.astype(float)
    coords_bef, pca_bef = _pca_2d(X_before_arr)
    pca_jsons["baseline"] = _pca_to_json(coords_bef, pca_bef, meta)

    # baseline 校正后
    X_corr_arr = X_baseline.fillna(0.0).values.astype(float)
    coords_aft, pca_aft = _pca_2d(X_corr_arr)
    pca_jsons["baseline"] = _pca_to_json(coords_aft, pca_aft, meta)

    # 方法 1: mean 填充（不校正，仅作对照）
    X_mean = X_all.fillna(X_all.mean())
    coords_mean, pca_mean = _pca_2d(X_mean.values.astype(float))
    pca_jsons["mean"] = _pca_to_json(coords_mean, pca_mean, meta)
    sil_b_m = _silhouette_safe(coords_mean, batch_labels)
    cent_m = _centroid_separation(coords_mean, batch_labels)
    methods_data["mean"] = {
        "method": "mean",
        "display_name": "Mean Imputation（对照）",
        "silhouette_batch": sil_b_m,
        "batch_centroid_dist": cent_m,
    }

    # 方法 2: baseline 校正
    sil_b_bl = _silhouette_safe(coords_aft, batch_labels)
    cent_bl = _centroid_separation(coords_aft, batch_labels)
    methods_data["baseline"] = {
        "method": "baseline",
        "display_name": "Baseline Correction",
        "silhouette_batch": sil_b_bl,
        "batch_centroid_dist": cent_bl,
    }

    # 写入 evaluation_table.csv
    rows = []
    for m, d in methods_data.items():
        rows.append({
            "method": m,
            "display_name": d["display_name"],
            "silhouette_batch_id_pc12": d["silhouette_batch"],
            "batch_centroid_separation_pc12": d["batch_centroid_dist"],
        })
    pd.DataFrame(rows).to_csv(eval_dir / "evaluation_table.csv", index=False)

    # 写入各方法 PCA JSON
    for method_name, pca_data in pca_jsons.items():
        (eval_dir / f"pca_{method_name}.json").write_text(
            json.dumps(pca_data, ensure_ascii=False), encoding="utf-8"
        )

    # 写入 evaluation_report.json
    eval_report = {
        "schema_version": "1.0",
        "dataset": dataset_label,
        "methods_order": list(methods_data.keys()),
        "methods_display_order": list(methods_data.keys()),
        "inputs": {
            "methods_display_names": {m: d["display_name"] for m, d in methods_data.items()},
            "before_method_for_plot": "mean",
            "after_method_for_plot": "baseline",
            "before_method_for_plot_display": "Mean Imputation（对照）",
            "after_method_for_plot_display": "Baseline Correction",
        },
        "methods": methods_data,
        "note": f"方法对比实验产物（{dataset_label}）。",
    }
    (eval_dir / "evaluation_report.json").write_text(
        json.dumps(eval_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 生成对比 PCA 图
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=120)
    batch_arr = batch_labels
    cmap = matplotlib.colormaps.get_cmap("tab20")
    uniq_b = list(dict.fromkeys(batch_arr.tolist()))
    for i, b in enumerate(uniq_b[:15]):
        mask = batch_arr == b
        axes[0].scatter(coords_mean[mask, 0], coords_mean[mask, 1], s=8, alpha=0.7,
                        label=str(b)[:20], color=cmap(i % 20))
        axes[1].scatter(coords_aft[mask, 0], coords_aft[mask, 1], s=8, alpha=0.7,
                        label=str(b)[:20], color=cmap(i % 20))
    axes[0].set_title("Before（Mean Imputation）", fontsize=9)
    axes[1].set_title("After（Baseline Correction）", fontsize=9)
    for ax in axes:
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.legend(loc="best", fontsize=6, ncol=1)
    fig.suptitle(f"方法对比 PCA（{dataset_label}）", fontsize=10)
    fig.tight_layout()
    fig.savefig(eval_dir / "pca_before_vs_after.png")
    plt.close(fig)

    print(f"[OK] evaluation 产物已生成: {eval_dir}")


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="为非 benchmark 数据集生成 pipeline 产物")
    parser.add_argument(
        "--dataset",
        choices=list(DATASET_CONFIGS.keys()) + ["all"],
        required=True,
        help="要处理的数据集名称，或 'all' 处理全部",
    )
    args = parser.parse_args()

    datasets = list(DATASET_CONFIGS.keys()) if args.dataset == "all" else [args.dataset]
    for ds in datasets:
        build_dataset_pipeline(ds)


if __name__ == "__main__":
    main()
