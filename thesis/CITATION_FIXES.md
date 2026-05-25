# 参考文献全量引用 + 重排顺序方案

> 目标：让初稿中的 46 篇参考文献全部在正文出现，并按 GB/T 7714「顺序编码制」即"首次出现顺序"重新编号。
>
> 用法：先按 §4 的"段落替换清单"在 Word 里逐段替换正文（共 9 处段落，覆盖第 1 章的 1.1、1.2.1、1.2.2、1.2.3、1.2.4），随后用 §3 的新版参考文献列表整体替换原参考文献节。第 2 章以后不动。

---

## 1. 整体思路

- 初稿正文只引用了原编号 [1]–[18]，因此为了把 [19]–[46] 全部用上，必须**在第 1 章追加 28 处新引用**。
- 国标 GB/T 7714「顺序编码制」要求参考文献列表的编号顺序 = 正文中首次出现的顺序。因此 28 处新引用插入后，整张参考文献表都需要**重排+重新编号**。
- 为避免句子被「引用炸弹」灌爆，本方案的策略是：
  1. 第 1.1 节按"代谢组学背景 → 批次效应 → 缺失值 → 现有平台 → 深度学习 → 多组学整合"6 段递进，每段最多新增 3–5 个引用；
  2. 第 1.2.1–1.2.4 把各方向"国内外代表性工作"补齐；
  3. 中文学位论文（杨庆霞、王远山、秦家辉）作为各方向的国内代表工作出现一次。

---

## 2. 旧 → 新 编号映射（共 46 条）

下表第 1 列是初稿现状中的编号，第 3 列是按新顺序得到的目标编号；同一行代表是同一篇文献，只是位置编号变化。

| 旧编号 | 文献（首字 + 年份） | 新编号 | 首次出现章节 |
|:---:|---|:---:|---|
| [1]  | FIEHN 2002                | [1]  | 1.1 第1段 |
| [20] | PATTI 2012                | [2]  | 1.1 第1段 |
| [19] | WISHART 2019              | [3]  | 1.1 第1段 |
| [43] | 白跃花 2024                | [4]  | 1.1 第1段 |
| [2]  | WISHART 2018 HMDB 4.0     | [5]  | 1.1 第1段 |
| [25] | NANDAKUMAR 2021           | [6]  | 1.1 第1段 |
| [26] | CHEN 2022                 | [7]  | 1.1 第1段 |
| [3]  | KIND 2006                 | [8]  | 1.1 第1段 |
| [4]  | LEEK 2010                 | [9]  | 1.1 第2段 |
| [33] | HAN 2022                  | [10] | 1.1 第2段 |
| [34] | YU 2024                   | [11] | 1.1 第2段 |
| [21] | DUNN 2011                 | [12] | 1.1 第3段 |
| [5]  | LAZAR 2016                | [13] | 1.1 第3段 |
| [35] | LIU 2020                  | [14] | 1.1 第3段 |
| [6]  | WEI 2018                  | [15] | 1.1 第3段 |
| [7]  | PANG 2021 MetaboAnalyst 5 | [16] | 1.1 第4段 |
| [8]  | GONDARA 2018 MIDA         | [17] | 1.1 第5段 |
| [38] | SEN 2021                  | [18] | 1.1 第5段 |
| [39] | CHI 2024                  | [19] | 1.1 第5段 |
| [22] | SUN 2024                  | [20] | 1.1 第5段 |
| [29] | MA 2025                   | [21] | 1.1 第5段 |
| [28] | LIU 2019 WGAN             | [22] | 1.1 第5段 |
| [30] | LUO 2024                  | [23] | 1.1 新增第6段 |
| [42] | 刘晓帆 2024                | [24] | 1.1 新增第6段 |
| [24] | CHONG 2019 MetaboAnalyst4 | [25] | 1.2.1 |
| [9]  | TAUTENHAHN 2012 XCMS      | [26] | 1.2.1 |
| [23] | LI 2022 MetDIT            | [27] | 1.2.1 |
| [27] | SPICER 2017               | [28] | 1.2.1 |
| [44] | 杨庆霞 2022                | [29] | 1.2.1 |
| [46] | 秦家辉 2019                | [30] | 1.2.2 |
| [10] | TROYANSKAYA 2001 KNN      | [31] | 1.2.2 |
| [11] | QI 2012 Random Forest     | [32] | 1.2.2 |
| [41] | ABRAM 2022                | [33] | 1.2.2 |
| [12] | JOHNSON 2007 ComBat       | [34] | 1.2.3 |
| [13] | KORSUNSKY 2019 Harmony    | [35] | 1.2.3 |
| [14] | SHAHAM 2017 DM-RN         | [36] | 1.2.3 |
| [15] | LOPEZ 2018 scVI           | [37] | 1.2.3 |
| [31] | RONG 2020 NormAE          | [38] | 1.2.3 |
| [32] | DMITRENKO 2023 RALPS      | [39] | 1.2.3 |
| [36] | DENG 2019 WaveICA         | [40] | 1.2.3 |
| [37] | PELLETIER 2024            | [41] | 1.2.3 |
| [45] | 王远山 2021                | [42] | 1.2.3 |
| [16] | VAN DEN BERG 2006         | [43] | 1.2.4 |
| [17] | KANEHISA 2000 KEGG        | [44] | 1.2.4 |
| [40] | BAO 2025 MS2MP            | [45] | 1.2.4 |
| [18] | WISHART 2013 HMDB 3.0     | [46] | 1.2.4 |

