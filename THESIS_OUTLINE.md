# 毕业论文大纲

**题目**：基于深度学习的代谢组学批次效应系统设计与开发  
**学生**：高云端  
**预计总字数**：2.5～3万字  

---

## 摘要

- **中文摘要**（300字左右）
  - 研究背景：代谢组学批次效应问题的挑战
  - 主要工作：系统设计与实现，重点算法（Autoencoder + ComBat）
  - 创新点：Mask-then-Impute 评估框架、深度学习填充与传统方法对比、下游分析与知识图谱一体化
  - 实验结论：关键指标数值（RMSE 对比、Silhouette 系数改善）
  - 关键词：代谢组学、批次效应、缺失值填充、深度学习、自动编码器、Web 平台

- **英文摘要**（Abstract，与中文对应）
  - Keywords: Metabolomics, Batch Effect, Missing Value Imputation, Deep Learning, Autoencoder, Web Platform

---

## 第一章 绪论

### 1.1 研究背景与意义
- 代谢组学的发展及其在疾病研究中的重要地位
- 大规模代谢组学实验中批次效应问题的普遍性与危害
  - 批次效应的定义：不同批次间系统性偏差（仪器、时间、人员差异）
  - 危害：掩盖真实生物学差异，影响差异代谢物筛选和通路分析可靠性
- 缺失值问题的来源与影响（检测灵敏度限制、信号噪声）
- 现有工具的局限性（MetaboAnalyst 等平台缺乏深度学习方法和一体化分析流程）
- 研究意义：开发集成化 Web 平台，提升代谢组学数据分析效率和可用性

### 1.2 国内外研究现状
- **1.2.1 代谢组学数据分析研究现状**
  - 主流分析平台（MetaboAnalyst、XCMS 等）及其功能特点
  - 现有平台在批次效应处理上的局限
- **1.2.2 缺失值填充方法研究**
  - 传统方法：均值/中位数填充、KNN 填充
  - 深度学习方法：Denoising Autoencoder（MIDA，Gondara & Wang, 2018）
- **1.2.3 批次效应校正方法研究**
  - 统计类方法：ComBat（Johnson et al., 2007）、均值方差归一化
  - 低维对齐类方法：Harmony
  - 深度学习类方法：基于神经网络的批次去除
- **1.2.4 代谢组学下游分析研究**
  - 差异代谢物分析方法（t-test、方差分析）
  - KEGG 通路富集分析
  - 知识图谱在生物数据中的应用

### 1.3 本文主要工作
- 设计并实现了代谢组学数据处理 Web 平台（前后端分离架构）
- 实现了基于 Autoencoder 的深度学习缺失值填充方法，并设计 Mask-then-Impute 评估框架
- 集成了 baseline 逐特征位置尺度对齐和 ComBat 经验 Bayes 两种批次效应校正方法
- 实现了差异代谢物分析、KEGG 通路富集分析和 MetaKG 知识图谱溯源展示

### 1.4 论文组织结构
- 各章节内容简要说明（第二章至第六章）

---

## 第二章 相关技术与方法综述

### 2.1 代谢组学数据特点与预处理需求
- 数据矩阵结构（样本 × 特征，高维小样本特点）
- 数据质量问题：批次效应、缺失值、异常值、量纲差异
- 预处理的必要性与流程概述

### 2.2 缺失值填充方法
- **2.2.1 传统统计填充方法**
  - 均值/中位数填充：原理、适用场景、局限（破坏分布结构）
  - KNN 填充：原理（以邻近样本估计）、sklearn 实现、计算复杂度
- **2.2.2 深度学习填充方法**
  - Autoencoder 基本原理（编码-解码架构，无监督特征学习）
  - Masked Reconstruction 训练策略（仅对已知位置计算损失）
  - 与传统方法的对比优势（能捕获特征间复杂相关结构）
- **2.2.3 各方法适用场景分析**
  - 小样本场景下各方法的性能权衡

### 2.3 批次效应校正方法
- **2.3.1 逐特征位置尺度对齐方法**
  - 原理：将各批次的特征均值/标准差归一化到全局分布
  - 公式推导
  - 适用范围与局限（忽略生物学协变量）
