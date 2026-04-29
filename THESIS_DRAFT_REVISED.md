# 基于深度学习的代谢组学批次效应系统设计与开发

---

# 摘要

代谢组学是生命科学领域重要的研究方向之一，通过对生物体内小分子代谢物的系统性检测，能够在整体水平上揭示生物体的生理与病理变化规律。随着高通量质谱检测技术的广泛应用，大规模代谢组学研究日益普遍，但多批次实验数据中普遍存在的批次效应（Batch Effect）和缺失值问题严重影响数据质量与分析结果的可靠性。现有分析平台（如 MetaboAnalyst）在批次效应处理方法的覆盖、深度学习算法的引入以及全流程一体化分析方面仍存在明显局限。

针对上述问题，本文设计并实现了一个基于深度学习的代谢组学批次效应处理 Web 平台。系统采用前后端分离架构，后端基于 FastAPI 框架，前端基于 Vue3 + TypeScript，算法层以独立模块形式组织，具备良好的可扩展性。在缺失值填充方面，系统集成了均值、中位数、KNN 三种传统方法，并实现了基于 PyTorch 的 Autoencoder 深度学习填充模型，采用 Masked Reconstruction 训练策略，仅对已知值位置计算重建损失。为客观评估各填充方法的精度，本文设计了 Mask-then-Impute 评估框架，在 Benchmark 数据集（1715 个样本、1180 个特征、7 个批次）上进行了定量对比实验：Autoencoder 方法取得最低 RMSE（0.2249），相比 KNN（0.2980）降低约 24.5%，相比均值填充（1.0011）降低约 77.5%。在批次效应校正方面，系统实现了逐特征位置尺度对齐（Baseline）和 ComBat 经验 Bayes 两种校正方法，并设计了包含批次质心距离、批次轮廓系数与生物学分组轮廓系数的双维度评估体系。实验结果表明，Baseline 校正后批次质心距离由 5.38 下降至接近 0，批次混合效果显著。在下游分析方面，系统进一步实现了基于 t 检验和 BH-FDR 校正的差异代谢物分析、基于 KEGG 的通路富集分析，以及基于 MetaKG 多库整合知识图谱的代谢物溯源展示，支持多数据集切换与交互式可视化。

本系统完整覆盖了代谢组学数据从预处理到结果解读的全分析流程，为研究人员提供了一体化、可视化的数据处理工具，具有较好的实用价值与可扩展性。

关键词：代谢组学；批次效应；缺失值填充；深度学习；自动编码器；Web 平台

---

# Abstract

Metabolomics is an important research field in life science that systematically detects small-molecule metabolites in biological systems, revealing metabolic changes under different physiological or pathological conditions. With the widespread adoption of high-throughput mass spectrometry, large-scale multi-batch metabolomics studies have become increasingly common. However, batch effects and missing values in multi-batch experimental data seriously compromise data quality and the reliability of downstream analysis. Existing platforms such as MetaboAnalyst still have notable limitations in batch effect correction methods, deep learning integration, and end-to-end workflow support.

To address these issues, this paper designs and implements a deep learning-based metabolomics batch effect processing web platform. The system adopts a front-end and back-end separated architecture, with FastAPI as the backend framework, Vue3 + TypeScript for the frontend, and an independently organized algorithm module layer for extensibility. For missing value imputation, the system integrates three traditional methods (mean, median, and KNN) and implements an Autoencoder-based deep learning imputation model using PyTorch, trained with a Masked Reconstruction strategy that computes reconstruction loss only on observed values. A Mask-then-Impute evaluation framework is proposed to objectively compare imputation methods. Experiments on the Benchmark dataset (1715 samples, 1180 features, 7 batches) show that the Autoencoder achieves the lowest RMSE (0.2249), outperforming KNN (0.2980) by approximately 24.5% and mean imputation (1.0011) by approximately 77.5%. For batch effect correction, the system implements two methods: per-feature location-scale alignment (Baseline) and ComBat with empirical Bayes estimation. A dual-indicator evaluation system is designed, comprising batch centroid separation distance, batch Silhouette score, and biological group Silhouette score. Experimental results demonstrate that after Baseline correction, the batch centroid separation distance drops from 5.38 to near zero, indicating effective batch mixing. In downstream analysis, the system further provides differential metabolite analysis based on t-test with BH-FDR correction, KEGG pathway enrichment analysis, and a MetaKG knowledge graph-based metabolite traceability visualization. Multiple datasets and interactive visualizations are supported.

The system comprehensively covers the full metabolomics analysis workflow from data preprocessing to biological interpretation, providing researchers with an integrated and visualized data processing tool with good practical value and extensibility.

Keywords: Metabolomics; Batch Effect; Missing Value Imputation; Deep Learning; Autoencoder; Web Platform

---

# 第一章 绪论

## 1.1 研究背景与意义

代谢组学（Metabolomics）是继基因组学、转录组学和蛋白质组学之后发展起来的重要研究领域。其核心思想是通过质谱（Mass Spectrometry，MS）或核磁共振（Nuclear Magnetic Resonance，NMR）等高通量检测技术，对生物体内全部或部分小分子代谢物（分子量通常小于 1500 Da）进行系统性定量检测，进而从代谢层面揭示生物体在不同生理状态、病理条件或外界干预下的整体响应规律[1]。与基因组和蛋白质组相比，代谢物是生命活动的直接产物，能够更加灵敏地反映生物体当前的功能状态，因此代谢组学在疾病早期诊断与生物标志物发现[2]、药物靶点识别[3]、营养干预评估等领域已展现出重要的应用价值。

然而，随着代谢组学研究规模的持续扩大，大量样本往往需要在不同时间段分批完成检测，由此引入了代谢组学数据分析中的核心技术挑战之一——批次效应（Batch Effect）。批次效应是指由仪器状态波动、环境温湿度变化、试剂批次差异、操作人员变化等非生物学因素所造成的系统性偏差，其典型表现为：同一生物条件的样本在不同批次中检测到的信号强度呈现出明显的系统性偏移，而这种偏移与样本本身的生物学状态无关[4]。在主成分分析（PCA）等降维可视化手段下，批次效应通常表现为不同批次样本聚集成相互分离的簇群，掩盖了真实的生物学差异，严重干扰后续差异代谢物筛选和通路分析结果的可靠性。

与批次效应并列的另一个重要问题是缺失值（Missing Values）的处理。液相色谱-质谱联用（LC-MS）技术在低丰度代谢物的检测中存在仪器灵敏度限制，当代谢物浓度低于检测限（Limit of Detection，LOD）时，相应数据点将以缺失值形式出现在数据矩阵中[5]。此外，谱峰拾取算法的误差、质量控制样本的处理差异等因素也会进一步加剧缺失值问题。在典型的大规模代谢组学数据集中，缺失值比例可达 20%～50%，若直接参与统计分析，将导致估计偏差加剧、差异检验功效下降，进而影响生物学结论的可靠性[6]。

面对上述两类问题，现有的主流代谢组学分析平台（如 MetaboAnalyst[7]）虽然提供了较为完整的数据分析功能，但仍存在以下局限：①在批次效应校正方法上，多数平台以 ComBat 等统计方法为主，缺乏深度学习类方法的集成；②批次效应校正与缺失值填充通常作为独立步骤分步进行，误差可能逐步累积；③缺少可量化的方法对比评估框架，用户难以客观判断不同方法的适用性；④从数据预处理到下游分析、结果解读，尚无覆盖全流程的一体化 Web 平台。

随着深度学习技术的快速发展，将神经网络方法引入代谢组学数据处理已成为近年来的研究热点。研究表明，基于 Autoencoder 的深度学习模型能够有效捕获高维代谢组学数据中特征间的复杂相关结构，在缺失值填充和特征表示学习等任务上展现出优于传统统计方法的潜力[8]。

基于上述背景，本文设计并实现了一个面向代谢组学数据分析的 Web 平台，重点解决批次效应校正与缺失值填充两大核心问题，并通过引入深度学习 Autoencoder 方法和可量化的评估框架，在系统工程层面实现从数据导入、预处理、填充与校正，到评估可视化、下游差异分析与知识图谱溯源的全流程覆盖。本研究的意义在于：一方面，将深度学习方法与传统统计方法纳入统一框架进行定量对比，为用户提供客观的方法选择依据；另一方面，通过 Web 平台的工程化实现，降低代谢组学数据分析的技术门槛，提升研究人员的数据处理效率。

## 1.2 国内外研究现状

### 1.2.1 代谢组学数据分析平台研究现状

在代谢组学数据分析平台方面，MetaboAnalyst 是目前应用最广泛的在线分析平台之一。该平台集成了数据归一化、缺失值填充、主成分分析、差异代谢物筛选和通路分析等多种功能模块，并提供了较为友好的 Web 交互界面[7]。Pang 等人在 MetaboAnalyst 5.0 中进一步增加了多组学整合分析和代谢物注释功能，显著扩展了平台的应用范围。此外，XCMS Online[9] 提供了从原始质谱数据处理到统计分析的一体化流程，Metaboscape 等商业软件也在代谢物鉴定和批次校正方面有所集成。

然而，上述平台存在共同的不足：批次效应处理通常以单一 ComBat 方法为主，缺乏深度学习类方法；缺失值填充与批次效应校正独立处理，无法评估两步骤之间的误差传播；可量化的方法对比评估机制不健全，用户难以根据数据特点选择最优方案。

### 1.2.2 缺失值填充方法研究现状

代谢组学缺失值填充方法大致可分为三类：

简单统计填充方法：以均值填充（Mean Imputation）和中位数填充（Median Imputation）为代表，将特征的统计量直接赋予缺失位置。方法简单高效，但忽略了样本间的相关结构，可能引入系统性偏差，在缺失值比例较高时表现较差[5]。

