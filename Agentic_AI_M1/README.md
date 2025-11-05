# Module 1---Research Agent Tutorial

一个典型的数据驱动任务Research流程为：
1. 梳理任务SoW (Statement of Work)，包括任务简介、任务Benchmark（训练集和测试集）、测评指标和脚本等；
2. 综述完成任务相关工作，对现有技术进行分类；
3. 实验筛选，将检索到的相关工作在已有任务Benchmark上进行适配和复现，选出效果最佳的工作；
4. 在已有工作上进行优化以进一步提升方案性能。

Research Agent的目标是将上述Research流程尽可能自动化由Agent完成，本文以LLM merge任务为例，以下是一个完整的Research Agent tutorial。

## 1. 面向Agent的任务SoW   
### 任务简介
动机：
Training high-performing large language models (LLMs) from scratch is a notoriously expensive and difficult task, costing hundreds of millions of dollars in compute alone. These pretrained LLMs, however, can cheaply and easily be adapted to new tasks via fine-tuning, leading to a proliferation of models that suit specific use cases. Recent work has shown that specialized fine-tuned models can be rapidly merged to combine capabilities and generalize to new skills.

任务：
The competition will provide the participants with a list of expert models that have already been trained on a task-specific dataset. All of these models will be publicly available on the Hugging Face Model Hub with licenses that permit their use for research purposes. These models can either be fully fine-tuned models or models obtained by parameter-efficient fine-tuning methods such as LoRA. Models on this list will be required to satisfy the following criteria: (1) model size $\leq 8$B parameters, and (2) model with licenses compatible with research use (e.b., MIT, Apache 2 etc). 
The goal of this competition is to re-use the provided models to create a generalist model that can perform well on a wide variety of skills like reasoning, coding, maths, chat, and tool use. This list of models will include popular pre-trained models such as LLaMA-7B, Mistral-7B, and Gemma-7B.

Allowed Models：
本次我们对允许的models做了限定，以减少任务的复杂度：
- MergeBench/gemma-2-9b-it_instruction
- MergeBench/gemma-2-9b-it_coding
- MergeBench/gemma-2-9b-it_math

注意：实验时需要将上述模型下载到本地，具体huggingface模型下载方式：https://blog.frognew.com/2024/06/using-huggingface-cli-to-download-models.html

### Benchmark
本次实验仅以代码数据集为例，如HumanEval+

数据地址：https://huggingface.co/datasets/evalplus/humanevalplus/viewer?views%5B%5D=test

数据构成：
![alt text](imgs/image-1.png)
task_id表示任务的ID，prompt表示题目（通常直接请求大模型获取答案），entry_point是唯一标记，canonica_solution是参考答案，test是测试单元。

在原始 HumanEval 164 道 Python 题目基础上，对每道题新增约 80 倍测试用例，从而得到 HumanEval+，即用海量、高覆盖率的单元测试严格验证代码功能正确性。

### 评估指标
指标：Pass @ 1

1）背景：为什么要用 pass @ k

传统代码评估用 BLEU／Edit Distance 等“文本相似度”指标，但这些 **无法保证语义等价** 。于是近几年工作（Kulal 2019；Chen 2021）转向 **功能正确性** ：只认“是否通过全部单元测试”。
当一次对同一题采样 k 份代码，只要 至少 1 份 通过，就视为“题目被解决”，这一概率就是 pass @ k ([arXiv][1])。

2） 一般公式（无偏估计器）

设
| 记号 | 含义                       |
|:----|:---------------------------|
| n   | 对该题实际生成的候选总数（≥ k） |
| c   | 其中通过全部测试的候选数       |
| k   | 我们关心的排名阈值            |


无偏估计器（Chen 2021 式 (1)）：
![alt text](imgs/image-2.png)

直观上，分子是“从不正确样本里抽到 k 份全错”的组合数，分母是“从全部 n 份里抽 k 份”的组合数；用 1 减去它即得到“至少 1 份对”的概率。
作者证明该表达式无偏，且比朴素估计 $$1-(1-\hat p)^k$$ 方差更低，避免随着 n 变化而系统性低估 ([arXiv][1])。

