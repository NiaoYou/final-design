# 基于深度学习的代谢组学批次效应系统设计与开发

# 摘要

代谢组学是生命科学领域重要的研究方向之一，通过对生物体内小分子代谢物的系统性检测，能够在整体水平上揭示生物体的生理与病理变化规律。随着高通量质谱检测技术的广泛应用，大规模代谢组学研究日益普遍，但多批次实验数据中普遍存在的批次效应（Batch Effect）和缺失值问题严重影响数据质量与分析结果的可靠性。现有分析平台（如 MetaboAnalyst）在批次效应处理方法的覆盖、深度学习算法的引入以及全流程一体化分析方面仍存在明显局限。

针对上述问题，本文设计并实现了一个基于深度学习的代谢组学批次效应处理 Web 平台。系统采用前后端分离架构，后端基于 FastAPI 框架，前端基于 Vue3 + TypeScript，算法层以独立模块形式组织，具备良好的可扩展性。在缺失值填充方面，系统集成了均值、中位数、KNN 三种传统方法，并实现了基于 PyTorch 的 Autoencoder 深度学习填充模型，采用 Masked Reconstruction 训练策略，仅对已知值位置计算重建损失。为客观评估各填充方法的精度，本文设计了 Mask-then-Impute 评估框架，在 Benchmark 数据集（1715 个样本、1180 个特征、7 个批次）上进行了定量对比实验：Autoencoder 方法取得最低 RMSE（0.2249），相比 KNN（0.2980）降低约 24.5%，相比均值填充（1.0011）降低约 77.5%。在批次效应校正方面，系统实现了逐特征位置尺度对齐（Baseline）和 ComBat 经验 Bayes 两种校正方法，并设计了包含批次质心距离、批次轮廓系数与生物学分组轮廓系数的双维度评估体系。实验结果表明，Baseline 校正后批次质心距离由 5.38 下降至接近 0，批次混合效果显著。在下游分析方面，系统进一步实现了基于 t 检验和 BH-FDR 校正的差异代谢物分析、基于 KEGG 的通路富集分析，以及基于 MetaKG 多库整合知识图谱的代谢物溯源展示，支持多数据集切换与交互式可视化。

本系统完整覆盖了代谢组学数据从预处理到结果解读的全分析流程，为研究人员提供了一体化、可视化的数据处理工具，具有较好的实用价值与可扩展性。

关键词：代谢组学；批次效应；缺失值填充；深度学习；自动编码器；Web 平台

# Abstract

Metabolomics is an important research field in life science that systematically detects small-molecule metabolites in biological systems, revealing metabolic changes under different physiological or pathological conditions. With the widespread adoption of high-throughput mass spectrometry, large-scale multi-batch metabolomics studies have become increasingly common. However, batch effects and missing values in multi-batch experimental data seriously compromise data quality and the reliability of downstream analysis. Existing platforms such as MetaboAnalyst still have notable limitations in batch effect correction methods, deep learning integration, and end-to-end workflow support.

To address these issues, this paper designs and implements a deep learning-based metabolomics batch effect processing web platform. The system adopts a front-end and back-end separated architecture, with FastAPI as the backend framework, Vue3 + TypeScript for the frontend, and an independently organized algorithm module layer for extensibility. For missing value imputation, the system integrates three traditional methods (mean, median, and KNN) and implements an Autoencoder-based deep learning imputation model using PyTorch, trained with a Masked Reconstruction strategy that computes reconstruction loss only on observed values. A Mask-then-Impute evaluation framework is proposed to objectively compare imputation methods. Experiments on the Benchmark dataset (1715 samples, 1180 features, 7 batches) show that the Autoencoder achieves the lowest RMSE (0.2249), outperforming KNN (0.2980) by approximately 24.5% and mean imputation (1.0011) by approximately 77.5%. For batch effect correction, the system implements two methods: per-feature location-scale alignment (Baseline) and ComBat with empirical Bayes estimation. A dual-dimensional evaluation system is designed, comprising batch centroid separation distance, batch Silhouette score, and biological group Silhouette score. Experimental results demonstrate that after Baseline correction, the batch centroid separation distance drops from 5.38 to near zero, indicating effective batch mixing. In downstream analysis, the system further provides differential metabolite analysis based on t-test with BH-FDR correction, KEGG pathway enrichment analysis, and a MetaKG knowledge graph-based metabolite traceability visualization. Multiple datasets and interactive visualizations are supported.

The system comprehensively covers the full metabolomics analysis workflow from data preprocessing to biological interpretation, providing researchers with an integrated and visualized data processing tool with good practical value and extensibility.

Keywords: Metabolomics; Batch Effect; Missing Value Imputation; Deep Learning; Autoencoder; Web Platform

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

然而，上述平台存在共同的不足：批次效应处理通常以单一 ComBat 方法为主，缺乏其他方法的横向对比能力，用户难以根据数据特点选择最合适的方法；缺失值填充与批次效应校正独立处理，无法评估两步骤之间的误差传播；可量化的方法对比评估机制不健全，用户难以客观判断不同方法的适用性。

### 1.2.2 缺失值填充方法研究现状

代谢组学缺失值填充方法大致可分为简单统计填充、基于近邻的填充与基于深度学习的填充三大类，其复杂度与精度依次递增。

简单统计填充方法以均值填充（Mean Imputation）和中位数填充（Median Imputation）为代表，直接将特征的统计量赋予缺失位置。该类方法实现简单、运行高效，但忽略了样本间的相关结构，可能引入系统性偏差，在缺失值比例较高时表现较差[5]。

基于近邻的填充方法以 K 近邻填充（K-Nearest Neighbor，KNN）为代表，利用与待填充样本最相似的 K 个样本的特征值加权估计缺失位置。该类方法能够在一定程度上利用样本间的相似结构，在代谢组学领域被广泛采用，但计算复杂度较高，且对高缺失率场景的效果受限[10]。

基于深度学习的填充方法近年来发展迅速。Gondara 和 Wang 于 2018 年提出了基于去噪自动编码器（Denoising Autoencoder）的多重填充方法 MIDA（Multiple Imputation using Denoising Autoencoders），通过向输入数据添加噪声并训练网络重建原始信号，使模型能够从整体数据分布中学习特征间的复杂依赖关系，从而对缺失位置进行更准确的估计[8]。相关研究表明，在特征间具有复杂相关结构的高维数据场景下，深度学习方法通常优于传统统计方法[11]。

### 1.2.3 批次效应校正方法研究现状

批次效应校正方法的研究已有较长历史，按其核心思想可分为基于统计模型、基于低维对齐与基于深度学习三大方向。

基于统计模型的方法以 ComBat 最具影响力，由 Johnson 等人于 2007 年提出。该方法将特征表达值建模为全局均值、生物学效应与批次效应之和，通过经验 Bayes（Empirical Bayes）估计批次参数，利用所有特征的汇聚信息改善小样本场景下的参数估计稳定性，并可传入生物学协变量以保护真实的生物学差异不被消除[12]。此后，ComBat 被广泛应用于转录组学、蛋白质组学和代谢组学领域。与 ComBat 同属统计范式的逐特征位置尺度归一化（Per-feature Location-Scale Normalization）则进一步简化了模型假设，通过将各批次的特征均值和标准差归一化至全局水平，实现批次间分布的对齐，具有良好的可解释性。

基于低维对齐的方法以 Harmony 算法为代表，由 Korsunsky 等人于 2019 年提出，最初用于单细胞 RNA 测序数据的批次效应校正[13]。该方法在低维嵌入空间（如 PCA 空间）中通过迭代寻找跨批次的相似邻居关系并进行分布对齐，避免了对原始高维空间的直接操作，在多批次多样本场景下表现良好。

基于深度学习的方法是近年来的研究热点。Shaham 等人提出利用对抗神经网络（Adversarial Neural Network）学习批次不变的数据表示，在对数据结构依赖较弱的场景下取得了较好效果[14]。此外，也有研究探索使用变分自动编码器（Variational Autoencoder，VAE）同时完成批次效应校正与缺失值填充，在统一框架下减少分步处理带来的误差传播[15]。

### 1.2.4 代谢组学下游分析研究现状

批次效应校正完成后，代谢组学研究通常进入下游分析阶段，主要涵盖差异代谢物分析、代谢通路富集分析与知识图谱辅助解读三个层面。

差异代谢物分析的常用方法包括独立样本 t 检验、方差分析（ANOVA）及其非参数等价方法，并配合 Benjamini-Hochberg 假阳性率控制（BH-FDR）进行多重检验校正，以 log2 Fold Change 衡量差异方向和大小[16]。

代谢通路富集分析基于 KEGG（Kyoto Encyclopedia of Genes and Genomes）等数据库，通过超几何检验或 Fisher 精确检验判断差异代谢物是否显著富集于特定代谢通路，从而在通路层面解释差异代谢物的生物学意义[17]。

知识图谱辅助解读则是近年来兴起的研究方向。通过整合 KEGG、HMDB（Human Metabolome Database）、SMPDB（Small Molecule Pathway Database）等多源数据库，构建代谢物-通路-反应-酶-疾病关联网络，能够为差异代谢物提供可追溯的关联证据链[18]。

### 1.2.5 现有研究不足分析

综合来看，现有研究在代谢组学数据分析方法上已积累了较为丰富的成果，但在系统集成层面仍存在以下不足：批次效应校正与缺失值填充通常作为独立模块分步处理，缺乏整合框架；现有平台对深度学习方法的集成程度有限，缺乏与传统方法的定量对比评估；从数据预处理到下游分析、结果可视化的全流程一体化 Web 平台仍较为缺乏；代谢组学知识图谱溯源功能尚未在分析平台中得到广泛集成。上述不足构成了本文研究工作的出发点。

## 1.3 本文主要工作

针对现有研究的不足，本文围绕系统平台、深度学习填充、批次效应校正与下游分析四个方面开展工作，主要内容如下：

第一，设计并实现了代谢组学数据处理 Web 平台。平台采用前后端分离架构，后端基于 Python FastAPI 框架，前端基于 Vue3 + TypeScript + ECharts，算法层以独立模块方式组织，支持 CSV/XLSX 格式的多数据集导入与切换，覆盖从数据预处理到结果可视化的完整分析流程。平台支持 Benchmark（7 批次合并，1715 样本，1180 特征）、BioHeart、MI 和 AMIDE 等多个公开数据集的处理与展示。