---

## 3. 重排后的参考文献列表（直接替换原"参考文献"整节）

```
参考文献

[1]  FIEHN O. Metabolomics—the link between genotypes and phenotypes[J]. Plant Molecular Biology, 2002, 48(1-2): 155-171.

[2]  PATTI G J, YANES O, SIUZDAK G. Metabolomics: the apogee of the omics trilogy[J]. Nature Reviews Molecular Cell Biology, 2012, 13(4): 263-269.

[3]  WISHART D S. Metabolomics for investigating physiological and pathophysiological processes[J]. Physiological Reviews, 2019, 99(4): 1819-1875.

[4]  白跃花, 李若冰, 王莉, 等. 代谢组学：解锁生命奥秘与疾病治疗的新篇章[J]. 临床个性化医学, 2024, 3(4): 2538-2546. DOI: 10.12677/jcpm.2024.34362.

[5]  WISHART D S, FEUNANG Y D, MARCU A, et al. HMDB 4.0: the human metabolome database for 2018[J]. Nucleic Acids Research, 2018, 46(D1): D608-D617.

[6]  NANDAKUMAR P, MA J, RAMAN B, et al. Interpretable machine learning on metabolomics data reveals biomarkers for Parkinson's disease[J]. Metabolites, 2021, 11(8): 525.

[7]  CHEN H, ZHANG Z, ZHAO L, et al. Metabolomic machine learning predictor for diagnosis and prognosis of gastric cancer[J]. Frontiers in Oncology, 2022, 12: 824245.

[8]  KIND T, FIEHN O. Metabolomic database annotations via query of elemental compositions: mass accuracy is insufficient even at less than 1 ppm[J]. BMC Bioinformatics, 2006, 7: 234.

[9]  LEEK J T, SCHARPF R B, BRAVO H C, et al. Tackling the widespread and critical impact of batch effects in high-throughput data[J]. Nature Reviews Genetics, 2010, 11(10): 733-739.

[10] HAN W, LI L. Evaluating and minimizing batch effects in metabolomics[J]. Mass Spectrometry Reviews, 2022, 41(3): 421-442.

[11] YU M K, MA J, FISHER J, et al. Assessing and mitigating batch effects in large-scale omics studies[J]. Genome Biology, 2024, 25(1): 73.

[12] DUNN W B, BROADHURST D I, ATHERTON H J, et al. Systems level studies of mammalian metabolomes: the roles of mass spectrometry and nuclear magnetic resonance spectroscopy[J]. Chemical Society Reviews, 2011, 40(1): 387-426.

[13] LAZAR C, GATTO L, FERRO M, et al. Accounting for the multiple natures of missing values in label-free quantitative proteomics data sets to compare imputation strategies[J]. Journal of Proteome Research, 2016, 15(4): 1116-1125.

[14] LIU Q, ZÍDEK L, LEIMKÜHLER N I, et al. Addressing the batch effect issue for LC/MS metabolomics data in data preprocessing[J]. Scientific Reports, 2020, 10(1): 13856.

[15] WEI R, WANG J, SU M, et al. Missing value imputation approach for mass spectrometry-based metabolomics data[J]. Scientific Reports, 2018, 8(1): 663.

[16] PANG Z, CHONG J, WEEK G, et al. MetaboAnalyst 5.0: narrowing the gap between raw spectra and functional insights[J]. Nucleic Acids Research, 2021, 49(W1): W388-W396.

[17] GONDARA L, WANG K. MIDA: Multiple imputation using denoising autoencoders[C]//Proceedings of the Pacific-Asia Conference on Knowledge Discovery and Data Mining (PAKDD). New York: Springer, 2018: 260-272.

[18] SEN P, SARAFIAN M H, MATHEMA V B, et al. Deep learning meets metabolomics: a methodological perspective[J]. Briefings in Bioinformatics, 2021, 22(2): 1531-1542.

[19] CHI Y, SARAFIAN M H, BARUPAL D K, et al. Artificial intelligence in metabolomics: A current review[J]. TrAC Trends in Analytical Chemistry, 2024, 172: 117566.

[20] SUN L Q, FAN X J, ZHAO Y W, et al. Deep learning-based metabolomics data study of prostate cancer[J]. BMC Bioinformatics, 2024, 25(1): 391.

[21] MA X, SHEDLOCK C J, MEDINA T, et al. AI-driven framework to map the brain metabolome in three dimensions[J]. Nature Metabolism, 2025, 7(4): 842-853.

[22] LIU Y F, ZHOU Y, LI X, et al. Wasserstein GAN-based small-sample augmentation for new-generation artificial intelligence: a case study of cancer-staging data in biology[J]. Engineering, 2019, 5(1): 156-163.

[23] LUO Y, ZHAO C, CHEN F. Multiomics research: principles and challenges in integrated analysis[J/OL]. BioDesign Research, 2024, 6: 0059[2026-05-17]. https://doi.org/10.34133/bdr.0059. DOI: 10.34133/bdr.0059.

[24] 刘晓帆, 鲁志. 复杂疾病中多组学多模态数据的生物信息学研究进展[J]. 科学通报, 2024, 69(30): 4432-4446.

[25] CHONG J, WISHART D S, XIA J. Using MetaboAnalyst 4.0 for comprehensive and integrative metabolomics data analysis[J]. Current Protocols in Bioinformatics, 2019, 68(1): e86.

[26] TAUTENHAHN R, PATTI G J, RINEHART D, et al. XCMS Online: a web-based platform to process untargeted metabolomic data[J]. Analytical Chemistry, 2012, 84(11): 5035-5039.

[27] LI X, ZHANG Y, WANG J, et al. MetDIT: transforming and analyzing clinical metabolomics data with convolutional neural networks[J]. Bioinformatics, 2022, 38(15): 3684-3691.

[28] SPICER R, SALEK M R, MORENO P, et al. Navigating freely available software tools for metabolomics analysis[J]. Metabolomics, 2017, 13(9): 106.

[29] 杨庆霞. 代谢组学数据分析的算法研究及在线工具开发[D]. 重庆: 重庆大学, 2022.

[30] 秦家辉. 代谢组学数据清洗中的缺失值处理和变量分类方法[D]. 厦门: 厦门大学, 2019.

[31] TROYANSKAYA O, CANTOR M, SHERLOCK G, et al. Missing value estimation methods for DNA microarrays[J]. Bioinformatics, 2001, 17(6): 520-525.

[32] QI Y. Random forest for bioinformatics[M]//ZHANG C, MA Y. Ensemble Machine Learning. New York: Springer, 2012: 307-323.

[33] ABRAM K, MCCLOSKEY D. Comprehensive evaluation of metabolomics data preprocessing methods for deep learning[J]. Metabolites, 2022, 12(5): 434.

[34] JOHNSON W E, LI C, RABINOVIC A. Adjusting batch effects in microarray expression data using empirical Bayes methods[J]. Biostatistics, 2007, 8(1): 118-127.

[35] KORSUNSKY I, MILLARD N, FAN J, et al. Fast, sensitive and accurate integration of single-cell data with Harmony[J]. Nature Methods, 2019, 16(12): 1289-1296.

[36] SHAHAM U, STANTON K P, ZHAO J, et al. Removal of batch effects using distribution-matching residual networks[J]. Bioinformatics, 2017, 33(16): 2539-2546.

[37] LOPEZ R, REGIER J, COLE M B, et al. Deep generative modeling for single-cell transcriptomics[J]. Nature Methods, 2018, 15(12): 1053-1058.

[38] RONG Z, MIN H, WANG S, et al. NormAE: Deep adversarial learning model to remove batch effects in liquid chromatography mass spectrometry-based metabolomics data[J]. Analytical Chemistry, 2020, 92(7): 5082-5090.

[39] DMITRENKO A, KUNATH B J, POPE P B, et al. RALPS: Regularized adversarial learning preserving similarities for metabolomics batch correction[J]. Bioinformatics, 2023, 39(1): btac786.

[40] DENG K, ZHANG F, TAN Q, et al. WaveICA: A novel algorithm to remove batch effects for large-scale untargeted metabolomics data based on wavelet analysis[J]. Analytica Chimica Acta, 2019, 1061: 60-69.

[41] PELLETIER A R, BHATT D L, DREYFUSS J M, et al. Correcting for batch effects in metabolomics data by leveraging a pooled reference sample[J]. Nature Communications, 2024, 15(1): 1-14.

[42] 王远山. 质谱代谢组学数据预处理中的缺失值填补和批次效应校正方法[D]. 厦门: 厦门大学, 2021.

[43] VAN DEN BERG R A, HOEFSLOOT H C, WESTERHUIS J A, et al. Centering, scaling, and transformations: improving the biological information content of metabolomics data[J]. BMC Genomics, 2006, 7: 142.

[44] KANEHISA M, GOTO S. KEGG: Kyoto encyclopedia of genes and genomes[J]. Nucleic Acids Research, 2000, 28(1): 27-30.

[45] BAO Q L, CHENG Y, ZHAO C X, et al. MS2MP: predicting KEGG metabolic pathways from tandem mass spectra via deep learning[J]. Analytical Chemistry, 2025, 97(5): 2800-2809.

[46] WISHART D S, JEWISON T, GUO A C, et al. HMDB 3.0—the human metabolome database in 2013[J]. Nucleic Acids Research, 2013, 41(D1): D801-D807.
```

