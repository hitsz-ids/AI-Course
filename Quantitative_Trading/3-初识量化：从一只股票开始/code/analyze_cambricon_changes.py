import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('cambricon_688256_daily.csv')

# 按日期排序（确保数据按时间顺序）
df['date'] = pd.to_datetime(df['datetime'])
df = df.sort_values('date')

# 计算每日涨跌幅
# 涨跌幅 = (当日收盘价 - 前一日收盘价) / 前一日收盘价 * 100
df['prev_close'] = df['close'].shift(1)
df['change_pct'] = ((df['close'] - df['prev_close']) / df['prev_close'] * 100).round(2)

# 删除第一行（没有前一日数据）
df_with_change = df[df['change_pct'].notna()].copy()

# 找出涨幅最大的10个交易日
top_10_gains = df_with_change.nlargest(10, 'change_pct')[['date', 'change_pct', 'close']]

# 找出跌幅最大的10个交易日
top_10_losses = df_with_change.nsmallest(10, 'change_pct')[['date', 'change_pct', 'close']]

print("=" * 60)
print("寒武纪（688256）每日涨跌幅分析")
print("=" * 60)

print("\n【涨幅最大的10个交易日】")
print("-" * 60)
print(f"{'日期':<12} {'涨跌幅(%)':<12} {'收盘价(元)':<12}")
print("-" * 60)
for idx, row in top_10_gains.iterrows():
    date_str = row['date'].strftime('%Y-%m-%d')
    print(f"{date_str:<12} {row['change_pct']:>10.2f}% {row['close']:>12.2f}")

print("\n" + "=" * 60)
print("\n【跌幅最大的10个交易日】")
print("-" * 60)
print(f"{'日期':<12} {'涨跌幅(%)':<12} {'收盘价(元)':<12}")
print("-" * 60)
for idx, row in top_10_losses.iterrows():
    date_str = row['date'].strftime('%Y-%m-%d')
    print(f"{date_str:<12} {row['change_pct']:>10.2f}% {row['close']:>12.2f}")

print("\n" + "=" * 60)

# 保存结果到CSV文件
output_df = pd.DataFrame({
    '类型': ['涨幅最大'] * 10 + ['跌幅最大'] * 10,
    '日期': list(top_10_gains['date'].dt.strftime('%Y-%m-%d')) + list(top_10_losses['date'].dt.strftime('%Y-%m-%d')),
    '涨跌幅(%)': list(top_10_gains['change_pct']) + list(top_10_losses['change_pct']),
    '收盘价(元)': list(top_10_gains['close']) + list(top_10_losses['close'])
})

output_df.to_csv('cambricon_top_changes.csv', index=False, encoding='utf-8-sig')
print("\n结果已保存到: cambricon_top_changes.csv")
