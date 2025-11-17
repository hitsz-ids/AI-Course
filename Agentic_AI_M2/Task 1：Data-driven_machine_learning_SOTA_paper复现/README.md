
# 引言

随着深度学习和数据驱动机器学习（data-driven machine learning）技术的快速发展，许多研究提出了新的模型和方法，并在基准数据集上取得了显著的性能提升。然而，这些成果的可复现性仍然是学术界面临的重要问题。复现不仅仅是将代码成功运行，更关键的是实验结果是否与原论文中声明的一致。实际复现过程中，论文往往省略了许多对模型性能有显著影响的细节，例如超参数范围、训练技巧、数据预处理步骤和网络初始化策略等，这些隐性知识缺失导致了实践和理论之间的巨大鸿沟。

尤其在数据驱动的机器学习（包括自然语言处理、计算机视觉等领域），复现一个SOTA（state-of-the-art）工作通常不仅要求准确复现算法，还要求严格遵循论文中的实验设定，避免由于实验环境、实现细节或随机性导致的性能差异。尽管已有一定的标准化工作，如NeurIPS 2019的复现性计划，但在实际操作中，环境异构性和缺失的细节仍然是复现成功的重大挑战。

近年来，基于大语言模型（LLM）的AI Agent在复杂任务中表现出了巨大的潜力。通过“读—思考—行动”的闭环，这些代理已经能够在跨工具、跨环境的任务中取得可重复的成功。这些进展表明，AI Agent不仅能够理解论文中的算法和代码实现，还能够自动化完成从环境配置到实验执行的所有步骤。

本研究的目标是提出一种基于AI Agent的自动化复现系统，旨在通过AI Agent自主完成数据集下载、环境配置、训练和评测等任务，从而实现对数据驱动的机器学习SOTA工作进行高效且准确的复现。

# 技术挑战

## 环境异构性

在复现SOTA论文的过程中，不同研究的代码环境差异巨大，涉及的依赖关系和系统配置复杂多变。尤其是深度学习框架和库的版本不同，可能导致复现结果的不一致。由于论文中对环境配置的描述通常较为简略，缺乏详细的操作步骤或软件版本说明，这增加了复现的难度。

## 隐性知识缺失

另一个重要问题是“隐性知识”的缺失。许多SOTA论文中，尽管给出了模型架构和基本的算法流程，但训练过程中的微调技巧、数据增强方法、网络初始化策略等关键实现细节往往没有被明确记录。这些“隐性知识”对复现结果的影响往往被低估，导致实际复现过程中出现偏差。因此，如何发现和补全这些隐性知识，成为复现工作的另一大挑战。

# 技术需求

- **自动化准备****SOTA****工作运行环境并复现：**根据SOTA的github项目，自动下载数据集、安装代码运行环境并复现sota论文中的评测信息
- 每个SOTA独立重复5次，**成功跑通**指Experiment Agent成功复现sota（训练+评测），**最终复现得分**指复现sota最终的效果（用于人来评判是否复现了SOTA效果）

# 实验及考核

给定2个Data-driven machine learning task， 评测目前主流的Coding Agent（Openhands）对于sota复现的性能。

具体要做：

1、用openhands跑通sota，得到评估结果。（考核：及格）

2、结果分析：（考核：良）

- 分析openhands code generation过程日志，发现问题AI Agent本身的设计问题。
- 分析openhands生成代码的评估结果与实际论文声明结果的差距，以及造成这一差异的根本原因。

3、选其中1个问题，给出解决方案。（考核：优）

4、更进一步，实现方案，解决这一问题。（考核：100）

# **时间动作定位（**Temporal Action Localisation）

任务背景： [MLRC-Bench  Temporal Action Localisation SOW](../MLRC-Bench_Temporal_Action_Localisation_SOW/README.md) 

| SOTA                                                         | 是否成功跑通 | 最终复现得分 | 日志 | 结果分析 | 负责人 |
| ------------------------------------------------------------ | ------------ | ------------ | ---- | -------- | ------ |
| [DyFADet](https://github.com/yangle15/DyFADet-pytorch?tab=readme-ov-file) |              |              |      |          | 蔡启晔 |
| [TemporalMaxer](https://github.com/TuanTNG/TemporalMaxer)    |              |              |      |          | 王涵   |
| [TriDet](https://github.com/dingfengshi/TriDet)              |              |              |      |          | 王涵   |
| [actionformer](https://github.com/happyharrycn/actionformer_release) |              |              |      |          | 蔡启晔 |

# 风电功率预测（Wind Power ）

任务背景： [风电功率预测（短期）SOW](../风电功率预测（短期）_SOW/README.md) 

| SOTA                                               | 是否成功跑通 | 最终复现得分 | 运行日志 | 结果分析 | 负责人 |
| -------------------------------------------------- | ------------ | ------------ | -------- | -------- | ------ |
| [Time-MoE](https://github.com/Time-MoE/Time-MoE)   |              |              |          |          | 方烨   |
| [Hiformer](https://github.com/linyi201314/Hiformer) |              |              |          |          | 方烨   |
| [2DXformer](https://github.com/jseaj/2DXformer)    |              |              |          |          |        |
| [TimeXer](https://github.com/thuml/TimeXer)        |              |              |          |          |        |
| [EAC](https://github.com/Onedean/EAC)              |              |              |          |          |        |
| [ST-ReP](https://github.com/zhuoshu/ST-ReP)        |              |              |          |          |        |
