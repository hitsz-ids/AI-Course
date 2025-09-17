#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取英伟达(NVDA)股票历史数据并保存为CSV文件
时间范围：2020-01-01 到 2025-08-26
"""

import yfinance as yf
import pandas as pd
import os

def get_nvda_stock_data():
    """
    获取NVDA股票历史数据并保存为CSV文件
    """
    # 股票代码和时间范围
    ticker = "NVDA"
    start_date = "2020-01-01"
    end_date = "2025-08-26"
    
    # 输出文件路径
    output_file = "../data/NVDA_stock_data_2020_2025.csv"
    
    print(f"正在获取 {ticker} 股票数据 ({start_date} 到 {end_date})...")
    
    try:
        # 获取股票数据
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            print("未获取到数据，请检查股票代码和时间范围")
            return
        
        # 保存为CSV文件
        data.to_csv(output_file)
        print(f"数据已保存到: {output_file}")
        print(f"数据形状: {data.shape}")
        
        # 打印前5行数据
        print("\n前5行数据:")
        print(data.head())
        
        # 解释数据含义
        print("\n数据列含义解释:")
        print("1. Open: 开盘价 - 交易日开始时的股票价格")
        print("2. High: 最高价 - 交易日内的最高价格")
        print("3. Low: 最低价 - 交易日内的最低价格")
        print("4. Close: 收盘价 - 交易日结束时的股票价格")
        print("5. Volume: 成交量 - 交易日内的股票交易数量")
        print("6. Dividends: 股息 - 如果有股息支付的话")
        print("7. Stock Splits: 股票分割 - 如果有股票分割的话")
        
        # 显示基本统计信息
        print(f"\n数据统计信息:")
        print(f"时间范围: {data.index.min()} 到 {data.index.max()}")
        print(f"总交易日数: {len(data)}")
        print(f"收盘价范围: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
        
    except Exception as e:
        print(f"获取数据时出错: {e}")
        print("请确保已安装yfinance库: pip install yfinance")

if __name__ == "__main__":
    get_nvda_stock_data()
