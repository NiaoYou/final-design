# 论文图表总清单（共 21 张）

> 本清单跟踪 `thesis/THESIS_DRAFT_REVISED_V5.md` 中所有图占位的来源、状态与目标路径。
> 三个子目录约定：
> - `system-generated/`：由 `thesis/scripts/generate_figures.py` 直接从系统 Pipeline 产物生成
> - `external/`：需外部 AI 绘图工具（如 ChatGPT 画图、draw.io、PlantUML 等）绘制
> - `screenshots/`：用户在系统运行时手动截屏

| 图号 | 图名 | 类别 | 状态 | 文件路径 / 操作说明 |
| --- | --- | --- | --- | --- |
| 图 3-1 | Autoencoder 网络结构示意图 | external | 待绘制 | `external/fig_3_1_autoencoder_arch.png`，prompt 见 `external/figures-prompt.txt` |
| 图 3-2 | ComBat 安全封装异常降级流程图 | external | 待绘制 | `external/fig_3_2_combat_fallback_flow.png`，draw.io / Mermaid 流程图 |
| 图 3-3 | 四种缺失值填充方法的 RMSE / MAE / NRMSE 对比柱状图 | system | ✅ 已生成 | `system-generated/fig_3_3_imputation_metrics_bar.png` |
| 图 3-4 | Benchmark 数据集批次效应校正前后 PCA 对比 | system | ✅ 已生成 | `system-generated/fig_3_4_benchmark_pca_before_after.png` |
| 图 3-5 | Benchmark 数据集批次质心距离校正前后对比 | system | ✅ 已生成 | `system-generated/fig_3_5_benchmark_centroid_distance.png` |
| 图 3-6 | P1_AA_0001 vs P1_AA_1024 差异代谢物火山图 | system | ✅ 已生成 | `system-generated/fig_3_6_volcano_aa.png` |
| 图 3-7 | KEGG 通路富集气泡图 | system | ✅ 已生成 | `system-generated/fig_3_7_kegg_enrichment_bubble.png` |
| 图 3-8 | MetaKG 知识图谱代谢物-通路-酶力导向子图 | screenshots | ✅ 已截图 | `screenshots/fig_3_8_metakg_subgraph.png`，截图位置见 `external/figures-prompt.txt` |
| 图 3-9 | BioHeart / MI / AMIDE 三数据集批次校正前后 PCA 对比 | system | ✅ 已生成 | `system-generated/fig_3_9_three_datasets_pca.png` |
| 图 4-1 | 系统总体架构图（前后端分离） | external | 待绘制 | `external/fig_4_1_system_architecture.png`，draw.io |
| 图 4-2 | 后端四层分层架构图 | external | 待绘制 | `external/fig_4_2_backend_layers.png`，draw.io |
| 图 4-3 | 前端组件树与状态管理关系图 | external | 待绘制 | `external/fig_4_3_frontend_component_tree.png`，draw.io / Mermaid |
| 图 4-4 | 数据库 E-R 图 | external | 待绘制 | `external/fig_4_4_database_er.png`，draw.io |
| 图 4-5 | 系统数据流 Pipeline 示意图 | external | 待绘制 | `external/fig_4_5_pipeline_dataflow.png`，draw.io |
| 图 4-6 | 任务状态机示意图 | external | 待绘制 | `external/fig_4_6_task_state_machine.png`，draw.io / PlantUML |
| 图 4-7 | 首页 KPI 概览界面 | screenshots | ✅ 已截图 | `screenshots/fig_4_7_dashboard.png` |
| 图 4-8 | 数据导入与列名映射配置界面 | screenshots | ✅ 已截图 | `screenshots/fig_4_8_import_mapping.png` |
| 图 4-9 | PCA 校正前后对比可视化界面 | screenshots | ✅ 已截图 | `screenshots/fig_4_9_pca_compare.png` |
| 图 4-10 | 差异代谢物火山图与表格界面 | screenshots | ✅ 已截图 | `screenshots/fig_4_10_volcano_table.png` |
| 图 4-11 | KEGG 通路富集气泡图界面 | screenshots | ✅ 已截图 | `screenshots/fig_4_11_kegg_bubble.png` |
| 图 4-12 | MetaKG 力导向知识图谱与节点过滤面板 | screenshots | ✅ 已截图 | `screenshots/fig_4_12_metakg_force.png` |

## 进度统计
- **system-generated（已自动生成）**：6 / 6 张
- **external（待手绘）**：8 张
- **screenshots（已自动截图）**：7 / 7 张
- **总计**：21 张

## 重新生成系统图
```bash
python3 thesis/scripts/generate_figures.py
```
脚本读取 `backend/data/processed/.../_pipeline/` 下 JSON 产物，输出至 `thesis/figures/system-generated/`。

> **注意**：图 3-4（Benchmark PCA 对比）为系统 Pipeline 直接产出的 PNG，
> 路径为 `backend/data/processed/benchmark_merged/_pipeline/pca_before_vs_after_batch_correction.png`，
> 手动拷贝至 `system-generated/fig_3_4_benchmark_pca_before_after.png` 即可，无需脚本重绘。
