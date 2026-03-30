from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.core.config import Settings


REQUIRED_SHEETS = ["injections", "intensities", "ions", "annotation"]


def _normalize_sample_col_name(s: Any) -> str:
    """
    归一化样本列名，尽可能适配 Excel 里“ / ”两侧空格不一致的问题。
    """
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s2 = str(s).replace("\u00A0", " ").strip()  # 去除不换行空格
    # 处理 "A/B" 或 "A / B" 统一为 "A / B"
    if "/" in s2:
        left, right = s2.split("/", 1)
        left = left.strip()
        right = right.strip()
        s2 = f"{left} / {right}"
    # 多空格归一
    s2 = " ".join(s2.split())
    return s2


def _infer_sample_type(label: Any) -> str:
    lab = "" if label is None else str(label)
    lab_l = lab.lower()
    if "burnin" in lab_l:
        return "burnin"
    if "water" in lab_l:
        return "water"
    if "blank" in lab_l:
        return "blank"
    if "srm" in lab_l:
        return "srm"
    if "qc" in lab_l:
        return "qc"
    return "formal_or_unknown"


def scan_benchmark_excels(raw_benchmark_dir: Path) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    xlsx_files = sorted(raw_benchmark_dir.glob("*.xlsx"))
    for f in xlsx_files:
        try:
            xl = pd.ExcelFile(f)
            sheets = xl.sheet_names
            detected = sorted(sheets)
            has_intensities = "intensities" in sheets
            has_injections = "injections" in sheets
            results.append(
                {
                    "file_name": f.name,
                    "detected_sheets": detected,
                    "has_intensities": has_intensities,
                    "has_injections": has_injections,
                    "is_valid": bool(has_intensities and has_injections),
                }
            )
        except Exception as e:
            results.append(
                {
                    "file_name": f.name,
                    "detected_sheets": [],
                    "has_intensities": False,
                    "has_injections": False,
                    "is_valid": False,
                    "error": str(e),
                }
            )
    return results


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    # header=0 默认从第一行做表头
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def parse_benchmark_xlsx(path: Path) -> Dict[str, Any]:
    """
    解析单个 benchmark xlsx，并生成标准输入：
    - feature_meta (DataFrame)
    - sample_meta (DataFrame)
    - sample_by_feature (DataFrame: sample x feature)
    同时生成 ions / annotation 的原始解析结果供解释模块使用（当前只要求保存）。
    """
    xlsx_stem = path.stem

    # 读取 required sheets
    sheets_present: List[str]
    try:
        xl = pd.ExcelFile(path, engine="openpyxl")
        sheets_present = xl.sheet_names
    except Exception:
        sheets_present = []

    missing = [s for s in REQUIRED_SHEETS if s not in sheets_present]
    if missing:
        raise ValueError(f"缺少 required sheet: {missing}. path={path.name}")

    injections_df = _read_sheet(path, "injections")
    intensities_df = _read_sheet(path, "intensities")
    ions_df = _read_sheet(path, "ions")
    annotation_df = _read_sheet(path, "annotation")

    # --- intensities: 前两列 feature meta，后续列为样本强度 ---
    if intensities_df.shape[1] < 3:
        raise ValueError("intensities 列数不足（至少需要前两列 + 1 个样本列）。")

    intensities_cols = [str(c) for c in intensities_df.columns.tolist()]
    # 取前两列，作为 feature_meta 的基础字段
    feat0 = intensities_df.iloc[:, 0]
    feat1 = intensities_df.iloc[:, 1]
    feature_meta = pd.DataFrame(
        {
            "ionIdx": feat0.astype(str).map(lambda x: x.strip()),
            "ionMz": pd.to_numeric(feat1, errors="coerce"),
        }
    )

    # 样本列
    sample_cols_raw = intensities_df.columns.tolist()[2:]
    sample_cols = [_normalize_sample_col_name(c) for c in sample_cols_raw]
    # 若出现空列名，尝试用原始表头字符串替代
    sample_cols = [c if c else _normalize_sample_col_name(rc) for c, rc in zip(sample_cols, sample_cols_raw)]

    intensity_values = intensities_df.iloc[:, 2:].copy()
    # 转数字：非数字将变为 NaN
    for col in intensity_values.columns:
        intensity_values[col] = pd.to_numeric(intensity_values[col], errors="coerce")

    # sample_by_feature: sample x feature
    sample_by_feature = intensity_values.T
    sample_by_feature.index = sample_cols
    # features 列名：使用 ionIdx 并确保唯一
    raw_feature_names = feature_meta["ionIdx"].astype(str).tolist()
    unique_feature_names: List[str] = []
    seen: Dict[str, int] = {}
    for n in raw_feature_names:
        if n not in seen:
            seen[n] = 1
            unique_feature_names.append(n)
        else:
            seen[n] += 1
            unique_feature_names.append(f"{n}_dup{seen[n]}")
    feature_meta["feature_col_name"] = unique_feature_names
    sample_by_feature.columns = unique_feature_names
    sample_by_feature.index.name = "sample_col_name"

    feature_count = int(sample_by_feature.shape[1])
    sample_count = int(sample_by_feature.shape[0])

    # --- injections: 生成 sample_meta，并与 intensities 样本列匹配 ---
    # 允许大小写差异：找出对应列名
    inv_cols = {str(c).strip().upper(): str(c) for c in injections_df.columns.tolist()}

    def _get_col(col_key: str) -> str:
        if col_key in inv_cols:
            return inv_cols[col_key]
        raise ValueError(f"injections 缺少列：{col_key}. 实际列：{list(injections_df.columns)}")

    col_index = _get_col("INDEX")
    col_file_name = _get_col("FILE_NAME")
    col_file_code = _get_col("FILE_CODE")
    col_sample_name = _get_col("SAMPLE_NAME")
    col_label = _get_col("LABEL")
    col_sequence = _get_col("SEQUENCE")

    injections_df2 = injections_df.copy()
    # 构造 sample_col_name：INDEX 三位补零 + " / " + LABEL
    def _idx3(v: Any) -> str:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "000"
        try:
            iv = int(v)
            return f"{iv:03d}"
        except Exception:
            return str(v).strip().zfill(3)[-3:]

    injections_df2["sample_col_name"] = [
        _normalize_sample_col_name(f"{_idx3(idx)} / {lab}") for idx, lab in zip(injections_df2[col_index], injections_df2[col_label])
    ]
    injections_df2["sample_type"] = injections_df2[col_label].apply(_infer_sample_type)
    injections_df2["batch_id"] = xlsx_stem  # 先以文件名作为 batch_id
    injections_df2["group_label"] = injections_df2[col_label]  # 预留：先保留 LABEL 原值

    # sample_meta 只取所需字段
    sample_meta = pd.DataFrame(
        {
            "sample_col_name": injections_df2["sample_col_name"],
            "INDEX": injections_df2[col_index].apply(lambda v: int(v) if not (isinstance(v, float) and np.isnan(v)) else None),
            "FILE_NAME": injections_df2[col_file_name],
            "FILE_CODE": injections_df2[col_file_code],
            "SAMPLE_NAME": injections_df2[col_sample_name],
            "LABEL": injections_df2[col_label],
            "SEQUENCE": injections_df2[col_sequence],
            "sample_type": injections_df2["sample_type"],
            "batch_id": injections_df2["batch_id"],
            "group_label": injections_df2["group_label"],
        }
    )

    # 去重：如果 injections 有重复 sample_col_name，保留第一条
    sample_meta = sample_meta.drop_duplicates(subset=["sample_col_name"], keep="first")

    injection_map = dict(zip(sample_meta["sample_col_name"].tolist(), sample_meta.index.tolist()))

    matched_samples = [s for s in sample_by_feature.index.tolist() if s in injection_map]
    unmatched_samples = [s for s in sample_by_feature.index.tolist() if s not in injection_map]

    matched_sample_meta = sample_meta[sample_meta["sample_col_name"].isin(matched_samples)].copy()
    # 调整 sample_by_feature 行顺序以匹配 sample_meta 的 sample_col_name 顺序（与 intensities 相同）
    matched_sample_meta = matched_sample_meta.set_index("sample_col_name").loc[matched_samples].reset_index()
    sample_by_feature_matched = sample_by_feature.loc[matched_samples].copy()
    matched_sample_count = int(len(matched_samples))

    # ions/annotation 保存：当前不做强结构依赖
    data_check_common = {
        "intensities_shape": [int(intensities_df.shape[0]), int(intensities_df.shape[1])],
        "injections_shape": [int(injections_df.shape[0]), int(injections_df.shape[1])],
        "ions_shape": [int(ions_df.shape[0]), int(ions_df.shape[1])],
        "annotation_shape": [int(annotation_df.shape[0]), int(annotation_df.shape[1])],
        "feature_count": feature_count,
        "sample_count": sample_count,
        "matched_sample_count": matched_sample_count,
        "unmatched_sample_columns": unmatched_samples,
        "label_unique_values": sorted(pd.unique(matched_sample_meta["LABEL"].astype(str)).tolist()),
    }

    # missing ratio（在 matched 矩阵上计算）
    if matched_sample_count == 0 or feature_count == 0:
        missing_value_ratio = None
    else:
        mat = sample_by_feature_matched.to_numpy(dtype=float)
        missing_value_ratio = float(np.isnan(mat).mean())

    sample_type_counts = (
        matched_sample_meta["sample_type"].value_counts().to_dict() if matched_sample_count > 0 else {}
    )

    # can_run 逻辑
    can_run_preprocess = matched_sample_count >= 2 and feature_count >= 1
    can_run_imputation = matched_sample_count >= 1 and feature_count >= 1 and (missing_value_ratio is not None)

    # batch correction：按文件名单 batch => 当前不可用
    can_run_batch_correction = False
    notes: List[str] = []
    if matched_sample_count < 2:
        notes.append("匹配样本数不足（<2），后续统计/分组比较不可靠。")
    if len(unmatched_samples) > 0:
        notes.append(f"存在 {len(unmatched_samples)} 个无法匹配 injections 的样本列（详见 unmatched_sample_columns）。")
    notes.append(
        "batch_id 目前仅用文件名（每个 xlsx 一个 batch），因此单 batch 内无法完成真实批次效应校正。"
    )

    # downstream：需要 formal 样本与可比较的 group
    formal_meta = matched_sample_meta[matched_sample_meta["sample_type"] == "formal_or_unknown"]
    formal_groups = sorted(pd.unique(formal_meta["group_label"].astype(str)).tolist()) if len(formal_meta) else []
    can_run_downstream_analysis = len(formal_groups) >= 2
    if not can_run_downstream_analysis:
        notes.append(
            "downstream 暂不满足条件：formal_or_unknown 样本不足或 group_label 可比较组数 < 2。"
        )

    data_check = {
        "file_name": path.name,
        "detected_sheets": sorted(xl.sheet_names) if sheets_present else [],
        "intensities_shape": data_check_common["intensities_shape"],
        "injections_shape": data_check_common["injections_shape"],
        "ions_shape": data_check_common["ions_shape"],
        "annotation_shape": data_check_common["annotation_shape"],
        "feature_count": data_check_common["feature_count"],
        "sample_count": data_check_common["sample_count"],
        "matched_sample_count": data_check_common["matched_sample_count"],
        "unmatched_sample_columns": data_check_common["unmatched_sample_columns"],
        "label_unique_values": data_check_common["label_unique_values"],
        "sample_type_counts": sample_type_counts,
        "missing_value_ratio": missing_value_ratio,
        "can_run_preprocess": bool(can_run_preprocess),
        "can_run_imputation": bool(can_run_imputation),
        "can_run_batch_correction": bool(can_run_batch_correction),
        "can_run_downstream_analysis": bool(can_run_downstream_analysis),
        "notes": notes,
    }

    # ions/annotation 目前保存原样
    return {
        "dataset_name": xlsx_stem,
        "feature_meta": feature_meta,
        "sample_meta": matched_sample_meta,
        "sample_by_feature": sample_by_feature_matched,
        "ions_df": ions_df,
        "annotation_df": annotation_df,
        "data_check": data_check,
    }


