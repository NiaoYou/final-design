"""
build_metakg_subgraph.py
========================
从 MetaKG 大文件中提取本项目代谢物相关子图，生成轻量 JSON 供前端可视化。

用法：
    cd backend
    python3 app/scripts/build_metakg_subgraph.py \
        /Users/gaoyunduan/Downloads/metakg_entities.csv \
        /Users/gaoyunduan/Downloads/metakg_triples.csv

输出：
    data/processed/benchmark_merged/_pipeline/metakg_subgraph.json
"""

import sys
import json
import os
import time
import pandas as pd

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

# 只保留这些关系类型（过滤掉化学属性等无意义关系）
KEEP_RELATIONS = {
    "has_pathway",
    "has_reaction",
    "has_enzyme",
    "has_module",
    "has_network",
    "has_disease",
    "related_to_protein",
    "related_to_gene",
    "is_a",
    "same_as",
    "same as",
    "is a",
}

# 只保留这些节点类型（过滤 Synonym / Smiles / Inchikey 等）
KEEP_ENTITY_TYPES = {
    "Compound", "Pathway", "Reaction", "Enzyme", "Disease",
    "Protein", "Gene", "Orthology", "Drug",
}

# 子图中过滤掉的字面量节点（不是真实实体）
LITERAL_NODES = {"Compound", "Pathway", "Reaction", "Enzyme", "Disease", "Protein", "Gene"}

CHUNK_SIZE = 200_000   # 流式读取 triples 的块大小

# ──────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────

def load_project_kegg_ids(pipeline_dir: str) -> set:
    """从 annotated_feature_meta.json 读取项目中所有 KEGG compound ID"""
    ann_path = os.path.join(pipeline_dir, "annotated_feature_meta.json")
    with open(ann_path, encoding="utf-8") as f:
        ann = json.load(f)
    kegg_ids = set()
    for feat in ann.get("features", []):
        for kid in (feat.get("kegg_ids") or []):
            if kid:
                kegg_ids.add(f"compound_id:{kid}")
    # 也保留原始 HMDB ID（如果有）
    hmdb_ids = set()
    for feat in ann.get("features", []):
        for hid in (feat.get("hmdb_ids") or []):
            if hid:
                hmdb_ids.add(f"hmdb_id:{hid}")
    return kegg_ids, hmdb_ids, ann.get("features", [])


def load_entities(entities_path: str) -> dict:
    """读取实体表，返回 {entity_id: entity_type} 字典"""
    print(f"[1/4] 读取实体表 {entities_path} ...")
    t0 = time.time()
    df = pd.read_csv(entities_path, dtype=str)
    df.columns = ["entity_id", "entity_type"]
    df = df[df["entity_type"].isin(KEEP_ENTITY_TYPES)]
    entity_map = dict(zip(df["entity_id"], df["entity_type"]))
    print(f"      有效实体: {len(entity_map):,}  (耗时 {time.time()-t0:.1f}s)")
    return entity_map


def extract_triples(triples_path: str, seed_ids: set, entity_map: dict) -> list:
    """
    流式扫描三元组文件，提取以 seed_ids 为种子（head 或 tail）的有意义三元组。
    同时收集一跳邻居节点 ID。
    """
    print(f"[2/4] 流式扫描三元组 {triples_path} ...")
    t0 = time.time()
    matched = []
    chunk_idx = 0
    for chunk in pd.read_csv(triples_path, dtype=str, chunksize=CHUNK_SIZE):
        chunk.columns = ["head", "relation", "tail"]
        # 只保留关注的关系类型
        chunk = chunk[chunk["relation"].isin(KEEP_RELATIONS)]
        # head 在种子集合中
        hit = chunk[chunk["head"].isin(seed_ids)]
        matched.append(hit)
        chunk_idx += 1
        if chunk_idx % 10 == 0:
            total_so_far = sum(len(m) for m in matched)
            print(f"      已处理 {chunk_idx * CHUNK_SIZE:,} 行，命中三元组 {total_so_far:,} ...")

    result = pd.concat(matched, ignore_index=True) if matched else pd.DataFrame(columns=["head", "relation", "tail"])
    print(f"      三元组命中: {len(result):,}  (耗时 {time.time()-t0:.1f}s)")
    return result


def _guess_type(node_id: str) -> str:
    """根据前缀猜测节点类型（用于 entities 文件中不存在的节点）"""
    prefix = node_id.split(":")[0] if ":" in node_id else ""
    mapping = {
        "compound_id": "Compound",
        "pathway_id":  "Pathway",
        "reaction_id": "Reaction",
        "enzyme_id":   "Enzyme",
        "disease_id":  "Disease",
        "protein_id":  "Protein",
        "gene_id":     "Gene",
        "drug_id":     "Drug",
        "module_id":   "Module",
        "network_id":  "Network",
        "hmdb_id":     "Compound",
    }
    return mapping.get(prefix, "Other")


