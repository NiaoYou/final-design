from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd


def read_long_dataframe(file_path: str, data_format: str = "long") -> pd.DataFrame:
    """
    目前 MVP 只完整支持 long format。
    文件后缀自动判断：
    - .csv => read_csv
    - .xlsx/.xls => read_excel
    """

    p = Path(file_path)
    if data_format != "long":
        raise ValueError("MVP 目前仅支持 long format（后续可扩展 matrix format）。")

    if p.suffix.lower() == ".csv":
        return pd.read_csv(p)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    raise ValueError(f"不支持的文件类型: {p.suffix}")


def to_feature_sample_matrix(
    df_long: pd.DataFrame,
    feature_column: str,
    sample_column: str,
    value_column: str,
) -> Tuple[pd.DataFrame, list[str]]:
    """
    返回：
    - matrix: 行=feature，列=sample
    - feature_names: feature 列表（与 matrix.index 对齐）
    """

    # 同一 feature/sample 可能存在多行，取均值聚合
    matrix = (
        df_long.pivot_table(
            index=feature_column,
            columns=sample_column,
            values=value_column,
            aggfunc="mean",
        )
        .astype(float)
    )
    feature_names = matrix.index.tolist()
    return matrix, feature_names


def extract_sample_metadata(
    df_long: pd.DataFrame,
    sample_column: str,
    batch_column: str,
    group_column: str,
    matrix_columns: list[Any],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    基于 long 表提取样本维度的 batch/group，并与 matrix 的列顺序对齐。
    """

    meta = df_long[[sample_column, batch_column, group_column]].drop_duplicates(subset=[sample_column])
    meta = meta.set_index(sample_column)
    meta = meta.loc[matrix_columns]

    batch = meta[batch_column].to_numpy()
    group = meta[group_column].to_numpy()
    return batch, group


def df_to_preview_records(df: pd.DataFrame, limit: int = 20) -> list[Dict[str, Any]]:
    return df.head(limit).to_dict(orient="records")