---

## 4. 正文段落替换清单（共 9 处）

### 替换 1：1.1 第 1 段

**【原文】**

> 代谢组学（Metabolomics）是继基因组学、转录组学和蛋白质组学之后发展起来的重要研究领域。其核心思想是通过质谱（Mass Spectrometry，MS）或核磁共振（Nuclear Magnetic Resonance，NMR）等高通量检测技术，对生物体内全部或部分小分子代谢物（分子量通常小于 1500 Da）进行系统性定量检测，进而从代谢层面揭示生物体在不同生理状态、病理条件或外界干预下的整体响应规律[1]。与基因组和蛋白质组相比，代谢物是生命活动的直接产物，能够更加灵敏地反映生物体当前的功能状态，因此代谢组学在疾病早期诊断与生物标志物发现[2]、药物靶点识别[3]、营养干预评估等领域已展现出重要的应用价值。

**【修改后】**

> 代谢组学（Metabolomics）是继基因组学、转录组学和蛋白质组学之后发展起来的重要研究领域[1]，被视为多组学研究"基因→转录→蛋白→代谢"链条的下游汇聚层，在临床诊断与生理机制研究中具有不可替代的作用[2,3]。其核心思想是通过质谱（Mass Spectrometry，MS）或核磁共振（Nuclear Magnetic Resonance，NMR）等高通量检测技术，对生物体内全部或部分小分子代谢物（分子量通常小于 1500 Da）进行系统性定量检测，进而从代谢层面揭示生物体在不同生理状态、病理条件或外界干预下的整体响应规律[4]。与基因组和蛋白质组相比，代谢物是生命活动的直接产物，能够更加灵敏地反映生物体当前的功能状态，因此代谢组学在疾病早期诊断与生物标志物发现[5]方面应用广泛，已有研究将其应用于帕金森病[6]、胃癌[7]等疾病的早期筛查与预后评估，并在药物靶点识别[8]、营养干预评估等领域展现出重要的应用价值。

