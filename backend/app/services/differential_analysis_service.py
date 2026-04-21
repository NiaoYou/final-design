"""
差异代谢物分析服务（Differential Metabolite Analysis）

策略
-----
- 输入：batch 校正后矩阵（sample × feature）+ 样本元数据（含 group_label）
- 方法：独立双样本 t-test（scipy.stats.ttest_ind）
- 多重检验校正：Benjamini-Hochberg FDR（statsmodels.stats.multitest）
- 效应量：Log2 Fold Change（log2(mean_group2 / mean_group1)）
- 输出：每个特征的 p-value、adjusted p-value（q-value）、log2FC、显著性标签
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 辅助函数
# --------------------------------------------------------------------------- #

def _safe_log2fc(mean1: float, mean2: float, eps: float = 1e-9) -> float:
    """
    计算 log2(mean2 / mean1)，当 mean1 或 mean2 接近 0 时加小量避免 log(0)。
    正值表示 group2 上调，负值表示 group2 下调。
    """
    v1 = max(abs(mean1), eps)
    v2 = max(abs(mean2), eps)
    # 保留方向
    sign2 = 1.0 if mean2 >= 0 else -1.0
    sign1 = 1.0 if mean1 >= 0 else -1.0
    return float(np.log2(v2 / v1) * sign2 * sign1)


def _benjamini_hochberg(pvalues: np.ndarray) -> np.ndarray:
    """
    BH-FDR 校正（与 statsmodels 的 multipletests 结果一致）。
    对 NaN p-value 的特征保留 NaN q-value。
    """
    try:
        from statsmodels.stats.multitest import multipletests  # type: ignore
        mask = ~np.isnan(pvalues)
        qvalues = np.full_like(pvalues, np.nan)
        if mask.sum() > 0:
            _, q_corrected, _, _ = multipletests(pvalues[mask], method="fdr_bh")
            qvalues[mask] = q_corrected
        return qvalues
    except ImportError:
        # fallback: 手动 BH
        n = len(pvalues)
        mask = ~np.isnan(pvalues)
        qvalues = np.full(n, np.nan)
        valid_idx = np.where(mask)[0]
        p_valid = pvalues[valid_idx]
        order = np.argsort(p_valid)
        ranks = np.argsort(order) + 1
        q_valid = np.minimum(1.0, p_valid * len(p_valid) / ranks)
        # 单调化（cummin from right）
        q_valid = np.minimum.accumulate(q_valid[::-1])[::-1]
        qvalues[valid_idx] = q_valid
        return qvalues


# --------------------------------------------------------------------------- #
# 核心分析函数
# --------------------------------------------------------------------------- #

def run_differential_analysis(
    matrix: pd.DataFrame,
    sample_meta: pd.DataFrame,
    group1: str,
    group2: str,
    group_col: str = "group_label",
    fc_threshold: float = 1.0,
    pvalue_threshold: float = 0.05,
    use_fdr: bool = True,
    equal_var: bool = False,
) -> Dict[str, Any]:
    """
    在 matrix 的 group1 vs group2 子集上运行差异分析。

    Parameters
    ----------
    matrix : pd.DataFrame
        sample × feature，index = sample_id（字符串）。
    sample_meta : pd.DataFrame
        含 group_col 列，index 或某列为 sample_id。
    group1, group2 : str
        要比较的两个组名。group2 为"实验组"（fold change 方向参照）。
    group_col : str
        sample_meta 中标注组别的列名。
    fc_threshold : float
        |log2FC| 阈值，高于此值才标注为"显著上调/下调"。
    pvalue_threshold : float
        p-value / q-value 阈值。
    use_fdr : bool
        True 时用 q-value 做显著性判断，False 时用原始 p-value。
    equal_var : bool
        t-test 是否假设等方差（Welch t-test 时设 False）。

    Returns
    -------
    dict with keys:
        group1, group2, n_group1, n_group2,
        features: list of dicts (one per feature),
        summary: {n_total, n_sig_up, n_sig_down, n_sig}
    """
    from scipy import stats  # type: ignore

    t0 = time.time()

    # ---- 对齐 meta 与 matrix ----
    meta = sample_meta.copy()
    # 如果 sample_id 不是 index，尝试自动设定
    if "merged_sample_id" in meta.columns:
        meta = meta.set_index("merged_sample_id")
    elif "sample_id" in meta.columns:
        meta = meta.set_index("sample_id")
    meta.index = meta.index.astype(str)

    matrix = matrix.copy()
    matrix.index = matrix.index.astype(str)

    # 取交集
    common = matrix.index.intersection(meta.index)
    if len(common) == 0:
        raise ValueError(
            "matrix 与 sample_meta 无公共 index，请检查 sample_id 列名与格式。"
        )
    matrix = matrix.loc[common]
    meta = meta.loc[common]

    # ---- 筛选两组样本 ----
    idx1 = meta[meta[group_col] == group1].index
    idx2 = meta[meta[group_col] == group2].index

    if len(idx1) < 2:
        raise ValueError(f"'{group1}' 组样本数 {len(idx1)} < 2，无法做 t-test。")
    if len(idx2) < 2:
        raise ValueError(f"'{group2}' 组样本数 {len(idx2)} < 2，无法做 t-test。")

    mat1 = matrix.loc[idx1].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)  # n1 × p
    mat2 = matrix.loc[idx2].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)  # n2 × p
    feature_names: List[str] = matrix.columns.astype(str).tolist()
    p = len(feature_names)

    # ---- t-test 逐特征 ----
    pvalues = np.full(p, np.nan)
    tstats = np.full(p, np.nan)

    for i in range(p):
        col1 = mat1[:, i]
        col2 = mat2[:, i]
        valid1 = col1[~np.isnan(col1)]
        valid2 = col2[~np.isnan(col2)]
        if len(valid1) < 2 or len(valid2) < 2:
            continue
        t, pv = stats.ttest_ind(valid1, valid2, equal_var=equal_var)
        tstats[i] = float(t)
        pvalues[i] = float(pv)

    # ---- FDR 校正 ----
    qvalues = _benjamini_hochberg(pvalues)

    # ---- Fold Change ----
    mean1 = np.nanmean(mat1, axis=0)  # (p,)
    mean2 = np.nanmean(mat2, axis=0)
    log2fc = np.array([_safe_log2fc(mean1[i], mean2[i]) for i in range(p)])

    # ---- 显著性标注 ----
    sig_pv = qvalues if use_fdr else pvalues
    is_sig = (~np.isnan(sig_pv)) & (sig_pv < pvalue_threshold) & (np.abs(log2fc) >= fc_threshold)
    labels = np.where(
        is_sig & (log2fc > 0), "up",
        np.where(is_sig & (log2fc < 0), "down", "ns")
    )

    # ---- 构造结果列表 ----
    features: List[Dict[str, Any]] = []
    for i, fname in enumerate(feature_names):
        features.append({
            "feature": fname,
            "mean_group1": _f(mean1[i]),
            "mean_group2": _f(mean2[i]),
            "log2fc": _f(log2fc[i]),
            "tstat": _f(tstats[i]),
            "pvalue": _f(pvalues[i]),
            "qvalue": _f(qvalues[i]),
            "neg_log10_pvalue": _f(-np.log10(pvalues[i])) if (not np.isnan(pvalues[i]) and pvalues[i] > 0) else None,
            "neg_log10_qvalue": _f(-np.log10(qvalues[i])) if (not np.isnan(qvalues[i]) and qvalues[i] > 0) else None,
            "label": labels[i],
        })

    n_sig_up = int((labels == "up").sum())
    n_sig_down = int((labels == "down").sum())

    elapsed = round(time.time() - t0, 3)
    logger.info(
        "差异分析完成：%s vs %s，共 %d 特征，显著上调 %d，显著下调 %d，耗时 %.2f s",
        group1, group2, p, n_sig_up, n_sig_down, elapsed,
    )

    return {
        "group1": group1,
        "group2": group2,
        "n_group1": int(len(idx1)),
        "n_group2": int(len(idx2)),
        "n_features": p,
        "fc_threshold": fc_threshold,
        "pvalue_threshold": pvalue_threshold,
        "use_fdr": use_fdr,
        "equal_var": equal_var,
        "elapsed_seconds": elapsed,
        "features": features,
        "summary": {
            "n_total": p,
            "n_sig_up": n_sig_up,
            "n_sig_down": n_sig_down,
            "n_sig": n_sig_up + n_sig_down,
            "n_ns": p - n_sig_up - n_sig_down,
        },
    }


def _f(v: Any) -> Optional[float]:
    """将 numpy scalar 转 Python float，NaN → None（JSON 友好）。"""
    if v is None:
        return None
    try:
        fv = float(v)
        return None if np.isnan(fv) or np.isinf(fv) else fv
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Pipeline 级别入口（读文件 → 分析 → 写输出）
# --------------------------------------------------------------------------- #

def run_differential_analysis_for_benchmark(
    benchmark_merged_dir: Path,
    pipeline_dir: Path,
    group1: str,
    group2: str,
    matrix_filename: str = "batch_corrected_sample_by_feature.csv",
    fc_threshold: float = 1.0,
    pvalue_threshold: float = 0.05,
    use_fdr: bool = True,
) -> Dict[str, Any]:
    """
    从 benchmark merged pipeline 产物中读取矩阵，对 group1 vs group2 做差异分析，
    结果中自动注入代谢物注释（名称、HMDB/KEGG 链接），
    最终写入 pipeline_dir/diff_analysis/ 目录。
    """
    matrix_path = pipeline_dir / matrix_filename
    if not matrix_path.is_file():
        # fallback: 用 imputed 矩阵
        matrix_path = pipeline_dir / "imputed_sample_by_feature.csv"
    if not matrix_path.is_file():
        raise FileNotFoundError(f"找不到输入矩阵: {pipeline_dir / matrix_filename}")

    meta_path = benchmark_merged_dir / "merged_sample_meta.csv"
    if not meta_path.is_file():
        raise FileNotFoundError(f"找不到样本元数据: {meta_path}")

    matrix = pd.read_csv(matrix_path, index_col=0)
    matrix.index = matrix.index.astype(str)

    # ---- 矩阵完整性验证 ----
    all_nan_rows = matrix.isna().all(axis=1)
    if all_nan_rows.any():
        logger.warning("矩阵中存在 %d 行全为 NaN，已自动过滤（sample_id: %s...）",
                       all_nan_rows.sum(), list(matrix.index[all_nan_rows])[:3])
        matrix = matrix.loc[~all_nan_rows]
    all_nan_cols = matrix.isna().all(axis=0)
    if all_nan_cols.any():
        logger.warning("矩阵中存在 %d 列全为 NaN，已自动过滤", all_nan_cols.sum())
        matrix = matrix.loc[:, ~all_nan_cols]
    if matrix.empty:
        raise ValueError("过滤全 NaN 行/列后矩阵为空，请检查输入文件。")

    sample_meta = pd.read_csv(meta_path)

    result = run_differential_analysis(
        matrix=matrix,
        sample_meta=sample_meta,
        group1=group1,
        group2=group2,
        fc_threshold=fc_threshold,
        pvalue_threshold=pvalue_threshold,
        use_fdr=use_fdr,
    )
    result["input_matrix"] = str(matrix_path)

    # ---- 注入代谢物注释 ----
    try:
        from app.services.annotation_service import build_annotation_lookup
        lookup = build_annotation_lookup(pipeline_dir)
        if lookup:
            for feat in result.get("features", []):
                ann = lookup.get(str(feat["feature"]))
                if ann:
                    feat["metabolite_name"] = ann.get("metabolite_name")
                    feat["formula"] = ann.get("formula")
                    feat["hmdb_ids"] = ann.get("hmdb_ids") or []
                    feat["kegg_ids"] = ann.get("kegg_ids") or []
                    feat["hmdb_url"] = ann.get("hmdb_url")
                    feat["kegg_url"] = ann.get("kegg_url")
                    feat["ion_mz"] = ann.get("ion_mz")
                else:
                    feat["metabolite_name"] = None
                    feat["formula"] = None
                    feat["hmdb_ids"] = []
                    feat["kegg_ids"] = []
                    feat["hmdb_url"] = None
                    feat["kegg_url"] = None
                    feat["ion_mz"] = None
            result["annotation_injected"] = True
            logger.info("差异分析结果已注入代谢物注释（%d 条 lookup）", len(lookup))
    except Exception as ann_err:
        logger.warning("代谢物注释注入失败（不影响差异分析主结果）: %s", ann_err)
        result["annotation_injected"] = False

    # ---- 写输出 ----
    out_dir = pipeline_dir / "diff_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_g1 = group1.replace("/", "_").replace(" ", "_")
    safe_g2 = group2.replace("/", "_").replace(" ", "_")
    out_name = f"diff_{safe_g1}_vs_{safe_g2}.json"
    out_path = out_dir / out_name

    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)

    logger.info("差异分析结果已写入: %s", out_path)
    return result


def run_differential_analysis_for_dataset(
    dataset_dir: Path,
    pipeline_dir: Path,
    group1: str,
    group2: str,
    fc_threshold: float = 1.0,
    pvalue_threshold: float = 0.05,
    use_fdr: bool = True,
) -> Dict[str, Any]:
    """
    通用数据集差异分析入口（amide / bioheart / mi）。
    从 dataset_dir/merged_sample_meta.csv 和
       pipeline_dir/batch_corrected_sample_by_feature.csv 读取数据，
    对 group1 vs group2 做差异分析，结果写入 pipeline_dir/diff_analysis/。
    """
    import re

    # ---- 缓存路径 ----
    out_dir = pipeline_dir / "diff_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_g1 = re.sub(r"[^\w\-]", "_", group1)
    safe_g2 = re.sub(r"[^\w\-]", "_", group2)
    cache_path = out_dir / f"diff_{safe_g1}_vs_{safe_g2}.json"

    # 读缓存
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

    # ---- 读取矩阵 ----
    matrix_path = pipeline_dir / "batch_corrected_sample_by_feature.csv"
    if not matrix_path.is_file():
        raise FileNotFoundError(f"找不到批次校正矩阵: {matrix_path}")

    meta_path = dataset_dir / "merged_sample_meta.csv"
    if not meta_path.is_file():
        raise FileNotFoundError(f"找不到样本元数据: {meta_path}")

    matrix = pd.read_csv(matrix_path, index_col=0)
    matrix.index = matrix.index.astype(str)

    # 矩阵完整性过滤
    all_nan_rows = matrix.isna().all(axis=1)
    if all_nan_rows.any():
        matrix = matrix.loc[~all_nan_rows]
    all_nan_cols = matrix.isna().all(axis=0)
    if all_nan_cols.any():
        matrix = matrix.loc[:, ~all_nan_cols]
    if matrix.empty:
        raise ValueError("过滤全 NaN 行/列后矩阵为空，请检查输入文件。")

    sample_meta = pd.read_csv(meta_path)

    result = run_differential_analysis(
        matrix=matrix,
        sample_meta=sample_meta,
        group1=group1,
        group2=group2,
        fc_threshold=fc_threshold,
        pvalue_threshold=pvalue_threshold,
        use_fdr=use_fdr,
    )
    result["input_matrix"] = str(matrix_path)

    # 写缓存
    with cache_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)

    logger.info("通用数据集差异分析完成并写入: %s", cache_path)
    return result
