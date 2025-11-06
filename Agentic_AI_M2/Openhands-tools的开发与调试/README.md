# 介绍

本教程介绍在openhands中Agent的tool开发与调试

# 本课涵盖以下内容

- tool的创建与注册
- tool工具的使用

# tool的创建与注册

## 创建tool

在openhands/agenthub/codeact_agent/tools目录下包含该agent的所有tools

- **Bash（bash.py）**： 在持久shell会话的终端中执行bash命令。
- **Ipython****(ipython.py)****：**在ipython环境中运行Python代码单元(cell)。
- **llm_based_edit****(llm_based_edit.py)****：**基于LLM编辑文件
- **str_replace_edit:****(str_replace_editor.py)**  文件相关操作（创建、编辑、查看），提供了字符串替换修改、查看文件行对应内容
- **Think****(think.py)****:** 使用这个工具来思考一些事情。它不会获取新信息或对存储库进行任何更改，而只是记录这个想法在对话历史中。当需要复杂的推理或头脑风暴时使用它。
- **Browser（browser.py）：**使用Python代码与浏览器交互。
- **Finish****(finish.py)****:**  表示当前任务或会话完成的信号。
![img.png](imgs/img.png)

新增一个tool专门用于github代码下载

在openhands/agenthub/codeact_agent/tools目录下新建git_repo_download.py文件
![img_1.png](imgs/img_1.png)

在git_repo_download.py文件声明工具描述与Tool的相关结构参数

```Python
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
)

_DGIT_REPO_DOWNLOAD_DESCRIPTION = """
Download a Git repository to a specified location.
* This tool downloads the repository from a given Git URL.
* It saves the repository code to the specified local directory and renames the project folder based on the provided project name.
"""
GitRepoDownloadTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='git_repo_download',
        description=_DGIT_REPO_DOWNLOAD_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'git_url': {
                    'type': 'string',
                    'description': 'The URL of the Git repository to be cloned.',
                },
                'destination_path': {
                    'type': 'string',
                    'description': 'The local directory where the repository should be saved.',
                },
                'project_name': {
                    'type': 'string',
                    'description': 'The name to rename the downloaded project folder.',
                },
            },
            'required': ['git_url', 'destination_path', 'project_name'],
        },
    ),
)
```

## 注册tool

openhands/agenthub/codeact_agent/tools/__init__.py注册GitRepoDownloadTool
![img_2.png](imgs/img_2.png)

打开openhands/agenthub/codeact_agent/codeact_agent.py文件,在_get_tools方法中将代码下载tool注册到agent中
![img_3.png](imgs/img_3.png)
![img_4.png](imgs/img_4.png)
## 创建Action与Observation

1. ### 新增ActionType和ObervationType

在openhands/core/schema/action.py中新增GIT_REPO_DOWNLOAD
![img_5.png](imgs/img_5.png)

在openhands/core/schema/observation.py中新增GIT_REPO_DOWNLOAD
![img_6.png](imgs/img_6.png)

### 2.新增Action

openhands/events/action目录下新增environment.py

environment.py中创建GitRepoDownloadAction

```Python
from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action
from typing import ClassVar

@dataclass
class GitRepoDownloadAction(Action):
    """Get the recommended Python version based on project dependencies"""

    git_url: str = '',
    destination_path: str = ''
    project_name: str = ''
    action: str = ActionType.GIT_REPO_DOWNLOAD
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f"git repo need download ,the git url : {self.git_url}"

    def __str__(self) -> str:
        ret = f'**GitRepoDownloadAction (source={self.source})**\n'
        ret += f'git_url:{self.git_url}\n'
        ret += f'destination_path:{self.destination_path}\n'
        ret += f'project_name:{self.project_name}\n'
        return ret
```
![img_7.png](imgs/img_7.png)

openhands/events/action/__init__.py中注册Action
![img_8.png](imgs/img_8.png)

### 3.新增Observation

openhands/events/observation目录下新增environment.py

environment.py创建GitRepoDownloadObservation

```Python
from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation import Observation

@dataclass
class GitRepoDownloadObservation(Observation):
    git_url: str
    observation: str = ObservationType.GIT_REPO_DOWNLOAD
    success: bool = True

    @property
    def message(self) -> str:
        return f'I get the git url: {self.git_url}.'

    def __str__(self) -> str:
        return (f'**GitRepoDownloadObservation  (source={self.source},**\n,'
                f'git url={self.git_url})**\n'
                '--BEGIN AGENT OBSERVATION--\n'
                f'{self.observation}\n'
                '--END AGENT OBSERVATION--'
                )
```
![img_9.png](imgs/img_9.png)

openhands/events/observation/__init__.py中注册Obvservation
![img_10.png](imgs/img_10.png)

### 4.Action序列化新增

openhands/events/serialization/action.py中新增GitRepoDownloadAction
![img_11.png](imgs/img_11.png)

### 5.Observation序列化新增

openhands/events/serialization/observation.py中新增GitRepoDownloadObservation
![img_12.png](imgs/img_12.png)

# tool工具的使用

## 新增Function Calling 调用

openhands/agenthub/codeact_agent/function_calling.py中的response_to_actions方法中新增工具GitRepoDownloadToolAction的解析
![img_13.png](imgs/img_13.png)

## RuntimeClient新增接口调用

1. ### 增加abstractmethod

openhands/runtime/base.py中新增abstractmethod  git_repo_download
![img_14.png](imgs/img_14.png)

1. ### 增加方法实现类

openhands/runtime/impl/action_execution/action_execution_client.py 增加git_repo_download请求实现方法
![img_15.png](imgs/img_15.png)

发送http请求到runtime-server
![img_16.png](imgs/img_16.png)

## RuntimeServer新增方法git_repo_download

openhands/runtime/action_execution_server.py中新增git_repo_download,action_execution_client发出的http请求到/execute_action接口接收后,进行action的方法转换处理
![img_17.png](imgs/img_17.png)
![img_18.png](imgs/img_18.png)

## Memory处理返回Observation

openhands/memory/conversation_memory.py新增GitRepoDownloadAction消息处理
![img_19.png](imgs/img_19.png)
![img_20.png](imgs/img_20.png)
![img_21.png](imgs/img_21.png)

## 工具调用用例

因为我们修改了runtime-server源代码,所以需要重新打包runtime镜像,将最新代码覆盖到镜像中,在项目相同目录层级加入dockerfile文件
![img_22.png](imgs/img_22.png)

[openhans_dockerfile](code/openhans_dockerfile)


```Plain
docker build --no-cache  -t runtime:0.48 -f openhans_dockerfile .
```

修改config.toml镜像名

```Plain
base_container_image = "runtime:0.48"
runtime_container_image = "runtime:0.48"
```
![img_23.png](imgs/img_23.png)

修改task.txt来测试工具是否添加并被Agent使用

[task.txt](code/task.txt)

```Plain
拉取Dliner代码
https://github.com/vivva/DLinear.git
```

执行启动脚本

```Plain
sh run.sh
```

查看容器内是否有工具调用
![img_24.png](imgs/img_24.png)
![img_25.png](imgs/img_25.png)

可以看到容器内日志中已经成功访问到我们新加的工具了
![img_26.png](imgs/img_26.png)

workspace下也成功下载了DLinear代码
