#!/bin/bash

# 下载 qlib 二进制数据包
echo "正在下载 qlib_bin.tar.gz ..."
curl -L -o qlib_bin.tar.gz https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz

# 检查下载是否成功
if [ $? -ne 0 ]; then
    echo "下载失败，请检查网络或链接。"
    exit 1
fi

# 创建目标目录（如果不存在）
mkdir -p ~/.qlib/qlib_data/cn_data

# 解压到目标目录，并去掉顶层目录结构
echo "正在解压到 ~/.qlib/qlib_data/cn_data ..."
tar -zxvf qlib_bin.tar.gz -C ~/.qlib/qlib_data/cn_data --strip-components=1

# 检查解压是否成功
if [ $? -ne 0 ]; then
    echo "解压失败，请检查 tar 包内容。"
    exit 1
fi

# 删除压缩包
echo "删除临时文件 qlib_bin.tar.gz ..."
rm -f qlib_bin.tar.gz

echo "完成！数据已放置在 ~/.qlib/qlib_data/cn_data"