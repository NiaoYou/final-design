"""
build_metakg_subgraph_dataset.py
===================================
为 bioheart / mi 等"代谢物名已知"的数据集从 MetaKG 大文件中提取子图。

前置条件
--------
    先运行 build_named_dataset_annotation.py，生成 annotated_feature_meta.json

用法
-----
    cd backend
    python3 scripts/build_metakg_subgraph_dataset.py --dataset bioheart
    python3 scripts/build_metakg_subgraph_dataset.py --dataset mi
    python3 scripts/build_metakg_subgraph_dataset.py --dataset all

    # 可自定义 MetaKG 文件路径（默认 ~/Downloads）
    python3 scripts/build_metakg_subgraph_dataset.py --dataset bioheart \\
        --entities /path/to/metakg_entities.csv \\
        --triples  /path/to/metakg_triples.csv

输出
-----
    data/processed/{dataset}/_pipeline/metakg_subgraph.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Set, Tuple

import pandas as pd

# ─── 路径常量 ────────────────────────────────────────────────────────────────
BACKEND_DIR   = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"

DEFAULT_ENTITIES = Path.home() / "Downloads" / "metakg_entities.csv"
DEFAULT_TRIPLES  = Path.home() / "Downloads" / "metakg_triples.csv"

NAMED_DATASETS = {
    "bioheart": PROCESSED_DIR / "bioheart",
    "mi":       PROCESSED_DIR / "mi",
}

# 只保留有意义的关系类型
KEEP_RELATIONS = {
    "has_pathway", "has_reaction", "has_enzyme",
    "has_module", "has_network", "has_disease",
    "related_to_protein", "related_to_gene",
    "is_a", "same_as", "same as", "is a",
}

# 只保留真实实体类型
KEEP_ENTITY_TYPES = {
    "Compound", "Pathway", "Reaction", "Enzyme",
    "Disease", "Protein", "Gene", "Orthology", "Drug",
}

LITERAL_NODES = {"Compound", "Pathway", "Reaction", "Enzyme", "Disease", "Protein", "Gene"}

CHUNK_SIZE = 200_000


# ─── 从 annotated_feature_meta.json 读取种子 ID ───────────────────────────────

def load_seed_ids_from_annotation(pipeline_dir: Path) -> Tuple[Set[str], Set[str], list]:
    """
    返回 (kegg_seeds, hmdb_seeds, features_list)
    kegg_seeds : compound_id:Cxxxxx 格式
    hmdb_seeds : hmdb_id:HMDBxxxxxxx 格式
    """
    ann_path = pipeline_dir / "annotated_feature_meta.json"
    if not ann_path.is_file():
        raise FileNotFoundError(
            f"找不到 {ann_path}，请先运行 build_named_dataset_annotation.py"
        )
    ann = json.loads(ann_path.read_text(encoding="utf-8"))
    features = ann.get("features", [])

    kegg_seeds: Set[str] = set()
    hmdb_seeds: Set[str] = set()
    for feat in features:
        for kid in (feat.get("kegg_ids") or []):
            if kid:
                kegg_seeds.add(f"compound_id:{kid}")
        for hid in (feat.get("hmdb_ids") or []):
            if hid:
                hmdb_seeds.add(f"hmdb_id:{hid}")

    return kegg_seeds, hmdb_seeds, features


# ─── MetaKG 处理函数（与原脚本一致）─────────────────────────────────────────

def load_entities(entities_path: Path) -> Dict[str, str]:
    print(f"[1/4] 读取实体表 {entities_path} ...")
    t0 = time.time()
    df = pd.read_csv(str(entities_path), dtype=str).dropna()
    df.columns = ["entity_id", "entity_type"]
    df = df[df["entity_type"].isin(KEEP_ENTITY_TYPES)]
    entity_map = dict(zip(df["entity_id"], df["entity_type"]))
    print(f"      有效实体: {len(entity_map):,}  (耗时 {time.time()-t0:.1f}s)")
    return entity_map


def extract_triples(triples_path: Path, seed_ids: Set[str], entity_map: Dict) -> pd.DataFrame:
    print(f"[2/4] 流式扫描三元组 {triples_path} ...")
    t0 = time.time()
    matched = []
    for i, chunk in enumerate(pd.read_csv(str(triples_path), dtype=str, chunksize=CHUNK_SIZE)):
        chunk.columns = ["head", "relation", "tail"]
        chunk = chunk[chunk["relation"].isin(KEEP_RELATIONS)]
        hit = chunk[chunk["head"].isin(seed_ids)]
        if len(hit):
            matched.append(hit)
        if (i + 1) % 10 == 0:
            print(f"      已处理 {(i+1)*CHUNK_SIZE:,} 行，命中 {sum(len(m) for m in matched):,} ...")

    result = (pd.concat(matched, ignore_index=True)
              if matched else pd.DataFrame(columns=["head", "relation", "tail"]))
    print(f"      三元组命中: {len(result):,}  (耗时 {time.time()-t0:.1f}s)")
    return result


def _guess_type(node_id: str) -> str:
    prefix = node_id.split(":")[0] if ":" in node_id else ""
    mapping = {
        "compound_id": "Compound", "pathway_id": "Pathway",
        "reaction_id": "Reaction", "enzyme_id": "Enzyme",
        "disease_id": "Disease", "protein_id": "Protein",
        "gene_id": "Gene", "drug_id": "Drug",
        "module_id": "Module", "network_id": "Network",
        "hmdb_id": "Compound",
    }
    return mapping.get(prefix, "Other")


def build_subgraph(seed_ids: Set[str], triples_df: pd.DataFrame,
                   entity_map: Dict, feature_map: Dict) -> dict:
    print("[3/4] 构建子图节点与边 ...")
    all_node_ids = set(triples_df["head"]) | set(triples_df["tail"]) | seed_ids
    all_node_ids = {n for n in all_node_ids if n not in LITERAL_NODES}

    nodes = []
    for nid in sorted(all_node_ids):
        etype = entity_map.get(nid, _guess_type(nid))
        node: Dict = {
            "id": nid,
            "type": etype,
            "label": nid.split(":", 1)[-1] if ":" in nid else nid,
            "is_seed": nid in seed_ids,
        }
        if nid in feature_map:
            feat = feature_map[nid]
            node["metabolite_name"] = feat.get("metabolite_name", "")
            node["formula"]         = feat.get("formula", "")
            node["ion_mz"]          = feat.get("ion_mz")
        nodes.append(node)

    edges_raw = triples_df[["head", "relation", "tail"]].drop_duplicates()
    edges = [e for e in edges_raw.to_dict(orient="records")
             if e["tail"] not in LITERAL_NODES]

    type_counts = {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1

    rel_counts = triples_df["relation"].value_counts().to_dict()

    print(f"      节点总数: {len(nodes)}，边总数: {len(edges)}")
    print(f"      节点类型分布: {type_counts}")

    return {
        "meta": {
            "n_nodes": len(nodes),
            "n_edges": len(edges),
            "n_seed_compounds": len(seed_ids),
            "node_type_counts": type_counts,
            "relation_counts": rel_counts,
            "description": "MetaKG subgraph for named metabolite dataset (one-hop neighbors)",
        },
        "nodes": nodes,
        "edges": edges,
    }


# ─── 单数据集处理 ─────────────────────────────────────────────────────────────

def process_dataset(ds_name: str, ds_dir: Path,
                    entities_path: Path, triples_path: Path):
    print(f"\n{'='*60}")
    print(f"处理数据集: {ds_name}")

    pipeline_dir = ds_dir / "_pipeline"
    out_path     = pipeline_dir / "metakg_subgraph.json"

    # 1. 读取种子 IDs
    print("[0/4] 读取 annotated_feature_meta.json ...")
    kegg_seeds, hmdb_seeds, features = load_seed_ids_from_annotation(pipeline_dir)
    seed_ids = kegg_seeds | hmdb_seeds
    print(f"      KEGG 种子: {len(kegg_seeds)}，HMDB 种子: {len(hmdb_seeds)}")

    if not seed_ids:
        print(f"[{ds_name}] ⚠️  无有效种子 ID，跳过")
        return

    # 构建 feature_map：compound_id:Cxxxxx -> feature 字典
    feature_map: Dict = {}
    for feat in features:
        for kid in (feat.get("kegg_ids") or []):
            if kid:
                feature_map[f"compound_id:{kid}"] = feat
        for hid in (feat.get("hmdb_ids") or []):
            if hid:
                feature_map[f"hmdb_id:{hid}"] = feat

    # 2. 读取实体表
    entity_map = load_entities(entities_path)

    valid_seeds = seed_ids & set(entity_map.keys())
    print(f"      在 entities 中找到: {len(valid_seeds)} / {len(seed_ids)}")

    if not valid_seeds:
        print(f"[{ds_name}] ⚠️  所有种子都不在 entities 中，跳过")
        return

    # 3. 流式扫描三元组
    triples_df = extract_triples(triples_path, valid_seeds, entity_map)

    if len(triples_df) == 0:
        print(f"[{ds_name}] ⚠️  未找到匹配三元组")
        # 仍写出空子图（仅含种子节点）
        triples_df = pd.DataFrame(columns=["head", "relation", "tail"])

    # 4. 构建子图
    subgraph = build_subgraph(valid_seeds, triples_df, entity_map, feature_map)

    # 5. 写出
    print(f"[4/4] 写出子图到 {out_path} ...")
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(subgraph, f, ensure_ascii=False, indent=2)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n[{ds_name}] 完成！")
    print(f"   文件大小: {size_mb:.2f} MB")
    print(f"   节点数: {subgraph['meta']['n_nodes']}")
    print(f"   边数:   {subgraph['meta']['n_edges']}")
    print(f"   输出:   {out_path}")


# ─── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="为命名代谢物数据集提取 MetaKG 子图")
    parser.add_argument("--dataset", default="all",
                        choices=list(NAMED_DATASETS.keys()) + ["all"])
    parser.add_argument("--entities", default=str(DEFAULT_ENTITIES),
                        help="metakg_entities.csv 路径")
    parser.add_argument("--triples", default=str(DEFAULT_TRIPLES),
                        help="metakg_triples.csv 路径")
    args = parser.parse_args()

    entities_path = Path(args.entities)
    triples_path  = Path(args.triples)

    for p, label in [(entities_path, "entities"), (triples_path, "triples")]:
        if not p.is_file():
            print(f"❌ 找不到 {label} 文件: {p}", file=sys.stderr)
            sys.exit(1)

    targets = (NAMED_DATASETS if args.dataset == "all"
               else {args.dataset: NAMED_DATASETS[args.dataset]})

    for ds_name, ds_dir in targets.items():
        try:
            process_dataset(ds_name, ds_dir, entities_path, triples_path)
        except FileNotFoundError as e:
            print(f"[{ds_name}] ❌ {e}")

    print("\n[全部完成]")


if __name__ == "__main__":
    main()