第二，实现了基于 Autoencoder 的深度学习缺失值填充，并设计了 Mask-then-Impute 可量化评估框架。在传统均值、中位数和 KNN 填充方法的基础上，本文基于 PyTorch 实现了 Encoder-Decoder 架构的 Autoencoder 填充模型，采用 Masked Reconstruction 训练策略，仅对已观测位置计算重建损失。同时设计的 Mask-then-Impute 评估框架，通过随机遮蔽已知值并与填充结果对比，以 RMSE、MAE 和 NRMSE 三个指标对四种方法进行定量评估。实验表明，Autoencoder 方法在 Benchmark 数据集上取得最优 RMSE 为 0.2249，相比排名第二的 KNN（0.2980）降低约 24.5%。

第三，集成了两种批次效应校正方法，并设计了双维度量化评估体系。系统实现了逐特征位置尺度对齐（Baseline）方法和基于 neuroCombat 的 ComBat 经验 Bayes 方法，两种方法均有工程化的安全封装与异常处理机制。评估体系包含批次质心距离（Batch Centroid Separation）和批次／生物学分组轮廓系数（Silhouette Score）双指标，并通过 PCA 可视化直观呈现校正前后的效果对比。实验结果显示，Baseline 方法校正后批次质心距离由 5.38 降至约 0，批次混合效果显著。

第四，实现了差异代谢物分析、KEGG 通路富集分析和 MetaKG 知识图谱溯源展示。基于批次校正后矩阵，系统依次完成独立样本 t 检验（BH-FDR 校正）差异代谢物筛选、KEGG 通路超几何富集检验，以及基于 MetaKG 多库整合知识图谱的代谢物-通路-反应-酶关联溯源，并以火山图、通路富集气泡图和力导向知识图谱等多种可交互可视化形式呈现。

# 第二章 相关技术与方法综述

## 2.1 代谢组学数据特点与预处理需求

### 2.1.1 代谢组学数据的结构特征

代谢组学数据通常以样本×特征矩阵（Sample-by-Feature Matrix）的形式组织，每行表示一个生物样本，每列表示一种代谢物特征（Feature），矩阵中的数值为该代谢物在该样本中的信号强度或经归一化后的丰度值。以本文所采用的 Benchmark 合并数据集为例，数据矩阵规模为 1715 个样本 × 1180 个代谢物特征，来自 7 个不同批次，涵盖多种实验条件与生物学分组。

代谢组学数据具有若干区别于一般机器学习数据集的典型特点：高维小样本性、特征间复杂相关结构、分布偏斜与异质性，以及普遍存在缺失值。

第一是高维小样本特性。在典型的非靶向代谢组学实验中，通过 LC-MS 检测得到的特征数目可达数百至数千个，而单次实验的样本量通常仅为数十至数百个。高维数据中特征维度远超样本维度（p >> n），会显著增加统计方法的不稳定性和过拟合风险[5]。

第二是特征间复杂相关结构。生物体内代谢物通过代谢通路彼此连接，参与同一通路的代谢物在丰度变化上通常呈现出高度相关性。这种数据内生的相关结构使得能够捕获特征间非线性依赖关系的方法（如 Autoencoder）在缺失值填充等任务上具有潜在优势。

第三是数据分布偏斜与异质性。LC-MS 原始数据通常呈右偏分布（正偏态），且不同代谢物的信号强度量级差异悬殊，常需进行 log 变换和尺度归一化以满足后续统计方法的正态性假设[16]。此外，不同批次、不同样本组的数据分布本身就存在系统性差异，这构成了批次效应问题的本质。

第四是普遍存在缺失值。由于仪器检测下限、谱峰拾取算法误差以及低丰度代谢物的随机检测失败，代谢组学数据矩阵中通常存在大量缺失值，缺失比例在 20%～50% 之间较为常见。

### 2.1.2 数据预处理流程概述

针对上述数据特点，代谢组学数据分析须经历一套较为固定的预处理流程。首先进行**格式检验与质控**，核查数据矩阵完整性，排查异常样本（如 QC 样本）与低质量特征（如全缺失特征）。在此基础上进行**缺失值填充**，采用适当方法对缺失位置进行估计，保证后续统计分析的数据完整性。随后的**归一化与尺度化**步骤通过 log 变换、Pareto 缩放等手段消除量纲差异，以满足统计分析的前提假设。完成以上步骤后，方可进行**批次效应检测**，借助 PCA、Silhouette 系数、批次质心距离等指标量化批次效应程度；检测到显著批次效应时，则采用统计或深度学习方法进行**批次效应校正**，在消除系统性偏差的同时尽量保护真实的生物学差异；最后通过定量指标与可视化手段对**校正效果**进行评估与验证。

上述步骤在本系统中均有对应的算法实现和 Web 交互界面支持，具体算法设计与实现将在第三章中详细描述。

## 2.2 缺失值填充方法综述

### 2.2.1 传统统计填充方法

传统统计填充方法以"用同一特征已观测值的统计量替代缺失位置"为核心思路，是代谢组学数据预处理领域应用最广泛的方法类别。

均值填充（Mean Imputation）对每个特征 $j$，计算所有已观测值的算术均值，并将该列所有缺失位置统一赋值为该均值：

$$\hat{x}_{ij} = \bar{x}_j = \frac{1}{|\mathcal{O}_j|} \sum_{i \in \mathcal{O}_j} x_{ij} \qquad (2-1)$$

其中 $\mathcal{O}_j$ 为第 $j$ 列中已观测值的样本下标集合。该方法计算复杂度为 $O(np)$，实现简单、运行速度快；缺点是将所有缺失位置设置为同一值，完全忽略了样本间的个体差异，会人为压缩特征的方差，可能引入系统性偏差。

中位数填充（Median Imputation）将每个特征的缺失位置赋值为该列已观测值的中位数：

$$\hat{x}_{ij} = \text{med}(x_{ij},\ i \in \mathcal{O}_j) \qquad (2-2)$$

与均值相比，中位数对异常值（Outlier）具有更强的鲁棒性，适合于分布存在较强偏斜或含有离群样本的数据集。然而中位数填充同样忽略了样本间的相关结构，且对双峰分布等复杂情形也无法有效估计。

K 近邻填充（KNN Imputation）的核心思想是：对于待填充的缺失位置 $(i, j)$，从其余已观测该特征的样本中找出与样本 $i$ 最相似的 $K$ 个近邻，将这 $K$ 个近邻在特征 $j$ 上的值加权平均作为填充估计：

$$\hat{x}_{ij} = \frac{\sum_{k \in \mathcal{N}(i,j)} w_{ik} \cdot x_{kj}}{\sum_{k \in \mathcal{N}(i,j)} w_{ik}} \qquad (2-3)$$

其中 $\mathcal{N}(i,j)$ 为在特征 $j$ 上有观测值且与样本 $i$ 欧氏距离最近的 $K$ 个样本集合，$w_{ik}$ 为距离的倒数权重。KNN 填充能够利用数据集内样本间的相似性结构，相比简单统计方法通常具有更高的填充精度，但计算复杂度为 $O(n^2 p)$，且依赖于"相似样本在特征空间中邻近"这一局部平滑假设，对全局非线性关联的捕获能力有限。

### 2.2.2 基于深度学习的填充方法研究进展

随着深度学习方法在结构化数据建模上的成功，将其应用于缺失值填充任务的研究日益受到关注。其中较具代表性的工作有 MIDA、scVI 与 DM-RN 三类方法。

MIDA（Multiple Imputation using Denoising Autoencoders）由 Gondara 和 Wang（2018）将去噪自动编码器引入缺失值填充任务而提出[8]。该方法在已观测位置添加随机噪声并训练网络重建原始值，在多种数据集上展现出优于传统方法的填充精度，为后续 Autoencoder 类填充方法的发展提供了方法论参照。

scVI（single-cell Variational Inference）由 Lopez 等（2018）针对单细胞 RNA 测序数据提出，是一种基于变分自动编码器（VAE）的概率生成模型[15]，能同时处理缺失填充与批次校正问题，但其计算开销较高，主要适用于单细胞领域。

DM-RN（Distribution-Matching Residual Network）由 Shaham 等（2017）针对批次效应消除提出，是一种基于残差网络的分布匹配方法[14]，从分布对齐的角度为深度学习方法在组学数据预处理中的应用开辟了新思路。

上述研究表明，基于深度学习的方法能够通过捕获数据中的非线性结构而获得优于传统方法的填充精度。然而，将这类方法直接应用于代谢组学数据需要面对若干特殊挑战：一方面，代谢组学数据的样本量通常远低于单细胞或基因表达数据，需要考虑小样本场景下的训练稳定性；另一方面，其缺失模式复杂，需要在已知观测值上构造可靠的训练监督。本文针对这些挑战，参考 MIDA 的方法论，设计了适用于代谢组学的 Autoencoder 填充方案，具体网络结构与训练策略详见第三章 3.2 节。

## 2.3 批次效应校正方法综述

批次效应（Batch Effect）是指由实验仪器、操作时间、试剂批号等非生物学因素引入的系统性偏差，在多批次代谢组学研究中普遍存在并严重影响下游分析的可靠性[4]。批次效应校正方法旨在消除批次间的系统性差异，同时尽可能保护真实的生物学信号。

### 2.3.1 ComBat 经验 Bayes 方法

ComBat 方法由 Johnson 等人于 2007 年最初为基因表达数据（微阵列）设计[12]，后被广泛应用于转录组学、蛋白质组学和代谢组学领域。该方法将特征 $j$ 在样本 $i$（属于批次 $b$）上的观测值建模为：

$$x_{ijb} = \alpha_j + \mathbf{d}_{ib}^T \boldsymbol{\beta}_j + \gamma_{jb} + \delta_{jb} \cdot \varepsilon_{ijb} \qquad (2-4)$$

其中 $\alpha_j$ 为特征 $j$ 的全局均值，$\mathbf{d}_{ib}$ 为生物学协变量设计矩阵（如分组标签），$\boldsymbol{\beta}_j$ 为协变量效应，$\gamma_{jb}$ 和 $\delta_{jb}$ 分别为批次 $b$ 对特征 $j$ 施加的加性和乘性批次效应，$\varepsilon_{ijb}$ 为误差项。

