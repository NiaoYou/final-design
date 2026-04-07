"""
特征注释服务（Feature Annotation）

数据来源
--------
- 每批次 processed/ 目录下的 annotation.csv，包含字段：
    ionIdx, ionMz, ionAverageInt, mz delta, formula, ion,
    label (bona fide), HMDB ids, KEGG ids, other ids
- 同一 ionIdx 可能对应多个候选代谢物（同 m/z 多结构），
  按 |mz delta| 最小选取最优注释。

产物
----
- _pipeline/annotated_feature_meta.json：
    每个 ionIdx 对应的注释信息（代谢物名、分子式、HMDB/KEGG ID 列表）
- 同时更新 merged_feature_meta.csv（追加注释列）
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def _parse_id_list(raw: Any) -> List[str]:
    """
    把 'HMDB0000042; HMDB0003344; ...' 拆分并去重，
    统一格式为 HMDB0000042（10 位，去除旧格式短 ID 的重复）。
    """
    if not raw or (isinstance(raw, float) and np.isnan(raw)):
        return []
    ids = [x.strip() for x in str(raw).split(";") if x.strip()]
    # 去重：HMDB 旧格式（8位 HMDB01234）和新格式（10位 HMDB0001234）同一物质
    # 简单去重保留唯一值
    return list(dict.fromkeys(ids))  # 保序去重


def _parse_kegg_list(raw: Any) -> List[str]:
    if not raw or (isinstance(raw, float) and np.isnan(raw)):
        return []
    return [x.strip() for x in str(raw).split(";") if x.strip()]


def _hmdb_url(hmdb_id: str) -> Optional[str]:
    """生成 HMDB 详情页 URL（用第一个标准格式 ID）。"""
    # 统一成 10 位格式
    m = re.search(r"(\d+)$", hmdb_id)
    if not m:
        return None
    num = int(m.group(1))
    return f"https://hmdb.ca/metabolites/HMDB{num:07d}"


def _kegg_url(kegg_id: str) -> Optional[str]:
    k = kegg_id.strip()
    if k.startswith("C"):
        return f"https://www.genome.jp/entry/{k}"
    return None


# ─────────────────────────────────────────────
# 核心：加载并合并 annotation
# ─────────────────────────────────────────────

def load_best_annotation_per_ion(
    batch_annotation_path: Path,
) -> pd.DataFrame:
    """
    从单个 batch 的 annotation.csv 中，
    对每个 ionIdx 取 |mz delta| 最小的行作为最优注释。

    Returns
    -------
    pd.DataFrame  列: ionIdx, formula, ion_mode, metabolite_name,
                       hmdb_ids (list[str]), kegg_ids (list[str]),
                       hmdb_url, kegg_url, mz_delta_best
    """
    df = pd.read_csv(batch_annotation_path)
    df.columns = [c.strip() for c in df.columns]

    # 归一化列名
    col_map = {
        "label (bona fide)": "metabolite_name",
        "mz delta": "mz_delta",
        "ion": "ion_mode",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # 取 |mz_delta| 最小的候选
    df["abs_delta"] = df["mz_delta"].abs()
    best = (
        df.sort_values("abs_delta")
        .groupby("ionIdx", sort=False)
        .first()
        .reset_index()
    )

    # 解析 ID 列表
    best["hmdb_ids"] = best["HMDB ids"].apply(_parse_id_list)
    best["kegg_ids"] = best["KEGG ids"].apply(_parse_kegg_list)

    # 生成主链接（取第一个 ID）
    best["hmdb_url"] = best["hmdb_ids"].apply(
        lambda ids: _hmdb_url(ids[0]) if ids else None
    )
    best["kegg_url"] = best["kegg_ids"].apply(
        lambda ids: _kegg_url(ids[0]) if ids else None
    )

    keep_cols = [
        "ionIdx", "formula", "ion_mode", "metabolite_name",
        "hmdb_ids", "kegg_ids", "hmdb_url", "kegg_url", "abs_delta",
    ]
    return best[[c for c in keep_cols if c in best.columns]]


def build_feature_annotation(
    benchmark_merged_dir: Path,
    pipeline_dir: Path,
    *,
    prefer_batch: int = 1,
) -> Dict[str, Any]:
    """
    构建 merged 数据集中 1180 个特征的注释表。

    Strategy
    --------
    1. 优先使用 prefer_batch（默认 Batch1）的 annotation.csv。
    2. 对 merged_feature_meta.csv 中的 ionIdx 做 left join。
    3. 对未命中的 ionIdx，逐个尝试其余 batch 的 annotation.csv。
    4. 最终结果写入 _pipeline/annotated_feature_meta.json。

    Returns
    -------
    dict  含 'features'（list of dicts）和 'stats' 字段。
    """
    feat_meta_path = benchmark_merged_dir / "merged_feature_meta.csv"
    if not feat_meta_path.is_file():
        raise FileNotFoundError(f"找不到 merged_feature_meta.csv: {feat_meta_path}")

    feat_meta = pd.read_csv(feat_meta_path)
    feat_meta["ionIdx"] = feat_meta["ionIdx"].astype(int)

    # 找所有 batch 的 annotation.csv
    processed_dir = benchmark_merged_dir.parent
    batch_dirs = sorted(
        [d for d in processed_dir.iterdir() if d.is_dir() and "Batch" in d.name],
        key=lambda p: p.name,
    )
    if not batch_dirs:
        raise FileNotFoundError(f"在 {processed_dir} 下找不到 Batch* 目录。")

    logger.info("发现 %d 个 batch 目录，加载注释数据…", len(batch_dirs))

    # 按 prefer_batch 优先排序
    def _batch_priority(d: Path) -> int:
        m = re.search(r"Batch(\d+)", d.name)
        if not m:
            return 99
        n = int(m.group(1))
        return 0 if n == prefer_batch else n

    batch_dirs = sorted(batch_dirs, key=_batch_priority)

    # 逐 batch 加载，合并注释
    annotation_pool: Optional[pd.DataFrame] = None
    for bd in batch_dirs:
        ann_path = bd / "annotation.csv"
        if not ann_path.is_file():
            continue
        try:
            ann = load_best_annotation_per_ion(ann_path)
            if annotation_pool is None:
                annotation_pool = ann
            else:
                # 补充 pool 中还没有的 ionIdx
                missing = ~ann["ionIdx"].isin(annotation_pool["ionIdx"])
                if missing.any():
                    annotation_pool = pd.concat(
                        [annotation_pool, ann[missing]], ignore_index=True
                    )
        except Exception as e:
            logger.warning("加载 %s 失败: %s", ann_path, e)

    if annotation_pool is None:
        raise RuntimeError("所有 batch 目录中均未找到有效的 annotation.csv。")

    # Left join：feat_meta ← annotation_pool
    merged = feat_meta.merge(annotation_pool, on="ionIdx", how="left")

    # 构造输出列表
    features: List[Dict[str, Any]] = []
    for _, row in merged.iterrows():
        name = row.get("metabolite_name")
        if pd.isna(name) or name == "":
            name = None

        features.append({
            "feature_col": str(row["feature_col_name"]),   # 矩阵列名（"1","2"...）
            "ion_idx": int(row["ionIdx"]),
            "ion_mz": round(float(row["ionMz"]), 6),
            "metabolite_name": name,
            "formula": row.get("formula") if pd.notna(row.get("formula")) else None,
            "ion_mode": row.get("ion_mode") if pd.notna(row.get("ion_mode")) else None,
            "hmdb_ids": row.get("hmdb_ids") if isinstance(row.get("hmdb_ids"), list) else [],
            "kegg_ids": row.get("kegg_ids") if isinstance(row.get("kegg_ids"), list) else [],
            "hmdb_url": row.get("hmdb_url") if pd.notna(row.get("hmdb_url") or None) else None,
            "kegg_url": row.get("kegg_url") if pd.notna(row.get("kegg_url") or None) else None,
        })

    n_annotated = sum(1 for f in features if f["metabolite_name"])
    n_kegg = sum(1 for f in features if f["kegg_ids"])
    n_hmdb = sum(1 for f in features if f["hmdb_ids"])

    result = {
        "schema_version": "annotation_v1",
        "n_features": len(features),
        "n_annotated": n_annotated,
        "n_with_kegg": n_kegg,
        "n_with_hmdb": n_hmdb,
        "coverage_pct": round(n_annotated / len(features) * 100, 1) if features else 0,
        "features": features,
    }

    # 写入 JSON
    out_path = pipeline_dir / "annotated_feature_meta.json"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(
        "注释完成：%d/%d 特征有代谢物名（%.1f%%），%d 有 KEGG ID，%d 有 HMDB ID，写入 %s",
        n_annotated, len(features), result["coverage_pct"], n_kegg, n_hmdb, out_path,
    )
    return result


# ─────────────────────────────────────────────
# 只读加载（供 API 层调用）
# ─────────────────────────────────────────────

def load_annotation_json(pipeline_dir: Path) -> Optional[Dict[str, Any]]:
    p = pipeline_dir / "annotated_feature_meta.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_annotation_lookup(pipeline_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    返回 {feature_col → annotation_dict} 的查找字典，
    供差异分析结果富化代谢物名使用。
    """
    data = load_annotation_json(pipeline_dir)
    if not data:
        return {}
    return {f["feature_col"]: f for f in data.get("features", [])}