3） pass @ 1 的特化

令 k = 1：

$$\operatorname{pass@1}=1-\frac{\binom{n-c}{1}}{\binom{n}{1}}=\frac{c}{n}.$$

若一次仅生成 1 份代码（n = 1），此式退化为“该份代码是否通过”——也是最常见的实验设定。
若一次生成 n > 1 份，仍可算出 pass @ 1 = c/n；它表示“随机从这 n 份里抽 1 份就通过”的期望成功率，而不是“第 1 个候选是否通过”。

4） 计算示例（官方实现）
```python
def pass_at_k(n: int, c: int, k: int):
    if n - c < k:
        return 1.0
    import numpy as np
    return 1 - np.prod(1 - k / np.arange(n-c+1, n+1))
```
这是 Codex 论文给出的 **数值稳定实现**，避免大阶乘溢出 ([arXiv][1])。

单元测试覆盖度：若测试不全，*pass @ 1* 可能“漏网”错误实现——Humaneval+ 之所以把每题测试扩大 × 80，就是为提高置信度。

5） 小结

pass @ 1 是 **概率论严格推导的无偏估计量**：衡量“从模型当前输出中随机抽 1 份，就能一次性通过全部单元测试”的可信概率。它兼具
**可解释性（直接映射到开发者体验）**、<br>
**公平性（无偏、与样本量解耦）**，<br>
**可操作性（一行 NumPy 代码即可计算）**。<br>
因此已成为 HumanEval、Humaneval⁺、MBPP⁺ 等主流代码基准的核心指标，并被 GitHub Copilot、OpenAI Codex、BigCode StarCoder 等系统广泛采用。

[1]: https://arxiv.org/pdf/2107.03374 "Evaluating Large Language Models Trained on Code"

### 测评脚本
```shell
conda create -n bigcode python=3.10.9
conda activate bigcode

git clone https://github.com/bigcode-project/bigcode-evaluation-harness.git
cd bigcode-evaluation-harness

pip install -e .
pip install -U torch>=2.2 torchvision torchaudio
pip install numpy==1.24.1

CUDA_VISIBLE_DEVICES=1 accelerate launch  main.py \
  --model $MODEL \   # 替换为你的模型地址
  --max_length_generation 512 \
  --precision bf16 \
  --tasks humanevalplus \
  --temperature 0.2 \
  --n_samples 10 \
  --batch_size 10 \
  --allow_code_execution \
  --metric_output_path $OUTPUT_PATH/code_eval.json \ # 替换为你的输出地址
  --use_auth_token
```
得出评估结果：
pass@1: 0.5060975609756098

code_eval.json样例如下：
```json
{
  "humanevalplus": {
    "pass@1": 0.5060975609756098,
    "pass@10": 0.6646341463414634
  },
  "config": {
    "prefix": "",
    "do_sample": true,
    "temperature": 0.2,
    "top_k": 0,
    "top_p": 0.95,
    "n_samples": 10,
    "eos": "<|endoftext|>",
    "seed": 0,
    "model": "../models--meta-llama--Meta-Llama-3-8B-Instruct/snapshots/e1945c40cd546c78e41f1151f4db032b271faeaa",  //
    "modeltype": "causal",
    "peft_model": null,
    "revision": null,
    "use_auth_token": true,
    "trust_remote_code": false,
    "tasks": "humanevalplus",
    "instruction_tokens": null,
    "batch_size": 10,
    "max_length_generation": 512,
    "precision": "bf16",
    "load_in_8bit": false,
    "load_in_4bit": false,
    "left_padding": false,
    "limit": null,
    "limit_start": 0,
    "save_every_k_tasks": -1,
    "postprocess": true,
    "allow_code_execution": true,
    "generation_only": false,
    "load_generations_path": null,
    "load_data_path": null,
    "metric_output_path": "code_eval.json",
    "save_generations": false,
    "load_generations_intermediate_paths": null,
    "save_generations_path": "generations.json",
    "save_references": false,
    "save_references_path": "references.json",
    "prompt": "prompt",
    "max_memory_per_gpu": null,
    "check_references": false
  }
```

