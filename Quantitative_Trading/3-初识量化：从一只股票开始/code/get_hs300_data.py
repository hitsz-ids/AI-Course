#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import time
from datetime import datetime
import os

def get_hs300_constituents():
    """获取沪深300指数成分股"""
    print("正在获取沪深300指数成分股...")
    try:
        # 获取沪深300指数成分股
        hs300_df = ak.index_stock_cons_csindex(symbol="000300")
        print(f"成功获取 {len(hs300_df)} 只沪深300成分股")
        return hs300_df
    except Exception as e:
        print(f"获取沪深300成分股失败: {e}")
        return None

def get_stock_history_data(stock_code, stock_name, start_date, end_date):
    """获取单只股票的历史前复权数据"""
    try:
        # 获取前复权日线数据
        stock_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                     start_date=start_date, end_date=end_date, 
                                     adjust="qfq")
        
        # 添加股票代码和名称列
        stock_df['股票代码'] = stock_code
        stock_df['股票名称'] = stock_name
        
        print(f"成功获取 {stock_name}({stock_code}) 的历史数据，共 {len(stock_df)} 条记录")
        return stock_df
    except Exception as e:
        print(f"获取 {stock_name}({stock_code}) 数据失败: {e}")
        return None

def main():
    # 设置时间范围
    start_date = "20230901"
    end_date = "20250831"
    
    # 输出文件路径
    output_file = "../data/hs300_stock_data.csv"
    
    print("开始获取沪深300成分股历史数据...")
    print(f"时间范围: {start_date} 至 {end_date}")
    
    # 获取沪深300成分股
    hs300_df = get_hs300_constituents()
    if hs300_df is None or len(hs300_df) == 0:
        print("无法获取沪深300成分股，程序退出")
        return
    
    # 显示成分股信息
    print("\n沪深300成分股前10只:")
    print(hs300_df[['成分券代码', '成分券名称']].head(10))
    
    all_data = []
    total_stocks = len(hs300_df)
    
    print(f"\n开始批量获取 {total_stocks} 只股票的历史数据...")
    
    # 遍历所有成分股获取数据
    for i, (index, row) in enumerate(hs300_df.iterrows(), 1):
        stock_code = row['成分券代码']
        stock_name = row['成分券名称']
        
        print(f"\n[{i}/{total_stocks}] 正在获取 {stock_name}({stock_code}) 的数据...")
        
        # 获取股票历史数据
        stock_data = get_stock_history_data(stock_code, stock_name, start_date, end_date)
        
        if stock_data is not None and len(stock_data) > 0:
            all_data.append(stock_data)
        
        # 添加延迟避免请求过于频繁
        time.sleep(0.1)
    
    if not all_data:
        print("没有获取到任何股票数据，程序退出")
        return
    
    # 合并所有数据
    print("\n正在合并所有股票数据...")
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # 保存到CSV文件
    print(f"正在保存数据到 {output_file}...")
    combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"数据保存完成！共 {len(combined_df)} 条记录")
    
    # 显示数据前5行和列名
    print("\n数据前5行:")
    print(combined_df.head())
    
    print("\n列名:")
    print(combined_df.columns.tolist())
    
    # 显示数据统计信息
    print(f"\n数据统计:")
    print(f"股票数量: {combined_df['股票代码'].nunique()}")
    print(f"时间范围: {combined_df['日期'].min()} 至 {combined_df['日期'].max()}")
    print(f"总记录数: {len(combined_df)}")

if __name__ == "__main__":
    main()
