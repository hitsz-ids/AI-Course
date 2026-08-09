回测入口为 `backtest.py`，会加载训练好的模型对 test 集预测并执行策略回测。

```bash
python backtest.py --stage reproduce --universe csi300 --exp_no 1 --seed 0
```

回测规则（简述）：
- 每个回测交易日根据测试集预测得到的 `score` 给出调仓信号（多因子长仓）。
- 采用 `TopkDropoutStrategy`：目标持仓选择 `topk` 个 `score` 最高的股票；在现有持仓中丢弃 `n_drop` 个 `score` 最差的股票，从而形成“轮动 + 控制换手”。
- 采用盈利保护 `WinnerProtectTopkDropoutStrategy`：当某股票从入场价计算的浮盈落在 `[5%, 10%]` 区间时，保护其不被卖出持续 `protect_days` 个交易日；浮盈超过 10% 则取消本次保护（直至卖出）。
- 交易由 Qlib 的 `SimulatorExecutor` 模拟撮合，默认以 `deal_price=close`（收盘价）成交，并计入开仓/平仓成本与最小成本。

回测输出（默认）：

- `output/backtest/pred_score.csv`
- `output/backtest/nav_curve.csv`
- `output/backtest/nav_curve.png`