> 修改要点：把"代谢组学定义"句末 [1] 改为 [1]+[2,3]+[4]，并在生物标志物示例后补 [6][7] 作为典型应用支撑。

---

### 替换 2：1.1 第 2 段

**【原文】**

> 然而，随着代谢组学研究规模的持续扩大，大量样本往往需要在不同时间段分批完成检测，由此引入了代谢组学数据分析中的核心技术挑战之一——批次效应（Batch Effect）。批次效应是指由仪器状态波动、环境温湿度变化、试剂批次差异、操作人员变化等非生物学因素所造成的系统性偏差，其典型表现为：同一生物条件的样本在不同批次中检测到的信号强度呈现出明显的系统性偏移，而这种偏移与样本本身的生物学状态无关[4]。在主成分分析（PCA）等降维可视化手段下，批次效应通常表现为不同批次样本聚集成相互分离的簇群，掩盖了真实的生物学差异，严重干扰后续差异代谢物筛选和通路分析结果的可靠性。

**【修改后】**

> 然而，随着代谢组学研究规模的持续扩大，大量样本往往需要在不同时间段分批完成检测，由此引入了代谢组学数据分析中的核心技术挑战之一——批次效应（Batch Effect）。批次效应是指由仪器状态波动、环境温湿度变化、试剂批次差异、操作人员变化等非生物学因素所造成的系统性偏差，其典型表现为：同一生物条件的样本在不同批次中检测到的信号强度呈现出明显的系统性偏移，而这种偏移与样本本身的生物学状态无关[9]。Han 与 Li 对代谢组学批次效应的评估与最小化策略进行了系统综述[10]，Yu 等亦对大规模 omics 研究中的批次效应进行了全面梳理，强调了其在跨批次合并分析中的普遍性与危害[11]。在主成分分析（PCA）等降维可视化手段下，批次效应通常表现为不同批次样本聚集成相互分离的簇群，掩盖了真实的生物学差异，严重干扰后续差异代谢物筛选和通路分析结果的可靠性。

> 修改要点：[4] → [9]；在 PCA 描述前补一句综述支撑，引入 [10][11]。

---

### 替换 3：1.1 第 3 段

**【原文】**

> 与批次效应并列的另一个重要问题是缺失值（Missing Values）的处理。液相色谱-质谱联用（LC-MS）技术在低丰度代谢物的检测中存在仪器灵敏度限制，当代谢物浓度低于检测限（Limit of Detection，LOD）时，相应数据点将以缺失值形式出现在数据矩阵中[5]。此外，谱峰拾取算法的误差、质量控制样本的处理差异等因素也会进一步加剧缺失值问题。在典型的大规模代谢组学数据集中，缺失值比例可达 20%～50%，若直接参与统计分析，将导致估计偏差加剧、差异检验功效下降，进而影响生物学结论的可靠性[6]。

**【修改后】**

> 与批次效应并列的另一个重要问题是缺失值（Missing Values）的处理。液相色谱-质谱联用（LC-MS）与核磁共振是当前代谢组学数据采集的两类主流技术[12]，其中 LC-MS 在低丰度代谢物的检测中存在仪器灵敏度限制，当代谢物浓度低于检测限（Limit of Detection，LOD）时，相应数据点将以缺失值形式出现在数据矩阵中[13]。此外，谱峰拾取算法的误差、质量控制样本的处理差异、以及多批次采集中的信号漂移等因素也会进一步加剧缺失值与质量波动问题[14]。在典型的大规模代谢组学数据集中，缺失值比例可达 20%～50%，若直接参与统计分析，将导致估计偏差加剧、差异检验功效下降，进而影响生物学结论的可靠性[15]。

> 修改要点：[5] → [13]、[6] → [15]；在 LC-MS 处补 [12]，在质控/批次漂移处补 [14]。

