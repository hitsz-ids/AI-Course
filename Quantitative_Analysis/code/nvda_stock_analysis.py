#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NVDA股票数据分析脚本
功能：
1. 绘制累计收益趋势图
2. 计算每日收益率
3. 找到排名前十的收益率最大和最小的日期
4. 计算年化收益率和年化波动率
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import seaborn as sns

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_and_preprocess_data(file_path):
    """加载并预处理股票数据"""
    print("正在加载股票数据...")
    
    # 读取CSV文件
    df = pd.read_csv(file_path)
    
    # 转换日期列
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    # 确保数据按日期排序
    df.sort_index(inplace=True)
    
    print(f"数据加载完成，时间范围: {df.index.min()} 到 {df.index.max()}")
    print(f"总交易日数: {len(df)}")
    
    return df

def calculate_daily_returns(df):
    """计算每日收益率"""
    print("\n正在计算每日收益率...")
    
    # 计算每日收益率 (今日收盘价/昨日收盘价 - 1)
    df['Daily_Return'] = df['Close'].pct_change()
    
    # 计算累计收益率
    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
    
    # 删除第一行的NaN值
    df = df.dropna(subset=['Daily_Return'])
    
    print(f"每日收益率计算完成，有效交易日数: {len(df)}")
    
    return df

def plot_cumulative_returns(df):
    """绘制累计收益趋势图"""
    print("\n正在绘制累计收益趋势图...")
    
    plt.figure(figsize=(14, 8))
    
    # 绘制累计收益率
    plt.plot(df.index, df['Cumulative_Return'] * 100, 
             linewidth=2, color='blue', label='累计收益率')
    
    # 设置图表标题和标签
    plt.title('NVDA股票累计收益率趋势 (2020-2025)', fontsize=16, fontweight='bold')
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('累计收益率 (%)', fontsize=12)
    
    # 设置日期格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    
    # 添加网格
    plt.grid(True, alpha=0.3)
    
    # 添加图例
    plt.legend(fontsize=12)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('nvda_cumulative_returns.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("累计收益趋势图已保存为 'nvda_cumulative_returns.png'")

def find_top_returns(df):
    """找到收益率最大和最小的前十日期"""
    print("\n正在分析收益率极值...")
    
    # 找到收益率最大的前十日期
    top_gains = df.nlargest(10, 'Daily_Return')[['Close', 'Daily_Return']]
    top_gains['Daily_Return_Pct'] = top_gains['Daily_Return'] * 100
    
    # 找到收益率最小的前十日期
    top_losses = df.nsmallest(10, 'Daily_Return')[['Close', 'Daily_Return']]
    top_losses['Daily_Return_Pct'] = top_losses['Daily_Return'] * 100
    
    print("=" * 80)
    print("收益率最大的前十日期:")
    print("=" * 80)
    for i, (date, row) in enumerate(top_gains.iterrows(), 1):
        print(f"{i:2d}. {date.strftime('%Y-%m-%d')}: {row['Daily_Return_Pct']:7.2f}% "
              f"(收盘价: ${row['Close']:.2f})")
    
    print("\n" + "=" * 80)
    print("收益率最小的前十日期:")
    print("=" * 80)
    for i, (date, row) in enumerate(top_losses.iterrows(), 1):
        print(f"{i:2d}. {date.strftime('%Y-%m-%d')}: {row['Daily_Return_Pct']:7.2f}% "
              f"(收盘价: ${row['Close']:.2f})")
    
    return top_gains, top_losses

def calculate_annualized_metrics(df):
    """计算年化收益率和年化波动率"""
    print("\n正在计算年化指标...")
    
    # 计算总收益率
    total_return = df['Cumulative_Return'].iloc[-1]
    
    # 计算总交易天数
    total_days = len(df)
    
    # 计算年化交易日数 (通常按252个交易日计算)
    trading_days_per_year = 252
    
    # 计算年化收益率
    years = total_days / trading_days_per_year
    annualized_return = (1 + total_return) ** (1 / years) - 1
    
    # 计算年化波动率 (日收益率的标准差 * sqrt(252))
    annualized_volatility = df['Daily_Return'].std() * np.sqrt(trading_days_per_year)
    
    print("=" * 80)
    print("NVDA股票五年表现分析 (2020-2025)")
    print("=" * 80)
    print(f"总交易日数: {total_days} 天")
    print(f"总收益率: {total_return * 100:.2f}%")
    print(f"年化收益率: {annualized_return * 100:.2f}%")
    print(f"年化波动率: {annualized_volatility * 100:.2f}%")
    print(f"夏普比率(假设无风险收益率为0): {annualized_return / annualized_volatility:.2f}")
    
    return annualized_return, annualized_volatility

def plot_daily_returns_distribution(df):
    """绘制每日收益率分布图"""
    print("\n正在绘制每日收益率分布图...")
    
    plt.figure(figsize=(12, 6))
    
    # 绘制直方图
    plt.hist(df['Daily_Return'] * 100, bins=50, alpha=0.7, 
             color='skyblue', edgecolor='black')
    
    # 添加统计信息
    mean_return = df['Daily_Return'].mean() * 100
    std_return = df['Daily_Return'].std() * 100
    
    plt.axvline(mean_return, color='red', linestyle='--', 
                linewidth=2, label=f'均值: {mean_return:.2f}%')
    plt.axvline(mean_return + std_return, color='orange', linestyle=':', 
                linewidth=1, label=f'±1标准差')
    plt.axvline(mean_return - std_return, color='orange', linestyle=':', 
                linewidth=1)
    
    plt.title('NVDA每日收益率分布 (2020-2025)', fontsize=14, fontweight='bold')
    plt.xlabel('日收益率 (%)', fontsize=12)
    plt.ylabel('频次', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('nvda_daily_returns_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("每日收益率分布图已保存为 'nvda_daily_returns_distribution.png'")

def main():
    """主函数"""
    print("=" * 80)
    print("NVDA股票数据分析工具")
    print("=" * 80)
    
    # 文件路径
    file_path = "../data/NVDA_stock_data_2020_2025.csv"
    
    try:
        # 1. 加载数据
        df = load_and_preprocess_data(file_path)
        
        # 2. 计算收益率
        df = calculate_daily_returns(df)
        
        # 3. 绘制累计收益趋势图
        plot_cumulative_returns(df)
        
        # 4. 找到收益率极值
        top_gains, top_losses = find_top_returns(df)
        
        # 5. 计算年化指标
        annualized_return, annualized_volatility = calculate_annualized_metrics(df)
        
        # 6. 绘制收益率分布图
        plot_daily_returns_distribution(df)
        
        # 7. 保存分析结果到CSV
        df[['Close', 'Daily_Return', 'Cumulative_Return']].to_csv('nvda_analysis_results.csv')
        print(f"\n分析结果已保存到 'nvda_analysis_results.csv'")
        
        print("\n" + "=" * 80)
        print("分析完成！")
        print("=" * 80)
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        print("请确保NVDA_stock_data_2020_2025.csv文件存在")
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
