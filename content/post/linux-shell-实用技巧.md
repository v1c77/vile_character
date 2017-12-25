---
title: linux shell 实用技巧
date: 2016-12-02
category: develop
tags:
    - linux
    - shell
---

linux忽悠原则： 一切皆文件， 通信皆管道， 不管闲事，不说废话.(只能信50%)
<!--more-->

## 统计常用命令 （使用次数最多的10条命令）
```bash
 history | awk '{print $2}' | sort | uniq -c | sort -k1,1nr | head -10n
```
> Tips: ohmyzsh扩大了history 记录行数到2000，大概索引宝宝平时一个月的命令 ，可以按需求修改 `~zshrc`


## 批量修改文件名（rename）
> rename 在各发行版语法不同，写通用脚本宁可用 `mv` ... 示例运行在ubuntu16.04

- 修改当前目录下的所有`.log` 文件为`.json` 格式
```bash
rename 's/.log$/.json/' *.log
```

## 递归删除匹配到的文件

> 首先需要知道的是在bash／zsh 环境中， 不加引号的语句会首先被zsh 或者 bash 解析
所以 类似 `rm -r *.pyc` 这种语句是错误的（并不会像你想象的那样删除所有子目录下的pyc 文件）

- stackoverflow上评分最高的两个答案：
    1. `find . -name "*.pyc" -exec rm -rf {} \;`  
    2. `find . -name '*.pyc' -delete` 这种显然看上去更为安全一些。毕竟看到 `rm -rf` 这样的东东总是感觉很害怕。


## 命令行reformat log 文件
比如说将log中的回车显式表示。`sed -e ’s/#012/\n/g’`
