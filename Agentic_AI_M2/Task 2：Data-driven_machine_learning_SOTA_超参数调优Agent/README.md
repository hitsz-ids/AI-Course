

# 引言

近年来，深度学习及其衍生的数据驱动机器学习方法取得了显著进展。然而，这些进展在实际复现时却常面临挑战。尽管论文通常附带代码或说明，但实际上“可运行”并不等同于“达到报告指标”。问题的一个根源在于超参数调优过程：学习率、批量大小、优化器选型、正则化策略、数据增强方案、初始化方式以及训练时长等，往往在论文中只简略提及或未明示，但却对最终性能具有决定性影响。

与此同时，基于大型语言模型（LLMs）的代理（Agent）技术正在突破传统人机交互范式：它们具备理解文档、解析代码库、执行环境配置、迭代实验的能力。理论上，这类代理已能从“读—思考—行动”闭环中，完成从论文理解到训练执行的自动化流程。可是在实际落地中，这些代理往往将“跑通训练流程”作为目标，而非“优化模型性能至论文水平”。

因此，本研究提出一种面向数据驱动机器学习任务的超参数调优代理。该系统在完整代码仓库层面工作：代理自主识别超参数入口、构建搜索空间、执行迭代实验、记录和分析结果，并按照论文中报告的评测协议判断是否达到目标性能。其目标是缩小“算法可运行–性能达标”之间的鸿沟，使自动化复现从能跑通迈向可对齐指标。

# 技术挑战

## 实验效率与计算预算限制

传统超参数优化方法通常需要大量试验，消耗大量计算资源，且在有限的预算下难以高效找到最优配置 。

## 隐性知识缺失

另一个重要问题是“隐性知识”的缺失。许多SOTA论文中，尽管给出了模型架构和基本的算法流程，但训练过程中的微调技巧、数据增强方法、网络初始化策略等关键实现细节往往没有被明确记录。这些“隐性知识”对复现结果的影响往往被低估，导致实际复现过程中出现偏差。因此，如何发现和补全这些隐性知识，成为论文复现中超参数调优工作的另一大挑战。

## **跨任务与跨模型的通用性**

超参数优化方法往往依赖于特定的任务或模型架构，如何设计一个通用且灵活的框架，使其适用于多种任务和模型架构，是一大挑战 。

# 实验

给定2个data-driven machine learning tasks，输入包括：

- Task SOW
- 基于某一个sota工作，Openhands已适配、走通的代码库（但并没有达到已知的最佳效果）

具体工作：

1、复现超参数调优Agent的论文工作，明确是否能提升性能。（考核：复现sota成功，良）

需复现的论文如下：

 [AutoML-Agent-A_Multi-Agent_LLM_Framework_for_Full-Pipeline_AutoML.pdf](pdf/AutoML-Agent- A Multi-Agent LLM Framework for Full-Pipeline AutoML.pdf) 

 [SELA-TREE-SEARCH_ENHANCED_LLM_AGENTS_FOR_AUTOMATED_MACHINE_LEARNING.pdf](pdf/SELA- TREE-SEARCH ENHANCED LLM AGENTS FOR AUTOMATED MACHINE LEARNING.pdf) 

2、自己继续探索其他相关工作的效果，

- 能逼近最佳性能。（考核：优）
- 超越最佳性能。（考核：100）

## 风电功率预测（Wind Power ）

任务背景： [风电功率预测（短期）SOW](../风电功率预测（短期）_SOW/README.md) 

| SOTA                                        | OpenHands性能 | 目前最高性能 |
| ------------------------------------------- | ------------- | ------------ |
| [TimeXer](https://github.com/thuml/TimeXer) | 53.1281       | 49.0054      |

## **时间动作定位（**Temporal Action Localisation）

任务背景： [MLRC-Bench  Temporal Action Localisation SOW](../MLRC-Bench_Temporal_Action_Localisation_SOW/README.md) 

| SOTA                                                         | OpenHands性能 | 目前最高性能 |
| ------------------------------------------------------------ | ------------- | ------------ |
| [actionformer](https://github.com/ptchallenge-workshop/actionformer_release_PT/tree/main) | 8.34%         | 12.15%       |