- **2.3.2 ComBat 经验 Bayes 方法**
  - 算法背景（Johnson et al., 2007, Biostatistics）
  - 基本原理：线性模型分解 + 经验 Bayes 参数收缩
  - 经验 Bayes 的优势：改善小样本场景的参数估计稳定性
  - 生物学协变量的保护机制
- **2.3.3 方法对比**
  - 两种方法在校正能力、计算复杂度、适用场景上的对比

### 2.4 批次效应评估指标
- **2.4.1 PCA 降维可视化**
  - PCA 原理（主成分分析）
  - 在批次效应可视化中的应用
- **2.4.2 Silhouette 系数**
  - 定义：簇内紧密度 a(i) 与簇间分离度 b(i)
  - 公式：s(i) = (b(i) − a(i)) / max(a(i), b(i))
  - 双指标设计：Silhouette(batch_id) 与 Silhouette(group_label) 的相互制衡
- **2.4.3 批次质心距离**
  - 定义：PCA 空间中各批次样本质心间的平均欧氏距离
  - 与 Silhouette 的互补关系

### 2.5 本章小结
- 现有方法的不足与本文的改进思路

---

## 第三章 系统总体设计

### 3.1 系统需求分析
- **3.1.1 功能需求**
  - 数据上传与管理（CSV/XLSX 格式支持）
  - 参数可配置的预处理流程
  - 多方法缺失值填充（含深度学习方法）
  - 多方法批次效应校正与对比评估
  - 差异代谢物分析与通路富集分析
  - 知识图谱溯源展示
  - 结果可视化与文件下载
- **3.1.2 非功能需求**
  - 可用性：Web 界面友好，无需编程背景
  - 可扩展性：模块化设计，便于新增算法
  - 可靠性：异常处理，失败不中断整体流程

### 3.2 系统总体架构
- **3.2.1 前后端分离架构概述**
  - 前端：Vue3 + TypeScript + Element Plus + ECharts
  - 后端：Python + FastAPI + SQLite + SQLAlchemy
  - 算法服务层：独立 `algorithms/` 模块
- **3.2.2 系统架构图**（图 3-1）
  - 前端展示层 → HTTP/REST → 后端 API 层 → Service 层 → Algorithm 层
- **3.2.3 分层架构设计原则**
  - api/routes（接口层）→ services（业务逻辑层）→ algorithms（纯算法层）→ repositories（数据访问层）

### 3.3 数据库设计
- **3.3.1 数据库选型说明**（SQLite，轻量单机部署）
- **3.3.2 表结构设计**
  - Task 表：task_id、状态、参数配置 JSON、创建时间
  - Dataset 表：数据集路径、格式、列名映射
  - Result 表：结果文件路径、metrics JSON
- **3.3.3 ER 图**（图 3-2）
- **3.3.4 文件系统与数据库的分工**（矩阵数据存文件，元数据存库）

### 3.4 模块划分
- **3.4.1 数据管理模块**：上传、解析、格式标准化
- **3.4.2 预处理模块**：log 变换、标准化、缺失率过滤
- **3.4.3 缺失值填充模块**：多策略、参数可配置
- **3.4.4 批次效应校正模块**：两种方法 + 安全封装
- **3.4.5 评估可视化模块**：指标计算 + 图表生成
- **3.4.6 下游分析模块**：差异分析 + 通路富集 + 知识图谱

### 3.5 系统整体数据流
- 从数据上传到结果展示的完整数据流图（图 3-3）
- 中间产物的格式与持久化策略

### 3.6 本章小结

---

## 第四章 核心算法设计与实现

### 4.1 数据预处理算法
- **4.1.1 缺失率过滤**
  - 阈值设定（默认 50%）与过滤逻辑
- **4.1.2 log1p 变换**
  - 目的：压缩右偏分布，减少极端值影响
  - 公式：x' = log(1 + x)
- **4.1.3 Z-score 标准化**
  - 公式：x' = (x − μ) / σ（按样本维度计算）
  - 标准差为 0 时的处理（替换为 1.0）

### 4.2 缺失值填充算法

#### 4.2.1 传统填充方法
- 均值填充（Mean Imputation）
- 中位数填充（Median Imputation）
- KNN 填充：sklearn KNNImputer，k=5（默认），矩阵转置处理说明

