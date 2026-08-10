"""
使用qlib对训练好的模型进行回测
"""
# runtime_compatibility_patch: ensure master.py and base_model.py are importable
# regardless of the working directory from which backtest.py is invoked.
import sys
import os
_MASTER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'MASTER')
_REPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if os.path.isdir(_MASTER_DIR) and _MASTER_DIR not in sys.path:
    sys.path.insert(0, _MASTER_DIR)
# DatetimeMajorWrapper must be registered before unpickling qlib-adapted datasets
if _REPO_DIR not in sys.path:
    sys.path.insert(0, _REPO_DIR)
from prepare_csi300_data import DatetimeMajorWrapper  # noqa: F401

import qlib
import pandas as pd
import pickle
import argparse
from pprint import pprint
from dataclasses import dataclass
from typing import Optional

# ========== 路径配置 ==========
# runtime_compatibility_patch: output lives under MASTER/ regardless of cwd.
OUTPUT_DIR = os.path.join(_MASTER_DIR, 'output')
from qlib.utils.time import Freq
from qlib.contrib.evaluate import backtest_daily, risk_analysis
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.backtest import backtest, executor
from master import MASTERModel
from qlib.contrib.report import analysis_position

from qlib.data import D
import numpy as np
import pandas as pd
import torch
from base_model import calc_ic, DailyBatchSamplerRandom


import matplotlib.pyplot as plt

def plot_nav_curve(report: pd.DataFrame, title: str = "NAV Curve"):
    df = report.copy()
    df = df.sort_index()

    # 日收益率口径
    ret = df["return"].fillna(0.0)
    bench = df["bench"].fillna(0.0)
    cost = df["cost"].fillna(0.0) if "cost" in df.columns else 0.0

    nav_wo_cost = (1.0 + ret).cumprod()
    nav_w_cost  = (1.0 + ret - cost).cumprod()
    nav_bench   = (1.0 + bench).cumprod()

    plt.figure(figsize=(12, 5))
    plt.plot(nav_wo_cost.index, nav_wo_cost.values, label="Strategy (no cost)")
    plt.plot(nav_w_cost.index,  nav_w_cost.values,  label="Strategy (with cost)")
    plt.plot(nav_bench.index,   nav_bench.values,   label="Benchmark")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("NAV")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    backtest_output_dir = f"{OUTPUT_DIR}/backtest"
    os.makedirs(backtest_output_dir, exist_ok=True)
    plt.savefig(f"{backtest_output_dir}/nav_curve.png")

    # 如果你也想保存净值到文件：
    nav_df = pd.DataFrame({
        "nav_no_cost": nav_wo_cost,
        "nav_with_cost": nav_w_cost,
        "nav_bench": nav_bench,
    })
    nav_df.to_csv(f"{backtest_output_dir}/nav_curve.csv")
    print(f"Saved {backtest_output_dir}/nav_curve.csv")

# 用法：在你拿到 report 后调用
# plot_nav_curve(report, title=f"NAV {config.start_time}~{config.end_time}")


def cs_zscore(s):
    return s.groupby(level=0).transform(lambda x: (x - x.mean()) / (x.std() + 1e-12))

def ema_smooth_score(pred_score: pd.DataFrame, alpha=0.7):
    sig = pred_score["score"].copy()
    sig = cs_zscore(sig)

    wide = sig.unstack("instrument").sort_index()
    wide_sm = wide.ewm(alpha=alpha, adjust=False).mean()
    sig_sm = wide_sm.stack().reindex(sig.index)

    return sig_sm.to_frame("score")

def add_trend_overlay(pred_score: pd.DataFrame, start_time: str, end_time: str,
                      mom_win=3, trend_win=20, lam_mom=0.2, lam_trend=0.1):
    sig = cs_zscore(pred_score["score"].copy())

    inst = pred_score.reset_index()["instrument"].unique().tolist()

    close = D.features(inst, ["$close"], start_time=start_time, end_time=end_time).reset_index()
    close["datetime"] = pd.to_datetime(close["datetime"]).dt.normalize()
    close = close.pivot(index="datetime", columns="instrument", values=close.columns[-1]).sort_index()

    mom = close.pct_change(mom_win).stack().reindex(sig.index)        # 短动量（抓续涨）
    trend = close.pct_change(trend_win).stack().reindex(sig.index)    # 长趋势（允许回撤后再涨）
    mom = cs_zscore(mom)
    trend = cs_zscore(trend).clip(lower=0)                            # 只奖励趋势，不惩罚

    sig_adj = (sig + lam_mom * mom + lam_trend * trend).dropna()
    return sig_adj.to_frame("score")


import copy
import numpy as np
import pandas as pd
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.backtest.decision import Order, OrderDir, TradeDecisionWO

