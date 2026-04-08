"""
通路富集分析服务（KEGG Pathway Enrichment Analysis）

策略
-----
- 背景集：annotated_feature_meta.json 中含 KEGG ID 的所有特征（577 个）
- 显著集：差异分析结果中 label in ['up', 'down'] 的特征对应 KEGG ID
- 方法：超几何检验（等价于 Fisher's exact test，单侧）
- 多重校正：Benjamini-Hochberg FDR
- 数据来源：KEGG REST API（化合物-通路映射 + 通路名称），本地缓存

参考
-----
Kanehisa, M. et al. (2017). KEGG: new perspectives on genomes,
pathways, diseases and drugs. Nucleic Acids Research 45(D1):D353–D361.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

KEGG_REST_BASE = "https://rest.kegg.jp"
KEGG_CACHE_DIR = "kegg_cache"
# 仅保留 reference pathway（map 前缀），过滤掉物种特异通路
_MAP_PREFIX = "map"


# --------------------------------------------------------------------------- #
# KEGG 数据获取与缓存
# --------------------------------------------------------------------------- #

def _kegg_cache_dir(pipeline_dir: Path) -> Path:
    d = pipeline_dir / KEGG_CACHE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _fetch_kegg_text(url: str, timeout: int = 30) -> Optional[str]:
    """调用 KEGG REST API，返回响应文本；失败时返回 None。"""
    try:
        import requests  # type: ignore
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "metabolomics-webapp/1.0"})
        resp.raise_for_status()
        return resp.text
    except ImportError:
        logger.warning("requests 库未安装，无法调用 KEGG API。请运行: pip install requests")
        return None
    except Exception as e:
        logger.warning("KEGG API 请求失败 [%s]: %s: %s", url, type(e).__name__, e)
        return None


def load_or_fetch_compound_pathway_map(pipeline_dir: Path) -> Dict[str, List[str]]:
    """
    加载或从 KEGG REST API 获取化合物-通路映射。

    Returns
    -------
    dict
        {cpd_id: [pathway_id, ...], ...}  e.g. {"C00207": ["map00071", ...]}
    """
    cache_path = _kegg_cache_dir(pipeline_dir) / "compound_pathway_map.json"
    if cache_path.is_file():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info("KEGG 化合物-通路映射从缓存加载：%d 个化合物", len(data))
            return data
        except Exception as e:
            logger.warning("KEGG 缓存文件损坏，重新获取: %s", e)

    logger.info("从 KEGG REST API 获取化合物-通路映射（首次获取，约需 10-30s）…")
    t0 = time.time()
    text = _fetch_kegg_text(f"{KEGG_REST_BASE}/link/pathway/compound")
    if not text:
        return {}

    cpd_pathway: Dict[str, List[str]] = {}
    for line in text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) != 2:
            continue
        cpd_raw, path_raw = parts
        cpd_id = cpd_raw.replace("cpd:", "").strip()          # C00207
        path_id = path_raw.replace("path:", "").strip()       # map00071
        if not path_id.startswith(_MAP_PREFIX):
            continue   # 跳过物种特异通路（hsa00010 等）
        cpd_pathway.setdefault(cpd_id, []).append(path_id)

    cache_path.write_text(json.dumps(cpd_pathway, ensure_ascii=False), encoding="utf-8")
    logger.info(
        "KEGG 化合物-通路映射已缓存：%d 个化合物，耗时 %.1f s",
        len(cpd_pathway), time.time() - t0,
    )
    return cpd_pathway


def load_or_fetch_pathway_names(pipeline_dir: Path) -> Dict[str, str]:
    """
    加载或从 KEGG REST API 获取通路名称。

    Returns
    -------
    dict
        {pathway_id: name, ...}  e.g. {"map00071": "Fatty acid degradation"}
    """
    cache_path = _kegg_cache_dir(pipeline_dir) / "pathway_names.json"
    if cache_path.is_file():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info("KEGG 通路名称从缓存加载：%d 条", len(data))
            return data
        except Exception as e:
            logger.warning("KEGG 通路名称缓存损坏，重新获取: %s", e)

    logger.info("从 KEGG REST API 获取通路名称…")
    text = _fetch_kegg_text(f"{KEGG_REST_BASE}/list/pathway")
    if not text:
        return {}

    names: Dict[str, str] = {}
    for line in text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) != 2:
            continue
        path_raw, name = parts
        path_id = path_raw.replace("path:", "").strip()
        names[path_id] = name.strip()

    cache_path.write_text(json.dumps(names, ensure_ascii=False), encoding="utf-8")
    logger.info("KEGG 通路名称已缓存：%d 条", len(names))
    return names


# --------------------------------------------------------------------------- #
# 超几何检验 + BH-FDR
# --------------------------------------------------------------------------- #

def _bh_correct(pvalues: List[float]) -> List[float]:
    """Benjamini-Hochberg FDR 校正（手动实现，避免额外依赖）。"""
    m = len(pvalues)
    if m == 0:
        return []
    indexed = sorted(enumerate(pvalues), key=lambda x: x[1])
    qvalues = [1.0] * m
    min_q = 1.0
    for rank, (orig_i, pv) in enumerate(reversed(indexed)):
        q = pv * m / (m - rank)
        min_q = min(min_q, q)
        qvalues[orig_i] = round(min(1.0, min_q), 6)
    return qvalues


def run_pathway_enrichment(
    sig_cpd_ids: Set[str],
    bg_cpd_ids: Set[str],
    cpd_pathway_map: Dict[str, List[str]],
    pathway_names: Dict[str, str],
    top_n: int = 20,
    qvalue_cutoff: float = 0.2,
) -> Dict[str, Any]:
    """
    超几何检验通路富集分析。

    Parameters
    ----------
    sig_cpd_ids : 显著差异特征的 KEGG compound ID 集合
    bg_cpd_ids  : 背景（全部含注释特征）的 KEGG compound ID 集合
    cpd_pathway_map : {cpd_id: [pathway_id, ...]}
    pathway_names   : {pathway_id: name}
    top_n       : 最多返回的通路数
    qvalue_cutoff : FDR 截止值，超过时仍返回 top_n 条（宽松显示）
    """
    try:
        from scipy.stats import hypergeom  # type: ignore
        _use_scipy = True
    except ImportError:
        _use_scipy = False
        logger.warning("scipy 未安装，退化为近似超几何检验")

    # 取交集（只考虑背景中存在的 sig ID）
    sig_in_bg = sig_cpd_ids & bg_cpd_ids
    M = len(bg_cpd_ids)   # 背景总体大小
    n = len(sig_in_bg)    # 显著集大小（in background）

    if n == 0:
        return {
            "available": False,
            "reason": f"显著差异特征中无 KEGG ID（共 {len(sig_cpd_ids)} 个显著特征）。",
            "pathways": [],
        }
    if M == 0:
        return {"available": False, "reason": "背景集为空。", "pathways": []}

    # 构建通路 → 背景化合物的映射
    pathway_bg: Dict[str, Set[str]] = {}
    for cpd, pathways in cpd_pathway_map.items():
        if cpd not in bg_cpd_ids:
            continue
        for pid in pathways:
            pathway_bg.setdefault(pid, set()).add(cpd)

    # 逐通路计算 p-value
    raw_results: List[Dict[str, Any]] = []
    for path_id, bg_cpds in pathway_bg.items():
        K = len(bg_cpds)                  # 通路在背景中的化合物数
        overlap = sig_in_bg & bg_cpds     # 交集
        k = len(overlap)
        if k == 0:
            continue
        # P(X >= k)，X ~ Hypergeom(M, K, n)
        if _use_scipy:
            pval = float(hypergeom.sf(k - 1, M, K, n))
        else:
            # 简单近似：k/n vs K/M
            expected = n * K / M
            pval = max(1e-10, 1.0 - k / (expected + 1e-9)) if k > expected else 1.0

        raw_results.append({
            "pathway_id": path_id,
            "pathway_name": pathway_names.get(path_id, path_id),
            "hits": k,
            "pathway_size": K,
            "background_size": M,
            "sig_size": n,
            "rich_factor": round(k / K, 4) if K > 0 else 0,
            "gene_ratio": f"{k}/{n}",
            "bg_ratio": f"{K}/{M}",
            "pvalue": round(pval, 8),
            "hit_cpd_ids": sorted(overlap),
        })

    if not raw_results:
        return {
            "available": False,
            "reason": "未找到与显著差异特征相关的 KEGG 通路。",
            "pathways": [],
        }

    # BH-FDR
    pvals = [r["pvalue"] for r in raw_results]
    qvals = _bh_correct(pvals)
    for r, q in zip(raw_results, qvals):
        r["qvalue"] = q

    # 排序
    raw_results.sort(key=lambda x: (x["pvalue"], -x["hits"]))

    # 过滤 + 截断（宽松：qvalue < 0.2，若全无则展示全部）
    sig = [r for r in raw_results if r["qvalue"] < qvalue_cutoff]
    display = (sig if sig else raw_results)[:top_n]

    return {
        "available": True,
        "n_sig_features": n,
        "n_bg_features": M,
        "n_pathways_tested": len(raw_results),
        "n_sig_pathways": len(sig),
        "pathways": display,
    }


# --------------------------------------------------------------------------- #
# ECharts 网络图数据构建
# --------------------------------------------------------------------------- #

def build_network_data(
    enrichment_result: Dict[str, Any],
    cpd_ann_lookup: Dict[str, Dict[str, Any]],
    top_pathways: int = 10,
) -> Dict[str, Any]:
    """
    构建 ECharts force-directed graph 所需节点/边数据。

    节点类别：
      category 0 = 代谢物（蓝色小圆）
      category 1 = KEGG 通路（橙色大圆）
    """
    pathways = enrichment_result.get("pathways", [])[:top_pathways]
    if not pathways:
        return {"nodes": [], "edges": [], "categories": []}

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids: Set[str] = set()

    # -log10(qvalue) 范围，用于颜色映射
    max_neg_log = max(
        (-math.log10(max(r["qvalue"], 1e-10)) for r in pathways),
        default=1.0,
    )
    if max_neg_log <= 0:
        max_neg_log = 1.0   # 防止除以零

    for pw in pathways:
        pid = pw["pathway_id"]
        neg_log_q = -math.log10(max(pw["qvalue"], 1e-10))
        intensity = min(1.0, neg_log_q / max(max_neg_log, 1.0))
        # 通路节点大小与 hits 正相关
        sym_size = max(22, min(55, 14 + pw["hits"] * 4))
        if pid not in node_ids:
            nodes.append({
                "id": pid,
                "name": pw["pathway_name"],
                "category": 1,
                "symbolSize": sym_size,
                "value": pw["hits"],
                "label": {"show": True, "fontSize": 10},
                "_meta": {
                    "pathway_id": pid,
                    "hits": pw["hits"],
                    "pathway_size": pw["pathway_size"],
                    "pvalue": pw["pvalue"],
                    "qvalue": pw["qvalue"],
                    "rich_factor": pw["rich_factor"],
                    "intensity": round(intensity, 3),
                },
            })
            node_ids.add(pid)

        for cpd_id in pw.get("hit_cpd_ids", []):
            if cpd_id not in node_ids:
                ann = cpd_ann_lookup.get(cpd_id, {})
                met_name = ann.get("metabolite_name") or cpd_id
                nodes.append({
                    "id": cpd_id,
                    "name": met_name,
                    "category": 0,
                    "symbolSize": 9,
                    "value": 1,
                    "label": {"show": False},
                    "_meta": {
                        "cpd_id": cpd_id,
                        "formula": ann.get("formula"),
                        "metabolite_name": met_name,
                    },
                })
                node_ids.add(cpd_id)
            edges.append({
                "source": cpd_id,
                "target": pid,
                "lineStyle": {"opacity": 0.4, "width": 1},
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "categories": [
            {"name": "显著差异代谢物"},
            {"name": "KEGG 通路"},
        ],
    }


# --------------------------------------------------------------------------- #
# 主入口（缓存感知）
# --------------------------------------------------------------------------- #

def get_or_run_pathway_enrichment(
    pipeline_dir: Path,
    benchmark_merged_dir: Path,
    group1: str,
    group2: str,
    fc_threshold: float = 1.0,
    pvalue_threshold: float = 0.05,
    use_fdr: bool = True,
    top_n: int = 20,
) -> Dict[str, Any]:
    """
    主入口：从差异分析结果中提取显著特征，执行 KEGG 通路富集分析。

    流程
    ----
    1. 读取（或触发）差异分析缓存
    2. 从 annotated_feature_meta.json 中提取 KEGG ID 映射
    3. 调用 KEGG REST API 获取化合物-通路映射（有缓存则直接用）
    4. 超几何检验 + BH-FDR
    5. 构建 ECharts 网络图数据
    6. 写入缓存

    Returns
    -------
    dict 含 pathways（富集通路列表）和 network（ECharts 图数据）
    """
    # ---- 缓存键 ----
    cache_key = f"{group1}_vs_{group2}_fc{fc_threshold}_pv{pvalue_threshold}_fdr{use_fdr}"
    safe_key = hashlib.md5(cache_key.encode()).hexdigest()[:10]
    cache_path = pipeline_dir / "pathway_enrichment" / f"enrich_{safe_key}.json"

    if cache_path.is_file():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info("通路富集分析从缓存加载: %s", cache_path.name)
            return data
        except Exception:
            pass

    # ---- 读取差异分析结果 ----
    safe_g1 = group1.replace("/", "_").replace(" ", "_")
    safe_g2 = group2.replace("/", "_").replace(" ", "_")
    diff_path = pipeline_dir / "diff_analysis" / f"diff_{safe_g1}_vs_{safe_g2}.json"

    if diff_path.is_file():
        diff_result: Dict[str, Any] = json.loads(diff_path.read_text(encoding="utf-8"))
    else:
        # 触发差异分析
        from app.services.benchmark_merged_read import get_or_run_diff_analysis  # type: ignore
        diff_result = get_or_run_diff_analysis(
            group1=group1, group2=group2,
            fc_threshold=fc_threshold, pvalue_threshold=pvalue_threshold, use_fdr=use_fdr,
        )

    # ---- 加载注释数据 ----
    ann_path = pipeline_dir / "annotated_feature_meta.json"
    if not ann_path.is_file():
        raise FileNotFoundError("annotated_feature_meta.json 不存在，请先运行特征注释。")

    ann_data: Dict[str, Any] = json.loads(ann_path.read_text(encoding="utf-8"))
    ann_features: List[Dict[str, Any]] = ann_data.get("features", [])

    # feature_col -> [kegg_ids]
    feat_kegg: Dict[str, List[str]] = {}
    # cpd_id -> annotation dict（用于网络图节点名称）
    cpd_ann_lookup: Dict[str, Dict[str, Any]] = {}
    for f in ann_features:
        fc_name = str(f.get("feature_col", ""))
        kegg_ids: List[str] = f.get("kegg_ids") or []
        if kegg_ids:
            feat_kegg[fc_name] = kegg_ids
        for kid in kegg_ids:
            cpd_ann_lookup[kid] = {
                "metabolite_name": f.get("metabolite_name"),
                "formula": f.get("formula"),
            }

    # ---- 背景集与显著集 ----
    bg_cpd_ids: Set[str] = set()
    for kids in feat_kegg.values():
        bg_cpd_ids.update(kids)

    sig_labels = {"up", "down"}
    sig_cpd_ids: Set[str] = set()
    n_sig_total = 0
    for feat in diff_result.get("features", []):
        if feat.get("label") in sig_labels:
            n_sig_total += 1
            fc_name = str(feat.get("feature", ""))
            for kid in feat_kegg.get(fc_name, []):
                sig_cpd_ids.add(kid)

    logger.info(
        "通路富集：显著特征 %d 个（其中含 KEGG ID %d 个），背景 %d 个",
        n_sig_total, len(sig_cpd_ids), len(bg_cpd_ids),
    )

    # ---- KEGG 数据 ----
    cpd_pathway_map = load_or_fetch_compound_pathway_map(pipeline_dir)
    pathway_names = load_or_fetch_pathway_names(pipeline_dir)

    if not cpd_pathway_map:
        return {
            "available": False,
            "reason": "无法获取 KEGG 通路映射数据（请检查网络连接，或等待缓存就绪后重试）。",
            "pathways": [],
            "network": {"nodes": [], "edges": [], "categories": []},
            "group1": group1,
            "group2": group2,
        }

    # ---- 富集检验 ----
    result = run_pathway_enrichment(
        sig_cpd_ids=sig_cpd_ids,
        bg_cpd_ids=bg_cpd_ids,
        cpd_pathway_map=cpd_pathway_map,
        pathway_names=pathway_names,
        top_n=top_n,
    )

    # ---- ECharts 网络图 ----
    network = build_network_data(result, cpd_ann_lookup, top_pathways=min(10, top_n))
    result["network"] = network

    # 元信息
    result.update({
        "group1": group1,
        "group2": group2,
        "fc_threshold": fc_threshold,
        "pvalue_threshold": pvalue_threshold,
        "use_fdr": use_fdr,
        "n_sig_features_total": n_sig_total,
    })

    # ---- 写缓存 ----
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("通路富集分析结果已写入缓存: %s", cache_path.name)

    return result
