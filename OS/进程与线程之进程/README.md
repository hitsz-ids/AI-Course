# 进程与线程之进程

\[实验脚手架\.pptx\]

# 一、准备deepseek api key

本实验采用deepseek作为模型提供方。

## 1、创建api key

需要提前准备deepseek账号。如果没有，请先注册并充值：https://platform.deepseek.com/sign_up

进入deepseek管理页面。左侧选择“API keys”，然后点击“创建API key”。

![Image](img/1.PNG)

输入一个名称，比如myos。然后点击“创建”。

![Image](img/2.PNG)

点击“复制”，把API key复制下来，后续需要使用。

![Image](img/3.PNG)

## 2、充值

左侧选择“充值”，进入充值页面。充值10元即可。

![Image](img/4.PNG)

# 二、codex使用配置

本实验采用codex作为AI辅助开发环境，按照以下配置。

## 1、下载codex

https://openai\.com/zh\-Hans\-CN/codex/

## 2、退出登录

**注意：**如果之前在codex客户端上登陆过codex账号，请先退出。如果未登录过，忽略此步骤。

方法如下

在左下角的“设置”，点击“账户”。

![Image](img/5.PNG)

会弹出浏览器访问的chatGPT页面。左下角点击“退出登录”。

![Image](img/6.PNG)

## 3、配置api key

这里采用deepseek作为模型提供方。会用到之前创建的deepseek api key。

配置方式：https://api\-docs\.deepseek\.com/zh\-cn/quick\_start/agent\_integrations/codex

推荐使用链接中描述的“一键配置脚本”

macOS/Linux用户，在命令行运行

```Bash
bash <(curl -fsSL https://cdn.deepseek.com/api-docs/codex-deepseek-setup.sh)
```

Windows用户，在命令行运行

```Bash
irm https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.ps1 | iex
```

根据提示，选择要执行的操作。这里输入数字`1`，表示使用deepseek\-v4\-flash模型。

然后输入之前创建的api key，以sk开头。按回车，配置完成。

![Image](img/7.png)



如要恢复原始配置，再次运行脚本，选择`9`即可。

## 4、测试

此步骤确保codex能正常使用大模型。

开始一个新对话

![Image](img/8.png)

输入“你好”，查看是否能正常访问

![Image](img/9.png)

一些特殊的配置要求，由于后续codex需要访问docker，为了更方便可以直接开启`完全访问权限`（当然也可开启`帮我批准`模式，当codex需要访问命令时由我们来同意）

![Image](img/10.png)

![Image](img/11.png)

![Image](img/12.png)

![Image](img/13.png)

# 三、使用codex开始进行进程的实验

## 了解操作系统的启动过程

1. 打开codex，开启一个新对话

![Image](img/14.png)

2. 跟codex进行交互，了解操作系统的启动流程

```Plain Text
一个操作系统是如何启动的呢
```

![Image](img/15.png)

下面将使用codex编写bootloader启动程序和进程创建的程序。这里展示了GPT\-5\.5版本和deepseek\-v4\-flash两种不同模型版本的实验结果。

具体的实验结果不能保证一模一样，可能会有所差异。

## bootloader启动程序与进程创建（deepseek\-v4\-flash版本）

1. 跟codex进行交互，安装qemu，模拟目标机器，安全地跑操作系统

```Plain Text
我现在想要用qemu，再不影响当前系统的前提下，使用虚拟的方式，以docker的方式安装好qemu，来运行操作系统
```

![Image](img/16.png)

2. 让codex创建qemu镜像环境

```Plain Text
我现在想要用qemu，那么你根据我当前电脑的型号，帮我构建docker镜像
你基于一个ubuntu的镜像开始帮我做，并且要安装好qemu和相关依赖为后续我们去编写和运行操作系统做代码做好准备
如果你发现官方的docker无法访问，可以使用以下的源地址去拉去镜像：
https://daocloud.io
https://tencentyun.com
帮我启动并开启ssh链接
```

![Image](img/17.png)

