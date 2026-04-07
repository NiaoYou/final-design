from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from app.algorithms.batch_correction.combat import run_combat_safe
from app.core.config import Settings
from app.services.baseline_batch_correction_merged import run_baseline_batch_correction_merged_pipeline
from app.services.batch_service import run_batch_correction_matrix
from app.services.benchmark_cross_batch_merge import merge_benchmark_batches
from app.services.evaluation_service import (
    run_cross_batch_pre_correction_evaluation,
    run_evaluation_matrix,
    run_preprocess_method_comparison_evaluation,
)
from app.services.imputation_eval_service import run_imputation_mask_evaluation
from app.services.imputation_service import run_imputation_matrix
from app.services.preprocess_service import run_preprocess_matrix


def _read_merged(processed_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    d = processed_root / "benchmark_merged"
    xf = pd.read_csv(d / "merged_sample_by_feature.csv", index_col=0)
    sm = pd.read_csv(d / "merged_sample_meta.csv")
    fm = pd.read_csv(d / "merged_feature_meta.csv")
    xf.index = xf.index.astype(str)
    return fm, sm, xf


def _get_batch_labels(sample_meta: pd.DataFrame, matrix: pd.DataFrame) -> np.ndarray:
    """从 sample_meta 对齐并提取 batch_id 数组（与 matrix 行顺序一致）。"""
    if "merged_sample_id" in sample_meta.columns:
        meta = sample_meta.set_index("merged_sample_id").loc[matrix.index.astype(str)]
    elif "sample_col_name" in sample_meta.columns:
        meta = sample_meta.set_index("sample_col_name").loc[matrix.index]
    else:
        meta = sample_meta
    return meta["batch_id"].astype(str).to_numpy()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Merge Batch1~Batch7 then run preprocess/impute/batch-correct/evaluation"
    )
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
    p.add_argument("--batch-method", type=str, default="combat", choices=["combat", "baseline"])
    p.add_argument("--combat-parametric", dest="combat_parametric", action="store_true", default=True)
    p.add_argument("--combat-non-parametric", dest="combat_parametric", action="store_false")
    p.add_argument("--pca-components", type=int, default=2)
    # 缺失值填充评估参数
    p.add_argument("--skip-imputation-eval", action="store_true", help="跳过 Mask-then-Impute 填充评估（数据量大时可节省时间）")
    p.add_argument("--imputation-eval-mask-ratio", type=float, default=0.15)
    p.add_argument("--imputation-eval-repeats", type=int, default=3)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    processed_root = Path(args.processed_root)

    # ---- 1. 合并多批次数据 ----
    if not args.skip_merge:
        merge_benchmark_batches(
            processed_root,
            merge_strategy=args.merge_strategy,  # type: ignore[arg-type]
            out_dir_name="benchmark_merged",
        )

    feature_meta, sample_meta, sample_by_feature = _read_merged(processed_root)
    pipeline_dir = processed_root / "benchmark_merged" / "_pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    # ---- 2. 预处理 ----
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

    # ---- 3. 主链路缺失值填充 ----
    imputation_out = run_imputation_matrix(
        matrix=preprocessed,
        config={"method": args.imputation_method, "knn_k": args.knn_k},
        output_dir=pipeline_dir,
    )

    imputed = pd.read_csv(Path(imputation_out["imputed_matrix_path"]), index_col=0)
    imputed.index = imputed.index.astype(str)

    # ---- 4. 多种填充方法（用于评估对比）----
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

    # ---- 5. 批次校正（主链路）----
    batch_out = run_batch_correction_matrix(
        matrix=imputed,
        sample_meta=sample_meta,
        config={
            "method": args.batch_method,
            "batch_id_field": "batch_id",
            "parametric": args.combat_parametric,
        },
        output_dir=pipeline_dir,
    )

    print(f"  batch_correct status: {batch_out.get('status')}")
    print(f"  batch_correct reason: {batch_out.get('reason')}")

    # ---- 6. ComBat 校正（用于评估对比，即使主链路选了 baseline 也运行） ----
    batch_labels = _get_batch_labels(sample_meta, imputed)
    combat_df, combat_err = run_combat_safe(
        imputed, batch_labels, parametric=args.combat_parametric
    )
    combat_status: Dict[str, Any] = {}
    if combat_df is None:
        print(f"  [WARNING] ComBat 对比组失败: {combat_err}")
        combat_status = {"available": False, "error": combat_err}
    else:
        combat_path = pipeline_dir / "_combat_corrected_sample_by_feature.csv"
        combat_df.to_csv(combat_path, index=True)
        combat_status = {
            "available": True,
            "path": str(combat_path),
            "parametric": args.combat_parametric,
        }
        print(f"  ComBat 对比组: 成功，保存至 {combat_path}")

    # ---- 7. Baseline 批次校正（产出主要报告/PCA 图）----
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

    # ---- 8. 统一多方法对比评估 ----
    baseline_matrix_path = pipeline_dir / "batch_corrected_sample_by_feature.csv"
    baseline_df = pd.read_csv(baseline_matrix_path, index_col=0)
    baseline_df.index = baseline_df.index.astype(str)

    matrices_by_method: dict[str, pd.DataFrame] = {
        "mean": imputed_by_method["mean"],
        "median": imputed_by_method["median"],
        "knn": imputed_by_method["knn"],
        "baseline": baseline_df,
    }

    # 若 ComBat 成功，加入对比
    if combat_df is not None:
        matrices_by_method["combat"] = combat_df

    # 确定对比图的 before/after
    before_method = (
        str(args.imputation_method).lower()
        if str(args.imputation_method).lower() in {"mean", "median", "knn"}
        else "knn"
    )
    after_method = "combat" if combat_df is not None else "baseline"

    evaluation_compare_out = run_preprocess_method_comparison_evaluation(
        matrices_by_method=matrices_by_method,
        sample_meta=sample_meta,
        output_dir=pipeline_dir / "evaluation",
        n_components=2,
        before_method=before_method,
        after_method=after_method,
    )

    # ---- 9. 缺失值填充 Mask-then-Impute 评估 ----
    imputation_eval_out: Dict[str, Any] = {}
    if not args.skip_imputation_eval:
        print("\n运行缺失值填充评估（Mask-then-Impute）...")
        try:
            imputation_eval_out = run_imputation_mask_evaluation(
                matrix=imputed,           # 使用主链路填充后矩阵（无 NaN）作为基准
                mask_ratio=args.imputation_eval_mask_ratio,
                knn_k=args.knn_k,
                n_repeats=args.imputation_eval_repeats,
                output_dir=pipeline_dir / "imputation_eval",
            )
            print(f"  填充评估完成 — 最优方法: {imputation_eval_out.get('best_method')}")
            for m, stats in (imputation_eval_out.get("summary") or {}).items():
                print(f"    {m:8s}: RMSE={stats['rmse_mean']:.4f} ± {stats['rmse_std']:.4f}"
                      f"  MAE={stats['mae_mean']:.4f}  NRMSE={stats['nrmse_mean']:.4f}")
        except Exception as e:
            print(f"  [WARNING] 填充评估失败: {e}")
            imputation_eval_out = {"error": str(e)}
    else:
        print("  跳过填充评估（--skip-imputation-eval）")

    # ---- 10. 写汇总报告 ----
    report: Dict[str, Any] = {
        "merge_strategy": args.merge_strategy,
        "preprocess_out": preprocess_out,
        "imputation_out": imputation_out,
        "imputation_variants_note": (
            "为方法对比评估额外生成 mean/median/knn 的填充结果，"
            "写入 _pipeline/_imputation_{method}/ 子目录；主链路仍使用 imputed_sample_by_feature.csv。"
        ),
        "batch_correction_main_out": batch_out,
        "combat_comparison_status": combat_status,
        "evaluation_out": eval_out,
        "pre_correction_evaluation_out": pre_eval_out,
        "baseline_batch_correction_out": baseline_out,
        "evaluation_compare_out": evaluation_compare_out,
        "methods_in_comparison": list(matrices_by_method.keys()),
        "combat_available_in_comparison": combat_df is not None,
        "imputation_eval_out": imputation_eval_out,
    }
    mr_path = processed_root / "benchmark_merged" / "merge_report.json"
    if mr_path.is_file():
        report["merge_report_path"] = str(mr_path)

    with (pipeline_dir / "merged_pipeline_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nOK: benchmark_merged pipeline finished.")
    print(f"  merged dir : {processed_root / 'benchmark_merged'}")
    print(f"  pipeline dir: {pipeline_dir}")
    print(f"  methods in comparison: {list(matrices_by_method.keys())}")
    print(f"  combat in comparison : {combat_df is not None}")


if __name__ == "__main__":
    main()
