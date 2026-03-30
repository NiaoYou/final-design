import os
import pandas as pd
import numpy as np
import re
import csv

def normalize_key(name):
    """归一化：去除所有符号，用于判断是否为同一物质"""
    if not isinstance(name, str): return str(name)
    return re.sub(r'[\s,\-，\(\)]', '', name).lower()

def standardize_name_for_output(name):
    """标准化：保留逗号，修整空格"""
    if not isinstance(name, str): return str(name)
    name = name.replace('，', ',') # 中文逗号转英文
    name = re.sub(r',\s+', ',', name) # 去除逗号后空格
    return name.strip()

def combine_datasets_v3():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file1_path = os.path.join(script_dir, "安贞医院-氧化脂质发现集.xlsx")
    file2_path = os.path.join(script_dir, "北医三院验证集数据.xlsx")
    # 1. 读取数据
    df1 = pd.read_excel(file1_path, sheet_name="随机森林metaboanlyst")
    df2 = pd.read_excel(file2_path, sheet_name="Sheet1")

    # 2. 准备 Sample 和 Group 列
    # 安贞
    if 'ID' in df1.columns: df1.rename(columns={'ID': 'Sample'}, inplace=True)
    else: df1['Sample'] = [f'Anzhen_{i}' for i in range(len(df1))]
    # 北医 (Group -> Sample, Group.1 -> Group)
    if 'Group.1' in df2.columns: 
        if 'Group' in df2.columns: df2.drop(columns=['Group'], inplace=True)
        df2.rename(columns={'Group.1': 'Group'}, inplace=True)
    if 'Sample' not in df2.columns:
        df2['Sample'] = [f'Peking_{i}' for i in range(len(df2))]

    # 统一 Group 值
    for df in [df1, df2]:
        if 'Group' in df.columns:
            df['Group'] = df['Group'].replace({'NONE': 'non-MACE', 'Non-MACE': 'non-MACE'})

    # 3. 匹配代谢物列
    meta_cols = ['Sample', 'Group', 'Batch', 'Unnamed: 0']
    cols1 = [c for c in df1.columns if c not in meta_cols]
    cols2 = [c for c in df2.columns if c not in meta_cols]
    
    # 建立映射: {normalized_key: original_name}
    map1 = {normalize_key(c): c for c in cols1}
    map2 = {normalize_key(c): c for c in cols2}
    
    common_keys = set(map1.keys()).intersection(set(map2.keys()))
    if not common_keys:
        print("未找到共同代谢物！")
        return
    print(f"匹配到 {len(common_keys)} 个共同代谢物")

    # 4. 向量化构建  
    # 准备列名映射表 {old_name: new_standard_name}
    rename_dict1 = {}
    rename_dict2 = {}
    
    # 确定最终列的顺序 (按名称排序)
    final_metabolites = []
    for key in common_keys:
        orig1 = map1[key]
        orig2 = map2[key]
        std_name = standardize_name_for_output(orig1)
        
        rename_dict1[orig1] = std_name
        rename_dict2[orig2] = std_name
        final_metabolites.append(std_name)
    
    final_metabolites.sort()
    
    # --- 处理 Batch 0 (安贞) ---
    # 选出需要的列 -> 重命名 -> 添加Batch列
    df1_final = df1[['Sample', 'Group'] + list(rename_dict1.keys())].copy()
    df1_final.rename(columns=rename_dict1, inplace=True)
    df1_final['Batch'] = 0 
    
    # --- 处理 Batch 1 (北医) ---
    df2_final = df2[['Sample', 'Group'] + list(rename_dict2.keys())].copy()
    df2_final.rename(columns=rename_dict2, inplace=True)
    df2_final['Batch'] = 1  # 直接整列赋值
    
    # 5. 合并
    df_combined = pd.concat([df1_final, df2_final], ignore_index=True)
    
    # 强制列顺序
    ordered_cols = ['Sample', 'Group', 'Batch'] + final_metabolites
    df_combined = df_combined[ordered_cols]
    
    # --- 质量检查 ---
    print(f"   - 总行数: {len(df_combined)}")
    # 检查 Batch 列的唯一值
    batch_counts = df_combined['Batch'].value_counts()
    print(f"   - Batch 列统计:\n{batch_counts}")
    
    if df_combined['Batch'].isnull().any():
        print("警告: Batch 列存在空值！这不应该发生。")
    else:
        print("Batch 列数据完整。")
    print("-" * 30)

    # 6. 保存结果
    xlsx_path = os.path.join(script_dir, 'mi.xlsx')
    df_combined.to_excel(xlsx_path, index=False)

if __name__ == "__main__":
    combine_datasets_v3()