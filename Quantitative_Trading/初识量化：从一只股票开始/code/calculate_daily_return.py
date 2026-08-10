import pandas as pd

# 1. 读取CSV文件
df = pd.read_csv('cambricon_688256_daily.csv')

# 2. 按日期排序
df['date'] = pd.to_datetime(df['datetime'])
df = df.sort_values('date').reset_index(drop=True)

# 3. 使用收盘价计算每日收益率
# 每日收益率 = (当日开盘价 - 当日收盘价) / 当日开盘价
# 4. 新增 return 字段
df['return'] = (df['open'] - df['close']) / df['open']

# 5. 输出前5条数据 / 后5条数据
print("=" * 80)
print("寒武纪（688256）每日收益率 - 前5条数据")
print("=" * 80)
print(df[['datetime', 'open', 'close', 'return']].head(5).to_string(index=False))

print("\n" + "=" * 80)
print("寒武纪（688256）每日收益率 - 后5条数据")
print("=" * 80)
print(df[['datetime', 'open', 'close', 'return']].tail(5).to_string(index=False))

# 6. 保存新的CSV文件
output_df = df.drop(columns=['date'])
output_df.to_csv('cambricon_688256_daily_with_return.csv', index=False, encoding='utf-8-sig')
print("\n结果已保存到: cambricon_688256_daily_with_return.csv")
