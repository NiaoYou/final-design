from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd

MergeStrategy = Literal["inner", "outer"]


DEFAULT_BATCH_DIRS: List[str] = [
    "Batch1_0108 DATA",
    "Batch2_0110 DATA",
    "Batch3_0124 DATA",
    "Batch4_0219 DATA",
    "Batch5_0221 DATA",
    "Batch6_0304 DATA",
    "Batch7_0306 DATA",
]


def _read_sample_by_feature(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0)


def _ion_idx_series(feature_meta: pd.DataFrame) -> pd.Series:
    s = pd.to_numeric(feature_meta["ionIdx"], errors="coerce")
    if s.isna().any():
        raise ValueError("feature_meta.ionIdx 存在无法解析为数值的行。")
    return s.astype(int)


def _build_ion_to_col(feature_meta: pd.DataFrame) -> Dict[int, str]:
    ions = _ion_idx_series(feature_meta)
    cols = feature_meta["feature_col_name"].astype(str)
    return dict(zip(ions.tolist(), cols.tolist()))


def merge_benchmark_batches(
    processed_root: Path,
    batch_dir_names: Optional[List[str]] = None,
    *,
    merge_strategy: MergeStrategy = "inner",
    feature_alignment_key: str = "ionIdx",
    out_dir_name: str = "benchmark_merged",
) -> Dict[str, Any]:
    """
    跨 Batch 合并 processed 目录下的单 batch 结果。

    - feature 对齐：以 ionIdx 为主键；合并策略 inner=全 batch 特征交集，outer=并集（缺失补 NaN）。
    - 样本：行拼接；因不同 batch 可能存在相同 sample_col_name，生成 merged_sample_id = batch_id + \"::\" + sample_col_name。
    - 合并后矩阵列名统一为 str(ionIdx)，与 merged_feature_meta 一致。
    """
    batch_dir_names = batch_dir_names or DEFAULT_BATCH_DIRS
    out_root = processed_root / out_dir_name
    out_root.mkdir(parents=True, exist_ok=True)

    loaded: List[Dict[str, Any]] = []
    per_batch_feature_count: Dict[str, int] = {}
    per_batch_sample_count: Dict[str, int] = {}
    ion_sets: List[set[int]] = []

    for name in batch_dir_names:
        d = processed_root / name
        if not d.is_dir():
            raise FileNotFoundError(f"缺少 batch 目录: {d}")

        fm_path = d / "feature_meta.csv"
        sm_path = d / "sample_meta.csv"
        xf_path = d / "sample_by_feature.csv"
        for p in (fm_path, sm_path, xf_path):
            if not p.is_file():
                raise FileNotFoundError(f"缺少文件: {p}")

        feature_meta = pd.read_csv(fm_path)
        sample_meta = pd.read_csv(sm_path)
        X = _read_sample_by_feature(xf_path)

        if "batch_id" not in sample_meta.columns:
            raise ValueError(f"{name}: sample_meta 缺少 batch_id")

        ions = set(_ion_idx_series(feature_meta).tolist())
        ion_sets.append(ions)
        per_batch_feature_count[name] = len(ions)
        per_batch_sample_count[name] = int(X.shape[0])

        ion_to_col = _build_ion_to_col(feature_meta)
        loaded.append(
            {
                "batch_dir": name,
                "feature_meta": feature_meta,
                "sample_meta": sample_meta,
                "X": X,
                "ion_to_col": ion_to_col,
                "batch_id_values": sample_meta["batch_id"].astype(str).unique().tolist(),
            }
        )

    if merge_strategy == "inner":
        unified_ions = sorted(set.intersection(*ion_sets))
    elif merge_strategy == "outer":
        unified_ions = sorted(set.union(*ion_sets))
    else:
        raise ValueError(f"merge_strategy 必须是 inner 或 outer: {merge_strategy}")

    if len(unified_ions) == 0:
        raise ValueError("合并后特征集合为空，请检查各 batch 的 ionIdx 是否一致或改用 outer。")

    # 参考 ionMz：取第一个 batch 中出现的 ionIdx 对应行；若 outer 某 batch 缺 ion，则在 feature_meta 合并时仍保留 ionIdx 行，ionMz 可能为 NaN
    ref_fm = loaded[0]["feature_meta"].copy()
    ref_fm["_ion"] = _ion_idx_series(ref_fm)
    ref_fm = ref_fm.set_index("_ion").reindex(unified_ions)
    merged_feature_meta = pd.DataFrame(
        {
            "ionIdx": unified_ions,
            "ionMz": ref_fm["ionMz"].values,
            "feature_col_name": [str(i) for i in unified_ions],
        }
    )

    merged_rows: List[pd.DataFrame] = []
    sample_blocks: List[pd.DataFrame] = []

    for item in loaded:
        name = item["batch_dir"]
        X = item["X"]
        sm = item["sample_meta"].copy()
        ion_to_col = item["ion_to_col"]
        # 为每个样本生成全局唯一 ID
        sm["merged_sample_id"] = sm["batch_id"].astype(str) + "::" + sm["sample_col_name"].astype(str)

        mat_cols: Dict[str, np.ndarray] = {}
        for ion in unified_ions:
            col_name = ion_to_col.get(ion)
            if col_name is None or col_name not in X.columns:
                if merge_strategy == "inner":
                    raise RuntimeError(f"inner 策略下不应缺列: batch={name} ionIdx={ion}")
                mat_cols[str(ion)] = np.full(X.shape[0], np.nan, dtype=float)
            else:
                mat_cols[str(ion)] = pd.to_numeric(X[col_name], errors="coerce").to_numpy(dtype=float)

        X_merged = pd.DataFrame(mat_cols, index=sm["merged_sample_id"].astype(str).values)

        merged_rows.append(sm)
        sample_blocks.append(X_merged)

    merged_sample_meta = pd.concat(merged_rows, axis=0, ignore_index=True)
    merged_sample_by_feature = pd.concat(sample_blocks, axis=0)

    # 确保 meta 与矩阵行顺序一致
    merged_sample_by_feature = merged_sample_by_feature.loc[merged_sample_meta["merged_sample_id"].tolist()]

    missing_ratio = float(np.isnan(merged_sample_by_feature.to_numpy(dtype=float)).mean())

    merge_report: Dict[str, Any] = {
        "merged_batch_count": len(batch_dir_names),
        "merged_sample_count": int(merged_sample_by_feature.shape[0]),
        "merged_feature_count": int(merged_sample_by_feature.shape[1]),
        "feature_alignment_key": feature_alignment_key,
        "merge_strategy": merge_strategy,
        "per_batch_sample_count": per_batch_sample_count,
        "per_batch_feature_count": per_batch_feature_count,
        "missing_ratio_after_merge": missing_ratio,
        "batch_id_unique_values": sorted(pd.unique(merged_sample_meta["batch_id"].astype(str)).tolist()),
        "sample_type_counts": merged_sample_meta["sample_type"].value_counts().to_dict(),
        "group_label_counts": merged_sample_meta["group_label"].astype(str).value_counts().to_dict(),
        "notes": [
            f"特征合并策略为 {merge_strategy}：inner 表示所有 batch 在 ionIdx 上的交集；outer 表示并集，缺失处为 NaN。",
            "样本主键使用 merged_sample_id = batch_id + '::' + sample_col_name，避免跨 batch 样本名列冲突。",
        ],
    }

    merged_sample_by_feature.to_csv(out_root / "merged_sample_by_feature.csv", index=True)
    merged_sample_meta.to_csv(out_root / "merged_sample_meta.csv", index=False)
    merged_feature_meta.to_csv(out_root / "merged_feature_meta.csv", index=False)

    with (out_root / "merge_report.json").open("w", encoding="utf-8") as f:
        json.dump(merge_report, f, ensure_ascii=False, indent=2)

    return {
        "output_dir": str(out_root),
        "merge_report": merge_report,
        "merged_sample_by_feature": merged_sample_by_feature,
        "merged_sample_meta": merged_sample_meta,
        "merged_feature_meta": merged_feature_meta,
    }
