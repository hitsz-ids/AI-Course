#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
绘制寒武纪（688256）收盘价走势图

功能说明：
1. 读取寒武纪历史数据CSV文件
2. 绘制收盘价走势图
3. 横轴为日期，纵轴为收盘价
4. 显示完整历史走势

作者: AI Assistant
创建日期: 2026-06-17
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import sys


def read_stock_data(filename='cambricon_688256_daily.csv'):
    """
    读取股票历史数据
    
    参数:
        filename: str, CSV文件名
        
    返回:
        pandas.DataFrame: 股票数据
    """
    try:
        print("=" * 70)
        print(f"正在读取数据文件: {filename}")
        print("=" * 70)
        
        # 读取CSV文件
        df = pd.read_csv(filename)
        
        # 转换日期列为 datetime 类型
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 按日期排序（确保从旧到新）
        df = df.sort_values('datetime').reset_index(drop=True)
        
        print(f"✓ 数据读取成功！")
        print(f"  数据条数: {len(df)} 条")
        print(f"  日期范围: {df['datetime'].min()} 至 {df['datetime'].max()}")
        print(f"  收盘价范围: {df['close'].min():.2f}元 至 {df['close'].max():.2f}元")
        print("=" * 70 + "\n")
        
        return df
        
    except FileNotFoundError:
        print(f"✗ 错误：找不到文件 {filename}")
        print("  请先运行 get_cambricon_data.py 获取数据")
        raise
    except Exception as e:
        print(f"✗ 读取数据失败: {e}")
        raise


def plot_price_trend(df, save_filename='cambricon_price_trend.png'):
    """
    绘制收盘价走势图
    
    参数:
        df: pandas.DataFrame, 包含日期和收盘价的数据
        save_filename: str, 保存的图片文件名
    """
    try:
        print("=" * 70)
        print("正在绘制收盘价走势图...")
        print("=" * 70)
        
        # 设置中文字体（macOS）
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'STHeiti', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 创建图形和坐标轴
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # 绘制收盘价曲线
        ax.plot(df['datetime'], df['close'], 
                linewidth=1.5, 
                color='#1f77b4',  # 蓝色
                label='收盘价',
                alpha=0.9)
        
        # 填充曲线下方区域，增加视觉效果
        ax.fill_between(df['datetime'], df['close'], 
                        alpha=0.2, 
                        color='#1f77b4')
        
        # 设置图表标题
        ax.set_title('寒武纪（688256）历史收盘价走势图', 
                     fontsize=18, 
                     fontweight='bold',
                     pad=20)
        
        # 设置横轴标签
        ax.set_xlabel('日期', fontsize=14, fontweight='bold')
        
        # 设置纵轴标签
        ax.set_ylabel('收盘价（元）', fontsize=14, fontweight='bold')
        
        # 设置横轴日期格式
        # 使用自动日期格式化
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # 每3个月显示一次
        
        # 旋转日期标签，避免重叠
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 添加网格线，使图表更易读
        ax.grid(True, linestyle='--', alpha=0.4, linewidth=0.8)
        ax.set_axisbelow(True)  # 网格线在图形后面
        
        # 添加图例
        ax.legend(loc='upper left', fontsize=12, framealpha=0.9)
        
        # 添加统计信息文本框
        # 计算关键统计数据
        start_date = df['datetime'].min().strftime('%Y-%m-%d')
        end_date = df['datetime'].max().strftime('%Y-%m-%d')
        start_price = df['close'].iloc[0]
        end_price = df['close'].iloc[-1]
        max_price = df['close'].max()
        min_price = df['close'].min()
        total_return = ((end_price - start_price) / start_price) * 100
        
        # 在图表右上角添加统计信息
        stats_text = (
            f'数据范围: {start_date} 至 {end_date}\n'
            f'交易日数: {len(df)} 天\n'
            f'起始价: {start_price:.2f} 元\n'
            f'最新价: {end_price:.2f} 元\n'
            f'最高价: {max_price:.2f} 元\n'
            f'最低价: {min_price:.2f} 元\n'
            f'累计涨幅: {total_return:+.2f}%'
        )
        
        # 添加文本框
        ax.text(0.98, 0.97, stats_text,
                transform=ax.transAxes,
                fontsize=11,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', 
                         facecolor='wheat', 
                         alpha=0.8,
                         edgecolor='gray',
                         linewidth=1.5))
        
        # 标注最高价和最低价位置
        max_idx = df['close'].idxmax()
        min_idx = df['close'].idxmin()
        
        # 最高价标注
        ax.annotate(f'最高: {max_price:.2f}',
                   xy=(df['datetime'].iloc[max_idx], max_price),
                   xytext=(10, 10),
                   textcoords='offset points',
                   fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', 
                            facecolor='red', 
                            alpha=0.7),
                   arrowprops=dict(arrowstyle='->', 
                                 connectionstyle='arc3,rad=0',
                                 color='red',
                                 lw=1.5),
                   color='white',
                   fontweight='bold')
        
        # 最低价标注
        ax.annotate(f'最低: {min_price:.2f}',
                   xy=(df['datetime'].iloc[min_idx], min_price),
                   xytext=(10, -20),
                   textcoords='offset points',
                   fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', 
                            facecolor='green', 
                            alpha=0.7),
                   arrowprops=dict(arrowstyle='->', 
                                 connectionstyle='arc3,rad=0',
                                 color='green',
                                 lw=1.5),
                   color='white',
                   fontweight='bold')
        
        # 自动调整布局，避免标签被截断
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(save_filename, dpi=300, bbox_inches='tight')
        print(f"✓ 图表已保存: {save_filename}")
        print(f"  分辨率: 300 DPI")
        print(f"  图片尺寸: 16x8 英寸")
        
        # 显示图表
        print("\n正在显示图表...")
        plt.show()
        
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"✗ 绘图失败: {e}")
        raise


