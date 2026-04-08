# 代谢组学 Web 平台 — 操作指南

> 适用范围：本地开发环境 / 答辩演示  
> 数据集：1715 样本 × 1180 特征 × 7 batches（benchmark_merged 固定数据集）  
> 最后更新：2026-04-08

---

## 目录

1. [环境准备](#1-环境准备)
2. [后端启动](#2-后端启动)
3. [前端启动](#3-前端启动)
4. [数据产物说明（首次使用必读）](#4-数据产物说明首次使用必读)
5. [核心功能演示路径](#5-核心功能演示路径)
6. [API 手动调用参考](#6-api-手动调用参考)
7. [常见问题排查](#7-常见问题排查)
8. [目录与文件速查](#8-目录与文件速查)

---

## 1. 环境准备

### 1.1 Python 环境（后端）

```bash
# 推荐 Python 3.9（项目使用 Optional[X] 兼容写法）
python3 --version    # 应输出 Python 3.9.x

# 在 backend/ 下安装依赖
cd backend
pip install -r requirements.txt
```

**核心依赖说明**：

| 包名 | 用途 |
|------|------|
| fastapi / uvicorn | REST API 框架与 ASGI 服务器 |
| sqlalchemy | ORM（SQLite） |
| pandas / numpy | 数据矩阵操作 |
| scikit-learn | KNN 填充、PCA、Silhouette |
| scipy / statsmodels | Welch t-test、BH-FDR |
| neuroCombat / pyComBat | ComBat 批次效应校正 |
| torch（CPU） | Autoencoder 深度学习填充 |
| requests | KEGG REST API 调用 |
| matplotlib | 服务端 PCA 图生成 |

> **注意**：`torch` CPU 版约 200 MB，安装较慢。若已有 GPU 版 torch 也可直接使用。

### 1.2 Node.js 环境（前端）

```bash
node --version    # 推荐 18.x 或 20.x
npm --version     # 推荐 9.x+
```

---

## 2. 后端启动

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

启动成功后终端输出：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

- **API 文档（Swagger UI）**：http://127.0.0.1:8000/docs
- **健康检查**：http://127.0.0.1:8000/api/benchmark/merged/summary

> `--reload` 模式下代码修改会自动重载，答辩演示建议去掉 `--reload` 以避免意外重启：
> ```bash
> uvicorn app.main:app --port 8000
> ```

---

## 3. 前端启动

```bash
cd frontend
npm install          # 首次运行或依赖变更后执行
npm run dev
```

启动成功后终端输出：
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

打开浏览器访问 **http://localhost:5173**

> Vite 已配置代理：所有 `/api/*` 请求自动转发到 `http://127.0.0.1:8000`，无需额外配置跨域。

---

## 4. 数据产物说明（首次使用必读）

本项目采用**预计算产物**方式演示，所有分析结果已提前运行并缓存在 `backend/data/processed/benchmark_merged/` 下。**正常演示无需重跑管线**。

### 4.1 产物目录结构

```
backend/data/processed/benchmark_merged/
├── merge_report.json                    # 合并摘要（样本数/特征数/batch分布）
├── merged_sample_by_feature.csv         # 原始合并矩阵（1715×1180）
├── merged_sample_meta.csv               # 样本元信息（batch_id/group_label）
└── _pipeline/
    ├── batch_corrected_sample_by_feature.csv   # baseline 批次校正后矩阵
    ├── batch_correction_method_report.json
    ├── batch_correction_metrics.json           # 校正前后指标对比
    ├── pca_before_vs_after_batch_correction.png
    ├── annotated_feature_meta.json             # 特征注释（1180个，100%覆盖）
    ├── imputation_eval/
    │   ├── imputation_eval_report.json         # 4方法RMSE对比，Autoencoder最优
    │   └── imputation_eval_feature.json        # per-feature RMSE
    ├── evaluation/
    │   ├── evaluation_report.json              # 5方法对比摘要
    │   ├── evaluation_table.csv
    │   ├── pca_before_vs_after.png
    │   └── pca_{mean,median,knn,baseline,combat}.json
    ├── diff_analysis/
    │   └── diff_{group1}_vs_{group2}.json      # 差异分析缓存（按组对）
    ├── kegg_cache/
    │   ├── compound_pathway_map.json           # KEGG化合物→通路映射（本地缓存）
    │   └── pathway_names.json                  # KEGG通路名称（本地缓存）
    └── pathway_enrichment/
        └── enrich_{params_hash}.json           # 通路富集结果（按参数缓存）
```

### 4.2 重新运行管线（可选）

**仅在需要重建产物时执行**（正常演示跳过此步）：

```bash
cd backend

# 完整重跑（含 Autoencoder 训练，约 5-10 分钟）
PYTHONPATH=. python3 app/scripts/run_merged_benchmark_pipeline.py

# 跳过耗时步骤（仅重跑批次校正/评估）
PYTHONPATH=. python3 app/scripts/run_merged_benchmark_pipeline.py \
    --skip-imputation-eval \
    --skip-evaluation
```

> **Autoencoder 填充**单次训练约 43 秒（CPU），若机器配置较低建议使用 `--skip-imputation-eval`。

### 4.3 KEGG 缓存说明

首次调用通路富集 API 时，系统会自动从 KEGG REST API 下载化合物-通路映射（约 10-30 秒，取决于网络），下载完成后缓存到 `kegg_cache/`，后续调用直接读本地缓存，秒级响应。

若 `kegg_cache/` 目录已存在（项目已预缓存），则首次调用也是秒级。

---

## 5. 核心功能演示路径

### 5.1 首页概览

**访问** http://localhost:5173/

页面展示：
- 9 张技术亮点卡（3×3 布局）：数据合并、批次校正、Autoencoder填充、方法对比、差异分析、特征注释、KEGG通路富集等
- 系统处理流程（5步）：导入 → 预处理 → 填充 → 批次校正 → 分析
- 快捷入口按钮

### 5.2 结果仪表盘（核心演示页）

**访问** http://localhost:5173/result

页面从上到下依次展示以下区块：

#### ① KPI 统计卡
- 样本数：1715，特征数：1180，Batch 数：7，缺失率：0%

#### ② PCA 可视化
- 四宫格图（校正前/后 × 按batch着色/按group着色）
- 解释方差柱图（PC1-PC5 贡献比）

#### ③ 批次校正指标对比
- 校正前后 batch centroid separation、Silhouette 数值对比

#### ④ 缺失值填充评估
- 4 方法 RMSE 对比箱线图（Autoencoder 紫色标注为"深度学习"，RMSE=0.2249 最优）
- 配置信息：mask_ratio=15%，重复次数=3，ae_epochs=200

#### ⑤ 差异代谢物分析
1. 在组别选择器中选择 **group1 = P1_AA_0001**，**group2 = P1_AA_1024**
2. 点击"运行差异分析"
3. 火山图加载（首次约 2-5 秒，结果缓存后秒级）
4. 显著代谢物：538 个（|log2FC|≥1，q≤0.05）
5. 火山图点可悬浮查看代谢物名、m/z、HMDB/KEGG 链接

#### ⑥ 通路富集分析
1. 在组别选择器中选择同上（P1_AA_0001 vs P1_AA_1024）
2. 参数默认：FC阈值=1，p-value阈值=0.05，使用FDR，展示Top 20
3. 点击"运行富集分析"
4. 气泡图加载（首次调用含 KEGG 网络请求，约 10-30 秒；命中缓存秒级）
5. 切换"网络图"Tab 查看力导向代谢物-通路网络图（可拖拽节点）
6. 明细表：D-氨基酸代谢（map00470）RichFactor=0.968，q=0.0002

#### ⑦ MetaKG 知识图谱溯源
- 图表自动加载（2.6 MB 子图，首次约 1-2 秒）
- 展示 977 个代谢物（蓝色圆点）与 7,866 个实体的关系网络
- 控制面板：按节点类型（代谢物/通路/反应/酶）和关系类型过滤
- 搜索框输入代谢物名（如 "Alanine"）可高亮定位节点（黄色）
- 开启"仅展示代谢物直连节点"可聚焦代谢物-酶/通路直接关系
- 拖拽节点 / 滚轮缩放交互

#### ⑧ 特征注释
- 分页表格：1180 个特征，全部含 HMDB ID，577 个含 KEGG ID
- 支持代谢物名 / 分子式 / KEGG ID 关键词搜索
- 点击 HMDB/KEGG 链接可跳转外部数据库

#### ⑧ 方法对比实验
- 5 方法评估表（baseline/combat/knn/mean/median 的 Silhouette 和 centroid separation）
- PCA 对比图

### 5.3 数据导入流程（可选演示）

**访问** http://localhost:5173/import

1. 上传 Excel 文件（位于 `backend/data/raw/benchmark/` 下的任一 `.xlsx`）
2. 系统解析 sheet 结构并返回 task_id
3. 跳转配置页（`/config`）可选择预处理/填充/批次校正参数

> 注意：通用任务链产物存储在 `backend/data/uploads/` 和 `backend/data/results/`，与 benchmark_merged 固定数据集相互独立。

### 5.4 历史任务

**访问** http://localhost:5173/history

查看历史上传/分析任务记录（SQLite 持久化）。

---

## 6. API 手动调用参考

后端启动后可通过 Swagger UI（http://127.0.0.1:8000/docs）交互调用，以下为常用端点速查：

### 6.1 合并数据摘要

```bash
curl http://127.0.0.1:8000/api/benchmark/merged/summary
```

返回示例：
```json
{
  "n_samples": 1715,
  "n_features": 1180,
  "n_batches": 7,
  "missing_rate": 0.0
}
```

### 6.2 差异代谢物分析

```bash
curl -X POST http://127.0.0.1:8000/api/benchmark/merged/diff-analysis/run \
  -H "Content-Type: application/json" \
  -d '{"group1": "P1_AA_0001", "group2": "P1_AA_1024", "fc_threshold": 1.0, "pvalue_threshold": 0.05}'
```

### 6.3 通路富集分析

```bash
curl "http://127.0.0.1:8000/api/benchmark/merged/pathway-enrichment?\
group1=P1_AA_0001&group2=P1_AA_1024&fc_threshold=1.0&pvalue_threshold=0.05&use_fdr=true&top_n=20"
```

返回关键字段：
```json
{
  "pathways": [
    {
      "pathway_id": "map00470",
      "pathway_name": "D-Amino acid metabolism",
      "hits": 30,
      "pathway_size": 31,
      "rich_factor": 0.968,
      "pvalue": 1.2e-05,
      "qvalue": 0.0002
    }
  ],
  "bubble_chart": { ... },
  "network": { "nodes": [...], "edges": [...] }
}
```

### 6.4 填充评估摘要

```bash
curl http://127.0.0.1:8000/api/benchmark/merged/imputation-eval/summary
```

### 6.5 特征注释（分页）

```bash
# 第1页，每页20条，关键词搜索
curl "http://127.0.0.1:8000/api/benchmark/merged/annotation/features?page=1&page_size=20&keyword=Alanine"
```

---

## 7. 常见问题排查

### Q1：前端页面加载空白 / 数据不显示

**检查**：
1. 后端是否正常运行：`curl http://127.0.0.1:8000/api/benchmark/merged/summary`
2. 前端控制台（F12）是否有网络请求报错
3. Vite 代理是否正常：查看 `frontend/vite.config.ts` 中 proxy 配置

```ts
// vite.config.ts 中应有：
proxy: {
  '/api': 'http://127.0.0.1:8000'
}
```

### Q2：通路富集分析加载超时

**原因**：首次调用需从 KEGG REST API 下载化合物-通路映射（约 10-30 秒）。

**解决**：
- 等待首次下载完成（页面 Loading 状态），之后命中本地缓存
- 如网络不通，检查 `backend/data/processed/benchmark_merged/_pipeline/kegg_cache/` 目录是否有预缓存文件

### Q3：后端启动失败 / ModuleNotFoundError

```bash
# 确认在 backend/ 目录下运行
cd backend
pip install -r requirements.txt

# 如果 neuroCombat 安装失败
pip install neuroCombat
# 或
pip install pyComBat
```

### Q4：torch 相关错误

```bash
# 安装 CPU 版 PyTorch（约 200 MB）
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Q5：SQLite 数据库错误

```bash
# 重建数据库（会清空历史任务记录）
rm backend/data/app.sqlite3
# 重启后端后自动重建
```

### Q6：差异分析返回 422 错误

常见原因：group1 和 group2 相同，或输入的组名不在 60 个组中。

有效组名示例：`P1_AA_0001`、`P1_AA_1024`、`P2_AICAR_0001`（格式：`P{n}_{物质}_{浓度}`）。

可通过以下接口获取全部有效组名：
```bash
curl http://127.0.0.1:8000/api/benchmark/merged/diff-analysis/groups
```

---

## 8. 目录与文件速查

### 关键后端文件

| 文件 | 说明 |
|------|------|
| `backend/app/main.py` | FastAPI 应用入口，挂载所有路由 |
| `backend/app/api/routes/benchmark_merged.py` | Benchmark Merged 专用 20 个 REST 端点 |
| `backend/app/services/benchmark_merged_read.py` | 只读数据聚合层（读取 _pipeline/ 各 JSON/CSV） |
| `backend/app/services/differential_analysis_service.py` | Welch t-test + BH-FDR + log2FC |
| `backend/app/services/annotation_service.py` | m/z 精确质量匹配注释 |
| `backend/app/services/pathway_enrichment_service.py` | 超几何检验 + KEGG REST API 缓存 |
| `backend/app/services/imputation_service.py` | mean/median/KNN/Autoencoder 填充 |
| `backend/app/scripts/run_merged_benchmark_pipeline.py` | 一键重跑全分析管线 |
| `backend/requirements.txt` | Python 依赖列表 |

### 关键前端文件

| 文件 | 说明 |
|------|------|
| `frontend/src/views/ResultDashboardView.vue` | 结果仪表盘主页面（组合所有子组件） |
| `frontend/src/views/HomeView.vue` | 首页（9 张技术亮点卡） |
| `frontend/src/components/PathwayEnrichmentCard.vue` | 通路富集气泡图 + 网络图 + 明细表 |
| `frontend/src/components/VolcanoPlotCard.vue` | 差异分析火山图 |
| `frontend/src/components/ImputationEvalCard.vue` | 填充评估 RMSE 对比箱线图 |
| `frontend/src/components/AnnotationTableCard.vue` | 特征注释分页表格 |
| `frontend/src/api/benchmark.ts` | 所有 benchmark 相关 API 请求函数 |
| `frontend/src/stores/benchmark.ts` | Pinia 状态管理（数据缓存） |
| `frontend/vite.config.ts` | Vite 配置（含 /api 代理） |

---

## 附：快速启动命令汇总

```bash
# ── 终端 1：后端 ──
cd /path/to/final-design/backend
pip install -r requirements.txt   # 首次或更新依赖时
uvicorn app.main:app --port 8000

# ── 终端 2：前端 ──
cd /path/to/final-design/frontend
npm install                        # 首次或更新依赖时
npm run dev

# ── 浏览器 ──
# 首页：    http://localhost:5173/
# 结果页：  http://localhost:5173/result
# API文档： http://127.0.0.1:8000/docs
```