根据提示使用ssh登录一下容器

```Bash
ssh dev@127.0.0.1 -p 2223
```

![Image](img/18.png)

3. 让codex把容器补成 Codex Desktop能识别的远端主机

```Bash
把docker镜像配置成codex可以通过ssh登录的机器
```

![Image](img/19.png)

4. 在codex配置中添加ssh链接，让codex能链接到docker中环境中

左下角点击“设置”。

![Image](img/20.png)

选择“连接”，在出现的连接页面，点击“添加”。

![Image](img/21.png)

此时出现可连接的机器列表。

![Image](img/22.png)

此时显示已连接的状态

![Image](img/23.png)

5. 在docker中创建一个项目，开始让codex创建一个bootloader并输出hello world

![Image](img/24.png)

6. 让codex帮我编写最小集的第一操作系统

```C
我现在是什么环境，现在的cpu指令集是什么，你给我写一个操作系统的汇编启动代码，输出hello world
并且你帮我运行，让我可以直接看到结果
```

![Image](img/25.png)

7. 验证实验结果。根据codex的提示进行复现。

![Image](img/26.png)

```Bash
ssh dev@127.0.0.1 -p 2223
cd /home/dev
nasm -f bin boot.asm -o boot.bin
qemu-system-i386 -display none -monitor none -serial stdio \
  -drive file=boot.bin,format=raw,if=floppy
```

![Image](img/27.png)

**Tips: 如果ssh无法链接进去的话，可以使用docker直接进入：**

打开一个terminal，输入docker ps，根据复制当前运行的qemu镜像的container id并输入

docker exec \-it \{container\_id\} bash 进入到docker内部直接运行codex输出的脚本，可以看到Hello, world\! 一个最小版的bootloader就完成了

```Plain Text
# 这里请注意，根据根据codex的输入来
cd /home/codex/aarch64-os-startup
make run
```

![Image](img/28.png)

![Image](img/29.PNG)



![Image](img/30.PNG)

可以看到我当前的cpu是arm64的，所以使用了qemu\-system\-aarch64的交叉编译链进行编译

8. 接下来我们基于这个bootloader，来进行编写进程

```C
你就基于bootloader程序进行升级与修改，用这个最小的os，而不是直接使用本身的系统，实现一个fork功能。要有系统调用。通过bootloader启动后，进入fork功能，父子进程的输出要显示pid。
要有用户态的testfork程序，用户态程序从main为入口，调用fork，用c语言实现。
```

![Image](img/31.png)

根据结果提示，在命令行中输入以下命令进行验证

```Bash
ssh dev@127.0.0.1 -p 2223
cd /home/dev/minios
bash build.sh
qemu-system-i386 -drive file=build/os.img,format=raw,if=floppy \
  -display none -monitor none -serial stdio -no-reboot
```

![Image](img/32.png)

9. 为了能让我们更好观察，把整个bootloader和程序不要直接退出，可以看到程序与进程的持续输出

```C
主程序与进程应该会一直存在一段时间，持续输出内容，可以实现sleep的内核调用，然后可以一段时间后再退出
要注意，我这里要的是主程序和进程，执行一段时间后再停止，等待输出q就退出OS
```

![Image](img/33.png)

复现命令不变。

![Image](img/34.png)

根据结果提示，在命令行中输入以下命令进行验证

```Bash
ssh dev@127.0.0.1 -p 2223
cd /home/dev/minios
bash build.sh
qemu-system-i386 -drive file=build/os.img,format=raw,if=floppy \
  -display none -monitor none -serial stdio -no-reboot
```

![Image](img/35.png)

10. 最后让codex帮我们review和解释一下当前的代码

```C
你也帮我review一下代码，说明这里你编写的bootloader和fork汇编代码是哪些，怎么理解，同时用户态的程序代码是哪些，怎么理解，然后你如何确定当前的程序不是直接使用了我们系统的调用而是我们自己实现的bootloader内的调用，你给出详细解释和具体的流程图
```

![Image](img/36.png)



