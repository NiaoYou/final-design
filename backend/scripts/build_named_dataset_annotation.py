"""
build_named_dataset_annotation.py
===================================
为 bioheart / mi 等"代谢物名已知"的数据集生成 annotated_feature_meta.json。

策略
-----
代谢物名称 → 在 hmdb_metabolites.json 中按 name + synonyms 匹配 →
  获得 HMDB Accession + kegg_id → 写入 annotated_feature_meta.json。
该文件格式与 benchmark annotation_service.py 生成的完全一致，
可直接复用通路富集和 MetaKG 脚本。

用法
-----
    cd backend
    python3 scripts/build_named_dataset_annotation.py --dataset bioheart
    python3 scripts/build_named_dataset_annotation.py --dataset mi
    python3 scripts/build_named_dataset_annotation.py --dataset all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ─── 路径常量 ────────────────────────────────────────────────────
BACKEND_DIR   = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
HMDB_JSON     = Path("/Users/gaoyunduan/Downloads/hmdb_metabolites.json")

# 仅这些数据集有真实代谢物名称（amide 无法处理，跳过）
NAMED_DATASETS = {
    "bioheart": {
        "dir": PROCESSED_DIR / "bioheart",
        "label": "BioHeart 数据集",
    },
    "mi": {
        "dir": PROCESSED_DIR / "mi",
        "label": "MI（心肌梗死）数据集",
    },
}


# ─── 自定义别名映射（数据集特有的缩写/非标准名称）──────────────────────────────
# 格式：{ 原始特征名: 查询别名列表（按优先级）}
CUSTOM_ALIASES: Dict[str, List[str]] = {
    # bioheart
    "3HK":                ["3-hydroxykynurenine", "hydroxykynurenine"],
    "TMNO":               ["trimethylamine n-oxide", "trimethylamine oxide"],
    "trans-HYP":          ["trans-4-hydroxyproline", "4-hydroxyproline"],
    "Isoleucine_Leucine": ["isoleucine", "leucine"],
    "3-IPA":              ["indole-3-propionic acid", "3-indolepropionic acid"],
    "Valine-d8":          ["l-valine", "valine"],
    "DMGV":               ["dimethylguanidino valeric acid"],
    # mi
    "6keto-PGF1":         ["6-keto-prostaglandin f1alpha", "6-ketoprostaglandin f1a", "6-keto-pgf1a"],
    "13(S)-HODE":         ["13-hode", "13s-hode", "13(s)-hode"],
    "12(13)-DiHOME":      ["12,13-dihydroxyoctadecenoic acid", "leukotoxin diol", "12(13)-dihome"],
    # 3-deaazadenosine / GlucosePos2: 非标准测试物质，跳过（无 HMDB 记录）
}

# ─── HMDB 索引构建 ────────────────────────────────────────────────────────────

def build_hmdb_index(hmdb_path: Path) -> Tuple[Dict, Dict]:
    """
    从 hmdb_metabolites.json 构建两个索引：
      name_index:    normalized_name → (hmdb_id, kegg_id, formula)
      synonym_index: normalized_name → (hmdb_id, kegg_id, formula)
    返回 (name_index, synonym_index)
    """
    print(f"[HMDB] 加载 {hmdb_path} ...")
    with open(hmdb_path, encoding="utf-8") as f:
        data: Dict = json.load(f)

    name_index: Dict[str, dict] = {}
    synonym_index: Dict[str, dict] = {}

    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())

    for hmdb_id, entry in data.items():
        kegg_id: Optional[str] = entry.get("kegg_id") or None
        formula: Optional[str] = entry.get("chemical_formula") or None
        primary_name: str = entry.get("name", "") or ""

        info = {
            "hmdb_id": hmdb_id,
            "kegg_id": kegg_id,
            "name": primary_name,
            "formula": formula,
        }

        # 主名称
        if primary_name:
            name_index[_norm(primary_name)] = info

        # 同义词
        raw_syn = entry.get("synonyms")
        syns: List[str] = []
        if isinstance(raw_syn, dict):
            sv = raw_syn.get("synonym")
            if isinstance(sv, list):
                syns = [s for s in sv if isinstance(s, str)]
            elif isinstance(sv, str):
                syns = [sv]
        elif isinstance(raw_syn, list):
            syns = [s for s in raw_syn if isinstance(s, str)]

        for s in syns:
            k = _norm(s)
            if k not in synonym_index:
                synonym_index[k] = info

    print(f"[HMDB] 主名称索引: {len(name_index):,} 条，同义词索引: {len(synonym_index):,} 条")
    return name_index, synonym_index


def lookup_hmdb(metabolite_name: str, name_index: Dict, synonym_index: Dict) -> Optional[dict]:
    """
    按优先级查找：精确主名 → 精确同义词 → 自定义别名 → 无结果
    """
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())

    key = _norm(metabolite_name)
    if key in name_index:
        return name_index[key]
    if key in synonym_index:
        return synonym_index[key]

    # 自定义别名兜底
    for alias in CUSTOM_ALIASES.get(metabolite_name, []):
        ak = _norm(alias)
        if ak in name_index:
            return name_index[ak]
        if ak in synonym_index:
            return synonym_index[ak]

    return None


# ─── annotated_feature_meta.json 格式 ────────────────────────────────────────

def _hmdb_url(hmdb_id: str) -> Optional[str]:
    m = re.search(r"(\d+)$", hmdb_id)
    if not m:
        return None
    num = int(m.group(1))
    return f"https://hmdb.ca/metabolites/HMDB{num:07d}"


def _kegg_url(kegg_id: str) -> Optional[str]:
    if not kegg_id:
        return None
    return f"https://www.genome.jp/dbget-bin/www_bget?cpd:{kegg_id}"


def build_annotation(
    feature_names: List[str],
    name_index: Dict,
    synonym_index: Dict,
) -> dict:
    """
    对 feature_names 逐一查询，构建 annotated_feature_meta.json 格式。
    """
    features = []
    n_annotated = 0
    n_with_kegg = 0

    for fname in feature_names:
        hit = lookup_hmdb(fname, name_index, synonym_index)
        if hit:
            hmdb_ids = [hit["hmdb_id"]]
            kegg_ids = [hit["kegg_id"]] if hit["kegg_id"] else []
            formula  = hit["formula"] or None
            met_name = hit["name"] or fname
            n_annotated += 1
            if kegg_ids:
                n_with_kegg += 1
        else:
            hmdb_ids = []
            kegg_ids = []
            formula  = None
            met_name = fname   # fallback：用原始名称

        features.append({
            "feature": fname,
            "metabolite_name": met_name,
            "formula": formula,
            "ion_mz": None,          # 命名数据集无 m/z
            "hmdb_ids": hmdb_ids,
            "kegg_ids": kegg_ids,
            "hmdb_url": _hmdb_url(hmdb_ids[0]) if hmdb_ids else None,
            "kegg_url": _kegg_url(kegg_ids[0]) if kegg_ids else None,
        })

    return {
        "schema": "annotated_feature_meta_v1",
        "n_features": len(feature_names),
        "n_annotated": n_annotated,
        "n_with_kegg": n_with_kegg,
        "annotation_source": "hmdb_metabolites.json（名称/同义词精确匹配）",
        "features": features,
    }


# ─── 主流程 ──────────────────────────────────────────────────────────────────

def process_dataset(ds_name: str, ds_cfg: dict, name_index: Dict, synonym_index: Dict):
    ds_dir      = ds_cfg["dir"]
    pipeline_dir = ds_dir / "_pipeline"
    out_path    = pipeline_dir / "annotated_feature_meta.json"

    # 读取特征名列表（从批次校正后矩阵的列名）
    matrix_path = pipeline_dir / "batch_corrected_sample_by_feature.csv"
    if not matrix_path.is_file():
        print(f"[{ds_name}] ⚠️  找不到 {matrix_path}，跳过")
        return

    import pandas as pd
    mat = pd.read_csv(matrix_path, index_col=0, nrows=0)   # 只读 header
    feature_names = mat.columns.tolist()
    print(f"\n{'='*60}")
    print(f"[{ds_name}] 特征数: {len(feature_names)}")

    ann = build_annotation(feature_names, name_index, synonym_index)
    print(f"[{ds_name}] 注释命中: {ann['n_annotated']}/{ann['n_features']}  含KEGG ID: {ann['n_with_kegg']}")

    # 打印未命中
    missed = [f["feature"] for f in ann["features"] if not f["hmdb_ids"]]
    if missed:
        print(f"[{ds_name}] 未命中代谢物（{len(missed)}个）: {missed}")

    pipeline_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ann, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{ds_name}] ✅ 已写入: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="all", choices=list(NAMED_DATASETS.keys()) + ["all"])
    args = parser.parse_args()

    if not HMDB_JSON.is_file():
        print(f"❌ 找不到 hmdb_metabolites.json: {HMDB_JSON}", file=sys.stderr)
        sys.exit(1)

    name_index, synonym_index = build_hmdb_index(HMDB_JSON)

    targets = NAMED_DATASETS if args.dataset == "all" else {args.dataset: NAMED_DATASETS[args.dataset]}
    for ds_name, ds_cfg in targets.items():
        process_dataset(ds_name, ds_cfg, name_index, synonym_index)

    print("\n[完成] 所有数据集注释产物已生成。")
    print("下一步：运行 build_metakg_subgraph.py --dataset bioheart/mi")


if __name__ == "__main__":
    main()
