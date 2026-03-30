from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import Settings
from app.services.benchmark_cross_batch_merge import merge_benchmark_batches


def main() -> None:
    p = argparse.ArgumentParser(description="Merge Batch1~Batch7 processed outputs into benchmark_merged/")
    p.add_argument("--processed-root", type=str, default=str(Settings.PROCESSED_DIR))
    p.add_argument("--merge-strategy", type=str, default="inner", choices=["inner", "outer"])
    args = p.parse_args()

    out = merge_benchmark_batches(
        Path(args.processed_root),
        merge_strategy=args.merge_strategy,  # type: ignore[arg-type]
        out_dir_name="benchmark_merged",
    )
    print("merge done:", out["output_dir"])
    print("merged_sample_count:", out["merge_report"]["merged_sample_count"])
    print("merged_feature_count:", out["merge_report"]["merged_feature_count"])


if __name__ == "__main__":
    main()