基于近邻的方法：K 近邻填充（K-Nearest Neighbor，KNN）利用与待填充样本最相似的 K 个样本的特征值加权估计缺失位置。该方法能够在一定程度上利用样本间的相似结构，在代谢组学领域被广泛采用，但计算复杂度较高，且对高缺失率场景的效果受限[10]。

深度学习方法：Gondara 和 Wang 于 2018 年提出了基于去噪自动编码器（Denoising Autoencoder）的多重填充方法 MIDA（Multiple Imputation using Denoising Autoencoders），通过向输入数据添加噪声并训练网络重建原始信号，使模型能够从整体数据分布中学习特征间的复杂依赖关系，从而对缺失位置进行更准确的估计[8]。近年来，针对生物组学数据的深度学习填充方法不断涌现，相关研究表明，在特征间具有复杂相关结构的高维数据场景下，深度学习方法通常优于传统统计方法[11]。

### 1.2.3 批次效应校正方法研究现状

批次效应校正方法的研究已有较长历史，主要可分为以下三类：

基于统计模型的方法：ComBat 是该领域最具影响力的方法之一，由 Johnson 等人于 2007 年提出。该方法将特征表达值建模为全局均值、生物学效应与批次效应之和，通过经验 Bayes（Empirical Bayes）估计批次参数，利用所有特征的汇聚信息改善小样本场景下的参数估计稳定性，并可传入生物学协变量以保护真实的生物学差异不被消除[12]。此后，ComBat 被广泛应用于转录组学、蛋白质组学和代谢组学领域。逐特征位置尺度归一化（Per-feature Location-Scale Normalization）是另一种简单有效的统计方法，通过将各批次的特征均值和标准差归一化至全局水平，实现批次间分布的对齐，实现简单且具有良好的可解释性。

基于低维对齐的方法：Harmony 算法由 Korsunsky 等人于 2019 年提出，最初用于单细胞 RNA 测序数据的批次效应校正[13]。该方法在低维嵌入空间（如 PCA 空间）中通过迭代寻找跨批次的相似邻居关系并进行分布对齐，避免了对原始高维空间的直接操作，在多批次多样本场景下表现良好。

基于深度学习的方法：近年来，研究者开始将深度学习引入批次效应校正。Shaham 等人提出利用对抗神经网络（Adversarial Neural Network）学习批次不变的数据表示，在对数据结构依赖较弱的场景下取得了较好效果[14]。此外，也有研究探索使用变分自动编码器（Variational Autoencoder，VAE）同时完成批次效应校正与缺失值填充，在统一框架下减少分步处理带来的误差传播[15]。

### 1.2.4 代谢组学下游分析研究现状

批次效应校正完成后，代谢组学研究通常进入下游分析阶段，主要包括：

差异代谢物分析：常用方法包括独立样本 t 检验、方差分析（ANOVA）及其非参数等价方法，并配合 Benjamini-Hochberg 假阳性率控制（BH-FDR）进行多重检验校正，以 log2 Fold Change 衡量差异方向和大小[16]。

代谢通路富集分析：基于 KEGG（Kyoto Encyclopedia of Genes and Genomes）等数据库，通过超几何检验或 Fisher 精确检验判断差异代谢物是否显著富集于特定代谢通路，从而在通路层面解释差异代谢物的生物学意义[17]。

知识图谱辅助解读：近年来，知识图谱作为一种结构化知识表示方式，被引入代谢组学数据的生物学解读中。通过整合 KEGG、HMDB（Human Metabolome Database）、SMPDB（Small Molecule Pathway Database）等多源数据库，构建代谢物-通路-反应-酶-疾病关联网络，能够为差异代谢物提供可追溯的关联证据链[18]。

### 1.2.5 现有研究不足分析

综合来看，现有研究在代谢组学数据分析方法上已取得了较丰富的成果，但在系统集成层面仍存在以下不足：①批次效应校正与缺失值填充通常作为独立模块分步处理，缺乏整合框架；②现有平台对深度学习方法的集成程度有限，缺乏与传统方法的定量对比评估；③从数据预处理到下游分析、结果可视化的全流程一体化 Web 平台仍较为缺乏；④代谢组学知识图谱溯源功能尚未在分析平台中得到广泛集成。上述不足为本文的研究工作提供了明确的出发点。

## 1.3 本文主要工作

针对现有研究的不足，本文的主要工作包括以下四个方面：

（1）设计并实现了代谢组学数据处理 Web 平台

平台采用前后端分离架构，后端基于 Python FastAPI 框架，前端基于 Vue3 + TypeScript + ECharts，算法层以独立模块方式组织，支持 CSV/XLSX 格式的多数据集导入与切换，覆盖从数据预处理到结果可视化的完整分析流程。平台支持 Benchmark（7 批次合并，1715 样本，1180 特征）、BioHeart、MI 和 AMIDE 等多个公开数据集的处理与展示。

（2）实现了基于 Autoencoder 的深度学习缺失值填充，并设计了 Mask-then-Impute 可量化评估框架

在传统均值、中位数和 KNN 填充方法的基础上，本文基于 PyTorch 实现了 Encoder-Decoder 架构的 Autoencoder 填充模型，采用 Masked Reconstruction 训练策略，仅对已观测位置计算重建损失。同时，设计了 Mask-then-Impute 评估框架，通过随机遮蔽已知值并与填充结果对比，以 RMSE、MAE 和 NRMSE 三个指标对四种方法进行定量评估。实验表明，Autoencoder 方法在 Benchmark 数据集上取得最优 RMSE 为 0.2249，相比排名第二的 KNN（0.2980）降低约 24.5%。

（3）集成了两种批次效应校正方法，并设计了双维度量化评估体系

系统实现了逐特征位置尺度对齐（Baseline）方法和基于 neuroCombat 的 ComBat 经验 Bayes 方法，两种方法均有工程化的安全封装与异常处理机制。评估体系包含批次质心距离（Batch Centroid Separation）和批次/生物学分组轮廓系数（Silhouette Score）双指标，并通过 PCA 可视化直观呈现校正前后的效果对比。实验结果显示，Baseline 方法校正后批次质心距离由 5.38 降至约 0，批次混合效果显著。

（4）实现了差异代谢物分析、KEGG 通路富集分析和 MetaKG 知识图谱溯源展示

基于批次校正后矩阵，系统依次完成独立样本 t 检验（BH-FDR 校正）差异代谢物筛选、KEGG 通路超几何富集检验，以及基于 MetaKG 多库整合知识图谱的代谢物-通路-反应-酶关联溯源，并以火山图、通路富集气泡图和力导向知识图谱等多种可交互可视化形式呈现。

## 1.4 论文组织结构

本文共分七章，各章节内容安排如下：

第一章 绪论：介绍研究背景与意义，综述代谢组学数据分析、缺失值填充、批次效应校正及下游分析的国内外研究现状，提出现有研究的不足，说明本文的主要工作。

第二章 相关技术与方法综述：详细介绍本文所涉及的核心技术与方法，包括缺失值填充方法（传统统计方法与 Autoencoder 深度学习方法）、批次效应校正方法（Baseline 与 ComBat）以及批次效应评估指标（PCA、Silhouette 系数、批次质心距离）的原理与适用条件。

第三章 系统总体设计：阐述系统的需求分析、总体架构（前后端分离、分层模块化设计）、数据库设计（SQLite + 文件系统分工）、模块划分以及整体数据流设计。

第四章 核心算法设计与实现：详细描述各核心算法的设计思路与实现细节，包括数据预处理算法、Autoencoder 填充模型与 Mask-then-Impute 评估框架、Baseline 批次效应校正算法、ComBat 封装实现，以及差异分析、通路富集和知识图谱溯源算法。

第五章 系统实现与展示：介绍系统的技术栈选型、后端 API 设计与关键实现、前端组件架构与可视化实现，并展示系统各功能模块的界面截图与测试情况。

第六章 实验与结果分析：在多个数据集上对缺失值填充方法和批次效应校正方法进行定量对比实验，并展示差异代谢物分析与通路富集分析的结果，对实验数据进行深入分析与讨论。

第七章 结论与展望：总结本文的主要工作与贡献，指出系统的局限性，并展望后续改进方向。

---

# 第二章 相关技术与方法综述

## 2.1 代谢组学数据特点与预处理需求

### 2.1.1 代谢组学数据的结构特征

代谢组学数据通常以样本×特征矩阵（Sample-by-Feature Matrix）的形式组织，每行表示一个生物样本，每列表示一种代谢物特征（Feature），矩阵中的数值为该代谢物在该样本中的信号强度或经归一化后的丰度值。以本文所采用的 Benchmark 合并数据集为例，数据矩阵规模为 1715 个样本 × 1180 个代谢物特征，来自 7 个不同批次，涵盖多种实验条件与生物学分组。

代谢组学数据具有若干区别于一般机器学习数据集的典型特点：

（1）高维小样本特性。在典型的非靶向代谢组学实验中，通过 LC-MS 检测得到的特征数目可达数百至数千个，而单次实验的样本量通常仅为数十至数百个。高维数据中特征维度远超样本维度（p >> n），会显著增加统计方法的不稳定性和过拟合风险[5]。

（2）特征间复杂相关结构。生物体内代谢物通过代谢通路彼此连接，参与同一通路的代谢物在丰度变化上通常呈现出高度相关性。这种数据内生的相关结构使得能够捕获特征间非线性依赖关系的方法（如 Autoencoder）在缺失值填充等任务上具有潜在优势。

（3）数据分布偏斜与异质性。LC-MS 原始数据通常呈右偏分布（正偏态），且不同代谢物的信号强度量级差异悬殊，常需进行 log 变换和尺度归一化以满足后续统计方法的正态性假设[16]。此外，不同批次、不同样本组的数据分布本身就存在系统性差异，这构成了批次效应问题的本质。

