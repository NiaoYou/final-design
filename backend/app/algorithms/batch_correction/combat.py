"""
ComBat batch effect correction (empirical Bayes).

依赖：neuroCombat（pip install neuroCombat）
    - Python 实现：https://github.com/Jfortin1/neuroCombat_python
    - 算法参考：Johnson et al., 2007, Biostatistics

接口说明
---------
- 输入 matrix: sample × feature DataFrame（行=样本，列=特征）
- 输入 batch_labels: 与 matrix 行对齐的 batch 标签序列
- 可选 covariate_df: 生物学协变量 DataFrame（sample × cov），用于保护生物学信号
- 输出: ComBat 校正后的 sample × feature DataFrame，与输入形状相同

注意
-----
- neuroCombat 内部以 feature × sample 处理，本模块自动完成转置
- 每个 batch 内样本数需 ≥ 2（否则 neuroCombat 会报错）
- 若 neuroCombat 未安装，抛出 ImportError 并给出安装提示
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def run_combat(
    matrix: pd.DataFrame,
    batch_labels: "np.ndarray | pd.Series | list",
    *,
    covariate_df: Optional[pd.DataFrame] = None,
    parametric: bool = True,
    ref_batch: Optional[str] = None,
) -> pd.DataFrame:
    """
    使用 neuroCombat（经验 Bayes ComBat）对 sample × feature 矩阵执行批次校正。

    Parameters
    ----------
    matrix : pd.DataFrame
        sample × feature，行为样本、列为代谢特征。
        数值应已完成缺失值填充（ComBat 不支持 NaN）。
    batch_labels : array-like
        与 matrix 行一一对应的批次标签（字符串或整数均可）。
    covariate_df : pd.DataFrame, optional
        生物学协变量矩阵（sample × cov），用于在 ComBat 中保护生物学变量。
        列名将作为 continuous_cols 传入，保护这些变量的效应不被移除。
        若为 None，则不添加协变量。
    parametric : bool
        True（默认）= 参数 ComBat（高斯先验，更快）；
        False = 非参数 ComBat（适用于非高斯数据，较慢）。
    ref_batch : str, optional
        参考 batch 名称。若设置，则将其他 batch 校正到该 batch 的分布。

    Returns
    -------
    pd.DataFrame
        ComBat 校正后的 sample × feature DataFrame，与 matrix 形状相同。

    Raises
    ------
    ImportError
        若 neuroCombat 未安装。
    ValueError
        若输入维度不合法或批次数 < 2。
    """
    try:
        from neuroCombat import neuroCombat  # type: ignore[import]
    except ImportError as e:
        raise ImportError(
            "ComBat 校正依赖 neuroCombat 库，请先安装：pip install neuroCombat"
        ) from e

    # ---- 输入校验 ----
    batch_arr = np.asarray(batch_labels).astype(str)
    if len(batch_arr) != matrix.shape[0]:
        raise ValueError(
            f"batch_labels 长度 ({len(batch_arr)}) 与 matrix 行数 ({matrix.shape[0]}) 不一致。"
        )

    unique_batches = np.unique(batch_arr)
    if unique_batches.size < 2:
        raise ValueError(
            f"ComBat 需要至少 2 个不同 batch，当前只有 {unique_batches.size} 个。"
        )

    # 校验每 batch 样本数
    for b in unique_batches:
        cnt = int((batch_arr == b).sum())
        if cnt < 2:
            raise ValueError(
                f"Batch '{b}' 只有 {cnt} 个样本，ComBat 要求每 batch ≥ 2 个样本。"
            )

    # ---- 数据准备 ----
    X = matrix.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if np.isnan(X).any():
        raise ValueError(
            "ComBat 不支持 NaN 值，请先执行缺失值填充（imputation）后再运行 ComBat。"
        )

    # neuroCombat 要求 dat: feature × sample
    sample_ids = matrix.index.astype(str).tolist()
    feature_ids = matrix.columns.astype(str).tolist()

    dat_fs = pd.DataFrame(
        X.T,
        index=feature_ids,
        columns=sample_ids,
    )

    # ---- 构造 covars DataFrame ----
    # neuroCombat 的 covars: 行=sample，列=协变量（含 batch）
    covars = pd.DataFrame({"batch": batch_arr}, index=sample_ids)

    continuous_cols: list[str] = []
    categorical_cols: list[str] = []

    if covariate_df is not None:
        cov = covariate_df.copy()
        cov.index = cov.index.astype(str)
        cov_aligned = cov.loc[sample_ids]
        for col in cov_aligned.columns:
            covars[str(col)] = cov_aligned[col].values
            continuous_cols.append(str(col))

    # ---- 运行 neuroCombat ----
    kwargs: dict = {
        "dat": dat_fs,
        "covars": covars,
        "batch_col": "batch",
        "parametric": parametric,
    }
    if continuous_cols:
        kwargs["continuous_cols"] = continuous_cols
    if categorical_cols:
        kwargs["categorical_cols"] = categorical_cols
    if ref_batch is not None:
        kwargs["ref_batch"] = ref_batch

    result = neuroCombat(**kwargs)

    # result["data"]: numpy array, feature × sample
    corrected_fs: np.ndarray = result["data"]

    # 转回 sample × feature，恢复原始 index/columns
    corrected_sf = pd.DataFrame(
        corrected_fs.T,
        index=matrix.index,
        columns=matrix.columns,
    )

    return corrected_sf


def run_combat_safe(
    matrix: pd.DataFrame,
    batch_labels: "np.ndarray | pd.Series | list",
    *,
    covariate_df: Optional[pd.DataFrame] = None,
    parametric: bool = True,
    ref_batch: Optional[str] = None,
) -> tuple[pd.DataFrame | None, str]:
    """
    run_combat 的安全封装版：捕获所有异常，返回 (corrected_df, error_msg)。
    若成功则 error_msg 为空字符串；若失败则 corrected_df 为 None。

    用于 pipeline 中即使 ComBat 失败也不中断整体流程。
    """
    try:
        result = run_combat(
            matrix,
            batch_labels,
            covariate_df=covariate_df,
            parametric=parametric,
            ref_batch=ref_batch,
        )
        return result, ""
    except ImportError as e:
        return None, f"[ComBat] 依赖缺失: {e}"
    except ValueError as e:
        return None, f"[ComBat] 参数错误: {e}"
    except Exception as e:  # noqa: BLE001
        return None, f"[ComBat] 运行时错误: {e}"
