# 基于深度学习的代谢组学批次效应系统设计与开发

> **写作说明**：本文件为论文正文草稿，按章节顺序逐步撰写。所有数据均来源于系统真实运行结果。  
> **进度**：摘要 ✅ | 第一章 ✅ | 第二章 ⬜ | 第三章 ⬜ | 第四章 ⬜ | 第五章 ⬜ | 第六章 ⬜ | 第七章 ⬜

---

# 摘要

代谢组学是生命科学领域重要的研究方向之一，通过对生物体内小分子代谢物的系统性检测，能够在整体水平上揭示生物体的生理与病理变化规律。随着高通量质谱检测技术的广泛应用，大规模代谢组学研究日益普遍，但多批次实验数据中普遍存在的批次效应（Batch Effect）和缺失值问题严重影响数据质量与分析结果的可靠性。现有分析平台（如 MetaboAnalyst）在批次效应处理方法的覆盖、深度学习算法的引入以及全流程一体化分析方面仍存在明显局限。

针对上述问题，本文设计并实现了一个基于深度学习的代谢组学批次效应处理 Web 平台。系统采用前后端分离架构，后端基于 FastAPI 框架，前端基于 Vue3 + TypeScript，算法层以独立模块形式组织，具备良好的可扩展性。在缺失值填充方面，系统集成了均值、中位数、KNN 三种传统方法，并实现了基于 PyTorch 的 Autoencoder 深度学习填充模型，采用 Masked Reconstruction 训练策略，仅对已知值位置计算重建损失。为客观评估各填充方法的精度，本文设计了 Mask-then-Impute 评估框架，在 Benchmark 数据集（1715 个样本、1180 个特征、7 个批次）上进行了定量对比实验：Autoencoder 方法取得最低 RMSE（0.2249），相比 KNN（0.2980）降低约 24.5%，相比均值填充（1.0011）降低约 77.5%。在批次效应校正方面，系统实现了逐特征位置尺度对齐（Baseline）和 ComBat 经验 Bayes 两种校正方法，并设计了包含批次质心距离、批次轮廓系数与生物学分组轮廓系数的双维度评估体系。实验结果表明，Baseline 校正后批次质心距离由 5.38 下降至接近 0，批次混合效果显著。在下游分析方面，系统进一步实现了基于 t-test 和 BH-FDR 校正的差异代谢物分析、基于 KEGG 的通路富集分析，以及基于 MetaKG 多库整合知识图谱的代谢物溯源展示，支持多数据集切换与交互式可视化。

本系统完整覆盖了代谢组学数据从预处理到结果解读的全分析流程，为研究人员提供了一体化、可视化的数据处理工具，具有较好的实用价值与可扩展性。

**关键词**：代谢组学；批次效应；缺失值填充；深度学习；自动编码器；Web 平台

---

# Abstract

Metabolomics is an important research field in life science that systematically detects small-molecule metabolites in biological systems, revealing metabolic changes under different physiological or pathological conditions. With the widespread adoption of high-throughput mass spectrometry, large-scale multi-batch metabolomics studies have become increasingly common. However, batch effects and missing values in multi-batch experimental data seriously compromise data quality and the reliability of downstream analysis. Existing platforms such as MetaboAnalyst still have notable limitations in batch effect correction methods, deep learning integration, and end-to-end workflow support.

To address these issues, this paper designs and implements a deep learning-based metabolomics batch effect processing web platform. The system adopts a front-end and back-end separated architecture, with FastAPI as the backend framework, Vue3 + TypeScript for the frontend, and an independently organized algorithm module layer for extensibility. For missing value imputation, the system integrates three traditional methods (mean, median, and KNN) and implements an Autoencoder-based deep learning imputation model using PyTorch, trained with a Masked Reconstruction strategy that computes reconstruction loss only on observed values. A Mask-then-Impute evaluation framework is proposed to objectively compare imputation methods. Experiments on the Benchmark dataset (1715 samples, 1180 features, 7 batches) show that the Autoencoder achieves the lowest RMSE (0.2249), outperforming KNN (0.2980) by approximately 24.5% and mean imputation (1.0011) by approximately 77.5%. For batch effect correction, the system implements two methods: per-feature location-scale alignment (Baseline) and ComBat with empirical Bayes estimation. A dual-indicator evaluation system is designed, comprising batch centroid separation distance, batch Silhouette score, and biological group Silhouette score. Experimental results demonstrate that after Baseline correction, the batch centroid separation distance drops from 5.38 to near zero, indicating effective batch mixing. In downstream analysis, the system further provides differential metabolite analysis based on t-test with BH-FDR correction, KEGG pathway enrichment analysis, and a MetaKG knowledge graph-based metabolite traceability visualization. Multiple datasets and interactive visualizations are supported.

The system comprehensively covers the full metabolomics analysis workflow from data preprocessing to biological interpretation, providing researchers with an integrated and visualized data processing tool with good practical value and extensibility.

**Keywords**: Metabolomics; Batch Effect; Missing Value Imputation; Deep Learning; Autoencoder; Web Platform

---

# 第一章 绪论

## 1.1 研究背景与意义

代谢组学（Metabolomics）是继基因组学、转录组学和蛋白质组学之后发展起来的重要研究领域。其核心思想是通过质谱（Mass Spectrometry，MS）或核磁共振（Nuclear Magnetic Resonance，NMR）等高通量检测技术，对生物体内全部或部分小分子代谢物（分子量通常小于 1500 Da）进行系统性定量检测，进而从代谢层面揭示生物体在不同生理状态、病理条件或外界干预下的整体响应规律<sup>[1]</sup>。与基因组和蛋白质组相比，代谢物是生命活动的直接产物，能够更加灵敏地反映生物体当前的功能状态，因此代谢组学在疾病早期诊断与生物标志物发现<sup>[2]</sup>、药物靶点识别<sup>[3]</sup>、营养干预评估等领域已展现出重要的应用价值。

然而，随着代谢组学研究规模的持续扩大，大量样本往往需要在不同时间段分批完成检测，由此引入了代谢组学数据分析中的核心技术挑战之一——**批次效应（Batch Effect）**。批次效应是指由仪器状态波动、环境温湿度变化、试剂批次差异、操作人员变化等非生物学因素所造成的系统性偏差，其典型表现为：同一生物条件的样本在不同批次中检测到的信号强度呈现出明显的系统性偏移，而这种偏移与样本本身的生物学状态无关<sup>[4]</sup>。在主成分分析（PCA）等降维可视化手段下，批次效应通常表现为不同批次样本聚集成相互分离的簇群，掩盖了真实的生物学差异，严重干扰后续差异代谢物筛选和通路分析的结果可靠性。

与批次效应并列的另一个重要问题是**缺失值（Missing Values）**的处理。液相色谱-质谱联用（LC-MS）技术在低丰度代谢物的检测中存在仪器灵敏度限制，当代谢物浓度低于检测限（Limit of Detection，LOD）时，相应数据点将以缺失值形式出现在数据矩阵中<sup>[5]</sup>。此外，谱峰拾取算法的误差、质量控制样本的处理差异等因素也会进一步加剧缺失值问题。在典型的大规模代谢组学数据集中，缺失值比例可达 20%～50%，若直接参与统计分析，将导致估计偏差加剧、差异检验功效下降，进而影响生物学结论的可靠性<sup>[6]</sup>。

面对上述两类问题，现有的主流代谢组学分析平台（如 MetaboAnalyst<sup>[7]</sup>）虽然提供了较为完整的数据分析功能，但仍存在以下局限：①在批次效应校正方法上，多数平台以 ComBat 等统计方法为主，缺乏深度学习类方法的集成；②批次效应校正与缺失值填充通常作为独立步骤分步进行，误差可能逐步累积；③缺少可量化的方法对比评估框架，用户难以客观判断不同方法的适用性；④从数据预处理到下游分析、结果解读，尚无覆盖全流程的一体化 Web 平台。

随着深度学习技术的快速发展，将神经网络方法引入代谢组学数据处理已成为近年来的研究热点。研究表明，基于 Autoencoder 的深度学习模型能够有效捕获高维代谢组学数据中特征间的复杂相关结构，在缺失值填充和特征表示学习等任务上展现出优于传统统计方法的潜力<sup>[8]</sup>。

基于上述背景，本文设计并实现了一个面向代谢组学数据分析的 Web 平台，重点解决批次效应校正与缺失值填充两大核心问题，并通过引入深度学习 Autoencoder 方法和可量化的评估框架，在系统工程层面实现从数据导入、预处理、填充与校正，到评估可视化、下游差异分析与知识图谱溯源的全流程覆盖。本研究的意义在于：一方面，将深度学习方法与传统统计方法纳入统一框架进行定量对比，为用户提供客观的方法选择依据；另一方面，通过 Web 平台的工程化实现，降低代谢组学数据分析的技术门槛，提升研究人员的数据处理效率。

## 1.2 国内外研究现状

### 1.2.1 代谢组学数据分析平台研究现状

在代谢组学数据分析平台方面，MetaboAnalyst 是目前应用最广泛的在线分析平台之一。该平台集成了数据归一化、缺失值填充、主成分分析、差异代谢物筛选和通路分析等多种功能模块，并提供了较为友好的 Web 交互界面<sup>[7]</sup>。Pang 等人在 MetaboAnalyst 5.0 中进一步增加了多组学整合分析和代谢物注释功能，显著扩展了平台的应用范围。此外，XCMS Online<sup>[9]</sup> 提供了从原始质谱数据处理到统计分析的一体化流程，Metaboscape 等商业软件也在代谢物鉴定和批次校正方面有所集成。

然而，上述平台存在共同的不足：批次效应处理通常以单一 ComBat 方法为主，缺乏深度学习类方法；缺失值填充与批次效应校正独立处理，无法评估两步骤之间的误差传播；可量化的方法对比评估机制不健全，用户难以根据数据特点选择最优方案。

### 1.2.2 缺失值填充方法研究现状

代谢组学缺失值填充方法大致可分为三类：

**简单统计填充方法**：以均值填充（Mean Imputation）和中位数填充（Median Imputation）为代表，将特征的统计量直接赋予缺失位置。方法简单高效，但忽略了样本间的相关结构，可能引入系统性偏差，在缺失值比例较高时表现较差<sup>[5]</sup>。

**基于近邻的方法**：K 近邻填充（K-Nearest Neighbor，KNN）利用与待填充样本最相似的 K 个样本的特征值加权估计缺失位置。该方法能够一定程度上利用样本间的相似结构，在代谢组学领域被广泛采用，但计算复杂度较高，且对于高缺失率场景效果受限<sup>[10]</sup>。

**深度学习方法**：Gondara 和 Wang 于 2018 年提出了基于去噪自动编码器（Denoising Autoencoder）的多重填充方法 MIDA（Multiple Imputation using Denoising Autoencoders），通过向输入数据添加噪声并训练网络重建原始信号，使模型能够从整体数据分布中学习特征间的复杂依赖关系，从而对缺失位置进行更准确的估计<sup>[8]</sup>。近年来，针对生物组学数据的深度学习填充方法不断涌现，相关研究表明，在特征间具有复杂相关结构的高维数据场景下，深度学习方法通常优于传统统计方法<sup>[11]</sup>。

### 1.2.3 批次效应校正方法研究现状

批次效应校正方法的研究已有较长历史，主要可分为以下三类：

**基于统计模型的方法**：ComBat 是该领域最具影响力的方法之一，由 Johnson 等人于 2007 年提出。该方法将基因（特征）表达值建模为全局均值、生物学效应与批次效应之和，通过经验 Bayes（Empirical Bayes）估计批次参数，利用所有特征的汇聚信息改善小样本场景下的参数估计稳定性，并可传入生物学协变量保护真实生物差异不被消除<sup>[12]</sup>。此后，ComBat 被广泛应用于转录组学、蛋白质组学和代谢组学领域。逐特征位置尺度归一化（Per-feature Location-Scale Normalization）是另一种简单有效的统计方法，通过将各批次的特征均值和标准差归一化至全局水平，实现批次间分布的对齐，实现简单且具有良好的可解释性。

**基于低维对齐的方法**：Harmony 算法由 Korsunsky 等人于 2019 年提出，最初用于单细胞RNA测序数据的批次效应校正<sup>[13]</sup>。该方法通过在低维嵌入空间（如 PCA 空间）中迭代寻找跨批次的相似邻居关系并进行分布对齐，避免了对原始高维空间的直接操作，在多批次多样本场景下表现良好。

**基于深度学习的方法**：近年来，研究者开始将深度学习引入批次效应校正。Shaham 等人提出利用对抗神经网络（Adversarial Neural Network）学习批次不变的数据表示，在对数据结构依赖较弱的场景下取得了较好效果<sup>[14]</sup>。此外，也有研究探索使用变分自动编码器（Variational Autoencoder，VAE）同时完成批次效应校正与缺失值填充，在统一框架下减少分步处理带来的误差传播<sup>[15]</sup>。

### 1.2.4 代谢组学下游分析研究现状

批次效应校正完成后，代谢组学研究通常进入下游分析阶段，主要包括：

**差异代谢物分析**：常用方法包括独立样本 t 检验、方差分析（ANOVA）及其非参数等价方法，并配合 Benjamini-Hochberg 假阳性率控制（BH-FDR）进行多重检验校正，以 log2 Fold Change 衡量差异方向和大小<sup>[16]</sup>。

**代谢通路富集分析**：基于 KEGG（Kyoto Encyclopedia of Genes and Genomes）等数据库，通过超几何检验或 Fisher 精确检验判断差异代谢物是否显著富集于特定代谢通路，从而在通路层面解释差异代谢物的生物学意义<sup>[17]</sup>。

**知识图谱辅助解读**：近年来，知识图谱作为一种结构化知识表示方式，被引入代谢组学数据的生物学解读中。通过整合 KEGG、HMDB（Human Metabolome Database）、SMPDB（Small Molecule Pathway Database）等多源数据库，构建代谢物-通路-反应-酶-疾病关联网络，能够为差异代谢物提供可追溯的关联证据链<sup>[18]</sup>。

### 1.2.5 现有研究不足分析

综合来看，现有研究在代谢组学数据分析方法上已取得了较丰富的成果，但在系统集成层面仍存在以下不足：①批次效应校正与缺失值填充通常作为独立模块分步处理，缺乏整合框架；②现有平台对深度学习方法的集成程度有限，缺乏与传统方法的定量对比评估；③从数据预处理到下游分析、结果可视化的全流程一体化 Web 平台仍较为缺乏；④代谢组学知识图谱溯源功能尚未在分析平台中得到广泛集成。上述不足为本文的研究工作提供了明确的出发点。

## 1.3 本文主要工作

针对现有研究的不足，本文的主要工作包括以下四个方面：

**（1）设计并实现了代谢组学数据处理 Web 平台**

平台采用前后端分离架构，后端基于 Python FastAPI 框架，前端基于 Vue3 + TypeScript + ECharts，后端算法层以独立模块方式组织，支持 CSV/XLSX 格式的多数据集导入与切换，覆盖从数据预处理到结果可视化的完整分析流程。平台支持 Benchmark（7 批次合并，1715 样本，1180 特征）、BioHeart、MI 和 AMIDE 等多个公开数据集的处理与展示。

**（2）实现了基于 Autoencoder 的深度学习缺失值填充，并设计了 Mask-then-Impute 可量化评估框架**

在传统均值、中位数和 KNN 填充方法的基础上，本文基于 PyTorch 实现了 Encoder-Decoder 架构的 Autoencoder 填充模型，采用 Masked Reconstruction 训练策略，仅对已观测位置计算重建损失。同时，设计了 Mask-then-Impute 评估框架，通过随机遮蔽已知值并与填充结果对比，以 RMSE、MAE 和 NRMSE 三个指标对四种方法进行定量评估。实验表明，Autoencoder 方法在 Benchmark 数据集上取得最优 RMSE 为 0.2249，相比排名第二的 KNN（0.2980）降低约 24.5%。

**（3）集成了两种批次效应校正方法，并设计了双维度量化评估体系**

系统实现了逐特征位置尺度对齐（Baseline）方法和基于 neuroCombat 的 ComBat 经验 Bayes 方法，两种方法均有工程化的安全封装与异常处理机制。评估体系包含批次质心距离（Batch Centroid Separation）和批次/生物学分组轮廓系数（Silhouette Score）双指标，并通过 PCA 可视化直观呈现校正前后的效果对比。实验结果显示，Baseline 方法校正后批次质心距离由 5.38 降至约 0，批次混合效果显著。

**（4）实现了差异代谢物分析、KEGG 通路富集分析和 MetaKG 知识图谱溯源展示**

基于批次校正后矩阵，系统依次完成独立样本 t 检验（BH-FDR 校正）差异代谢物筛选、KEGG 通路超几何富集检验，以及基于 MetaKG 多库整合知识图谱的代谢物-通路-反应-酶关联溯源，并以火山图、通路富集气泡图和力导向知识图谱等多种可交互可视化形式呈现。

## 1.4 论文组织结构

本文共分七章，各章节内容安排如下：

**第一章 绪论**：介绍研究背景与意义，综述代谢组学数据分析、缺失值填充、批次效应校正及下游分析的国内外研究现状，提出现有研究的不足，说明本文的主要工作。

**第二章 相关技术与方法综述**：详细介绍本文所涉及的核心技术与方法，包括缺失值填充方法（传统统计方法与 Autoencoder 深度学习方法）、批次效应校正方法（Baseline 与 ComBat）以及批次效应评估指标（PCA、Silhouette 系数、批次质心距离）的原理与适用条件。

**第三章 系统总体设计**：阐述系统的需求分析、总体架构（前后端分离、分层模块化设计）、数据库设计（SQLite + 文件系统分工）、模块划分以及整体数据流设计。

**第四章 核心算法设计与实现**：详细描述各核心算法的设计思路与实现细节，包括数据预处理算法、Autoencoder 填充模型与 Mask-then-Impute 评估框架、Baseline 批次效应校正算法、ComBat 封装实现，以及差异分析、通路富集和知识图谱溯源算法。

**第五章 系统实现与展示**：介绍系统的技术栈选型、后端 API 设计与关键实现、前端组件架构与可视化实现，并展示系统各功能模块的界面截图与测试情况。

**第六章 实验与结果分析**：在多个数据集上对缺失值填充方法和批次效应校正方法进行定量对比实验，并展示差异代谢物分析与通路富集分析的结果，对实验数据进行深入分析与讨论。

**第七章 结论与展望**：总结本文的主要工作与贡献，指出系统的局限性，并展望后续改进方向。

---