class WinnerProtectTopkDropoutStrategy(TopkDropoutStrategy):
    """
    赢家保护（区间触发 + 超过上限永不保护）：
    - 仅当 pnl ∈ [protect_profit_low, protect_profit_high] 才触发/生效保护
    - 第一次进入区间时触发保护窗口 protect_days 个交易日（含触发日）
    - 一旦 pnl > protect_profit_high：本次持仓期间永久取消保护（直到卖出）
    """

    def __init__(
        self,
        *args,
        protect_profit_low=0.05,
        protect_profit_high=0.20,
        protect_days=5,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.protect_profit_low = float(protect_profit_low)
        self.protect_profit_high = float(protect_profit_high)
        self.protect_days = int(protect_days)

        assert self.protect_profit_low < self.protect_profit_high, "protect_profit_low must < protect_profit_high"

        self._entry_price = {}            # code -> entry price
        self._protect_until_step = {}     # code -> last protected trade_step
        self._protect_disabled = set()    # code -> protection permanently disabled for this holding

    def _sync_state(self, pos):
        cur = set(pos.get_stock_list())

        for k in list(self._entry_price.keys()):
            if k not in cur:
                self._entry_price.pop(k, None)

        for k in list(self._protect_until_step.keys()):
            if k not in cur:
                self._protect_until_step.pop(k, None)

        self._protect_disabled = {k for k in self._protect_disabled if k in cur}

        # 对已有持仓但没 entry 的兜底（避免 keyerror）
        for k in cur:
            self._entry_price.setdefault(k, float(pos.get_stock_price(k)))

    def _is_winner_protected(self, code, pos, trade_step: int) -> bool:
        if self.protect_days <= 0:
            return False

        self._sync_state(pos)

        if code in self._protect_disabled:
            return False

        ep = self._entry_price.get(code, None)
        if ep is None or ep <= 0:
            return False

        cp = float(pos.get_stock_price(code))
        pnl = cp / ep - 1.0

        # ✅ 超过上限：永久取消保护（直到卖出）
        if pnl > self.protect_profit_high:
            self._protect_disabled.add(code)
            self._protect_until_step.pop(code, None)
            return False

        # ✅ 未达到下限：不保护
        if pnl < self.protect_profit_low:
            return False

        # pnl 在区间内：可能触发/维持保护
        if code not in self._protect_until_step:
            # 第一次进入区间，触发保护窗口（只触发一次）
            self._protect_until_step[code] = trade_step + self.protect_days - 1

        until = self._protect_until_step.get(code, None)
        return (until is not None) and (trade_step <= until)

    def generate_trade_decision(self, execute_result=None):
        trade_step = self.trade_calendar.get_trade_step()
        trade_start_time, trade_end_time = self.trade_calendar.get_step_time(trade_step)

        # qlib 原生 TopkDropoutStrategy 用 shift=1 的信号
        pred_start_time, pred_end_time = self.trade_calendar.get_step_time(trade_step, shift=1)
        pred_score = self.signal.get_signal(start_time=pred_start_time, end_time=pred_end_time)

        if pred_score is None:
            return TradeDecisionWO([], self)

        if isinstance(pred_score, pd.DataFrame):
            pred_score = pred_score.iloc[:, 0]

        current_temp = copy.deepcopy(self.trade_position)
        sell_order_list = []
        buy_order_list = []

        cash = current_temp.get_cash()
        current_stock_list = current_temp.get_stock_list()

        last = pred_score.reindex(current_stock_list).sort_values(ascending=False)
        last_idx = last.index

        today = pred_score[~pred_score.index.isin(last_idx)].sort_values(ascending=False).index
        today = list(today[: (self.n_drop + self.topk - len(last_idx))])

        comb = pred_score.reindex(last_idx.union(pd.Index(today))).sort_values(ascending=False).index
        base_sell = list(last_idx[last_idx.isin(comb[-self.n_drop:])])

        # 过滤掉“受保护”的卖出
        sell = []
        for code in base_sell:
            if not self._is_winner_protected(code, current_temp, trade_step):
                sell.append(code)

        # 补足卖出数量：从持仓里按分数从低到高补齐（仍跳过受保护的）
        target_sell_n = min(self.n_drop, len(last_idx))
        if len(sell) < target_sell_n:
            last_asc = last.sort_values(ascending=True).index
            for code in last_asc:
                if code in sell:
                    continue
                if self._is_winner_protected(code, current_temp, trade_step):
                    continue
                sell.append(code)
                if len(sell) >= target_sell_n:
                    break

        buy = today[: (len(sell) + self.topk - len(last_idx))]

        # 卖出
        for code in current_stock_list:
            if not self.trade_exchange.is_stock_tradable(
                stock_id=code, start_time=trade_start_time, end_time=trade_end_time,
                direction=None if self.forbid_all_trade_at_limit else OrderDir.SELL
            ):
                continue

            if code in sell:
                bar = self.trade_calendar.get_freq()
                if current_temp.get_stock_count(code, bar=bar) < self.hold_thresh:
                    continue

                sell_amount = current_temp.get_stock_amount(code=code)
                sell_order = Order(
                    stock_id=code, amount=sell_amount,
                    start_time=trade_start_time, end_time=trade_end_time,
                    direction=Order.SELL,
                )
                if self.trade_exchange.check_order(sell_order):
                    sell_order_list.append(sell_order)
                    trade_val, trade_cost, _ = self.trade_exchange.deal_order(sell_order, position=current_temp)
                    cash += trade_val - trade_cost

                    # 清理状态
                    self._entry_price.pop(code, None)
                    self._protect_until_step.pop(code, None)
                    self._protect_disabled.discard(code)

        # 买入（等权）
        value = cash * self.risk_degree / len(buy) if len(buy) > 0 else 0.0
        for code in buy:
            if not self.trade_exchange.is_stock_tradable(
                stock_id=code, start_time=trade_start_time, end_time=trade_end_time,
                direction=None if self.forbid_all_trade_at_limit else OrderDir.BUY
            ):
                continue

            buy_price = self.trade_exchange.get_deal_price(
                stock_id=code, start_time=trade_start_time, end_time=trade_end_time, direction=OrderDir.BUY
            )
            buy_amount = value / buy_price
            factor = self.trade_exchange.get_factor(stock_id=code, start_time=trade_start_time, end_time=trade_end_time)
            buy_amount = self.trade_exchange.round_amount_by_trade_unit(buy_amount, factor)

            buy_order = Order(
                stock_id=code, amount=buy_amount,
                start_time=trade_start_time, end_time=trade_end_time,
                direction=Order.BUY,
            )
            buy_order_list.append(buy_order)

            # 记录入场价（重置保护状态）
            self._entry_price[code] = float(buy_price)
            self._protect_until_step.pop(code, None)
            self._protect_disabled.discard(code)

        return TradeDecisionWO(sell_order_list + buy_order_list, self)


import copy
import numpy as np
import pandas as pd

from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.backtest.decision import Order, OrderDir, TradeDecisionWO
from qlib.data import D


class RegimeSwitchWinnerProtectTopkDropoutStrategy(TopkDropoutStrategy):
    """
    赢家保护（区间触发 + 超过上限永不保护）+ 大盘下行关闭保护

    - 仅当 pnl ∈ [protect_profit_low, protect_profit_high] 才触发/生效保护
    - 第一次进入区间时触发保护窗口 protect_days 个交易日（含触发日）
    - 一旦 pnl > protect_profit_high：本次持仓期间永久取消保护（直到卖出）
    - 若 market 20日收益 < mom_threshold：当日关闭保护（不触发、不生效；并清空已触发窗口）
    """

    def __init__(
        self,
        *args,
        protect_profit_low=0.05,
        protect_profit_high=0.10,
        protect_days=1,
        market_index="SH000300",
        mom_window=20,
        mom_threshold=0.0,
        start_time=None,
        end_time=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.protect_profit_low = float(protect_profit_low)
        self.protect_profit_high = float(protect_profit_high)
        self.protect_days_up = int(protect_days)      # 上行/非下行时的保护天数
        self.protect_days_down = 0                    # 下行时：关闭保护
        self._cur_protect_days = self.protect_days_up

        assert self.protect_profit_low < self.protect_profit_high

        self.market_index = market_index
        self.mom_window = int(mom_window)
        self.mom_threshold = float(mom_threshold)

        # 记录入场价 / 保护窗口 / 永久禁用
        self._entry_price = {}
        self._protect_until_step = {}
        self._protect_disabled = set()

        # 预取指数收盘价并算动量（必须传 start/end 才能一次性取齐）
        if start_time is None or end_time is None:
            raise ValueError("Please pass start_time and end_time to strategy for market regime switch.")
        self._mom = self._build_mom_series(start_time, end_time)

    def _build_mom_series(self, start_time: str, end_time: str) -> pd.Series:
        # 留个 buffer，确保能算出前20个交易日动量
        st = pd.Timestamp(start_time) - pd.Timedelta(days=120)
        st = st.strftime("%Y-%m-%d")

        df = D.features([self.market_index], ["$close"], start_time=st, end_time=end_time).reset_index()
        close_col = df.columns[-1]
        s = df.pivot(index="datetime", columns="instrument", values=close_col)[self.market_index]
        s.index = pd.to_datetime(s.index).normalize()
        s = s.sort_index().astype(float)

        mom = s.pct_change(self.mom_window)
        return mom

    def _mom_at(self, ref_time) -> float:
        """ref_time 可能不是交易日，取 <=ref_time 的最后一个交易日"""
        ref = pd.Timestamp(ref_time).normalize()
        idx = self._mom.index
        if ref in idx:
            v = self._mom.loc[ref]
            return float(v) if np.isfinite(v) else np.nan

        pos = np.searchsorted(idx.values, ref.to_datetime64(), side="right") - 1
        if pos < 0:
            return np.nan
        v = self._mom.iloc[pos]
        return float(v) if np.isfinite(v) else np.nan

    def _update_regime(self, pred_end_time, trade_step: int):
        """
        用“前一交易日”的20日动量判断是否下行：
        - 下行：关闭保护，并清空已触发的保护窗口（立刻可卖）
        - 非下行：打开保护
        """
        m = self._mom_at(pred_end_time)
        down = (np.isfinite(m) and (m < self.mom_threshold))

        if down:
            self._cur_protect_days = self.protect_days_down  # 0
            # 关键：下行时直接取消正在保护的窗口，避免“捂住不该捂的”
            self._protect_until_step.clear()
        else:
            self._cur_protect_days = self.protect_days_up

    def _sync_state(self, pos):
        cur = set(pos.get_stock_list())

        for k in list(self._entry_price.keys()):
            if k not in cur:
                self._entry_price.pop(k, None)

        for k in list(self._protect_until_step.keys()):
            if k not in cur:
                self._protect_until_step.pop(k, None)

        self._protect_disabled = {k for k in self._protect_disabled if k in cur}

        for k in cur:
            self._entry_price.setdefault(k, float(pos.get_stock_price(k)))

    def _is_winner_protected(self, code, pos, trade_step: int) -> bool:
        # 下行：保护关闭
        if self._cur_protect_days <= 0:
            return False

        self._sync_state(pos)

        if code in self._protect_disabled:
            return False

        ep = self._entry_price.get(code, None)
        if ep is None or ep <= 0:
            return False

        cp = float(pos.get_stock_price(code))
        pnl = cp / ep - 1.0

        # 超过上限：永久取消保护
        if pnl > self.protect_profit_high:
            self._protect_disabled.add(code)
            self._protect_until_step.pop(code, None)
            return False

        # 未到下限：不保护
        if pnl < self.protect_profit_low:
            return False

        # 触发窗口（只触发一次，不滚动延长）
        if code not in self._protect_until_step:
            self._protect_until_step[code] = trade_step + self._cur_protect_days - 1

        until = self._protect_until_step.get(code, None)
        return (until is not None) and (trade_step <= until)

    def generate_trade_decision(self, execute_result=None):
        trade_step = self.trade_calendar.get_trade_step()
        trade_start_time, trade_end_time = self.trade_calendar.get_step_time(trade_step)

        # qlib 原生 TopkDropoutStrategy 用 shift=1 的信号
        pred_start_time, pred_end_time = self.trade_calendar.get_step_time(trade_step, shift=1)

        # 更新当日regime（用 pred_end_time，也就是“前一交易日”）
        self._update_regime(pred_end_time, trade_step)

        pred_score = self.signal.get_signal(start_time=pred_start_time, end_time=pred_end_time)
        if pred_score is None:
            return TradeDecisionWO([], self)
        if isinstance(pred_score, pd.DataFrame):
            pred_score = pred_score.iloc[:, 0]

        current_temp = copy.deepcopy(self.trade_position)
        sell_order_list = []
        buy_order_list = []

        cash = current_temp.get_cash()
        current_stock_list = current_temp.get_stock_list()

        last = pred_score.reindex(current_stock_list).sort_values(ascending=False)
        last_idx = last.index

        today = pred_score[~pred_score.index.isin(last_idx)].sort_values(ascending=False).index
        today = list(today[: (self.n_drop + self.topk - len(last_idx))])

        comb = pred_score.reindex(last_idx.union(pd.Index(today))).sort_values(ascending=False).index
        base_sell = list(last_idx[last_idx.isin(comb[-self.n_drop:])])

        # 过滤掉受保护的卖出
        sell = []
        for code in base_sell:
            if not self._is_winner_protected(code, current_temp, trade_step):
                sell.append(code)

        # 补足卖出数量
        target_sell_n = min(self.n_drop, len(last_idx))
        if len(sell) < target_sell_n:
            last_asc = last.sort_values(ascending=True).index
            for code in last_asc:
                if code in sell:
                    continue
                if self._is_winner_protected(code, current_temp, trade_step):
                    continue
                sell.append(code)
                if len(sell) >= target_sell_n:
                    break

        buy = today[: (len(sell) + self.topk - len(last_idx))]

        # 卖出
        for code in current_stock_list:
            if not self.trade_exchange.is_stock_tradable(
                stock_id=code, start_time=trade_start_time, end_time=trade_end_time,
                direction=None if self.forbid_all_trade_at_limit else OrderDir.SELL
            ):
                continue

            if code in sell:
                bar = self.trade_calendar.get_freq()
                if current_temp.get_stock_count(code, bar=bar) < self.hold_thresh:
                    continue

                sell_amount = current_temp.get_stock_amount(code=code)
                sell_order = Order(
                    stock_id=code, amount=sell_amount,
                    start_time=trade_start_time, end_time=trade_end_time,
                    direction=Order.SELL,
                )
                if self.trade_exchange.check_order(sell_order):
                    sell_order_list.append(sell_order)
                    trade_val, trade_cost, _ = self.trade_exchange.deal_order(sell_order, position=current_temp)
                    cash += trade_val - trade_cost

                    self._entry_price.pop(code, None)
                    self._protect_until_step.pop(code, None)
                    self._protect_disabled.discard(code)

        # 买入（等权）
        value = cash * self.risk_degree / len(buy) if len(buy) > 0 else 0.0
        for code in buy:
            if not self.trade_exchange.is_stock_tradable(
                stock_id=code, start_time=trade_start_time, end_time=trade_end_time,
                direction=None if self.forbid_all_trade_at_limit else OrderDir.BUY
            ):
                continue

            buy_price = self.trade_exchange.get_deal_price(
                stock_id=code, start_time=trade_start_time, end_time=trade_end_time, direction=OrderDir.BUY
            )
            buy_amount = value / buy_price
            factor = self.trade_exchange.get_factor(stock_id=code, start_time=trade_start_time, end_time=trade_end_time)
            buy_amount = self.trade_exchange.round_amount_by_trade_unit(buy_amount, factor)

            buy_order = Order(
                stock_id=code, amount=buy_amount,
                start_time=trade_start_time, end_time=trade_end_time,
                direction=Order.BUY,
            )
            buy_order_list.append(buy_order)

            self._entry_price[code] = float(buy_price)
            self._protect_until_step.pop(code, None)
            self._protect_disabled.discard(code)

        return TradeDecisionWO(sell_order_list + buy_order_list, self)


def tradability_stats(pred_score: pd.DataFrame, start_time: str, end_time: str):
    df_sig = pred_score.reset_index().copy()
    # 统一格式，避免 reindex 对不上
    df_sig["datetime"] = pd.to_datetime(df_sig["datetime"]).dt.normalize()
    df_sig["instrument"] = df_sig["instrument"].astype(str).str.strip()

    inst = df_sig["instrument"].unique().tolist()

    feat = D.features(
        instruments=inst,
        fields=["$close", "$amount"],
        start_time=start_time,
        end_time=end_time,
    ).reset_index()

    # 统一格式
    feat["datetime"] = pd.to_datetime(feat["datetime"]).dt.normalize()
    feat["instrument"] = feat["instrument"].astype(str).str.strip()
    feat = feat.rename(columns={feat.columns[-2]: "close", feat.columns[-1]: "amount"})  # 兼容列名

    m = df_sig.merge(feat, on=["datetime", "instrument"], how="left")

    bad = m["close"].isna() | (m["close"] <= 0) | m["amount"].isna() | (m["amount"] <= 0)

    print("\n[Tradability stats - merge]")
    print("signal rows:", len(m))
    print("matched rows:", int(m["close"].notna().sum()))
    print("bad rows   :", int(bad.sum()))
    print("bad ratio  :", float(bad.mean()))

    daily_bad = bad.groupby(m["datetime"]).mean()
    print("daily bad ratio: mean", float(daily_bad.mean()),
          "p90", float(np.percentile(daily_bad.values, 90)),
          "max", float(daily_bad.max()))


def topk_turnover_stats(pred_score: pd.DataFrame, topk: int = 30):
    """
    统计相邻两天 topK 持仓集合重叠率
    - overlap 越高 -> 换手越低 -> 成本越低
    """
    df = pred_score.reset_index()
    df = df.sort_values(["datetime", "score"], ascending=[True, False])

    daily_sets = df.groupby("datetime").head(topk).groupby("datetime")["instrument"].apply(lambda s: set(s.tolist()))
    days = list(daily_sets.index)

    if len(days) < 2:
        print("\n[TopK turnover stats] not enough days")
        return

    overlaps = []
    for i in range(1, len(days)):
        a = daily_sets.iloc[i - 1]
        b = daily_sets.iloc[i]
        overlaps.append(len(a & b) / topk)

    overlaps = np.asarray(overlaps, dtype=float)
    print("\n[TopK turnover stats]")
    print(f"topk={topk} overlap mean={overlaps.mean():.3f} p10={np.percentile(overlaps,10):.3f} p90={np.percentile(overlaps,90):.3f} min={overlaps.min():.3f}")
    print(f"implied daily turnover approx mean={1 - overlaps.mean():.3f}")


@dataclass
class ModelConfig:
    """模型预测配置"""
    # 数据路径配置
    universe: str = 'csi300'  # 或 'csi800'
    prefix: str = 'opensource'  # 或 'original'
    seed: int = 0
    model_dir: str = 'model'
    data_dir: str = 'data'
    
    # 模型参数（需要与训练时保持一致）
    d_feat: int = 158
    d_model: int = 256
    t_nhead: int = 4
    s_nhead: int = 2
    dropout: float = 0.5
    gate_input_start_index: int = 158
    gate_input_end_index: int = 221
    GPU: int = 0
    
    @property
    def model_path(self) -> str:
        """模型文件路径"""
        return f'{self.model_dir}/{self.universe}_{self.prefix}_{self.seed}_best.pkl'
    
    @property
    def test_data_path(self) -> str:
        """测试数据路径"""
        return f'{self.data_dir}/{self.prefix}/{self.universe}_dl_test.pkl'
    
    @property
    def beta(self) -> int:
        """根据universe自动确定beta值"""
        if self.universe == 'csi300':
            return 5
        elif self.universe == 'csi800':
            return 2
        else:
            return 5


@dataclass
class BacktestConfig:
    """回测配置"""
    # 回测时间范围
    start_time: str = "2020-07-01"
    end_time: str = "2022-12-31"
    freq: str = "day"
    
    # qlib配置
    qlib_data_dir: Optional[str] = None  # 默认: ~\qlib_data\cn_data
    region: str = "cn"  # qlib区域配置
    
    # 策略参数
    topk: int = 30
    n_drop: int = 30
    
    # 回测参数
    benchmark: str = "SH000300"  # 基准指数代码（沪深300）
    account: float = 100000000  # 初始资金（1亿）
    use_detailed: bool = True  # 是否使用详细的backtest函数
    
    # 交易成本配置
    limit_threshold: float = 0.095
    deal_price: str = "close"
    # 之前的设置，AI设高了
    # open_cost: float = 0.0005
    # close_cost: float = 0.0015
    open_cost: float = 0.00026  # 万2.5佣金+万0.1过户费
    close_cost: float = 0.00076  # 万2.5佣金+万0.1过户费+万5印花税
    min_cost: float = 5


def load_model_and_predict(config: ModelConfig) -> pd.DataFrame:
    """
    加载训练好的模型并进行预测
    
    Parameters
    ----------
    config : ModelConfig
        模型预测配置
        
    Returns
    -------
    pred_score : pd.DataFrame
        预测分数，格式为DataFrame，索引为(datetime, instrument)，包含score列
    """
    # 加载测试数据
    print(f"加载测试数据: {config.test_data_path}")
    with open(config.test_data_path, 'rb') as f:
        dl_test = pickle.load(f)
    
    # DatetimeMajorWrapper must be applied before predict so that
    # DailyBatchSamplerRandom yields cross-sectional (datetime-major) batches.
    # Without it the batch order is instrument-major and the cross-sectional
    # attention receives a random mix of dates, degrading IC significantly.
    dl_test = DatetimeMajorWrapper(dl_test)
    gate_input_end_index = np.asarray(dl_test[0]).shape[1]-1
    # 初始化模型
    print(f"加载模型: {config.model_path}")
    model = MASTERModel(
        d_feat=config.d_feat,
        d_model=config.d_model,
        t_nhead=config.t_nhead,
        s_nhead=config.s_nhead,
        T_dropout_rate=config.dropout,
        S_dropout_rate=config.dropout,
        beta=config.beta,
        gate_input_end_index=gate_input_end_index,
        gate_input_start_index=config.gate_input_start_index,
        n_epochs=1,  # 不需要训练，只是初始化
        lr=1e-5,
        GPU=config.GPU,
        seed=config.seed,
        train_stop_loss_thred=0.95,
        save_path=config.model_dir,
        save_prefix=''
    )
    
    # 加载模型参数
    model.load_param(config.model_path)
    # 修复：load_param会将fitted设为字符串，需要设置为>=0的数值以便predict方法正常工作
    # 设置为0表示模型已加载（训练过的模型）
    model.fitted = 1
    
    # 进行预测
    print("开始预测...")
    predictions, metrics = model.predict(dl_test)
    
    print("预测完成，指标如下:")
    print(f"IC: {metrics['IC']:.4f}")
    print(f"ICIR: {metrics['ICIR']:.4f}")
    print(f"RIC: {metrics['RIC']:.4f}")
    print(f"RICIR: {metrics['RICIR']:.4f}")
    
    # 将预测结果转换为qlib需要的格式
    # predictions是一个pd.Series，索引是MultiIndex(datetime, instrument)
    # 需要转换为DataFrame，包含score列
    pred_score = predictions.to_frame(name='score')
    
    return pred_score


def calculate_metrics_from_predictions(predictions: pd.Series, dl_test) -> dict:
    """
    根据预测结果和测试数据计算 IC、ICIR、RIC、RICIR 指标
    
    Parameters
    ----------
    predictions : pd.Series
        预测结果，索引为 MultiIndex(datetime, instrument)
    dl_test
        测试数据集
        
    Returns
    -------
    metrics : dict
        包含 IC、ICIR、RIC、RICIR 的字典
    """
    print("计算预测指标...")
    # 从 dl_test 中提取标签
    sampler = DailyBatchSamplerRandom(dl_test, shuffle=False)
    base_index = dl_test.get_index()
    
    labels = []
    idx_parts = []
    for batch_pos in sampler.daily_batches:
        xs = [np.asarray(dl_test[int(i)]) for i in batch_pos]
        x = np.stack(xs, axis=0)
        data = torch.from_numpy(x)
        label = data[:, -1, -1].detach().cpu().numpy().reshape(-1)
        labels.append(label)
        idx_parts.append(base_index.take(batch_pos))
    
    all_labels = np.concatenate(labels) if len(labels) else np.array([], dtype=float)
    all_index = idx_parts[0]
    for part in idx_parts[1:]:
        all_index = all_index.append(part)
    
    # 将标签转换为 Series，索引与预测结果对齐
    label_series = pd.Series(all_labels, index=all_index)
    
    # 对齐预测结果和标签（使用交集索引）
    common_index = predictions.index.intersection(label_series.index)
    aligned_pred = predictions.loc[common_index]
    aligned_label = label_series.loc[common_index]
    
    # 按日期分组计算每日的 IC 和 RIC
    ic = []
    ric = []
    for date in aligned_pred.index.get_level_values("datetime").unique():
        date_mask = aligned_pred.index.get_level_values("datetime") == date
        pred_day = aligned_pred[date_mask].values
        label_day = aligned_label[date_mask].values
        
        daily_ic, daily_ric = calc_ic(pred_day, label_day)
        ic.append(daily_ic)
        ric.append(daily_ric)
    
    # 计算最终指标
    metrics = {
        'IC': np.nanmean(ic),
        'ICIR': np.nanmean(ic) / (np.nanstd(ic) + 1e-12),
        'RIC': np.nanmean(ric),
        'RICIR': np.nanmean(ric) / (np.nanstd(ric) + 1e-12)
    }
    
    return metrics


def load_model_and_predict_ensemble(config: ModelConfig, seeds=(0,1,2,3,4)) -> pd.DataFrame:
    with open(config.test_data_path, 'rb') as f:
        dl_test = pickle.load(f)
    gate_input_end_index = np.asarray(dl_test[0]).shape[1] - 1

    preds = []
    for sd in seeds:
        mp = f'{config.model_dir}/{config.universe}_{config.prefix}_{sd}_best.pkl'
        if not os.path.exists(mp):
            print(f"模型文件不存在,跳过: {mp}")
            continue
        print(f"加载模型 {sd}: {mp}")
        model = MASTERModel(
            d_feat=config.d_feat, d_model=config.d_model,
            t_nhead=config.t_nhead, s_nhead=config.s_nhead,
            T_dropout_rate=config.dropout, S_dropout_rate=config.dropout,
            beta=config.beta,
            gate_input_end_index=gate_input_end_index,
            gate_input_start_index=config.gate_input_start_index,
            n_epochs=1, lr=1e-5, GPU=config.GPU, seed=sd,
            train_stop_loss_thred=0.95, save_path=config.model_dir, save_prefix=''
        )
        model.load_param(mp)
        model.fitted = 1
        p, _ = model.predict(dl_test)          # pd.Series
        preds.append(p.rename(f"s{sd}"))


    # df = pd.concat(preds, axis=1).dropna()
    # df["score"] = df.mean(axis=1)             # 简单均值集成
    def cs_zscore(s):
        return s.groupby(level=0).transform(lambda x: (x - x.mean()) / (x.std() + 1e-12))

    # preds: list[pd.Series] 每个 seed 一个
    zs = [cs_zscore(p) for p in preds]
    df = pd.concat(zs, axis=1)
    score = df.median(axis=1)

    # 最后再 cs_zscore 一次，保证输出稳定
    score = cs_zscore(score)

    # 计算集成后的指标
    # ensemble_pred = df["score"]
    ensemble_pred = score
    metrics = calculate_metrics_from_predictions(ensemble_pred, dl_test)
    
    print("集成预测完成，指标如下:")
    print(f"IC: {metrics['IC']:.4f}")
    print(f"ICIR: {metrics['ICIR']:.4f}")
    print(f"RIC: {metrics['RIC']:.4f}")
    print(f"RICIR: {metrics['RICIR']:.4f}")
    
    # return df[["score"]]
    return score.to_frame(name='score')


def run_backtest(pred_score: pd.DataFrame, config: BacktestConfig):
    """
    使用qlib进行回测
    
    Parameters
    ----------
    pred_score : pd.DataFrame
        预测分数，索引为(datetime, instrument)，包含score列
    config : BacktestConfig
        回测配置
        
    Returns
    -------
    report : pd.DataFrame
        回测报告
    positions : pd.DataFrame
        持仓信息
    analysis_df : pd.DataFrame
        风险分析结果
    """
    # 初始化qlib
    if config.qlib_data_dir:
        qlib.init(provider_uri=config.qlib_data_dir, region=config.region)
    else:
        # 如果没有指定，尝试使用默认路径
        print("警告: 未指定qlib数据目录，尝试使用默认路径")
        try:
            qlib.init(region=config.region)
        except:
            print(f"请先初始化qlib: qlib.init(provider_uri='your_qlib_data_dir', region='{config.region}')")
            raise
    
    # 配置策略
    STRATEGY_CONFIG = {
        "topk": config.topk,
        "n_drop": config.n_drop,
        "signal": pred_score['score'],  # 传入Series格式的信号
    }
    
    # 创建策略对象
    # strategy_obj = TopkDropoutStrategy(**STRATEGY_CONFIG)

    # 盈利卖出保护（测试结果：收益会变好）
    strategy_obj = WinnerProtectTopkDropoutStrategy(
        **STRATEGY_CONFIG,
        protect_profit_low=0.05,      # 浮盈>=5% 开始保护
        protect_profit_high=0.10,     # 浮盈>=10% 永久取消保护
        protect_days=1,               # 保护3个交易日
    )

    # 大盘下行关闭盈利保护（测试结果：收益会变差）
    # strategy_obj = RegimeSwitchWinnerProtectTopkDropoutStrategy(
    #     **STRATEGY_CONFIG,
    #     protect_profit_low=0.05,
    #     protect_profit_high=0.10,
    #     protect_days=1,
    #     market_index=config.benchmark,  # CSI300 用 SH000300
    #     mom_window=30,
    #     mom_threshold=0.0,
    #     start_time=config.start_time,
    #     end_time=config.end_time,
    # )
    
    if config.use_detailed:
        # 使用详细的backtest函数，支持更多参数
        EXECUTOR_CONFIG = {
            "time_per_step": config.freq,
            "generate_portfolio_metrics": True,
        }
        
        backtest_config = {
            "start_time": config.start_time,
            "end_time": config.end_time,
            "account": config.account,
            "benchmark": config.benchmark,
            "exchange_kwargs": {
                "freq": config.freq,
                "limit_threshold": config.limit_threshold,
                "deal_price": config.deal_price,
                "open_cost": config.open_cost,
                "close_cost": config.close_cost,
                "min_cost": config.min_cost,
            },
        }
        
        executor_obj = executor.SimulatorExecutor(**EXECUTOR_CONFIG)
        portfolio_metric_dict, indicator_dict = backtest(
            executor=executor_obj,
            strategy=strategy_obj,
            **backtest_config
        )
        
        # 获取回测结果（参考官方示例）
        analysis_freq = "{0}{1}".format(*Freq.parse(config.freq))
        report, positions = portfolio_metric_dict.get(analysis_freq)
    else:
        # 使用简单的backtest_daily函数
        report, positions = backtest_daily(
            start_time=config.start_time,
            end_time=config.end_time,
            strategy=strategy_obj,
        )
        analysis_freq = config.freq

    # 打印回测基本信息
    print(f"\n开始回测: {config.start_time} 到 {config.end_time}")
    print(f"频率: {analysis_freq}")
    print(f"策略参数: topk={config.topk}, n_drop={config.n_drop}")
    print(f"基准指数: {config.benchmark}")
    
    
    # 风险分析
    print("\n进行风险分析...")
    analysis = dict()
    analysis["excess_return_without_cost"] = risk_analysis(
        report["return"] - report["bench"],
        freq=analysis_freq
    )
    analysis["excess_return_with_cost"] = risk_analysis(
        report["return"] - report["bench"] - report["cost"],
        freq=analysis_freq
    )
    
    analysis_df = pd.concat(analysis)  # type: pd.DataFrame
    
    return report, positions, analysis_df


def print_results(report: pd.DataFrame, analysis_df: pd.DataFrame):
    print("\n" + "="*60)
    print("回测结果")
    print("="*60)
    print("\n风险分析结果:")
    pprint(analysis_df)

    # 计算累计收益（复利）
    # report["return"] 是日收益率，report["cost"] 是日成本（同口径）
    ret = report["return"].fillna(0.0)
    cost = report["cost"].fillna(0.0) if "cost" in report.columns else 0.0

    nav_wo_cost = (1.0 + ret).cumprod()
    nav_w_cost = (1.0 + ret - cost).cumprod()

    total_ret_wo_cost = float(nav_wo_cost.iloc[-1] - 1.0)
    total_ret_w_cost = float(nav_w_cost.iloc[-1] - 1.0)

    # # 计算策略最大回撤（不含成本）
    # running_max_wo_cost = nav_wo_cost.expanding().max()
    # drawdown_wo_cost = (nav_wo_cost - running_max_wo_cost) / running_max_wo_cost
    # max_drawdown_wo_cost = float(drawdown_wo_cost.min())

    # 计算策略最大回撤（含成本）
    running_max_w_cost = nav_w_cost.expanding().max()
    drawdown_w_cost = (nav_w_cost - running_max_w_cost) / running_max_w_cost
    max_drawdown_w_cost = float(drawdown_w_cost.min())

    # 年化收益率，不含成本
    nav = (1 + report["return"]).cumprod()
    years = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr_wo_cost = nav.iloc[-1] ** (1/years) - 1

    # 年化收益率，含成本
    nav = (1 + report["return"] - report["cost"]).cumprod()
    years = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr_w_cost = nav.iloc[-1] ** (1/years) - 1

    print("\n回测报告摘要:")
    print(f"累计收益率(不含成本, 复利): {total_ret_wo_cost:.4f}")
    print(f"年化收益率(不含成本, 复利): {cagr_wo_cost:.4f}")
    print(f"累计收益率(含成本, 复利):   {total_ret_w_cost:.4f}")
    print(f"年化收益率(含成本, 复利): {cagr_w_cost:.4f}")
    print(f"策略最大回撤(含成本): {max_drawdown_w_cost:.4f}")

    try:
        annualized_return = analysis_df.loc[('excess_return_with_cost', 'annualized_return'), 'risk']
        information_ratio = analysis_df.loc[('excess_return_with_cost', 'information_ratio'), 'risk']
        excess_max_drawdown = analysis_df.loc[('excess_return_with_cost', 'max_drawdown'), 'risk']

        print(f"年化超额收益率(含成本): {annualized_return:.4f}")
        print(f"超额收益最大回撤(含成本):   {excess_max_drawdown:.4f}")
        print(f"超额收益信息比率(含成本):   {information_ratio:.4f}")
    except (KeyError, IndexError) as e:
        print(f"无法获取部分指标: {e}")

    print("\n回测完成!")


def main(stage, universe, exp_no, seed=0, ensemble=False):
    """
    主函数：示例用法
    """
    # ── 路径配置 ─────────────────────────────────────────────────────────────
    # reproduce 阶段：直接使用 MASTER/data 和 MASTER/model，不依赖 output 子目录
    if stage in ('reproduce', 'reproduce_download', 'reproduce_new'):
        data_dir = os.path.join(_MASTER_DIR, 'data')
        model_dir = os.path.join(_MASTER_DIR, 'model')
        prefix = 'new' if stage == 'reproduce_new' else 'qlib'
    else:
        data_dir = f'{OUTPUT_DIR}/{stage}/data'
        model_dir = f'{OUTPUT_DIR}/{stage}/model_{exp_no}'
        prefix = 'opensource'

    # qlib 行情数据路径
    _QLIB_DATA_DIR = '/data/jcl/qt_v2/workspace_master/dataset/qlib_bin'

    if universe == 'csi300':
        benchmark = "SH000300"
    elif universe == 'csi800':
        benchmark = "SH000906"
    elif universe == 'csi500':
        benchmark = "SH000905"
    
    if stage in ('reproduce', 'reproduce_download', 'reproduce_new'):
        start_time = "2020-07-01"
        end_time = "2022-12-31"
    elif stage == 'dev':
        start_time = "2023-01-01"
        end_time = "2025-12-31"
    elif stage == 'dev_bear':
        start_time = "2021-02-10"
        end_time = "2024-02-09"
    elif stage == 'production':
        start_time = "2025-11-01"
        end_time = "2026-1-31"
        
    # ========== 配置参数 ==========
    # 创建模型预测配置
    model_config = ModelConfig(
        universe=universe,  # csi300 或 'csi800'
        prefix=prefix,
        seed=seed,
        model_dir=model_dir,
        data_dir=data_dir,
    )
    
    # 创建回测配置
    backtest_config = BacktestConfig(
        start_time=start_time,
        end_time=end_time,
        qlib_data_dir=_QLIB_DATA_DIR,
        region="cn",
        topk=10,    # 优化策略：Top10 持仓，低换手
        n_drop=2,   # 每次最多换 2 只，配合盈利保护
        benchmark=benchmark,  # 沪深300指数
        account=100000000,  # 1亿初始资金
        use_detailed=True,
        deal_price="close",
    )
    
    # ========== 执行回测 ==========
    try:
        # 1. 加载模型并预测
        if ensemble == False:
            pred_score = load_model_and_predict(model_config)
        else:
            pred_score = load_model_and_predict_ensemble(model_config, seeds=(0,1,2,3,4))
        
        # 初始化 qlib（统计需要用 D.features）
        qlib.init(provider_uri=_QLIB_DATA_DIR, region="cn")

        # 任选其一
        # pred_score = ema_smooth_score(pred_score, alpha=0.7)
        # 或
        # pred_score = add_trend_overlay(pred_score, start_time, end_time, mom_win=3, trend_win=20, lam_mom=0.2, lam_trend=0.1)

        backtest_output_dir = f"{OUTPUT_DIR}/backtest"
        os.makedirs(backtest_output_dir, exist_ok=True)
        pred_score.to_csv(f'{backtest_output_dir}/pred_score.csv')
        print(f"预测结果已保存到 {backtest_output_dir}/pred_score.csv")


        tradability_stats(pred_score, start_time, end_time)
        topk_turnover_stats(pred_score, topk=backtest_config.topk)
        
        # 2. 运行回测
        report, positions, analysis_df = run_backtest(pred_score, backtest_config)
        
        # 3. 输出结果
        print_results(report, analysis_df)


        # report 的 index 通常是 date/datetime
        # analysis_position.report_graph(report)
        # analysis_position.risk_analysis_graph(analysis_df)
        # # cumulative_return_graph 需要 report_normal 和 label_data 参数，如果没有基准报告和标签数据，可以传 None
        # analysis_position.cumulative_return_graph(report, report_normal=None, label_data=None)
        # plt.show()
        plot_nav_curve(report, title=f"NAV(Net Asset Value) {start_time}~{end_time}")

    except FileNotFoundError as e:
        print(f"错误: 文件未找到 - {e}")
        print("请确保模型文件和数据文件路径正确")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='回测')
    parser.add_argument('--stage', type=str, choices=['reproduce', 'reproduce_new', 'dev', 'dev_bear', 'production'], 
                        required=True, help='stage')
    parser.add_argument('--universe', type=str, default='csi300', choices=['csi300','csi800','csi500'], help='universe')
    parser.add_argument('--exp_no', type=str, default='16', help='exp_no')
    parser.add_argument('--seed', type=int, default=0, help='seed')
    parser.add_argument('--ensemble', action='store_true', help='ensemble')
    args = parser.parse_args()
    main(args.stage, args.universe, args.exp_no, args.seed, args.ensemble)