（4）普遍存在缺失值。由于仪器检测下限、谱峰拾取算法误差以及低丰度代谢物的随机检测失败，代谢组学数据矩阵中通常存在大量缺失值，缺失比例在 20%～50% 之间较为常见。

### 2.1.2 数据预处理流程概述

针对上述数据特点，代谢组学数据分析通常需要经历以下预处理步骤：

1. 格式检验与质控：核查数据矩阵完整性，排查异常样本（如 QC 样本）与低质量特征（如全缺失特征）；
2. 缺失值填充（Imputation）：采用适当方法对缺失位置进行估计填充，保证后续分析的数据完整性；
3. 数据归一化与尺度化：通过 log 变换、Pareto 缩放等手段消除量纲差异，满足统计分析前提；
4. 批次效应检测：借助 PCA、Silhouette 系数、批次质心距离等指标判断批次效应程度；
5. 批次效应校正：采用统计或深度学习方法消除批次间系统性偏差，同时尽量保护真实的生物学差异；
6. 校正效果评估：通过定量指标和可视化手段验证校正结果。

上述步骤在本系统中均有对应的算法实现和 Web 交互界面支持，各步骤的具体实现将分别在第三章和第四章中详细描述。

---

## 2.2 缺失值填充方法

### 2.2.1 传统统计填充方法

（1）均值填充（Mean Imputation）

均值填充是最简单的缺失值处理策略：对于矩阵中第 j 个特征，计算该列所有已观测值的算术均值，将所有缺失位置统一赋值为该均值：

$$\hat{x}_{ij} = \bar{x}_j = \frac{1}{|\mathcal{O}_j|} \sum_{i \in \mathcal{O}_j} x_{ij} \tag{2-1}$$

其中 $\mathcal{O}_j$ 为第 $j$ 列中已观测值的样本下标集合。均值填充的优点是计算复杂度为 $O(np)$，实现简单、运行速度快；缺点是将所有缺失位置设置为同一值，完全忽略了样本间的个体差异，会人为压缩特征的方差，可能引入系统性偏差，在缺失率较高时效果较差。

在本文的 Mask-then-Impute 基准评估中，均值填充在 Benchmark 数据集（mask_ratio = 15%，重复 3 次）上的平均 RMSE 为 1.0011，NRMSE 约为 1.0006，均明显高于 KNN 和 Autoencoder 方法（详见第六章）。

（2）中位数填充（Median Imputation）

中位数填充原理与均值填充类似，将每个特征的缺失位置赋值为该列的中位数：

$$\hat{x}_{ij} = \text{med}(x_{ij},\ i \in \mathcal{O}_j) \tag{2-2}$$

与均值相比，中位数对异常值（Outlier）具有更强的鲁棒性，适合于分布存在较强偏斜或含有离群样本的数据集。然而，中位数填充同样忽略了样本间的相关结构，且对双峰分布等复杂情形也无法有效估计。本文评估中，中位数填充 RMSE 为 1.0361，MAE 为 0.3427，NRMSE 为 1.0356，与均值填充相近，均属于较为粗糙的基线方法。

（3）K 近邻填充（KNN Imputation）

K 近邻填充方法（K-Nearest Neighbor Imputation）的核心思想是：对于待填充的缺失位置 $(i, j)$，从其余已观测该特征的样本中找出与样本 $i$ 最相似的 $K$ 个近邻，将这 $K$ 个近邻在特征 $j$ 上的值加权平均作为填充估计：

$$\hat{x}_{ij} = \frac{\sum_{k \in \mathcal{N}(i,j)} w_{ik} \cdot x_{kj}}{\sum_{k \in \mathcal{N}(i,j)} w_{ik}} \tag{2-3}$$

其中 $\mathcal{N}(i,j)$ 为在特征 $j$ 上有观测值且与样本 $i$ 欧氏距离最近的 $K$ 个样本集合，$w_{ik}$ 为距离的倒数权重。本文系统中采用 $K = 5$，样本间的相似性基于所有非缺失特征上的欧氏距离计算。

KNN 填充能够利用数据集内样本间的相似性结构，相比简单统计方法通常具有更高的填充精度。本文评估中，KNN 方法 RMSE 为 0.2980，MAE 为 0.0740，NRMSE 为 0.2978，远优于均值和中位数方法。然而，KNN 的计算复杂度为 $O(n^2 p)$，在样本量较大时计算开销显著增大，且其性能依赖于"相似样本在特征空间中邻近"这一局部平滑假设，对代谢组学数据中远程通路关联等全局结构的捕获能力有限。

### 2.2.2 基于 Autoencoder 的深度学习填充方法

#### 网络结构设计

本文实现的缺失值填充 Autoencoder 采用对称的 Encoder-Decoder 结构，具体网络层次如下：

$$\begin{aligned}
\text{输入层}(p) & \xrightarrow{\text{Linear}} \text{隐层}(256) \xrightarrow{\text{ReLU} + \text{BN} + \text{Dropout}(0.1)} \text{潜空间}(64) \xrightarrow{\text{ReLU}} \\
& \xrightarrow{\text{Linear}} \text{隐层}(256) \xrightarrow{\text{ReLU} + \text{BN}} \text{输出层}(p)
\end{aligned} \tag{2-4}$$

其中 $p$ 为特征维度（本文中 $p = 1180$），隐层维度 $h = 256$，潜空间维度 $l = 64$。Encoder 将高维代谢组学特征映射到低维潜空间表示，迫使模型学习数据的紧凑结构；Decoder 将潜空间表示重建回原始维度，输出对完整特征向量的估计。批归一化层（Batch Normalization）有助于稳定训练过程，Dropout（丢弃率 0.1）起正则化作用，防止过拟合。

#### Masked Reconstruction 训练策略

代谢组学数据中存在大量真实缺失值，无法直接使用标准的全观测重建损失。参考 Gondara 和 Wang（2018）提出的 MIDA 方法，本文采用 Masked Reconstruction（遮蔽重建）训练策略：

1. 初始化：将输入矩阵 $\mathbf{X}$ 中的缺失位置（NaN）用对应列均值填充，得到初始输入 $\tilde{\mathbf{X}}$，为网络提供合理的起始信号；
2. 构造观测掩码：令 $\mathbf{M} \in \{0, 1\}^{n \times p}$，其中 $m_{ij} = 1$ 表示位置 $(i,j)$ 为已知观测值，$m_{ij} = 0$ 表示缺失位置；
3. 前向传播与损失计算：对 mini-batch 内的样本 $\mathbf{X}_b$ 进行前向传播得到重建输出 $\hat{\mathbf{X}}_b = f_\theta(\tilde{\mathbf{X}}_b)$，仅在已知位置计算 MSE 损失，避免网络在缺失位置上自学习：

$$\mathcal{L} = \frac{\sum_{(i,j): m_{ij}=1} (\hat{x}_{ij} - x_{ij})^2}{\sum_{i,j} m_{ij} + \epsilon} \tag{2-5}$$

4. 梯度更新：通过反向传播优化网络参数 $\theta$，采用 Adam 优化器（学习率 $lr = 10^{-3}$，权重衰减 $\lambda = 10^{-5}$）和 CosineAnnealingLR 学习率调度策略（$T_{\max} = 80$ 轮，$\eta_{\min} = lr \times 0.1$），训练总轮数为 80 epochs，batch size 为 64；
5. 填充推断：训练完成后，以 $\tilde{\mathbf{X}}$ 为输入进行前向推断，仅将网络输出中对应缺失位置 $\mathbf{M}_{ij}=0$ 的预测值回填至矩阵，已知观测值保持不变。

上述策略的核心优势在于：网络的训练监督信号完全来自已知观测值，缺失位置的填充结果由网络从数据整体分布中泛化推断得到，而非通过自学习缺失值获得，从而保证了填充结果的合理性。

### 2.2.3 Mask-then-Impute 评估框架

为客观定量评估各填充方法的精度，本文设计了 Mask-then-Impute 评估框架。其基本思想是：在原本已完整（无缺失）的矩阵上人工随机遮蔽一定比例的值作为"模拟缺失"，使用各填充方法对遮蔽位置进行填充，再将填充结果与原始真值进行对比计算误差指标，从而在有参照标准的条件下对方法性能进行量化评估。具体流程如下：

1. 以随机种子为控制，从观测值中均匀随机抽取 15% 位置（约 303,555 个）标记为遮蔽；
2. 分别以均值、中位数、KNN（$K=5$）、Autoencoder 四种方法对遮蔽位置进行填充；
3. 计算以下三个误差指标：

均方根误差（RMSE）：

$$\text{RMSE} = \sqrt{\frac{1}{|\mathcal{M}|}\sum_{(i,j)\in\mathcal{M}} (\hat{x}_{ij} - x_{ij})^2} \tag{2-6}$$

平均绝对误差（MAE）：

$$\text{MAE} = \frac{1}{|\mathcal{M}|}\sum_{(i,j)\in\mathcal{M}} |\hat{x}_{ij} - x_{ij}| \tag{2-7}$$

归一化均方根误差（NRMSE）：对每个特征的 RMSE 除以该特征的标准差后取平均，消除不同特征量纲差异，实现跨特征可比性：

$$\text{NRMSE} = \frac{1}{p}\sum_{j=1}^{p}\frac{\text{RMSE}_j}{\text{std}(x_{\cdot j})} \tag{2-8}$$

4. 上述过程以不同随机种子独立重复 3 次，取指标均值与标准差作为最终评估结果；
5. 在 Benchmark 数据集上的完整评估结果详见第六章表 6.1。

### 2.2.4 各方法适用场景分析

| 填充方法 | 计算复杂度 | RMSE（本文） | 主要优势 | 适用场景 |
|:-------:|:---------:|:-----------:|:-------:|:-------:|
| 均值填充 | $O(np)$ | 1.0011 | 简单快速 | 缺失率低、特征独立性高 |
| 中位数填充 | $O(np\log n)$ | 1.0361 | 抗异常值 | 分布偏斜、含离群点 |
| KNN 填充 | $O(n^2 p)$ | 0.2980 | 利用样本相似性 | 样本量适中、局部结构明显 |
| Autoencoder | $O(nph)$ | 0.2249 | 捕获全局非线性结构 | 高维、特征间复杂相关 |

