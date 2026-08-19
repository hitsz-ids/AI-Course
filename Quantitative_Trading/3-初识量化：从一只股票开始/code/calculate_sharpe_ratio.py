import pandas as pd
import numpy as np

# 1. 读取数据并按日期排序
df = pd.read_csv('cambricon_688256_daily.csv')
df['date'] = pd.to_datetime(df['datetime'])
df = df.sort_values('date').reset_index(drop=True)

# 2. 使用收盘价计算每日收益率
df['daily_return'] = df['close'].pct_change()
returns = df['daily_return'].dropna()

# 3. 计算年化收益率（基于累计收益率，按交易天数折算为年化）
cumulative_return = (1 + returns).prod() - 1
n_days = len(returns)
trading_days_per_year = 252
annualized_return = (1 + cumulative_return) ** (trading_days_per_year / n_days) - 1

# 4. 计算年化波动率 = 日收益率标准差 × sqrt(252)
daily_std = returns.std()
annualized_volatility = daily_std * np.sqrt(trading_days_per_year)

# 5. 计算夏普比率 = (年化收益率 - 无风险收益率) / 年化波动率
risk_free_rate = 0.014
sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility

print("=" * 60)
print("寒武纪（688256）夏普比率分析")
print("=" * 60)
print(f"数据区间:         {df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}")
print(f"样本天数:         {n_days} 天")
print(f"累计收益率:        {cumulative_return*100:>10.2f}%")
print("-" * 60)
print(f"无风险收益率:      {risk_free_rate*100:>10.2f}%")
print(f"年化收益率:        {annualized_return*100:>10.2f}%")
print(f"年化波动率:        {annualized_volatility*100:>10.2f}%")
print(f"夏普比率:          {sharpe_ratio:>10.4f}")
print("=" * 60)
