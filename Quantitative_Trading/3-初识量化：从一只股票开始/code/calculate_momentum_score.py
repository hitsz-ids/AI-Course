#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calculate_momentum_scores():
    """计算沪深300成分股的动量分数"""
    
    # 读取数据文件
    print("正在读取数据文件...")
    try:
        # 直接读取CSV文件，第一行就是列名
        df = pd.read_csv('../data/hs300_stock_data.csv')
        print(f"成功读取数据，共 {len(df)} 条记录")
        print(f"股票数量: {df['股票代码'].nunique()}")
    except Exception as e:
        print(f"读取数据文件失败: {e}")
        return
    
    # 将股票代码转换为字符串，确保格式一致
    df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
    
    # 确保日期列是datetime类型
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 获取最新的日期
    latest_date = df['日期'].max()
    print(f"数据最新日期: {latest_date}")
    
    # 计算各个时间段的起始日期
    one_month_ago = latest_date - timedelta(days=30)
    three_months_ago = latest_date - timedelta(days=90)
    six_months_ago = latest_date - timedelta(days=180)
    twelve_months_ago = latest_date - timedelta(days=365)
    
    print(f"计算时间点:")
    print(f"  1个月前: {one_month_ago}")
    print(f"  3个月前: {three_months_ago}")
    print(f"  6个月前: {six_months_ago}")
    print(f"  12个月前: {twelve_months_ago}")
    
    # 为每只股票计算收益率
    results = []
    
    for stock_code in df['股票代码'].unique():
        stock_data = df[df['股票代码'] == stock_code].copy()
        stock_data = stock_data.sort_values('日期')
        
        # 获取股票名称
        stock_name = stock_data['股票名称'].iloc[0]
        
        # 获取各个时间点的收盘价
        try:
            # 最新收盘价
            latest_close = stock_data[stock_data['日期'] == latest_date]['收盘'].values[0]
            
            # 1个月前收盘价（找最接近的日期）
            one_month_data = stock_data[stock_data['日期'] <= one_month_ago]
            if len(one_month_data) > 0:
                one_month_close = one_month_data.iloc[-1]['收盘']
                one_month_return = (latest_close / one_month_close - 1) * 100
            else:
                one_month_return = np.nan
            
            # 3个月前收盘价
            three_months_data = stock_data[stock_data['日期'] <= three_months_ago]
            if len(three_months_data) > 0:
                three_months_close = three_months_data.iloc[-1]['收盘']
                three_months_return = (latest_close / three_months_close - 1) * 100
            else:
                three_months_return = np.nan
            
            # 6个月前收盘价
            six_months_data = stock_data[stock_data['日期'] <= six_months_ago]
            if len(six_months_data) > 0:
                six_months_close = six_months_data.iloc[-1]['收盘']
                six_months_return = (latest_close / six_months_close - 1) * 100
            else:
                six_months_return = np.nan
            
            # 12个月前收盘价
            twelve_months_data = stock_data[stock_data['日期'] <= twelve_months_ago]
            if len(twelve_months_data) > 0:
                twelve_months_close = twelve_months_data.iloc[-1]['收盘']
                twelve_months_return = (latest_close / twelve_months_close - 1) * 100
            else:
                twelve_months_return = np.nan
            
            results.append({
                '股票代码': stock_code,
                '股票名称': stock_name,
                '1个月收益率': one_month_return,
                '3个月收益率': three_months_return,
                '6个月收益率': six_months_return,
                '12个月收益率': twelve_months_return
            })
            
        except (IndexError, ValueError):
            continue
    
    # 创建结果DataFrame
    result_df = pd.DataFrame(results)
    
    # 计算百分位值
    periods = ['1个月收益率', '3个月收益率', '6个月收益率', '12个月收益率']
    
    for period in periods:
        # 计算该周期的百分位值
        valid_returns = result_df[period].dropna()
        if len(valid_returns) > 0:
            result_df[f'{period}百分位值'] = result_df[period].apply(
                lambda x: (valid_returns <= x).mean() * 100 if pd.notna(x) else np.nan
            )
        else:
            result_df[f'{period}百分位值'] = np.nan
    
    # 计算动量分数（百分位值的平均值）
    percentile_cols = [f'{period}百分位值' for period in periods]
    result_df['动量分数'] = result_df[percentile_cols].mean(axis=1)
    
    # 按动量分数排序
    result_df = result_df.sort_values('动量分数', ascending=False)
    
    # 保存结果到CSV文件
    output_file = '../data/momentum_scores.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n结果已保存到: {output_file}")
    
    # 打印结果
    print("\n动量分数排名前20的股票:")
    print("=" * 120)
    print(f"{'排名':<4} {'股票代码':<10} {'股票名称':<10} {'1个月收益':<10} {'3个月收益':<10} {'6个月收益':<10} {'12个月收益':<10} {'动量分数':<10}")
    print("=" * 120)
    
    for i, (idx, row) in enumerate(result_df.head(20).iterrows(), 1):
        print(f"{i:<4} {row['股票代码']:<10} {row['股票名称']:<10} "
              f"{row['1个月收益率']:>8.2f}% {row['3个月收益率']:>8.2f}% "
              f"{row['6个月收益率']:>8.2f}% {row['12个月收益率']:>8.2f}% "
              f"{row['动量分数']:>8.2f}")
    
    # 打印完整的列信息
    print(f"\n完整结果包含以下列:")
    for col in result_df.columns:
        print(f"  - {col}")
    
    return result_df

if __name__ == "__main__":
    calculate_momentum_scores()