## 2. 任务相关工作综述  
本小节的目标是找到尽可能系统、全面的相关工作及其开源项目地址，以供后续Experiment Agent实验，选出最佳工作

### 利用Deep Research查询相关工作
登入google gemini： https://gemini.google.com/app
【选择Deep Reseach】

输入下述提示词：
```
模型融合(Model Merge)是机器学习领域一种高效的赋能技术，它无需收集原始训练数据，也不需要昂贵的计算资源。请帮我综述现有大模型融合的相关工作，要求：
 1、尽可能多的检索相关工作，按照技术特征进行分类，并讨论这些方法的优缺点；
 2、如果有开源项目，请帮我梳理出开源地址；
 3、仅限于大模型的模型融合方法。
 ```

生成综述报告如下：
[大模型融合技术综述_.pdf](doc/大模型融合技术综述_.pdf)

### 人工筛选
由于现有Deep Research工具生成的综述报告，只提供了有限的几个代表工作，为了进一步检索更加系统和全面的工作，还需要人工基于检索到的综述报告去进行梳理和查找，一般步骤如下：
- 1、以Deep Research检索到的工作为基础，查看里面是否检索到本领域综述论文，一般成熟且系统研究的领域会有最新综述论文，研究人员会将已有工作进行梳理和分类；
- 2、如果Deep research没有检索到综述论文，则需要人工确认是否遗漏，人工在Google scholar、Arxiv等平台手动检索确认；
- 3、如果人工确认没有相关领域综述，则以Deep Research检索到的论文为起点，分析论文里的相关工作，可按照Deep research给出的分类，人工检索更多论文和开源项目。

在本任务中，Deep research检索到了本领域的最新综述论文：
- 《Model Merging in LLMs, MLLMs, and Beyond: Methods, Theories, Applications and Opportunities》

    论文地址：https://arxiv.org/pdf/2408.07666

    github地：https://github.com/EnnengYang/Awesome-Model-Merging-Methods-Theories-Applications.git

该综述已经将每项工作按照技术特征进行分类。
根据综述可知，目前LLM Merge领域的相关工作分为以下几类（每类工作仅列举5项开源项目作为后续实验选项）：

#### 基于权重的合并方法
这类方法旨在为不同的模型或任务向量分配不同的重要性权重，从而更有效地合并模型。
代表工作：
- RegMean++: Enhancing Effectiveness and Generalization of Regression Mean for Model Merging

    论文地址：https://arxiv.org/pdf/2508.03121

    github地址：https://github.com/nthehai01/RegMean-plusplus

- CALM: Consensus-Aware Localized Merging for Multi-Task Learning （ICML 2025）

    论文地址：https://arxiv.org/pdf/2506.13406

    github地址：https://github.com/yankd22/CALM/tree/main

- Arcee’s MergeKit: A Toolkit for Merging Large Language Models
    论文地址：https://arxiv.org/pdf/2403.13257

    github地址：https://github.com/arcee-ai/MergeKit

- Evolutionary Optimization of Model Merging Recipes

    论文地址：https://arxiv.org/pdf/2403.13187

    github地址：https://github.com/SakanaAI/evolutionary-model-merge

- Sens-Merging: Sensitivity-Guided Parameter Balancing for Merging Large Language Models

    论文地址：https://arxiv.org/pdf/2502.12420

    github未发布，这篇文章的单位之一是华为诺亚方舟实验室，华为开源了一个toolkit（https://github.com/hahahawu/Long-to-Short-via-Model-Merging.git），将一系列llm  merging的论文集成在这个toolkit里面。但这篇文章的代码还没集成进来。可测试这个toolkit已集成的其他方法：
    - Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch  https://github.com/yule-BUAA/MergeLM
    - TIES-Merging: Resolving Interference When Merging Models https://github.com/prateeky2806/ties-merging

#### 基于子空间的合并方法
这类方法旨在将多个模型投影到稀疏子空间中进行合并，从而减轻任务间的干扰。
代表工作：
- Training-free LLM Merging for Multi-task Learning （ACL2025）

    论文：https://arxiv.org/pdf/2506.12379

    github地址：https://github.com/Applied-Machine-Learning-Lab/Hi-Merging