#### 4.2.2 基于 Autoencoder 的深度学习填充
- **网络结构**
  - Encoder：Linear(n_features → 256) → ReLU → BatchNorm → Dropout(0.1) → Linear(256 → 64) → ReLU
  - Decoder：Linear(64 → 256) → ReLU → BatchNorm → Linear(256 → n_features)
  - 网络结构图（图 4-1）
- **训练策略：Masked Reconstruction**
  - 缺失位置初始化为列均值，作为网络初始输入
  - 损失函数：仅对已知值位置计算 MSE
  - 公式：$L = \frac{\sum_{i,j} (x_{ij} - \hat{x}_{ij})^2 \cdot m_{ij}}{\sum_{i,j} m_{ij}}$，其中 $m_{ij}=1$ 表示已知值
  - 参考方法：MIDA（Gondara & Wang, 2018）
- **训练配置**
  - 优化器：Adam（lr=1e-3，weight_decay=1e-5）
  - 学习率调度：CosineAnnealingLR（eta_min = lr × 0.1）
  - 训练轮数：80 epochs
- **推断阶段**：用训练好的模型预测缺失位置的值

#### 4.2.3 Mask-then-Impute 评估框架
- 框架设计原理（图 4-2）
  1. 在已完整填充的矩阵上，随机遮蔽 15% 值为 NaN
  2. 四种方法分别填充遮蔽位置
  3. 与真值对比计算误差指标
  4. 多次重复取均值
- 评估指标定义
  - RMSE（均方根误差）
  - MAE（平均绝对误差）
  - NRMSE（标准化 RMSE，便于跨数据集对比）

### 4.3 批次效应校正算法

#### 4.3.1 Baseline 逐特征位置尺度对齐
- 算法原理：对每个特征 j 独立进行批次间均值/标准差对齐
- 公式推导：
  - 计算全局均值 $\mu_j$ 和全局标准差 $\sigma_j$
  - 对批次 b 中样本 i：$x'_{ij} = \frac{x_{ij} - \mu_{bj}}{\sigma_{bj}} \cdot \sigma_j + \mu_j$
- 适用条件与限制（忽略生物学协变量，批次 < 2 个样本时退化处理）

#### 4.3.2 ComBat 经验 Bayes 校正
- 算法背景与原理概述（Johnson et al., 2007）
- 线性模型分解：$Y_{ijg} = \alpha_g + X\beta_g + \gamma_{ig} + \delta_{ig}\varepsilon_{ijg}$
- 经验 Bayes 的作用：通过汇集所有特征的信息改善单特征参数估计的稳定性
- 生物学协变量保护机制
- 工程封装：安全封装 `run_combat_safe`，失败不中断流程

#### 4.3.3 批次效应校正评估指标
- 批次质心距离：各批次 PCA 空间质心间平均欧氏距离
- Silhouette(batch_id)：以批次标签计算，越低越好（批次难以区分）
- Silhouette(group_label)：以生物分组标签计算，越高越好（生物信号保留）
- 双指标相互制衡的意义：防止过度校正破坏生物学信号

### 4.4 下游分析算法

#### 4.4.1 差异代谢物分析
- 独立双样本 t-test（scipy.stats.ttest_ind）
- Log2 Fold Change 计算（含符号处理，避免 log(0)）
- BH-FDR 多重检验校正（statsmodels.stats.multitest）
- 显著性判断阈值：q-value < 0.05，|log2FC| > 1

#### 4.4.2 KEGG 通路富集分析
- 背景集：含 KEGG Compound ID 注释的全部特征
- 显著集：差异分析结果中 label ∈ {上调, 下调} 的代谢物
- 超几何检验原理与公式
- BH-FDR 多重校正
- KEGG REST API 数据获取与本地缓存策略

#### 4.4.3 MetaKG 知识图谱溯源
- MetaKG 多库整合数据来源（KEGG / SMPDB / HMDB）
- 子图提取策略：以差异代谢物为起点提取一跳关联子图
- 节点类型：代谢物、通路、反应、酶、基因、疾病

### 4.5 本章小结

---

## 第五章 系统实现与展示

### 5.1 开发环境与技术栈
- 后端：Python 3.x、FastAPI、SQLAlchemy、neuroCombat、PyTorch、scikit-learn、scipy
- 前端：Node.js、Vue3、TypeScript、Vite、Element Plus、ECharts
- 开发工具：VSCode、Git

### 5.2 后端关键实现