def display_summary_statistics(df):
    """
    显示数据的汇总统计信息
    
    参数:
        df: pandas.DataFrame, 股票数据
    """
    print("=" * 70)
    print(" 数据统计摘要 ")
    print("=" * 70)
    
    # 基本统计
    print("\n收盘价统计:")
    print(df['close'].describe())
    
    # 计算涨跌幅
    df['pct_change'] = df['close'].pct_change() * 100
    
    # 最大单日涨幅
    max_gain = df['pct_change'].max()
    max_gain_date = df[df['pct_change'] == max_gain]['datetime'].iloc[0]
    print(f"\n最大单日涨幅: {max_gain:.2f}% ({max_gain_date.strftime('%Y-%m-%d')})")
    
    # 最大单日跌幅
    max_loss = df['pct_change'].min()
    max_loss_date = df[df['pct_change'] == max_loss]['datetime'].iloc[0]
    print(f"最大单日跌幅: {max_loss:.2f}% ({max_loss_date.strftime('%Y-%m-%d')})")
    
    # 平均日涨跌幅
    avg_change = df['pct_change'].mean()
    print(f"平均日涨跌幅: {avg_change:.2f}%")
    
    # 上涨天数和下跌天数
    up_days = (df['pct_change'] > 0).sum()
    down_days = (df['pct_change'] < 0).sum()
    print(f"\n上涨天数: {up_days} 天 ({up_days/len(df)*100:.1f}%)")
    print(f"下跌天数: {down_days} 天 ({down_days/len(df)*100:.1f}%)")
    
    print("=" * 70 + "\n")


def main():
    """
    主函数
    """
    print("\n" + "=" * 70)
    print(" 寒武纪（688256）收盘价走势图绘制程序 ")
    print("=" * 70 + "\n")
    
    try:
        # 步骤1: 读取数据
        df = read_stock_data('cambricon_688256_daily.csv')
        
        # 步骤2: 显示统计摘要
        display_summary_statistics(df)
        
        # 步骤3: 绘制走势图
        plot_price_trend(df, save_filename='cambricon_price_trend.png')
        
        # 完成
        print("=" * 70)
        print("✓ 程序执行完成！")
        print("=" * 70)
        print("\n📊 生成的文件:")
        print("  - cambricon_price_trend.png (收盘价走势图)")
        print("\n💡 提示:")
        print("  - 图片已保存在当前目录")
        print("  - 图表窗口关闭后程序将退出\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断程序执行")
        return 130
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ 程序执行失败: {str(e)}")
        print("=" * 70 + "\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    """
    程序入口点
    
    使用方法:
        1. 确保已经运行 get_cambricon_data.py 获取数据
        2. 激活虚拟环境: source mootdx_env/bin/activate
        3. 运行程序: python plot_cambricon_price.py
        4. 查看生成的图片: open cambricon_price_trend.png
    """
    exit_code = main()
    sys.exit(exit_code)
