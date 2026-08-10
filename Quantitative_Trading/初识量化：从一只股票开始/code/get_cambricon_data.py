#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取寒武纪（688256）历史日线数据

功能说明：
1. 连接 mootdx 行情服务器
2. 获取寒武纪（688256）2020-2025年的历史日线数据
3. 输出前10行和后10行数据
4. 输出数据总行数
5. 保存为 CSV 文件

股票信息：
- 股票名称：寒武纪
- 股票代码：688256
- 市场：上海科创板（market=1）

作者: AI Assistant
创建日期: 2026-06-17
"""

from mootdx.quotes import Quotes
import pandas as pd
import sys
from datetime import datetime


def connect_server():
    """
    连接到 mootdx 行情服务器
    
    返回:
        Quotes: 已连接的行情服务器对象
        
    异常:
        Exception: 当无法连接服务器时抛出
    """
    try:
        print("=" * 70)
        print("正在连接行情服务器...")
        print("=" * 70)
        
        # 使用 factory 方法自动选择最佳服务器
        # market='std' 表示使用标准行情服务器
        client = Quotes.factory(market='std', timeout=15)
        
        print("✓ 成功连接到行情服务器！\n")
        return client
        
    except Exception as e:
        print(f"✗ 连接服务器失败: {e}")
        raise Exception(f"无法连接到行情服务器: {str(e)}")


def get_stock_kline_data(client, symbol, market=1):
    """
    获取股票的历史日线数据（K线数据）
    
    参数:
        client: Quotes 对象，已连接的行情服务器
        symbol: str, 股票代码，例如 '688256'
        market: int, 市场代码（0-深圳，1-上海）
        
    返回:
        pandas.DataFrame: 包含历史日线数据的 DataFrame
        
    说明:
        - frequency=9 表示日K线数据
        - start=0 表示从最新数据开始获取
        - offset 参数用于分批获取大量数据
    """
    try:
        print("-" * 70)
        print(f"正在获取股票 {symbol} 的历史日线数据...")
        print("-" * 70)
        
        # mootdx 的 bars 方法用于获取K线数据
        # frequency 参数说明:
        # 0: 5分钟, 1: 15分钟, 2: 30分钟, 3: 1小时
        # 4: 日线, 5: 周线, 6: 月线, 7: 1分钟, 8: 1分钟K, 9: 日K
        
        all_data = []
        offset = 0
        batch_size = 800  # 每次获取800条数据
        
        print(f"开始获取数据（每次获取 {batch_size} 条记录）...")
        
        while True:
            # 获取一批数据
            # symbol: 股票代码
            # frequency: K线类型（9=日K）
            # start: 起始位置（0表示最新数据）
            # offset: 偏移量，用于分批获取
            batch_data = client.bars(
                symbol=symbol,
                frequency=9,  # 9 表示日K线
                start=offset,
                market=market
            )
            
            # 检查是否获取到数据
            if batch_data is None or batch_data.empty:
                print(f"  第 {offset // batch_size + 1} 批: 没有更多数据")
                break
            
            print(f"  第 {offset // batch_size + 1} 批: 获取到 {len(batch_data)} 条记录")
            all_data.append(batch_data)
            
            # 如果获取的数据少于批次大小，说明已经获取完毕
            if len(batch_data) < batch_size:
                print(f"  数据获取完成（本批次 {len(batch_data)} 条 < {batch_size}）")
                break
            
            # 增加偏移量，获取下一批数据
            offset += batch_size
        
        # 合并所有批次的数据
        if not all_data:
            print("✗ 未获取到任何数据")
            return pd.DataFrame()
        
        # 使用 pd.concat 合并所有 DataFrame
        df = pd.concat(all_data, ignore_index=True)
        
        # 数据清洗和排序
        # 按日期排序（从旧到新）
        if 'datetime' in df.columns:
            df = df.sort_values('datetime').reset_index(drop=True)
        
        print(f"\n✓ 数据获取成功！共获取 {len(df)} 条记录")
        print("-" * 70)
        
        return df
        
    except Exception as e:
        print(f"✗ 获取数据失败: {e}")
        raise


def display_dataframe_info(df, stock_name="寒武纪", stock_code="688256"):
    """
    显示 DataFrame 的详细信息
    
    参数:
        df: pandas.DataFrame, 要显示的数据
        stock_name: str, 股票名称
        stock_code: str, 股票代码
    """
    try:
        print("\n" + "=" * 70)
        print(f" {stock_name}（{stock_code}）历史数据统计 ")
        print("=" * 70)
        
        # 输出数据总行数
        total_rows = len(df)
        print(f"\n📊 数据总行数: {total_rows} 条记录\n")
        
        # 输出列名信息
        print("📋 数据列名:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        # 如果有日期列，显示日期范围
        if 'datetime' in df.columns and total_rows > 0:
            start_date = df['datetime'].iloc[0]
            end_date = df['datetime'].iloc[-1]
            print(f"\n📅 数据时间范围: {start_date} 至 {end_date}")
        
        print("\n" + "-" * 70)
        print("📈 前 10 行数据:")
        print("-" * 70)
        # 使用 to_string 确保完整显示
        print(df.head(10).to_string())
        
        print("\n" + "-" * 70)
        print("📉 后 10 行数据:")
        print("-" * 70)
        print(df.tail(10).to_string())
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"✗ 显示数据信息时出错: {e}")


def save_to_csv(df, filename="cambricon_688256_daily.csv"):
    """
    将 DataFrame 保存为 CSV 文件
    
    参数:
        df: pandas.DataFrame, 要保存的数据
        filename: str, 保存的文件名
        
    返回:
        str: 保存的完整文件路径
    """
    try:
        print("\n" + "=" * 70)
        print(f"正在保存数据到文件: {filename}")
        print("=" * 70)
        
        # 保存为 CSV 文件
        # index=False: 不保存行索引
        # encoding='utf-8-sig': 使用 UTF-8 BOM 编码，Excel 可以正确打开中文
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # 获取文件大小
        import os
        file_size = os.path.getsize(filename)
        file_size_kb = file_size / 1024
        
        print(f"✓ 数据已成功保存到: {filename}")
        print(f"  文件大小: {file_size_kb:.2f} KB ({file_size} 字节)")
        print(f"  保存位置: {os.path.abspath(filename)}")
        print("=" * 70)
        
        return os.path.abspath(filename)
        
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        raise


def main():
    """
    主函数：程序入口
    
    执行流程:
    1. 连接服务器
    2. 获取历史数据
    3. 显示数据信息
    4. 保存为 CSV 文件
    """
    print("\n" + "=" * 70)
    print(" 寒武纪（688256）历史日线数据获取程序 ")
    print("=" * 70 + "\n")
    
    # 股票信息
    STOCK_CODE = "688256"  # 寒武纪股票代码
    STOCK_NAME = "寒武纪"
    MARKET = 1  # 上海市场（科创板属于上海市场）
    OUTPUT_FILE = "cambricon_688256_daily.csv"
    
    client = None
    
    try:
        # 步骤1: 连接服务器
        client = connect_server()
        
        # 步骤2: 获取历史数据
        df = get_stock_kline_data(client, symbol=STOCK_CODE, market=MARKET)
        
        # 检查是否获取到数据
        if df.empty:
            print("✗ 未获取到数据，程序退出")
            return 1
        
        # 步骤3: 显示数据信息（前10行、后10行、总行数）
        display_dataframe_info(df, stock_name=STOCK_NAME, stock_code=STOCK_CODE)
        
        # 步骤4: 保存为 CSV 文件
        saved_path = save_to_csv(df, filename=OUTPUT_FILE)
        
        # 程序执行成功
        print("\n" + "=" * 70)
        print("✓ 程序执行完成！")
        print("=" * 70)
        print(f"\n💾 数据已保存至: {saved_path}")
        print(f"📊 共获取 {len(df)} 条历史记录\n")
        
        return 0  # 成功退出
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断程序执行")
        return 130  # 用户中断的退出码
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ 程序执行失败: {str(e)}")
        print("=" * 70 + "\n")
        import traceback
        traceback.print_exc()
        return 1  # 错误退出
        
    finally:
        # 清理资源
        if client:
            try:
                print("\n正在关闭连接...")
            except:
                pass


if __name__ == "__main__":
    """
    程序入口点
    
    使用方法:
        1. 激活虚拟环境: source mootdx_env/bin/activate
        2. 运行程序: python get_cambricon_data.py
        3. 查看生成的 CSV 文件: cambricon_688256_daily.csv
    """
    exit_code = main()
    sys.exit(exit_code)