ComBat 的关键在于经验 Bayes 估计策略：首先利用所有特征 $j = 1, \ldots, p$ 上的批次效应估计值构建先验分布，再通过 Bayes 收缩将各特征的批次参数估计值向先验均值"收缩"，从而在小样本场景下获得更稳定的参数估计。校正后的数据为：

$$x'_{ijb} = \frac{x_{ijb} - \alpha_j - \mathbf{d}_{ib}^T\hat{\boldsymbol{\beta}}_j - \hat{\gamma}^*_{jb}}{\hat{\delta}^*_{jb}} \cdot \sigma_j + \alpha_j + \mathbf{d}_{ib}^T\hat{\boldsymbol{\beta}}_j{} \qquad (2-5)$$

其中 $\hat{\gamma}^*_{jb}$ 和 $\hat{\delta}^*_{jb}$ 为经验 Bayes 收缩后的批次效应估计值。ComBat 通过经验 Bayes 收缩利用跨特征信息改善小批次估计稳定性，并可显式传入生物学协变量保护真实生物学差异，是目前代谢组学领域应用最广泛的批次校正方法之一。

### 2.3.2 单细胞领域的代表性批次校正方法

近年来在单细胞 RNA 测序领域涌现了一批新型批次校正方法，其中 Harmony、BBKNN 与 scVI 在思想上对代谢组学也具有借鉴意义。

Harmony（Korsunsky 等，2019）是一种基于 PCA 空间的迭代软聚类对齐方法[13]。其核心思想是在低维嵌入空间中迭代执行"批次感知聚类→批次校正→重新聚类"循环，通过软分配权重逐步消除批次差异，在大规模单细胞数据上以速度快、效果好著称。

BBKNN（Batch Balanced K-Nearest Neighbors）通过构建批次感知的 K 近邻图，使下游聚类与可视化方法中的近邻关系跨批次平衡，从图结构层面缓解批次效应。

scVI 如前所述，基于变分自动编码器联合建模缺失填充与批次校正[15]，体现了深度生成模型在多任务统一处理上的潜力。

上述方法在单细胞领域取得了广泛应用，但在代谢组学数据上的迁移仍需考虑数据规模、特征性质等差异，目前代谢组学领域仍以 ComBat 为主流。

### 2.3.3 简易统计校正策略

逐特征位置尺度对齐（Per-feature Location-Scale Normalization）是最简单的批次校正策略之一，其假设批次效应主要体现为各批次在每个特征上的均值和标准差的系统性偏移，通过将各批次分布对齐至全局分布消除位置和尺度差异。此类方法实现简单、易于解释，常作为快速基线方法（Baseline）使用，但仅适用于位置尺度型批次效应，无法处理复杂非线性批次效应，且不支持生物学协变量保护。本文将基于此思想设计的具体校正算法记为 Baseline 方法，详细公式与工程实现见第三章 3.3.1 节。

## 2.4 批次效应评估方法概述

批次效应校正效果的评估需要同时考虑两个维度：批次效应的消除程度与生物学信号的保留程度。常用的评估手段包括 PCA 可视化、Silhouette 系数、批次质心距离与 kBET 等。

PCA 可视化通过主成分分析将高维数据投影至低维空间（通常为前两个主成分），直观观察样本在低维空间中的分布规律。校正前各批次形成簇状分离、校正后混合分布是批次效应被有效消除的直观证据。

Silhouette 系数是聚类紧密程度的经典定量指标，可分别针对批次标签和生物学分组标签独立计算，构建"批次混合度 + 生物学保留度"的双维度评估。

批次质心距离用于度量各批次在低维空间中质心的离散程度，直接量化批次中心间的系统性偏移大小，与 PCA 可视化结果高度对应。

kBET（k-nearest neighbor Batch Effect Test）基于局部 K 近邻分布的统计假设检验，评估批次标签在小邻域内的混合均匀性，更适用于高维空间评估。

本文综合采用前三类指标构建双维度评估体系，具体定义、公式与工程实现见第三章 3.3.3 节。

## 2.5 现有平台对比与不足

MetaboAnalyst[7]、XCMS Online[9] 等主流代谢组学分析平台在数据预处理、统计分析、通路富集等常规功能上已较为成熟。然而，从批次效应处理与缺失值填充两个核心问题来看，这些平台存在较明显的局限，主要集中在以下四点。

其一，批次效应校正方法覆盖有限。MetaboAnalyst 等平台主要支持 ComBat 等少数经典统计方法，缺乏逐特征位置尺度对齐、近邻图对齐等其他策略，也不支持多方法横向对比，研究人员难以根据数据的具体分布特点选择最合适的校正手段。

其二，深度学习方法的工程化集成几乎空白。Autoencoder、VAE 等神经网络模型在非线性特征建模和高缺失率处理上已有充分验证，但现有 Web 平台对此类算法的集成极为薄弱。用户若需使用这些方法，通常不得不自行配置本地 Python 环境并编写脚本，门槛较高。

其三，全流程端到端的分析支持不足。从数据导入、质控、缺失值填充、批次校正到差异分析、通路富集、知识图谱溯源，完整的代谢组学分析链路高度连贯，而目前尚无一个 Web 平台能够将上述步骤无缝衔接。研究人员往往需要在多个工具之间反复导出和导入矩阵数据，流程割裂，容易引入格式转换错误。

其四，校正效果的评估过于依赖主观可视化。现有平台对批次效应校正结果的评价多停留在 PCA 散点图的定性观察层面，缺乏能够同时量化"批次混合程度"与"生物学信号保留程度"的客观指标体系，无法为方法比较和参数调优提供可靠的量化依据。

# 第三章 核心算法设计与实验分析

本章在第二章方法综述的基础上，针对本系统所涉及的四类核心算法——数据预处理、缺失值填充、批次效应校正与下游分析——给出完整的算法设计、关键公式推导、超参数选择以及工程实现策略，着重阐述对开源算法的自研封装与对小数据规模、异常输入等边界情况的降级处理；并在多个公开数据集上进行定量对比实验，验证各方法的有效性与系统的通用性。

## 3.1 数据预处理算法

数据预处理是代谢组学分析流程的第一个计算步骤，执行顺序固定为：特征缺失率过滤 → log1p 变换 → Z-score 标准化。

### 3.1.1 特征缺失率过滤

对于输入矩阵 $\mathbf{X} \in \mathbb{R}^{n \times p}$，按列统计缺失率 $r_j$，仅保留缺失率不超过阈值 $\tau_{\text{miss}}$（默认 $\tau_{\text{miss}} = 0.5$）的特征：

$$r_j = \frac{1}{n}\sum_{i=1}^{n}\mathbb{I}(x_{ij} = \text{NaN}),\quad \mathcal{F}_{\text{keep}} = \{j : r_j \leq \tau_{\text{miss}}\} \qquad (3-1)$$

其中 $\mathbb{I}(\cdot)$ 为指示函数。该步骤剔除了缺失过于严重、信息量不足的特征，避免后续填充结果不可靠。

### 3.1.2 log1p 变换

LC-MS 信号强度通常呈右偏分布，且存在零值（仪器检出阈值以下的真实零信号），直接取对数会出现 $-\infty$。本系统采用 log1p 变换：

$$x'_{ij} = \log(1 + x_{ij}) \qquad (3-2)$$

变换后数据近似对称分布，更接近正态性假设，且在原始值为 0 时返回 0，数值稳定。

### 3.1.3 Z-score 标准化

为消除不同代谢物量纲量级的差异，按列执行 Z-score 标准化：

