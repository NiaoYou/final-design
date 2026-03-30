from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from app.core.config import Settings
from app.services.baseline_batch_correction_merged import run_baseline_batch_correction_merged_pipeline
from app.services.batch_service import run_batch_correction_matrix
from app.services.benchmark_cross_batch_merge import merge_benchmark_batches
from app.services.evaluation_service import (
    run_cross_batch_pre_correction_evaluation,
    run_evaluation_matrix,
    run_preprocess_method_comparison_evaluation,
)
from app.services.imputation_service import run_imputation_matrix
from app.services.preprocess_service import run_preprocess_matrix


def _read_merged(processed_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    d = processed_root / "benchmark_merged"
    xf = pd.read_csv(d / "merged_sample_by_feature.csv", index_col=0)
    sm = pd.read_csv(d / "merged_sample_meta.csv")
    fm = pd.read_csv(d / "merged_feature_meta.csv")
    xf.index = xf.index.astype(str)
    return fm, sm, xf


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge Batch1~Batch7 then run preprocess/impute/batch-correct/evaluation")
    p.add_argument("--processed-root", type=str, default=str(Settings.PROCESSED_DIR))
    p.add_argument("--merge-strategy", type=str, default="inner", choices=["inner", "outer"])
    p.add_argument("--skip-merge", action="store_true", help="若 benchmark_merged 已存在且不需重新合并")
    p.add_argument("--normalization", type=str, default="standardize")
    p.add_argument("--log-transform", dest="log_transform", action="store_true")
    p.add_argument("--no-log-transform", dest="log_transform", action="store_false")
    p.set_defaults(log_transform=False)
    p.add_argument("--max-feature-missing-rate", type=float, default=0.5)
    p.add_argument("--imputation-method", type=str, default="knn", choices=["mean", "median", "knn"])
    p.add_argument("--knn-k", type=int, default=5)
    p.add_argument("--batch-method", type=str, default="combat")
    p.add_argument("--pca-components", type=int, default=2)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    processed_root = Path(args.processed_root)

    if not args.skip_merge:
        merge_benchmark_batches(
            processed_root,
            merge_strategy=args.merge_strategy,  # type: ignore[arg-type]
            out_dir_name="benchmark_merged",
        )

    feature_meta, sample_meta, sample_by_feature = _read_merged(processed_root)
    pipeline_dir = processed_root / "benchmark_merged" / "_pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    preprocess_out = run_preprocess_matrix(
        sample_by_feature=sample_by_feature,
        sample_meta=sample_meta,
        feature_meta=feature_meta,
        config={
            "normalization": args.normalization,
            "log_transform": args.log_transform,
            "max_feature_missing_rate": args.max_feature_missing_rate,
        },
        output_dir=pipeline_dir,
    )

    preprocessed = pd.read_csv(Path(preprocess_out["preprocessed_matrix_path"]), index_col=0)
    preprocessed.index = preprocessed.index.astype(str)

    # 主链路保持不动：仍按命令行指定 method 写入 pipeline_dir/imputed_sample_by_feature.csv
    imputation_out = run_imputation_matrix(
        matrix=preprocessed,
        config={"method": args.imputation_method, "knn_k": args.knn_k},
        output_dir=pipeline_dir,
    )

    imputed = pd.read_csv(Path(imputation_out["imputed_matrix_path"]), index_col=0)
    imputed.index = imputed.index.astype(str)

    # 仅用于“方法对比评估”的 combat-like 校正（不影响 baseline 逻辑，也不改主链路产物）
    # 说明：这里是“按 batch 做 per-feature 位置-尺度对齐到全局”的简化实现，用于对比评估；
    # 严格 ComBat（经验 Bayes 语义）仍未在本仓库实现。
    def _combat_like_sample_by_feature(X_df: pd.DataFrame, sm: pd.DataFrame) -> pd.DataFrame:
        if "merged_sample_id" not in sm.columns or "batch_id" not in sm.columns:
            raise ValueError("combat-like: sample_meta 需要 merged_sample_id 与 batch_id")
        meta = sm.set_index("merged_sample_id").loc[X_df.index.astype(str)]
        batch = meta["batch_id"].astype(str).to_numpy()

        X = X_df.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        X = np.nan_to_num(X, nan=0.0)

        overall_mean = np.mean(X, axis=0, keepdims=True)
        overall_std = np.std(X, axis=0, keepdims=True, ddof=0)
        overall_std = np.where(overall_std == 0, 1.0, overall_std)

        corrected = X.copy()
        for b in np.unique(batch):
            idx = batch == b
            if idx.sum() == 0:
                continue
            bm = np.mean(X[idx, :], axis=0, keepdims=True)
            bs = np.std(X[idx, :], axis=0, keepdims=True, ddof=0)
            bs = np.where(bs == 0, 1.0, bs)
            corrected[idx, :] = (X[idx, :] - bm) / bs * overall_std + overall_mean

        return pd.DataFrame(corrected, index=X_df.index, columns=X_df.columns)

    combat_df = _combat_like_sample_by_feature(imputed, sample_meta)

    # 评估模块需要 mean/median/knn/baseline 四种方法统一对比：
    # - mean/median/knn：对同一 preprocessed 矩阵分别填充（写入各自子目录，避免覆盖主链路产物）
    # - baseline：使用 merged baseline 批次校正产物 batch_corrected_sample_by_feature.csv（由下方 baseline pipeline 生成）
    imputed_by_method: dict[str, pd.DataFrame] = {}
    impute_methods = ["mean", "median", "knn"]
    for m in impute_methods:
        out_dir = pipeline_dir / f"_imputation_{m}"
        out = run_imputation_matrix(
            matrix=preprocessed,
            config={"method": m, "knn_k": args.knn_k},
            output_dir=out_dir,
        )
        mat = pd.read_csv(Path(out["imputed_matrix_path"]), index_col=0)
        mat.index = mat.index.astype(str)
        imputed_by_method[m] = mat

    batch_out = run_batch_correction_matrix(
        matrix=imputed,
        sample_meta=sample_meta,
        config={"method": args.batch_method, "batch_id_field": "batch_id"},
        output_dir=pipeline_dir,
    )

    eval_out = run_evaluation_matrix(
        matrix_before=imputed,
        matrix_after=None,
        sample_meta=sample_meta,
        config={"n_components": args.pca_components, "color_by": "group_label"},
        output_dir=pipeline_dir,
    )

    pre_eval_out = run_cross_batch_pre_correction_evaluation(
        matrix=imputed,
        sample_meta=sample_meta,
        output_dir=pipeline_dir,
        n_components=args.pca_components,
    )

    baseline_out = run_baseline_batch_correction_merged_pipeline(
        benchmark_merged_dir=processed_root / "benchmark_merged",
        pipeline_dir=pipeline_dir,
        n_pca_components=args.pca_components,
        input_matrix_filename="imputed_sample_by_feature.csv",
    )

    # 统一评估：将 mean/median/knn/baseline 组织为 matrices_by_method 并输出到 _pipeline/evaluation/
    baseline_matrix_path = pipeline_dir / "batch_corrected_sample_by_feature.csv"
    baseline_df = pd.read_csv(baseline_matrix_path, index_col=0)
    baseline_df.index = baseline_df.index.astype(str)

    matrices_by_method: dict[str, pd.DataFrame] = {
        "mean": imputed_by_method["mean"],
        "median": imputed_by_method["median"],
        "knn": imputed_by_method["knn"],
        "combat": combat_df,
        "baseline": baseline_df,
    }
    evaluation_compare_out = run_preprocess_method_comparison_evaluation(
        matrices_by_method=matrices_by_method,
        sample_meta=sample_meta,
        output_dir=pipeline_dir / "evaluation",
        n_components=2,
        before_method=str(args.imputation_method).lower() if str(args.imputation_method).lower() in {"mean", "median", "knn"} else "knn",
        after_method="baseline",
    )

    report: Dict[str, Any] = {
        "merge_strategy": args.merge_strategy,
        "preprocess_out": preprocess_out,
        "imputation_out": imputation_out,
        "imputation_variants_note": "为方法对比评估额外生成 mean/median/knn 的填充结果，写入 _pipeline/_imputation_{method}/ 子目录；主链路仍使用 imputed_sample_by_feature.csv。",
        "batch_correction_out": batch_out,
        "evaluation_out": eval_out,
        "pre_correction_evaluation_out": pre_eval_out,
        "baseline_batch_correction_out": baseline_out,
        "evaluation_compare_out": evaluation_compare_out,
    }
    mr_path = processed_root / "benchmark_merged" / "merge_report.json"
    if mr_path.is_file():
        report["merge_report_path"] = str(mr_path)
    with (pipeline_dir / "merged_pipeline_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("OK: benchmark_merged pipeline finished.")
    print(f"  merged dir: {processed_root / 'benchmark_merged'}")
    print(f"  pipeline dir: {pipeline_dir}")
    print(f"  batch_correct status: {batch_out.get('status')}")
    print(f"  strict_combat_implemented: {batch_out.get('strict_combat_implemented')}")


if __name__ == "__main__":
    main()