---

### 替换 4：1.1 第 4 段

**【原文】**

> 面对上述两类问题，现有的主流代谢组学分析平台（如 MetaboAnalyst[7]）虽然提供了较为完整的数据分析功能，但仍存在以下局限：在批次效应校正方法上，多数平台以 ComBat 等统计方法为主，缺乏深度学习类方法的集成……

**【修改后】**

> 面对上述两类问题，现有的主流代谢组学分析平台（如 MetaboAnalyst[16]）虽然提供了较为完整的数据分析功能，但仍存在以下局限：在批次效应校正方法上，多数平台以 ComBat 等统计方法为主，缺乏深度学习类方法的集成……（其余不变）

> 修改要点：仅把 [7] 改为 [16]。

---

### 替换 5：1.1 第 5 段（并在末尾新增第 6 段）

**【原文】**

> 随着深度学习技术的快速发展，将神经网络方法引入代谢组学数据处理已成为近年来的研究热点。研究表明，基于 Autoencoder 的深度学习模型能够有效捕获高维代谢组学数据中特征间的复杂相关结构，在缺失值填充和特征表示学习等任务上展现出优于传统统计方法的潜力[8]。

**【修改后】**

> 随着深度学习技术的快速发展，将神经网络方法引入代谢组学数据处理已成为近年来的研究热点。研究表明，基于 Autoencoder 的深度学习模型能够有效捕获高维代谢组学数据中特征间的复杂相关结构，在缺失值填充和特征表示学习等任务上展现出优于传统统计方法的潜力[17]。Sen 等人从方法论角度对深度学习在代谢组学中的整体应用进行了系统梳理[18]，Chi 等人则进一步综述了人工智能技术在代谢组学全流程中的最新进展[19]。在具体应用层面，已有研究将深度学习方法应用于前列腺癌代谢组学分类[20]、脑代谢三维成像[21]等场景，针对样本量受限的问题，Liu 等还提出基于 Wasserstein GAN 的小样本数据增强策略[22]，证实了深度学习方法在复杂代谢数据上的应用价值。
>
> 在更宏观的多组学整合背景下，代谢组学还被视为连接基因型与表型的关键层。Luo 等人系统讨论了多组学研究的核心原则与整合分析的工程挑战[23]，刘晓帆与鲁志亦从复杂疾病角度梳理了多组学多模态数据的生物信息学研究进展[24]，为本文将代谢组学分析平台延伸至多组学整合奠定了背景基础。

> 修改要点：[8] → [17]；句末追加深度学习相关引用 [18]–[22]；在 1.1 末尾**新增独立一段**作为"多组学整合背景"，引入 [23][24]，使后续 1.3 节"本文工作"对一体化平台的强调更自然。

---

### 替换 6：1.2.1 代谢组学数据分析平台研究现状

**【原文】**（共 2 段）

> 在代谢组学数据分析平台方面，MetaboAnalyst 是目前应用最广泛的在线分析平台之一。该平台支持数据归一化、缺失值填充、PCA、差异分析和通路分析，提供 Web 界面，是目前引用量最高的代谢组学分析工具之一。Pang 等人在 MetaboAnalyst 5.0 中进一步增加了多组学整合分析和代谢物注释功能，显著扩展了平台的应用范围。此外，XCMS Online[9] 提供了从原始质谱数据处理到统计分析的一体化流程，Metaboscape 等商业软件也在代谢物鉴定和批次校正方面有所集成。
>
> 然而，上述平台在批次效应方法覆盖、深度学习集成与全流程一体化支持方面均存在明显不足，具体分析见第 2.5 节。

**【修改后】**

> 在代谢组学数据分析平台方面，MetaboAnalyst 是目前应用最广泛的在线分析平台之一。Chong 等人在 MetaboAnalyst 4.0 中给出了较为完整的综合分析协议[25]，Pang 等人随后在 MetaboAnalyst 5.0 中进一步增加了多组学整合分析和代谢物注释功能，显著扩展了平台的应用范围。此外，XCMS Online[26] 提供了从原始质谱数据处理到统计分析的一体化流程；Li 等人提出的 MetDIT 平台则尝试将卷积神经网络引入临床代谢组学数据的特征转换与分析[27]；Spicer 等对当时可免费获取的代谢组学分析工具生态进行了较为系统的梳理[28]；Metaboscape 等商业软件也在代谢物鉴定和批次校正方面有所集成。国内方面，杨庆霞针对代谢组学数据分析算法与在线工具的开发进行了较为系统的探索[29]，为本文的平台设计提供了重要参照。
>
> 然而，上述平台在批次效应方法覆盖、深度学习集成与全流程一体化支持方面均存在明显不足，具体分析见第 2.5 节。

> 修改要点：把原段落里的 [9] 改为 [26]（XCMS），新增 [25]（CHONG MetaboAnalyst 4.0）、[27]（MetDIT）、[28]（Spicer）、[29]（杨庆霞）共 5 处，引用顺序与正文出现顺序保持一致。

---

### 替换 7：1.2.2 缺失值填充方法研究现状

**【原文】**（共 4 段）