- Adaptive LoRA Merge with Parameter Pruning for Low-Resource Generation （ACL2025）

    论文：https://arxiv.org/pdf/2505.24174

    github地址:https://github.com/mr0223/adaptive_lora_merge

- LoRI: Reducing Cross-Task Interference in Multi-Task LowRank Adaptation (COLM2025)

    论文：https://arxiv.org/pdf/2504.07448

    github地址：https://github.com/juzhengz/LoRI

- AdaRank: Adaptive Rank Pruning for Enhanced Model Merging

    论文：https://arxiv.org/pdf/2503.22178

    github地址：https://github.com/david3684/AdaRank

- STAR: Spectral Truncation and Rescale for Model Merging  (NAACL 2025)

    论文：https://arxiv.org/pdf/2502.10339

    github地址：https://github.com/IBM/STAR

- Task Vector Quantization for Memory-Efficient Model Merging （ICCV 2025）

    论文：https://arxiv.org/pdf/2503.06921

    github地址：https://github.com/AIM-SKKU/TVQ

#### 基于路由的合并方法
这类方法是一种动态合并策略，根据输入样本的特征在推理阶段动态地决定如何合并模型。
代表工作：
- Dynamic Fisher-weighted Model Merging via Bayesian Optimization （NAACL2025）

    论文：https://arxiv.org/pdf/2504.18992

    github地址：https://github.com/sanwooo/df-merge

- MASS: MoErging through Adaptive Subspace Selection

    论文：https://arxiv.org/pdf/2504.05342

    github地址：https://github.com/crisostomi/mass

- CAMEX: CURVATURE-AWARE MERGING OF EXPERTS (ICLR2025)

    论文：https://arxiv.org/pdf/2502.18821

    github地址：https://github.com/kpup1710/CAMEx

- DAWIN: TRAINING-FREE DYNAMIC WEIGHT INTER - POLATION FOR ROBUST ADAPTATION (ICLR 2025)

    论文：http://arxiv.org/pdf/2410.03782

    github地址：https://github.com/naver-ai/dawin

- Learning to Route Among Specialized Experts for Zero-Shot Generalization

    论文:https://arxiv.org/pdf/2402.05859

    Github地址：https://github.com/r-three/phatgoose

#### 基于后校准的合并方法
代表工作
- Why Train Everything? Tint a Single Layer for Multi-task Model Merging

    论文：https://arxiv.org/pdf/2412.19098

    github地址:https://github.com/AIM-SKKU/ModelTinting

- Fine-tuning Aligned Classifiers for Merging Outputs: Towards a Superior Evaluation Protocol in Model Merging （ICML 2024）

    论文：https://arxiv.org/pdf/2412.13526

    github地址：https://github.com/fskong/FT-Classifier-for-Model-Merging

- SurgeryV2: Bridging the Gap Between Model Merging and Multi-Task Learning with Deep Representation Surgery

    论文：https://arxiv.org/pdf/2410.14389

    github地址：https://github.com/EnnengYang/SurgeryV2

- Representation Surgery for Multi-Task Model Merging （ICML 2024）

    论文：https://openreview.net/pdf/602906ec02919eb95d78d634321fcba1b68a2f03.pdf

    github地址：https://github.com/EnnengYang/RepresentationSurgery

### 小结
综述任务相关工作对于领域研究非常重要，现有Deep Research可以根据现有技术特征进行分类，但是仅仅输出代表性的几项工作，而Research Agent的目标是找出尽可能系统、全面的找到本任务相关的所有工作，通过实验从其中选择最佳工作，当前的Deep Research无法满足要求，仅仅只能作为相关工作检索的入口。

思考：
如何优化现有Deep Research工作以使其满足Research Agent要求？

## 3. Experiment Agent实验适配   
  