def build_subgraph(seed_ids: set, triples_df: pd.DataFrame, entity_map: dict,
                   feature_map: dict) -> dict:
    """
    整合种子节点、三元组、邻居节点，构建子图 JSON。
    feature_map: {compound_id_str -> feature info}，用于给代谢物节点加上代谢物名等属性。
    """
    print("[3/4] 构建子图节点与边 ...")

    # 收集所有出现的节点 ID
    all_node_ids = set(triples_df["head"]) | set(triples_df["tail"])
    all_node_ids |= seed_ids  # 确保种子节点都在

    # 过滤掉字面量节点（如 head/tail 直接是 "Compound" 字符串的）
    all_node_ids = {n for n in all_node_ids if n not in LITERAL_NODES}

    # 构建节点列表
    nodes = []
    for nid in sorted(all_node_ids):
        etype = entity_map.get(nid, _guess_type(nid))
        node = {
            "id": nid,
            "type": etype,
            "label": nid.split(":", 1)[-1] if ":" in nid else nid,
            "is_seed": nid in seed_ids,
        }
        # 如果是本项目代谢物，附加代谢物名称
        if nid in feature_map:
            feat = feature_map[nid]
            node["metabolite_name"] = feat.get("metabolite_name", "")
            node["formula"] = feat.get("formula", "")
            node["ion_mz"] = feat.get("ion_mz")
        nodes.append(node)

    # 构建边列表（去重）
    edges_raw = triples_df[["head", "relation", "tail"]].drop_duplicates()
    edges = edges_raw.to_dict(orient="records")

    # 过滤 edges 中 tail 是字面量的
    edges = [e for e in edges if e["tail"] not in LITERAL_NODES]

    # 统计各类型节点数
    type_counts = {}
    for n in nodes:
        t = n["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # 统计各关系类型数
    rel_counts = triples_df["relation"].value_counts().to_dict()

    print(f"      节点总数: {len(nodes)}，边总数: {len(edges)}")
    print(f"      节点类型分布: {type_counts}")
    print(f"      关系类型分布: {rel_counts}")

    return {
        "meta": {
            "n_nodes": len(nodes),
            "n_edges": len(edges),
            "n_seed_compounds": len(seed_ids),
            "node_type_counts": type_counts,
            "relation_counts": rel_counts,
            "description": "MetaKG subgraph for project KEGG compound IDs (one-hop neighbors)",
        },
        "nodes": nodes,
        "edges": edges,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    entities_path = sys.argv[1]
    triples_path  = sys.argv[2]

    # 输出目录
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    backend_dir  = os.path.dirname(os.path.dirname(script_dir))
    pipeline_dir = os.path.join(
        backend_dir,
        "data", "processed", "benchmark_merged", "_pipeline"
    )
    out_path = os.path.join(pipeline_dir, "metakg_subgraph.json")

    # 1. 读取项目 KEGG IDs
    print("[0/4] 读取项目 KEGG compound IDs ...")
    seed_ids, hmdb_ids, features = load_project_kegg_ids(pipeline_dir)
    print(f"      KEGG compound 种子: {len(seed_ids)}")

    # 构建 feature_map：compound_id:Cxxxxx -> feature 字典
    feature_map = {}
    for feat in features:
        for kid in (feat.get("kegg_ids") or []):
            if kid:
                feature_map[f"compound_id:{kid}"] = feat

    # 2. 读取实体表
    entity_map = load_entities(entities_path)

    # 过滤掉 entities 中不存在的种子（避免孤立节点混入）
    valid_seeds = seed_ids & set(entity_map.keys())
    print(f"      在 entities 中找到的种子: {len(valid_seeds)} / {len(seed_ids)}")

    # 3. 流式扫描三元组
    triples_df = extract_triples(triples_path, valid_seeds, entity_map)

    if len(triples_df) == 0:
        print("⚠️  未找到任何匹配三元组，请检查文件格式和种子 ID 格式")
        sys.exit(1)

    # 4. 构建子图
    subgraph = build_subgraph(valid_seeds, triples_df, entity_map, feature_map)

    # 5. 写出
    print(f"[4/4] 写出子图到 {out_path} ...")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(subgraph, f, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n✅ 完成！")
    print(f"   文件大小: {size_mb:.1f} MB")
    print(f"   节点数:   {subgraph['meta']['n_nodes']}")
    print(f"   边数:     {subgraph['meta']['n_edges']}")
    print(f"   输出路径: {out_path}")


if __name__ == "__main__":
    main()