> 代谢组学缺失值填充方法大致可分为简单统计填充、基于近邻的填充与基于深度学习的填充三大类，其复杂度与精度依次递增。
>
> 简单统计填充方法以均值填充（Mean Imputation）和中位数填充（Median Imputation）为代表，直接将特征的统计量赋予缺失位置。该类方法实现简单、运行高效，但忽略了样本间的相关结构，可能引入系统性偏差，在缺失值比例较高时表现较差。
>
> 基于近邻的填充方法以 K 近邻填充（K-Nearest Neighbor，KNN）为代表，利用与待填充样本最相似的 K 个样本的特征值加权估计缺失位置。该类方法能够在一定程度上利用样本间的相似结构，在代谢组学领域被广泛采用，但计算复杂度较高，且对高缺失率场景的效果受限[10]。
>
> 基于深度学习的填充方法近年来发展迅速。Gondara 和 Wang 于 2018 年提出了基于去噪自动编码器（Denoising Autoencoder）的多重填充方法 MIDA（Multiple Imputation using Denoising Autoencoders），通过向输入数据添加噪声并训练网络重建原始信号，使模型能够从整体数据分布中学习特征间的复杂依赖关系，从而对缺失位置进行更准确的估计。相关研究表明，在特征间具有复杂相关结构的高维数据场景下，深度学习方法通常优于传统统计方法[11]。

**【修改后】**

> 代谢组学缺失值填充方法大致可分为简单统计填充、基于近邻的填充与基于深度学习的填充三大类，其复杂度与精度依次递增。国内学者秦家辉对代谢组学数据清洗中的缺失值处理与变量分类方法进行了系统研究[30]，为本文方法分类的整理提供了参考。
>
> 简单统计填充方法以均值填充（Mean Imputation）和中位数填充（Median Imputation）为代表，直接将特征的统计量赋予缺失位置。该类方法实现简单、运行高效，但忽略了样本间的相关结构，可能引入系统性偏差，在缺失值比例较高时表现较差。
>
> 基于近邻的填充方法以 K 近邻填充（K-Nearest Neighbor，KNN）为代表，利用与待填充样本最相似的 K 个样本的特征值加权估计缺失位置。该类方法能够在一定程度上利用样本间的相似结构，在代谢组学领域被广泛采用，但计算复杂度较高，且对高缺失率场景的效果受限[31]。
>
> 基于深度学习的填充方法近年来发展迅速。Gondara 和 Wang 于 2018 年提出了基于去噪自动编码器（Denoising Autoencoder）的多重填充方法 MIDA（Multiple Imputation using Denoising Autoencoders），通过向输入数据添加噪声并训练网络重建原始信号，使模型能够从整体数据分布中学习特征间的复杂依赖关系，从而对缺失位置进行更准确的估计。相关研究表明，在特征间具有复杂相关结构的高维数据场景下，基于集成学习与深度学习的非线性方法通常优于传统统计方法[32]；Abram 与 McCloskey 也对面向深度学习的代谢组学预处理方法进行了较为全面的评估，进一步证实了深度学习方法在该类数据上的潜力[33]。

> 修改要点：第 1 段末新增 [30]（秦家辉，作为首个出现的国内方法学研究）；[10]（KNN）→ [31]；[11]（QI 随机森林）→ [32]；末尾补 [33]（ABRAM）。引用顺序与正文出现顺序保持一致。

---

### 替换 8：1.2.3 批次效应校正方法研究现状

**【原文】**（共 4 段）

> 批次效应校正方法的研究已有较长历史，早期工作以 ComBat 为代表，近年来随着单细胞组学的兴起，Harmony 等基于低维对齐的方法也逐渐被引入代谢组学场景。
>
> 其中，基于统计模型的方法以 ComBat 最具影响力，由 Johnson 等人于 2007 年提出。该方法将特征表达值建模为全局均值、生物学效应与批次效应之和……并可传入生物学协变量以保护真实的生物学差异不被消除[12]。此后，ComBat 被广泛应用于转录组学、蛋白质组学和代谢组学领域。与 ComBat 同属统计范式的逐特征位置尺度归一化（Per-feature Location-Scale Normalization）则进一步简化了模型假设……具有良好的可解释性。
>
> 基于低维对齐的方法以 Harmony 算法为代表，由 Korsunsky 等人于 2019 年提出，最初用于单细胞 RNA 测序数据的批次效应校正[13]。该方法在低维嵌入空间（如 PCA 空间）中通过迭代寻找跨批次的相似邻居关系并进行分布对齐，避免了对原始高维空间的直接操作，在多批次多样本场景下表现良好。
>
> 基于深度学习的方法是近年来的研究热点。Shaham 等人提出利用对抗神经网络（Adversarial Neural Network）学习批次不变的数据表示，在对数据结构依赖较弱的场景下取得了较好效果[14]。此外，也有研究探索使用变分自动编码器（Variational Autoencoder，VAE）同时完成批次效应校正与缺失值填充，在统一框架下减少分步处理带来的误差传播[15]。

**【修改后】**