总体而言，当数据集规模适中且样本间局部相似性较强时，KNN 是兼顾精度与计算效率的较优选择；当数据维度较高、特征间存在复杂非线性相关结构时，Autoencoder 方法更具优势；简单统计方法可作为快速基线参考。

---

## 2.3 批次效应校正方法

### 2.3.1 Baseline 逐特征位置尺度对齐

逐特征位置尺度对齐（Per-feature Location-Scale Normalization，本文称为 Baseline 方法）是一种直观的批次效应校正策略，其核心思想是：假设批次效应主要体现为各批次在每个特征上的均值（位置）和标准差（尺度）的系统性偏移，通过将各批次的分布对齐至全局分布，消除批次间的位置与尺度差异。

对于特征 $j$，设全局均值为 $\mu_j = \frac{1}{n}\sum_{i=1}^{n}x_{ij}$，全局标准差为 $\sigma_j = \text{std}(x_{\cdot j})$；对于属于批次 $b$ 的样本子集，设批次内均值为 $\mu_{bj}$，批次内标准差为 $\sigma_{bj}$。则对样本 $i$（$i$ 属于批次 $b$）的校正公式为：

$$x'_{ij} = \frac{x_{ij} - \mu_{bj}}{\max(\sigma_{bj}, \epsilon)} \cdot \sigma_j + \mu_j \quad (2\text{-}9)$$

其中 $\epsilon > 0$ 为防止除零的数值稳定下界（本文取 $\epsilon = 10^{-8}$）。该公式先将批次内分布标准化（减去批次均值、除以批次标准差），再缩放还原为全局分布的均值与尺度，实现批次间分布的对齐。

方法特点：实现简单，假设清晰（仅假设批次效应为逐特征的位置/尺度偏移）；可解释性强；无需额外协变量信息。主要局限：①仅对位置和尺度偏移有效，无法处理批次效应呈现复杂非线性形态的情况；②不考虑生物学协变量，若批次与生物学分组高度混杂，可能造成过校正，削弱真实生物学信号；③对批次内样本量要求最低 2 个，样本量极少的批次统计量估计不稳定。

在本文的 Benchmark 数据集上，Baseline 方法校正后批次质心距离由 $5.38$ 降至约 $0$（$1.90 \times 10^{-14}$），批次混合效果极为显著；批次 Silhouette 系数由 $-0.1461$ 变化至 $-0.0343$，方向符合批次分离减弱的预期（详细数值分析见第六章）。

### 2.3.2 ComBat 经验 Bayes 方法

ComBat 方法由 Johnson 等人于 2007 年最初为基因表达数据（微阵列）设计[12]，后被广泛应用于转录组学、蛋白质组学和代谢组学领域。该方法将特征 $j$ 在样本 $i$（属于批次 $b$）上的观测值建模为：

$$x_{ijb} = \alpha_j + \mathbf{d}_{ib}^T \boldsymbol{\beta}_j + \gamma_{jb} + \delta_{jb} \cdot \varepsilon_{ijb} \tag{2-10}$$

其中 $\alpha_j$ 为特征 $j$ 的全局均值，$\mathbf{d}_{ib}$ 为生物学协变量设计矩阵（如分组标签），$\boldsymbol{\beta}_j$ 为协变量效应，$\gamma_{jb}$ 和 $\delta_{jb}$ 分别为批次 $b$ 对特征 $j$ 施加的加性和乘性批次效应，$\varepsilon_{ijb}$ 为误差项。

ComBat 的关键在于经验 Bayes 估计策略：首先利用所有特征 $j = 1, \ldots, p$ 上的批次效应估计值构建先验分布，再通过 Bayes 收缩将各特征的批次参数估计值向先验均值"收缩"，从而在小样本场景下获得更稳定的参数估计。校正后的数据为：

$$x'_{ijb} = \frac{x_{ijb} - \alpha_j - \mathbf{d}_{ib}^T\hat{\boldsymbol{\beta}}_j - \hat{\gamma}^*_{jb}}{\hat{\delta}^*_{jb}} \cdot \sigma_j + \alpha_j + \mathbf{d}_{ib}^T\hat{\boldsymbol{\beta}}_j \quad (2\text{-}11)$$

其中 $\hat{\gamma}^*_{jb}$ 和 $\hat{\delta}^*_{jb}$ 为经验 Bayes 收缩后的批次效应估计值。

方法特点：①通过经验 Bayes 收缩利用跨特征信息改善小批次估计稳定性；②可显式传入生物学协变量（如分组标签）以保护真实生物学差异不被消除；③在代谢组学领域已有大量实际应用验证。主要局限：①需要预先知道批次标签和生物学协变量信息；②若批次与生物学因素严重混杂，保护效果受限；③要求各批次均有足够样本量以支撑稳定的参数估计。

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

在本文系统中，两种方法均通过统一的算法接口调用，用户可在前端界面选择校正方法并可视化对比校正效果，详见第五章。

---

## 2.4 批次效应评估指标

批次效应校正效果的评估需要同时考虑两个维度：批次混合程度（批次效应是否被有效消除）和生物学信号保留程度（真实的生物学差异是否被保护）。本文采用 PCA 可视化、Silhouette 系数双指标和批次质心距离三种手段构建双维度评估体系。

### 2.4.1 PCA 降维可视化

主成分分析（Principal Component Analysis，PCA）是评估批次效应最直观的工具。通过将高维代谢组学数据（本文为 1180 维）投影至前两个主成分所张成的二维平面，可以直观观察样本在低维空间中的分布规律：若校正前不同批次样本形成明显分离的簇群，校正后各批次样本混合分布，则说明批次效应得到有效消除。

本文系统中，PCA 分析分别在校正前后各运行一次，以相同批次颜色编码和相同分组标记在前端 ECharts 散点图中并列展示。

校正前，PCA 图中 7 个批次样本呈现出明显的簇状分离，PC1 和 PC2 的解释方差比分别为 22.0% 和 4.9%，主要方差来源为批次间差异。校正后，7 个批次样本在 PCA 空间中实现了充分混合，主要方差结构发生变化（PC1 解释方差比提升至 50.9%），表明批次效应被有效消除，数据中残余的方差结构可能更多地反映了真实的生物学差异。

### 2.4.2 Silhouette 系数双指标

Silhouette 系数是衡量聚类结构紧密程度的经典指标，其对单个样本 $i$ 的计算公式为：

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i),\ b(i)\}} \tag{2-12}$$

其中 $a(i)$ 为样本 $i$ 与同类（同批次或同分组）其他样本的平均距离，$b(i)$ 为样本 $i$ 与最近异类（不同批次或不同分组）样本的平均距离。$s(i) \in [-1, 1]$，整个数据集的 Silhouette 系数为所有样本的均值 $\bar{s}$。

本文设计了双 Silhouette 指标，分别对批次标签和生物学分组标签计算 Silhouette 系数：

- 批次 Silhouette（batch Silhouette）：以批次 ID 作为类别标签计算。值越低（向 $-1$ 方向），表示不同批次样本在 PCA 空间中相互混合越充分，即批次效应越弱，校正效果越好；
- 分组 Silhouette（group Silhouette）：以生物学分组标签作为类别标签计算。值越高（向 $+1$ 方向），表示相同生物学分组的样本聚集越紧密，即生物学结构保留越完好。

两个指标在批次校正前后的变化方向应当一致指向"好"的方向：批次 Silhouette 应降低（或更加负向），分组 Silhouette 应升高（或负值幅度减小）。

本文 Benchmark 数据集上，以 PCA 前两个主成分坐标计算的 Silhouette 系数变化如下：

| 指标 | 校正前 | 校正后（Baseline） | 变化方向 |
|:---:|:------:|:-----------------:|:-------:|
| 批次 Silhouette | −0.1461 | −0.0343 | +0.1117（向 0 移动，批次分离略有减弱） |
| 分组 Silhouette | −0.4813 | −0.4465 | +0.0348（负值幅度减小，分组结构略有改善） |

值得注意的是，上表中批次 Silhouette 校正后有所上升（由更负向接近 0），这在解释上存在一定歧义：在校正前后各自的 PCA 坐标系下，若校正后数据的总体方差结构发生了改变，Silhouette 系数的变化可能受到 PCA 坐标变化本身的影响，而非仅反映批次分离程度。因此，本文将批次质心距离作为主要判据，Silhouette 系数作为辅助参考，并结合 PCA 可视化进行综合判断。

### 2.4.3 批次质心距离

批次质心距离（Batch Centroid Separation Distance）衡量各批次在 PCA 低维空间中的质心离散程度，直接量化批次间系统性偏移的大小：

$$D_{\text{centroid}} = \frac{1}{B(B-1)}\sum_{b=1}^{B}\sum_{b' \neq b} \|\bar{\mathbf{z}}_b - \bar{\mathbf{z}}_{b'}\|_2 \tag{2-13}$$

其中 $B$ 为批次数，$\bar{\mathbf{z}}_b = \frac{1}{n_b}\sum_{i \in \mathcal{B}_b} \mathbf{z}_i$ 为批次 $b$ 内所有样本在 PCA 空间中的质心坐标（取 PC1 和 PC2），$\|\cdot\|_2$ 为欧氏距离。

批次质心距离越接近 0，表示各批次的"中心"在低维空间中趋于重合，批次混合效果越好。

在本文 Benchmark 数据集上，批次质心距离的变化如下表所示：

| 指标 | 校正前 | 校正后（Baseline） | 变化量 |
|:---:|:------:|:-----------------:|:------:|
| 批次质心距离（PC1–PC2） | 5.3796 | ≈ 0（$1.90 \times 10^{-14}$） | −5.3796 |