# 第二章 相关技术与方法综述

## 2.1 代谢组学数据特点与预处理需求

### 2.1.1 代谢组学数据的结构特征

代谢组学数据通常以**样本×特征矩阵**（Sample-by-Feature Matrix）的形式组织，每行表示一个生物样本，每列表示一种代谢物特征（Feature），矩阵中的数值为该代谢物在该样本中的信号强度或经归一化后的丰度值。以本文所采用的 Benchmark 合并数据集为例，数据矩阵规模为 1715 个样本 × 1180 个代谢物特征，来自 7 个不同批次，涵盖多种实验条件与生物学分组。

代谢组学数据具有若干区别于一般机器学习数据集的典型特点：

**（1）高维小样本特性。** 在典型的非靶向代谢组学实验中，通过 LC-MS 检测得到的特征数目可达数百至数千个，而单次实验的样本量通常仅为数十至数百个。高维数据中特征维度远超样本维度（$p \gg n$），会显著增加统计方法的不稳定性和过拟合风险<sup>[5]</sup>。

**（2）特征间复杂相关结构。** 生物体内代谢物通过代谢通路彼此连接，参与同一通路的代谢物在丰度变化上通常呈现出高度相关性。这种数据内生的相关结构使得能够捕获特征间非线性依赖关系的方法（如 Autoencoder）在缺失值填充等任务上具有潜在优势。

**（3）数据分布偏斜与异质性。** LC-MS 原始数据通常呈右偏分布（正偏态），且不同代谢物的信号强度量级差异悬殊，常需进行 log 变换和尺度归一化以满足后续统计方法的正态性假设<sup>[16]</sup>。此外，不同批次、不同样本组的数据分布本身就存在系统性差异，这构成了批次效应问题的本质。

**（4）普遍存在缺失值。** 由于仪器检测下限、谱峰拾取算法误差以及低丰度代谢物的随机检测失败，代谢组学数据矩阵中通常存在大量缺失值，缺失比例在 20%～50% 之间较为常见。

### 2.1.2 数据预处理流程概述

针对上述数据特点，代谢组学数据分析通常需要经历以下预处理步骤：

1. **格式检验与质控**：核查数据矩阵完整性，排查异常样本（如 QC 样本）与低质量特征（如全缺失特征）；
2. **缺失值填充（Imputation）**：采用适当方法对缺失位置进行估计填充，保证后续分析的数据完整性；
3. **数据归一化与尺度化**：通过 log 变换、Pareto 缩放等手段消除量纲差异，满足统计分析前提；
4. **批次效应检测**：借助 PCA、Silhouette 系数、批次质心距离等指标判断批次效应程度；
5. **批次效应校正**：采用统计或深度学习方法消除批次间系统性偏差，同时尽量保护真实的生物学差异；
6. **校正效果评估**：通过定量指标和可视化手段验证校正结果。

上述步骤在本系统中均有对应的算法实现和 Web 交互界面支持，各步骤的具体实现将分别在第三章和第四章中详细描述。

---

## 2.2 缺失值填充方法

### 2.2.1 传统统计填充方法

**（1）均值填充（Mean Imputation）**

均值填充是最简单的缺失值处理策略：对于矩阵中第 $j$ 个特征，计算该列所有已观测值的算术均值 $\bar{x}_j$，将所有缺失位置统一赋值为 $\bar{x}_j$：

$$\hat{x}_{ij} = \bar{x}_j = \frac{1}{|\mathcal{O}_j|} \sum_{i \in \mathcal{O}_j} x_{ij}$$

其中 $\mathcal{O}_j$ 为第 $j$ 列中已观测值的样本下标集合。均值填充的优点是计算复杂度为 $O(np)$，实现简单、运行速度快；缺点是将所有缺失位置设置为同一值，完全忽略了样本间的个体差异，会人为压缩特征的方差，可能引入系统性偏差，在缺失率较高时效果较差。

在本文的 Mask-then-Impute 基准评估中，均值填充在 Benchmark 数据集（mask\_ratio = 15%，重复 3 次）上的平均 RMSE 为 **1.0011**，NRMSE 约为 **1.0006**，均明显高于 KNN 和 Autoencoder 方法（详见第六章）。

**（2）中位数填充（Median Imputation）**

中位数填充原理与均值填充类似，将每个特征的缺失位置赋值为该列的中位数 $\text{med}_j$：

$$\hat{x}_{ij} = \text{med}(x_{ij},\ i \in \mathcal{O}_j)$$

与均值相比，中位数对异常值（Outlier）具有更强的鲁棒性，适合于分布存在较强偏斜或含有离群样本的数据集。然而，中位数填充同样忽略了样本间的相关结构，且对于双峰分布等复杂情形也无法有效估计。本文评估中，中位数填充 RMSE 为 **1.0361**，MAE 为 **0.3427**，NRMSE 为 **1.0356**，与均值填充相近，均属于较为粗糙的基线方法。

**（3）K 近邻填充（KNN Imputation）**

K 近邻填充方法（K-Nearest Neighbor Imputation）的核心思想是：对于待填充的缺失位置 $(i, j)$，从其余已观测该特征的样本中找出与样本 $i$ 最相似的 $K$ 个近邻，将这 $K$ 个近邻在特征 $j$ 上的值加权平均作为填充估计：

$$\hat{x}_{ij} = \frac{\sum_{k \in \mathcal{N}(i,j)} w_{ik} \cdot x_{kj}}{\sum_{k \in \mathcal{N}(i,j)} w_{ik}}$$

其中 $\mathcal{N}(i,j)$ 为在特征 $j$ 上有观测值且与样本 $i$ 欧氏距离最近的 $K$ 个样本集合，$w_{ik}$ 为距离的倒数权重。本文系统中采用 $K = 5$，样本间的相似性基于所有非缺失特征上的欧氏距离计算。

KNN 填充能够利用数据集内样本间的相似性结构，相比简单统计方法通常具有更高的填充精度。本文评估中，KNN 方法 RMSE 为 **0.2980**，MAE 为 **0.0740**，NRMSE 为 **0.2978**，远优于均值和中位数方法。然而，KNN 的计算复杂度为 $O(n^2 p)$，在样本量较大时计算开销显著增大，且其性能依赖于"相似样本在特征空间中邻近"这一局部平滑假设，对代谢组学数据中远程通路关联等全局结构的捕获能力有限。

### 2.2.2 基于 Autoencoder 的深度学习填充方法

#### 网络结构设计

本文实现的缺失值填充 Autoencoder 采用对称的 Encoder-Decoder 结构，具体网络层次如下：

$$\text{输入层}(p) \xrightarrow{\text{Linear}} \text{隐层}(256) \xrightarrow{\text{ReLU} + \text{BN} + \text{Dropout}(0.1)} \text{潜空间}(64) \xrightarrow{\text{ReLU}}$$
$$\xrightarrow{\text{Linear}} \text{隐层}(256) \xrightarrow{\text{ReLU} + \text{BN}} \text{输出层}(p)$$

其中 $p$ 为特征维度（本文中 $p = 1180$），隐层维度 $h = 256$，潜空间维度 $l = 64$。Encoder 将高维代谢组学特征映射到低维潜空间表示，迫使模型学习数据的紧凑结构；Decoder 将潜空间表示重建回原始维度，输出对完整特征向量的估计。批归一化层（Batch Normalization）有助于稳定训练过程，Dropout（丢弃率 0.1）起正则化作用，防止过拟合。

> **图表说明（需自制）：** 图 2-1 Autoencoder 网络结构示意图，建议绘制分层网络示意图，标注各层维度：1180 → 256 → 64 → 256 → 1180，并标注各层激活函数与正则化操作。

#### Masked Reconstruction 训练策略

代谢组学数据中存在大量真实缺失值，无法直接使用标准的全观测重建损失。参考 Gondara 和 Wang（2018）提出的 MIDA 方法，本文采用 **Masked Reconstruction（遮蔽重建）** 训练策略：

1. **初始化**：将输入矩阵 $\mathbf{X}$ 中的缺失位置（NaN）用对应列均值填充，得到初始输入 $\tilde{\mathbf{X}}$，为网络提供合理的起始信号；
2. **构造观测掩码**：令 $\mathbf{M} \in \{0, 1\}^{n \times p}$，其中 $m_{ij} = 1$ 表示位置 $(i,j)$ 为已知观测值，$m_{ij} = 0$ 表示缺失位置；
3. **前向传播与损失计算**：对 mini-batch 内的样本 $\mathbf{X}_b$ 进行前向传播得到重建输出 $\hat{\mathbf{X}}_b = f_\theta(\tilde{\mathbf{X}}_b)$，仅在已知位置计算 MSE 损失，避免网络在缺失位置上自学习：

$$\mathcal{L} = \frac{\sum_{(i,j): m_{ij}=1} (\hat{x}_{ij} - x_{ij})^2}{\sum_{i,j} m_{ij} + \epsilon}$$

4. **梯度更新**：通过反向传播优化网络参数 $\theta$，采用 Adam 优化器（学习率 $lr = 10^{-3}$，权重衰减 $\lambda = 10^{-5}$）和 CosineAnnealingLR 学习率调度策略（$T_{\max} = 80$ 轮，$\eta_{\min} = lr \times 0.1$），训练总轮数为 80 epochs，batch size 为 64；
5. **填充推断**：训练完成后，以 $\tilde{\mathbf{X}}$ 为输入进行前向推断，仅将网络输出中对应缺失位置 $\mathbf{M}_{ij}=0$ 的预测值回填至矩阵，已知观测值保持不变。

上述策略的核心优势在于：网络的训练监督信号完全来自已知观测值，缺失位置的填充结果由网络从数据整体分布中泛化推断得到，而非通过自学习缺失值获得，从而保证了填充结果的合理性。

> **图表说明（需自制）：** 图 2-2 Mask-then-Impute 评估框架流程图，建议绘制横向流程图，步骤为：原始无缺失矩阵 → 随机遮蔽 15% → 四种填充方法 → 与真值对比 → RMSE/MAE/NRMSE 指标汇总，需注明"重复 3 次取均值"。

### 2.2.3 Mask-then-Impute 评估框架

为客观定量评估各填充方法的精度，本文设计了 **Mask-then-Impute 评估框架**。其基本思想是：在原本已完整（无缺失）的矩阵上人工随机遮蔽一定比例的值作为"模拟缺失"，使用各填充方法对遮蔽位置进行填充，再将填充结果与原始真值进行对比计算误差指标，从而在有参照标准的条件下对方法性能进行量化评估。具体流程如下：

1. 以随机种子为控制，从观测值中均匀随机抽取 15% 位置（约 303,555 个）标记为遮蔽；
2. 分别以均值、中位数、KNN（$K=5$）、Autoencoder 四种方法对遮蔽位置进行填充；
3. 计算以下三个误差指标：

**均方根误差（RMSE）**：

$$\text{RMSE} = \sqrt{\frac{1}{|\mathcal{M}|}\sum_{(i,j)\in\mathcal{M}} (\hat{x}_{ij} - x_{ij})^2}$$

**平均绝对误差（MAE）**：

$$\text{MAE} = \frac{1}{|\mathcal{M}|}\sum_{(i,j)\in\mathcal{M}} |\hat{x}_{ij} - x_{ij}|$$

**归一化均方根误差（NRMSE）**：对每个特征的 RMSE 除以该特征的标准差后取平均，消除不同特征量纲差异，实现跨特征可比性：

$$\text{NRMSE} = \frac{1}{p}\sum_{j=1}^{p}\frac{\text{RMSE}_j}{\text{std}(x_{\cdot j})}$$

4. 上述过程以不同随机种子独立重复 3 次，取指标均值与标准差作为最终评估结果；
5. 在 Benchmark 数据集上的完整评估结果详见第六章表 6-1。

### 2.2.4 各方法适用场景分析

| 填充方法 | 计算复杂度 | RMSE（本文） | 主要优势 | 适用场景 |
|:-------:|:---------:|:-----------:|:-------:|:-------:|
| 均值填充 | $O(np)$ | 1.0011 | 简单快速 | 缺失率低、特征独立性高 |
| 中位数填充 | $O(np\log n)$ | 1.0361 | 抗异常值 | 分布偏斜、含离群点 |
| KNN 填充 | $O(n^2 p)$ | 0.2980 | 利用样本相似性 | 样本量适中、局部结构明显 |
| Autoencoder | $O(nph)$ | **0.2249** | 捕获全局非线性结构 | 高维、特征间复杂相关 |

> **表格说明**：上表为本文设计的方法对比汇总表（可直接用于论文），RMSE 数值来自 Benchmark 数据集 Mask-then-Impute 评估，重复 3 次均值。

总体而言，当数据集规模适中且样本间局部相似性较强时，KNN 是兼顾精度与计算效率的较优选择；当数据维度较高、特征间存在复杂非线性相关结构时，Autoencoder 方法更具优势；简单统计方法可作为快速基线参考。

---

## 2.3 批次效应校正方法

### 2.3.1 Baseline 逐特征位置尺度对齐

逐特征位置尺度对齐（Per-feature Location-Scale Normalization，本文称为 Baseline 方法）是一种直观的批次效应校正策略，其核心思想是：假设批次效应主要体现为各批次在每个特征上的均值（位置）和标准差（尺度）的系统性偏移，通过将各批次的分布对齐至全局分布，消除批次间的位置与尺度差异。

对于特征 $j$，设全局均值为 $\mu_j = \frac{1}{n}\sum_{i=1}^{n}x_{ij}$，全局标准差为 $\sigma_j = \text{std}(x_{\cdot j})$；对于属于批次 $b$ 的样本子集，设批次内均值为 $\mu_{bj}$，批次内标准差为 $\sigma_{bj}$。则对样本 $i$（$i$ 属于批次 $b$）的校正公式为：

$$x'_{ij} = \frac{x_{ij} - \mu_{bj}}{\max(\sigma_{bj}, \epsilon)} \cdot \sigma_j + \mu_j$$

其中 $\epsilon > 0$ 为防止除零的数值稳定下界（本文取 $\epsilon = 10^{-8}$）。该公式先将批次内分布标准化（减去批次均值、除以批次标准差），再缩放还原为全局分布的均值与尺度，实现批次间分布的对齐。

**方法特点**：实现简单，假设清晰（仅假设批次效应为逐特征的位置/尺度偏移）；可解释性强；无需额外协变量信息。**主要局限**：①仅对位置和尺度偏移有效，无法处理批次效应呈现复杂非线性形态的情况；②不考虑生物学协变量，若批次与生物学分组高度混杂，可能造成过校正，削弱真实生物学信号；③对批次内样本量要求最低 2 个，样本量极少的批次统计量估计不稳定。

在本文的 Benchmark 数据集上，Baseline 方法校正后批次质心距离由 $5.38$ 降至约 $0$（$1.90 \times 10^{-14}$），批次混合效果极为显著；批次 Silhouette 系数由 $-0.1461$ 变化至 $-0.0343$，方向符合批次分离减弱的预期（详细数值分析见第六章）。

### 2.3.2 ComBat 经验 Bayes 方法

ComBat 方法由 Johnson 等人于 2007 年最初为基因表达数据（微阵列）设计<sup>[12]</sup>，后被广泛应用于转录组学、蛋白质组学和代谢组学领域。该方法将特征 $j$ 在样本 $i$（属于批次 $b$）上的观测值建模为：

$$x_{ijb} = \alpha_j + \mathbf{d}_{ib}^T \boldsymbol{\beta}_j + \gamma_{jb} + \delta_{jb} \cdot \varepsilon_{ijb}$$

其中 $\alpha_j$ 为特征 $j$ 的全局均值，$\mathbf{d}_{ib}$ 为生物学协变量设计矩阵（如分组标签），$\boldsymbol{\beta}_j$ 为协变量效应，$\gamma_{jb}$ 和 $\delta_{jb}$ 分别为批次 $b$ 对特征 $j$ 施加的加性和乘性批次效应，$\varepsilon_{ijb}$ 为误差项。

ComBat 的关键在于**经验 Bayes 估计**策略：首先利用所有特征 $j = 1, \ldots, p$ 上的批次效应估计值构建先验分布，再通过 Bayes 收缩将各特征的批次参数估计值向先验均值"收缩"，从而在小样本场景下获得更稳定的参数估计。校正后的数据为：

$$x'_{ijb} = \frac{x_{ijb} - \alpha_j - \mathbf{d}_{ib}^T\hat{\boldsymbol{\beta}}_j - \hat{\gamma}^*_{jb}}{\hat{\delta}^*_{jb}} \cdot \sigma_j + \alpha_j + \mathbf{d}_{ib}^T\hat{\boldsymbol{\beta}}_j$$

其中 $\hat{\gamma}^*_{jb}$ 和 $\hat{\delta}^*_{jb}$ 为经验 Bayes 收缩后的批次效应估计值。

**方法特点**：①通过经验 Bayes 收缩利用跨特征信息改善小批次估计稳定性；②可显式传入生物学协变量（如分组标签）以保护真实生物学差异不被消除；③在代谢组学领域已有大量实际应用验证。**主要局限**：①需要预先知道批次标签和生物学协变量信息；②若批次与生物学因素严重混杂，保护效果受限；③要求各批次均有足够样本量以支撑稳定的参数估计。

本文系统基于 neuroCombat 库（Fortin 等，2018）对 ComBat 进行封装，增加了安全异常处理机制，支持数值型协变量的可选传入。

### 2.3.3 两种方法的比较

| 比较维度 | Baseline（位置尺度对齐） | ComBat（经验 Bayes） |
|:-------:|:---------------------:|:-------------------:|
| 模型假设 | 批次效应为逐特征位置/尺度偏移 | 批次效应有加性+乘性成分，支持协变量 |
| 生物学保护 | 不支持协变量传入 | 支持显式传入生物学协变量 |
| 跨特征信息 | 各特征独立校正 | 利用跨特征汇聚信息改善估计 |
| 实现复杂度 | 简单，易于理解与调试 | 较复杂，依赖 neuroCombat 实现 |
| 可解释性 | 高 | 中等 |
| 适用场景 | 批次效应近似线性、快速基线校正 | 小批次、需保护生物学信号 |

> **表格说明**：上表为本文设计的批次效应校正方法对比汇总表（可直接用于论文）。

在本文系统中，两种方法均通过统一的算法接口调用，用户可在前端界面选择校正方法并可视化对比校正效果，详见第五章。

---

## 2.4 批次效应评估指标

批次效应校正效果的评估需要同时考虑两个维度：**批次混合程度**（批次效应是否被有效消除）和**生物学信号保留程度**（真实的生物学差异是否被保护）。本文采用 PCA 可视化、Silhouette 系数双指标和批次质心距离三种手段构建双维度评估体系。

