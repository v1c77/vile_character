---
title: pyenv 常用命令
date: 2017-04-20 17:54:00
categories:
- develop
tags:
 - python
---

>明日再有风雨，明日再作打算

<!--more-->


{{< alert info >}}
**Tip：每次使用brew 安装后注意认真阅读安装信息，或者使用 brew info 命令查看。**
{{< /alert >}}

## 安装/卸载

> ### 安装
```
$ brew update
$ brew install pyen
$ brew upgrade pyenv

```
*upgrade* 可以用来更新 pyenv

> ### 卸载
```
 brew uninstall pyenv
```

## 常规使用



> ### 列出所有可安装python版本

```
pyenv install --list
```

> ### 安装
```
pyenv install 3.6.0
```

> ### 查看现有版本
```
pyenv versions
```
> ### 设置全局环境
```
pyenv global 3.6.0
```

> ### 设置当前目录环境
```
pyenv local 2.7.13
```

> ### 查看当前目录使用版本
```
pyenv version
```

> ### 删除某个版本
```
pyenv uninstall 2.7.10
```

## pyenv-virtualenv

> ### 安装
```
brew install pyenv-virtualenv
```
似乎还需要添加参数到 你的 `.bashrc/.zshrc`里,详见`brew info pyenv-vritualenv`

> ### 创建一个虚拟环境
```
pyenv virtualenv 3.6.0 tensorlering-env-3.6
```

上述命令会在 `pyenv root` 目录下生成新的基于`3.6.0`虚拟环境`tensorflow-env-3.6`。

> ### 为虚拟环境的pip加速（国内用户）
出于某些原因，pip安装依赖包有辣么一点点慢。
将默认源替换为豆瓣源是个很好的选择（https://pypi.doubanio.com/simple）

不同于普通的pip配置（将pip源写入 ~/.pip/pip.conf）,virtualenv 的pip配置需要写入到 `(pyenv root)/虚拟环境名／pip.conf`下。
比如我的tensorlearing-env 环境的pip配置文件就位于：
```
/usr/local/Cellar/pyenv/1.0.7/versions/3.6.0/envs/tensorlering-env-3.6/pip.conf
```

**pip.conf** 内容：
```
[global]
timeout = 60
index-url = https://pypi.doubanio.com/simple
```
