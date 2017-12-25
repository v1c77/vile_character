---
title: celery任务分发-术业有专攻的worker们
date: 2016-11-29
categories:
- develop
tags:
- python
- celery
---

本事借的钱，为什么要还？

> 此文章脱胎于我在stackoverflow的某回答
<!--more-->

# celery 高阶用法


## 需求

项目需要多个任务队列进行任务分发，每个队列的任务都会请求获取某种资源。
CTO大人给的建议是使用线程模型自己维护队列。（说实话我当时就怒了） 什么年代了？昂？当然我并没有为此而辞职

## 环境
- linux (Centos/ubuntu/arch)
- pyhon 2.7
- celery 任务队列中间件(djcelery 及flask 都适用)


## 干活

### celery worker 部署代码

下面的代码实现了：
- 生成了一堆以`w_*` 命名的 worker 和 以 `q_*`命名的任务队列，限制各个worker的并发数及绑定worker 与队列
    + `w_celery` 负责默认`celery`队列，并发数为10，
    + 剩下的worker 都为单线程任务， 绑定各自的任务队列
    + `-A celery_worker.celery`  表明了任务内容
    + `-Q celery` 设置了默认队列为 celery
    + `--pidfile`,`--logfile` 定义了进程文件及日志名称规范及存放地点
```bash
celery multi start w_celery w_sas w_aosp w_avpro w_pw764 w_pw786 w_pxp w_cwxp w_cw786 \
-c 1  -A celery_worker.celery -l debug -Q celery --pidfile=/tmp/celery_%n.pid --logfile=/tmp/celery_%n.log  \
-Q:w_celery celery -c:w_celery 10 \
-Q:w_sas q_sas \
-Q:w_aosp q_aosp \
-Q:w_avpro q_avpro \
-Q:w_pw764 q_pw764 \
-Q:w_pw786 q_pw786 \
-Q:w_pxp q_pxp \
-Q:w_cwxp q_cwxp \
-Q:w_cw786 q_cw786
```

### task定义及调用方法示例

```python?linenumber=true

# 定义


@celery.task
def sub_sas(*args):
    # 申请某独占资源

    pass

# 如何在调用时绑定queue


def sub():
    sub_sas.apply_async(args=(), queue='q_sas')  # 将sas任务 提交到q_sas 队列，从而交由w_sas 实现  
```
通过这样的绑定即可实现worker的术业专攻，并通过上下文控制（with）独占资源的锁


老哥稳！