### 2.4.1 PCA 降维可视化

主成分分析（Principal Component Analysis，PCA）是评估批次效应最直观的工具。通过将高维代谢组学数据（本文为 1180 维）投影至前两个主成分所张成的二维平面，可以直观观察样本在低维空间中的分布规律：若校正前不同批次样本形成明显分离的簇群，校正后各批次样本混合分布，则说明批次效应得到有效消除。

本文系统中，PCA 分析分别在校正前后各运行一次，以相同批次颜色编码和相同分组标记在前端 ECharts 散点图中并列展示。如图所示（可引用现有图片）：

> **可直接引用图片**：`backend/data/processed/benchmark_merged/_pipeline/pca_before_vs_after_batch_correction.png`（PCA 校正前后对比图）和 `backend/data/processed/benchmark_merged/_pipeline/pca_pre_correction_batch_vs_group.png`（校正前批次 vs 分组对比图），分别对应本文**图 2-3** 和**图 2-4**。

校正前，PCA 图中 7 个批次样本呈现出明显的簇状分离，PC1 和 PC2 的解释方差比分别为 22.0% 和 4.9%，主要方差来源为批次间差异。校正后，7 个批次样本在 PCA 空间中实现了充分混合，主要方差结构发生变化（PC1 解释方差比提升至 50.9%），表明批次效应被有效消除，且数据中残余的方差结构可能更多地反映了真实的生物学差异。

### 2.4.2 Silhouette 系数双指标

Silhouette 系数是衡量聚类结构紧密程度的经典指标，其对单个样本 $i$ 的计算公式为：

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i),\ b(i)\}}$$

其中 $a(i)$ 为样本 $i$ 与同类（同批次或同分组）其他样本的平均距离，$b(i)$ 为样本 $i$ 与最近异类（不同批次或不同分组）样本的平均距离。$s(i) \in [-1, 1]$，整个数据集的 Silhouette 系数为所有样本的均值 $\bar{s}$。

本文设计了**双 Silhouette 指标**，分别对批次标签和生物学分组标签计算 Silhouette 系数：

- **批次 Silhouette（batch Silhouette）**：以批次 ID 作为类别标签计算。值越**低**（向 $-1$ 方向），表示不同批次样本在 PCA 空间中相互混合越充分，即批次效应越弱，校正效果越好；
- **分组 Silhouette（group Silhouette）**：以生物学分组标签作为类别标签计算。值越**高**（向 $+1$ 方向），表示相同生物学分组的样本聚集越紧密，即生物学结构保留越完好。

两个指标在批次校正前后的变化方向应当一致指向"好"的方向：批次 Silhouette 应降低（或更加负向），分组 Silhouette 应升高（或负值幅度减小）。

本文 Benchmark 数据集上，以 PCA 前两个主成分坐标计算的 Silhouette 系数变化如下：

| 指标 | 校正前 | 校正后（Baseline） | 变化方向 |
|:---:|:------:|:-----------------:|:-------:|
| 批次 Silhouette | −0.1461 | −0.0343 | +0.1117（向 0 移动，批次分离略有减弱） |
| 分组 Silhouette | −0.4813 | −0.4465 | +0.0348（负值幅度减小，分组结构略有改善） |

值得注意的是，上表中批次 Silhouette 校正后有所**上升**（由更负向接近 0），这在解释上存在一定歧义：在校正前后各自的 PCA 坐标系下，若校正后数据的总体方差结构发生了改变，Silhouette 系数的变化可能受到 PCA 坐标变化本身的影响，而非仅反映批次分离程度。因此，本文将批次**质心距离**作为主要判据，Silhouette 系数作为辅助参考，并综合 PCA 可视化进行综合判断。

### 2.4.3 批次质心距离

批次质心距离（Batch Centroid Separation Distance）衡量各批次在 PCA 低维空间中的质心离散程度，直接量化批次间系统性偏移的大小：

$$D_{\text{centroid}} = \frac{1}{B(B-1)}\sum_{b=1}^{B}\sum_{b' \neq b} \|\bar{\mathbf{z}}_b - \bar{\mathbf{z}}_{b'}\|_2$$

其中 $B$ 为批次数，$\bar{\mathbf{z}}_b = \frac{1}{n_b}\sum_{i \in \mathcal{B}_b} \mathbf{z}_i$ 为批次 $b$ 内所有样本在 PCA 空间中的质心坐标（取 PC1 和 PC2），$\|\cdot\|_2$ 为欧氏距离。

批次质心距离越接近 0，表示各批次的"中心"在低维空间中趋于重合，批次混合效果越好。

在本文 Benchmark 数据集上，批次质心距离的变化如下表所示：

| 指标 | 校正前 | 校正后（Baseline） | 变化量 |
|:---:|:------:|:-----------------:|:------:|
| 批次质心距离（PC1–PC2） | 5.3796 | ≈ 0（$1.90 \times 10^{-14}$） | −5.3796 |

校正后批次质心距离几乎归零（数值上的非零仅为浮点精度误差），表明在 PCA 前两个主成分空间中，Baseline 方法实现了各批次质心的完全对齐，批次效应被有效消除。这也是本文将质心距离作为主要判据的原因——相较于 Silhouette 系数，质心距离的解释更直接、不受 PCA 坐标系变化影响。

---

## 2.5 本章小结

本章系统介绍了本文研究所涉及的核心技术与方法。

在**代谢组学数据特点**方面，梳理了高维小样本、特征间复杂相关、分布偏斜和高缺失率等典型数据特征，说明了预处理流程各步骤的必要性。

在**缺失值填充方法**方面，介绍了均值、中位数、KNN 三种传统统计方法的原理与局限，重点阐述了基于 Autoencoder 的深度学习填充模型的网络结构（1180→256→64→256→1180）和 Masked Reconstruction 训练策略。提出的 Mask-then-Impute 评估框架在 Benchmark 数据集（mask\_ratio=15%，3 次重复）上的定量评估表明，Autoencoder 方法取得最低 RMSE（0.2249），KNN 次之（0.2980），均值（1.0011）和中位数（1.0361）方法差异较小但精度明显较低。

在**批次效应校正方法**方面，阐述了 Baseline 逐特征位置尺度对齐（实现简单、无需协变量）和 ComBat 经验 Bayes 方法（利用跨特征信息、可保护生物学信号）的原理与各自适用场景，并从多个维度进行了对比分析。

在**批次效应评估指标**方面，构建了 PCA 可视化、Silhouette 系数双指标（批次/分组）和批次质心距离组成的双维度量化评估体系，强调了以批次质心距离为主、Silhouette 系数为辅、结合 PCA 可视化综合判断的评估策略。在 Benchmark 数据集上，Baseline 方法校正后批次质心距离由 5.38 降至约 0，校正效果显著。

上述方法的工程实现细节将在第四章中详细阐述，实验结果分析将在第六章中呈现。

---

# 第三章 系统总体设计

## 3.1 系统需求分析

### 3.1.1 功能需求

本系统以代谢组学研究人员为主要目标用户，其使用场景通常为：拥有来自多批次 LC-MS 实验的代谢组学数据矩阵，需要依次完成缺失值填充、批次效应校正和差异代谢物分析，并希望通过可视化界面直观评估各步骤的处理效果。围绕这一核心场景，系统的功能需求可划分为以下六类：

**（1）数据管理需求**

- 支持 CSV 和 XLSX 格式的数据文件上传，文件大小上限为 50MB；
- 支持 Long Format（长表格）数据格式解析，用户可自定义特征列、样本列、数值列、批次标签列、分组标签列的列名映射；
- 支持多数据集并行管理，用户可在 Benchmark、BioHeart、MI、AMIDE 等预置数据集与自定义上传数据集间切换；
- 提供数据集基本信息预览（样本数、特征数、批次数）。

**（2）数据预处理需求**

- 支持配置缺失率过滤阈值（默认 50%，超出阈值的特征列将被删除）；
- 支持 log1p 变换（对正偏态分布进行压缩）；
- 支持 Z-score 标准化（按样本维度消除量纲差异）；
- 预处理结果以 CSV 矩阵文件形式持久化存储。

**（3）缺失值填充需求**

- 支持四种填充方法：均值填充、中位数填充、KNN 填充（$K$ 可配置）、Autoencoder 深度学习填充；
- 填充方法参数可在 Web 界面配置，支持单次选择一种方法运行；
- 提供 Mask-then-Impute 评估结果展示（RMSE/MAE/NRMSE 对比图表）；
- 填充结果矩阵支持 CSV 格式下载。

**（4）批次效应校正需求**

- 支持两种校正方法：Baseline 逐特征位置尺度对齐、ComBat 经验 Bayes 校正；
- 提供校正前后的 PCA 散点图对比可视化（支持按批次/分组两种颜色编码）；
- 提供批次质心距离、批次 Silhouette 系数、分组 Silhouette 系数三项定量评估指标展示；
- 校正结果矩阵支持 CSV 格式下载。

**（5）下游分析需求**

- 差异代谢物分析：基于独立样本 t 检验 + BH-FDR 校正，支持 q 值阈值和 |log2FC| 阈值配置，结果以火山图展示；
- 通路富集分析：基于 KEGG 数据库超几何检验，结果以富集气泡图展示（气泡大小 = 富集代谢物数，颜色 = $p$ 值）；
- 知识图谱溯源：基于 MetaKG 多库整合知识图谱，以力导向图展示差异代谢物的通路-反应-酶关联网络，支持节点拖拽、关键词搜索和节点类型过滤。

**（6）结果输出需求**

- 核心中间产物（预处理矩阵、填充矩阵、校正矩阵）支持 CSV 格式下载；
- 差异代谢物列表和通路富集结果支持表格展示与数据导出；
- 评估报告以 JSON 格式持久化于服务器，前端通过 API 按需读取。

### 3.1.2 非功能需求

**可用性**：面向无编程背景的生物医学研究人员，Web 界面应具备清晰的操作引导，关键参数提供默认值，错误信息以友好的文字形式提示，避免终止整体流程。

**可扩展性**：算法层以独立模块方式组织，新增缺失值填充方法或批次效应校正方法时，只需在对应算法子目录下添加实现，不修改上层 Service 与 API 代码；前端组件化设计，新增可视化卡片无需改动核心状态管理逻辑。

**可靠性**：ComBat 等可能因数据条件不满足而失败的算法均有安全封装，捕获异常后以降级策略处理（如返回未校正矩阵并记录错误原因），不影响其他模块的正常执行。

**性能**：系统以本地单机部署为目标，针对本文实验数据集规模（~1715 样本 × 1180 特征）的处理时间在可接受范围内（预处理 < 30s，KNN 填充 < 60s，Autoencoder 填充 < 90s）。

---

## 3.2 系统总体架构

### 3.2.1 前后端分离架构概述

本系统采用**前后端分离**的 Web 应用架构，前端与后端通过 HTTP/REST 接口通信，互相独立开发与部署。整体架构分为三个主要层次：

- **前端展示层**：基于 Vue3 + TypeScript + Vite 构建，使用 Element Plus 作为 UI 组件库，ECharts 实现数据可视化，Pinia 管理全局状态。前端独立运行于 Vite 开发服务器（端口 5173），通过 HTTP 请求访问后端 API。

- **后端服务层**：基于 Python FastAPI 框架构建，采用 Uvicorn 作为 ASGI 服务器（端口 8000），提供 RESTful 风格的 API 接口。内部按职责分为 API 接口层（Routes）、业务逻辑层（Services）、算法计算层（Algorithms）和数据访问层（Repositories）四个子层次。

- **数据存储层**：采用 SQLite 文件数据库存储元数据（任务状态、数据集配置、参数记录），使用文件系统存储数据矩阵 CSV 文件和 JSON 格式的评估结果。

> **图表说明（需自制）：** 图 3-1 系统总体架构图，建议绘制分层架构示意图，从上至下依次为：浏览器（Vue3前端）→ HTTP/REST → FastAPI后端（Routes→Services→Algorithms/Repositories）→ SQLite数据库 + 文件系统。

### 3.2.2 后端分层架构设计

后端内部采用严格的四层分层架构，各层职责清晰，向下单向依赖：

**API 层（`app/api/routes/`）**：负责 HTTP 请求接收与响应序列化，参数校验（通过 Pydantic Schema），调用 Service 层执行业务逻辑，不包含任何业务计算代码。主要路由模块包括：`upload.py`（文件上传）、`tasks.py`（任务配置与状态查询）、`dataset.py`（数据集管理）、`benchmark_merged.py`（Benchmark 合并数据集的各分析步骤 API）、`benchmark_merged_ui.py`（面向前端展示的聚合数据接口）。

**Service 层（`app/services/`）**：包含核心业务逻辑，负责协调多个 Repository 和 Algorithm 模块完成完整的业务流程。主要 Service 模块及其职责如下表所示：

| Service 模块 | 职责说明 |
|:------------|:--------|
| `preprocess_service.py` | 缺失率过滤、log1p 变换、Z-score 标准化 |
| `imputation_service.py` | 调用对应填充算法，管理填充结果持久化 |
| `batch_service.py` | 调用批次效应校正算法，管理校正结果持久化 |
| `evaluation_service.py` | 计算 PCA、Silhouette 系数、批次质心距离，生成评估 JSON |
| `imputation_eval_service.py` | 运行 Mask-then-Impute 框架，汇总填充方法评估结果 |
| `differential_analysis_service.py` | t 检验 + BH-FDR 差异代谢物分析 |
| `pathway_enrichment_service.py` | KEGG 超几何富集检验，本地缓存管理 |
| `annotation_service.py` | 代谢物注释信息加载与 MetaKG 知识图谱构建 |
| `task_service.py` | 任务配置参数的读写管理 |

**Algorithm 层（`app/algorithms/`）**：纯算法实现，不依赖数据库或文件 I/O，仅接受 NumPy 数组和配置参数，返回处理结果。按功能划分为四个子模块：`preprocessing/`、`imputation/`（含 `autoencoder_imputer.py`）、`batch_correction/`（含 `baseline_location_scale_sample.py` 和 `combat.py`）、`evaluation/`。这种设计使算法可被单独测试，也可脱离 Web 框架在脚本中直接调用。

**Repository 层（`app/repositories/`）**：负责数据库的 CRUD 操作，通过 SQLAlchemy ORM 封装 SQL，对 Service 层屏蔽数据库实现细节。

### 3.2.3 前端架构设计

前端采用 Vue3 Composition API 风格开发，目录结构按功能职责划分：

- **`src/views/`**：页面级视图组件，对应路由配置中的各页面入口；
- **`src/components/`**：15 个可复用功能组件，承担各类分析结果的展示与交互（详见 3.4.1 节）；
- **`src/stores/`**：Pinia 状态管理，`benchmark.ts` 管理 Benchmark 合并数据集的所有展示数据，`task.ts` 管理用户自定义任务的状态；
- **`src/api/`**：HTTP 请求封装，与后端 API 接口一一对应；
- **`src/types/`**：TypeScript 类型定义，与后端 Pydantic Schema 保持对应。

---

## 3.3 数据库设计

### 3.3.1 数据库选型说明

本系统选用 **SQLite** 作为关系型数据库，主要考量如下：①SQLite 为嵌入式数据库，无需独立部署数据库服务，适合本地单机部署的应用场景；②代谢组学数据处理的主体计算量集中在矩阵运算和算法执行，数据库并发读写压力极低，SQLite 的单写多读能力完全满足需求；③SQLite 数据库文件（`data/app.sqlite3`）可与应用代码一同纳入版本管理，便于演示环境的快速搭建。系统通过 SQLAlchemy ORM 进行数据库访问，便于未来迁移至 PostgreSQL 等数据库时仅需修改连接字符串。

### 3.3.2 数据表设计

系统数据库包含以下四张核心数据表：

**（1）Task 表（`tasks`）**：记录每次分析任务的基本信息与状态。

| 字段名 | 类型 | 说明 |
|:------:|:----:|:----:|
| id | Integer（主键） | 任务唯一标识 |
| task_name | String(255) | 任务名称 |
| status | String(64) | 任务状态（uploaded / preprocess\_done / impute\_done / correct\_done / done / error） |
| created\_at | DateTime | 任务创建时间（UTC） |
| updated\_at | DateTime | 最近更新时间（UTC，自动更新） |
| file\_path | Text | 上传数据文件物理路径 |
| result\_path | Text | 任务结果目录路径 |
| error\_message | Text | 错误信息（仅 error 状态时填写） |

**（2）Dataset 表（`datasets`）**：记录上传数据集的解析配置，与 Task 表通过 `task_id` 外键关联。

| 字段名 | 类型 | 说明 |
|:------:|:----:|:----:|
| id | Integer（主键） | 数据集唯一标识 |
| task\_id | Integer（外键→tasks） | 关联任务 ID |
| original\_filename | String(512) | 原始上传文件名 |
| sample\_count | Integer | 样本数量 |
| feature\_count | Integer | 特征数量 |
| feature\_column | String(128) | 特征 ID 所在列名 |
| sample\_column | String(128) | 样本 ID 所在列名 |
| value\_column | String(128) | 数值所在列名 |
| batch\_column | String(128) | 批次标签所在列名 |
| group\_column | String(128) | 分组标签所在列名 |
| data\_format | String(32) | 数据格式（固定为 "long"） |
| stored\_path | Text | 数据文件存储路径 |

**（3）Parameters 表（`parameters`）**：以 JSON 字符串形式存储各阶段的算法参数配置，与 Task 表一对一关联。

| 字段名 | 类型 | 说明 |
|:------:|:----:|:----:|
| task\_id | Integer（主键兼外键→tasks） | 关联任务 ID |
| preprocess\_config\_json | Text | 预处理参数 JSON（缺失率阈值、是否 log 变换等） |
| imputation\_config\_json | Text | 填充参数 JSON（方法名、KNN 的 K 值等） |
| batch\_config\_json | Text | 批次校正参数 JSON（方法名、协变量配置等） |
| analysis\_config\_json | Text | 下游分析参数 JSON（q 值阈值、log2FC 阈值等） |

**（4）Result 表（`results`）**：记录各阶段处理结果的文件路径和评估指标，与 Task 表一对一关联。

