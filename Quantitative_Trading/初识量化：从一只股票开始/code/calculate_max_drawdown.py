import pandas as pd

# 1. 读取数据并按日期排序
df = pd.read_csv('cambricon_688256_daily.csv')
df['date'] = pd.to_datetime(df['datetime'])
df = df.sort_values('date').reset_index(drop=True)

# 2. 使用收盘价计算每日收益率，累计收益，账户资产价值（初始资金10万）
df['daily_return'] = df['close'].pct_change().fillna(0)
df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1

initial_capital = 100_000
df['portfolio_value'] = initial_capital * (1 + df['cumulative_return'])

# 3. 计算历史最高资产（累计最大值，即历史新高）
df['peak'] = df['portfolio_value'].cummax()

# 4. 计算每日回撤比例 = (当前资产 - 历史最高资产) / 历史最高资产
df['drawdown'] = (df['portfolio_value'] - df['peak']) / df['peak']

# 5. 找出最大回撤（回撤比例最小值，即负得最多）
max_dd_idx = df['drawdown'].idxmin()
max_drawdown = df.loc[max_dd_idx, 'drawdown']
max_dd_date = df.loc[max_dd_idx, 'date']  # 最大回撤结束日期（谷底）
max_dd_peak_value = df.loc[max_dd_idx, 'peak']
max_dd_trough_value = df.loc[max_dd_idx, 'portfolio_value']

# 6. 找出最大回撤开始日期：即在谷底之前，最后一次达到该峰值(peak)的日期
peak_mask = df['portfolio_value'] == max_dd_peak_value
peak_dates_before = df.loc[peak_mask & (df['date'] <= max_dd_date), 'date']
max_dd_start_date = peak_dates_before.max()

print("=" * 60)
print("寒武纪（688256）最大回撤分析")
print("=" * 60)
print(f"初始资金:         ¥{initial_capital:>12,.2f}")
print(f"历史最高资产:     ¥{max_dd_peak_value:>12,.2f}")
print(f"回撤谷底资产:     ¥{max_dd_trough_value:>12,.2f}")
print(f"最大回撤幅度:      {max_drawdown*100:>10.2f}%")
print(f"最大回撤开始日期（峰值日）: {max_dd_start_date.date()}")
print(f"最大回撤结束日期（谷底日）: {max_dd_date.date()}")
print(f"回撤持续天数:      {(max_dd_date - max_dd_start_date).days} 天")
print("=" * 60)

# 保存包含回撤信息的CSV
output_df = df.drop(columns=['date'])
output_df.to_csv('cambricon_688256_drawdown.csv', index=False, encoding='utf-8-sig')
print("\n结果已保存到: cambricon_688256_drawdown.csv")