> 批次效应校正方法的研究已有较长历史，早期工作以 ComBat 为代表，近年来随着单细胞组学的兴起，Harmony 等基于低维对齐的方法也逐渐被引入代谢组学场景。
>
> 其中，基于统计模型的方法以 ComBat 最具影响力，由 Johnson 等人于 2007 年提出。该方法将特征表达值建模为全局均值、生物学效应与批次效应之和……并可传入生物学协变量以保护真实的生物学差异不被消除[34]。此后，ComBat 被广泛应用于转录组学、蛋白质组学和代谢组学领域。与 ComBat 同属统计范式的逐特征位置尺度归一化（Per-feature Location-Scale Normalization）则进一步简化了模型假设……具有良好的可解释性。
>
> 基于低维对齐的方法以 Harmony 算法为代表，由 Korsunsky 等人于 2019 年提出，最初用于单细胞 RNA 测序数据的批次效应校正[35]。该方法在低维嵌入空间（如 PCA 空间）中通过迭代寻找跨批次的相似邻居关系并进行分布对齐，避免了对原始高维空间的直接操作，在多批次多样本场景下表现良好。
>
> 基于深度学习的方法是近年来的研究热点。Shaham 等人提出利用对抗神经网络（Adversarial Neural Network）学习批次不变的数据表示，在对数据结构依赖较弱的场景下取得了较好效果[36]。Lopez 等人提出的 scVI 进一步使用变分自动编码器（Variational Autoencoder，VAE）同时完成批次效应校正与缺失值填充，在统一框架下减少分步处理带来的误差传播[37]。围绕代谢组学场景，Rong 等人提出的 NormAE 通过对抗学习专门面向 LC-MS 代谢组学数据进行批次效应去除[38]，Dmitrenko 等人在此基础上提出的 RALPS 通过加入相似性保持的正则化进一步改善了生物学结构保留[39]。除上述对抗 / 生成式深度方法外，Deng 等人提出的 WaveICA 借助小波分析在大规模非靶向代谢组学数据上去除批次效应[40]，Pelletier 等人则提出基于汇集参考样本的校正策略[41]，丰富了非深度方法范式。国内方面，王远山围绕质谱代谢组学预处理中的缺失值填补与批次效应校正问题进行了系统的方法研究[42]，对本文将填充与批次校正两类问题统一在同一平台中处理具有重要启发。

> 修改要点：[12] → [34]、[13] → [35]、[14] → [36]、[15] → [37]；第 4 段末追加 NormAE/RALPS/WaveICA/Pelletier/王远山 共 5 篇 ([38]–[42])。

---

### 替换 9：1.2.4 代谢组学下游分析研究现状

**【原文】**（共 4 段）

> 批次校正后的分析通常沿三条路径展开：筛选差异代谢物、将其映射到代谢通路、再借助知识图谱追溯其与酶/疾病/反应的关联。
>
> 差异代谢物分析的常用方法包括独立样本 t 检验、方差分析（ANOVA）及其非参数等价方法，并配合 Benjamini-Hochberg 假阳性率控制（BH-FDR）进行多重检验校正，以 log2 Fold Change 衡量差异方向和大小[16]。
>
> 代谢通路富集分析基于 KEGG（Kyoto Encyclopedia of Genes and Genomes）等数据库，通过超几何检验或 Fisher 精确检验判断差异代谢物是否显著富集于特定代谢通路，从而在通路层面解释差异代谢物的生物学意义[17]。
>
> 知识图谱辅助解读则是近年来兴起的研究方向。通过整合 KEGG、HMDB（Human Metabolome Database）、SMPDB（Small Molecule Pathway Database）等多源数据库，构建代谢物-通路-反应-酶-疾病关联网络，能够为差异代谢物提供可追溯的关联证据链[18]。

**【修改后】**

> 批次校正后的分析通常沿三条路径展开：筛选差异代谢物、将其映射到代谢通路、再借助知识图谱追溯其与酶/疾病/反应的关联。
>
> 差异代谢物分析的常用方法包括独立样本 t 检验、方差分析（ANOVA）及其非参数等价方法，并配合 Benjamini-Hochberg 假阳性率控制（BH-FDR）进行多重检验校正，以 log2 Fold Change 衡量差异方向和大小[43]。
>
> 代谢通路富集分析基于 KEGG（Kyoto Encyclopedia of Genes and Genomes）等数据库[44]，通过超几何检验或 Fisher 精确检验判断差异代谢物是否显著富集于特定代谢通路，从而在通路层面解释差异代谢物的生物学意义。近年来亦有工作尝试用深度学习直接从串联质谱数据预测 KEGG 通路归属，进一步丰富了通路层面的分析范式[45]。
>
> 知识图谱辅助解读则是近年来兴起的研究方向。通过整合 KEGG、HMDB（Human Metabolome Database）、SMPDB（Small Molecule Pathway Database）等多源数据库，构建代谢物-通路-反应-酶-疾病关联网络，能够为差异代谢物提供可追溯的关联证据链[46]。

> 修改要点：[16] → [43]、[17] → [44]、[18] → [46]；在通路富集段末追加 [45]（BAO 2025 深度学习 + KEGG）。

---

## 5. 第 2 章以后无需改动

第 2 章及之后章节没有引用任何新文献，原文也未携带文中引用编号（只是综述/算法/工程描述），因此**不需要任何引用层面的改动**——本次重排只涉及第 1 章和参考文献节本身。

