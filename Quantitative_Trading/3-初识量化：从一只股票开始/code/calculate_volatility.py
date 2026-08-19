import pandas as pd
import numpy as np

# 1. 读取数据并按日期排序
df = pd.read_csv('cambricon_688256_daily.csv')
df['date'] = pd.to_datetime(df['datetime'])
df = df.sort_values('date').reset_index(drop=True)

# 2. 使用收盘价计算每日收益率
# 每日收益率 = (今日收盘价 - 昨日收盘价) / 昨日收盘价
df['daily_return'] = df['close'].pct_change()

# 去除首行 NaN
returns = df['daily_return'].dropna()

# 3. 计算日收益率标准差
daily_std = returns.std()

# 4. 计算年化波动率 = 日收益率标准差 × sqrt(252)
annualized_volatility = daily_std * np.sqrt(252)

print("=" * 60)
print("寒武纪（688256）收益率波动率分析")
print("=" * 60)
print(f"样本天数:         {len(returns)} 天")
print(f"日收益率均值:      {returns.mean()*100:>10.4f}%")
print(f"日收益率标准差:    {daily_std*100:>10.4f}%")
print(f"年化波动率:        {annualized_volatility*100:>10.2f}%")
print("=" * 60)