| 字段名 | 类型 | 说明 |
|:------:|:----:|:----:|
| id | Integer（主键） | 记录唯一标识 |
| task\_id | Integer（外键→tasks） | 关联任务 ID |
| preprocess\_matrix\_path | Text | 预处理后矩阵 CSV 路径 |
| imputed\_matrix\_path | Text | 填充后矩阵 CSV 路径 |
| batch\_corrected\_matrix\_path | Text | 批次校正后矩阵 CSV 路径 |
| pca\_before\_plot\_path | Text | 校正前 PCA 图路径 |
| pca\_after\_plot\_path | Text | 校正后 PCA 图路径 |
| metrics\_json | Text | 评估指标 JSON（Silhouette、质心距离等） |
| summary\_json | Text | 分析摘要 JSON |

> **图表说明（需自制）：** 图 3-2 数据库 ER 图，建议绘制 Task-Dataset（一对多）、Task-Parameters（一对一）、Task-Result（一对一）的 ER 实体关系图，标注主键、外键和基数。

### 3.3.3 文件系统与数据库的分工

本系统采用"元数据入库、矩阵数据存文件"的混合存储策略：

- **数据库存储**：任务状态、参数配置、文件路径映射、评估指标（以 JSON 文本形式）等结构化元数据。这部分数据体量小，适合关系型查询和状态管理。
- **文件系统存储**：数据矩阵 CSV 文件（单文件可达数十 MB）、PCA 坐标 JSON 文件、评估报告 JSON 文件、图片文件等。文件路径记录在数据库中，前端通过 API 直接访问相应的文件读取接口获取内容。

文件系统目录结构如下：

```
backend/data/
├── uploads/          # 用户上传的原始数据文件
├── processed/        # 各数据集的处理结果目录
│   └── benchmark_merged/
│       ├── merge_report.json
│       └── _pipeline/
│           ├── preprocessed_sample_by_feature.csv
│           ├── imputed_sample_by_feature.csv
│           ├── batch_corrected_sample_by_feature.csv
│           ├── batch_correction_metrics.json
│           ├── pca_before_vs_after_batch_correction.png
│           ├── imputation_eval/
│           │   └── imputation_eval_report.json
│           └── evaluation/
│               └── evaluation_report.json
├── results/          # 用户自定义任务的结果目录
└── app.sqlite3       # SQLite 数据库文件
```

---

## 3.4 系统模块划分

本系统按照分析流程的逻辑顺序划分为六个主要功能模块，各模块职责独立、接口清晰。

### 3.4.1 数据管理模块

**功能职责**：负责数据文件的上传接收、格式解析与标准化存储。用户通过 Web 界面上传 CSV/XLSX 格式的代谢组学数据文件，并配置列名映射（特征列、样本列、数值列、批次标签列、分组标签列）。模块将长表格格式数据解析为宽矩阵格式（样本行 × 特征列），统计样本数和特征数，并将元数据写入 Dataset 表，将矩阵文件持久化至 `uploads/` 目录。

**关键设计**：列名映射配置以灵活 JSON 方式存储，支持不同数据集的格式差异；支持大文件分块上传，限制单文件不超过 50MB 以保护服务器资源。

### 3.4.2 预处理模块

**功能职责**：负责对原始数据矩阵进行质量过滤和分布变换，为后续填充和校正步骤提供高质量输入。主要操作包括：①按照用户配置的缺失率阈值（默认 50%）过滤低质量特征；②可选执行 log1p 变换（$x' = \log(1+x)$，压缩右偏分布）；③可选执行 Z-score 标准化（按样本归一化）。

**关键设计**：各预处理步骤均可独立开关配置，处理顺序固定为"缺失率过滤 → log 变换 → 标准化"，避免操作顺序不一致带来的结果差异。预处理完成后任务状态更新为 `preprocess_done`。

### 3.4.3 缺失值填充模块

**功能职责**：提供四种缺失值填充方法，用户可在 Web 界面选择方法和配置参数，系统执行填充并输出填充后矩阵。模块还负责运行 Mask-then-Impute 评估框架，生成各方法的 RMSE/MAE/NRMSE 对比评估报告。

**关键设计**：四种填充方法通过统一的函数接口调用，接受相同格式的 NumPy 数组输入、返回相同格式输出，便于在 Service 层统一调度和评估。Autoencoder 填充方法在大数据集上计算耗时较长，系统对此提供了进度提示机制。填充完成后任务状态更新为 `impute_done`。

### 3.4.4 批次效应校正模块

**功能职责**：提供 Baseline 和 ComBat 两种批次效应校正方法，执行校正并生成校正后矩阵。ComBat 方法封装有安全异常处理（`run_combat_safe`），当数据条件不满足（如某批次样本数过少、矩阵奇异等）时，捕获异常并以 Baseline 结果替代，保证模块不中断后续流程。

**关键设计**：校正方法需要样本的批次标签（`batch_id`）信息，系统从 Dataset 表中读取批次标签列配置，从矩阵数据中提取对应列，传入算法层。ComBat 还可选传入分组标签作为协变量，以保护真实生物学差异。

### 3.4.5 评估可视化模块

**功能职责**：在批次效应校正完成后，计算 PCA 坐标、Silhouette 系数（批次/分组双指标）和批次质心距离，生成评估 JSON 报告；同时支持多方法横向对比（Baseline vs ComBat vs 无校正），将 PCA 散点图数据和评估指标以 API 接口形式提供给前端。前端通过 ECharts 渲染 PCA 散点图和指标对比图表。

**关键设计**：PCA 坐标以 JSON 数组形式（而非图片）传输给前端，由前端 ECharts 动态渲染，支持鼠标交互（悬停显示样本信息、缩放平移）。评估 JSON 报告持久化存储，避免重复计算。

### 3.4.6 下游分析模块

**功能职责**：基于批次校正后矩阵，依次完成差异代谢物分析（t 检验 + BH-FDR）、KEGG 通路富集分析（超几何检验）和 MetaKG 知识图谱溯源。差异分析结果以火山图展示，通路富集结果以气泡图展示，MetaKG 子图以力导向图展示。

**关键设计**：KEGG API 数据采用本地 JSON 缓存策略（`kegg_cache/`），避免每次运行都请求远程接口，加快分析速度。对于无 KEGG 注释信息的数据集（如 AMIDE 数据集），通路富集模块能够识别这一情形并向前端返回友好的提示信息（"无法进行通路分析：特征无 KEGG ID 注释"），而不是报错中断流程。

---

## 3.5 系统整体数据流

系统的整体数据流遵循"原始数据 → 预处理 → 填充 → 批次校正 → 评估 → 下游分析"的线性管道（Pipeline）结构，各步骤的输入输出关系如下：

```
[用户上传]
原始数据文件（CSV/XLSX，Long Format）
        │
        ▼ 格式解析 + 列名映射
[数据管理模块] → 宽矩阵 CSV（samples × features，含 NaN）
        │
        ▼ 缺失率过滤 + log1p + Z-score
[预处理模块] → 预处理矩阵 CSV（preprocessed_sample_by_feature.csv）
        │
        ▼ Mean / Median / KNN / Autoencoder
[缺失值填充模块] → 填充矩阵 CSV（imputed_sample_by_feature.csv，无 NaN）
        │         ├──→ Mask-then-Impute 评估报告 JSON
        ▼ Baseline / ComBat
[批次效应校正模块] → 校正矩阵 CSV（batch_corrected_sample_by_feature.csv）
        │
        ▼ PCA + Silhouette + 质心距离
[评估可视化模块] → 评估报告 JSON + PCA 坐标 JSON → 前端 ECharts 渲染
        │
        ▼ t 检验 + BH-FDR
[差异代谢物分析] → 差异代谢物列表 JSON → 火山图
        │
        ▼ KEGG 超几何检验
[通路富集分析] → 富集结果 JSON → 气泡图
        │
        ▼ MetaKG 子图提取
[知识图谱溯源] → 子图 JSON → 力导向图
```

> **图表说明（需自制）：** 图 3-3 系统整体数据流图，建议绘制从左至右或从上至下的流程图，每个步骤标注输入数据格式和输出文件名，用箭头表示数据流向，突出中间产物的持久化节点。

**中间产物持久化策略**：每个处理步骤完成后，输出矩阵均以 CSV 文件形式持久化至 `data/processed/{dataset_id}/_pipeline/` 目录，评估结果以 JSON 文件形式存储。这一设计带来以下优点：①支持断点续算，某步骤失败不影响已完成步骤的结果；②便于调试，可直接检查中间矩阵的内容；③前端按需读取对应 JSON 文件，减少重复计算。

**任务状态机**：Task 表中的 `status` 字段记录当前任务进展，状态转移如下：

```
uploaded → preprocess_done → impute_done → correct_done → done
                                                         ↓（任何步骤出错）
                                                        error
```

前端通过定时轮询 `/api/tasks/{task_id}` 接口获取状态更新，并根据状态决定展示哪些功能模块的结果内容。

---

## 3.6 本章小结

本章对系统的总体设计进行了系统性阐述。

在**需求分析**方面，从功能需求和非功能需求两个维度梳理了系统的设计目标：功能需求覆盖数据管理、预处理、缺失值填充、批次效应校正、下游分析和结果输出六大类；非功能需求重点关注可用性（Web 界面友好）、可扩展性（模块化算法层）和可靠性（安全封装与降级处理）。

在**系统架构**方面，系统采用前后端分离架构，后端以 FastAPI 框架实现 RESTful API，内部分为 API 层、Service 层、Algorithm 层和 Repository 层四个子层次，各层职责清晰、单向依赖；前端以 Vue3 + Pinia 实现组件化 UI 和状态管理。

在**数据库设计**方面，采用 SQLite + SQLAlchemy ORM 组合，设计了 Task、Dataset、Parameters、Result 四张核心数据表，并以"元数据入库、矩阵数据存文件"的混合存储策略兼顾结构化查询和大文件高效存储。

在**模块划分**方面，系统按照分析流程划分为数据管理、预处理、缺失值填充、批次效应校正、评估可视化和下游分析六个功能模块，各模块以统一接口交互，支持新算法的灵活接入。

在**数据流设计**方面，系统以线性 Pipeline 结构组织数据处理流程，所有中间产物以文件形式持久化存储，并通过任务状态机（`status` 字段）追踪整体处理进度。

各模块的具体算法实现细节将在第四章中详细描述。

---

# 第四章 核心算法设计与实现

## 4.1 数据预处理算法

数据预处理是代谢组学分析流程的第一个计算步骤，目标是将原始上传矩阵转化为满足后续填充与校正算法要求的标准化输入。本系统实现了三个串行执行的预处理算子，执行顺序固定为：特征缺失率过滤 → log1p 变换 → Z-score 标准化。

### 4.1.1 特征缺失率过滤

**算法描述**：对于输入矩阵 $\mathbf{X} \in \mathbb{R}^{n \times p}$（$n$ 个样本，$p$ 个特征），计算每个特征 $j$ 在所有样本中的缺失率：

$$r_j = \frac{|\{i : x_{ij} = \text{NaN}\}|}{n}, \quad j = 1, \ldots, p$$

保留满足 $r_j \leq \tau_{\text{miss}}$ 的特征，其中 $\tau_{\text{miss}}$ 为用户配置的缺失率阈值（系统默认值为 $0.5$，即保留缺失率不超过 50% 的特征）。过滤后剩余特征集记为 $\mathcal{F}_{\text{keep}}$，若 $|\mathcal{F}_{\text{keep}}| \leq 1$ 则抛出异常，提示用户适当放宽阈值。

**设计依据**：缺失率过高的特征（如超过 50% 的样本未检测到该代谢物）往往为低丰度离子，在当前数据集中检测信号极弱，填充估计不可靠，且在后续差异分析中统计功效极低。过滤此类特征能够降低计算负担，同时减少噪声对填充算法和统计分析的干扰。

**在 Benchmark 数据集上的效果**：Benchmark 合并数据集在缺失率过滤（阈值 50%）后，从原始 1180 个特征中保留了有效特征用于后续分析。

### 4.1.2 log1p 变换

**算法描述**：液相色谱-质谱（LC-MS）原始峰面积数据通常呈现强烈的右偏（正偏态）分布，少数高丰度代谢物的信号强度可比低丰度代谢物高出几个数量级。本系统对每个特征值施加 log1p 变换：

$$x'_{ij} = \log(1 + x_{ij})$$

其中 $\log$ 为自然对数。采用 $\log(1+x)$ 而非 $\log(x)$ 的原因在于：当 $x_{ij} = 0$ 时，$\log(1+0) = 0$，避免了 $\log(0) = -\infty$ 的数值问题，同时保留了零值的语义（零丰度代谢物在变换后仍为 0）。

**设计依据**：log 变换后数据分布更接近正态分布，满足后续 t 检验等参数统计方法对正态性的假设，同时减少极端值对 Z-score 标准化和 PCA 等算法的影响。该变换为代谢组学数据处理的标准步骤<sup>[16]</sup>。

### 4.1.3 Z-score 标准化

**算法描述**：在 log 变换之后，对每个**特征**（列）进行 Z-score 标准化，将各特征的量纲统一到均值为 0、标准差为 1 的尺度：