### openhands环境安装
#### 依赖准备
##### Docker 安装
软件下载
官网地址: https://www.docker.com/
点击地址进入官网
![alt text](imgs/image-3.png)
根据自身电脑版本下载安装包
![alt text](imgs/image-4.png)
软件安装
[Windows安装参考视频](https://www.bilibili.com/video/BV1Vk4y1V7bV/?spm_id_from=333.337.search-card.all.click&vd_source=99a1a0fc95d22736eceeb45b8bf76c45)
MacOS:
打开安装包,拖拽图标到Applications
![alt text](imgs/image-5.png)

#### 软件启动
点击Docker Desktop应用打开界面,启动docker完成
![alt text](imgs/image-6.png)

#### Openhands-0.48.0
##### 源码下载
https://github.com/OpenHands/OpenHands/archive/refs/tags/0.48.0.zip
点击下载地址下载源码压缩包
![alt text](imgs/image-7.png)

解压缩文件夹
![alt text](imgs/image-8.png)

##### 镜像准备
终端执行命令
```shell
docker pull ghcr.io/all-hands-ai/runtime:0.48-nikolaik
```
![alt text](imgs/image-9.png)


![alt text](imgs/image-10.png)

下载完成后
执行镜像查看命令查看镜像
```shell
docker images
```

![alt text](imgs/image-11.png)

可以在docker desktop中查看
![alt text](imgs/image-12.png)

##### 依赖安装
1、打开VSCode
![alt text](imgs/image-13.png)

2、打开资源管理器
![alt text](imgs/image-14.png)

3、点击打开文件夹
![alt text](imgs/image-15.png)

4、选择解压完成的openhands代码文件夹并点击打开按钮
![alt text](imgs/image-16.png)

5、新建终端
![alt text](imgs/image-17.png)

6、选择创建的自定义的python环境,若没有创建参考第二部分python环境准备（此处的python环境必须>=3.12）中Conda下的创建自定义python环境

终端输入以下代码并执行
```shell
conda create -n python_env python=3.12
conda activate python_env
```
![alt text](imgs/image-18.png)
![alt text](imgs/image-19.png)

7、终端输入命令安装程序依赖
```shell
pip install -e .
pip install Deprecated
```
![alt text](imgs/image-20.png)
![alt text](imgs/image-21.png)
安装完成
![alt text](imgs/image-22.png)

##### 配置文件准备
需要将以下配置文件放入到openhands项目根目录下
openhands项目配置文件
[config.toml](code/config.toml)

启动脚本文件
[run.sh](code/run.sh)

任务描述文件,这里以创建一个hello world的python文件为例
[task.txt](code/task.txt)

入口函数
[main.py](code/main.py)

1、下载配置文件,并将配置文件复制到VSCode中Openhands项目下

![alt text](imgs/image-23.png)

2、添加DeepSeek-API Key

双击打开config.toml
![alt text](imgs/image-24.png)
找到[llm.deepseek]配置
![alt text](imgs/image-25.png)
替换为我们已经申请的deepseek-key
![alt text](imgs/image-26.png)

3、确认切换python环境

终端确认已经切换到openhands所应用的python环境,如果没有执行命令切换
```shell
conda activate python_env
```
![alt text](imgs/image-27.png)

4.运行脚本文件

```shell
sh run.sh
```
![alt text](imgs/image-28.png)
openhands运行启动容器
![alt text](imgs/image-29.png)

5、查看容器

打开docker desktop可以查看到已经启动了一个openhands容器,点击打开
![alt text](imgs/image-30.png)
容器内已经在启动程序
![alt text](imgs/image-31.png)

6、查看大模型对话

查看openhands目录下logs/llm文件夹,该文件夹是agent的对话信息,prompt和response是成对生成
![alt text](imgs/image-32.png)

7、查看运行结果

终端输出已经完成创建python代码文件并输出hello_world
![alt text](imgs/image-33.png)

8、验证结果

查看任务容器已经结束,点击运行重新启动容器
![alt text](imgs/image-34.png)
点击exec进入命令窗口
![alt text](imgs/image-35.png)
输入以下命令并执行
```shell
bash
```
![alt text](imgs/image-36.png)
执行命令查看是否有生成文件
```shell
cd /workspace && ls
```
![alt text](imgs/image-37.png)
查看文件内容
```shell
cat hello_world.py
```
![alt text](imgs/image-38.png)
helloworld代码已创建,运行校验
![alt text](imgs/image-39.png)
正确输出hello world 验证完成
