"""
缺失值填充方法评估服务（Mask-then-Impute）

评估策略
---------
在已完整填充的矩阵上，随机遮蔽一定比例的值为 NaN（模拟缺失），
分别用 mean / median / KNN 三种方法填充，与真实值对比计算 RMSE / MAE，
量化不同填充方法的精度。

输出产物
---------
- imputation_eval_report.json   : 每种方法的汇总指标
- imputation_eval_feature.json  : 每种方法在各特征上的 RMSE（用于箱线图）
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer


# ---- 核心算法 ----

def _impute_mean(X_masked: np.ndarray) -> np.ndarray:
    fills = np.nanmean(X_masked, axis=0)
    fills = np.nan_to_num(fills, nan=0.0)
    idx = np.isnan(X_masked)
    result = X_masked.copy()
    result[idx] = np.take(fills, np.where(idx)[1])
    return result


def _impute_median(X_masked: np.ndarray) -> np.ndarray:
    fills = np.nanmedian(X_masked, axis=0)
    fills = np.nan_to_num(fills, nan=0.0)
    idx = np.isnan(X_masked)
    result = X_masked.copy()
    result[idx] = np.take(fills, np.where(idx)[1])
    return result


def _impute_knn(X_masked: np.ndarray, k: int = 5) -> np.ndarray:
    n = X_masked.shape[0]
    k = min(k, max(1, n - 1))
    imputer = KNNImputer(n_neighbors=k)
    return imputer.fit_transform(X_masked)


def _rmse(true: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((true - pred) ** 2)))


def _mae(true: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(true - pred)))


def _nrmse(true: np.ndarray, pred: np.ndarray) -> float:
    """Normalized RMSE (除以真实值标准差，使不同特征可比)。"""
    std = np.std(true)
    return float(np.sqrt(np.mean((true - pred) ** 2)) / (std + 1e-8))


# ---- 主评估函数 ----

def run_imputation_mask_evaluation(
    *,
    matrix: pd.DataFrame,
    mask_ratio: float = 0.15,
    knn_k: int = 5,
    n_repeats: int = 3,
    random_seed: int = 42,
    output_dir: Path,
    methods: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Mask-then-Impute 评估。

    Parameters
    ----------
    matrix : sample × feature，不含 NaN（已完成原始填充的矩阵）
    mask_ratio : 随机遮蔽比例（默认 15%）
    knn_k : KNN 填充的 k 值
    n_repeats : 重复次数（取平均，减少随机性）
    random_seed : 随机种子
    output_dir : 产物写入目录
    methods : 需要评估的方法列表（默认 ['mean', 'median', 'knn']）

    Returns
    -------
    dict 含 report_path, feature_rmse_path, summary 等
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if methods is None:
        methods = ["mean", "median", "knn"]

    X_full = matrix.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    n_samples, n_features = X_full.shape

    if np.isnan(X_full).any():
        # 把已有 NaN 剔除（评估要求基准值已知）
        col_valid = ~np.isnan(X_full).all(axis=0)
        X_full = X_full[:, col_valid]
        n_features = X_full.shape[1]

    n_mask = max(1, int(X_full.size * mask_ratio))

    # ---- 累计各方法的指标 ----
    method_rmse_acc: Dict[str, List[float]] = {m: [] for m in methods}
    method_mae_acc:  Dict[str, List[float]] = {m: [] for m in methods}
    method_nrmse_acc: Dict[str, List[float]] = {m: [] for m in methods}
    # 每个特征的 RMSE（用于箱线图，只保存最后一次 repeat）
    method_feature_rmse: Dict[str, List[float]] = {m: [] for m in methods}

    rng = np.random.default_rng(random_seed)

    t_start = time.time()
    for rep in range(n_repeats):
        # 随机遮蔽
        flat_idx = rng.choice(X_full.size, size=n_mask, replace=False)
        row_idx, col_idx = np.unravel_index(flat_idx, X_full.shape)
        X_masked = X_full.copy()
        X_masked[row_idx, col_idx] = np.nan

        true_vals = X_full[row_idx, col_idx]

        for m in methods:
            if m == "mean":
                X_imp = _impute_mean(X_masked)
            elif m == "median":
                X_imp = _impute_median(X_masked)
            elif m == "knn":
                X_imp = _impute_knn(X_masked, k=knn_k)
            else:
                continue

            pred_vals = X_imp[row_idx, col_idx]
            method_rmse_acc[m].append(_rmse(true_vals, pred_vals))
            method_mae_acc[m].append(_mae(true_vals, pred_vals))
            method_nrmse_acc[m].append(_nrmse(true_vals, pred_vals))

            # 最后一次 repeat 计算各特征 RMSE（供箱线图）
            if rep == n_repeats - 1:
                per_feat_rmse = []
                for j in range(n_features):
                    feat_mask = col_idx == j
                    if feat_mask.sum() == 0:
                        per_feat_rmse.append(None)
                        continue
                    per_feat_rmse.append(_rmse(true_vals[feat_mask], pred_vals[feat_mask]))
                method_feature_rmse[m] = per_feat_rmse

    elapsed = time.time() - t_start

    # ---- 汇总 ----
    summary: Dict[str, Any] = {}
    for m in methods:
        summary[m] = {
            "method": m,
            "rmse_mean":  float(np.mean(method_rmse_acc[m])),
            "rmse_std":   float(np.std(method_rmse_acc[m])),
            "mae_mean":   float(np.mean(method_mae_acc[m])),
            "mae_std":    float(np.std(method_mae_acc[m])),
            "nrmse_mean": float(np.mean(method_nrmse_acc[m])),
            "nrmse_std":  float(np.std(method_nrmse_acc[m])),
        }

    # 排名（以 RMSE 升序）
    ranking = sorted(methods, key=lambda m: summary[m]["rmse_mean"])

    report: Dict[str, Any] = {
        "schema_version": "imputation_eval_v1",
        "config": {
            "mask_ratio": mask_ratio,
            "n_repeats": n_repeats,
            "knn_k": knn_k,
            "random_seed": random_seed,
            "n_samples": n_samples,
            "n_features": n_features,
            "n_masked_per_repeat": n_mask,
        },
        "elapsed_seconds": round(elapsed, 2),
        "methods": summary,
        "ranking_by_rmse": ranking,
        "best_method": ranking[0] if ranking else None,
        "notes": [
            "评估方式：Mask-then-Impute（在无缺失矩阵上随机遮蔽后填充，与真值对比）。",
            f"指标平均自 {n_repeats} 次独立重复（不同随机遮蔽种子）。",
            "RMSE/MAE 越低越好；NRMSE = RMSE / 特征标准差（用于跨特征归一化比较）。",
            "特征级 RMSE 分布见 imputation_eval_feature.json，可用于箱线图。",
        ],
    }

    report_path = output_dir / "imputation_eval_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 特征级 RMSE（箱线图数据）
    feat_report: Dict[str, Any] = {
        "methods": methods,
        "n_features": n_features,
        "feature_rmse_by_method": {
            m: method_feature_rmse.get(m, []) for m in methods
        },
        "note": (
            "feature_rmse_by_method 中每项对应一个特征的 RMSE（最后一次 repeat）。"
            "None 表示该特征在本次遮蔽中无被遮蔽的值，无法计算 RMSE。"
        ),
    }
    feat_path = output_dir / "imputation_eval_feature.json"
    feat_path.write_text(json.dumps(feat_report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "report_path": str(report_path),
        "feature_rmse_path": str(feat_path),
        "summary": summary,
        "ranking_by_rmse": ranking,
        "best_method": ranking[0] if ranking else None,
        "elapsed_seconds": round(elapsed, 2),
    }
