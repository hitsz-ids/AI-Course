import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，避免终端环境下阻塞
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 1. 读取带收益率的CSV（或重新计算）
df = pd.read_csv('cambricon_688256_daily_with_return.csv')
df['date'] = pd.to_datetime(df['datetime'])
df = df.sort_values('date').reset_index(drop=True)

# 2. 根据每日收益率计算累计收益
# 第一天 return 为 NaN，填充为 0（持仓起始日，资金不变）
df['return'] = df['return'].fillna(0)

# 累计收益率 = (1 + r1) * (1 + r2) * ... - 1
df['cumulative_return'] = (1 + df['return']).cumprod() - 1

# 3. 假设初始资金 100000 元，计算账户资产价值
initial_capital = 100_000
df['portfolio_value'] = initial_capital * (1 + df['cumulative_return'])

# 打印最终统计
print("=" * 60)
print("寒武纪（688256）累计收益分析")
print("=" * 60)
print(f"初始资金:     ¥{initial_capital:>12,.2f}")
print(f"最终资产:     ¥{df['portfolio_value'].iloc[-1]:>12,.2f}")
print(f"累计收益率:    {df['cumulative_return'].iloc[-1]*100:>10.2f}%")
print(f"数据区间:     {df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}")
print(f"交易天数:     {len(df)} 天")
print("=" * 60)

# 4. 绘制资金变化曲线
fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(df['date'], df['portfolio_value'], color='#2196F3', linewidth=1.5, label='账户资产')
ax.fill_between(df['date'], initial_capital, df['portfolio_value'],
                where=(df['portfolio_value'] >= initial_capital),
                alpha=0.15, color='#4CAF50', label='盈利区间')
ax.fill_between(df['date'], initial_capital, df['portfolio_value'],
                where=(df['portfolio_value'] < initial_capital),
                alpha=0.15, color='#F44336', label='亏损区间')

# 初始资金基准线
ax.axhline(y=initial_capital, color='gray', linestyle='--', linewidth=1, label=f'初始资金 ¥{initial_capital:,}')

# 标注最高点和最低点
max_idx = df['portfolio_value'].idxmax()
min_idx = df['portfolio_value'].idxmin()
ax.annotate(f"最高 ¥{df['portfolio_value'][max_idx]:,.0f}",
            xy=(df['date'][max_idx], df['portfolio_value'][max_idx]),
            xytext=(30, -20), textcoords='offset points',
            fontsize=9, color='#4CAF50',
            arrowprops=dict(arrowstyle='->', color='#4CAF50'))
ax.annotate(f"最低 ¥{df['portfolio_value'][min_idx]:,.0f}",
            xy=(df['date'][min_idx], df['portfolio_value'][min_idx]),
            xytext=(30, 20), textcoords='offset points',
            fontsize=9, color='#F44336',
            arrowprops=dict(arrowstyle='->', color='#F44336'))

# 格式化
ax.set_title('寒武纪（688256）累计收益曲线\n初始资金 ¥100,000', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('日期', fontsize=11)
ax.set_ylabel('账户资产价值（元）', fontsize=11)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.xticks(rotation=45)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'¥{x:,.0f}'))
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cambricon_cumulative_return.png', dpi=150, bbox_inches='tight')
print("\n图表已保存到: cambricon_cumulative_return.png")
