#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class MomentumBacktest:
    def __init__(self, data_file='hs300_stock_data.csv'):
        """
        初始化回测类
        
        Parameters:
        data_file: str, 历史数据文件路径
        """
        self.data_file = data_file
        self.df = None
        self.portfolio_returns = []
        self.portfolio_details = []
        
    def load_data(self):
        """加载历史数据"""
        print("正在加载历史数据...")
        try:
            self.df = pd.read_csv(self.data_file)
            self.df['股票代码'] = self.df['股票代码'].astype(str).str.zfill(6)
            self.df['日期'] = pd.to_datetime(self.df['日期'])
            print(f"成功加载数据，共 {len(self.df)} 条记录")
            print(f"股票数量: {self.df['股票代码'].nunique()}")
            print(f"数据时间范围: {self.df['日期'].min()} 至 {self.df['日期'].max()}")
            return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False
    
    def get_trading_days(self, start_date, end_date):
        """获取指定时间范围内的交易日"""
        mask = (self.df['日期'] >= start_date) & (self.df['日期'] <= end_date)
        trading_days = sorted(self.df.loc[mask, '日期'].unique())
        return trading_days
    
    def get_first_trading_day_of_month(self, year, month):
        """获取指定年月的第一个交易日"""
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        end_date = end_date - timedelta(days=1)
        
        trading_days = self.get_trading_days(start_date, end_date)
        return trading_days[0] if trading_days else None
    
    def calculate_momentum_score(self, calculation_date):
        """
        计算指定日期的动量分数
        
        Parameters:
        calculation_date: datetime, 计算日期
        
        Returns:
        DataFrame: 包含动量分数的股票列表
        """
        print(f"\n计算 {calculation_date.strftime('%Y-%m-%d')} 的动量分数...")
        
        # 计算各个时间段的起始日期
        one_month_ago = calculation_date - timedelta(days=30)
        three_months_ago = calculation_date - timedelta(days=90)
        six_months_ago = calculation_date - timedelta(days=180)
        twelve_months_ago = calculation_date - timedelta(days=365)
        
        results = []
        
        # 筛选计算日期之前的数据
        historical_data = self.df[self.df['日期'] <= calculation_date]
        
        for stock_code in self.df['股票代码'].unique():
            stock_data = historical_data[historical_data['股票代码'] == stock_code].copy()
            stock_data = stock_data.sort_values('日期')
            
            if len(stock_data) == 0:
                continue
                
            # 获取股票名称
            stock_name = stock_data['股票名称'].iloc[0]
            
            try:
                # 最新收盘价（计算日期当天或之前最近的）
                latest_data = stock_data[stock_data['日期'] <= calculation_date]
                if len(latest_data) == 0:
                    continue
                latest_close = latest_data.iloc[-1]['收盘']
                
                # 计算各时间段收益率
                def get_return(target_date):
                    target_data = stock_data[stock_data['日期'] <= target_date]
                    if len(target_data) > 0:
                        target_close = target_data.iloc[-1]['收盘']
                        return (latest_close / target_close - 1) * 100
                    else:
                        return np.nan
                
                one_month_return = get_return(one_month_ago)
                three_months_return = get_return(three_months_ago)
                six_months_return = get_return(six_months_ago)
                twelve_months_return = get_return(twelve_months_ago)
                
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
        
        if len(result_df) == 0:
            return result_df
        
        # 计算百分位值
        periods = ['1个月收益率', '3个月收益率', '6个月收益率', '12个月收益率']
        
        for period in periods:
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
        
        # 按动量分数排序，选择前30名
        result_df = result_df.sort_values('动量分数', ascending=False).head(30)
        
        print(f"成功计算 {len(result_df)} 只股票的动量分数")
        return result_df
    
    def calculate_monthly_return(self, stock_list, start_date, end_date):
        """
        计算投资组合在指定月份的收益率
        
        Parameters:
        stock_list: list, 股票代码列表
        start_date: datetime, 月初日期
        end_date: datetime, 月末日期
        
        Returns:
        dict: 包含每只股票收益率和组合总收益率的字典
        """
        print(f"计算投资组合 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} 的收益率...")
        
        stock_returns = {}
        valid_returns = []
        
        for stock_code in stock_list:
            stock_data = self.df[self.df['股票代码'] == stock_code].copy()
            stock_data = stock_data.sort_values('日期')
            
            # 获取月初价格
            start_data = stock_data[stock_data['日期'] <= start_date]
            if len(start_data) == 0:
                continue
            start_price = start_data.iloc[-1]['收盘']
            
            # 获取月末价格
            end_data = stock_data[stock_data['日期'] <= end_date]
            if len(end_data) == 0:
                continue
            end_price = end_data.iloc[-1]['收盘']
            
            # 计算收益率
            monthly_return = (end_price / start_price - 1) * 100
            stock_returns[stock_code] = monthly_return
            valid_returns.append(monthly_return)
        
        # 计算等权重投资组合收益率
        portfolio_return = np.mean(valid_returns) if valid_returns else 0
        
        return {
            'stock_returns': stock_returns,
            'portfolio_return': portfolio_return,
            'valid_stocks': len(valid_returns)
        }
    
    def run_backtest(self):
        """运行回测"""
        print("开始运行动量策略回测...")
        print("="*50)
        
        if not self.load_data():
            return
        
        # 定义回测时间范围
        backtest_months = [
            (2025, 1), (2025, 2), (2025, 3), (2025, 4),
            (2025, 5), (2025, 6), (2025, 7), (2025, 8)
        ]
        
        for year, month in backtest_months:
            print(f"\n{'='*60}")
            print(f"处理 {year}年{month}月")
            print(f"{'='*60}")
            
            # 获取该月第一个交易日
            first_trading_day = self.get_first_trading_day_of_month(year, month)
            if first_trading_day is None:
                print(f"无法找到 {year}年{month}月 的交易日")
                continue
            
            print(f"该月第一个交易日: {first_trading_day.strftime('%Y-%m-%d')}")
            
            # 计算动量分数并选择前30只股票
            momentum_scores = self.calculate_momentum_score(first_trading_day)
            if len(momentum_scores) == 0:
                print("无法计算动量分数")
                continue
            
            # 获取前30只股票
            top_30_stocks = momentum_scores.head(30)
            selected_stocks = top_30_stocks['股票代码'].tolist()
            
            print(f"\n{year}年{month}月投资组合（前30只股票）:")
            print(f"{'排名':<4} {'股票代码':<8} {'股票名称':<10} {'动量分数':<10}")
            print("-" * 40)
            for i, (idx, row) in enumerate(top_30_stocks.iterrows(), 1):
                print(f"{i:<4} {row['股票代码']:<8} {row['股票名称']:<10} {row['动量分数']:>8.2f}")
            
            # 计算该月的收益率
            if month == 12:
                next_month_start = datetime(year + 1, 1, 1)
            else:
                next_month_start = datetime(year, month + 1, 1)
            
            month_end = next_month_start - timedelta(days=1)
            
            # 获取月末最后一个交易日
            month_trading_days = self.get_trading_days(first_trading_day, month_end)
            if len(month_trading_days) == 0:
                print("该月无交易日数据")
                continue
            
            last_trading_day = month_trading_days[-1]
            
            # 计算月收益率
            monthly_results = self.calculate_monthly_return(
                selected_stocks, first_trading_day, last_trading_day
            )
            
            print(f"\n{year}年{month}月投资组合收益率:")
            print(f"{'股票代码':<8} {'股票名称':<10} {'月收益率':<10}")
            print("-" * 35)
            
            for stock_code in selected_stocks:
                if stock_code in monthly_results['stock_returns']:
                    stock_name = top_30_stocks[top_30_stocks['股票代码'] == stock_code]['股票名称'].iloc[0]
                    return_rate = monthly_results['stock_returns'][stock_code]
                    print(f"{stock_code:<8} {stock_name:<10} {return_rate:>8.2f}%")
            
            portfolio_return = monthly_results['portfolio_return']
            print(f"\n投资组合总收益率: {portfolio_return:.2f}%")
            print(f"有效股票数量: {monthly_results['valid_stocks']}/30")
            
            # 保存结果
            self.portfolio_returns.append({
                'year': year,
                'month': month,
                'date': first_trading_day,
                'portfolio_return': portfolio_return,
                'valid_stocks': monthly_results['valid_stocks']
            })
            
            self.portfolio_details.append({
                'year': year,
                'month': month,
                'date': first_trading_day,
                'stocks': top_30_stocks,
                'returns': monthly_results['stock_returns']
            })
    
    def get_hs300_etf_data(self):
        """获取沪深300ETF基金数据"""
        print("\n获取沪深300ETF基金(510300)数据...")
        try:
            # 获取沪深300ETF基金数据
            etf_data = ak.fund_etf_hist_em(symbol="510300", period="daily", 
                                         start_date="20250101", end_date="20250831", 
                                         adjust="qfq")
            
            etf_data['日期'] = pd.to_datetime(etf_data['日期'])
            print(f"成功获取ETF数据，共 {len(etf_data)} 条记录")
            return etf_data
        except Exception as e:
            print(f"获取ETF数据失败: {e}")
            return None
    
    def calculate_cumulative_returns(self):
        """计算累计收益率并绘图对比"""
        if not self.portfolio_returns:
            print("没有投资组合收益率数据")
            return
        
        print("\n计算累计收益率...")
        
        # 计算投资组合累计收益率
        portfolio_df = pd.DataFrame(self.portfolio_returns)
        portfolio_df['cumulative_return'] = (1 + portfolio_df['portfolio_return'] / 100).cumprod() - 1
        
        print("\n投资组合月度收益率:")
        print(f"{'年月':<8} {'月收益率':<10} {'累计收益率':<12}")
        print("-" * 35)
        for _, row in portfolio_df.iterrows():
            print(f"{row['year']}-{row['month']:02d}   {row['portfolio_return']:>8.2f}%   {row['cumulative_return']*100:>10.2f}%")
        
        # 获取沪深300ETF数据
        etf_data = self.get_hs300_etf_data()
        if etf_data is None:
            print("无法获取ETF数据，跳过对比")
            return
        
        # 计算ETF月度收益率
        etf_monthly_returns = []
        for year, month in [(2025, 1), (2025, 2), (2025, 3), (2025, 4), (2025, 5), (2025, 6), (2025, 7), (2025, 8)]:
            # 获取该月第一个和最后一个交易日
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            month_data = etf_data[(etf_data['日期'] >= start_date) & (etf_data['日期'] <= end_date)]
            if len(month_data) > 0:
                start_price = month_data.iloc[0]['收盘']
                end_price = month_data.iloc[-1]['收盘']
                monthly_return = (end_price / start_price - 1) * 100
                etf_monthly_returns.append({
                    'year': year,
                    'month': month,
                    'monthly_return': monthly_return
                })
        
        etf_df = pd.DataFrame(etf_monthly_returns)
        etf_df['cumulative_return'] = (1 + etf_df['monthly_return'] / 100).cumprod() - 1
        
        print("\n沪深300ETF月度收益率:")
        print(f"{'年月':<8} {'月收益率':<10} {'累计收益率':<12}")
        print("-" * 35)
        for _, row in etf_df.iterrows():
            print(f"{int(row['year'])}-{int(row['month']):02d}   {row['monthly_return']:>8.2f}%   {row['cumulative_return']*100:>10.2f}%")
        
        # 绘制对比图
        self.plot_comparison(portfolio_df, etf_df)
        
        # 打印最终结果对比
        final_portfolio_return = portfolio_df['cumulative_return'].iloc[-1] * 100
        final_etf_return = etf_df['cumulative_return'].iloc[-1] * 100
        
        print(f"\n最终累计收益率对比:")
        print(f"动量策略投资组合: {final_portfolio_return:.2f}%")
        print(f"沪深300ETF基金:   {final_etf_return:.2f}%")
        print(f"超额收益:         {final_portfolio_return - final_etf_return:.2f}%")
    
    def plot_comparison(self, portfolio_df, etf_df):
        """绘制投资组合与ETF的收益率对比图"""
        plt.figure(figsize=(12, 8))
        
        # 创建时间轴
        months = [f"{row['year']}-{row['month']:02d}" for _, row in portfolio_df.iterrows()]
        
        # 绘制累计收益率曲线
        plt.plot(months, portfolio_df['cumulative_return'] * 100, 
                marker='o', linewidth=2, label='Momentum Strategy Portfolio', color='blue')
        plt.plot(months, etf_df['cumulative_return'] * 100, 
                marker='s', linewidth=2, label='CSI 300 ETF (510300)', color='red')
        
        # 设置图表样式
        plt.title('Cumulative Returns Comparison: Momentum Strategy vs CSI 300 ETF', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Cumulative Return (%)', fontsize=12)
        plt.legend(fontsize=12, loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # 旋转x轴标签
        plt.xticks(rotation=45)
        
        # 添加零线
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig('momentum_strategy_comparison.png', dpi=300, bbox_inches='tight')
        print("\n对比图已保存为: momentum_strategy_comparison.png")
        
        # 显示图片
        plt.show()
    
    def save_detailed_results(self):
        """保存详细的回测结果"""
        if not self.portfolio_returns:
            return
        
        # 保存月度收益率
        portfolio_df = pd.DataFrame(self.portfolio_returns)
        portfolio_df['cumulative_return'] = (1 + portfolio_df['portfolio_return'] / 100).cumprod() - 1
        portfolio_df.to_csv('momentum_backtest_results.csv', index=False, encoding='utf-8-sig')
        
        # 保存每月的投资组合详情
        detailed_results = []
        for detail in self.portfolio_details:
            for _, stock in detail['stocks'].iterrows():
                stock_code = stock['股票代码']
                monthly_return = detail['returns'].get(stock_code, np.nan)
                detailed_results.append({
                    'year': detail['year'],
                    'month': detail['month'],
                    'date': detail['date'],
                    'stock_code': stock_code,
                    'stock_name': stock['股票名称'],
                    'momentum_score': stock['动量分数'],
                    'monthly_return': monthly_return
                })
        
        detailed_df = pd.DataFrame(detailed_results)
        detailed_df.to_csv('momentum_portfolio_details.csv', index=False, encoding='utf-8-sig')
        
        print("\n详细结果已保存:")
        print("- momentum_backtest_results.csv: 月度收益率汇总")
        print("- momentum_portfolio_details.csv: 每月投资组合详情")


def main():
    """主函数"""
    print("多周期动量策略回测系统")
    print("="*50)
    
    # 创建回测实例
    backtest = MomentumBacktest('../data/hs300_stock_data.csv')
    
    # 运行回测
    backtest.run_backtest()
    
    # 计算累计收益率并绘图对比
    backtest.calculate_cumulative_returns()
    
    # 保存详细结果
    backtest.save_detailed_results()
    
    print("\n回测完成！")


if __name__ == "__main__":
    main()