#### 5.2.1 API 接口设计
- RESTful 接口规范
- 主要接口列表（上传、预处理、填充、校正、评估、下游分析）
- 统一响应格式与错误处理

#### 5.2.2 数据处理 Pipeline 实现
- 多批次数据合并逻辑（格式标准化、批次标签对齐）
- 任务状态机设计（idle → preprocess_done → impute_done → correct_done）
- 中间产物文件管理策略

#### 5.2.3 算法集成实现
- algorithms 模块的独立性设计
- ComBat 安全封装的实现细节
- Autoencoder 离线 Pipeline 的设计考量

### 5.3 前端关键实现

#### 5.3.1 组件架构设计
- 15 个功能组件的职责划分
- Pinia 状态管理（benchmark store / task store）

#### 5.3.2 数据可视化实现
- PCA 散点图（批次效应校正前后对比）
- 缺失值填充方法 RMSE 对比图（ImputationEvalCard）
- 火山图（VolcanoPlotCard）：横轴 log2FC、纵轴 -log10(q-value)
- 通路富集气泡图（PathwayEnrichmentCard）
- MetaKG 知识图谱力导向图（MetaKGCard）：节点拖拽、关键词搜索、类型过滤

#### 5.3.3 多数据集支持实现
- DatasetSelector 组件
- benchmark / bioheart / mi / amide 四数据集的差异化处理逻辑

### 5.4 系统界面展示
- 首页 KPI 概览（图 5-1）
- 数据导入页（图 5-2）
- 参数配置与任务运行页（图 5-3）
- 结果展示页——PCA 对比图（图 5-4）
- 结果展示页——填充方法评估（图 5-5）
- 结果展示页——火山图（图 5-6）
- 结果展示页——通路富集气泡图（图 5-7）
- 结果展示页——MetaKG 知识图谱（图 5-8）

### 5.5 系统测试
- **5.5.1 功能测试**：各模块主链路测试覆盖情况
- **5.5.2 边界情况测试**：小批次数据（ComBat 降级）、高缺失率特征过滤、无注释特征（AMIDE 数据集）的提示处理
- **5.5.3 多数据集测试**：四个数据集完整 pipeline 运行结果

### 5.6 本章小结

---

## 第六章 实验与结果分析

### 6.1 实验数据集说明
| 数据集 | 样本数 | 特征数 | 批次数 | 用途 |
|--------|--------|--------|--------|------|
| Benchmark | 1715 | 1180 | 7 | 批次效应校正主验证集 |
| BioHeart | — | 53 | — | 下游分析链路验证 |
| MI | — | 14 | — | 下游分析链路验证 |
| AMIDE | — | 6461 | — | 系统通用性验证（无注释场景） |

### 6.2 缺失值填充方法对比实验

#### 6.2.1 实验设置
- 数据集：Benchmark（合并后矩阵）
- Mask-then-Impute 框架参数：遮蔽比例 15%，重复次数 N 次
- 对比方法：Mean / Median / KNN（k=5）/ Autoencoder

#### 6.2.2 实验结果
- 四种方法的 RMSE / MAE / NRMSE 对比表（表 6-1）
- 特征级 RMSE 分布箱线图（图 6-1）

#### 6.2.3 结果分析
- 各方法性能分析（Autoencoder 在特征相关结构复杂时的优势）
- 小样本场景下深度学习方法的局限性讨论
- 最优方法的选择依据

### 6.3 批次效应校正对比实验

#### 6.3.1 实验设置
- 数据集：Benchmark（7批次合并）
- 对比方法：无校正（仅填充）/ Baseline / ComBat

#### 6.3.2 实验结果
- 校正前后 PCA 散点图对比（图 6-2）
- 三指标对比表（表 6-2）：

| 方法 | 批次质心距离 | Silhouette(batch_id) | Silhouette(group_label) |
|------|------------|---------------------|------------------------|
| 无校正 | — | — | — |
| Baseline | — | — | — |
| ComBat | — | — | — |

#### 6.3.3 结果分析
- 各方法校正效果对比分析
- 双指标相互制衡的体现（过度校正与校正不足的权衡）
- ComBat vs Baseline 的适用场景讨论

### 6.4 下游分析结果展示

#### 6.4.1 差异代谢物分析结果
- Benchmark 数据集火山图展示（图 6-3）
- 显著差异代谢物数量统计（上调 N 个，下调 M 个）

