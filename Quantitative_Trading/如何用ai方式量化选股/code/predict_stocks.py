#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用训练好的模型对训练集外的数据进行预测选股

使用方法:
    # 对最新日期进行预测选股
    python predict_stocks.py future --experiment_name=workflow --topk=50
    
    # 对指定日期范围进行预测
    python predict_stocks.py future --experiment_name=workflow --start_time=2020-09-01 --end_time=2020-09-30 --topk=50
    
    # 使用指定的 recorder
    python predict_stocks.py future --recorder_id=d2c0c94e108d4436ba67311d5da466cd --experiment_name=workflow --topk=50
"""

import fire
import qlib
import pandas as pd
from pathlib import Path
from qlib.constant import REG_CN
from qlib.workflow import R
from qlib.workflow.online.update import RMDLoader
from qlib.data import D
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP

import warnings
warnings.filterwarnings("ignore")

def _init_qlib(provider_uri, region):
    """初始化 qlib，设置正确的 exp_manager URI"""
    # 设置 exp_manager URI，指向 examples 目录下的 mlruns
    script_dir = Path(__file__).parent
    examples_dir = script_dir.parent.parent  # 从 benchmarks/LightGBM 回到 examples
    mlruns_path = examples_dir / "mlruns"
    
    qlib.init(
        provider_uri=provider_uri, 
        region=region,
        exp_manager={
            "class": "MLflowExpManager",
            "module_path": "qlib.workflow.expm",
            "kwargs": {
                "uri": str(mlruns_path.resolve()),
                "default_exp_name": "workflow",
            }
        }
    )


def predict_future_stocks(
    experiment_id=None,
    recorder_id=None,
    experiment_name="workflow",
    start_time=None,
    end_time=None,
    topk=50,
    provider_uri="~/.qlib/qlib_data/cn_data",
    region=REG_CN,
):
    """
    使用训练好的模型对指定日期进行预测选股
    
    这个方法会：
    1. 从 recorder 加载训练好的模型和数据集配置
    2. 使用相同的数据处理流程，对指定时间范围的数据进行预测
    3. 使用模型进行预测
    4. 按日期选择得分最高的 topk 只股票
    
    注意：预测时间范围由 start_time 和 end_time 参数决定，或使用最新可用日期
    
    Parameters
    ----------
    experiment_id : str
        实验 ID，如果提供则使用该实验
    recorder_id : str
        Recorder ID，如果提供则使用该 recorder
    experiment_name : str
        实验名称，默认 "workflow"
    start_time : str
        预测开始时间，格式 "YYYY-MM-DD"
        - 如果 start_time 和 end_time 都为 None，则都使用最新可用日期（单日预测）
        - 如果只指定了 end_time，start_time 也使用 end_time（单日预测）
        - 如果只指定了 start_time，end_time 使用最新可用日期
    end_time : str
        预测结束时间，格式 "YYYY-MM-DD"
        - 如果 start_time 和 end_time 都为 None，则都使用最新可用日期（单日预测）
        - 如果只指定了 end_time，start_time 也使用 end_time（单日预测）
        - 如果只指定了 start_time，end_time 使用最新可用日期
    topk : int
        选择前 topk 只股票，默认 50
    provider_uri : str
        数据路径
    region : str
        区域，默认 REG_CN
    """
    # 初始化 qlib
    _init_qlib(provider_uri, region)
    
    # 获取 recorder
    if recorder_id:
        recorder = R.get_recorder(recorder_id=recorder_id, experiment_name=experiment_name)
    elif experiment_id:
        # 通过 experiment_id 查找 recorder
        # 先获取所有实验，找到匹配的 experiment_id
        experiments = R.list_experiments()
        recorder = None
        for exp_name, exp in experiments.items():
            if exp.id == experiment_id:
                # 获取该实验的所有 recorder，选择最新的
                recorders = R.list_recorders(experiment_name=exp_name)
                if recorders:
                    recorder = list(recorders.values())[-1]  # 获取最新的 recorder
                    break
        if recorder is None:
            raise ValueError(f"找不到 experiment_id={experiment_id} 的 recorder")
    else:
        recorder = R.get_recorder(experiment_name=experiment_name)
    
    print(f"使用 Recorder ID: {recorder.info['id']}")
    print(f"实验 ID: {recorder.experiment_id}")
    
    # 加载训练好的模型
    model = recorder.load_object("params.pkl")
    print(f"\n模型类型: {type(model).__name__}")
    
    # 加载训练时的数据集（用于获取 handler 配置）
    train_dataset = recorder.load_object("dataset")
    
    # 获取可用的最新日期
    calendar = D.calendar()
    latest_available_date = calendar[-1]
    print(f"数据最新可用日期: {latest_available_date}")
    
    # 确定预测时间范围
    # 如果都没有指定，使用最新可用日期（单日预测）
    if start_time is None and end_time is None:
        start_time = latest_available_date.strftime("%Y-%m-%d")
        end_time = latest_available_date.strftime("%Y-%m-%d")
    # 如果只指定了 end_time，start_time 也使用 end_time（单日预测）
    elif start_time is None:
        start_time = end_time
    # 如果只指定了 start_time，end_time 使用最新可用日期
    elif end_time is None:
        end_time = latest_available_date.strftime("%Y-%m-%d")
    
    print(f"\n预测时间范围: {start_time} 到 {end_time}")
    print(f"说明: 使用 {start_time} 的数据（特征），预测的是下一个交易日的收益")
    print(f"      （根据 Alpha158 的 label 定义：Ref($close, -2)/Ref($close, -1) - 1）")
    
    # 使用训练时的数据集，但更新时间范围
    # 通过 config 方法更新 handler 的时间范围和 segments
    train_dataset.config(
        handler_kwargs={
            "start_time": start_time,
            "end_time": end_time
        },
        segments={
            "test": (start_time, end_time)  # 新的时间范围
        }
    )
    # 重新设置数据（使用新的时间范围）
    train_dataset.setup_data(handler_kwargs={"init_type": DataHandlerLP.IT_LS})
    
    print(f"数据集配置完成，segment: {train_dataset.segments}")
    
    # 进行预测
    print("\n开始预测...")
    predictions = model.predict(train_dataset, segment="test")
    
    if isinstance(predictions, pd.Series):
        predictions = predictions.to_frame("score")
    
    print(f"\n预测完成，共 {len(predictions)} 条预测结果")
    print("\n预测结果示例（前10条）:")
    print(predictions.head(10))
    
    # 按日期分组，每天选择 topk 只股票
    print(f"\n按日期选择前 {topk} 只股票...")
    selected_stocks = []
    
    if isinstance(predictions.index, pd.MultiIndex):
        # 多级索引 (datetime, instrument)
        dates = predictions.index.get_level_values(0).unique()
        for date in dates:
            date_pred = predictions.loc[date]
            # 按分数降序排列，选择前 topk
            top_stocks = date_pred.nlargest(topk, "score")
            # 计算下一个交易日（用于说明预测的是哪一天）
            try:
                calendar = D.calendar()
                date_idx = calendar.get_loc(pd.Timestamp(date))
                if date_idx + 1 < len(calendar):
                    next_trading_day = calendar[date_idx + 1]
                    predict_date = next_trading_day.strftime("%Y-%m-%d")
                else:
                    predict_date = "下一个交易日"
            except:
                predict_date = "下一个交易日"
            
            selected_stocks.append({
                "data_date": str(date),  # 数据日期
                "predict_date": predict_date,  # 预测的交易日
                "stocks": top_stocks.index.tolist(),
                "scores": top_stocks["score"].tolist(),
                "stock_count": len(top_stocks)
            })
            print(f"\n数据日期: {date} -> 预测交易日: {predict_date}")
            print(f"选择的股票（前10只）:")
            print(top_stocks.head(10))
    else:
        # 单级索引，假设所有预测都是同一日期
        top_stocks = predictions.nlargest(topk, "score")
        selected_stocks.append({
            "date": "latest",
            "stocks": top_stocks.index.tolist(),
            "scores": top_stocks["score"].tolist(),
            "stock_count": len(top_stocks)
        })
        print(f"\n选择的股票（前10只）:")
        print(top_stocks.head(10))
    
    # 保存结果
    result_df = pd.DataFrame(selected_stocks)
    output_file = f"future_selected_stocks_top{topk}_{start_time}_{end_time}.csv"
    result_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n选股结果已保存到: {output_file}")
    
    # 保存详细预测结果
    pred_file = f"future_predictions_{start_time}_{end_time}.csv"
    predictions.to_csv(pred_file, encoding="utf-8-sig")
    print(f"详细预测结果已保存到: {pred_file}")
    
    # 如果是单日预测，也保存一个简化的选股列表
    if len(selected_stocks) == 1:
        stock_list = selected_stocks[0]["stocks"]
        stock_df = pd.DataFrame({
            "stock": stock_list,
            "score": selected_stocks[0]["scores"],
            "rank": range(1, len(stock_list) + 1)
        })
        simple_file = f"selected_stocks_list_top{topk}.csv"
        stock_df.to_csv(simple_file, index=False, encoding="utf-8-sig")
        print(f"选股列表已保存到: {simple_file}")
    
    print("\n预测和选股完成！")
    return None


if __name__ == "__main__":
    # 直接使用 predict_future_stocks 作为主函数
    fire.Fire(predict_future_stocks)

