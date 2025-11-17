### 任务目标

挑战任务是**时间动作定位**。参赛模型需要接收一个视频，然后根据预定义的类别，对视频中发生的动作进行定位和分类，包括（1）识别动作是什么，（2）准确标注动作的开始和结束时间。

下图展示了**时间动作定位 (Temporal Action Localisation)** 和 **时间声音定位 (Temporal Sound Localisation)** 的概念，以及它们如何在一小段视频中进行标注。

本任务只做**时间动作定位 (Temporal Action Localisation)，不做时间声音定位 (Temporal Sound Localisation) 。**

![1](../MLRC-Bench_Temporal_Action_Localisation_SOW/imgs/1.PNG)

### 数据

高分辨率视频（RGB+音频，最长35秒，30帧/秒，最大分辨率1080p），每个视频都有多个动作片段标注。

下载地址：

| Split      | Videos                                                       | List of video_ids                                            | Action annotations                                           | Sound annotations                                            |
| ---------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Train      | [videos](https://storage.googleapis.com/dm-perception-test/zip_data/train_videos.zip) | [video_id_list](https://storage.googleapis.com/dm-perception-test/misc/localisation_challenge_train_id_list.csv) | [action_annotations](https://storage.googleapis.com/dm-perception-test/zip_data/action_localisation_train_annotations.zip) | [sound_annotations](https://storage.googleapis.com/dm-perception-test/zip_data/sound_localisation_train_annotations.zip) |
| Validation | [videos](https://storage.googleapis.com/dm-perception-test/zip_data/valid_videos.zip) | [video_id_list](https://storage.googleapis.com/dm-perception-test/misc/localisation_challenge_valid_id_list.csv) | [action_annotations](https://storage.googleapis.com/dm-perception-test/zip_data/challenge_action_localisation_valid_annotations.zip) | [sound_annotations](https://storage.googleapis.com/dm-perception-test/zip_data/challenge_sound_localisation_valid_annotations.zip) |
| Test       | [videos](https://storage.googleapis.com/dm-perception-test/zip_data/test_videos.zip) | [video_id_list](https://storage.googleapis.com/dm-perception-test/misc/localisation_challenge_test_id_list.csv) | -                                                            | -                                                            |

**Features (optional)**

| Split      | Video features ([TSP](https://github.com/HumamAlwassel/TSP)) | Audio features ([MMV](https://arxiv.org/abs/2006.16228))     |
| ---------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Train      | [video_features](https://storage.googleapis.com/dm-perception-test/zip_data/action_localisation_train_video_features.zip) | [audio_features](https://storage.googleapis.com/dm-perception-test/zip_data/sound_localisation_train_audio_features.zip) |
| Validation | [video_features](https://storage.googleapis.com/dm-perception-test/zip_data/action_localisation_valid_video_features.zip) | [audio_features](https://storage.googleapis.com/dm-perception-test/zip_data/sound_localisation_valid_audio_features.zip) |
| Test       | [video_features](https://storage.googleapis.com/dm-perception-test/zip_data/action_localisation_test_video_features.zip) | [audio_features](https://storage.googleapis.com/dm-perception-test/zip_data/sound_localisation_test_audio_features.zip) |

竞赛本身的测试集答案没有公开。MLRC-bench将训练集按8:2比例分为训练集、验证集；将原来的验证集作为测试集。

### 评估指标及baseline

- 指标：

The evaluation metric for this challenge is **mean** **average precision** **(mAP)**. It is calculated as the average precision over different action classes and IoU thresholds.

For the IoU thresholds in evaluation we use [0.1 -> 0.5] with 0.1 increments.

Each submission must contain at least an empty list for all the videos selected for each challenge phase. Submissions can use either video input alone or also utilise audio input to enhance model performance. We require participants to select the input modality of their models.

Submissions are evaluated separately for validation and test datasets.

- baseline及评估程序示例（[ActionFormer](https://github.com/deepmind/perception_test/blob/main/baselines/temporal_action_localisation.ipynb)）：
  - https://github.com/google-deepmind/perception_test/blob/main/baselines/temporal_action_localisation.ipynb
  - https://github.com/ptchallenge-workshop/actionformer_release_PT/tree/main
- 以baseline评估代码为例，评估公式及步骤分析，参考以下链接：https://chatgpt.com/s/t_6888a94b4c4081919e68187a698b3751

### 相关工作

- OpenTAD： GitHub地址：https://github.com/sming256/OpenTAD 是个工具集，可在本次竞赛数据集上做一次适配，尝试以下模型效果：
  - **DyFADet****(2024)**
    - https://github.com/yangle15/DyFADet-pytorch?tab=readme-ov-file
  - **TemporalMaxer**
    - https://github.com/TuanTNG/TemporalMaxer
  - TriDet
    - https://github.com/dingfengshi/TriDet
  - Re2TAL
  -  以上模型是OpenAI Deep Research推荐 + 在Baseline【ActionFormer】之后发表的Temporal Action Localization（TAL）领域的 SOTA 方法 + 已集成进OpenTAD工具集中。

![2](../MLRC-Bench_Temporal_Action_Localisation_SOW/imgs/2.PNG)

#### 技术路线分析：

- Two Stage：
  - 借鉴两阶段目标检测（如Faster R-CNN）的思想，将TAL划分为提案生成（proposal generation）和分类回归两个阶段。第一阶段模型从整段视频中产生候选的动作段（通常给出候选片段的起止时间及一个置信度)，第二阶段再对每个候选段进行进一步的特征提取、分类预测，并精细地回归边界位置。这一范式下，Stage 1 注重召回率（找到所有潜在动作位置），Stage 2 注重精度（过滤误检并提升分类/定位准确度）。
  - 代表工作主要集中在2017-2021年，两阶段方法在TAL发展早期（2017-2021）一直占据主导地位。例如上图中的VSGN (ICCV 2021)，在THUMOS14上精度有明显提升（mAP@0.5超过52%），是两阶段方法中后期的代表之一。
- One Stage：
  - 一个统一的模型中同时完成动作边界定位和动作分类，不再将其拆分为二阶段。
  - One-Stage路线目前在精度和效率上均表现出色，是TAL领域最为活跃和具有突破性的方向之一。
  - ActionFormer (ECCV 2022)：该模型将Transformer引入TAL，是首批基于Transformer架构的单阶段动作定位模型之一，取得了强劲的性能，在THUMOS14上平均mAP达到66.8%，mAP@0.5达到71%，显著超过以往两阶段方法
  - 近几年的相关工作在THUMOS14的表现，在ActionFormer上有微小提升：
    - TemporalMaxer (ArXiv 2023)  平均mAP达到67.7%，mAP@0.5达到 71.8 %
    - TriDet (CVPR 2023) 平均mAP达到 69.3%，mAP@0.5达到 72.9 %
    - DyFADet (ECCV 2024)平均mAP达到 69.2%，mAP@0.5达到 72.7 %
- DETR：
  - 将Detection Transformer（原由 Facebook/Meta AI 在 2020 年提出的端到端检测框架）引入时间动作定位，将动作检测任务建模为集合预测问题。与传统方法不同，DETR类模型使用Transformer编码视频特征，并通过一组可学习的查询（query）直接输出一个固定数量的预测段集合，每个预测包括动作类别和时间边界。
  - 在TAL领域的实际表现起初并不突出**，**存在**收敛慢、数据需求大**的问题。
  - 上图中这一技术路线的代表TadTR在标准基准上的mAP一度落后于精心设计的两阶段/一阶段方法。因此，大量后续工作致力于**改进DETR模型的训练效率和精度。**
  - **近年新兴且值得关注**
- 端到端训练：
  - 不是指某一种模型结构，而是一种**训练策略**，可以结合上述任意结构，能够**显著提高TAL精度**。
  - 其核心思想是在训练过程中**联合优化视频特征提取网络与检测头，将“同时训练骨干和检测头”的方法归为端到端类别。多数早期方法由于算力限制并未端到端训练。近年随着GPU性能提升和算法优化，端到端TAL逐渐可行。**
  - 近几年的相关工作在THUMOS14的表现：
    - AdaTAD (CVPR 2024)：平均mAP达到76.9%，mAP@0.5达到 80.9 %。AdaTAD 通过“**只微调时序适配器**”的方式，在显存可控的前提下，把 10 亿级视频大模型端到端塞进 TAL，用最少参数换来当前最强性能与最长序列处理能力。
    - LoSA ：平均mAP达到71%，mAP@0.5达到 74.5 % 。把十亿级视频基础模型（如 VideoMAEv2-g, 1 B+ 参数）真正“端到端”用在长视频 TAL，而显存、参数量都可控

#### 新兴方向与大模型多模态应用

除了上述传统范式，TAL领域近年还出现了一些新的技术路线和研究热点，主要涉及开放词汇动作定位和多模态/大模型的引入：

- 开放词汇（Open-Vocabulary）TAL：传统TAL假定训练和测试动作类别固定且有限。然而实际应用中可能出现未见过的新动作类别。为应对这一情况，研究者开始探索开放词汇的动作定位方法。典型做法是借助大规模预训练的视觉-语言模型来获取动作的语义描述，再让定位模型利用这些描述去匹配视频片段。例如OVTAL/OVFormer (2024)扩展了ActionFormer模型，引入以下创新: (1) 利用大型语言模型（LLM）针对每个动作类别生成丰富的文本描述；(2) 通过跨模态注意力模块，将类别的文本表示与视频帧特征对齐，融合出指导定位的多模态特征；(3) 采用两阶段训练策略，先在大词汇动作数据集预训包含海量类别的模型，再微调在目标小词汇数据集上，从而具备泛化到新类别的能力。实验表明，OVFormer在THUMOS14、ActivityNet等上能够检测出未在训练集中出现的新动作类别，效果显著优于只用静态词嵌入的基线方法。开放词汇TAL代表了TAL从封闭集识别走向开放世界的重要一步，结合多模态信息极大增强了模型的灵活性和知识面。
- 大模型与预训练的利用：一方面，有学者将大规模视频MAE、ViT等作为特征提取器，再通过LoSA、AdaTAD等适配模块进行端到端微调。这使模型能够利用数百万视频预训练所得的丰富特征，从而在下游检测中取得更高的精度。例如，上述LoSA适配VideoMAEv2后，在保持可训练参数较少的情况下显著提升了TAL的检测性能。另一方面，除了视觉模型，大语言模型（LLM）也被用来提供辅助信息：除了生成类别描述用于开放词汇，LLM还可用于挖掘动作之间的语义关系、生成合成训练样本描述、甚至推理动作序列的逻辑。一些前沿探索开始尝试让LLM阅读视频的事件序列描述来辅助定位决策，但这仍在初步阶段。总的来说，大模型在TAL中的应用体现为“大规模预训练 + 轻量适配微调”的范式。
- 多模态信息融合：除了文本描述，其他模态如音频也可用于辅助动作定位。例如在视频中判断“有人鼓掌”动作，掌声的声音是有力线索。近期有研究提出音频-视频联合的事件定位（如音视频事件检测DAVE任务），其方法可迁移到纯视频的动作定位上，利用音频模态提升对动作的辨识度。多模态融合通常通过跨模态注意力或图网络实现，将不同信号的特征对齐。在OpenTAD套件中甚至加入了音频动作数据集（EPIC-Sounds）供研究。因此，可以预见未来TAL系统可能同时分析视频的视觉特征、语音对话内容、环境声音甚至传感器数据，以获得对动作更加准确全面的理解。
  - 近几年的相关工作在THUMOS14的表现：
    - DEL (Dense Event Localization)：平均mAP达到71.9%，mAP@0.5达到 71.8 %

### 竞赛排名

![3](../MLRC-Bench_Temporal_Action_Localisation_SOW/imgs/3.png)