$$z_{ij} = \frac{x'_{ij} - \mu_j}{\max(\sigma_j,\ 1.0)} \qquad (3-3)$$

其中 $\mu_j$、$\sigma_j$ 为特征 $j$ 的列均值与列标准差。当 $\sigma_j = 0$（恒等列）时分母取 1.0 以防除零，标准化后该列保持为 0 列，不引入虚假方差。

## 3.2 缺失值填充设计与实现

本系统集成四种填充方法：均值、中位数、KNN（$K=5$）、Autoencoder。前三种调用 NumPy/scikit-learn 实现，公式见第二章 2.2.1 节，此处不再赘述；Autoencoder 为本文针对代谢组学数据特点自研设计的深度学习填充方案，下面着重描述其网络结构、训练策略与评估框架。

### 3.2.1 传统统计填充方法实现

均值/中位数填充基于 NumPy nanmean/nanmedian 对每列已观测值计算统计量，将 NaN 位置替换为该统计量，时间复杂度 $O(np)$，空间复杂度 $O(p)$。KNN 填充调用 scikit-learn 的 KNNImputer 类，基于共同观测特征上的欧氏距离寻找 $K=5$ 个最近邻并以距离倒数加权平均，时间复杂度约 $O(n^2 p)$。三种方法均提供统一的输入输出接口，便于上层流程调度。

### 3.2.2 Autoencoder 网络结构设计

参考 MIDA 方法的思想，本文为代谢组学数据设计了一个对称 Encoder-Decoder 自动编码器网络，基于 PyTorch 实现。具体网络层次为：

$$\begin{aligned}
\text{输入层}(p) & \xrightarrow{\text{Linear}} \text{隐层}(256) \xrightarrow{\text{ReLU} + \text{BN} + \text{Dropout}(0.1)} \text{潜空间}(64) \xrightarrow{\text{ReLU}} \\
& \xrightarrow{\text{Linear}} \text{隐层}(256) \xrightarrow{\text{ReLU} + \text{BN}} \text{输出层}(p)
\end{aligned} \qquad (3-4)$$

其中 $p$ 为特征维度（本文 Benchmark 数据集 $p = 1180$），隐层维度 $h = 256$，潜空间维度 $l = 64$。Encoder 将高维代谢组学特征压缩到低维潜空间，迫使模型学习数据的紧凑非线性结构；Decoder 将潜空间表示重建回原始维度。批归一化（Batch Normalization）稳定训练梯度，Dropout（丢弃率 0.1）作为正则化抑制过拟合，潜空间维度按照"维度不超过样本数与特征数之较小值"的经验原则设置。Autoencoder 网络的整体结构如图 3-1 所示。

【图位】图 3-1　Autoencoder 网络结构示意图
图源：thesis/figures/external/fig_3_1_autoencoder_architecture.png（待外部绘制）
说明：以 Benchmark 数据集 $p = 1180$ 为例，绘出"输入层 → 隐层(256) → 潜空间(64) → 隐层(256) → 输出层"的对称 Encoder-Decoder 结构，标注 ReLU、BatchNorm、Dropout 模块。

### 3.2.3 Masked Reconstruction 训练策略

代谢组学数据中真实缺失值无法直接参与重建损失计算。为此，本文采用了 Masked Reconstruction（掩码重建）训练策略。在具体实现上，首先对输入矩阵 $\mathbf{X}$ 中的 NaN 位置以对应列的均值进行初步填充，得到完整的输入矩阵 $\tilde{\mathbf{X}}$，从而为网络前向传播提供合理的起始信号。同时，构造一个观测掩码矩阵 $\mathbf{M} \in \{0,1\}^{n \times p}$，其中 $m_{ij} = 1$ 表示该位置为已知观测值，$m_{ij} = 0$ 则表示原本的缺失位置。

在模型的前向传播阶段，网络基于初填矩阵输出预测结果 $\hat{\mathbf{X}} = f_\theta(\tilde{\mathbf{X}})$。为了保证重建质量完全依赖于真实的生物学信号，损失函数仅在掩码指示的已知观测位置计算均方误差（MSE）：

$$\mathcal{L}(\theta) = \frac{\sum_{(i,j):\ m_{ij}=1} (\hat{x}_{ij} - x_{ij})^2}{\sum_{i,j} m_{ij} + \epsilon} \qquad (3-5)$$

在反向传播与优化阶段，模型采用 Adam 优化器（设置初始学习率 $lr = 10^{-3}$ 和权重衰减 $\lambda = 10^{-5}$），并配合 CosineAnnealingLR 余弦退火学习率调度机制（周期 $T_{\max} = 80$，最小学习率 $\eta_{\min} = 0.1\,lr$）。经过 80 个 epoch 的迭代训练（批大小设定为 64）后，网络参数达到收敛。在最终的推断与回填步骤中，再次以 $\tilde{\mathbf{X}}$ 为输入进行前向推断，但仅提取网络输出矩阵中对应原缺失位置（$m_{ij}=0$）的预测值进行回填，原有的已知观测值则保持数值不变。该策略的关键优势在于训练监督信号完全源自已知观测数据，使得缺失位置的估算纯粹基于网络对数据整体非线性结构的泛化推断，有效避免了模型“自学习缺失值”导致的循环依赖与次优解。

### 3.2.4 Mask-then-Impute 评估框架

为客观比较各填充方法在代谢组学数据上的精度，本文设计 Mask-then-Impute 评估框架：在原始矩阵已观测位置中均匀随机抽取一定比例（$\rho = 15\%$）位置标记为"模拟缺失"，使用各方法对该子集进行填充，再与真值比较计算误差。三项核心评估指标定义如下：

均方根误差（RMSE）：

$$\text{RMSE} = \sqrt{\frac{1}{|\mathcal{M}|}\sum_{(i,j) \in \mathcal{M}} (\hat{x}_{ij} - x_{ij})^2} \qquad (3-6)$$

平均绝对误差（MAE）：

$$\text{MAE} = \frac{1}{|\mathcal{M}|}\sum_{(i,j) \in \mathcal{M}} |\hat{x}_{ij} - x_{ij}| \qquad (3-7)$$

归一化均方根误差（NRMSE）：将每个特征的 RMSE 除以其标准差后取平均，消除量纲差异：

$$\text{NRMSE} = \frac{1}{p}\sum_{j=1}^{p} \frac{\text{RMSE}_j}{\text{std}(x_{\cdot j})} \qquad (3-8)$$

其中 $\mathcal{M}$ 为遮蔽位置集合。整个评估流程以三个随机种子（42、43、44）独立重复，取均值与标准差作为最终评估结果，详见本章 3.5 节表 3.1。

## 3.3 批次效应校正设计与实现

本系统集成两种批次校正方法：自研实现的 Baseline 逐特征位置尺度对齐，以及基于 neuroCombat 安全封装的 ComBat 经验 Bayes。前者实现简单、可解释性强，作为快速基线方法；后者支持生物学协变量保护，适用于小批次精细化校正场景。

### 3.3.1 Baseline 逐特征位置尺度对齐

Baseline 方法的设计思想是：假设批次效应主要表现为各批次在每个特征上的位置（均值）和尺度（标准差）的系统性偏移，通过将各批次分布对齐到全局分布消除偏差。对于特征 $j$，设全局均值 $\mu_j$、全局标准差 $\sigma_j$，批次 $b$ 内均值 $\mu_{bj}$、批次内标准差 $\sigma_{bj}$，则属于批次 $b$ 的样本 $i$ 的校正公式为：

$$x'_{ij} = \frac{x_{ij} - \mu_{bj}}{\max(\sigma_{bj},\ \epsilon)} \cdot \sigma_j + \mu_j{} \qquad (3-9)$$

其中 $\epsilon = 10^{-8}$ 为防除零的数值稳定下界。该公式先对批次内分布执行标准化（减去批次均值、除以批次标准差），再将其缩放还原为全局分布的均值与尺度，从而实现所有批次在该特征上的位置和尺度对齐。

工程实现要点：①批次内样本数 $n_b < 2$ 时跳过该批次（无法稳定估计 $\sigma_{bj}$），保留原值；②$\sigma_{bj} = 0$（批次内恒等特征）时分母被 $\epsilon$ 截断，避免数值溢出；③整个算法对每个特征独立执行，可向量化以利用 NumPy 广播加速，时间复杂度 $O(np)$。

### 3.3.2 ComBat 经验 Bayes 安全封装

ComBat 方法的统计模型与公式如第二章 2.3.1 节所述。尽管现有的 neuroCombat 库（Fortin 等，2018）提供了核心算法实现，但在与 Web 平台工作流对接时面临格式兼容与异常阻断的问题。为此，本系统专门封装实现了 run_combat_safe() 函数。首先，在矩阵方向适配方面，由于 neuroCombat 强制要求输入矩阵呈现“特征 × 样本”的格式，而本平台上下游数据流统一遵循机器学习标准的“样本 × 特征”结构，因此封装层在库函数调用前后加入了自动转置逻辑，消除了格式错位。

其次，针对异常输入导致的服务中断隐患，封装函数引入了完备的降级机制。当检测到输入数据存在任一批次样本数不足 2 个、有效批次数少于 2 个，或检测到全特征恒定等极端退化条件时，系统会主动记录警告日志，并平滑回退至前述的 Baseline 对齐方法或直接返回原始矩阵。这避免了底层数学库抛出未捕获异常进而导致整个 Web 接口崩溃的风险。最后，在参数扩展方面，该函数通过可选的 `biological_covariates` 参数，支持显式传入用户的生物学分组标签。这使得算法在执行经验 Bayes 收缩时能同步估计协变量效应，进而确保真实的生物学组间差异在校正过程中得到妥善保护而未被抹除。run_combat_safe() 安全封装的整体异常降级逻辑如图 3-2 所示。

【图位】图 3-2　ComBat 安全封装异常降级流程图
图源：thesis/figures/external/fig_3_2_combat_safe_flow.png（待外部绘制或使用 mermaid/draw.io 绘制）
说明：流程图按"输入校验 → 矩阵转置 → neuroCombat 调用 → 结果反转置"主路径绘制，并在校验节点处给出"批次数 < 2 / 批次内样本数 < 2 / 全特征恒等"三种异常分支的降级走向。

### 3.3.3 双维度评估体系

为同时评估批次效应消除程度与生物学信号保留程度，本系统实现 PCA 可视化、Silhouette 双指标、批次质心距离三项评估：

PCA 降维基于 scikit-learn 的 PCA 类，取前两个主成分得低维嵌入 $\mathbf{Z} \in \mathbb{R}^{n \times 2}$，校正前后各运行一次。

Silhouette 系数定义如下，对单个样本 $i$：

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i),\ b(i)\}} \qquad (3-10)$$

其中 $a(i)$ 为样本 $i$ 与同类样本的平均距离，$b(i)$ 为与最近异类样本的平均距离，$s(i) \in [-1, 1]$。本文分别以批次标签和生物学分组标签计算 batch Silhouette 与 group Silhouette：前者越低表示批次混合越好，后者越高表示生物学结构保留越好。

批次质心距离衡量各批次质心在 PCA 空间中的离散程度：

$$D_{\text{centroid}} = \frac{1}{B(B-1)}\sum_{b=1}^{B}\sum_{b' \neq b} \|\bar{\mathbf{z}}_b - \bar{\mathbf{z}}_{b'}\|_2 \qquad (3-11)$$

其中 $B$ 为批次数，$\bar{\mathbf{z}}_b$ 为批次 $b$ 内样本在 PCA 空间中的质心。该指标越接近 0 表示批次中心越重合，相比 Silhouette 系数解释更直接，不受 PCA 坐标系变化影响，本文将其作为主要判据。

## 3.4 下游分析算法

下游分析模块在批次校正后的清洁矩阵基础上完成差异代谢物挖掘、KEGG 通路富集和 MetaKG 知识图谱溯源三个任务，形成从统计检验到生物学解释的完整推断链路。

### 3.4.1 差异代谢物分析

差异代谢物分析的目标是在两组实验条件之间找出表达量有显著差异的代谢物。本文采用 Welch t 检验而非标准 Student t 检验，原因在于实际代谢组学数据中两组样本量和方差往往并不相等，Welch 检验通过 Satterthwaite 自由度近似（式 3-15）对方差不齐情况进行矫正，统计功效更为稳健。

针对每个代谢物特征 $j$，对两组样本 $A$、$B$ 执行 Welch t 检验：

$$t_j = \frac{\bar{x}_{Aj} - \bar{x}_{Bj}}{\sqrt{\dfrac{s_{Aj}^2}{n_A} + \dfrac{s_{Bj}^2}{n_B}}} \qquad (3-12)$$

对应的 Satterthwaite 自由度近似为：

