#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Benchmark 数据集统计与汇总

"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class BenchmarkDataProcessor:
    
    def __init__(self, data_dir='data/raw/benchmark', output_dir='data/processed_benchmark'):
        self.data_dir = data_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.batch_files = [
            "Batch1_0108 DATA.xlsx",
            "Batch2_0110 DATA.xlsx",
            "Batch3_0124 DATA.xlsx",
            "Batch4_0219 DATA.xlsx",
            "Batch5_0221 DATA.xlsx",
            "Batch6_0304 DATA.xlsx",
            "Batch7_0306 DATA.xlsx"
        ]
        
        self.df_merged = None
        self.quality_report = {}
        
    def load_single_batch(self, batch_file):
        print(f"  正在加载: {batch_file}") 
        # 读取 Excel，跳过前2列，然后转置
        file_path = os.path.join(self.data_dir, batch_file)
        df = pd.read_excel(file_path, sheet_name='intensities')
        intensities = df.iloc[:, 2:].transpose()
        # 提取样本信息
        sample_indices = intensities.index
        # 解析样本名称：从 "008 / P1_AA_0256" 提取 "P1_AA_0256"
        sample_names = []
        sample_labels = []
        
        for idx in sample_indices:
            parts = str(idx).split(" / ")
            if len(parts) >= 2:
                full_name = parts[1]
                sample_names.append(full_name)
                
                # 提取标签：从 "P1_AA_0256" 提取 "AA"
                label_parts = full_name.split("_")
                if len(label_parts) >= 2:
                    sample_labels.append(label_parts[1])
                else:
                    sample_labels.append("Unknown")
            else:
                sample_names.append(str(idx))
                sample_labels.append("Unknown")
        
        # 移除 burnin 和 water 样本
        valid_indices = [
            i for i, name in enumerate(sample_names)
            if 'burnin' not in name.lower() and 'water' not in name.lower()
        ]

        intensities = intensities.iloc[valid_indices]
        sample_names = [sample_names[i] for i in valid_indices]
        sample_labels = [sample_labels[i] for i in valid_indices]
        # 为样本名称添加递增编号
        numbered_names = [f"{str(i+1).zfill(2)}_{name}" for i, name in enumerate(sample_names)]
        # 添加元数据列
        intensities['names'] = numbered_names  
        intensities['original_names'] = sample_names 
        intensities['label'] = sample_labels
        intensities['batch'] = batch_file
        intensities['batch_id'] = int(batch_file.split('Batch')[1][0])

        # 重新排列列顺序：names, original_names, label, batch, batch_id, features...
        meta_cols = ['names', 'original_names', 'label', 'batch', 'batch_id']
        feature_cols = [col for col in intensities.columns if col not in meta_cols]
        intensities = intensities[meta_cols + feature_cols]
       
        print(f"    样本数: {len(intensities)}, 特征数: {len(feature_cols)}")
        
        return intensities
    
    def merge_all_batches(self):
        print("1: 加载和整合批次数据")
        batch_dataframes = []
        
        for batch_file in self.batch_files:
            df_batch = self.load_single_batch(batch_file)
            batch_dataframes.append(df_batch)
        
        # 1. 找到所有批次共有的特征（代谢物）
        meta_cols = ['names', 'original_names', 'label', 'batch', 'batch_id']

        # 获取每个批次的特征列
        feature_sets = []
        for df in batch_dataframes:
            features = set([col for col in df.columns if col not in meta_cols])
            feature_sets.append(features)

        # 计算交集：所有批次共有的特征
        common_features = feature_sets[0]
        for feature_set in feature_sets[1:]:
            common_features = common_features.intersection(feature_set)

        common_features = sorted(list(common_features))

        print(f"\n 特征筛选:")
        print(f"  各批次原始特征数: {[len(fs) for fs in feature_sets]}")
        print(f"  共有特征数: {len(common_features)}")

        # 2. 只保留共有特征进行合并
        filtered_dataframes = []
        for df in batch_dataframes:
            df_filtered = df[meta_cols + common_features]
            filtered_dataframes.append(df_filtered)

        # 3. 合并所有批次
        self.df_merged = pd.concat(filtered_dataframes, axis=0, ignore_index=True)
        
        # 4. 重新生成全局唯一的 names 列
        self.df_merged['names'] = [f"{str(i+1).zfill(4)}_Batch{row['batch_id']}_{row['original_names']}" 
                                    for i, (idx, row) in enumerate(self.df_merged.iterrows())]
        
        print(f"\n 样本编号重新生成:")
        print(f"  使用格式: XXXX_BatchY_OriginalName")

        # 5. 添加 type 列：识别样本类型
        print(f"\n 样本类型识别:")
        # 统计每个原始样本名称的出现情况
        sample_counts = self.df_merged.groupby('original_names').agg({
            'batch_id': lambda x: list(x),
            'names': 'count'
        })
        sample_counts.columns = ['batches', 'count']

        # 初始化 type 列
        self.df_merged['type'] = 'S'  # 默认为单一样本

        # 识别 SR (同批次重复)
        for orig_name, row in sample_counts.iterrows():
            batches = row['batches']
            count = row['count']
            
            if count > 1:
                # 检查是否有同批次重复
                batch_counter = {}
                for batch in batches:
                    batch_counter[batch] = batch_counter.get(batch, 0) + 1
                
                has_within_batch_rep = any(c > 1 for c in batch_counter.values())
                has_cross_batch_rep = len(set(batches)) > 1
                
                mask = self.df_merged['original_names'] == orig_name
                
                if has_within_batch_rep and has_cross_batch_rep:
                    # 既有同批次重复，又有跨批次重复
                    self.df_merged.loc[mask, 'type'] = 'BR+SR'
                elif has_cross_batch_rep:
                    # 仅跨批次重复
                    self.df_merged.loc[mask, 'type'] = 'BR'
                elif has_within_batch_rep:
                    # 仅同批次重复
                    self.df_merged.loc[mask, 'type'] = 'SR'

        type_counts = self.df_merged['type'].value_counts()
        print(f"  S (单一样本): {type_counts.get('S', 0)}")
        print(f"  SR (同批次重复): {type_counts.get('SR', 0)}")
        print(f"  BR (跨批次重复): {type_counts.get('BR', 0)}")
        print(f"  BR+SR (同时有跨批次和批次内重复): {type_counts.get('BR+SR', 0)}")

        # 5. 重新排列列顺序：names, original_names, label, batch, batch_id, type, features...
        meta_cols_final = ['names', 'original_names', 'label', 'batch', 'batch_id', 'type']
        self.df_merged = self.df_merged[meta_cols_final + common_features]
 
        print(f"\n数据整合完成:")
        print(f"  总样本数: {len(self.df_merged)}")
        print(f"  总特征数: {len(common_features)}")
        print(f"  批次数: {self.df_merged['batch_id'].nunique()}")
        
        return self.df_merged
        
    def quality_control(self):
        """数据质量控制和统计"""
        print("\n2: 数据质量控制")
        feature_cols = [col for col in self.df_merged.columns if col not in ['names', 'original_names', 'label', 'batch', 'batch_id', 'type']]
        feature_data = self.df_merged[feature_cols]   
        # 1. 缺失值统计
        missing_rate = feature_data.isnull().sum().sum() / (feature_data.shape[0] * feature_data.shape[1])
        print(f"\n缺失值率: {missing_rate:.2%}")
        # 2. 零值统计
        zero_rate = (feature_data == 0).sum().sum() / (feature_data.shape[0] * feature_data.shape[1])
        print(f"零值率: {zero_rate:.2%}")
        # 3. 样本标签分布
        print(f"样本标签分布:")
        label_counts = self.df_merged['label'].value_counts()
        for label, count in label_counts.items():
            print(f"   {label}: {count} 样本")
        # 4. 每个批次的样本数
        print(f"每个批次的样本数:")
        batch_counts = self.df_merged['batch_id'].value_counts().sort_index()
        for batch, count in batch_counts.items():
            print(f"   Batch {batch}: {count} 样本")
        # 5. 技术重复检查
        print(f"技术重复分析:")
        name_counts = self.df_merged['original_names'].value_counts()
        replicate_stats = name_counts.value_counts().sort_index()
        print(f"重复次数分布:")
        for rep_count, freq in replicate_stats.items():
            print(f"     {rep_count}次重复: {freq} 个样本")
        # 6. 跨批次样本分析
        print(f"跨批次样本分析:")
        sample_batch_spread = self.df_merged.groupby('original_names')['batch_id'].nunique()
        spread_dist = sample_batch_spread.value_counts().sort_index()
        print(f"样本批次覆盖分布:")
        for n_batches, count in spread_dist.items():
            print(f"     出现在 {n_batches} 个批次: {count} 个独特样本")       
        # 保存质量报告
        self.quality_report = {
            '缺失率': missing_rate,
            '零值率': zero_rate,
            '样本标签分布': label_counts.to_dict(),
            '每个批次的样本数': batch_counts.to_dict(),
            '技术重复分析': replicate_stats.to_dict(),
            '样本批次覆盖分布': spread_dist.to_dict()
        } 
        return self.quality_report
    
    def save_processed_data(self):
        """保存处理后的数据"""
        print("\n" + "="*80)
        print("3: 保存处理后的数据")
        
        # 保存完整数据
        output_path = os.path.join(self.output_dir, 'benchmark_integrated.csv')
        self.df_merged.to_csv(output_path, index=False)
        print(f"合并数据数据已保存: {output_path}")
        # 保存质量报告
        report_path = os.path.join(self.output_dir, 'quality_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Benchmark 数据集质量报告\n")
            f.write("="*80 + "\n\n")
            f.write(f"总样本数: {len(self.df_merged)}\n")
            f.write(f"总特征数: {len([c for c in self.df_merged.columns if c not in ['names', 'original_names', 'label', 'batch', 'batch_id', 'type']])}\n")
            f.write(f"批次数: {self.df_merged['batch_id'].nunique()}\n\n")
            
            for key, value in self.quality_report.items():
                f.write(f"{key}: {value}\n")
        print(f"质量报告已保存: {report_path}")
        
        return output_path
    
    def run_full_pipeline(self):
        """运行完整处理流程"""
        print("Benchmark 数据集整合与批次效应分析")     
        # 1. 整合数据
        self.merge_all_batches()
        # 2. 质量控制
        self.quality_control()
        # 4. 保存数据
        output_path = self.save_processed_data()
        
        return output_path


def main():
    """主函数"""
    processor = BenchmarkDataProcessor(
        data_dir='data/raw/benchmark',
        output_dir='data/raw/benchmark'
    )
    
    processor.run_full_pipeline()


if __name__ == '__main__':
    main()