"""
prepare_data.py (stub)
=======================
backtest.py 顶部有 `from prepare_data import FileLazyTSDataset`，
用于兼容旧版 pickle 反序列化(__main__.FileLazyTSDataset)。
本项目(master_v1)的预测结果是直接从 train_master.py 产出的 pd.Series pkl，
不涉及 FileLazyTSDataset 反序列化，这里提供一个占位类满足 import 即可。
"""


class FileLazyTSDataset:
    """占位类：仅用于满足 backtest.py 的 import，不在 master_v1 流程中实际使用。"""

    def __init__(self, data_path=None, lookback=8):
        self.data_path = data_path
        self.lookback = lookback

    def __getitem__(self, idx):
        raise NotImplementedError("stub FileLazyTSDataset is not functional")

    def __len__(self):
        return 0