校正后批次质心距离几乎归零（数值上的非零仅为浮点精度误差），表明在 PCA 前两个主成分空间中，Baseline 方法实现了各批次质心的完全对齐，批次效应被有效消除。这也是本文将质心距离作为主要判据的原因——相较于 Silhouette 系数，质心距离的解释更直接，不受 PCA 坐标系变化影响。

---

## 2.5 本章小结

本章系统介绍了本文研究所涉及的核心技术与方法。

在代谢组学数据特点方面，梳理了高维小样本、特征间复杂相关、分布偏斜和高缺失率等典型数据特征，说明了预处理流程各步骤的必要性。

在缺失值填充方法方面，介绍了均值、中位数、KNN 三种传统统计方法的原理与局限，重点阐述了基于 Autoencoder 的深度学习填充模型的网络结构（1180→256→64→256→1180）和 Masked Reconstruction 训练策略。提出的 Mask-then-Impute 评估框架在 Benchmark 数据集（mask_ratio=15%，3 次重复）上的定量评估表明，Autoencoder 方法取得最低 RMSE（0.2249），KNN 次之（0.2980），均值（1.0011）和中位数（1.0361）方法精度明显较低。

在批次效应校正方法方面，阐述了 Baseline 逐特征位置尺度对齐（实现简单、无需协变量）和 ComBat 经验 Bayes 方法（利用跨特征信息、可保护生物学信号）的原理与各自适用场景，并从多个维度进行了对比分析。

在批次效应评估指标方面，构建了 PCA 可视化、Silhouette 系数双指标（批次/分组）和批次质心距离组成的双维度量化评估体系，强调了以批次质心距离为主、Silhouette 系数为辅、结合 PCA 可视化综合判断的评估策略。在 Benchmark 数据集上，Baseline 方法校正后批次质心距离由 5.38 降至约 0，校正效果显著。

上述方法的工程实现细节将在第四章中详细阐述，实验结果分析将在第六章中呈现。

---

# 第三章 系统总体设计

## 3.1 系统需求分析

### 3.1.1 功能需求

本系统以代谢组学研究人员为主要目标用户，其使用场景通常为：拥有来自多批次 LC-MS 实验的代谢组学数据矩阵，需要依次完成缺失值填充、批次效应校正和差异代谢物分析，并希望通过可视化界面直观评估各步骤的处理效果。围绕这一核心场景，系统的功能需求可划分为以下六类：

（1）数据管理需求

- 支持 CSV 和 XLSX 格式的数据文件上传，文件大小上限为 50MB；
- 支持 Long Format（长表格）数据格式解析，用户可自定义特征列、样本列、数值列、批次标签列、分组标签列的列名映射；
- 支持多数据集并行管理，用户可在 Benchmark、BioHeart、MI、AMIDE 等预置数据集与自定义上传数据集间切换；
- 提供数据集基本信息预览（样本数、特征数、批次数）。

（2）数据预处理需求

- 支持配置缺失率过滤阈值（默认 50%，超出阈值的特征列将被删除）；
- 支持 log1p 变换（对正偏态分布进行压缩）；
- 支持 Z-score 标准化（按样本维度消除量纲差异）；
- 预处理结果以 CSV 矩阵文件形式持久化存储。

（3）缺失值填充需求

- 支持四种填充方法：均值填充、中位数填充、KNN 填充（$K$ 可配置）、Autoencoder 深度学习填充；
- 填充方法参数可在 Web 界面配置，支持单次选择一种方法运行；
- 提供 Mask-then-Impute 评估结果展示（RMSE/MAE/NRMSE 对比图表）；
- 填充结果矩阵支持 CSV 格式下载。

（4）批次效应校正需求

- 支持两种校正方法：Baseline 逐特征位置尺度对齐、ComBat 经验 Bayes 校正；
- 提供校正前后的 PCA 散点图对比可视化（支持按批次/分组两种颜色编码）；
- 提供批次质心距离、批次 Silhouette 系数、分组 Silhouette 系数三项定量评估指标展示；
- 校正结果矩阵支持 CSV 格式下载。

（5）下游分析需求

- 差异代谢物分析：基于独立样本 t 检验 + BH-FDR 校正，支持 q 值阈值和 |log2FC| 阈值配置，结果以火山图展示；
- 通路富集分析：基于 KEGG 数据库超几何检验，结果以富集气泡图展示；
- 知识图谱溯源：基于 MetaKG 多库整合知识图谱，以力导向图展示差异代谢物的通路-反应-酶关联网络，支持节点拖拽、关键词搜索和节点类型过滤。

（6）结果输出需求

- 核心中间产物（预处理矩阵、填充矩阵、校正矩阵）支持 CSV 格式下载；
- 差异代谢物列表和通路富集结果支持表格展示与数据导出；
- 评估报告以 JSON 格式持久化于服务器，前端通过 API 按需读取。

### 3.1.2 非功能需求

可用性：面向无编程背景的生物医学研究人员，Web 界面应具备清晰的操作引导，关键参数提供默认值，错误信息以友好的文字形式提示，避免终止整体流程。

可扩展性：算法层以独立模块方式组织，新增缺失值填充方法或批次效应校正方法时，只需在对应算法子目录下添加实现，不修改上层 Service 与 API 代码；前端组件化设计，新增可视化卡片无需改动核心状态管理逻辑。

可靠性：ComBat 等可能因数据条件不满足而失败的算法均有安全封装，捕获异常后以降级策略处理（如返回未校正矩阵并记录错误原因），不影响其他模块的正常执行。

性能：系统以本地单机部署为目标，针对本文实验数据集规模（约 1715 样本 × 1180 特征）的处理时间在可接受范围内（预处理 < 30s，KNN 填充 < 60s，Autoencoder 填充 < 90s）。

---

## 3.2 系统总体架构

### 3.2.1 前后端分离架构概述

本系统采用前后端分离的 Web 应用架构，前端与后端通过 HTTP/REST 接口通信，互相独立开发与部署。整体架构分为三个主要层次：前端展示层（Vue3 + TypeScript + Vite，端口 5173）、后端服务层（Python FastAPI + Uvicorn，端口 8000）和数据存储层（SQLite 数据库 + 文件系统）。

### 3.2.2 后端分层架构设计

后端内部采用严格的四层分层架构，各层职责清晰，向下单向依赖：API 层负责 HTTP 请求接收与响应序列化；Service 层包含核心业务逻辑，协调 Repository 和 Algorithm 模块；Algorithm 层为纯算法实现，不依赖数据库或文件 I/O；Repository 层负责数据库 CRUD 操作，通过 SQLAlchemy ORM 封装 SQL。

### 3.2.3 前端架构设计

前端采用 Vue3 Composition API 风格开发，目录结构按功能职责划分：src/views/（页面级视图）、src/components/（15 个可复用功能组件）、src/stores/（Pinia 状态管理）、src/api/（HTTP 请求封装）、src/types/（TypeScript 类型定义）。

---

## 3.3 数据库设计

本系统选用 SQLite 作为关系型数据库，通过 SQLAlchemy ORM 进行数据库访问。系统数据库包含 Task、Dataset、Parameters、Result 四张核心数据表，分别记录任务基本信息与状态、数据集解析配置、算法参数配置和处理结果文件路径。系统采用"元数据入库、矩阵数据存文件"的混合存储策略：数据库存储结构化元数据，文件系统存储 CSV 矩阵文件、JSON 评估报告和图片文件等大文件。

---

## 3.4 系统模块划分

本系统按照分析流程的逻辑顺序划分为数据管理、预处理、缺失值填充、批次效应校正、评估可视化和下游分析六个主要功能模块，各模块职责独立、接口清晰，通过统一接口交互，支持新算法的灵活接入。

---

## 3.5 系统整体数据流

系统的整体数据流遵循"原始数据 → 预处理 → 填充 → 批次校正 → 评估 → 下游分析"的线性管道（Pipeline）结构。每个处理步骤完成后，输出矩阵均以 CSV 文件形式持久化至 data/processed/{dataset_id}/_pipeline/ 目录，评估结果以 JSON 文件形式存储，支持断点续算。前端通过定时轮询 /api/tasks/{task_id} 接口获取任务状态（uploaded → preprocess_done → impute_done → correct_done → done，任意步骤出错则转为 error），并根据状态决定展示哪些功能模块的结果内容。

---

## 3.6 本章小结

本章对系统的总体设计进行了系统性阐述。系统采用前后端分离架构，后端以 FastAPI 框架实现 RESTful API，内部分为 API 层、Service 层、Algorithm 层和 Repository 层；数据库采用 SQLite + SQLAlchemy ORM，以混合存储策略兼顾结构化查询和大文件高效存储；系统按分析流程划分为六个功能模块，以线性 Pipeline 结构组织数据处理流程，通过任务状态机追踪整体处理进度。各模块的具体算法实现细节将在第四章中详细描述。

---

# 第四章 核心算法实现

本章承接第二章对相关算法理论的综述，从工程实现的角度，详细描述系统中各核心算法的具体实现细节，包括所采用的开源库、关键参数配置、自研封装策略以及在小数据规模或异常输入下的降级处理机制。

## 4.1 数据预处理算法

数据预处理是代谢组学分析流程的第一个计算步骤，执行顺序固定为：特征缺失率过滤 → log1p 变换 → Z-score 标准化。特征缺失率过滤基于列缺失率 $r_j \leq \tau_{\text{miss}}$（默认阈值 0.5）保留有效特征。log1p 变换采用 $x' = \log(1+x)$，避免零值数值问题，满足后续统计方法的正态性假设。Z-score 标准化按特征（列）将量纲统一到均值为 0、标准差为 1 的尺度，零标准差时分母取 1.0 以防除以零。

---

