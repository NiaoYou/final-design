from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from app.core.config import Settings
from app.services.batch_service import run_batch_correction_matrix
from app.services.evaluation_service import run_evaluation_matrix
from app.services.imputation_service import run_imputation_matrix
from app.services.preprocess_service import run_preprocess_matrix


def _read_matrix_csv(matrix_path: Path) -> pd.DataFrame:
    # sample_by_feature.csv 是 index=True 保存的，index 通常会落到 Unnamed: 0
    return pd.read_csv(matrix_path, index_col=0)


def _load_processed_inputs(dataset_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_meta = pd.read_csv(dataset_dir / "feature_meta.csv")
    sample_meta = pd.read_csv(dataset_dir / "sample_meta.csv")
    sample_by_feature = _read_matrix_csv(dataset_dir / "sample_by_feature.csv")
    # 强制对齐 index 与 sample_col_name
    if "sample_col_name" in sample_meta.columns:
        sample_by_feature = sample_by_feature.loc[sample_meta["sample_col_name"].tolist()]
    return feature_meta, sample_meta, sample_by_feature


def _write_pipeline_report(dataset_dir: Path, report: Dict[str, Any]) -> None:
    pipeline_dir = dataset_dir / "_pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    with (pipeline_dir / "pipeline_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def run_for_dataset(dataset_name: str, processed_root: Path, args: argparse.Namespace) -> Dict[str, Any]:
    dataset_dir = processed_root / dataset_name
    pipeline_dir = dataset_dir / "_pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    feature_meta, sample_meta, sample_by_feature = _load_processed_inputs(dataset_dir)

    preprocess_out = run_preprocess_matrix(
        sample_by_feature=sample_by_feature,
        sample_meta=sample_meta,
        feature_meta=feature_meta,
        config={
            "normalization": args.normalization,
            "log_transform": args.log_transform,
            "max_feature_missing_rate": args.max_feature_missing_rate,
            "sample_type_include": args.sample_type_include,
            "sample_type_exclude": args.sample_type_exclude,
        },
        output_dir=pipeline_dir,
    )

    preprocessed_matrix_path = Path(preprocess_out["preprocessed_matrix_path"])
    preprocessed = pd.read_csv(preprocessed_matrix_path, index_col=0)

    imputation_out = run_imputation_matrix(
        matrix=preprocessed,
        config={
            "method": args.imputation_method,
            "knn_k": args.knn_k,
        },
        output_dir=pipeline_dir,
    )

    imputed_matrix_path = Path(imputation_out["imputed_matrix_path"])
    imputed = pd.read_csv(imputed_matrix_path, index_col=0)

    batch_out = run_batch_correction_matrix(
        matrix=imputed,
        sample_meta=sample_meta,
        config={
            "method": args.batch_method,
            "batch_id_field": "batch_id",
        },
        output_dir=pipeline_dir,
    )

    corrected = None
    corrected_matrix_path = batch_out.get("batch_corrected_matrix_path")
    if corrected_matrix_path:
        corrected = pd.read_csv(Path(corrected_matrix_path), index_col=0)

    evaluation_out = run_evaluation_matrix(
        matrix_before=imputed,
        matrix_after=corrected,
        sample_meta=sample_meta,
        config={
            "n_components": args.pca_components,
            "color_by": args.color_by,
        },
        output_dir=pipeline_dir,
    )

    report = {
        "dataset_name": dataset_name,
        "preprocess_out": preprocess_out,
        "imputation_out": imputation_out,
        "batch_correction_out": batch_out,
        "evaluation_out": evaluation_out,
    }
    _write_pipeline_report(dataset_dir, report)
    return report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run benchmark preprocess/impute/evaluation pipeline")
    p.add_argument("--processed-root", type=str, default=str(Settings.PROCESSED_DIR))
    p.add_argument(
        "--datasets",
        type=str,
        nargs="*",
        default=[
            "Batch1_0108 DATA",
            "Batch2_0110 DATA",
            "Batch3_0124 DATA",
            "Batch4_0219 DATA",
            "Batch5_0221 DATA",
            "Batch6_0304 DATA",
            "Batch7_0306 DATA",
        ],
    )
    p.add_argument("--normalization", type=str, default="standardize")
    p.add_argument("--log-transform", dest="log_transform", action="store_true")
    p.add_argument("--no-log-transform", dest="log_transform", action="store_false")
    p.set_defaults(log_transform=False)
    p.add_argument("--max-feature-missing-rate", type=float, default=0.5)

    p.add_argument("--sample-type-include", type=str, nargs="*", default=None)
    p.add_argument("--sample-type-exclude", type=str, nargs="*", default=None)

    p.add_argument("--imputation-method", type=str, default="knn", choices=["mean", "median", "knn"])
    p.add_argument("--knn-k", type=int, default=5)

    p.add_argument("--batch-method", type=str, default="combat")

    p.add_argument("--pca-components", type=int, default=2)
    p.add_argument("--color-by", type=str, default="group_label", choices=["group_label", "sample_type", "batch_id"])

    return p.parse_args()


def main() -> None:
    args = parse_args()
    processed_root = Path(args.processed_root)

    ok_batches: List[str] = []
    failed_preprocess: List[str] = []
    failed_impute: List[str] = []
    failed_eval: List[str] = []

    batch_status: Dict[str, Any] = {}

    for ds in args.datasets:
        try:
            rep = run_for_dataset(ds, processed_root, args)
            ok_batches.append(ds)
            if rep["batch_correction_out"].get("status"):
                batch_status[ds] = rep["batch_correction_out"]
            print(f"[OK] {ds}")
        except Exception as e:
            msg = str(e)
            # 简化：根据异常信息猜测阶段
            if "imput" in msg.lower():
                failed_impute.append(ds)
            elif "pca" in msg.lower() or "evaluation" in msg.lower():
                failed_eval.append(ds)
            else:
                failed_preprocess.append(ds)
            print(f"[FAIL] {ds}: {e}")

    # 汇总打印
    print("\n=== Pipeline 汇总 ===")
    print(f"成功 batch 数: {len(ok_batches)}/{len(args.datasets)}")
    if failed_preprocess:
        print("preprocess 失败:", ", ".join(failed_preprocess))
    if failed_impute:
        print("imputation 失败:", ", ".join(failed_impute))
    if failed_eval:
        print("PCA evaluation 失败:", ", ".join(failed_eval))

    print("\nBatch-correct 状态（真实执行/跳过/未实现）:")
    for ds in args.datasets:
        st = batch_status.get(ds)
        if not st:
            continue
        print(f"- {ds}: status={st.get('status')} reason={st.get('reason')}")


if __name__ == "__main__":
    main()

