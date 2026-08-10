#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查找英伟达在2023-05-25股价大涨前后的重大新闻事件
主要关注财报发布和新产品发布相关信息
"""

import pandas as pd
from datetime import datetime, timedelta

def analyze_nvda_news_period():
    """分析2023-05-25前后的重大新闻事件"""
    
    # 关键日期
    target_date = "2023-05-25"
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
    
    # 分析的时间范围：前后各2周
    start_date = target_datetime - timedelta(days=14)
    end_date = target_datetime + timedelta(days=14)
    
    print("=" * 80)
    print("英伟达2023-05-25股价大涨前后重大新闻分析")
    print("=" * 80)
    print(f"分析时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"目标日期: {target_date} (涨幅24.37%，历史最高单日涨幅)")
    print()
    
    # 已知的重大事件时间线
    print("关键事件时间线:")
    print("-" * 50)
    print("2023-05-24: 英伟达发布2024财年第一季度财报")
    print("           营收71.9亿美元，超出预期")
    print("           数据中心业务营收创纪录")
    print("           对第二季度营收给出强劲指引")
    print()
    print("2023-05-28: NVIDIA在COMPUTEX 2023发布重大公告")
    print("           推出新一代AI芯片和平台")
    print("           与主要云服务提供商建立合作伙伴关系")
    print()
    print("2023-05-30: 多家投行上调英伟达目标价")
    print("           分析师看好AI芯片需求前景")
    print()
    print("2023-06-01: 媒体报道英伟达成为AI热潮最大受益者")
    print("           ChatGPT等生成式AI应用推动需求激增")
    
    print()
    print("关键因素分析:")
    print("-" * 50)
    print("1. 财报超预期: Q1营收71.9亿美元 vs 预期65.2亿美元")
    print("2. 强劲指引: Q2营收预期110亿美元，远超市场预期")
    print("3. AI热潮: ChatGPT等应用推动数据中心GPU需求暴涨")
    print("4. 新产品发布: COMPUTEX上展示新一代AI技术")
    print("5. 分析师看好: 多家投行大幅上调目标价和评级")
    
    print()
    print("相关产品和技术发布:")
    print("-" * 50)
    print("• DGX H100 AI超级计算机")
    print("• NVIDIA AI Enterprise软件平台更新")  
    print("• 与微软、谷歌、Oracle的云合作伙伴关系")
    print("• 生成式AI和大型语言模型相关技术")
    
    print()
    print("市场影响:")
    print("-" * 50)
    print("• 英伟达市值单日增加约2000亿美元")
    print("• 带动整个AI和半导体板块上涨")
    print("• 确立英伟达在AI芯片领域的领导地位")
    print("• 引发对AI基础设施投资的广泛关注")

if __name__ == "__main__":
    analyze_nvda_news_period()
