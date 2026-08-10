#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

def display_detailed_results():
    """显示详细的动量分数结果"""
    
    # 读取动量分数结果
    try:
        df = pd.read_csv('../data/momentum_scores.csv')
        print(f"成功读取动量分数结果，共 {len(df)} 只股票")
    except Exception as e:
        print(f"读取动量分数结果失败: {e}")
        return
    
    # 显示前20只股票的详细信息
    print("\n动量分数排名前20的股票（详细信息）:")
    print("=" * 150)
    print(f"{'排名':<4} {'股票代码':<8} {'股票名称':<10} {'1个月收益':<8} {'1个月%位':<8} {'3个月收益':<8} {'3个月%位':<8} {'6个月收益':<8} {'6个月%位':<8} {'12个月收益':<8} {'12个月%位':<8} {'动量分数':<8}")
    print("=" * 150)
    
    for i, (idx, row) in enumerate(df.head(20).iterrows(), 1):
        print(f"{i:<4} {row['股票代码']:<8} {row['股票名称']:<10} "
              f"{row['1个月收益率']:>7.1f}% {row['1个月收益率百分位值']:>7.1f} "
              f"{row['3个月收益率']:>7.1f}% {row['3个月收益率百分位值']:>7.1f} "
              f"{row['6个月收益率']:>7.1f}% {row['6个月收益率百分位值']:>7.1f} "
              f"{row['12个月收益率']:>7.1f}% {row['12个月收益率百分位值']:>7.1f} "
              f"{row['动量分数']:>7.1f}")
    
    # 显示统计信息
    print(f"\n统计信息:")
    print(f"股票总数: {len(df)}")
    print(f"平均动量分数: {df['动量分数'].mean():.2f}")
    print(f"最高动量分数: {df['动量分数'].max():.2f}")
    print(f"最低动量分数: {df['动量分数'].min():.2f}")
    
    # 显示各时间段收益率的统计
    periods = ['1个月收益率', '3个月收益率', '6个月收益率', '12个月收益率']
    for period in periods:
        valid_data = df[period].dropna()
        if len(valid_data) > 0:
            print(f"{period}: 平均={valid_data.mean():.2f}%, 最高={valid_data.max():.2f}%, 最低={valid_data.min():.2f}%")
    
    print(f"\n结果文件已保存为: momentum_scores.csv")
    print(f"文件包含以下列: {', '.join(df.columns.tolist())}")

if __name__ == "__main__":
    display_detailed_results()