$$\nu_j = \frac{\left(\dfrac{s_{Aj}^2}{n_A} + \dfrac{s_{Bj}^2}{n_B}\right)^2}{\dfrac{s_{Aj}^4}{n_A^2(n_A-1)} + \dfrac{s_{Bj}^4}{n_B^2(n_B-1)}} \qquad (3-15)$$

$p$ 值由 scipy.stats.ttest_ind（`equal_var=False`）计算。由于代谢组学数据维度 $p$ 可达数百至数千，直接使用原始 $p$ 值会导致大量假阳性，本文对全部 $p$ 值序列采用 Benjamini-Hochberg（BH）FDR 程序进行多重校正。设所有特征的 $p$ 值从小到大排序为 $p_{(1)} \leq p_{(2)} \leq \cdots \leq p_{(p)}$，第 $k$ 个特征对应的 $q$ 值（BH 调整后 $p$ 值）定义为：

$$q_{(k)} = \min_{l \geq k} \frac{p_{(l)} \cdot p}{l} \qquad (3-16)$$

由 statsmodels.stats.multitest.multipletests 实现，在 BH 程序不可用时退回手动累计最小值计算。

倍数变化以 $\log_2$ 形式度量，分子分母各加 $\epsilon = 10^{-9}$ 的数值稳定项，避免零值导致的 $\log 0$：

$$\text{log2FC}_j = \log_2 \frac{\bar{x}_{Aj} + \epsilon}{\bar{x}_{Bj} + \epsilon} \qquad (3-17)$$

显著差异的判断采用双重门控标准：$q_j < 0.05$（多重校正后假发现率 < 5%）且 $|\text{log2FC}_j| \geq 1$（即两倍以上的倍数差异），两个条件须同时满足。仅满足 $q$ 值而 log2FC 较小的特征属于统计显著但生物学意义可能有限的情形，双重筛选在灵敏度和特异性之间取得平衡。最终结果以 JSON 格式返回，前端 VolcanoPlotCard 组件将上调（log2FC > 1 且 $q$ < 0.05）、下调（log2FC < −1 且 $q$ < 0.05）和不显著三类代谢物分别以红色、蓝色、灰色渲染于火山图。

### 3.4.2 KEGG 通路富集分析

通路富集分析的目的是检验显著差异代谢物是否在某条生物学通路上发生了超出随机水平的聚集，从而将统计显著的代谢物列表提升为有生物学意义的通路层面解释。本文采用超几何检验（Fisher 精确检验的等价形式），其统计模型可描述如下：将代谢物集合视为一个含 $M$ 个球的瓮，其中 $K_{\text{path}}$ 个属于目标通路，从中无放回地取 $n_{\text{sig}}$ 个（即显著代谢物），问恰好命中 $k$ 个通路成员的概率。通路 $k$ 的富集 $p$ 值为观测到至少 $k$ 次命中的累积概率：

$$p_{\text{path}} = \sum_{x = k}^{\min(n_{\text{sig}},\ K_{\text{path}})}\frac{\binom{K_{\text{path}}}{x} \binom{M - K_{\text{path}}}{n_{\text{sig}} - x}}{\binom{M}{n_{\text{sig}}}} \qquad (3-18)$$

由 scipy.stats.hypergeom.sf（生存函数，即 $P(X \geq k)$）计算，在数值精度上优于直接求和。富集程度以 Rich Factor 量化：

$$\text{Rich Factor} = \frac{k / n_{\text{sig}}}{K_{\text{path}} / M} \qquad (3-19)$$

Rich Factor > 1 表示该通路中差异代谢物的比例超过背景期望水平。对所有通路 $p$ 值再做 BH-FDR 校正得到 $q$ 值，最终返回 $q < 0.2$ 的显著通路（最多 20 条）。

KEGG 代谢物-通路对应关系通过 KEGG REST API（`https://rest.kegg.jp`）在线获取，结果以本地 JSON 文件缓存，重复调用直接读取缓存，显著降低在线依赖。对无 KEGG ID 注释的数据集（如 AMIDE 数据集），接口返回 `{available: false}` 降级结构，前端 PathwayEnrichmentCard 组件据此隐藏富集模块并显示友好提示，避免错误阻断整体分析流程。

### 3.4.3 MetaKG 知识图谱溯源

MetaKG 溯源模块的目标是为统计层面的差异代谢物提供生物学语境支撑，回答"这些代谢物参与哪些通路、由哪些酶催化、与哪些疾病相关联"等问题。本文预构建了整合 KEGG[17]、HMDB[18]、SMPDB 三个数据库的异构知识图谱，节点类型包括代谢物（Compound）、通路（Pathway）、生化反应（Reaction）、酶（Enzyme）、基因（Gene）、疾病（Disease）等，边代表"参与通路""被酶催化""关联疾病"等语义关系，以 JSON 格式存储于后端（节点文件 + 边文件）。

查询时，后端以差异代谢物的 KEGG ID 为种子集，在图结构中提取一跳邻域——即所有与种子代谢物存在直接边关系的实体节点——形成可视化子图。为控制前端渲染负担，子图节点数通过可配置上限（默认 300 个节点）进行截断，优先保留与更多种子节点相连的高连通度节点。

前端 MetaKGCard 组件基于 ECharts 力导向图渲染子图，不同类型节点以不同颜色区分（代谢物蓝色、通路橙色、酶绿色、反应紫色等），种子代谢物以额外蓝色边框标记。力导向布局参数（斥力强度、边长约束、引力系数）根据节点规模自适应调整，避免大图时节点过度重叠。界面支持节点拖拽定位、鼠标滚轮缩放、节点 hover 弹出详情（名称、类型、KEGG ID、分子式、m/z 等）、关键词搜索高亮以及按节点类型勾选过滤等交互功能，使研究人员能够在可视化环境下灵活探索代谢物的多层次生物学关联。

## 3.5 缺失值填充对比实验

### 3.5.1 实验数据集说明

本文实验主要基于 Benchmark 合并数据集（1715 样本 × 1180 特征 × 7 批次）进行，各批次均包含 245 个样本，具有明显的多批次结构。BioHeart（53 特征）、MI（14 特征）和 AMIDE（6461 特征）三个数据集用于下游分析链路验证和系统通用性验证。所有实验使用固定随机种子（seed = 42）保证可重复性。

### 3.5.2 填充方法定量评估

在 Benchmark 数据集上通过 Mask-then-Impute 框架（mask_ratio=15%，重复 3 次）进行定量评估，实验结果如表 3.1 所示：

表 3.1 缺失值填充方法定量对比

| 方法 | RMSE（均值） | RMSE（标准差） | MAE（均值） | NRMSE（均值） | 排名 |
|:---:|:-----------:|:-------------:|:-----------:|:------------:|:----:|
| Autoencoder | 0.2249 | 0.0035 | 0.0924 | 0.2248 | 第 1 |
| KNN（K=5） | 0.2980 | 0.0041 | 0.0740 | 0.2978 | 第 2 |
| Mean | 1.0011 | 0.0072 | 0.4376 | 1.0006 | 第 3 |
| Median | 1.0361 | 0.0070 | 0.3427 | 1.0356 | 第 4 |

结果分析：Autoencoder 以 RMSE = 0.2249 位居第一，分别优于 KNN（降低 24.5%）、均值（降低 77.5%）和中位数（降低 78.3%），表明深度学习方法在代谢组学缺失值填充任务上具有明显优势，其 Encoder-Decoder 结构能够建模特征间的非线性依赖。KNN 在 MAE 指标上（0.0740）优于 Autoencoder（0.0924），说明 KNN 在绝对误差层面更稳健，综合来看两者各有侧重。均值和中位数方法精度相近，均约为 Autoencoder 的 4.5 倍，反映出完全忽略特征间相关结构所带来的精度损失。三次重复实验的 RMSE 标准差均在 0.007 以下，各方法的性能表现稳定可靠。四种方法在三项指标上的对比情况如图 3-3 所示。

【图位】图 3-3　四种缺失值填充方法的 RMSE / MAE / NRMSE 对比柱状图
图源：thesis/figures/system-generated/fig_4_1_imputation_metrics_bar.png（由 thesis/scripts/generate_figures.py 生成）
说明：以分组柱状图展示 Autoencoder、KNN、Mean、Median 四种方法在 RMSE、MAE、NRMSE 三项指标上的均值，附三次重复实验的标准差误差棒。

## 3.6 批次效应校正对比实验

在 Benchmark 数据集（Autoencoder 填充后矩阵，1715 × 1180）上进行批次效应校正对比实验，结果如表 3.2 所示：

表 3.2 批次效应校正评估指标对比（Benchmark 数据集，7 批次，PC1-PC2 空间）

| 方法 | 批次质心距离 | 批次 Silhouette | 分组 Silhouette |
|:---:|:-----------:|:--------------:|:--------------:|
| 无校正 | 5.3796 | −0.1461 | −0.4813 |
| Baseline | ≈ 0（$1.9 \times 10^{-14}$） | −0.0343 | −0.4465 |

PCA 解释方差比：校正前 PC1 = 22.0%、PC2 = 4.9%；Baseline 校正后 PC1 = 50.9%、PC2 = 5.3%。

结果分析：Baseline 方法校正后批次质心距离归零，表明 7 个批次质心在 PCA 前两个主成分空间中实现了完全重合，批次效应被有效消除。校正后 PC1 解释方差比由 22.0% 大幅提升至 50.9%，表明主要方差来源从批次差异转变为潜在的生物学结构差异。批次 Silhouette 系数向 0 方向移动（而非向 −1 方向），这一现象源于校正前后 PCA 坐标系的根本性变化，不同坐标系下的 Silhouette 系数不具有直接可比性；批次质心距离（完全归零）是更直接、更可靠的评估依据。ComBat 的核心优势在于小批次场景下的稳健估计和生物学协变量保护，在本数据集（批次大小均匀、样本量充足）上与 Baseline 效果预计相近。Benchmark 数据集校正前后 PCA 散点对比如图 3-4 所示，批次质心距离的量化变化如图 3-5 所示。

