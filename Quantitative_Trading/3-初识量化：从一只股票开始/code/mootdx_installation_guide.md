# mootdx 安装指南

## 安装环境
- **操作系统**: macOS Ventura
- **Python 版本**: Python 3.13.7
- **安装日期**: 2026年6月17日

## 完整安装命令

### 1. 创建独立的 Python 虚拟环境
```bash
python3 -m venv mootdx_env
```

### 2. 激活虚拟环境
```bash
source mootdx_env/bin/activate
```

### 3. 升级 pip 并安装 mootdx
```bash
pip install --upgrade pip
pip install mootdx
```

### 4. 验证安装
```bash
python -c "import mootdx; print('mootdx 版本:', mootdx.__version__)"
```

## 一键安装命令（合并版）
```bash
# 创建并激活虚拟环境，然后安装 mootdx
python3 -m venv mootdx_env && source mootdx_env/bin/activate && pip install --upgrade pip && pip install mootdx
```

## 安装结果

### 已安装的 mootdx 版本
- **mootdx**: 0.11.7

### 主要依赖包
- click: 8.4.1
- httpx: 0.25.2
- prettytable: 3.17.0
- py-mini-racer: 0.6.0
- tdxpy: 0.2.7
- tenacity: 8.5.0
- pandas: 3.0.3
- numpy: 2.4.6
- tqdm: 4.68.3

## 使用说明

### 激活虚拟环境
每次使用前需要激活虚拟环境：
```bash
source mootdx_env/bin/activate
```

### 退出虚拟环境
```bash
deactivate
```

### 基本使用示例
```python
from mootdx.quotes import Quotes

# 创建行情对象
client = Quotes.factory(market='std')

# 获取市场列表
markets = client.markets()
print(markets)
```

## 验证测试代码
```python
import mootdx
from mootdx.quotes import Quotes

print(f'mootdx 版本: {mootdx.__version__}')
print('导入成功！')
```

## 虚拟环境位置
```
/Users/xxxx/Documents/quant_workspace/AI-Course/Quantitative_Analysis/new/mootdx_env
```

## 注意事项
1. 虚拟环境已创建在当前目录的 `mootdx_env` 文件夹中
2. 每次使用 mootdx 前需要先激活虚拟环境
3. 使用清华大学 PyPI 镜像源加速下载
4. 所有依赖包已自动安装完成

## 常见问题

### 如何删除虚拟环境？
```bash
rm -rf mootdx_env
```

### 如何在虚拟环境中安装其他包？
```bash
source mootdx_env/bin/activate
pip install 包名
```

### 如何查看已安装的包？
```bash
source mootdx_env/bin/activate
pip list
```