#### 6.4.2 通路富集分析结果
- 富集通路列表（top 10 通路，表 6-3）
- 富集气泡图（图 6-4）

#### 6.4.3 知识图谱溯源展示
- MetaKG 子图统计（节点数、边数、关系类型分布）
- 知识图谱交互界面截图（图 6-5）

### 6.5 系统通用性验证
- BioHeart / MI 数据集的完整流程运行结果简述
- AMIDE 数据集的降级处理验证（提示无法做通路分析，不报错）

### 6.6 本章小结

---

## 第七章 结论与展望

### 7.1 研究总结
- 本文设计并实现了"基于深度学习的代谢组学批次效应处理 Web 平台"
- 核心成果回顾：
  1. 前后端分离的集成化 Web 平台，支持代谢组学数据全流程分析
  2. 基于 Masked Reconstruction Autoencoder 的深度学习缺失值填充方法
  3. Mask-then-Impute 可量化评估框架，支持多方法客观对比
  4. 集成 baseline 和 ComBat 两种批次效应校正方法，双指标评估体系
  5. 差异代谢物分析 + KEGG 通路富集 + MetaKG 知识图谱溯源一体化

### 7.2 系统局限性
- Autoencoder 未集成到 Web 在线任务流（当前为离线预计算）
- 批次效应校正方法数量有限（未集成 Harmony、BBKNN 等方法）
- 当前不支持多用户认证和数据隔离
- 部分数据集依赖手动运行 CLI 脚本生成产物

### 7.3 未来工作展望
- 引入异步任务队列（Celery + Redis），支持 Autoencoder 在线训练
- 扩展批次效应校正方法（Harmony、深度学习类方法）
- 实现自动化参数推荐（基于数据特征自动选择最优方法）
- 支持多组学联合分析（蛋白质组、转录组）
- 增加 PDF 报告自动生成功能

---

## 参考文献

> 按 GB/T 7714-2015 格式排列，预计 20-30 篇

1. Johnson W E, Li C, Rabinovic A. Adjusting batch effects in microarray expression data using empirical Bayes methods[J]. Biostatistics, 2007, 8(1): 118-127.
2. Gondara L, Wang K. MIDA: Multiple imputation using denoising autoencoders[C]. Pacific-Asia Conference on Knowledge Discovery and Data Mining, 2018.
3. Pang Z, Chong J, Zhou G, et al. MetaboAnalyst 5.0: narrowing the gap between raw spectra and functional insights[J]. Nucleic Acids Research, 2021.
4. Korsunsky I, Millard N, Fan J, et al. Fast, sensitive and accurate integration of single-cell data with Harmony[J]. Nature Methods, 2019.
5. Kanehisa M, Goto S. KEGG: Kyoto encyclopedia of genes and genomes[J]. Nucleic Acids Research, 2000.
6. （其余文献根据论文正文引用补全）

---

## 附录

### 附录 A：系统主要 API 接口列表
- 接口名称、请求方法、请求参数、响应格式

### 附录 B：实验数据集详细说明
- 各数据集的原始来源、格式、预处理参数

### 附录 C：核心算法伪代码
- Autoencoder 训练流程伪代码
- Mask-then-Impute 评估框架伪代码
- Baseline 批次校正伪代码

---

## 写作进度跟踪

| 章节 | 预计字数 | 状态 |
|------|---------|------|
| 摘要（中英文） | 600字 | ⬜ 未开始 |
| 第一章 绪论 | 3000字 | ⬜ 未开始 |
| 第二章 相关技术综述 | 4000字 | ⬜ 未开始 |
| 第三章 系统总体设计 | 4000字 | ⬜ 未开始 |
| 第四章 核心算法设计与实现 | 6000字 | ⬜ 未开始 |
| 第五章 系统实现与展示 | 4000字 | ⬜ 未开始 |
| 第六章 实验与结果分析 | 4000字 | ⬜ 未开始 |
| 第七章 结论与展望 | 1500字 | ⬜ 未开始 |
| 参考文献 | — | ⬜ 未开始 |
| 附录 | 1500字 | ⬜ 未开始 |
| **合计** | **~29000字** | — |

> 状态标记：⬜ 未开始 / 🟨 进行中 / ✅ 已完成 / 🔄 修改中