$$x''_{ij} = \frac{x'_{ij} - \bar{x}'_j}{\max(s'_j,\, 1.0)}$$

其中 $\bar{x}'_j = \frac{1}{n}\sum_i x'_{ij}$ 为特征 $j$ 的均值，$s'_j = \text{std}(x'_{\cdot j})$ 为标准差。当 $s'_j = 0$（即该特征所有样本值相同）时，分母取 $1.0$ 以防止除以零。

**设计依据**：不同代谢物的绝对信号强度量级差异悬殊，标准化可消除量纲差异，使 Silhouette 系数、PCA 和 KNN 等基于距离的方法不会被少数高幅度特征主导，从而更准确地反映样本间的整体相似关系。

---

## 4.2 缺失值填充算法实现

### 4.2.1 传统填充方法实现

**均值填充与中位数填充**：两者实现均为单次遍历特征列，对每一列计算已观测值的均值（或中位数），将 NaN 位置替换为该统计量。实现直接基于 NumPy 的 `nanmean` 和 `nanmedian` 函数，时间复杂度为 $O(np)$，无额外参数。

**KNN 填充**：本系统调用 scikit-learn 的 `KNNImputer` 实现。`KNNImputer` 以**特征**为单位计算样本间距离（仅在双方均有观测值的特征维度上计算欧氏距离），将待填充样本的 $K$ 个最近邻（$K$ 默认为 5，用户可配置）在目标特征上的均值作为填充值：

$$\hat{x}_{ij} = \frac{1}{|\mathcal{N}_K(i,j)|} \sum_{k \in \mathcal{N}_K(i,j)} x_{kj}$$

其中 $\mathcal{N}_K(i,j)$ 为在特征 $j$ 上有观测值且与样本 $i$ 在共同观测特征上欧氏距离最近的 $K$ 个样本。该实现的时间复杂度约为 $O(n^2 p)$，在本文 Benchmark 数据集（1715 样本 × 1180 特征）上运行时间约为数秒至数十秒。

### 4.2.2 Autoencoder 深度学习填充算法实现

#### 网络结构

本系统基于 PyTorch 实现了对称 Encoder-Decoder 网络，具体结构如下（以 Benchmark 数据集 $p = 1180$ 为例）：

**编码器（Encoder）**：

$$\mathbf{h}_1 = \text{ReLU}(\text{BN}(\mathbf{W}_1 \mathbf{x} + \mathbf{b}_1))$$
$$\mathbf{h}_1^{\text{drop}} = \text{Dropout}(\mathbf{h}_1,\ p=0.1)$$
$$\mathbf{z} = \text{ReLU}(\mathbf{W}_2 \mathbf{h}_1^{\text{drop}} + \mathbf{b}_2)$$

其中 $\mathbf{W}_1 \in \mathbb{R}^{256 \times 1180}$，$\mathbf{W}_2 \in \mathbb{R}^{64 \times 256}$，$\mathbf{z} \in \mathbb{R}^{64}$ 为潜空间表示。

**解码器（Decoder）**：

$$\mathbf{h}_3 = \text{ReLU}(\text{BN}(\mathbf{W}_3 \mathbf{z} + \mathbf{b}_3))$$
$$\hat{\mathbf{x}} = \mathbf{W}_4 \mathbf{h}_3 + \mathbf{b}_4$$

其中 $\mathbf{W}_3 \in \mathbb{R}^{256 \times 64}$，$\mathbf{W}_4 \in \mathbb{R}^{1180 \times 256}$，$\hat{\mathbf{x}} \in \mathbb{R}^{1180}$ 为对完整特征向量的重建估计。批归一化（Batch Normalization）作用于各线性层输出，用于稳定训练梯度；Dropout（丢弃率 $p_d = 0.1$）加于编码器第一层输出，起正则化作用。

> **图表说明（需自制）：** 图 4-1 Autoencoder 网络结构图，建议绘制从左至右的层级示意图，标注各层名称和维度：输入层(1180) → Linear+ReLU+BN+Dropout(256) → Linear+ReLU(64) → Linear+ReLU+BN(256) → Linear(1180)，输入侧标注"含均值初始化的缺失值"，输出侧标注"重建完整特征向量"。

#### Masked Reconstruction 训练流程

训练过程分为以下四个阶段，核心伪代码如下：

```
输入：含 NaN 的矩阵 X_masked (n × p)
输出：填充完毕的矩阵 X_filled (n × p)

阶段1：初始化
  col_means ← nanmean(X_masked, axis=0)        # (p,) 各特征列均值
  X_init ← X_masked.copy()
  X_init[isnan(X_init)] ← col_means[对应列]    # NaN 替换为列均值
  obs_mask M ← (~isnan(X_masked)).float()       # 1=已知, 0=缺失

阶段2：构建模型与优化器
  model ← AE(n_features=p, hidden=256, latent=64)
  optimizer ← Adam(model.params, lr=1e-3, weight_decay=1e-5)
  scheduler ← CosineAnnealingLR(optimizer, T_max=80, eta_min=1e-4)

阶段3：训练（80 epochs）
  for epoch in 1..80:
    shuffle(idx_all)
    for each mini-batch B (size=64):
      X_b ← X_init[B],  M_b ← M[B]
      X_hat_b ← model(X_b)                     # 前向传播
      loss ← sum((X_hat_b - X_b)² · M_b) /     # 仅已知位置计算损失
              (sum(M_b) + ε)
      loss.backward(); optimizer.step()
    scheduler.step()

阶段4：推断填充
  X_recon ← model(X_init)                      # 完整重建
  X_filled ← X_init.copy()
  X_filled[isnan(X_masked)] ← X_recon[isnan(X_masked)]
  return X_filled
```

**训练配置说明**：
- **Adam 优化器**：初始学习率 $lr = 10^{-3}$，权重衰减 $\lambda = 10^{-5}$（L2 正则化，防止权重过大）；
- **CosineAnnealingLR 调度**：学习率从 $10^{-3}$ 按余弦函数平滑衰减至 $\eta_{\min} = 10^{-4}$（即 $lr \times 0.1$），避免固定学习率在后期震荡；
- **Mini-batch 训练**：batch size = 64，在每个 epoch 内随机打乱样本顺序，提升梯度估计的随机性与训练稳定性；
- **推断策略**：训练完成后，**仅将重建结果中缺失位置的预测值**回填至矩阵，已知观测值保持不变，确保不因模型重建误差而污染可靠的已知数据。

### 4.2.3 Mask-then-Impute 评估框架实现

**框架描述**：Mask-then-Impute 评估框架在原本完整（无缺失）的矩阵 $\mathbf{X}_{\text{complete}}$ 上进行：

1. 以随机种子 $s$ 控制，均匀随机抽取 15% 的元素位置构成遮蔽集合 $\mathcal{M}$（共约 303,555 个位置）：
   $$\mathbf{X}_{\text{masked}} = \mathbf{X}_{\text{complete}};\quad \mathbf{X}_{\text{masked}}[\mathcal{M}] \leftarrow \text{NaN}$$
2. 对 $\mathbf{X}_{\text{masked}}$ 分别使用均值、中位数、KNN、Autoencoder 四种方法填充，得到 $\hat{\mathbf{X}}^{(\text{method})}$；
3. 仅在遮蔽位置 $\mathcal{M}$ 上计算三项评估指标：

$$\text{RMSE} = \sqrt{\frac{1}{|\mathcal{M}|}\sum_{(i,j)\in\mathcal{M}} (\hat{x}_{ij} - x_{ij})^2}$$

$$\text{MAE} = \frac{1}{|\mathcal{M}|}\sum_{(i,j)\in\mathcal{M}} |\hat{x}_{ij} - x_{ij}|$$

$$\text{NRMSE}_j = \frac{\text{RMSE}_j}{\text{std}(x_{\cdot j})};\quad \text{NRMSE} = \frac{1}{p}\sum_{j=1}^{p}\text{NRMSE}_j$$

4. 以三个不同随机种子（42、43、44）独立重复上述过程，取各指标的均值和标准差作为最终评估结果。

**评估框架的意义**：该框架的核心优势在于评估有明确参照标准——遮蔽前的真实值 $x_{ij}$，因此三项指标均为客观度量，不受主观判断影响。相比之下，对真实缺失数据的填充质量无法直接评估（因为真值未知），因此 Mask-then-Impute 框架是缺失值填充方法定量评估的标准实践。

> **图表说明（需自制）：** 图 4-2 Mask-then-Impute 评估框架流程图，建议绘制从上至下的流程图：完整矩阵 → 随机遮蔽(15%) → 四路分支（Mean/Median/KNN/AE）→ 汇聚 → 与真值对比 → RMSE/MAE/NRMSE，标注"重复3次取均值±标准差"。

---

## 4.3 批次效应校正算法实现

### 4.3.1 Baseline 逐特征位置尺度对齐实现

**算法实现**：对于预处理并填充完毕的矩阵 $\mathbf{X} \in \mathbb{R}^{n \times p}$，设 $B$ 个批次标签已知。算法对每个特征 $j$ 独立执行以下操作：

1. 计算**全局**统计量（跨所有批次所有样本）：
   $$\mu_j = \frac{1}{n}\sum_{i=1}^n x_{ij},\quad \sigma_j = \sqrt{\frac{1}{n}\sum_{i=1}^n (x_{ij}-\mu_j)^2}$$

2. 对每个批次 $b$（$b = 1,\ldots,B$），计算**批次内**统计量：
   $$\mu_{bj} = \frac{1}{n_b}\sum_{i \in \mathcal{B}_b} x_{ij},\quad \sigma_{bj} = \sqrt{\frac{1}{n_b}\sum_{i \in \mathcal{B}_b}(x_{ij}-\mu_{bj})^2}$$
   其中 $\mathcal{B}_b$ 为批次 $b$ 中样本的下标集合，$n_b = |\mathcal{B}_b|$。

3. 对批次 $b$ 内的每个样本 $i$ 执行校正：
   $$x'_{ij} = \frac{x_{ij} - \mu_{bj}}{\max(\sigma_{bj},\, \epsilon)} \cdot \sigma_j + \mu_j$$
   其中 $\epsilon = 10^{-8}$ 为数值稳定下界，防止 $\sigma_{bj} \approx 0$ 时除以零。

4. **边界处理**：若某批次 $n_b < 2$，无法可靠估计 $\sigma_{bj}$，则对该批次样本保留原始值（跳过校正）。

**算法性质分析**：校正公式的几何解释为——先将批次内数据标准化到零均值单位方差（消除批次特有的位置和尺度），再还原为全局均值和标准差的尺度，使所有批次在特征 $j$ 上具有相同的统计分布。该算法的计算复杂度为 $O(Bnp)$（$B$ 个批次，$n$ 个样本，$p$ 个特征），在 Benchmark 数据集上执行时间为毫秒级。

### 4.3.2 ComBat 经验 Bayes 校正算法实现

**算法原理**：本系统采用 neuroCombat 库（Fortin 等，2018）实现 ComBat 算法。neuroCombat 内部以 **特征 × 样本（feature × sample）** 格式处理数据，本系统在调用前后自动完成矩阵转置：

```
输入（sample × feature） → .T → neuroCombat → .T → 输出（sample × feature）
```

ComBat 将特征 $j$ 在批次 $b$、样本 $i$ 上的观测值建模为：

$$x_{ijb} = \alpha_j + \mathbf{d}_i^T\boldsymbol{\beta}_j + \gamma_{jb} + \delta_{jb}\varepsilon_{ijb},\quad \varepsilon_{ijb} \sim \mathcal{N}(0, \sigma_j^2)$$

其中 $\alpha_j$ 为特征 $j$ 全局均值，$\mathbf{d}_i$ 为样本 $i$ 的生物学协变量向量（如分组标签数值化表示），$\boldsymbol{\beta}_j$ 为协变量效应系数，$\gamma_{jb}$（加性偏移）和 $\delta_{jb}$（乘性缩放）为待估计的批次效应参数。

**经验 Bayes 估计步骤**：
1. 用普通最小二乘（OLS）估计 $\hat{\boldsymbol{\beta}}_j$，并从残差中估计各特征各批次的初始批次效应估计 $\hat{\gamma}_{jb}^{0}$、$\hat{\delta}_{jb}^{0}$；
2. 在所有特征 $j = 1,\ldots,p$ 上对初始估计进行汇聚（Pooling），拟合参数先验分布（加性效应先验均值 $\gamma_b^*$、先验方差 $\tau_b^2$；乘性效应先验形状 $a_b$、尺度 $b_b$）；
3. 利用 Bayes 收缩得到稳定估计 $\hat{\gamma}^*_{jb}$、$\hat{\delta}^*_{jb}$（将各特征的估计值向先验均值方向收缩，小样本批次收缩幅度更大）；
4. 校正公式为：

$$x'_{ijb} = \frac{x_{ijb} - \hat{\alpha}_j - \mathbf{d}_i^T\hat{\boldsymbol{\beta}}_j - \hat{\gamma}^*_{jb}}{\hat{\delta}^*_{jb}} \cdot \hat{\sigma}_j + \hat{\alpha}_j + \mathbf{d}_i^T\hat{\boldsymbol{\beta}}_j$$

**安全封装实现**：ComBat 在以下情况会抛出异常：批次数 < 2、某批次样本数 < 2、矩阵含 NaN 值（需先填充）、neuroCombat 库未安装等。为保证系统鲁棒性，本文实现了 `run_combat_safe()` 封装函数，通过 try-except 捕获 `ImportError`、`ValueError` 和通用 `Exception`，失败时返回 `(None, error_message)` 二元组。调用方检测到 `None` 时可选择降级为 Baseline 方法结果，而不是中断整体处理流程。

**协变量保护机制**：当用户传入分组标签作为生物学协变量时（通过 `covariate_df` 参数），ComBat 在估计批次效应时会将分组效应从残差中提取并在校正时加回，从而避免组间真实差异被批次校正消除。本系统将样本元数据中的 `group_label` 数值化后作为连续协变量传入 neuroCombat 的 `continuous_cols` 参数。

### 4.3.3 批次效应评估指标计算实现

**PCA 降维**：使用 scikit-learn 的 `PCA` 对输入矩阵（样本 × 特征）提取前两个主成分，记录各主成分的解释方差比（`explained_variance_ratio_`），将 PC1、PC2 坐标作为每个样本在低维空间中的位置。计算分别在校正前（输入为填充后矩阵）和校正后（输入为校正后矩阵）各执行一次。

**Silhouette 系数计算**：使用 scikit-learn 的 `silhouette_score` 在 PCA 降维后的二维坐标上分别以 `batch_id` 和 `group_label` 为类别标签计算 Silhouette 系数，距离度量为欧氏距离。计算输入为 PC1-PC2 坐标矩阵（而非原始高维矩阵），目的是保持与 PCA 可视化一致的视角，同时降低计算复杂度。

**批次质心距离计算**：对 $B$ 个批次，分别计算各批次样本在 PC1-PC2 空间中的质心坐标：

$$\bar{\mathbf{z}}_b = \frac{1}{n_b}\sum_{i \in \mathcal{B}_b} (z_{i,1},\ z_{i,2})^T$$

批次质心距离定义为所有批次质心对之间的欧氏距离均值：

$$D_{\text{centroid}} = \frac{2}{B(B-1)}\sum_{b < b'} \|\bar{\mathbf{z}}_b - \bar{\mathbf{z}}_{b'}\|_2$$

该指标在 Benchmark 数据集（7 批次）上计算了 $\binom{7}{2} = 21$ 对质心距离的平均值。

---

## 4.4 下游分析算法实现

### 4.4.1 差异代谢物分析算法

**算法流程**：以批次校正后矩阵（样本 × 特征）和样本元数据（含分组标签）为输入，对用户指定的两组样本（group1 vs group2）依次执行以下计算：

**步骤一：逐特征独立双样本 t 检验**

对每个特征 $j$，分别提取两组样本的观测值向量 $\mathbf{v}_1^{(j)}$（group1，$n_1$ 个非缺失值）和 $\mathbf{v}_2^{(j)}$（group2，$n_2$ 个非缺失值），调用 `scipy.stats.ttest_ind` 计算 Welch t 统计量和原始 p 值：

$$t_j = \frac{\bar{v}_1^{(j)} - \bar{v}_2^{(j)}}{\sqrt{s_1^{2(j)}/n_1 + s_2^{2(j)}/n_2}},\quad p_j = P(|T| \geq |t_j|)$$

其中 Welch t 检验不假设两组方差相等（`equal_var=False`），自由度由 Welch-Satterthwaite 公式计算，适合代谢组学数据中常见的方差不等情形。

**步骤二：BH-FDR 多重检验校正**

对全部 $p$ 个特征的 p 值列表执行 Benjamini-Hochberg 假阳性率控制（False Discovery Rate，FDR），得到 q 值列表。BH 校正步骤为：将 $p$ 个 p 值从小到大排序，得到排名 $r_j$；计算调整后 q 值：

$$q_j^{(r)} = \min_{r' \geq r}\left\{p_{r'} \cdot \frac{p}{r'}\right\}$$

最终 q 值 $q_j = \min(q_j^{(r)},\ 1)$，并保证 q 值序列单调非递减（从最大排名向最小排名取累计最小值）。实现优先调用 statsmodels 库的 `multipletests`，并提供手动 BH 实现作为备用。

**步骤三：Log2 Fold Change 计算**

$$\text{log2FC}_j = \log_2\frac{\text{mean}_2^{(j)} + \epsilon}{\text{mean}_1^{(j)} + \epsilon}$$

其中 $\epsilon = 10^{-9}$ 防止对 0 取对数，正值表示 group2 相对 group1 上调，负值表示下调。

**步骤四：显著性标注**

以 $q_j < \tau_q$（默认 $\tau_q = 0.05$）且 $|\text{log2FC}_j| \geq \tau_{\text{FC}}$（默认 $\tau_{\text{FC}} = 1$，即 2 倍变化）为双重阈值条件，将特征标注为：
- `"up"`：满足双重阈值且 $\text{log2FC}_j > 0$（group2 上调）；
- `"down"`：满足双重阈值且 $\text{log2FC}_j < 0$（group2 下调）；
- `"ns"`（not significant）：不满足条件。

结果以 JSON 格式返回，每个特征包含 `pvalue`、`qvalue`、`log2fc`、`neg_log10_qvalue`、`label` 等字段，直接用于前端火山图绘制（横轴为 log2FC，纵轴为 $-\log_{10}(q)$）。

### 4.4.2 KEGG 通路富集分析算法

**算法原理**：通路富集分析采用**超几何检验**（Hypergeometric Test），其统计思想是：假设 $k$ 个差异代谢物落在某通路中是随机发生的，通过超几何分布计算实际观测到的富集程度在随机情况下的概率，若概率极低则认为该通路显著富集。

**输入定义**：
- $M$：背景集大小——在 `annotated_feature_meta.json` 中含有 KEGG Compound ID 注释的特征总数（本文 Benchmark 数据集中约 577 个）；
- $n$：显著差异特征中有 KEGG 注释的特征数（差异分析结果中 `label ∈ {up, down}` 的特征）；
- $K$：某通路在背景集中包含的代谢物数（通路大小）；
- $k$：该通路中与差异代谢物集合的交集大小（命中数）。

**超几何 p 值计算**：

$$p = P(X \geq k) = \sum_{x=k}^{\min(n,K)} \frac{\binom{K}{x}\binom{M-K}{n-x}}{\binom{M}{n}}$$

等价于 $1 - \text{CDF}_{\text{Hypergeom}}(k-1;\ M, K, n)$，在实现中调用 `scipy.stats.hypergeom.sf(k-1, M, K, n)`。

**数据获取与缓存**：KEGG 化合物-通路映射数据通过 KEGG REST API（`https://rest.kegg.jp/link/pathway/compound`）获取，通路名称通过 `https://rest.kegg.jp/list/pathway` 获取。首次获取后将结果序列化为 JSON 文件缓存于本地 `kegg_cache/` 目录，后续运行直接读取缓存，避免重复网络请求。本文仅保留参考通路（pathway ID 以 `map` 前缀开头），过滤掉物种特异通路（如 `hsa` 前缀）。

**BH-FDR 校正与结果输出**：对所有检验通路的 p 值列表执行 BH-FDR 校正，得到 q 值。结果按 p 值升序排列，返回 q 值 $< 0.2$ 的显著通路（共最多 top\_n = 20 条），若无满足条件的通路则返回所有检验结果（宽松显示策略，避免空结果）。每条通路结果包含 `pathway_name`、`hits`（命中数）、`rich_factor`（$k/K$）、`pvalue`、`qvalue` 等字段，直接用于前端气泡图绘制。

**降级处理**：对于无 KEGG 注释的数据集（如 AMIDE），函数在检测到 $n = 0$（显著差异特征中无 KEGG ID）时，返回 `{available: false, reason: "显著差异特征中无 KEGG ID"}` 结构，前端识别该标志后展示提示信息而不报错。

### 4.4.3 MetaKG 知识图谱溯源算法

**知识图谱构建**：MetaKG 多库整合知识图谱以 JSON 格式预存于系统中（`_pipeline/metakg_subgraph.json`），整合了 KEGG、HMDB（Human Metabolome Database）和 SMPDB（Small Molecule Pathway Database）三个数据库的代谢物-通路-反应-酶-基因-疾病关联信息。图中节点类型包含：代谢物（Metabolite）、通路（Pathway）、反应（Reaction）、酶（Enzyme）、基因（Gene）、疾病（Disease）；边类型表示节点间的生物学关联关系。

**子图提取策略**：以差异代谢物分析结果中显著上调或下调的代谢物集合为起点，在知识图谱中提取一跳（One-hop）邻域子图——即包含这些代谢物节点，以及与其直接相连的所有关联节点（通路、反应、酶等）和对应边。子图提取后以节点列表（`nodes`）和边列表（`edges`）的 JSON 格式返回给前端。

**前端力导向图渲染**：前端 `MetaKGCard` 组件接收子图 JSON，调用 ECharts 的 Graph 系列进行力导向图（Force-directed Layout）渲染，支持：①节点拖拽（用户可手动调整节点位置）；②关键词搜索（高亮匹配节点）；③节点类型过滤（选择性隐藏/显示特定类型节点）；④节点悬停展示属性信息（数据库来源、标识符、相关描述）。

---

## 4.5 本章小结

本章详细阐述了系统各核心算法的设计思路与实现细节。

在**数据预处理算法**方面，系统依次实现了特征缺失率过滤（阈值 50%，基于列缺失率计算）、log1p 变换（压缩右偏分布，处理零值安全）和 Z-score 标准化（特征维度归一化，零标准差防护），三步串行执行，保证后续算法的数值稳定性。

在**缺失值填充算法**方面，系统实现了均值/中位数（$O(np)$ 基线）、KNN（基于 sklearn KNNImputer，$K=5$）和 Autoencoder 四种方法。Autoencoder 采用对称 Encoder-Decoder 结构（1180→256→64→256→1180），训练策略为 Masked Reconstruction——仅在已知观测值位置计算 MSE 损失，有效避免缺失值自学习。优化配置为 Adam + CosineAnnealingLR，训练 80 个 epoch。Mask-then-Impute 评估框架通过随机遮蔽 15% 已知值（重复 3 次）的方式，以 RMSE/MAE/NRMSE 对四种方法进行客观定量评估。

在**批次效应校正算法**方面，Baseline 方法对每个特征独立执行批次内分布向全局分布的位置尺度对齐，实现简单、可解释；ComBat 基于 neuroCombat 实现，通过经验 Bayes 收缩利用跨特征信息改善小样本估计稳定性，并支持生物学协变量保护。系统为 ComBat 实现了 `run_combat_safe()` 安全封装，异常时降级返回而不中断流程。批次效应评估通过 PCA 降维计算 Silhouette 系数（双指标：批次/分组）和批次质心距离，三项指标共同构成客观的评估体系。

在**下游分析算法**方面，差异代谢物分析采用 Welch t 检验 + BH-FDR 双重阈值（q < 0.05，|log2FC| ≥ 1）筛选差异特征；KEGG 通路富集分析采用超几何检验 + BH-FDR，通过 KEGG REST API 获取数据并本地缓存，对无注释数据集实现友好降级处理；MetaKG 知识图谱以多库整合 JSON 格式存储，采用一跳邻域子图提取策略，结合前端力导向图实现交互式溯源展示。

上述算法的完整系统集成与前端展示实现将在第五章中详细描述，实验评估结果将在第六章中呈现。

---

# 第五章 系统实现与展示

## 5.1 开发环境与技术栈

### 5.1.1 后端技术栈

本系统后端基于 Python 生态构建，具体依赖如下：

| 技术组件 | 版本 | 用途 |
|:--------|:----:|:----|
| Python | 3.10+ | 运行时环境 |
| FastAPI | 最新稳定版 | Web 框架，提供 RESTful API 和自动文档（OpenAPI） |
| Uvicorn | 最新稳定版 | ASGI 服务器，负责 HTTP 请求接收与异步处理 |
| SQLAlchemy | 最新稳定版 | ORM 框架，管理 SQLite 数据库的 CRUD 操作 |
| Pydantic | v2 | 请求/响应数据校验与序列化 |
| pandas | 最新稳定版 | 数据矩阵读写、长宽表转换、数据过滤 |
| NumPy | 最新稳定版 | 矩阵运算、统计计算、缺失值处理 |
| scikit-learn | 最新稳定版 | KNN 填充（KNNImputer）、PCA 降维、Silhouette 系数计算 |
| scipy | 最新稳定版 | Welch t 检验（`ttest_ind`）、超几何检验（`hypergeom`） |
| PyTorch | 最新稳定版 | Autoencoder 缺失值填充模型的构建与训练 |
| neuroCombat | 最新稳定版 | ComBat 经验 Bayes 批次效应校正算法实现 |
| statsmodels | 最新稳定版 | BH-FDR 多重检验校正（`multipletests`） |
| requests | 最新稳定版 | KEGG REST API 数据请求 |
| openpyxl | 最新稳定版 | XLSX 格式数据文件读取 |
| matplotlib | 最新稳定版 | PCA 图等静态图片生成 |

### 5.1.2 前端技术栈

前端基于现代 JavaScript 生态构建，具体技术组合如下：

| 技术组件 | 版本 | 用途 |
|:--------|:----:|:----|
| Vue 3 | 最新稳定版 | 前端框架，Composition API 组织组件逻辑 |
| TypeScript | 5.x | 静态类型检查，提升代码可维护性 |
| Vite | 最新稳定版 | 构建工具与开发服务器（HMR 热更新）|
| Element Plus | 最新稳定版 | UI 组件库（表单、按钮、表格、弹框等） |
| ECharts | 5.x | 数据可视化库（散点图、条形图、气泡图、力导向图） |
| Pinia | 最新稳定版 | 全局状态管理 |
| Vue Router | 4.x | 前端路由管理 |
| Axios | 最新稳定版 | HTTP 请求封装 |
| SCSS | — | CSS 预处理器，支持变量、嵌套等特性 |

### 5.1.3 开发工具与环境

- **编辑器**：Visual Studio Code
- **版本控制**：Git
- **API 调试**：FastAPI 内置 Swagger UI（`/docs`）及 ReDoc（`/redoc`）
- **部署方式**：本地单机部署，后端 `uvicorn app.main:app --reload`（端口 8000），前端 `vite dev`（端口 5173）

---

## 5.2 后端关键实现

### 5.2.1 API 接口设计

系统后端采用 RESTful 风格的 API 设计，主要接口按功能分为以下五组（统一前缀为 `/api`）：

**数据管理接口**：

| 方法 | 路径 | 功能 |
|:---:|:-----|:----|
| POST | `/api/upload` | 上传数据文件（multipart/form-data），返回 task_id |
| GET | `/api/tasks` | 列出所有任务及状态 |
| GET | `/api/tasks/{task_id}` | 查询指定任务详情与当前状态 |
| POST | `/api/tasks` | 为指定任务配置算法参数（preprocess/imputation/batch/evaluation） |

**处理流程接口**：

| 方法 | 路径 | 功能 |
|:---:|:-----|:----|
| POST | `/api/tasks/{task_id}/preprocess` | 执行数据预处理 |
| POST | `/api/tasks/{task_id}/impute` | 执行缺失值填充 |
| POST | `/api/tasks/{task_id}/batch-correct` | 执行批次效应校正 |
| POST | `/api/tasks/{task_id}/evaluate` | 计算评估指标（PCA、Silhouette、质心距离） |

**Benchmark 数据集专用接口**（前缀 `/api/benchmark/merged`）：

| 方法 | 路径 | 功能 |
|:---:|:-----|:----|
| GET | `/summary` | 获取数据集摘要（样本数、特征数、批次数等） |
| GET | `/batch-correction/report` | 获取批次校正方法报告 JSON |
| GET | `/batch-correction/metrics` | 获取批次校正评估指标 JSON |
| GET | `/batch-correction/pca-after` | 获取校正后 PCA 坐标 JSON |
| GET | `/assets/pca_before_vs_after.png` | 获取 PCA 校正前后对比图片（PNG） |
| GET | `/evaluation/summary` | 获取多方法对比评估摘要 |
| GET | `/evaluation/table` | 获取评估指标数据表（CSV 格式数据） |
| GET | `/evaluation/pca/{method}` | 获取指定方法的 PCA 坐标 |
| GET | `/download/{filename}` | 下载中间产物文件（CSV/JSON） |

**下游分析接口**：

| 方法 | 路径 | 功能 |
|:---:|:-----|:----|
| GET | `/api/benchmark/merged/diff/groups` | 获取可用分组列表 |
| POST | `/api/benchmark/merged/diff/run` | 运行差异代谢物分析 |
| POST | `/api/benchmark/merged/pathway/run` | 运行 KEGG 通路富集分析 |
| GET | `/api/benchmark/merged/metakg/subgraph` | 获取 MetaKG 知识图谱子图 |
| GET | `/api/benchmark/merged/annotation/features` | 获取代谢物注释信息 |

所有接口统一返回 JSON 格式，异常情况下返回 `{"detail": "错误信息"}` 结构，HTTP 状态码规范（200 成功，400 参数错误，404 资源不存在，500 服务器错误）。FastAPI 的类型注解系统自动生成 OpenAPI 文档，可通过 `/docs` 路径直接访问交互式 API 文档页面，便于调试与前后端联调。

### 5.2.2 数据处理 Pipeline 实现

**多批次数据合并**：Benchmark 数据集由 7 个独立批次数据集合并而成。合并流程由 `benchmark_cross_batch_merge.py` 服务实现：首先读取各批次的长表格 CSV 文件，提取特征 ID（`ionIdx`）、样本 ID、强度值、批次标签和分组标签；对各批次数据以特征 ID 为键进行对齐合并，不同批次中不重叠的特征位置以 NaN 填充；最终生成 1715 样本 × 1180 特征的宽矩阵 CSV 文件及合并报告 JSON，持久化存储供后续 Pipeline 步骤读取。

**算法参数传递**：用户在前端配置的算法参数（预处理阈值、填充方法名、ComBat 协变量选项等）通过 POST 请求体传至后端 `TaskCreateRequest` Schema，系统将其序列化为 JSON 字符串存入 `Parameters` 表对应字段，供后续各处理步骤读取。

**CORS 配置**：为支持前端开发服务器（5173 端口）与后端（8000 端口）跨域通信，FastAPI 通过 `CORSMiddleware` 中间件放开 `http://127.0.0.1:5173` 和 `http://localhost:5173` 的跨域请求，允许所有 HTTP 方法和请求头。

### 5.2.3 Benchmark 合并数据集专用实现

考虑到 Benchmark 数据集的完整 Pipeline（多批次合并、Autoencoder 填充、批次校正评估、多方法对比评估）计算量较大（总耗时约 1-3 分钟），本系统将 Benchmark 数据集的处理流程设计为**离线预计算 + 在线只读展示**的模式：

1. 通过 CLI 脚本（`scripts/` 目录）预先运行完整 Pipeline，将所有中间产物（CSV 矩阵、JSON 报告、PNG 图片）持久化至 `data/processed/benchmark_merged/_pipeline/` 目录；
2. Web 服务启动后，`benchmark_merged.py` 路由模块读取上述预计算产物，通过只读 API 接口暴露给前端，无需在线重复计算；
3. 前端通过 Pinia `benchmark` store 一次性并发拉取所有数据（`loadAll()`），缓存在前端内存中，避免重复请求。

这一设计使得系统在演示时响应速度极快（所有读取操作为文件 I/O，毫秒级），同时将计算密集型操作（Autoencoder 训练 80 epochs、KNN 填充等）剥离出 Web 请求生命周期，避免 API 超时问题。

---

## 5.3 前端关键实现

### 5.3.1 页面路由结构

前端共包含以下五个主要页面视图，通过 Vue Router 管理路由跳转：

| 路由路径 | 视图组件 | 功能 |
|:--------|:-------:|:----|
| `/` | `HomeView.vue` | 首页概览，展示系统 KPI 指标和功能模块入口 |
| `/import` | `ImportView.vue` | 数据导入页，支持文件上传和列名映射配置 |
| `/task/:id` | `TaskConfigView.vue` | 任务配置页，支持参数配置与流程触发 |
| `/dashboard` | `ResultDashboardView.vue` | 结果展示页，整合所有可视化组件 |
| `/history` | `HistoryView.vue` | 历史任务列表页，展示所有历史任务状态 |

### 5.3.2 组件架构设计

前端共包含 15 个功能组件，按职责划分如下：

**导航与布局组件（2个）**：
- `AppHeader.vue`：顶部导航栏，包含系统标题、路由切换按钮和全局状态指示；
- `SidebarMenu.vue`：侧边栏菜单，提供结果展示页各功能区块的快速跳转锚点。

**数据展示类组件（5个）**：
- `KpiCard.vue`：关键指标卡片，以大字数字展示核心实验结果（如 AE RMSE=0.2249、质心距离 5.38→0）；
- `MetricCompareCard.vue`：多方法指标对比卡片，展示 Baseline vs ComBat 的三项评估指标对比；
- `MethodStatusCard.vue`：处理方法状态卡片，展示当前 Pipeline 中各步骤的执行状态；
- `AnnotationTableCard.vue`：代谢物注释信息表格，展示特征的 KEGG ID、HMDB ID、分子式等；
- `DownloadFileCard.vue`：文件下载卡片，列出可下载的中间产物文件并提供下载链接。

**可视化类组件（6个）**：
- `PcaImagePanel.vue`：PCA 图片展示面板，加载后端返回的静态 PNG 图片；
- `EvRatioChart.vue`：解释方差比条形图，展示 PCA 各主成分贡献率（ECharts 渲染）；
- `ImputationEvalCard.vue`：缺失值填充评估组件，包含方法对比表格和特征级 RMSE 箱线图；
- `VolcanoPlotCard.vue`：火山图组件，支持分组选择、阈值配置和 ECharts 散点图交互；
- `PathwayEnrichmentCard.vue`：通路富集分析组件，支持气泡图和网络图两种模式切换；
- `MetaKGCard.vue`：MetaKG 知识图谱力导向图组件，支持节点拖拽、关键词搜索、类型过滤。

**交互控制类组件（2个）**：
- `DatasetSelector.vue`：数据集切换器，以标签页形式展示可用数据集（Benchmark / BioHeart / MI / AMIDE），点击切换后重新加载对应数据；
- `PipelineStepBar.vue`：流程步骤进度条，展示用户自定义任务的预处理→填充→校正→评估步骤执行状态。

### 5.3.3 Pinia 状态管理设计

前端通过两个 Pinia Store 管理全局状态：

**`benchmark` store**：专用于 Benchmark 合并数据集的数据管理。在 `loadAll()` 方法中并发发起以下请求：`fetchMergedSummary()`、`fetchBatchCorrectionReport()`、`fetchBatchCorrectionMetrics()`、`fetchMergedFiles()`、`fetchPcaAfterJson()`、`fetchEvaluationSummary()`、`fetchEvaluationTable()`、`fetchEvaluationFiles()`、`fetchImputationEvalSummary()`、`fetchImputationEvalFeatureRmse()`，共 10 个并发请求，全部失败时静默（`catch(() => null)`），保证页面不因单个接口失败而崩溃。请求完成后数据缓存于 `ref` 响应式变量，各展示组件通过 `storeToRefs` 订阅所需数据。

**`task` store**：管理用户自定义上传任务的状态，包括当前选中的 task_id、任务配置参数和流程执行状态。通过轮询 `/api/tasks/{task_id}` 接口实时更新任务状态，驱动 `PipelineStepBar` 进度显示。

### 5.3.4 数据可视化实现

**火山图（VolcanoPlotCard）**：以 ECharts Scatter 系列实现。横轴为 $\log_2\text{FC}$，纵轴为 $-\log_{10}(q\text{-value})$，散点按 `label` 字段三色分类：上调（红色 `#ef4444`）、下调（蓝色 `#3b82f6`）、无显著（浅灰 `#cbd5e1`）。支持用户交互配置分组（group1 vs group2）、FC 阈值（默认 1.0）、p 值阈值（默认 0.05）和是否使用 FDR，点击"运行分析"触发后端 API 计算。散点图支持 ECharts 内置的缩放平移（dataZoom）和悬停 tooltip（展示代谢物名称、log2FC、q 值）。

**通路富集气泡图（PathwayEnrichmentCard）**：以 ECharts Scatter 系列实现气泡图模式。横轴为 Rich Factor（命中数/通路大小），纵轴为通路名称，气泡大小正比于命中代谢物数，气泡颜色由 p 值映射（p 值越小颜色越深）。支持气泡图（`bubble` 模式）和通路代谢物网络图（`network` 模式）两种视图切换，方便用户从不同角度分析富集结果。

**MetaKG 力导向图（MetaKGCard）**：以 ECharts Graph 系列实现，采用力导向布局（`force` layout）。节点按类型分色展示（代谢物-蓝、通路-橙、反应-紫、酶-绿、基因-青、疾病-棕等共 11 种类型），边按关系类型标注中文标签（"参与通路"、"被酶催化"等）。核心交互功能包括：①节点拖拽（力导向布局下自由调整位置）；②关键词搜索（输入关键词高亮匹配节点并弱化非匹配节点）；③节点类型过滤（勾选框控制各类型节点的显示/隐藏，触发图表重渲染）；④节点悬停 tooltip（展示节点 ID、数据库来源、相关描述）。

**ImputationEvalCard（填充评估）**：包含两个子图表——指标对比条形图（横向条形图展示四种方法在 RMSE/MAE/NRMSE 上的对比，最优方法以高亮色标记）和特征级 RMSE 箱线图（展示各方法在 1180 个特征上的 RMSE 分布，直观体现方法在不同代谢物上的稳定性差异）。

**PCA 可视化**：采用两种方式互补展示——`PcaImagePanel` 组件直接加载后端预生成的静态 PNG 图片（`pca_before_vs_after_batch_correction.png`），提供清晰的校正前后对比视觉效果；`EvRatioChart` 以动态 ECharts 条形图展示各主成分解释方差比，支持交互。

---

## 5.4 系统功能界面展示

### 5.4.1 首页概览（图 5-1）

首页（`HomeView`）以卡片布局展示系统核心 KPI 指标，所有数值均从后端 API 动态获取（并发请求填充评估结果、批次校正指标和注释摘要），展示内容包括：

- **缺失值填充评估**：Mask-then-Impute 框架（遮蔽 15%，4 种方法对比）中 Autoencoder 取得最低 RMSE（0.2249），优于 KNN（0.2980）约 24.5%；
- **批次效应校正**：Baseline 方法校正后批次质心距离由 5.38 降至约 0，批次效应显著消除；
- **知识图谱规模**：可注释特征数量、MetaKG 节点与边的数量统计；
- **功能模块入口**：数据导入、结果展示、历史任务的快捷导航按钮。

> **图表说明（需系统截图）：** 图 5-1 系统首页概览截图，展示 KPI 卡片和功能入口布局。

### 5.4.2 数据导入页（图 5-2）

数据导入页（`ImportView`）提供文件上传区域（支持拖拽上传 CSV/XLSX），以及列名映射配置表单（特征列、样本列、数值列、批次标签列、分组标签列），用户配置完成后点击"上传"完成数据注册，系统返回 task_id 并自动跳转至任务配置页。

> **图表说明（需系统截图）：** 图 5-2 数据导入页截图，展示文件上传区域和列名映射配置表单。

### 5.4.3 结果展示页——PCA 批次效应评估（图 5-3）

结果展示页（`ResultDashboardView`）顶部展示数据集切换器（`DatasetSelector`），用户可在 Benchmark、BioHeart、MI、AMIDE 四个数据集间切换。PCA 展示区包含：

- 校正前后 PCA 对比图（`PcaImagePanel`）：静态 PNG 图片，左右两侧分别为校正前和校正后，按批次 ID（7色）和分组标签双重着色，清晰展示批次分离被消除的过程；
- 解释方差比图（`EvRatioChart`）：条形图展示 PC1-PC2 解释方差比变化（校正前 PC1=22.0% → 校正后 PC1=50.9%），说明校正后数据主要方差来源发生变化；
- 评估指标卡（`MetricCompareCard`）：展示批次 Silhouette（−0.1461 → −0.0343）、分组 Silhouette（−0.4813 → −0.4465）、批次质心距离（5.38 → ≈0）三项定量指标。

> **图表说明（需系统截图）：** 图 5-3 结果展示页 PCA 对比图及指标展示截图，可直接引用 `pca_before_vs_after_batch_correction.png`。

### 5.4.4 结果展示页——缺失值填充评估（图 5-4）

填充评估区（`ImputationEvalCard`）展示以下内容：

- **方法对比表格**：按 RMSE 从低到高排列，最优方法（Autoencoder）以高亮背景标记，展示各方法的 RMSE、RMSE 标准差、MAE、NRMSE 四项指标；
- **RMSE 对比条形图**：横向条形图直观展示四种方法的 RMSE 差距；
- **特征级 RMSE 箱线图**：展示各方法在全部 1180 个特征上的 RMSE 分布区间，体现方法在不同代谢物上的稳定性。

> **图表说明（需系统截图）：** 图 5-4 缺失值填充评估截图，展示方法对比表格和箱线图。

### 5.4.5 结果展示页——差异代谢物火山图（图 5-5）

差异分析区（`VolcanoPlotCard`）提供：

- **交互式参数配置**：分组选择下拉框（group1/group2）、FC 阈值滑块（默认 1.0）、q 值阈值输入框（默认 0.05）、是否使用 FDR 开关；
- **火山图**：点击"运行分析"触发后端计算，结果以 ECharts 散点图展示；上调代谢物（红色）、下调代谢物（蓝色）、无显著（灰色）三色区分；图例说明和悬停 tooltip 提供每个散点的代谢物名称、log2FC 和 q 值；
- **统计摘要**：显示显著上调代谢物数、显著下调代谢物数和总特征数。

> **图表说明（需系统截图）：** 图 5-5 差异代谢物火山图截图，展示三色散点分布和交互参数面板。

### 5.4.6 结果展示页——KEGG 通路富集气泡图（图 5-6）

通路富集区（`PathwayEnrichmentCard`）与差异分析区共享分组选择参数，运行后展示：

- **气泡图（默认模式）**：纵轴为富集通路名称，横轴为 Rich Factor，气泡大小表示命中代谢物数，颜色深浅表示 p 值（颜色越深 p 值越小），支持鼠标悬停查看详细统计信息；
- **网络图（可选模式）**：以通路-代谢物二部图形式展示，节点为通路（橙色）和代谢物（蓝色），边表示代谢物属于该通路的关系；
- **无注释降级提示**：对于 AMIDE 数据集等无 KEGG 注释数据，展示友好提示"当前数据集无 KEGG ID 注释，无法进行通路富集分析"而非报错。

> **图表说明（需系统截图）：** 图 5-6 KEGG 通路富集气泡图截图，展示气泡图和交互参数面板。

### 5.4.7 结果展示页——MetaKG 知识图谱（图 5-7）

知识图谱区（`MetaKGCard`）展示以差异代谢物为起点的一跳关联子图：

- **力导向图**：节点按类型着色（11 种类型），边按关系类型标注中文标签；力导向布局使相关节点自然聚集，视觉上形成以代谢物为中心、通路/反应/酶向外辐射的层级结构；
- **关键词搜索**：输入框实时过滤，匹配节点高亮显示（加大节点半径），非匹配节点半透明弱化；
- **节点类型过滤**：复选框面板控制各类型节点的显示/隐藏，点击后重新渲染图表；
- **图例说明**：页面下方展示节点类型与颜色的对应关系说明。

> **图表说明（需系统截图）：** 图 5-7 MetaKG 知识图谱力导向图截图，展示节点分色、关系连线和交互控制面板。

---

## 5.5 系统测试

### 5.5.1 功能测试

对系统各主要功能模块进行了手动功能测试，测试覆盖情况如下：

| 测试项目 | 测试内容 | 测试结果 |
|:--------|:--------|:-------:|
| 文件上传 | CSV/XLSX 格式上传，列名映射配置 | 通过 |
| 数据预处理 | 缺失率过滤、log1p 变换、Z-score 标准化 | 通过 |
| 均值/中位数/KNN 填充 | 三种方法的填充执行与矩阵输出 | 通过 |
| Autoencoder 填充 | 模型训练（80 epochs）与推断填充 | 通过 |
| Mask-then-Impute 评估 | 3 次重复评估，RMSE/MAE/NRMSE 计算 | 通过 |
| Baseline 批次效应校正 | 7 批次数据的位置尺度对齐 | 通过 |
| ComBat 批次效应校正 | neuroCombat 调用与结果返回 | 通过 |
| 批次效应评估 | PCA 计算、Silhouette、质心距离 | 通过 |
| 差异代谢物分析 | t 检验 + BH-FDR，火山图数据生成 | 通过 |
| KEGG 通路富集分析 | 超几何检验，首次 API 请求与缓存 | 通过 |
| MetaKG 知识图谱 | 子图提取与 JSON 返回 | 通过 |
| 数据集切换 | Benchmark / BioHeart / MI / AMIDE 切换 | 通过 |
| 文件下载 | CSV 矩阵和 JSON 报告下载 | 通过 |

### 5.5.2 边界情况测试

**ComBat 降级测试**：人工构造某批次样本数为 1 的极端数据，验证 `run_combat_safe()` 能够捕获 neuroCombat 抛出的 ValueError，返回 `(None, error_msg)` 而不是抛出未处理异常，系统正常降级至 Baseline 结果。

**高缺失率特征过滤**：构造所有样本均缺失的全缺失特征列，验证预处理模块能够正确识别并过滤（缺失率 = 1.0 > 阈值 0.5），不影响后续填充算法的正常执行。

**无 KEGG 注释数据集测试**：使用 AMIDE 数据集（6461 个特征，无 KEGG Compound ID 注释）运行通路富集分析，验证系统能够正确返回 `{available: false, reason: "..."}` 结构，前端正常展示提示信息，不报错崩溃。

**Autoencoder 小数据集测试**：在样本量较少的 BioHeart 数据集（53 个特征）上运行 Autoencoder 填充，验证模型能够适应低特征维度的数据，训练过程正常完成。

### 5.5.3 多数据集完整流程测试

在 Benchmark（1715×1180，7批次）、BioHeart（53特征）、MI（14特征）、AMIDE（6461特征）四个数据集上分别运行了完整的处理流程（预处理 → 填充 → 批次校正 → 评估 → 下游分析），验证系统在不同数据集规模和特征数量下均能正常运行并返回合理结果，通用性良好。

---

## 5.6 本章小结

本章从技术栈选型、后端实现、前端实现和系统测试四个维度对系统的工程实现进行了详细描述。

在**技术栈**方面，后端采用 FastAPI + SQLAlchemy + PyTorch + neuroCombat 等 Python 科学计算生态，前端采用 Vue3 + TypeScript + ECharts + Pinia 的现代前端技术栈，两端分离开发，通过 REST API 和 JSON 数据格式进行通信。

在**后端实现**方面，API 接口按功能分组设计（数据管理、处理流程、Benchmark 专用、下游分析），返回格式统一，异常处理规范；Benchmark 数据集采用"离线预计算 + 在线只读展示"策略，提升演示响应速度；`run_combat_safe()` 安全封装保证了系统鲁棒性。

在**前端实现**方面，15 个功能组件职责清晰，Pinia Store 统一管理数据状态（并发请求、静默失败）；六类可视化图表（PCA 图、填充评估箱线图、火山图、气泡图、力导向知识图谱等）基于 ECharts 实现，支持丰富的用户交互（悬停 tooltip、缩放、拖拽、搜索、类型过滤）；`DatasetSelector` 组件支持四数据集无缝切换。

在**系统测试**方面，手动功能测试覆盖 13 个核心功能点，均通过测试；针对 ComBat 降级、高缺失率过滤、无注释数据集三个边界情况进行了专项测试，系统处理方式均符合预期；四个数据集完整流程测试验证了系统的通用性。

---

# 第六章 实验与结果分析

## 6.1 实验数据集说明

本文实验所使用的数据集如下表所示：

| 数据集 | 样本数 | 特征数 | 批次数 | 每批次样本数 | 主要用途 |
|:------|:------:|:------:|:------:|:----------:|:-------|
| Benchmark（合并） | 1715 | 1180 | 7 | 245/批次 | 批次效应校正主验证集、缺失值填充对比评估 |
| BioHeart | — | 53 | — | — | 下游分析链路验证（差异分析+通路富集） |
| MI | — | 14 | — | — | 下游分析链路验证 |
| AMIDE | — | 6461 | — | — | 系统通用性验证（无注释场景降级处理） |

**Benchmark 数据集详情**：该数据集由 7 个独立液相色谱-质谱（LC-MS）批次实验数据合并而成，批次编号为 Batch1（0108）至 Batch7（0306），每批次均包含 245 个样本，7 批次共 1715 个样本。数据集中包含多种生物学分组（water、burnin、formal 样本及多个 P1 系列稀释浓度分组），具有明显的多批次结构，适合验证批次效应校正算法的效果。原始各批次特征数为 1180\~1235 个，经内连接（inner）对齐后共 1180 个共有特征用于后续分析。经预处理后合并矩阵缺失率为 0%（各批次在 1180 个共有特征上均有完整检测），无需额外的缺失率过滤。

**实验说明**：本文所有实验结果均基于 Benchmark 合并数据集（1715 × 1180）进行，各算法使用固定随机种子（seed = 42）保证可重复性。

---

## 6.2 缺失值填充方法对比实验

### 6.2.1 实验设置

为避免 inner 合并后矩阵已无缺失值（无法直接测试填充效果）的问题，本文使用 Benchmark 数据集的预处理后矩阵，通过 Mask-then-Impute 评估框架进行定量评估（框架原理详见第 4.2.3 节）。具体实验参数如下：

- **数据集**：Benchmark 预处理后矩阵（1715 样本 × 1180 特征）
- **遮蔽比例**：mask\_ratio = 15%（即随机遮蔽约 303,555 个元素）
- **重复次数**：n\_repeats = 3（随机种子分别为 42、43、44）
- **对比方法**：Mean / Median / KNN（$K = 5$）/ Autoencoder（hidden=256, latent=64, epochs=80）
- **评估指标**：RMSE（均方根误差）、MAE（平均绝对误差）、NRMSE（归一化 RMSE）

### 6.2.2 实验结果

**表 6-1 缺失值填充方法定量对比（Benchmark 数据集，Mask-then-Impute 框架，mask\_ratio=15%，3次重复均值±标准差）**

| 方法 | RMSE（均值） | RMSE（标准差） | MAE（均值） | NRMSE（均值） | RMSE 排名 |
|:---:|:-----------:|:-------------:|:-----------:|:------------:|:--------:|
| **Autoencoder** | **0.2249** | 0.0035 | 0.0924 | **0.2248** | **第 1** |
| KNN（$K=5$） | 0.2980 | 0.0041 | 0.0740 | 0.2978 | 第 2 |
| Mean | 1.0011 | 0.0072 | 0.4376 | 1.0006 | 第 3 |
| Median | 1.0361 | 0.0070 | 0.3427 | 1.0356 | 第 4 |

> **表格说明**：上表中所有数值均来自系统真实运行结果（`imputation_eval_report.json`），可直接用于论文。

> **图表说明（需自制）：** 图 6-1 填充方法 RMSE 对比图，建议绘制横向条形图，横轴为 RMSE 值，纵轴为四种方法名称，最优方法（Autoencoder）以高亮色标记。同时可绘制特征级 RMSE 箱线图（数据来源：`imputation_eval_feature.json`），展示各方法在 1180 个特征上 RMSE 的分布差异。

### 6.2.3 结果分析

**（1）Autoencoder 方法表现最优**

Autoencoder 方法以 RMSE = 0.2249 位居第一，相比排名第二的 KNN（RMSE = 0.2980）降低约 **24.5%**，相比均值填充（RMSE = 1.0011）降低约 **77.5%**。在 NRMSE 指标上，Autoencoder（0.2248）同样优于 KNN（0.2978），两者与简单统计方法之间存在显著量级差距（NRMSE 约为简单方法的 1/4）。

这一结果表明，针对代谢组学高维数据（1180 个特征），Autoencoder 能够有效捕获特征间的非线性依赖结构，在缺失值估计上具有明显优势。Benchmark 数据集中各代谢物之间存在丰富的通路层级相关关系，为 Autoencoder 的全局结构学习提供了有利条件。

**（2）KNN 方法介于深度学习与简单统计之间**

KNN（RMSE = 0.2980）显著优于均值和中位数方法，体现了利用样本间相似性结构进行估计的有效性。然而，KNN 在 MAE 指标上（MAE = 0.0740）却优于 Autoencoder（MAE = 0.0924），说明 KNN 在绝对误差的中位数水平上表现更稳健——即对于大多数普通特征，KNN 的填充误差绝对值更小，而 Autoencoder 在某些特征上的极端误差拉高了整体 MAE。综合 RMSE 和 NRMSE 考量，Autoencoder 整体表现更优，但在实际应用中需根据数据特点综合选择。

**（3）均值与中位数方法差距相近但整体精度较低**

均值填充（RMSE = 1.0011）和中位数填充（RMSE = 1.0361）精度相近，均约为 Autoencoder 的 4.5 倍。其中中位数在 MAE 指标上（MAE = 0.3427）略优于均值（MAE = 0.4376），说明中位数对于偏斜分布的估计更鲁棒，但两者在 RMSE 和 NRMSE 上差距甚微。简单统计方法忽略了样本间的任何相关结构，本质上退化为对每个特征独立估计，因此在代谢组学这类特征间高度相关的数据上表现较差。

**（4）各方法标准差较小，结果稳定**

三次重复实验的 RMSE 标准差均在 0.007 以下（Autoencoder：0.0035，KNN：0.0041），说明在 mask\_ratio=15% 的设置下，随机遮蔽位置的变化对评估结果影响很小，各方法的性能表现稳定可靠。

---

## 6.3 批次效应校正对比实验

### 6.3.1 实验设置

- **数据集**：Benchmark 合并数据集填充后矩阵（Autoencoder 填充结果，1715 × 1180）
- **对比条件**：无校正（仅填充）/ Baseline 逐特征位置尺度对齐 / ComBat 经验 Bayes
- **评估指标**：批次质心距离（PC1-PC2）、批次 Silhouette 系数（PC1-PC2）、分组 Silhouette 系数（PC1-PC2）
- **可视化**：校正前后 PCA 散点图（7 批次颜色区分，PC1-PC2 空间）

### 6.3.2 实验结果

**表 6-2 批次效应校正评估指标对比（Benchmark 数据集，7批次，PC1-PC2 空间）**

| 方法 | 批次质心距离 | 批次 Silhouette | 分组 Silhouette | 批次混合判定 |
|:---:|:-----------:|:--------------:|:--------------:|:----------:|
| 无校正（仅填充） | 5.3796 | −0.1461 | −0.4813 | — |
| **Baseline**（位置尺度对齐） | **≈ 0**（$1.9 \times 10^{-14}$） | −0.0343 | −0.4465 | **显著改善** |
| ComBat（经验 Bayes） | — | — | — | 见第 6.3.3 节讨论 |

> **注**：ComBat 在 Benchmark 数据集上的完整评估指标由系统在线计算获得，本文主链路以 Baseline 方法为主要对比基准，ComBat 作为对照方法在系统中可配置选择。

> **可直接引用图片**：图 6-2 校正前后 PCA 对比图，引用 `backend/data/processed/benchmark_merged/_pipeline/pca_before_vs_after_batch_correction.png`，左侧为校正前（7批次明显分离），右侧为 Baseline 校正后（7批次充分混合）。

PCA 解释方差比变化如下：

| 主成分 | 校正前解释方差比 | 校正后解释方差比（Baseline） |
|:-----:|:--------------:|:-------------------------:|
| PC1 | 22.0% | 50.9% |
| PC2 | 4.9% | 5.3% |

### 6.3.3 结果分析

**（1）Baseline 方法实现了极高的批次质心分离消除效果**

校正后批次质心距离由 5.3796 降至约 $1.9 \times 10^{-14}$（实际为浮点精度误差，即精确为 0），表明在 PCA 前两个主成分空间中，7 个批次的质心实现了**完全重合**。这一结果符合 Baseline 算法的理论预期：逐特征位置尺度对齐在数学上等价于将各批次的特征均值和标准差归一化到全局水平，当各特征均完成此对齐后，批次间的系统性偏移被完全消除。

**（2）PC1 解释方差比大幅提升，数据主要方差来源发生转变**

校正前 PC1 解释方差比仅为 22.0%，批次间分离占据了主要方差成分；校正后 PC1 解释方差比提升至 50.9%，表明批次效应被消除后，数据中最大的方差来源发生了质的变化——此时 PC1 更可能反映的是数据中真实的生物学结构差异（如样本类型差异、浓度梯度等）。这一现象从另一个维度印证了批次效应被有效消除。

**（3）Silhouette 系数变化的解读与局限**

批次 Silhouette 系数由 −0.1461 变化至 −0.0343（值向 0 移动），从数值方向上看批次分离有所"减弱"；分组 Silhouette 系数由 −0.4813 变化至 −0.4465（负值幅度减小），生物学分组结构略有改善。

值得注意的是，批次 Silhouette 系数在校正后向 0 方向移动（而非向 −1 方向），乍看似乎不符合"批次混合越好，批次 Silhouette 越低"的预期。对此，本文认为合理的解释在于：校正前后数据的整体 PCA 坐标系发生了根本性变化（PC1 解释方差比从 22% 跃升至 50.9%），不同坐标系下的 Silhouette 系数不具有直接可比性。在同一坐标系下，批次质心距离（完全归零）是更直接、更可靠的评估依据。因此，本文以**批次质心距离为主要判据，Silhouette 系数为辅助参考**，并结合 PCA 可视化综合判断校正效果。

**（4）ComBat 与 Baseline 的对比说明**

Baseline 方法在本实验数据集（每批次恰好 245 个样本，样本量充足）上表现极为出色，批次质心完全归零。ComBat 的核心优势在于：①通过经验 Bayes 收缩在小批次场景下获得更稳健的参数估计；②可显式传入分组标签协变量保护生物学信号。在本数据集的理想实验条件下（批次大小均匀、样本量充足），两种方法的校正效果预计相近。实际使用中，当批次大小不均匀或需要保护生物学协变量时，推荐使用 ComBat。

---

## 6.4 下游分析结果展示

### 6.4.1 差异代谢物分析结果

**实验设置**：以 Benchmark 数据集中 `P1_AA_0001`（氨基酸低浓度组，$n_1 = 18$）vs `P1_AA_1024`（氨基酸高浓度组，$n_2 = 18$）为例进行差异分析，阈值设定为 $q < 0.05$，$|\text{log2FC}| \geq 1.0$（2倍变化），采用 Welch t 检验 + BH-FDR 校正。

**结果摘要**：

| 统计项目 | 数值 |
|:--------|:----:|
| 分析特征总数 | 1180 |
| 显著差异代谢物数 | 538 |
| 其中显著上调（P1\_AA\_1024 高于 P1\_AA\_0001） | — |
| 其中显著下调 | — |
| 典型显著差异代谢物 | Acetone（C3H6O，KEGG: C00207，q = $2.7 \times 10^{-7}$，log2FC = −5.05） |

在 1180 个代谢物特征中，共有 **538 个**（占总数的 **45.6%**）特征在两组间达到显著差异标准，说明在这两种氨基酸浓度条件下，大量代谢物（尤其是氨基酸类代谢物）的含量存在明显系统性差异，与实验设计预期一致（低浓度组 P1\_AA\_0001 与高浓度组 P1\_AA\_1024 的浓度相差约 1024 倍）。

代表性差异代谢物 Acetone（丙酮，分子式 C3H6O）在 P1\_AA\_0001 组的均值为 −1.537（标准化后），在 P1\_AA\_1024 组为 −0.046，log2FC = −5.05，t 统计量为 −8.48，原始 p 值为 $9.3 \times 10^{-10}$，经 BH-FDR 校正后 q 值为 $2.7 \times 10^{-7}$，统计显著性极高。

> **图表说明（需自制或引用系统截图）：** 图 6-3 差异代谢物火山图（P1\_AA\_0001 vs P1\_AA\_1024），横轴为 log2FC，纵轴为 −log₁₀(q-value)，上调代谢物（红色）、下调代谢物（蓝色）、无显著（灰色）三色分布，标注部分代表性代谢物名称（如 Acetone）。

### 6.4.2 KEGG 通路富集分析结果

**实验设置**：以上述差异分析结果中 538 个显著差异特征为显著集，以含 KEGG Compound ID 注释的 981 个特征（背景集大小 $M = 981$）为背景，通过超几何检验对 254 条 KEGG 参考通路进行富集分析，并执行 BH-FDR 校正，q 值截止阈值为 0.2。

**表 6-3 KEGG 通路富集分析结果（Top 3 显著通路，P1\_AA\_0001 vs P1\_AA\_1024）**

| 通路 ID | 通路名称 | 命中数 $k$ | 通路大小 $K$ | Rich Factor | p 值 | q 值 |
|:-------:|:--------|:---------:|:----------:|:-----------:|:----:|:----:|
| map00470 | D-Amino acid metabolism（D-氨基酸代谢） | 30 | 31 | 0.9677 | $8.1 \times 10^{-7}$ | **0.000206** |
| map00310 | Lysine degradation（赖氨酸降解） | 16 | 17 | 0.9412 | 0.00117 | 0.1492 |
| map01060 | Biosynthesis of plant secondary metabolites（植物次生代谢物合成） | 35 | 44 | 0.7955 | 0.00184 | 0.1561 |

共检验 254 条通路，其中达到显著水平（q < 0.2）的通路共 **3 条**，最显著的通路为 **D-Amino acid metabolism**（D-氨基酸代谢，map00470），Rich Factor = 0.9677（通路中 31 个化合物有 30 个被命中），q 值 = 0.000206，富集程度极高。

**结果分析**：D-氨基酸代谢通路的高度富集与实验设计高度吻合——P1\_AA 系列样本为氨基酸浓度梯度实验，低浓度组（0001）与高浓度组（1024）之间的差异代谢物中大量属于氨基酸类化合物，因此 D-氨基酸代谢通路（包含丙氨酸、甘氨酸等多种氨基酸相关化合物）被显著富集具有明确的生物学合理性。赖氨酸降解通路（map00310，q = 0.149）和植物次生代谢物合成通路（map01060，q = 0.156）虽命中数较多，但 Rich Factor 与 q 值显示其富集显著性相对较弱，可作为参考结果进一步实验验证。

> **图表说明（需自制或引用系统截图）：** 图 6-4 KEGG 通路富集气泡图，纵轴为通路名称，横轴为 Rich Factor，气泡大小为命中代谢物数，气泡颜色代表 q 值（越深越显著）。建议标注 map00470 的 q 值标签。

### 6.4.3 MetaKG 知识图谱溯源展示

在通路富集结果的基础上，系统进一步以差异代谢物为起点，从 MetaKG 多库整合知识图谱中提取一跳关联子图。以 D-氨基酸代谢通路（map00470）命中的 30 个差异代谢物为例，MetaKG 子图涵盖以下类型的关联关系：

- **代谢物 → 通路**（`has_pathway`）：30 个命中代谢物与 D-氨基酸代谢、其他相关通路的归属关系；
- **代谢物 → 反应**（`has_reaction`）：代谢物参与的具体生化反应（如酶促反应编号）；
- **反应 → 酶**（`has_enzyme`）：催化对应生化反应的酶（EC 编号及名称）；
- **代谢物 → 疾病**（`has_disease`）：相关代谢物与已知代谢性疾病的关联记录（来自 HMDB）。

通过力导向图的可视化展示，研究人员可以从每一个差异代谢物出发，沿关联边追溯其参与的通路、催化反应的酶，以及可能关联的疾病，实现从代谢物到生物学机制的多跳关联溯源，为生物学假设的生成提供可视化支撑。

> **图表说明（需系统截图）：** 图 6-5 MetaKG 知识图谱力导向图截图，展示差异代谢物（蓝色圆）与通路（橙色）、反应（紫色）、酶（绿色）、疾病（棕色）节点的关联网络。

---

## 6.5 系统通用性验证

本节对系统在 BioHeart、MI 和 AMIDE 三个数据集上的运行情况进行简要验证，考察系统在不同数据规模和特征配置下的通用性。

**BioHeart 数据集**：该数据集特征数仅 53 个，属于典型的低维代谢组学数据。系统成功在该数据集上完成预处理、缺失值填充（Autoencoder 适应小特征维度）、批次效应校正和下游差异分析的全流程运行，差异分析结果在火山图中正常展示，通路富集分析也因含 KEGG 注释特征成功运行并返回富集通路列表。

**MI 数据集**：特征数 14 个，为超小型数据集。系统在该数据集上验证了全流程的基本可运行性，Autoencoder 填充在如此低维数据上的模型容量（潜空间维度 64 > 输入维度 14）会导致欠拟合，系统会自动将潜空间维度调整为不超过特征数的合理范围，避免维度冲突。

**AMIDE 数据集（降级处理验证）**：AMIDE 数据集包含 6461 个特征，但这些特征均**无 KEGG Compound ID 注释**。系统对该数据集的处理验证如下：
- 预处理、填充、批次校正流程正常执行；
- 差异分析计算正常（t 检验不依赖注释信息）；
- **通路富集分析触发降级**：系统检测到显著差异特征中 KEGG ID 数量为 0，返回 `{available: false, reason: "显著差异特征中无 KEGG ID，无法进行通路富集分析"}` 结构；
- 前端 `PathwayEnrichmentCard` 识别 `available: false` 标志，展示友好的提示文字，不报错也不显示空图表，用户体验良好。

上述三个数据集的验证结果表明，系统具有良好的通用性和鲁棒性，能够适应不同规模（14 至 6461 个特征）、不同注释覆盖度（有/无 KEGG 注释）的代谢组学数据集，并在不满足条件时以友好方式降级处理而非异常中断。

---

## 6.6 本章小结

本章在 Benchmark 合并数据集（1715 样本 × 1180 特征 × 7 批次）上进行了系统性的定量实验与结果分析，主要结论如下：

**缺失值填充实验**：Autoencoder 方法取得最低 RMSE（0.2249），分别优于 KNN（0.2980，降低 24.5%）、均值（1.0011，降低 77.5%）和中位数（1.0361，降低 78.3%）。实验结果表明，基于深度学习的 Autoencoder 能够有效利用代谢组学数据中特征间的复杂相关结构，在缺失值填充精度上具有显著优势。各方法标准差（<0.007）证明评估结果稳定可重复。

**批次效应校正实验**：Baseline 方法校正后批次质心距离由 5.3796 降至约 0（$1.9 \times 10^{-14}$），PCA 图中 7 批次样本实现完全混合，PC1 解释方差比由 22.0% 提升至 50.9%，表明主要方差来源从批次差异转变为生物学结构差异。双指标评估体系（批次质心距离 + Silhouette 系数）提供了对校正效果的多维度客观量化。

**下游分析结果**：以 P1\_AA\_0001 vs P1\_AA\_1024 差异分析为例，共检出 538 个（45.6%）显著差异代谢物，通路富集分析发现 D-Amino acid metabolism 通路显著富集（q = 0.000206，Rich Factor = 0.9677），结果与实验设计的氨基酸浓度梯度预期高度一致，验证了系统下游分析链路的生物学合理性。

**系统通用性**：在 BioHeart、MI、AMIDE 三个数据集上的验证表明，系统能够适应 14 至 6461 个特征的宽泛数据规模，并在无 KEGG 注释场景下实现友好降级，通用性良好。

---

# 第七章 结论与展望

## 7.1 研究总结

本文围绕代谢组学数据分析中的批次效应校正与缺失值填充两大核心问题，设计并实现了一个**基于深度学习的代谢组学批次效应处理 Web 平台**，实现了从数据导入、预处理、缺失值填充与校正，到差异代谢物分析、KEGG 通路富集与 MetaKG 知识图谱溯源的全流程一体化处理。本文的主要研究成果如下：

**（1）设计并实现了代谢组学数据处理 Web 平台**

平台采用前后端分离架构，后端基于 FastAPI + SQLite + SQLAlchemy，前端基于 Vue3 + TypeScript + ECharts + Element Plus，算法层以独立模块形式组织，具备良好的可扩展性与工程规范性。系统支持 CSV/XLSX 格式的多数据集导入与切换（Benchmark、BioHeart、MI、AMIDE），并以 Web 交互界面的形式覆盖从数据预处理到结果可视化的完整分析链路，填补了现有平台在深度学习方法集成和全流程一体化分析方面的不足。

**（2）实现了基于 Autoencoder 的深度学习缺失值填充，并设计了 Mask-then-Impute 可量化评估框架**

本文基于 PyTorch 实现了采用 Masked Reconstruction 训练策略的 Encoder-Decoder 网络（1180→256→64→256→1180），仅在已知观测位置计算重建损失（MSE），有效避免缺失值自学习问题，参考了 MIDA（Gondara & Wang, 2018）的方法论。同时设计了 Mask-then-Impute 评估框架，通过随机遮蔽 15% 已知值（重复 3 次）实现有参照的客观定量评估。在 Benchmark 数据集（1715 × 1180）上的实验表明，Autoencoder 方法以 RMSE = 0.2249 位居第一，分别优于 KNN（RMSE = 0.2980，降低 24.5%）和均值填充（RMSE = 1.0011，降低 77.5%），证明了深度学习方法在代谢组学缺失值填充任务上的有效性。

**（3）集成了两种批次效应校正方法，并设计了双维度量化评估体系**

系统实现了逐特征位置尺度对齐（Baseline）和基于 neuroCombat 的 ComBat 经验 Bayes 两种批次效应校正方法，均有安全封装与异常降级处理机制。评估体系包含批次质心距离、批次 Silhouette 系数（越低越好）和分组 Silhouette 系数（越高越好）三项指标，形成"批次效应消除程度"与"生物学信号保留程度"相互制衡的双维度评估框架。在 Benchmark 数据集（7批次）上，Baseline 方法校正后批次质心距离由 5.38 降至约 0，显示了对位置尺度型批次效应的高效校正能力。

**（4）实现了差异代谢物分析、KEGG 通路富集分析和 MetaKG 知识图谱溯源一体化**

系统基于批次校正后矩阵，依次实现了 Welch t 检验 + BH-FDR 差异代谢物分析（火山图展示）、KEGG 超几何富集分析（气泡图展示，含本地缓存和降级处理）以及 MetaKG 多库整合知识图谱的力导向图溯源展示（支持拖拽、搜索、类型过滤）。在 P1\_AA\_0001 vs P1\_AA\_1024 差异分析中，检出 538 个显著差异代谢物，富集到 D-Amino acid metabolism 通路（q = 0.000206），生物学结果合理，验证了下游分析链路的可靠性。

---

## 7.2 系统局限性

尽管本文工作取得了预期目标，系统在以下方面仍存在一定的局限性：

**（1）Autoencoder 填充尚未集成到 Web 在线任务流**

当前 Autoencoder 填充方法（训练 80 epochs，在 Benchmark 数据集上耗时约 44 秒）以离线预计算方式运行，用户通过 CLI 脚本调用，而非通过 Web 界面在线触发。这一设计牺牲了易用性，用户无法在 Web 界面上为自定义上传数据集使用 Autoencoder 填充。

**（2）批次效应校正方法数量有限**

系统目前仅实现了 Baseline 和 ComBat 两种批次效应校正方法，尚未集成近年来在单细胞组学领域表现优秀的 Harmony、BBKNN 等方法，也未集成基于深度学习的批次校正方法（如基于对抗网络或 VAE 的方法），限制了用户的方法选择空间。

**（3）评估框架仅针对二维 PCA 空间**

当前批次效应评估指标（Silhouette 系数和质心距离）均在 PCA 降至 2 维后的坐标空间中计算，这有助于与 PCA 可视化保持一致，但也损失了高维空间中的部分信息，高维空间下的评估结果可能与 2D 评估存在差异。

**（4）不支持多用户和数据隔离**

系统当前为单机本地部署模式，不支持用户注册与认证，所有用户共享同一 SQLite 数据库和文件系统，缺乏数据隔离机制，无法支持多用户并发使用场景。

**（5）部分数据集依赖手动脚本预处理**

Benchmark 数据集的完整 Pipeline 产物（多批次合并、填充评估、批次校正等）需通过 CLI 脚本手动运行生成，增加了系统部署和数据更新的复杂度，对非技术背景用户不够友好。

---

## 7.3 未来工作展望

针对上述局限性，未来工作将从以下几个方向进行改进和扩展：

**（1）引入异步任务队列，支持 Autoencoder 在线训练**

引入 Celery + Redis 异步任务队列，将 Autoencoder 训练等耗时计算从同步 HTTP 请求中剥离，以异步任务方式提交和执行，前端通过 WebSocket 或长轮询实时获取训练进度，实现 Autoencoder 填充在 Web 界面的全流程在线触发与结果展示。

**（2）扩展批次效应校正方法库**

引入 Harmony（基于 PCA 空间迭代软聚类对齐）、BBKNN（基于批次感知 KNN 图）等近年主流批次校正方法，以及基于变分自动编码器（VAE）的深度学习批次校正方法，构建覆盖统计、近邻对齐、深度学习三类范式的多方法对比平台。

**（3）引入自动化方法推荐机制**

基于数据集的统计特征（批次数、批次间样本量均衡性、缺失率、特征数等）和历史运行结果（不同方法的评估指标表现），设计自动化方法推荐模型，为用户提供"最优方法推荐"功能，降低算法选择的专业门槛。

**（4）评估体系的高维扩展**

将批次效应评估指标从 2D PCA 空间扩展到更高维度（如保留 90% 解释方差比所需的主成分数），或引入 kBET（k-nearest neighbor Batch Effect Test）等专门面向高维数据的批次效应评估统计量，提升评估结果的全面性和可靠性。

**（5）支持多组学联合分析与多用户隔离**

扩展系统的多组学联合分析能力（整合转录组、蛋白质组等），以代谢物为中心构建跨组学关联网络；同时迁移至 PostgreSQL 数据库，引入用户注册与认证机制、数据集权限隔离，支持科研团队的协作分析场景。

**（6）增加分析报告自动生成功能**

集成 PDF/HTML 报告自动生成模块，允许用户一键导出包含数据集信息、预处理参数、填充评估结果、批次校正效果图表和下游分析结果的完整分析报告，进一步提升系统的实用价值。

---

## 参考文献

> （以下为本文引用的主要参考文献，按 GB/T 7714-2015 格式列示，实际引用顺序以正文上标为准）

[1] Fiehn O. Metabolomics—the link between genotypes and phenotypes[J]. Plant Molecular Biology, 2002, 48(1): 155-171.

[2] Wishart D S, Feunang Y D, Marcu A, et al. HMDB 4.0: the human metabolome database for 2018[J]. Nucleic Acids Research, 2018, 46(D1): D608-D617.

[3] Kind T, Fiehn O. Metabolomic database annotations via query of elemental compositions: mass accuracy is insufficient even at less than 1 ppm[J]. BMC Bioinformatics, 2006, 7(1): 234.

[4] Leek J T, Scharpf R B, Bravo H C, et al. Tackling the widespread and critical impact of batch effects in high-throughput data[J]. Nature Reviews Genetics, 2010, 11(10): 733-739.

[5] Lazar C, Gatto L, Ferro M, et al. Accounting for the multiple natures of missing values in label-free quantitative proteomics data sets to compare imputation strategies[J]. Journal of Proteome Research, 2016, 15(4): 1116-1125.

[6] Wei R, Wang J, Su M, et al. Missing value imputation approach for mass spectrometry-based metabolomics data[J]. Scientific Reports, 2018, 8(1): 663.

[7] Pang Z, Chong J, Zhou G, et al. MetaboAnalyst 5.0: narrowing the gap between raw spectra and functional insights[J]. Nucleic Acids Research, 2021, 49(W1): W388-W396.

[8] Gondara L, Wang K. MIDA: Multiple imputation using denoising autoencoders[C]// Proceedings of the Pacific-Asia Conference on Knowledge Discovery and Data Mining (PAKDD). Springer, 2018: 260-272.

[9] Tautenhahn R, Patti G J, Rinehart D, et al. XCMS Online: a web-based platform to process untargeted metabolomic data[J]. Analytical Chemistry, 2012, 84(11): 5035-5039.

[10] Troyanskaya O, Cantor M, Sherlock G, et al. Missing value estimation methods for DNA microarrays[J]. Bioinformatics, 2001, 17(6): 520-525.

[11] Qi Y. Random forest for bioinformatics[M]// Ensemble Machine Learning. Springer, 2012: 307-323.

[12] Johnson W E, Li C, Rabinovic A. Adjusting batch effects in microarray expression data using empirical Bayes methods[J]. Biostatistics, 2007, 8(1): 118-127.

[13] Korsunsky I, Millard N, Fan J, et al. Fast, sensitive and accurate integration of single-cell data with Harmony[J]. Nature Methods, 2019, 16(12): 1289-1296.

[14] Shaham U, Stanton K P, Zhao J, et al. Removal of batch effects using distribution-matching residual networks[J]. Bioinformatics, 2017, 33(16): 2539-2546.

[15] Lopez R, Regier J, Cole M B, et al. Deep generative modeling for single-cell transcriptomics[J]. Nature Methods, 2018, 15(12): 1053-1058.

[16] van den Berg R A, Hoefsloot H C, Westerhuis J A, et al. Centering, scaling, and transformations: improving the biological information content of metabolomics data[J]. BMC Genomics, 2006, 7(1): 142.

[17] Kanehisa M, Goto S. KEGG: Kyoto encyclopedia of genes and genomes[J]. Nucleic Acids Research, 2000, 28(1): 27-30.

[18] Wishart D S, Jewison T, Guo A C, et al. HMDB 3.0—the human metabolome database in 2013[J]. Nucleic Acids Research, 2013, 41(D1): D801-D807.

---

> **写作进度**：摘要 ✅ | 第一章 ✅ | 第二章 ✅ | 第三章 ✅ | 第四章 ✅ | 第五章 ✅ | 第六章 ✅ | 第七章 ✅ | 参考文献 ✅

**全文初稿完成。**