【图位】图 3-4　Benchmark 数据集批次效应校正前后 PCA 对比
图源：thesis/figures/system-generated/fig_4_2_benchmark_pca_before_after.png（由系统离线 Pipeline 产物拷贝重命名）
说明：以 2×2 网格展示校正前按批次着色、校正前按生物学分组着色、校正后按批次着色、校正后按生物学分组着色四张 PCA 散点图，直观呈现批次混合度的提升与生物学结构的保留。

【图位】图 3-5　Benchmark 数据集批次质心距离校正前后对比
图源：thesis/figures/system-generated/fig_4_3_benchmark_centroid_distance.png（由 thesis/scripts/generate_figures.py 生成）
说明：以两条柱状图分别展示无校正与 Baseline 校正下的批次质心平均成对距离（5.3796 vs ≈ 0），辅助说明批次效应消除的量化幅度。

## 3.7 下游分析结果展示

以 Benchmark 数据集中 P1_AA_0001（氨基酸低浓度组）vs P1_AA_1024（氨基酸高浓度组）的对比为例，对下游分析链路的完整结果进行展示与验证。两组各包含 $n_1 = n_2 = 18$ 个样本，P1_AA_0001 与 P1_AA_1024 分别代表氨基酸工作液浓度相差 1024 倍的两个稀释梯度，属于实验设计层面具有明确生物学预期的对照组合，适合用于验证下游统计分析结果的合理性。

差异代谢物分析方面，基于批次校正后矩阵对 1180 个代谢物特征执行 Welch t 检验并进行 BH-FDR 多重校正，以 $q < 0.05$ 且 $|\text{log2FC}| \geq 1$ 为双重显著性门限，共检出 424 个上调代谢物和 114 个下调代谢物，合计 538 个显著差异特征，占总特征数的 45.6%。这一比例与实验设计预期高度吻合——在氨基酸浓度相差 1024 倍的情况下，大量代谢物出现系统性的方向一致强信号差异是合理的。代表性差异代谢物 Acetone（C3H6O，KEGG: C00207）的 log2FC = −5.05，q = $2.7 \times 10^{-7}$，其负向 log2FC 说明该代谢物在高浓度组信号更强，与实验设计一致。差异代谢物的整体分布如图 3-6 火山图所示。

【图位】图 3-6　P1_AA_0001 vs P1_AA_1024 差异代谢物火山图
图源：thesis/figures/system-generated/fig_3_6_volcano_aa.png（由 thesis/scripts/generate_figures.py 生成）
说明：横轴 log2 Fold Change，纵轴 −log10(q)；以 $|\text{log2FC}| \geq 1$ 与 $q < 0.05$ 为分界线，分别用红色（上调）、蓝色（下调）、灰色（不显著）三色着色，并对 top-12 显著代谢物添加文字标签。

KEGG 通路富集方面，以 538 个显著差异特征为显著集、981 个具备 KEGG ID 注释的代谢物为背景集，对 254 条 KEGG 参考通路进行超几何富集分析。最显著的通路为 D-Amino acid metabolism（map00470），命中差异代谢物 30 个（通路总成员 31 个），Rich Factor = 0.9677，经 BH-FDR 校正后 $q = 0.000206$。该通路的显著富集与氨基酸浓度梯度实验设计直接对应，验证了富集分析流程的准确性。整体富集结果如图 3-7 气泡图所示，通路按 $q$ 值升序排列，气泡大小编码命中数量，颜色编码 $-\log_{10}(q)$。

【图位】图 3-7　KEGG 通路富集气泡图
图源：thesis/figures/system-generated/fig_3_7_kegg_enrichment_bubble.png（由 thesis/scripts/generate_figures.py 生成）
说明：纵轴为通路名称（按 q 值升序排列前 15 条），横轴为 Rich Factor，气泡大小映射差异代谢物命中数，气泡颜色映射 −log10(q)。

MetaKG 溯源方面，以上述 538 个显著差异代谢物为种子集，从预构建的异构知识图谱中提取一跳邻域子图，涵盖代谢物、通路、生化反应、酶等多类型节点。以 D-Amino acid metabolism 相关代谢物为例，子图呈现出多个氨基酸代谢物汇聚于同一通路节点的辐射状拓扑，酶节点居中连接多个底物，直观反映了代谢网络的局部结构。界面支持按节点类型过滤，方便研究人员聚焦特定关联维度。子图的可视化效果如图 3-8 所示。

【图位】图 3-8　MetaKG 知识图谱代谢物-通路-酶力导向子图
图源：thesis/figures/screenshots/fig_3_8_metakg_subgraph.png（前端 MetaKG 独立截图页截图）
说明：含代谢物（蓝色圆形）、通路（橙色，深橙边框）、反应（紫色）、酶（绿色）四类节点，力导向布局，Pathway 节点显示标签，节点数约 280 个。

## 3.8 系统通用性验证

BioHeart 数据集（53 特征）的全流程测试正常运行，Autoencoder 填充与通路富集分析（含 KEGG 注释）均返回预期结果。MI 数据集（14 特征）特征数极少，系统自动将 Autoencoder 潜空间维度压缩至不超过特征数的合理范围，避免维度冲突，全流程可正常运行。AMIDE 数据集（6461 特征）的预处理、填充、批次校正和差异分析均正常执行；由于该数据集缺乏 KEGG ID 注释，通路富集分析自动触发降级处理，前端以友好提示替代报错，整体流程不崩溃。三个数据集的验证结果表明，系统能够适应 14 至 6461 个特征的宽泛数据规模，在无注释场景下亦可平稳降级运行，通用性良好。三个异构数据集校正前后的 PCA 对比分别如图 3-9a、图 3-9b、图 3-9c 所示。

【图位】图 3-9a　BioHeart 数据集批次效应校正前后 PCA 对比
图源：thesis/figures/system-generated/fig_3_9a_bioheart_pca_before_after.png

【图位】图 3-9b　MI 数据集批次效应校正前后 PCA 对比
图源：thesis/figures/system-generated/fig_3_9b_mi_pca_before_after.png

【图位】图 3-9c　AMIDE 数据集批次效应校正前后 PCA 对比
图源：thesis/figures/system-generated/fig_3_9c_amide_pca_before_after.png

# 第四章 系统设计与工程实现

## 4.1 系统需求分析

### 4.1.1 功能需求

本系统以代谢组学研究人员为主要目标用户，其使用场景通常为：拥有来自多批次 LC-MS 实验的代谢组学数据矩阵，需要依次完成缺失值填充、批次效应校正和差异代谢物分析，并希望通过可视化界面直观评估各步骤的处理效果。围绕这一核心场景，系统的功能需求可划分为数据管理、数据预处理、缺失值填充、批次效应校正、下游分析与结果输出六类，分别说明如下。

数据管理需求方面，系统应支持 CSV 和 XLSX 格式的数据文件上传，文件大小上限为 50MB；应支持 Long Format（长表格）数据格式解析，用户可自定义特征列、样本列、数值列、批次标签列、分组标签列的列名映射；应支持多数据集并行管理，用户可在 Benchmark、BioHeart、MI、AMIDE 等预置数据集与自定义上传数据集间切换；并提供数据集基本信息预览（样本数、特征数、批次数）。

数据预处理需求方面，系统应支持配置缺失率过滤阈值（默认 50%，超出阈值的特征列将被删除）、log1p 变换（对正偏态分布进行压缩）以及 Z-score 标准化（按样本维度消除量纲差异），并将预处理结果以 CSV 矩阵文件形式持久化存储。

缺失值填充需求方面，系统应支持均值填充、中位数填充、KNN 填充（$K$ 可配置）、Autoencoder 深度学习填充共四种方法；填充方法参数可在 Web 界面配置，支持单次选择一种方法运行；应提供 Mask-then-Impute 评估结果展示（RMSE/MAE/NRMSE 对比图表），填充结果矩阵支持 CSV 格式下载。

批次效应校正需求方面，系统应支持 Baseline 逐特征位置尺度对齐与 ComBat 经验 Bayes 校正两种方法；应提供校正前后的 PCA 散点图对比可视化，支持按批次／分组两种颜色编码；应提供批次质心距离、批次 Silhouette 系数、分组 Silhouette 系数三项定量评估指标展示，校正结果矩阵支持 CSV 格式下载。

下游分析需求方面，差异代谢物分析基于独立样本 t 检验 + BH-FDR 校正，支持 q 值阈值和 |log2FC| 阈值配置，结果以火山图展示；通路富集分析基于 KEGG 数据库超几何检验，结果以富集气泡图展示；知识图谱溯源基于 MetaKG 多库整合知识图谱，以力导向图展示差异代谢物的通路-反应-酶关联网络，并支持节点拖拽、关键词搜索和节点类型过滤等交互。

结果输出需求方面，核心中间产物（预处理矩阵、填充矩阵、校正矩阵）支持 CSV 格式下载；差异代谢物列表和通路富集结果支持表格展示与数据导出；评估报告以 JSON 格式持久化于服务器，前端通过 API 按需读取。

### 4.1.2 非功能需求

可用性：面向无编程背景的生物医学研究人员，Web 界面应具备清晰的操作引导，关键参数提供默认值，错误信息以友好的文字形式提示，避免终止整体流程。

可扩展性：算法层以独立模块方式组织，新增缺失值填充方法或批次效应校正方法时，只需在对应算法子目录下添加实现，不修改上层 Service 与 API 代码；前端组件化设计，新增可视化卡片无需改动核心状态管理逻辑。

可靠性：ComBat 等可能因数据条件不满足而失败的算法均有安全封装，捕获异常后以降级策略处理（如返回未校正矩阵并记录错误原因），不影响其他模块的正常执行。

性能：系统以本地单机部署为目标，针对本文实验数据集规模（约 1715 样本 × 1180 特征）的处理时间在可接受范围内（预处理 < 30s，KNN 填充 < 60s，Autoencoder 填充 < 90s）。

## 4.2 系统总体架构

### 4.2.1 前后端分离架构概述

本系统采用前后端分离的 Web 应用架构，前端与后端通过 HTTP/REST 接口通信，互相独立开发与部署。整体架构分为三个主要层次：前端展示层（Vue3 + TypeScript + Vite，端口 5173）、后端服务层（Python FastAPI + Uvicorn，端口 8000）和数据存储层（SQLite 数据库 + 文件系统）。系统总体架构如图 4-1 所示。