如果你担心第 2 章"完全没有外部引用"显得单薄，最经济的做法是：在 2.2.2 末尾、2.3.1 ComBat 介绍处、2.3.2 Harmony 介绍处，把"Johnson 等人于 2007 年"、"Korsunsky 等，2019"、"Gondara 和 Wang（2018）"、"Lopez 等（2018）"、"Shaham 等（2017）"这些已经出现的人名引用补一个 [34]/[35]/[17]/[37]/[36] 角标即可——这是可选项，不做也合规（同一篇文献的引用编号在全文是统一的，第一次出现已经登记，后续可以省略）。

---

## 6. 顺序校验（按正文首次出现顺序）

为方便检查，下面把第 1 章正文中每个引用第一次出现的位置依次列出，确认编号是单调递增的：

| 序 | 出现位置 | 编号 | 文献 |
|:---:|---|:---:|---|
| 1  | 1.1 第1段 | [1]  | FIEHN 2002 |
| 2  | 1.1 第1段 | [2]  | PATTI 2012 |
| 3  | 1.1 第1段 | [3]  | WISHART 2019 |
| 4  | 1.1 第1段 | [4]  | 白跃花 2024 |
| 5  | 1.1 第1段 | [5]  | WISHART 2018 HMDB 4.0 |
| 6  | 1.1 第1段 | [6]  | NANDAKUMAR 2021 |
| 7  | 1.1 第1段 | [7]  | CHEN 2022 |
| 8  | 1.1 第1段 | [8]  | KIND 2006 |
| 9  | 1.1 第2段 | [9]  | LEEK 2010 |
| 10 | 1.1 第2段 | [10] | HAN 2022 |
| 11 | 1.1 第2段 | [11] | YU 2024 |
| 12 | 1.1 第3段 | [12] | DUNN 2011 |
| 13 | 1.1 第3段 | [13] | LAZAR 2016 |
| 14 | 1.1 第3段 | [14] | LIU 2020 |
| 15 | 1.1 第3段 | [15] | WEI 2018 |
| 16 | 1.1 第4段 | [16] | PANG 2021 MetaboAnalyst 5 |
| 17 | 1.1 第5段 | [17] | GONDARA 2018 MIDA |
| 18 | 1.1 第5段 | [18] | SEN 2021 |
| 19 | 1.1 第5段 | [19] | CHI 2024 |
| 20 | 1.1 第5段 | [20] | SUN 2024 |
| 21 | 1.1 第5段 | [21] | MA 2025 |
| 22 | 1.1 第5段 | [22] | LIU 2019 WGAN |
| 23 | 1.1 新增第6段 | [23] | LUO 2024 |
| 24 | 1.1 新增第6段 | [24] | 刘晓帆 2024 |
| 25 | 1.2.1     | [25] | CHONG 2019 MetaboAnalyst 4 |
| 26 | 1.2.1     | [26] | TAUTENHAHN 2012 XCMS |
| 27 | 1.2.1     | [27] | LI 2022 MetDIT |
| 28 | 1.2.1     | [28] | SPICER 2017 |
| 29 | 1.2.1     | [29] | 杨庆霞 2022 |
| 30 | 1.2.2 第1段 | [30] | 秦家辉 2019 |
| 31 | 1.2.2 第3段 | [31] | TROYANSKAYA 2001 KNN |
| 32 | 1.2.2 第4段 | [32] | QI 2012 Random Forest |
| 33 | 1.2.2 第4段 | [33] | ABRAM 2022 |
| 34 | 1.2.3 第2段 | [34] | JOHNSON 2007 ComBat |
| 35 | 1.2.3 第3段 | [35] | KORSUNSKY 2019 Harmony |
| 36 | 1.2.3 第4段 | [36] | SHAHAM 2017 DM-RN |
| 37 | 1.2.3 第4段 | [37] | LOPEZ 2018 scVI |
| 38 | 1.2.3 第4段 | [38] | RONG 2020 NormAE |
| 39 | 1.2.3 第4段 | [39] | DMITRENKO 2023 RALPS |
| 40 | 1.2.3 第4段 | [40] | DENG 2019 WaveICA |
| 41 | 1.2.3 第4段 | [41] | PELLETIER 2024 |
| 42 | 1.2.3 第4段 | [42] | 王远山 2021 |
| 43 | 1.2.4 第2段 | [43] | VAN DEN BERG 2006 |
| 44 | 1.2.4 第3段 | [44] | KANEHISA 2000 KEGG |
| 45 | 1.2.4 第3段 | [45] | BAO 2025 MS2MP |
| 46 | 1.2.4 第4段 | [46] | WISHART 2013 HMDB 3.0 |

全部 46 篇文献编号单调递增，符合 GB/T 7714 顺序编码制要求。

---

## 7. 一句话总结

- **9 处段落替换** + **整张参考文献表替换** = 把 46 篇全部用上 + 顺序合规；
- 18 篇老引用的编号会改变，但语义位置不变；
- 28 篇新引用都以"自然衔接句"形式插入到 1.1 / 1.2.x 现有段落中，未生造章节，不破坏论文整体结构。
