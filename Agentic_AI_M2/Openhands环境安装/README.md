## openhands环境安装

#### 依赖准备

##### Docker 安装

###### 软件下载

官网地址: https://www.docker.com/

点击地址进入官网
![img.png](imgs/img.png)

根据自身电脑版本下载安装包
![img_1.png](imgs/img_1.png)

###### 软件安装

[Windows安装参考视频](https://www.bilibili.com/video/BV1Vk4y1V7bV/?spm_id_from=333.337.search-card.all.click&vd_source=99a1a0fc95d22736eceeb45b8bf76c45)

MacOS:

打开安装包,拖拽图标到Applications
![img_2.png](imgs/img_2.png)
####  软件启动

点击Docker Desktop应用打开界面,启动docker完成
![img_3.png](imgs/img_3.png)

#### Openhands-0.48.0

##### 源码下载:

[OpenHands_0.48.0.zip](code/OpenHands_0.48.0.zip)

点击下载地址下载源码压缩包
![img_4.png](imgs/img_4.png)

解压缩文件夹
![img_5.png](imgs/img_5.png)
##### 镜像准备:

终端执行命令

```Plain
docker pull ghcr.io/all-hands-ai/runtime:0.48-nikolaik
```
![img_6.png](imgs/img_6.png)

![img_7.png](imgs/img_7.png)
下载完成后

执行镜像查看命令查看镜像

```Plain
docker images 
```
![img_8.png](imgs/img_8.png)

可以在docker desktop中查看
![img_9.png](imgs/img_9.png)

##### 依赖安装

1、打开VSCode
![img_10.png](imgs/img_10.png)

2、打开资源管理器
![img_11.png](imgs/img_11.png)

3、点击打开文件夹
![img_12.png](imgs/img_12.png)

4、选择解压完成的openhands代码文件夹并点击打开按钮
![img_13.png](imgs/img_13.png)

5、新建终端
![img_14.png](imgs/img_14.png)

6、选择创建的自定义的python环境,若没有创建参考第二部分python环境准备（此处的python环境必须>=3.12）中Conda下的创建自定义python环境

终端输入以下代码并执行

```Plain
conda create -n python_env python=3.12
conda activate python_env
```
![img_15.png](imgs/img_15.png)
![img_16.png](imgs/img_16.png)

7、终端输入命令安装程序依赖

```Plain
pip install -e .
pip install Deprecated
```
![img_17.png](imgs/img_17.png)
![img_18.png](imgs/img_18.png)

安装完成
![img_19.png](imgs/img_19.png)

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
![img_20.png](imgs/img_20.png)

2、添加DeepSeek-API Key

双击打开config.toml

![img_21.png](imgs/img_21.png)
找到[llm.deepseek]配置
![img_22.png](imgs/img_22.png)

替换为我们已经申请的deepseek-key
![img_23.png](imgs/img_23.png)

3、确认切换python环境

终端确认已经切换到openhands所应用的python环境,如果没有执行命令切换

```Plain
conda activate python_env
```
![img_24.png](imgs/img_24.png)

4.运行脚本文件

```Plain
sh run.sh
```
![img_25.png](imgs/img_25.png)
openhands运行启动容器
![img_26.png](imgs/img_26.png)

5、查看容器

打开docker desktop可以查看到已经启动了一个openhands容器,点击打开
![img_27.png](imgs/img_27.png)

容器内已经在启动程序
![img_28.png](imgs/img_28.png)

6、查看大模型对话

查看openhands目录下logs/llm文件夹,该文件夹是agent的对话信息,prompt和response是成对生成
![img_29.png](imgs/img_29.png)

7、查看运行结果

终端输出已经完成创建python代码文件并输出hello_world
![img_30.png](imgs/img_30.png)

8、验证结果

查看任务容器已经结束,点击运行重新启动容器

![img_31.png](imgs/img_31.png)
点击exec进入命令窗口
![img_32.png](imgs/img_32.png)

输入以下命令并执行

```Plain
bash
```
![img_33.png](imgs/img_33.png)

执行命令查看是否有生成文件

```Plain
cd /workspace && ls
```
![img_34.png](imgs/img_34.png)

查看文件内容

```Plain
cat hello_world.py
```
![img_35.png](imgs/img_35.png)

helloworld代码已创建,运行校验
![img_36.png](imgs/img_36.png)

正确输出hello world 验证完成