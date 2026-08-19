#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mootdx 行情服务器连接示例

功能说明：
1. 自动选择可用的行情服务器
2. 建立连接并测试服务器响应
3. 输出服务器详细信息
4. 完整的异常处理机制

作者: AI Assistant
创建日期: 2026-06-17
"""

from mootdx.quotes import Quotes
import sys


def select_best_server():
    """
    自动选择最佳可用的行情服务器
    
    返回:
        Quotes: 已连接的行情服务器对象
        
    异常:
        Exception: 当无法连接任何服务器时抛出
    """
    try:
        print("=" * 60)
        print("正在自动选择最佳行情服务器...")
        print("=" * 60)
        
        # 使用 factory 方法自动选择最佳服务器
        # market='std' 表示使用标准行情服务器
        # timeout 设置连接超时时间（秒）
        client = Quotes.factory(market='std', timeout=10)
        
        print("✓ 成功连接到行情服务器！\n")
        return client
        
    except ConnectionError as e:
        print(f"✗ 连接错误: {e}")
        raise Exception("无法连接到任何行情服务器，请检查网络连接")
    except TimeoutError as e:
        print(f"✗ 连接超时: {e}")
        raise Exception("连接服务器超时，请稍后重试")
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        raise Exception(f"选择服务器时发生错误: {str(e)}")


def get_server_info(client):
    """
    获取并输出服务器详细信息
    
    参数:
        client: Quotes 对象，已连接的行情服务器
        
    返回:
        dict: 服务器信息字典
    """
    try:
        print("-" * 60)
        print("服务器详细信息：")
        print("-" * 60)
        
        # 获取服务器配置信息
        server_info = {}
        
        # 获取服务器的 IP 和端口
        if hasattr(client, 'client') and hasattr(client.client, 'args'):
            args = client.client.args
            server_info['IP地址'] = getattr(args, 'ip', '未知')
            server_info['端口'] = getattr(args, 'port', '未知')
        
        # 尝试获取其他可用信息
        if hasattr(client, '__class__'):
            server_info['服务器类型'] = client.__class__.__name__
        
        # 输出服务器信息
        if server_info:
            for key, value in server_info.items():
                print(f"  {key}: {value}")
        else:
            print("  无法获取详细服务器信息")
        
        # 测试服务器响应 - 尝试简单的API调用
        print("\n正在测试服务器响应...")
        try:
            # 尝试获取股票数量来验证连接
            test_stocks = client.stocks(market=0)
            if test_stocks is not None and not test_stocks.empty:
                print(f"✓ 服务器响应正常")
                print(f"  可访问深圳市场股票数据")
                server_info['状态'] = '在线'
            else:
                print("⚠ 服务器响应异常")
        except Exception as e:
            print(f"⚠ 测试连接时出现问题: {e}")
        
        print("-" * 60)
        
        return server_info
        
    except Exception as e:
        print(f"⚠ 警告: 获取服务器信息时出现问题 - {e}")
        print("-" * 60)
        return {}


def test_server_functionality(client):
    """
    测试服务器的基本功能
    
    参数:
        client: Quotes 对象，已连接的行情服务器
    """
    try:
        print("\n" + "=" * 60)
        print("测试服务器功能...")
        print("=" * 60)
        
        # 测试1: 获取股票列表
        print("\n1. 测试获取股票列表...")
        try:
            # 获取深圳市场的股票列表（market参数: 0-深圳, 1-上海）
            stocks = client.stocks(market=0)  # 0 表示深圳市场
            
            # 检查是否返回了 DataFrame 并且不为空
            if stocks is not None and not stocks.empty:
                print(f"   ✓ 成功获取深圳市场股票列表，共 {len(stocks)} 只股票")
                
                # 显示前3只股票的详细信息
                print("   示例股票（前3只）：")
                for i in range(min(3, len(stocks))):
                    stock = stocks.iloc[i]
                    # 根据DataFrame的实际列名显示信息
                    if 'code' in stocks.columns and 'name' in stocks.columns:
                        print(f"     {i+1}. 代码: {stock['code']}, 名称: {stock['name']}")
                    else:
                        print(f"     {i+1}. {stock.to_dict()}")
            else:
                print("   ⚠ 股票列表为空")
        except Exception as e:
            print(f"   ✗ 获取股票列表失败: {e}")
        
        # 测试2: 获取指数列表
        print("\n2. 测试获取指数列表...")
        try:
            # 获取上海市场指数列表
            indices = client.index(market=1)  # 1 表示上海市场
            
            # 检查是否返回了 DataFrame 并且不为空
            if indices is not None and not indices.empty:
                print(f"   ✓ 成功获取上海市场指数列表，共 {len(indices)} 个指数")
                
                # 显示前3个指数的详细信息
                print("   示例指数（前3个）：")
                for i in range(min(3, len(indices))):
                    index = indices.iloc[i]
                    # 根据DataFrame的实际列名显示信息
                    if 'code' in indices.columns and 'name' in indices.columns:
                        print(f"     {i+1}. 代码: {index['code']}, 名称: {index['name']}")
                    else:
                        print(f"     {i+1}. {index.to_dict()}")
            else:
                print("   ⚠ 指数列表为空")
        except Exception as e:
            print(f"   ✗ 获取指数列表失败: {e}")
        
        # 测试3: 获取实时行情（可选）
        print("\n3. 测试获取实时行情（上证指数）...")
        try:
            # 获取上证指数的实时行情
            # symbol: 股票代码, market: 市场（1-上海，0-深圳）
            quotes = client.quotes(symbol='000001', market=1)
            
            if quotes is not None and not quotes.empty:
                print(f"   ✓ 成功获取上证指数实时行情")
                # 显示关键信息
                quote = quotes.iloc[0]
                print(f"   代码: {quote.get('code', 'N/A')}")
                print(f"   当前价: {quote.get('price', 'N/A')}")
                print(f"   涨跌幅: {quote.get('percent', 'N/A')}%")
            else:
                print("   ⚠ 无法获取行情数据")
        except Exception as e:
            print(f"   ⚠ 获取实时行情时出现问题: {e}")
        
        print("\n" + "=" * 60)
        print("功能测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 功能测试时发生错误: {e}")
        # 不抛出异常，允许程序继续执行


def main():
    """
    主函数：程序入口
    """
    print("\n" + "=" * 60)
    print(" mootdx 行情服务器连接示例程序 ")
    print("=" * 60 + "\n")
    
    client = None
    
    try:
        # 步骤1: 自动选择并连接到最佳服务器
        client = select_best_server()
        
        # 步骤2: 获取并输出服务器信息
        server_info = get_server_info(client)
        
        # 步骤3: 测试服务器功能
        test_server_functionality(client)
        
        print("\n" + "=" * 60)
        print("✓ 程序执行完成！")
        print("=" * 60 + "\n")
        
        return 0  # 成功退出
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断程序执行")
        return 130  # 用户中断的退出码
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 程序执行失败: {str(e)}")
        print("=" * 60 + "\n")
        return 1  # 错误退出
        
    finally:
        # 清理资源
        if client:
            try:
                # 如果有断开连接的方法，在这里调用
                print("正在关闭连接...")
                # client.close()  # mootdx 可能不需要显式关闭
            except:
                pass


if __name__ == "__main__":
    """
    程序入口点
    
    使用方法:
        1. 激活虚拟环境: source mootdx_env/bin/activate
        2. 运行程序: python mootdx_example.py
    """
    exit_code = main()
    sys.exit(exit_code)