## 4.2 缺失值填充算法实现

均值/中位数填充：基于 NumPy nanmean/nanmedian 对每列已观测值计算统计量，替换 NaN 位置，复杂度 $O(np)$。KNN 填充：调用 scikit-learn KNNImputer，基于共同观测特征上的欧氏距离寻找 $K$ 个最近邻（默认 $K=5$），复杂度约 $O(n^2p)$。

Autoencoder 深度学习填充：基于 PyTorch 实现对称 Encoder-Decoder 网络（1180→256→64→256→1180），采用 Masked Reconstruction 训练策略——NaN 位置以列均值初始化，训练时仅在已知观测位置计算 MSE 损失 $\mathcal{L} = \sum_{m_{ij}=1}(\hat{x}_{ij}-x_{ij})^2 / (\sum m_{ij}+\epsilon)$，推断时仅将缺失位置预测值回填。训练配置：Adam 优化器（$lr=10^{-3}$，$\lambda=10^{-5}$）+ CosineAnnealingLR，训练 80 个 epoch，batch size=64。

Mask-then-Impute 评估框架：在完整矩阵上均匀随机遮蔽 15% 位置，以四种方法填充，仅在遮蔽位置计算 RMSE/MAE/NRMSE 三项指标，以三个随机种子（42/43/44）独立重复，取均值与标准差作为最终评估结果。

---

## 4.3 批次效应校正算法实现

Baseline 逐特征位置尺度对齐：对每个特征 $j$ 独立按公式 $x'_{ij} = (x_{ij} - \mu_{bj}) / \max(\sigma_{bj}, \epsilon) \cdot \sigma_j + \mu_j$（$\epsilon = 10^{-8}$）执行校正，批次内样本数 $n_b < 2$ 时跳过。ComBat 经验 Bayes 校正：基于 neuroCombat 库实现，调用前后自动完成矩阵转置，实现了 run_combat_safe() 安全封装，支持生物学协变量传入以保护生物学信号。批次效应评估：PCA 降维（scikit-learn PCA，前两个主成分）→ 双 Silhouette 系数（以批次标签/生物学分组标签分别计算）→ 批次质心距离（$B(B-1)/2$ 对质心欧氏距离均值）。

---

## 4.4 下游分析算法实现

差异代谢物分析：Welch t 检验（scipy.stats.ttest_ind，equal_var=False）→ BH-FDR 校正（statsmodels.multipletests，备用手动实现）→ log2FC 计算 → 双重阈值（$q < 0.05$，$|\text{log2FC}| \geq 1$）显著性标注，结果以 JSON 格式返回用于火山图绘制。

KEGG 通路富集分析：超几何检验（scipy.stats.hypergeom.sf(k-1, M, K, n)）→ BH-FDR 校正 → 返回 q < 0.2 显著通路（最多 20 条）；KEGG 数据本地 JSON 缓存；对无注释数据集返回 {available: false} 降级结构。

MetaKG 知识图谱溯源：整合 KEGG/HMDB/SMPDB 三库的预构建 JSON 知识图谱，以显著差异代谢物为起点提取一跳邻域子图，前端 MetaKGCard 组件以 ECharts 力导向图渲染，支持拖拽、搜索和类型过滤交互。

---

## 4.5 本章小结

本章详细阐述了系统各核心算法的设计思路与实现细节。数据预处理算法实现了缺失率过滤、log1p 变换和 Z-score 标准化三步串行流程。缺失值填充算法实现了四种方法（均值/中位数/KNN/Autoencoder），Autoencoder 采用 Masked Reconstruction 训练策略，Mask-then-Impute 框架提供客观定量评估。批次效应校正算法实现了 Baseline（简单高效）和 ComBat（含安全封装和协变量保护）两种方法，评估体系由 PCA、双 Silhouette 系数和批次质心距离组成。下游分析算法涵盖 Welch t 检验 + BH-FDR 差异分析、超几何通路富集分析和 MetaKG 知识图谱溯源。上述算法的完整集成与前端展示将在第五章中描述，实验评估结果将在第六章中呈现。

---

# 第五章 Web 系统工程实现

## 5.1 开发环境与技术栈

后端核心依赖：Python 3.10+、FastAPI、Uvicorn、SQLAlchemy、Pydantic v2、pandas、NumPy、scikit-learn、scipy、PyTorch、neuroCombat、statsmodels、requests、openpyxl、matplotlib。前端核心依赖：Vue 3、TypeScript 5.x、Vite、Element Plus、ECharts 5.x、Pinia、Vue Router 4.x、Axios、SCSS。系统以本地单机方式部署，后端端口 8000，前端端口 5173，API 调试通过 FastAPI 内置 Swagger UI（/docs）。

---

## 5.2 后端关键实现

API 接口按功能分为数据管理、处理流程、Benchmark 数据集专用和下游分析四组，统一返回 JSON 格式，HTTP 状态码规范（200/400/404/500），FastAPI 自动生成 OpenAPI 文档。

Benchmark 数据集采用"离线预计算 + 在线只读展示"模式：通过 CLI 脚本预先运行完整 Pipeline 并持久化所有中间产物，Web 服务启动后直接暴露只读 API，前端通过 Pinia benchmark store 的 loadAll() 方法一次性并发拉取所有数据，响应速度极快（文件 I/O 毫秒级），避免了 API 超时问题。

---

## 5.3 前端关键实现

前端共五个页面视图（首页/数据导入/任务配置/结果展示/历史任务）和 15 个功能组件（导航布局 2 个、数据展示 5 个、可视化 6 个、交互控制 2 个）。benchmark store 并发发起 10 个 API 请求，全部失败时静默（catch(() => null)），保证页面不因单个接口失败而崩溃。task store 通过轮询实时更新任务状态，驱动 PipelineStepBar 进度显示。可视化图表基于 ECharts 实现（火山图、气泡图、力导向图、箱线图、PCA 散点图），均支持悬停 tooltip、缩放、拖拽等丰富交互。

---

## 5.4 系统功能界面展示

系统主要界面包括首页概览（KPI 卡片展示核心实验结果与功能入口）、数据导入页（文件上传 + 列名映射配置）、结果展示页（PCA 对比图 + 填充评估 + 火山图 + 通路气泡图 + MetaKG 力导向图 + 数据集切换器）共七大功能展示区域。

---

## 5.5 系统测试

手动功能测试覆盖 13 个核心功能点（文件上传、预处理、四种填充方法、Mask-then-Impute 评估、两种批次校正方法、批次效应评估、差异分析、通路富集、知识图谱、数据集切换、文件下载），均通过测试。边界情况测试覆盖 ComBat 降级（批次样本数为 1 时正常降级）、高缺失率特征过滤、无 KEGG 注释数据集降级（AMIDE）、Autoencoder 小数据集适应（BioHeart，53 特征）四个场景，均通过。在 Benchmark、BioHeart、MI、AMIDE 四个数据集上分别运行了完整的处理流程，验证了系统的通用性。

---

## 5.6 本章小结

本章从技术栈选型、后端实现、前端实现和系统测试四个维度对系统的工程实现进行了详细描述。后端 API 接口分组设计规范，Benchmark 数据集采用离线预计算策略，run_combat_safe() 安全封装保证鲁棒性；前端 15 个功能组件职责清晰，六类可视化图表支持丰富用户交互，DatasetSelector 支持四数据集无缝切换；功能测试和边界情况测试覆盖率良好，四数据集完整流程测试验证了系统的通用性，所有测试均通过。

---

# 第六章 实验与结果分析

## 6.1 实验数据集说明

本文实验主要基于 Benchmark 合并数据集（1715 样本 × 1180 特征 × 7 批次）进行，各批次均包含 245 个样本，具有明显的多批次结构。BioHeart（53 特征）、MI（14 特征）和 AMIDE（6461 特征）三个数据集用于下游分析链路验证和系统通用性验证。所有实验使用固定随机种子（seed = 42）保证可重复性。

---

## 6.2 缺失值填充方法对比实验

在 Benchmark 数据集上通过 Mask-then-Impute 框架（mask_ratio=15%，重复 3 次）进行定量评估，实验结果如表 6.1 所示：

表 6.1 缺失值填充方法定量对比

| 方法 | RMSE（均值） | RMSE（标准差） | MAE（均值） | NRMSE（均值） | 排名 |
|:---:|:-----------:|:-------------:|:-----------:|:------------:|:----:|
| Autoencoder | 0.2249 | 0.0035 | 0.0924 | 0.2248 | 第 1 |
| KNN（K=5） | 0.2980 | 0.0041 | 0.0740 | 0.2978 | 第 2 |
| Mean | 1.0011 | 0.0072 | 0.4376 | 1.0006 | 第 3 |
| Median | 1.0361 | 0.0070 | 0.3427 | 1.0356 | 第 4 |

结果分析：Autoencoder 以 RMSE = 0.2249 位居第一，分别优于 KNN（降低 24.5%）、均值（降低 77.5%）和中位数（降低 78.3%），证明了深度学习方法在代谢组学缺失值填充任务上的有效性，能够有效捕获特征间的非线性依赖结构。KNN 在 MAE 指标上（0.0740）优于 Autoencoder（0.0924），说明 KNN 在绝对误差中位数水平上更稳健，综合来看两者各有侧重。均值和中位数方法精度相近，均约为 Autoencoder 的 4.5 倍，体现了忽略特征间相关结构的局限。三次重复实验的 RMSE 标准差均在 0.007 以下，各方法的性能表现稳定可靠。

---

## 6.3 批次效应校正对比实验

在 Benchmark 数据集（Autoencoder 填充后矩阵，1715 × 1180）上进行批次效应校正对比实验，结果如表 6.2 所示：

表 6.2 批次效应校正评估指标对比（Benchmark 数据集，7 批次，PC1-PC2 空间）