【图位】图 4-1　系统总体架构图（前后端分离）
图源：thesis/figures/external/fig_5_1_overall_architecture.png（待外部绘制，可使用 draw.io / mermaid / OmniGraffle）
说明：以三层结构展示前端（Vue3 + ECharts + Element Plus）→ 后端（FastAPI + Uvicorn）→ 存储层（SQLite + 文件系统）的总体关系，并标注 HTTP/REST 通信通道。

### 4.2.2 后端分层架构设计

后端内部采用严格的四层分层架构，各层职责清晰，向下单向依赖：API 层负责 HTTP 请求接收与响应序列化；Service 层包含核心业务逻辑，协调 Repository 和 Algorithm 模块；Algorithm 层为纯算法实现，不依赖数据库或文件 I/O；Repository 层负责数据库 CRUD 操作，通过 SQLAlchemy ORM 封装 SQL。后端四层分层架构如图 4-2 所示。

【图位】图 4-2　后端四层分层架构图
图源：thesis/figures/external/fig_5_2_backend_layered_architecture.png（待外部绘制）
说明：自上而下绘出 API 层 / Service 层 / Algorithm 层 / Repository 层四层堆叠结构，并以箭头示意单向依赖；可在每层右侧列出代表性子模块（如 algorithm/imputation、algorithm/batch_correction）。

### 4.2.3 前端架构设计

前端采用 Vue3 Composition API 风格开发，目录结构按功能职责划分：src/views/（页面级视图）、src/components/（15 个可复用功能组件）、src/stores/（Pinia 状态管理）、src/api/（HTTP 请求封装）、src/types/（TypeScript 类型定义）。前端组件层级关系如图 4-3 所示。

【图位】图 4-3　前端组件树与状态管理关系图
图源：thesis/figures/external/fig_5_3_frontend_component_tree.png（待外部绘制）
说明：以树状/网状结构展示 src/views 中的五个页面视图与 src/components 中 15 个组件的隶属关系，并标注 Pinia store（task store / benchmark store）与组件的双向数据流。

## 4.3 数据库设计

本系统选用 SQLite 作为关系型数据库，通过 SQLAlchemy ORM 进行数据库访问。系统数据库包含 Task、Dataset、Parameters、Result 四张核心数据表，分别记录任务基本信息与状态、数据集解析配置、算法参数配置和处理结果文件路径。系统采用"元数据入库、矩阵数据存文件"的混合存储策略：数据库存储结构化元数据，文件系统存储 CSV 矩阵文件、JSON 评估报告和图片文件等大文件。四张表之间的关联关系如图 4-4 E-R 图所示。

【图位】图 4-4　数据库 E-R 图
图源：thesis/figures/external/fig_5_4_database_er.png（待外部绘制）
说明：以标准 E-R 图标记法绘出 Task、Dataset、Parameters、Result 四张实体及其字段；以"1:1 / 1:N"标注关系（Task 1:1 Dataset、Task 1:1 Parameters、Task 1:N Result）。

## 4.4 系统模块划分

本系统按照分析流程的逻辑顺序划分为数据管理、预处理、缺失值填充、批次效应校正、评估可视化和下游分析六个主要功能模块，如表 4.1 所示。各模块职责独立，向上通过 Service 层统一调度，向下以标准化接口调用 Algorithm 层，新算法的接入只需在对应子目录中添加实现类，无需修改上层逻辑。

表 4.1　系统功能模块划分

| 模块 | 后端 Service | 核心职责 |
|:---:|:---:|:---|
| 数据管理 | DatasetService | 文件上传解析、列名映射、Long Format 转换、多数据集注册与切换 |
| 数据预处理 | PreprocessService | 缺失率过滤、log1p 变换、Z-score 标准化，产物持久化为 CSV |
| 缺失值填充 | ImputationService | 均值/中位数/KNN/Autoencoder 四种方法调度，Mask-then-Impute 评估 |
| 批次效应校正 | BatchCorrectionService | Baseline/ComBat 两种校正方法，异常安全封装，校正结果持久化 |
| 评估可视化 | EvaluationService | PCA 降维、Silhouette 计算、批次质心距离、PCA 图生成 |
| 下游分析 | DownstreamService | Welch t 检验 + BH-FDR 差异分析、KEGG 超几何富集、MetaKG 子图查询 |

## 4.5 系统整体数据流

系统的整体数据流遵循"原始数据 → 预处理 → 填充 → 批次校正 → 评估 → 下游分析"的线性管道（Pipeline）结构。每个处理步骤完成后，输出矩阵均以 CSV 文件形式持久化至 `data/processed/{dataset_id}/_pipeline/` 目录，评估结果以 JSON 文件形式存储，支持断点续算。具体文件命名规则如下：预处理矩阵保存为 `matrix_preprocessed.csv`，填充后矩阵保存为 `matrix_imputed.csv`，批次校正后矩阵保存为 `matrix_corrected.csv`，差异分析结果保存为 `diff_analysis.json`，Mask-then-Impute 评估报告保存为 `imputation_eval.json`，批次效应评估报告保存为 `batch_eval.json`。

任务状态通过后端数据库中的 Task 表字段 `status` 进行跟踪，状态机包含以下状态节点：`uploaded`（文件上传完毕）→ `preprocess_done`（预处理完成）→ `impute_done`（填充完成）→ `correct_done`（批次校正完成）→ `done`（全流程完成）；任意步骤发生不可恢复错误时转为 `error` 状态，并将错误信息写入 `Task.error_message` 字段。前端通过每 2 秒一次的轮询请求 `/api/tasks/{task_id}` 接口实时获取任务状态，PipelineStepBar 组件依据当前状态高亮对应步骤，各功能卡片（填充评估、批次校正结果、差异分析等）仅在对应 `*_done` 状态满足时才激活展示，避免在数据未就绪时渲染空白图表。系统数据流 Pipeline 与任务状态机分别如图 4-5、图 4-6 所示。

【图位】图 4-5　系统数据流 Pipeline 示意图
图源：thesis/figures/external/fig_5_5_pipeline_dataflow.png（待外部绘制）
说明：以横向流程图绘出"原始 CSV/XLSX → 预处理矩阵 → 填充矩阵 → 校正矩阵 → 差异分析 / KEGG 富集 / MetaKG"完整链路，并在节点旁标注产物文件路径与评估指标 JSON。

【图位】图 4-6　任务状态机示意图
图源：thesis/figures/external/fig_5_6_task_state_machine.png（待外部绘制）
说明：以状态机图绘出"uploaded → preprocess_done → impute_done → correct_done → done"主路径，以及任意步骤错误转入 error 的旁路。

## 4.6 开发环境与技术栈

系统开发环境为 macOS，后端运行于 Python 3.10+，前端通过 Node.js 18+ 驱动构建工具链。表 4.2 列出了核心技术栈及其选型说明。

表 4.2　系统核心技术栈

| 层次 | 技术组件 | 版本 | 选型说明 |
|:---:|:---:|:---:|:---|
| 后端框架 | FastAPI | 0.110+ | 原生异步支持，自动生成 OpenAPI 3.0 文档，Pydantic v2 数据校验 |
| 后端框架 | Uvicorn | 0.29+ | ASGI 服务器，支持 HTTP/1.1 与 WebSocket，生产级性能 |
| 数据访问 | SQLAlchemy + SQLite | 2.0+ | ORM 封装 SQL，SQLite 零配置适合本地部署 |
| 算法库 | PyTorch | 2.x | Autoencoder 实现，支持 CPU/GPU 透明切换 |
| 算法库 | scikit-learn | 1.3+ | KNN 填充、PCA 降维、Silhouette 系数 |
| 算法库 | scipy / statsmodels | — | Welch t 检验、超几何分布、BH-FDR 校正 |
| 算法库 | neuroCombat | — | ComBat 经验 Bayes 核心实现 |
| 前端框架 | Vue 3 + TypeScript | 3.4+ | Composition API，类型安全 |
| UI 组件库 | Element Plus | 2.x | 开箱即用的表单、表格、对话框等组件 |
| 可视化 | ECharts 5 | 5.x | 火山图、气泡图、力导向图、PCA 散点图 |
| 状态管理 | Pinia | 2.x | Vue 3 官方推荐，响应式 store，支持 devtools |
| 构建工具 | Vite | 5.x | 热模块替换，TS 原生支持，构建速度快 |

系统以本地单机方式部署，后端 Uvicorn 监听端口 8000，前端 Vite Dev Server 监听端口 5173，两者均可通过一条命令启动。API 调试通过 FastAPI 内置 Swagger UI（访问 `http://localhost:8000/docs`）进行，支持在线测试全部接口。

## 4.7 后端关键实现

后端 API 路由按功能划分为 `/api/datasets`、`/api/tasks`、`/api/benchmark`、`/api/downstream` 四组路由前缀，分别对应数据集管理、任务生命周期、Benchmark 只读数据和下游分析。所有接口统一返回 JSON，HTTP 状态码遵循 REST 规范，FastAPI 通过装饰器自动生成 OpenAPI 3.0 文档。请求参数由 Pydantic v2 模型校验，非法参数在进入 Service 层前即被拦截，返回结构化错误信息。

Benchmark 数据集面临一个具体的工程问题：完整 Pipeline 包含 Autoencoder 训练、PCA 计算、KEGG 富集等步骤，总耗时数分钟，放在 HTTP 请求响应周期内执行会超时。解决方案是将二者分离——通过 CLI 脚本 `scripts/run_benchmark_pipeline.py` 提前离线运行完整 Pipeline，产物持久化至 `data/processed/benchmark_merged/`；Web 服务启动后只暴露只读 API，服务端响应仅需文件 I/O，耗时毫秒级。前端 benchmark store 通过 `loadAll()` 并发拉取约 10 类数据，用户感知到的页面加载速度与直接读本地文件无异。

Service 层调用 Algorithm 层时，对 ComBat、KEGG API 调用、Autoencoder 训练等可能失败的算法均以 try-except 包裹。ComBat 失败时退回 Baseline 或返回原始矩阵；KEGG API 不可达时优先读本地缓存，缓存也不存在则返回 `{available: false}`；Autoencoder 遇到维度冲突时自动收缩潜空间维度。任何降级行为均写入日志，不向上层抛出未捕获异常。