def save_processed_dataset(parsed: Dict[str, Any], processed_root: Path) -> Path:
    dataset_name = parsed["dataset_name"]
    out_dir = processed_root / dataset_name
    out_dir.mkdir(parents=True, exist_ok=True)

    parsed["feature_meta"].to_csv(out_dir / "feature_meta.csv", index=False)
    parsed["sample_meta"].to_csv(out_dir / "sample_meta.csv", index=False)
    parsed["sample_by_feature"].to_csv(out_dir / "sample_by_feature.csv", index=True)
    parsed["ions_df"].to_csv(out_dir / "ions.csv", index=False)
    parsed["annotation_df"].to_csv(out_dir / "annotation.csv", index=False)

    with (out_dir / "data_check.json").open("w", encoding="utf-8") as f:
        json.dump(parsed["data_check"], f, ensure_ascii=False, indent=2)

    return out_dir


def run_benchmark_import(
    raw_benchmark_dir: Path,
    processed_root: Optional[Path] = None,
    target_file_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    processed_root = processed_root or Settings.PROCESSED_DIR

    scan_results = scan_benchmark_excels(raw_benchmark_dir)

    # 只处理指定的原始 7 个 xlsx（其余 xlsx 仅扫描不强制处理）
    if target_file_names is None:
        target_file_names = [
            "Batch1_0108 DATA.xlsx",
            "Batch2_0110 DATA.xlsx",
            "Batch3_0124 DATA.xlsx",
            "Batch4_0219 DATA.xlsx",
            "Batch5_0221 DATA.xlsx",
            "Batch6_0304 DATA.xlsx",
            "Batch7_0306 DATA.xlsx",
        ]

    targets = [n for n in target_file_names if n.lower().endswith(".xlsx")]
    target_set = {n for n in targets}

    scan_map = {r["file_name"]: r for r in scan_results}

    processed_files: List[Dict[str, Any]] = []
    failed_files: List[Dict[str, Any]] = []

    for name in targets:
        xlsx_path = raw_benchmark_dir / name
        if not xlsx_path.exists():
            failed_files.append({"file_name": name, "error": "文件不存在"})
            continue

        is_valid = bool(scan_map.get(name, {}).get("is_valid", False))
        if not is_valid:
            failed_files.append({"file_name": name, "error": "sheet 检查不通过（缺少 intensities 或 injections）"})
            continue

        try:
            parsed = parse_benchmark_xlsx(xlsx_path)
            out_dir = save_processed_dataset(parsed, processed_root=processed_root)
            data_check = parsed["data_check"]
            processed_files.append(
                {
                    "file_name": name,
                    "dataset_name": parsed["dataset_name"],
                    "processed_dir": str(out_dir),
                    "data_check": data_check,
                }
            )
        except Exception as e:
            failed_files.append({"file_name": name, "error": str(e)})

    return {
        "scan_results": scan_results,
        "processed_files": processed_files,
        "failed_files": failed_files,
    }

