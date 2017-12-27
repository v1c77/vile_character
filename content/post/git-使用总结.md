---
title: git 使用总结
date: 2016-12-01 19:09:25
category: develop
tags:
 - git
---

> They are gonna get me one wey or another.

<!--more-->
## 从一个分支上建立新分支

- 首先要切换到爹爹分支
```
git checkout master
```
- 然后生成儿子
```
git checkout -b hedada
```
- 然后提交到云
```
git push origin hedada
```

## 建立与远程分支的联系
```
git push --set-upstream origin hedada
```
- - -

## 删除分支 并删除云上的自己

- 删除本地

```git
git branch -d hedada
```
- 删除远程分支
```
git push origin 空格:hedada
```
- - -

## 将分支合并到当前分支

- 如果是master

- 可以使用marge提交其他分支的修改

```git
git checkout master

git marge hedada
```
- 如果在hedada 想把 远程的 master 合并倒当前

```git
git pull origin master

git add .

git commit -m "update"

git push
```
-------------
## 将本地缓存的东东删除

```git
git reset HEAD
```
```git
git branch -m old_branch new_branch         # Rename branch locally    
git push origin :old_branch                 # Delete the old branch    
git push --set-upstream origin new_branch   # Push the new branch, set local branch to track the new remote
```


## pull 时候把本地覆盖
```
git fetch --all  
git reset --hard origin/master
```

## init仓库并连接到远程
```
git init
git remote add orgin
```


## 我在检查代码的时候发现把种子传上git去了，觉得很羞耻，想让他在记录中消失
> 我想保存当前代码（修复过的），只是把历史线中的一次提交删除

```bash

# 首先git log 查看 提交历史 得到代有种子的那次提交
git log
# 从想要删除的commit的上一次提交开始删除提交历史（很绕口）
git rebase -i <想删除的提交的上一个提交>
# 把要删除的提交行删掉， vi 环境，保存退出
# 将冲突修改完成后
git rebase --continue
#覆盖远程提交历史
git push -f

#


```

## 在项目repo中进行svn模式的开发。
当与团队同事在一个三方repo中进行合作开发。
比如 有一个repo asm_team/client， 你和同时分别有 luoli/client, dashu/client的fork，
你们要同时在一个主repo的branch ‘feature/next_version’上开发。

1. 进行开发。

```
# 切换到远程开发分支
git checkout asm_team/feature/next_version
# 创建本地开发分支
git checkout -b feature/next_version
# 一顿操作之后提交
...
git commit -m 'v1.2.3'
git push asm_team feature/next_version:feature/next_version
```

2. 同步线上代码

```
git pull --rebase asm_team/feature/next_version
```

## submodule

- 添加子模块到项目

```
git submodule add woailuoli993/ooooxxxx
```

- 拉取一个包含子项目的项目。。

```
git submodule init
git submodule update
```

- 让项目中的所有子项目统一行动
```
# 比如 列出所有的子项目的diff。
git submodule foreach git diff
```
