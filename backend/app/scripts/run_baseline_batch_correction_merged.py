from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import Settings
from app.services.baseline_batch_correction_merged import run_baseline_batch_correction_merged_pipeline


def main() -> None:
    p = argparse.ArgumentParser(
        description="Run reproducible baseline batch correction on benchmark_merged pipeline outputs"
    )
    p.add_argument("--processed-root", type=str, default=str(Settings.PROCESSED_DIR))
    p.add_argument(
        "--input-matrix",
        type=str,
        default="imputed_sample_by_feature.csv",
        help="Relative to benchmark_merged/_pipeline/ (default: imputed matrix after merged pipeline)",
    )
    p.add_argument("--pca-components", type=int, default=2)
    args = p.parse_args()

    root = Path(args.processed_root)
    merged_dir = root / "benchmark_merged"
    pipeline_dir = merged_dir / "_pipeline"
    out = run_baseline_batch_correction_merged_pipeline(
        benchmark_merged_dir=merged_dir,
        pipeline_dir=pipeline_dir,
        n_pca_components=args.pca_components,
        input_matrix_filename=args.input_matrix,
    )
    print("baseline batch correction done.")
    print("  corrected:", out["batch_corrected_matrix_path"])
    print("  report:", out["batch_correction_method_report_path"])
    print("  pca plot:", out["pca_before_vs_after_path"])
    m = out.get("metrics") or {}
    if m.get("heuristic_mixing_improved_by_centroid") is not None:
        print("  mixing_improved_by_centroid:", m["heuristic_mixing_improved_by_centroid"])
    if m.get("heuristic_mixing_improved_by_silhouette") is not None:
        print("  mixing_improved_by_silhouette:", m["heuristic_mixing_improved_by_silhouette"])


if __name__ == "__main__":
    main()
