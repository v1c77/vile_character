---
title: postgresq-xl&docker分布式实践
date: 2017-02-15 16:20:14
category: develop
tags:
- docker
- postgre-xl
- postgre
---

> 本文在 2017年3月7日被重写。祝愿各位女王及屏幕那边的大雕萌妹们节日快乐。

<!--more-->
## 思路
- 全文围绕docker hub上的 potsgres-xl 镜像[在这][5]所写。
    - [github地址][6] 包括了 0.1/0.1 两版本。
    - 被重写前的博客 基于该repo 的 tag 0.1 ，使用 `pgxc_ctl` 自动化工具 及 ssh 隧道。有兴趣的可以去探索一波。其实还是蛮方便的。
    - 重写后的博客 fork from tag 0.2（默认提供docker-compose 部署方式）。我还是改成了swarm 构建方式。原因如下：[tirdpixel对使用swarm还是compose的解释][7]
- 本博客需要用到的源码， dockerfile， 及一些补充说明。都在[这里][9]。

## overview

- `OLTP` 联机事务处理
- `pssh` 用来多主机部署测试的工具
- 关于postgresql-xl 的更多中文介绍 可以看[这里][1]。
- postgre-xl 的[官方文档][3]详细介绍了使用方法。
![架构图][2]

- psql-xl 组件概述

    1. GTM（Global Transaction Monitor） 全局事务监视器

    确保集群范围内的事务一致性。（如果想要提升性能， 可以进一步添加各数据节点的 GTM proxy）

    2. Coordinator 协调器

        - 处理客户端网络链接。 数据库接入点。
        - 分析查询语句，执行计划， 将计划传递给 DataNode
        - 对DataNode 返回的查询中间结果做最后处理

    3. Data Node

        - 储存表和索引
        - 只有协调器 Coordinator  连接数据节点
        - 执行 Coordinator 发送的 查询
        - 节点间可以建立一对一连接。交换分布式表关联查询信息。

    4. GTM Proxy
        - 与Coordinator, Datanode 一起运行。
        - Coordinator 和 Datanode 于GTM Proxy 交互，proxy起到中间人的作用
        - 将原本对GTM 的请求进行分组归类。 多请求一次性提交给 GTM
        - 获取数据快照。


- 创建 postgres-xl 集群的注意事项。
    - 整个搭建过程都严重依赖各个节点的环境变量。
    - 把防火墙整好。


- docker 的补充知识
    - 创建swarm manager  `docker swarm init --advertise-addr *.*.*.*`
    - 在 想要加入为worker的host 运行 `docker swarm join 。。。。。` （init 完 会告诉你
    的。）
    - 查看swarm node `docker node ls`
    - 批量删除 swarm 容器 `docker service ls | grep "post" | awk '{print $1}' |
    xargs docker service rm`
    - 寡人写的一个查看 docker remote tags 的 [脚本][4]
    - 每次测试环境结束后都要记得清空那些东东。
        - volume：`docker volume prune`
        - network： `docker network prune`


## 实践

> 1 GTM 2proxy 2coordinator 10 datanode  in two swarm node


文档就不抄了，出来吧！ [传送门！！][8]




[1]: https://www.biaodianfu.com/postgres-xl.html
[2]: ./postgre-xl.jpg
[3]: http://files.postgres-xl.org/documentation/index.html
[4]: http://stackoverflow.com/questions/28320134/how-to-list-all-tags-for-a-docker-image-on-a-remote-registry/39454426#39454426
[5]: https://hub.docker.com/u/tiredpixel/
[6]: https://github.com/tiredpixel/postgres-xl-docker
[7]: https://github.com/tiredpixel/postgres-xl-docker/issues/11
[8]: https://github.com/woailuoli993/postgres-xl-docker/tree/master/deploy
[9]: https://github.com/woailuoli993/postgres-xl-docker
