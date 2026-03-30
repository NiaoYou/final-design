from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.services.benchmark_importer import run_benchmark_import
from app.core.config import Settings


TARGETS: List[str] = [
    "Batch1_0108 DATA.xlsx",
    "Batch2_0110 DATA.xlsx",
    "Batch3_0124 DATA.xlsx",
    "Batch4_0219 DATA.xlsx",
    "Batch5_0221 DATA.xlsx",
    "Batch6_0304 DATA.xlsx",
    "Batch7_0306 DATA.xlsx",
]


def _format_notes(notes: List[str]) -> str:
    if not notes:
        return ""
    return "\n".join([f"- {n}" for n in notes])


def main() -> None:
    raw_dir = Settings.BASE_DIR / "data" / "raw" / "benchmark"
    processed_dir = Settings.PROCESSED_DIR

    if not raw_dir.exists():
        raise FileNotFoundError(f"raw benchmark 目录不存在: {raw_dir}")

    result = run_benchmark_import(
        raw_benchmark_dir=raw_dir,
        processed_root=processed_dir,
        target_file_names=TARGETS,
    )

    scan_results = result["scan_results"]
    print("=== Benchmark 扫描检查结果（xls xlsx）=== ")
    for r in scan_results:
        print(
            f"[{r['file_name']}] sheets={r['detected_sheets']} valid={r['is_valid']} "
            f"(intensities={r['has_intensities']}, injections={r['has_injections']})"
        )

    print("\n=== Benchmark 处理报告（仅处理指定 7 个 xlsx）=== ")
    processed_files: List[Dict[str, Any]] = result["processed_files"]
    failed_files: List[Dict[str, Any]] = result["failed_files"]

    def _bool(v: Any) -> str:
        return "true" if bool(v) else "false"

    if failed_files:
        print("\n失败文件：")
        for f in failed_files:
            print(f"- {f['file_name']}: {f.get('error')}")

    if processed_files:
        print("\n成功处理文件：")
        for p in processed_files:
            data_check = p["data_check"]
            print(f"- {p['file_name']} -> {p['processed_dir']}")
            print(
                f"  feature_count={data_check['feature_count']} sample_count={data_check['sample_count']} "
                f"matched_sample_count={data_check['matched_sample_count']}"
            )
            if data_check.get("unmatched_sample_columns"):
                print("  unmatched_sample_columns:")
                for u in data_check["unmatched_sample_columns"]:
                    print(f"  - {u}")

            print("  can_run flags:")
            print(f"  - can_run_preprocess: {_bool(data_check['can_run_preprocess'])}")
            print(f"  - can_run_imputation: {_bool(data_check['can_run_imputation'])}")
            print(f"  - can_run_batch_correction: {_bool(data_check['can_run_batch_correction'])}")
            print(f"  - can_run_downstream_analysis: {_bool(data_check['can_run_downstream_analysis'])}")

            notes = data_check.get("notes", [])
            if notes:
                print("  notes:")
                print(_format_notes(notes))

    # 汇总输出一份 machine-readable 报告，方便后续你直接查
    report_path = processed_dir / "_benchmark_import_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n汇总报告已写入: {report_path}")


if __name__ == "__main__":
    main()

