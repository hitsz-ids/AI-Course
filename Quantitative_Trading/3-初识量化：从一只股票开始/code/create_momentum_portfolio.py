import pandas as pd
import numpy as np

# 读取动量分值文件
momentum_scores = pd.read_csv('../data/momentum_scores.csv')
# 按动量分数降序排序，取前30名
top_30_stocks = momentum_scores.sort_values('动量分数', ascending=False).head(30)

# 读取股票数据文件，指定数据类型
stock_data = pd.read_csv('../data/hs300_stock_data.csv', header=None, dtype={1: str})

# 设置列名（根据数据格式推断）
# 从之前查看的数据来看，列应该是：日期,股票代码,开盘价,收盘价,最高价,最低价,成交量,成交额,涨跌幅,换手率,振幅,量比,股票名称
stock_data.columns = ['date', 'stock_code', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                     'pct_change', 'turnover_rate', 'amplitude', 'volume_ratio', 'stock_name']

# 转换价格列为数值类型
stock_data['open'] = pd.to_numeric(stock_data['open'], errors='coerce')
stock_data['close'] = pd.to_numeric(stock_data['close'], errors='coerce')
stock_data['high'] = pd.to_numeric(stock_data['high'], errors='coerce')
stock_data['low'] = pd.to_numeric(stock_data['low'], errors='coerce')

# 获取2025年8月最后一个交易日的数据
august_2025_data = stock_data[stock_data['date'].str.startswith('2025-08')]
last_trading_day = august_2025_data['date'].max()

print(f"2025年8月最后一个交易日: {last_trading_day}")

# 获取最后交易日的所有股票数据
last_day_data = stock_data[stock_data['date'] == last_trading_day]

# 为前30只股票查找开盘价
portfolio_data = []
for _, stock in top_30_stocks.iterrows():
    stock_code = str(stock['股票代码']).zfill(6)  # 确保股票代码是6位
    stock_name = stock['股票名称']
    
    # 在最后交易日数据中查找该股票
    stock_info = last_day_data[last_day_data['stock_code'] == stock_code]
    
    if not stock_info.empty:
        open_price = stock_info['open'].iloc[0]
        # 计算购买股数（100000元 / 开盘价，向下取整）- 每只股票投资10万元
        shares = int(100000 / open_price)
        portfolio_data.append({
            '股票代码': stock_code,
            '股票名称': stock_name,
            '开盘价': open_price,
            '购买股数': shares,
            '投资金额': shares * open_price
        })
    else:
        print(f"警告: 未找到股票 {stock_code} ({stock_name}) 在 {last_trading_day} 的数据")

# 创建投资组合DataFrame
portfolio_df = pd.DataFrame(portfolio_data)

# 计算总投资金额
total_investment = portfolio_df['投资金额'].sum()
print(f"总投资金额: {total_investment:.2f} 元")
print(f"目标投资金额: 3,000,000 元")

# 保存结果到CSV文件
output_file = '../data/momentum_investment_portfolio.csv'
portfolio_df[['股票代码', '股票名称', '购买股数']].to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"投资组合已保存到 {output_file}")
print("\n前10只股票的投资详情:")
print(portfolio_df.head(10).to_string(index=False))