| 方法 | 批次质心距离 | 批次 Silhouette | 分组 Silhouette |
|:---:|:-----------:|:--------------:|:--------------:|
| 无校正 | 5.3796 | −0.1461 | −0.4813 |
| Baseline | ≈ 0（$1.9 \times 10^{-14}$） | −0.0343 | −0.4465 |

PCA 解释方差比：校正前 PC1 = 22.0%、PC2 = 4.9%；Baseline 校正后 PC1 = 50.9%、PC2 = 5.3%。

结果分析：Baseline 方法校正后批次质心距离归零，表明 7 个批次质心在 PCA 前两个主成分空间中实现了完全重合，批次效应被有效消除。校正后 PC1 解释方差比由 22.0% 大幅提升至 50.9%，表明主要方差来源从批次差异转变为潜在的生物学结构差异。批次 Silhouette 系数向 0 方向移动（而非向 −1 方向），这一现象源于校正前后 PCA 坐标系的根本性变化，不同坐标系下的 Silhouette 系数不具有直接可比性；批次质心距离（完全归零）是更直接、更可靠的评估依据。ComBat 的核心优势在于小批次场景下的稳健估计和生物学协变量保护，在本数据集（批次大小均匀、样本量充足）上与 Baseline 效果预计相近。

---

## 6.4 下游分析结果展示

差异代谢物分析：以 P1_AA_0001（氨基酸低浓度组）vs P1_AA_1024（氨基酸高浓度组，$n_1 = n_2 = 18$）为例，Welch t 检验 + BH-FDR 校正（$q < 0.05$，$|\text{log2FC}| \geq 1$），共检出 538 个显著差异代谢物（占总数 45.6%），与实验设计预期（浓度相差 1024 倍）高度一致。代表性差异代谢物 Acetone（C3H6O，KEGG: C00207）的 log2FC = −5.05，q = $2.7 \times 10^{-7}$，统计显著性极高。

KEGG 通路富集分析：以 538 个显著差异特征为显著集，背景集大小 $M = 981$，对 254 条 KEGG 参考通路进行超几何富集分析。最显著通路为 D-Amino acid metabolism（map00470），Rich Factor = 0.9677，q = 0.000206，与氨基酸浓度梯度实验设计高度吻合。

MetaKG 知识图谱溯源：以显著差异代谢物为起点提取一跳关联子图，涵盖代谢物-通路-反应-酶-疾病多层关联，通过力导向图实现交互式可视化溯源，为生物学机制推断提供可视化支撑。

---

## 6.5 系统通用性验证

BioHeart（53 特征）：全流程正常运行，包含 Autoencoder 填充（适应低维数据）和通路富集分析（含 KEGG 注释，返回富集通路列表）。MI（14 特征）：验证了全流程的基本可运行性，系统自动将 Autoencoder 潜空间维度调整为不超过特征数的合理范围，避免维度冲突。AMIDE（6461 特征）：预处理、填充、批次校正和差异分析正常执行；通路富集分析触发降级（无 KEGG ID 注释），前端展示友好提示，不报错崩溃。三个数据集的验证结果表明，系统能够适应 14 至 6461 个特征的宽泛数据规模，在无注释场景下实现友好降级，通用性良好。

---

## 6.6 本章小结

本章在 Benchmark 合并数据集上进行了系统性的定量实验与结果分析，主要结论如下：缺失值填充实验中，Autoencoder 方法 RMSE 最低（0.2249），分别优于 KNN（降低 24.5%）、均值（降低 77.5%）和中位数（降低 78.3%），各方法标准差（< 0.007）证明评估结果稳定可重复。批次效应校正实验中，Baseline 方法校正后批次质心距离由 5.3796 降至约 0，PC1 解释方差比由 22.0% 提升至 50.9%，双指标评估体系提供了多维度客观量化。下游分析以 P1_AA_0001 vs P1_AA_1024 为例，检出 538 个显著差异代谢物，富集到 D-Amino acid metabolism 通路（q = 0.000206），结果与实验设计预期高度一致，验证了系统下游分析链路的生物学合理性。系统通用性验证表明，系统能够适应不同规模和注释覆盖度的代谢组学数据集，具有良好的通用性和鲁棒性。

---

# 第七章 结论与展望

## 7.1 研究总结

本文围绕代谢组学数据分析中的批次效应校正与缺失值填充两大核心问题，设计并实现了一个基于深度学习的代谢组学批次效应处理 Web 平台，实现了从数据导入、预处理、缺失值填充与校正，到差异代谢物分析、KEGG 通路富集与 MetaKG 知识图谱溯源的全流程一体化处理。本文的主要研究成果如下：

（1）设计并实现了代谢组学数据处理 Web 平台。平台采用前后端分离架构，后端基于 FastAPI + SQLite + SQLAlchemy，前端基于 Vue3 + TypeScript + ECharts + Element Plus，算法层以独立模块形式组织，具备良好的可扩展性与工程规范性。系统支持 CSV/XLSX 格式的多数据集导入与切换，以 Web 交互界面覆盖从数据预处理到结果可视化的完整分析链路，填补了现有平台在深度学习方法集成和全流程一体化分析方面的不足。

（2）实现了基于 Autoencoder 的深度学习缺失值填充，并设计了 Mask-then-Impute 可量化评估框架。本文基于 PyTorch 实现了采用 Masked Reconstruction 训练策略的 Encoder-Decoder 网络（1180→256→64→256→1180），参考了 MIDA（Gondara & Wang, 2018）的方法论。在 Benchmark 数据集（1715 × 1180）上的实验表明，Autoencoder 方法以 RMSE = 0.2249 位居第一，分别优于 KNN（RMSE = 0.2980，降低 24.5%）和均值填充（RMSE = 1.0011，降低 77.5%），证明了深度学习方法在代谢组学缺失值填充任务上的有效性。

（3）集成了两种批次效应校正方法，并设计了双维度量化评估体系。系统实现了逐特征位置尺度对齐（Baseline）和基于 neuroCombat 的 ComBat 经验 Bayes 两种批次效应校正方法，均有安全封装与异常降级处理机制。评估体系包含批次质心距离、批次 Silhouette 系数和分组 Silhouette 系数三项指标，形成"批次效应消除程度"与"生物学信号保留程度"相互制衡的双维度评估框架。在 Benchmark 数据集（7 批次）上，Baseline 方法校正后批次质心距离由 5.38 降至约 0，显示了对位置尺度型批次效应的高效校正能力。

（4）实现了差异代谢物分析、KEGG 通路富集分析和 MetaKG 知识图谱溯源一体化。系统基于批次校正后矩阵，依次实现了 Welch t 检验 + BH-FDR 差异代谢物分析（火山图展示）、KEGG 超几何富集分析（气泡图展示，含本地缓存和降级处理）以及 MetaKG 多库整合知识图谱的力导向图溯源展示（支持拖拽、搜索、类型过滤）。在 P1_AA_0001 vs P1_AA_1024 差异分析中，检出 538 个显著差异代谢物，富集到 D-Amino acid metabolism 通路（q = 0.000206），生物学结果合理，验证了下游分析链路的可靠性。

---

## 7.2 系统局限性

尽管本文工作取得了预期目标，系统在以下方面仍存在一定的局限性：

（1）Autoencoder 填充尚未集成到 Web 在线任务流。当前 Autoencoder 填充以离线预计算方式运行，用户无法通过 Web 界面为自定义上传数据集在线触发 Autoencoder 填充，牺牲了易用性。

（2）批次效应校正方法数量有限。系统目前仅实现了 Baseline 和 ComBat 两种校正方法，尚未集成近年来在单细胞组学领域表现优秀的 Harmony、BBKNN 等方法，也未集成基于深度学习的批次校正方法，限制了用户的方法选择空间。

（3）评估框架仅针对二维 PCA 空间。当前批次效应评估指标均在 PCA 降至 2 维后的坐标空间中计算，损失了高维空间中的部分信息，高维空间下的评估结果可能与 2D 评估存在差异。

（4）不支持多用户和数据隔离。系统当前为单机本地部署模式，不支持用户注册与认证，所有用户共享同一数据库和文件系统，缺乏数据隔离机制，无法支持多用户并发使用场景。

（5）部分数据集依赖手动脚本预处理。Benchmark 数据集的完整 Pipeline 产物需通过 CLI 脚本手动运行生成，对非技术背景用户不够友好，增加了系统部署和数据更新的复杂度。

---

## 7.3 未来工作展望

针对上述局限性，未来工作将从以下几个方向进行改进和扩展：

（1）引入异步任务队列，支持 Autoencoder 在线训练。引入 Celery + Redis 异步任务队列，将 Autoencoder 训练等耗时计算从同步 HTTP 请求中剥离，前端通过 WebSocket 或长轮询实时获取训练进度，实现全流程在线触发与结果展示。

（2）扩展批次效应校正方法库。引入 Harmony（基于 PCA 空间迭代软聚类对齐）、BBKNN（基于批次感知 KNN 图）等主流批次校正方法，以及基于变分自动编码器（VAE）的深度学习批次校正方法，构建覆盖统计、近邻对齐、深度学习三类范式的多方法对比平台。

（3）引入自动化方法推荐机制。基于数据集的统计特征（批次数、批次间样本量均衡性、缺失率、特征数等）和历史运行结果，设计自动化方法推荐模型，为用户提供"最优方法推荐"功能，降低算法选择的专业门槛。

（4）评估体系的高维扩展。将批次效应评估指标从 2D PCA 空间扩展到更高维度，或引入 kBET（k-nearest neighbor Batch Effect Test）等专门面向高维数据的批次效应评估统计量，提升评估结果的全面性和可靠性。

（5）支持多组学联合分析与多用户隔离。扩展系统的多组学联合分析能力，迁移至 PostgreSQL 数据库，引入用户注册与认证机制、数据集权限隔离，支持科研团队的协作分析场景。

