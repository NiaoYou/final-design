"""
generate_figures.py
====================
生成论文 V4 第四章所需的系统图：
  - 图 4-1 缺失值填充方法 RMSE / MAE / NRMSE 对比柱状图
  - 图 4-3 Benchmark 数据集批次质心距离校正前后对比柱状图
  - 图 4-4 P1_AA_0001 vs P1_AA_1024 差异代谢物火山图
  - 图 4-5 KEGG 通路富集气泡图
  - 图 4-7 BioHeart / MI / AMIDE 三数据集校正前后 PCA 拼图

输入数据均取自 backend/data/processed/.../_pipeline/ 下系统离线 Pipeline 产物。
输出图片统一写入 thesis/figures/system-generated/。
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------------------------------------------------------
# 路径配置
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data" / "processed"
OUT = ROOT / "thesis" / "figures" / "system-generated"
OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 字体与样式
# -----------------------------------------------------------------------------
plt.rcParams["font.sans-serif"] = ["Heiti TC", "Hiragino Sans GB", "PingFang SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False


# -----------------------------------------------------------------------------
# 图 4-1：缺失值填充方法对比柱状图
# -----------------------------------------------------------------------------
def fig_4_1_imputation_metrics_bar() -> None:
    src = DATA / "benchmark_merged" / "_pipeline" / "imputation_eval" / "imputation_eval_report.json"
    report = json.loads(src.read_text(encoding="utf-8"))
    methods_order = ["autoencoder", "knn", "mean", "median"]
    display = {"autoencoder": "Autoencoder", "knn": "KNN", "mean": "Mean", "median": "Median"}
    metrics = ["rmse", "mae", "nrmse"]
    metric_labels = ["RMSE", "MAE", "NRMSE"]

    means = np.array([[report["methods"][m][f"{k}_mean"] for k in metrics] for m in methods_order])
    stds = np.array([[report["methods"][m][f"{k}_std"] for k in metrics] for m in methods_order])

    n_methods, n_metrics = means.shape
    x = np.arange(n_metrics)
    width = 0.18
    colors = ["#3D5A80", "#98C1D9", "#E0FBFC", "#EE6C4D"]

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, m in enumerate(methods_order):
        offsets = (i - (n_methods - 1) / 2) * width
        bars = ax.bar(x + offsets, means[i], width, yerr=stds[i],
                      capsize=3, label=display[m], color=colors[i],
                      edgecolor="black", linewidth=0.6)
        for rect, v in zip(bars, means[i]):
            ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height(),
                    f"{v:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=11)
    ax.set_ylabel("误差值（越低越好）", fontsize=11)
    ax.set_title("图 4-1  缺失值填充方法定量评估对比（Benchmark, mask=15%, n_repeats=3）",
                 fontsize=12)
    ax.legend(loc="upper left", frameon=False, fontsize=10)
    ax.set_ylim(0, max(1.15, means.max() * 1.2))
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)

    out = OUT / "fig_4_1_imputation_metrics_bar.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[saved] {out}")


# -----------------------------------------------------------------------------
# 图 4-3：批次质心距离校正前后对比
# -----------------------------------------------------------------------------
def fig_4_3_centroid_distance_bar() -> None:
    src = DATA / "benchmark_merged" / "_pipeline" / "evaluation" / "evaluation_report.json"
    report = json.loads(src.read_text(encoding="utf-8"))

    methods = report.get("methods", {})
    # 三种"无校正"填充方法 + 两种校正方法
    keys = ["mean", "median", "knn", "combat", "baseline"]
    labels_disp = ["Mean\n(无校正)", "Median\n(无校正)", "KNN\n(无校正)",
                   "ComBat-like\n(校正后)", "Baseline\n(校正后)"]
    values = []
    for k in keys:
        v = methods.get(k, {}).get("metrics", {}).get("batch_centroid_separation_pc12") or 0.0
        values.append(v)

    colors = ["#EE6C4D", "#EE6C4D", "#EE6C4D", "#3D5A80", "#293241"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels_disp, values, color=colors, width=0.6,
                  edgecolor="black", linewidth=0.7)
    for rect, v in zip(bars, values):
        text = "≈ 0" if abs(v) < 1e-6 else f"{v:.3f}"
        ax.text(rect.get_x() + rect.get_width() / 2,
                rect.get_height() + max(values) * 0.02,
                text, ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylabel("批次质心平均成对距离（PC1-PC2 空间，越低越好）", fontsize=11)
    ax.set_title("图 4-3  Benchmark 批次质心距离：填充方法（无校正）vs 批次校正方法", fontsize=12)
    ax.set_ylim(0, max(values) * 1.2)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)

    out = OUT / "fig_4_3_benchmark_centroid_distance.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[saved] {out}")


# -----------------------------------------------------------------------------
# 图 4-4：差异代谢物火山图
# -----------------------------------------------------------------------------
def fig_4_4_volcano() -> None:
    src = DATA / "benchmark_merged" / "_pipeline" / "diff_analysis" / "diff_P1_AA_0001_vs_P1_AA_1024.json"
    diff = json.loads(src.read_text(encoding="utf-8"))
    feats = diff["features"]
    fc_thr = diff.get("fc_threshold", 1.0)
    p_thr = diff.get("pvalue_threshold", 0.05)

    log2fc = np.array([f["log2fc"] for f in feats], dtype=float)
    qvals = np.array([f["qvalue"] for f in feats], dtype=float)
    qvals = np.where(qvals <= 0, 1e-300, qvals)
    neg_log_q = -np.log10(qvals)

    up_mask = (log2fc >= fc_thr) & (qvals < p_thr)
    down_mask = (log2fc <= -fc_thr) & (qvals < p_thr)
    ns_mask = ~(up_mask | down_mask)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(log2fc[ns_mask], neg_log_q[ns_mask], s=8, c="#B0B0B0",
               alpha=0.55, label=f"不显著 ({ns_mask.sum()})")
    ax.scatter(log2fc[down_mask], neg_log_q[down_mask], s=10, c="#3D5A80",
               alpha=0.85, label=f"下调 ({down_mask.sum()})")
    ax.scatter(log2fc[up_mask], neg_log_q[up_mask], s=10, c="#EE6C4D",
               alpha=0.85, label=f"上调 ({up_mask.sum()})")

    ax.axvline(fc_thr, color="grey", linestyle="--", linewidth=0.7)
    ax.axvline(-fc_thr, color="grey", linestyle="--", linewidth=0.7)
    ax.axhline(-np.log10(p_thr), color="grey", linestyle="--", linewidth=0.7)

    # 先确定坐标范围（避免标注超出右边界）
    x_max = float(np.nanmax(np.abs(log2fc))) * 1.05
    ax.set_xlim(-x_max, x_max)
    ax.set_ylim(0, float(neg_log_q.max()) * 1.08)

    # top-N 标注：用 adjustText 库做迭代避让
    sig_idx = np.where(up_mask | down_mask)[0]
    if len(sig_idx):
        score = np.abs(log2fc[sig_idx]) * neg_log_q[sig_idx]
        top_local = sig_idx[np.argsort(score)[-6:]]  # 限制 6 个，避免过密

        def _short(name: str, n: int = 18) -> str:
            return name if len(name) <= n else name[: n - 1] + "…"

        try:
            from adjustText import adjust_text
        except ImportError:
            adjust_text = None  # type: ignore

        texts = []
        for i in top_local:
            name = feats[i].get("metabolite_name") or feats[i].get("feature")
            if not name:
                continue
            t = ax.text(log2fc[i], neg_log_q[i], _short(str(name)),
                        fontsize=8, ha="center", va="center",
                        bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                  ec="none", alpha=0.7))
            texts.append(t)

        if adjust_text is not None and texts:
            adjust_text(
                texts, ax=ax,
                expand=(1.2, 1.4),
                arrowprops=dict(arrowstyle="-", color="grey",
                                lw=0.5, alpha=0.7),
                only_move={"texts": "xy", "static": "xy", "explode": "xy"},
            )

    ax.set_xlabel("log2 Fold Change（P1_AA_1024 / P1_AA_0001）", fontsize=11)
    ax.set_ylabel(r"$-\log_{10}(q)$", fontsize=11)
    ax.set_title("图 4-4  P1_AA_0001 vs P1_AA_1024 差异代谢物火山图", fontsize=12)
    ax.legend(loc="upper left", frameon=False, fontsize=10)
    ax.grid(linestyle="--", linewidth=0.4, alpha=0.5)

    out = OUT / "fig_4_4_volcano_aa.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[saved] {out}")


# -----------------------------------------------------------------------------
# 图 4-5：KEGG 通路富集气泡图
# -----------------------------------------------------------------------------
def fig_4_5_kegg_bubble() -> None:
    enrich_dir = DATA / "benchmark_merged" / "_pipeline" / "pathway_enrichment"
    candidates = sorted(enrich_dir.glob("enrich_*.json"))
    if not candidates:
        print("[skip] no enrichment json found")
        return
    enrich = json.loads(candidates[0].read_text(encoding="utf-8"))
    pathways = enrich.get("pathways", [])
    if not pathways:
        print("[skip] no pathways in enrichment json")
        return

    pathways = sorted(pathways, key=lambda p: p.get("qvalue", 1.0))[:15]
    names = [p["pathway_name"] for p in pathways]
    rich = [p["rich_factor"] for p in pathways]
    hits = [p["hits"] for p in pathways]
    qvals = np.array([p["qvalue"] for p in pathways], dtype=float)
    qvals = np.where(qvals <= 0, 1e-300, qvals)
    neg_log_q = -np.log10(qvals)

    # 缩小气泡 size，避免遮挡坐标
    sizes = [max(60, h * 8) for h in hits]
    y_pos = np.arange(len(names))[::-1]

    n = len(names)
    fig, ax = plt.subplots(figsize=(9, max(3.2, 0.7 * n + 2.0)))
    sc = ax.scatter(rich, y_pos, s=sizes, c=neg_log_q, cmap="viridis",
                    edgecolor="black", linewidth=0.5, alpha=0.9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Rich Factor", fontsize=11)
    ax.set_title("图 4-5  KEGG 通路富集气泡图（P1_AA_0001 vs P1_AA_1024）", fontsize=12)
    ax.grid(axis="x", linestyle="--", linewidth=0.4, alpha=0.5)

    # 给 x 轴两端留出充足 margin，确保气泡不溢出
    rich_min, rich_max = float(min(rich)), float(max(rich))
    span = max(0.3, rich_max - rich_min)
    ax.set_xlim(max(0.0, rich_min - span * 0.4), min(1.05, rich_max + span * 0.25))

    # 给 y 轴顶部和底部留出空隙，避免气泡贴边
    ax.set_ylim(-0.8, n - 1 + 0.8)

    cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label(r"$-\log_{10}(q)$", fontsize=10)

    # 命中数图例（用实际数据范围内的代表值）
    h_min, h_max = int(min(hits)), int(max(hits))
    legend_hits = sorted(set([h_min, (h_min + h_max) // 2, h_max]))
    for h_demo in legend_hits:
        ax.scatter([], [], s=max(60, h_demo * 8), c="lightgrey",
                   edgecolor="black", label=f"hits = {h_demo}")
    ax.legend(loc="upper left", frameon=True, fontsize=9, scatterpoints=1,
              labelspacing=1.2, framealpha=0.85)

    out = OUT / "fig_4_5_kegg_enrichment_bubble.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[saved] {out}")


# -----------------------------------------------------------------------------
# 图 4-7：BioHeart / MI / AMIDE 三数据集 PCA 校正前后拼图
# -----------------------------------------------------------------------------
def fig_4_7_three_datasets_pca() -> None:
    """裁掉原图顶部含中文乱码的标题条，再用 matplotlib 拼接并加自有标题。"""
    import matplotlib.image as mpimg

    src_paths = [
        ("BioHeart", DATA / "bioheart" / "_pipeline" / "pca_before_vs_after_batch_correction.png"),
        ("MI", DATA / "mi" / "_pipeline" / "pca_before_vs_after_batch_correction.png"),
        ("AMIDE", DATA / "amide" / "_pipeline" / "pca_before_vs_after_batch_correction.png"),
    ]
    items = []
    # 经测量原图为 1320×1680，顶部约前 145px 含 "PCA before vs after..." 与 "(XX 数据集)" 两行标题
    crop_top_ratio = 0.115
    for label, path in src_paths:
        if not path.exists():
            print(f"[warn] missing source: {path}")
            continue
        img = mpimg.imread(path)
        h = img.shape[0]
        cropped = img[int(h * crop_top_ratio):, :]
        items.append((label, cropped))
    if not items:
        return

    target_w = 12  # inches
    panel_heights = []
    for _, img in items:
        h, w = img.shape[:2]
        panel_heights.append(target_w * h / w)
    total_h = sum(panel_heights) + 0.4 * len(items)

    fig, axes = plt.subplots(
        nrows=len(items), ncols=1,
        figsize=(target_w, total_h),
        gridspec_kw={"height_ratios": panel_heights, "hspace": 0.20},
    )
    if len(items) == 1:
        axes = [axes]

    for ax, (label, img) in zip(axes, items):
        ax.imshow(img)
        ax.set_title(f"{label} 数据集：校正前 vs 校正后（左：按批次着色；右：按分组着色）",
                     fontsize=13, pad=8)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.suptitle("图 4-7  BioHeart / MI / AMIDE 三数据集批次校正前后 PCA 对比",
                 fontsize=15, y=0.997)

    out = OUT / "fig_4_7_three_datasets_pca.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {out}")


# -----------------------------------------------------------------------------
# Entry
# -----------------------------------------------------------------------------
def main() -> None:
    fig_4_1_imputation_metrics_bar()
    fig_4_3_centroid_distance_bar()
    fig_4_4_volcano()
    fig_4_5_kegg_bubble()
    fig_4_7_three_datasets_pca()
    print("\nAll figures generated under:", OUT)


if __name__ == "__main__":
    main()