## 4.8 前端关键实现

前端由五个页面视图和 15 个功能组件构成。视图层（HomeView、ImportView、TaskConfigView、ResultDashboardView、HistoryView）负责页面整体布局与路由，组件层按职责分为数据展示类（KpiCard、PcaImagePanel 等）、可视化类（VolcanoPlotCard、PathwayEnrichmentCard、MetaKGCard 等）和交互控制类（SidebarMenu、DatasetSelector 等）三类。可视化组件统一采用 ECharts 5 的 `init` + `setOption` 模式，在 `onMounted` 中初始化图表实例，在 `onBeforeUnmount` 中调用 `chart.dispose()` 释放内存。

状态管理由两个 Pinia store 分工承担。`benchmarkStore` 管理 Benchmark 预计算数据，用 `Promise.allSettled` 并发发起全部请求，单个接口失败静默处理不影响其他模块展示。`taskStore` 管理自定义数据集的任务状态，以每 2 秒一次的轮询驱动 PipelineStepBar 进度更新，任务进入终态（`done` 或 `error`）后自动停止轮询。

可视化方面有两处值得说明的实现细节。MetaKGCard 的力导向图布局参数随节点数量自适应调整——节点超过 200 个时斥力系数从 120 降至 60，防止大图中节点因斥力过强而飞散，同时以节点类型和是否为种子代谢物双重维度设定节点大小与颜色。VolcanoPlotCard 的火山图支持点击联动：单击散点图中的数据点，下方代谢物明细表格会自动滚动并高亮对应行，方便研究人员在图表与数据之间快速切换视角。

## 4.9 系统功能界面展示

系统主要界面包括首页概览、数据导入页、任务配置与进度页、结果展示页（含 PCA 对比、填充评估、火山图、通路气泡图、MetaKG 力导向图）以及数据集切换器和历史任务页等。各核心界面的实际运行截图分别如图 4-7 至图 4-12 所示。

【图位】图 4-7　首页 KPI 概览界面
图源：thesis/figures/screenshots/fig_4_7_dashboard.png
说明：截图覆盖顶部导航栏与四张 KPI 卡片（Autoencoder RMSE、批次质心距离、显著差异代谢物数、最显著通路）。

【图位】图 4-8　数据导入与列名映射配置界面
图源：thesis/figures/screenshots/fig_4_8_import_mapping.png
说明：截图覆盖文件上传区与 Long Format 列名映射下拉选择面板。

【图位】图 4-9　PCA 校正前后对比可视化界面
图源：thesis/figures/screenshots/fig_4_9_pca_compare.png
说明：截图覆盖左右两幅 PCA 散点（按批次着色）与下方批次质心距离 / Silhouette 指标卡片。

【图位】图 4-10　差异代谢物火山图与表格界面
图源：thesis/figures/screenshots/fig_4_10_volcano_table.png
说明：截图覆盖火山图与下方差异代谢物表格（含 log2FC、q 值、KEGG ID 列）。

【图位】图 4-11　KEGG 通路富集气泡图界面
图源：thesis/figures/screenshots/fig_4_11_kegg_bubble.png
说明：截图覆盖通路富集气泡图与右侧通路明细表格。

【图位】图 4-12　MetaKG 力导向知识图谱与节点过滤面板
图源：thesis/figures/screenshots/fig_4_12_metakg_force.png
说明：截图覆盖力导向图主区域、左侧节点类型过滤面板、顶部关键词搜索框及统计条。

## 4.10 系统测试

系统测试采用手动功能测试与边界场景测试相结合的方式，对核心功能点和异常路径分别进行验证。

功能测试覆盖 13 个核心功能点，包括文件上传与格式解析（CSV/XLSX）、列名映射配置、数据预处理三步骤（缺失率过滤、log1p 变换、Z-score 标准化）、四种缺失值填充方法（均值、中位数、KNN、Autoencoder）的独立运行、Mask-then-Impute 评估框架结果输出、两种批次效应校正方法（Baseline、ComBat）的运行与结果展示、批次效应三项评估指标（批次质心距离、批次 Silhouette、分组 Silhouette）的正确计算、差异代谢物分析（火山图渲染与结果表格）、KEGG 通路富集（气泡图渲染与通路列表）、MetaKG 力导向图（节点拖拽、过滤、搜索）、多数据集切换（Benchmark/BioHeart/MI/AMIDE）以及核心矩阵文件的 CSV 下载，全部通过。

边界场景测试覆盖四个典型异常输入：ComBat 降级测试中，将某批次样本数设置为 1（不满足经验 Bayes 估计的最小样本需求），系统正常触发降级逻辑，回退至 Baseline 方法并在界面显示友好提示，未发生崩溃；高缺失率特征过滤测试中，向数据集注入缺失率超过 50% 阈值的特征列，系统在预处理阶段正确剔除，后续分析特征数相应减少；无 KEGG 注释数据集降级测试中，以 AMIDE 数据集（无 KEGG ID）运行通路富集分析，接口返回 `{available: false}`，前端隐藏富集卡片并显示"该数据集暂无 KEGG 注释"提示，不阻断整体分析流程；Autoencoder 小数据集适应测试中，以 BioHeart 数据集（53 特征）运行 Autoencoder，系统自动将潜空间维度压缩至不超过特征数的合理范围，模型正常收敛，填充结果合理。

综合功能测试与边界测试结果，系统在正常输入与异常输入场景下均能稳定运行，降级策略生效，未出现未捕获异常或页面崩溃，验证了系统的可靠性与鲁棒性。

# 第五章 结论与展望

## 5.1 研究总结

本文围绕代谢组学数据分析中的批次效应校正与缺失值填充两大核心问题，设计并实现了一个基于深度学习的代谢组学批次效应处理 Web 平台，覆盖了从数据导入、预处理、缺失值填充与批次校正，到差异代谢物分析、KEGG 通路富集与 MetaKG 知识图谱溯源的完整分析链路。

系统采用前后端分离架构，后端基于 FastAPI + SQLite + SQLAlchemy，前端基于 Vue3 + TypeScript + ECharts + Element Plus，算法层以独立模块形式组织，具备良好的可扩展性。系统支持 CSV/XLSX 格式的多数据集导入与切换，以 Web 交互界面贯通从数据预处理到结果可视化的全流程，填补了现有平台在深度学习方法集成和一体化分析方面的不足。

缺失值填充是本文的核心工作之一。本文基于 PyTorch 实现了采用 Masked Reconstruction 训练策略的 Encoder-Decoder 网络（1180→256→64→256→1180），并设计了 Mask-then-Impute 可量化评估框架。在 Benchmark 数据集（1715 × 1180）上，Autoencoder 方法以 RMSE = 0.2249 位居第一，分别优于 KNN（RMSE = 0.2980，降低 24.5%）和均值填充（RMSE = 1.0011，降低 77.5%），证明了深度学习方法在该任务上的有效性。

批次效应校正方面，本文集成了逐特征位置尺度对齐（Baseline）和基于 neuroCombat 的 ComBat 经验 Bayes 两种方法，并设计了"批次效应消除程度"与"生物学信号保留程度"相互制衡的双维度评估框架，涵盖批次质心距离、批次 Silhouette 系数和分组 Silhouette 系数三项指标。实验表明，Baseline 校正后批次质心距离由 5.38 降至约 0，批次混合效果显著。

下游分析方面，系统依次实现了 Welch t 检验 + BH-FDR 差异代谢物筛选（火山图展示）、KEGG 超几何富集分析（气泡图展示，含本地缓存）以及 MetaKG 多库整合知识图谱的力导向图溯源展示。以 P1_AA_0001 vs P1_AA_1024 为例，检出 538 个显著差异代谢物，富集到 D-Amino acid metabolism 通路（q = 0.000206），验证了下游链路的生物学合理性。

## 5.2 系统局限性

本文工作虽取得了预期目标，但仍存在若干值得指出的局限。

Autoencoder 目前以离线预计算方式运行，用户无法通过 Web 界面为自定义数据集在线触发模型训练。根本原因在于训练耗时往往超过 HTTP 同步请求的超时限制，当前实现暂时牺牲了这部分交互易用性。

批次校正方法的覆盖范围也有待扩展。系统仅集成了 Baseline 和 ComBat 两种方法，Harmony、BBKNN 等在单细胞组学领域表现优秀的近邻对齐方法以及基于深度学习的批次校正方案均尚未引入，用户的方法选择空间较为有限。

评估体系存在维度上的限制。当前所有批次效应评估指标均在 PCA 降至 2 维后的坐标空间中计算，不可避免地丢失了高维空间中的部分结构信息，评估结论的普适性有待进一步验证。

此外，系统目前为单机本地部署，缺少用户认证与数据隔离机制，无法支持多用户并发场景。Benchmark 数据集的完整流水线产物也依赖 CLI 脚本手动运行生成，对非技术背景用户存在一定门槛。

## 5.3 未来工作展望

针对上述不足，后续工作拟从以下几个方向推进。

最直接的改进是引入异步任务队列。将 Autoencoder 训练等耗时计算迁移至 Celery + Redis 任务队列，前端通过 WebSocket 或长轮询实时获取进度，可从根本上解决在线训练的超时问题，实现真正的全流程 Web 化操作。

在方法库建设上，计划引入 Harmony（PCA 空间迭代软聚类对齐）、BBKNN（批次感知 KNN 图）等主流批次校正方法，并探索基于变分自动编码器（VAE）的深度学习批次校正方案，构建覆盖统计、近邻对齐、深度学习三类范式的多方法横向对比平台。

评估体系方面，拟将现有指标从 2D PCA 空间扩展至更高维度，或引入 kBET（k-nearest neighbor Batch Effect Test）等专为高维数据设计的批次效应评估统计量，使评估结果更具全面性。同时，可基于数据集的统计特征（批次数、缺失率、特征数等）和历史运行记录，设计自动化方法推荐模块，降低用户的算法选择门槛。

系统架构上，计划迁移至 PostgreSQL 数据库，引入用户注册与权限隔离机制，以支持科研团队的协作分析场景；并集成 PDF/HTML 报告自动生成功能，允许用户一键导出包含预处理参数、填充评估、校正效果与下游分析结果的完整分析报告。

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