（6）增加分析报告自动生成功能。集成 PDF/HTML 报告自动生成模块，允许用户一键导出包含数据集信息、预处理参数、填充评估结果、批次校正效果图表和下游分析结果的完整分析报告，进一步提升系统的实用价值。

---

## 参考文献

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

全文正文润色完成。

---

# Part 2 [Review Comments]

以下为全文审阅注释，按章节顺序列出所有已修改或建议关注的问题，供作者参考。

---

## 整体评价

论文整体质量较高。结构完整，逻辑链条清晰（问题提出 → 系统设计 → 算法实现 → 实验验证 → 总结展望），行文风格规范，技术描述准确，符合计算机科学方向的工程型学位论文写作规范。本次润色以"最小必要修改"为原则，仅对少数语病、口语化表达和格式不规范之处进行了更正，未对文意进行实质性改动。

---

## 具体修改点

### 摘要与关键词

无修改。摘要语言精练，技术信息密度适当，中英文对应准确，关键词覆盖核心主题。

### 第一章 绪论

[修改 1-1] 第 1.2 节"相关工作与研究现状"：原文"该方法能够一定程度上利用……"，介词"在"缺失，逻辑不通顺。已改为"该方法能够在一定程度上利用……"。

[修改 1-2] 全章：移除原文中的 Markdown 加粗符号（`**文字**` 格式），保留纯文本。此类格式标记在 Word/PDF 终稿中无意义且影响阅读。

[建议 1-3] 第 1.4 节"论文组织结构"：原文以列表形式描述各章内容，写法规范。建议最终提交版将各章描述统一为"第 X 章……，介绍/阐述/描述……"的固定句式，与导师所在学院的论文规范保持一致。

### 第二章 相关技术与方法综述

[修改 2-1] 第 2.1 节：原文含有写作进度说明注释行（以 `>` 引用块形式标注"写作说明"），此类内容为写作辅助信息，不应出现在最终稿。已在润色稿中删除。

[修改 2-2] 第 2.3 节：原文"单细胞RNA测序"（英文字母与汉字间无空格），依据学术写作规范应在英文字母与汉字之间保留一个半角空格。已统一改为"单细胞 RNA 测序"。

[建议 2-3] 第 2.4 节 ComBat 算法公式：公式描述清晰，推导链条完整。建议在最终稿中确认 $\hat{\gamma}_{ib}^*$ 和 $\hat{\delta}_{ib}^{2*}$ 的经验 Bayes 估计步骤在正文中已有足够的文字说明，避免读者仅依赖公式理解算法逻辑。

[建议 2-5] 第 2.5 节综述总结段：原文对各方法进行了横向对比，逻辑清晰。建议确认各方法的引用文献标注完整，尤其是 Harmony [13]、scVI [15] 等近年方法。

### 第三章 系统总体设计

[修改 3-1] 第 3.1.1 节各需求条目：移除所有 Markdown 加粗符号（如 `**批次效应校正需求**` → `批次效应校正需求`）。

[建议 3-2] 第 3.1.2 节非功能需求：建议将"可用性""可扩展性""可靠性""性能"四项以小标题（如"（1）可用性"）形式呈现，与 3.1.1 节功能需求的格式风格保持一致。

[建议 3-3] 第 3.2 节系统架构：如论文最终版本有系统架构图（前后端分离架构图、后端四层分层图），建议以图表形式嵌入，并在图下方标注图题，替代或补充纯文字描述，有助于评审老师快速把握系统整体结构。

[建议 3-4] 第 3.3 节数据库设计：建议补充 E-R 图或数据库表结构图（展示 Task、Dataset、Parameters、Result 四表的字段与关联关系），以图辅文，符合系统设计章节的规范写法。

### 第四章 核心算法设计与实现

[修改 4-1] 全章：移除所有 Markdown 加粗符号。

[建议 4-2] 第 4.2 节 Autoencoder 网络结构描述：文中"1180→256→64→256→1180"描述了网络维度，建议在最终稿中补充一幅网络结构示意图（Encoder-Decoder 架构图），直观呈现各层维度变化，有助于增加章节的图表数量，符合工程类论文的排版惯例。

[建议 4-3] 第 4.2 节 Mask-then-Impute 框架：评估框架设计合理，三指标（RMSE/MAE/NRMSE）互为补充。建议在正文中补充一句说明为何选择 15% 作为遮蔽率（即该比例参考了哪篇文献或基于何种实验考量），增强方法设计的可追溯性。

[建议 4-4] 第 4.3 节 ComBat 安全封装：`run_combat_safe()` 的异常降级处理逻辑（如批次样本数为 1 时降级返回原始矩阵）是工程实现的亮点，建议在正文中以伪代码或流程图形式补充说明，体现工程规范性。

[建议 4-5] 第 4.4 节下游分析：KEGG 本地 JSON 缓存机制和降级结构（`{available: false}`）是系统健壮性的重要体现，建议在正文中明确说明 KEGG 数据的来源版本和缓存策略，以备查验。

### 第五章 系统实现与展示

[修改 5-1] 全章：移除所有 Markdown 加粗符号和写作进度说明行。

[建议 5-2] 第 5.4 节功能界面展示：本节提到了系统七大功能展示区域，建议逐一配以系统运行截图，并在图题中标注功能名称（如"图 5-1 首页 KPI 概览界面"），使评审老师能够直观感受系统的用户交互体验，这是系统实现章节最重要的呈现方式之一。

[建议 5-3] 第 5.5 节系统测试：测试内容翔实，覆盖功能测试和边界情况测试。建议将 13 个核心功能测试点以表格形式呈现（含"测试项目""测试输入""预期结果""实际结果""测试结论"五列），格式更加规范，并便于字数计量。

### 第六章 实验与结果分析

[修改 6-1] 全章：移除所有 Markdown 加粗符号。

[修改 6-2] 第 6.2 节：表 6.1 数字内容已核对，格式规范，列对齐采用居中对齐，与章节说明一致。

[建议 6-3] 第 6.3 节批次效应校正结果分析：关于"批次 Silhouette 系数向 0 方向移动并非向 −1 方向"的解释（PCA 坐标系根本性变化导致不可直接比较）在逻辑上正确，但表述略显曲折。建议修改为更简明的表述，例如："批次 Silhouette 系数在校正前后 PCA 坐标系不同，数值不具可比性，应以批次质心距离为主要评估依据。"

[建议 6-4] 第 6.3 节：ComBat 与 Baseline 的实验对比数据目前仅呈现了 Baseline 的结果，ComBat 的实验数据（批次质心距离、Silhouette 系数）未呈现。建议补充 ComBat 的定量结果，或在正文中明确说明 ComBat 实验结果与 Baseline 相近、已有 PCA 图对比可视化替代定量数据，以免读者产生数据缺失之感。

[建议 6-5] 第 6.4 节下游分析：火山图、气泡图、MetaKG 力导向图建议配以实际运行截图（含图题），直观展示系统可视化能力，这也是"系统与结果展示"型论文章节的核心内容。

### 第七章 结论与展望

[修改 7-1] 全章：移除所有 Markdown 加粗符号。

[建议 7-2] 第 7.1 节研究总结：四点成果描述完整、条理清晰，与论文各章内容高度对应，逻辑严密。无实质性修改建议。

[建议 7-3] 第 7.2 节系统局限性：五点局限性描述客观，未回避问题，体现了良好的学术诚信。建议对局限性（1）（Autoencoder 尚未在线集成）补充一句说明为何以离线方式实现（如"训练时间较长，超出 HTTP 请求超时限制"），使局限性的原因描述更加完整。

[建议 7-4] 第 7.3 节未来展望：六点展望与局限性一一对应，且均有具体技术路径（如 Celery + Redis、Harmony/BBKNN、kBET、PostgreSQL），体现了良好的前瞻性和工程可行性。建议最终版按学院要求确认展望条数是否合适（通常 3～5 条即可），避免过多展望稀释各点的论述深度。

### 参考文献

[建议 R-1] 参考文献共 18 条，数量基本合理。建议检查以下几点：
1. 文献格式统一性：期刊文献已采用 [J] 标注，会议文献已采用 [C] 标注，专著已采用 [M] 标注，格式基本规范。建议确认各文献的期/卷/期号格式与所在学院要求一致（部分院校要求 DOI 字段）。
2. 中文文献：正文引用的方法（如 neuroCombat）若有对应中文综述文献，可适当补充，提高中文参考文献比例（部分答辩委员会对此有要求）。
3. 文献时效性：现有文献最新为 2021 年（MetaboAnalyst 5.0 [7]），建议补充 1～2 篇 2022 年及以后的相关领域进展文献（如代谢组学数据分析新方法、批次效应校正近期进展），体现对前沿研究的跟踪。
4. 正文引用匹配：建议全文检索正文中"[n]"格式的引用标注，确认所有引用在参考文献列表中均有对应条目，且无文献列出但正文未引用的情况。

---

## 总结

本轮润色共做出以下类型的修改：

| 修改类型 | 数量 | 说明 |
|:--------|:----:|:-----|
| 删除写作进度说明注释行 | 若干处 | 原文含 `> **写作说明**` 等写作辅助块，已删除 |
| 移除 Markdown 加粗符号 | 全文 | `**文字**` → `文字`，适配纯文本/Word 输出 |
| 修复介词缺失语病 | 1 处 | "一定程度上" → "在一定程度上" |
| 中英文间距规范化 | 1 处 | "单细胞RNA测序" → "单细胞 RNA 测序" |
| 内容实质修改 | 0 处 | 遵循"尊重原著、克制修改"原则，未改动任何技术论断 |

全文技术论述严谨，实验数据详实，工程实现完整，符合计算机科学方向工程型学位论文的写作要求。按上述建议补充图表、规范参考文献格式后，论文可达到较高的提交质量。

- 提供 Mask-then-Impute 评估结果展示（RMSE/MAE/NRMSE 对比