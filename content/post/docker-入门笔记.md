---
title: docker 入门笔记
date: 2016-11-28 19:48:21
category: develop
tags:
    - docker
---

<!-- toc -->
# 入门

* [入门手册一(偏理论)](https://www.gitbook.com/book/hujb2000/docker-flow-evolution/details)
* [入门手册二(偏实践)](https://www.gitbook.com/book/yeasy/docker_practice/details)
## qus1: 使用安装docker后 使用普通用户无法运行`docker run` AND `docker version`
<!--more-->
### 错误提示:
> Cannot connect to the Docker daemon. Is the docker daemon running on this host?

在使用`groupadd` 添加了docker 用户组及 将当前 ==$USER== 添加到用户组之后,__务必要进行注销重新登录__

```shell?linenums=false
cat /etc/group # 可以获取当前系统所有组及权限
```

## 技巧1: 使用阿里云做ecs 的docker 镜像下载加速
[点进这里申请及查看自己的加速地址](https://cr.console.aliyun.com/#/accelerator)
* 一下是ubuntu 14.04 的配置加速器命令
```perl
echo "DOCKER_OPTS=\"\$DOCKER_OPTS --registry-mirror=https://95s2tvj3.mirror.aliyuncs.com\"" | sudo tee -a /etc/default/docker
sudo service docker restart
```

* 以下是 centos 7的..
```bash
sudo cp -n /lib/systemd/system/docker.service /etc/systemd/system/docker.service
sudo sed -i "s|ExecStart=/usr/bin/docker daemon|ExecStart=/usr/bin/docker daemon --registry-mirror=https://95s2tvj3.mirror.aliyuncs.com|g" /etc/systemd/system/docker.service
sudo systemctl daemon-reload
sudo service docker restart
```

其中那个神奇的域名(https://95s2tvj3.mirror.aliyuncs.com)是 阿里云开发者账号生成的个人加速镜像地址

## 技巧2: 修改docker 容器镜像的默认地址（ubuntu16.04）：
```bash
# 关闭服务
systemctl stop docker
sudo mv /var/lib/docker /data/docker
sddo ln -s /data/docker /var/lib/docker
systemctl start docker
```


## docker 部署工具(自动化部署):

* Swarm
* Rancher
* Kubernetes
* Helios

## 大白话
** docker与虚拟机的相互理解:

|   docker |    像啥    |  术语  |
| -------  |    ------:   | :---:  |
|   镜像    |    iso 系统镜像   |   image   |  
|   容器    |   跑着的虚拟机    |   Container   |
|   仓库    |       github      |   repository  |   


++使用`docker run` 命令 相当于 在虚拟机中进行了一次从iso 到 运行实例的 过程++

* docker client 操纵 docker daemon, docker deamon 为底层的管家
* 由上面的大白话可以推测出, 镜像(image) 是只读对象 ,类似于工厂函数,可以创建多个实例 容器
* 因为镜像的只读性, 容器在启动时会在 最上层添加 可写层 做个性化部署

docker 基于 linux 的容器机制实现  其中关于 namespace  的进程 隔离部分 及 文件系统的分层 readonly / readwrite 决定了 docker 的运行机制

## 镜像操作

#### 显示所有本地存放的镜像
```bash
docker images
```

#### 从镜像仓库拉取镜像
```bash
docker pull imagename
```

#### 运行镜像
```bash
docker run imagename
```

### 容器常用操作命令

#### 启动容器

启动容器有两种方式，一种是基于镜像新建一个容器并启动，另外一个是将在终止状态（stopped）的容器 重新启动。
```bash
$sudo docker run node:latest /bin/echo "Hello World"
$sudo docker run -t -i node:latest /bin/bash
```
其中， `-t` 选项让Docker分配一个伪终端（pseudo-tty）并绑定到容器的标准输入上， `-i` 则让容器的标 准输入保持打开。
当利用 `docker run` 来创建容器时，Docker 在后台运行的标准操作包括：
检查本地是否存在指定的镜像，不存在就从公有仓库下载
利用镜像创建并启动一个容器
分配一个文件系统，并在只读的镜像层外面挂载一层可读写层
从宿主主机配置的网桥接口中桥接一个虚拟接口到容器中去
从地址池配置一个 ip 地址给容器
执行用户指定的应用程序
执行完毕后容器被终止
docker run 命令参数较多，可以通过以下命令`docker run --help`查看参数

可以利用 `docker start [containerId|containerName]` 命令，直接将一个已经终止的容器启动运行。
#### 重启容器

`docker restart` 命令会将一个运行态的容器终止，然后再重新启动它。
#### 守护态运行

更多的时候，需要让 Docker 容器在后台以守护态（Daemonized）形式运行。此时，可以通过添加 -d 参 数来实现。
#### 进入容器

`docker exec -it [containerId|containerName] /bin/bash`
获取容器的输出信息

要获取容器的输出信息，可以通过 `docker logs [containerId|containerName]` 命令。
#### 查看容器
```bash
$ sudo docker ps  # 查看正在运行的容器
$ sudo docker ps -a  # 查看所有的容器状态
```
#### 删除容器

可以使用 `docker rm` 来删除一个处于终止状态的容器。如果要删除一个运行中的容器，可以添加 ==-f== 参数。Docker 会发送 SIGKILL 信号给容器。
删除所有容器 `docker rm $(docker ps –a –q)`
### `docker run` 命令 重要参数
==-b==:  默认是空，附加在已存在的网桥上，如果是用'none'参数，就禁用了容器的网络  
==-p==：随机映射容器的所有暴露端口给主机 -p: 映射容器端口给主机
==--env==: 设置环境变量
==-v==: 挂载一个数据卷
==-entrypoint==:   覆盖镜像的默认的入口指令
==--name==: 给容器指定一个名称
==--link==: 连接另外的容器

#### 在原有镜像的基础上创建镜像
首先在`docker run` 之后一顿操作
然后:
```bash
docker commit -m "提交说明" -a "指定更新用户信息" 01231412981 huahua/start:test
# 上面的一串数字是容器id
```
* 容器id 就是 打开 docker bash 后的主机名
* 最后一部分为目标镜像的仓库名和tag 名

####  通过dokerfile 生成镜像
使用 docker commit 来扩展一个镜像比较简单，但是不方便在一个团队中分享。我们可以使用 docker build 来创建一个新的镜像。为此，首先需要创建一个 Dockerfile，包含一些如何创建镜像的指令。
新建一个目录和一个Dockerfile:
```dockerfile
# This is a comment
FROM node:latest
MAINTAINER Vi.Ci<heyuhuade@gmail.com>
RUN apt-get -qq curl
RUN apt-get -qq babe-cli
```
编写完成 Dockerfile 后可以使用 docker build 来生成镜像。
```bash
$ sudo docker build -t "huahua/start:v2" .
```
其中 ==-t== 标记来添加 tag，指定新的镜像的用户信息。 “.” 是 Dockerfile 所在的路径（当前目录），也可以 替换为一个具体的 Dockerfile 的路径。

Dockfile 中的指令被一条一条的执行。每一步都创建了一个新的容器，在 容器中执行指令并提交修改（就跟之前介绍过的 docker commit 一样）。当所有的指令都执行完毕之 后，返回了最终的镜像 id。所有的中间步骤所产生的容器都被删除和清理了。

**值得注意的是在dockerfile中的命令都必须避免io交互**
例如:
* 在ubuntu中 apt-get 要根据情况加上 ==-qq==(除了错误外什么都不输出 | linux哲学中有一条:什么都不提示就是最好的情况) 或者 ==-y==(对所有的询问回答yes)

------------------------------------------
##############################上面是入门笔记#################################

## docker 项目部署
**(按照官方文档进行安装)**
* ### 在安装后的一些必要操作
    * 添加docker用户组 并将docker管理者添加到group中
        1. `sudo group add docker` 添加docker用户组
        2. `sudo usermod -aG docker huahua` 将花花添加到docker 组
        3. `sudo service docker restart` 重启docker deamo
    * 将docker 添加到开机自启动后退出root
        4. `sudo chkconfig docker on`
        5. 切换到 huahua 进行 无拘无束的docker操作
* #### 项目文件 存放在数据卷或着数据卷容器中
数据卷的添加 可以看做mount

使用 -v 标记也可以指定挂载一个本地主机的目录到容器中去。

```bash
$ sudo docker run -d -P --name web -v /src/webapp:/opt/webapp training/webapp python app.py
```
上面的命令加载主机的 /src/webapp 目录到容器的 /opt/webapp 目录。这个功能在进行测试的时候十分方便，比如用户可以放置一些程序到本地目录中，来查看容器是否正常工作。本地目录的路径必须是绝对路径，如果目录不存在 Docker 会自动为你创建它。

* 注意：Dockerfile 中不支持这种用法，这是因为 Dockerfile 是为了移植和分享用的。然而，不同操作系统的路径格式不一样，所以目前还不能支持。

Docker 挂载数据卷的默认权限是读写，用户也可以通过 :ro 指定为只读。

```bash
$ sudo docker run -d -P --name web -v /src/webapp:/opt/webapp:ro
training/webapp python app.py
```
加了 :ro 之后，就挂载为只读了。

查看数据卷的具体信息

在主机里使用以下命令可以查看指定容器的信息

```bash
$ docker inspect web
```
...

* ### 实验环节: 在app2上部署mongo replica arbiter(仲裁者)
    * 从hub中下载合适的mongo镜像(version 3.0.1)
    **一定要使用阿里提供的加速服务,否则慢的爆炸**

    ```bash
    docker pull mongo:3.0.1
    ```
    * 在宿主机上创建mongo的数据目录及配置文件目录 并映射到容器
        * 数据目录
        ```bash
        $ sudo mkdir -p /data/mongo_data/mongo_arbiter
        $ sudo chmod -R a+rw /data/mongo_data/
        ```
        * 生成上线仲裁者容器
        日志目录绑定; db数据目录绑定; 端口绑定;
        ```
        docker run --name ksx_arbiter -p 10.163.8.90:27099:27017 -v /data/mongo_data/mongo_arbiter:/data/db -d mongo:3.0.1 --replSet "ksxingrs1"
        ```
        `--name` 定义了容器名
        `-p` 将内网ip的27099 端口映射到了docker中的mongodb端口
        `-v` 必要的目录及文件映射
        `-d` 建守护进程

        * 切换到 db1 服务器 ->添加arbiter节点
        ```mongo
        > rs.addArb('10.163.8.90:27099')
        ```
        * 返回app2 进入 ksx_arbiter -> 查看 mongo状态
        ```
        docker exec -it ksx_arbiter /bin/bash
        ```

        * 如果有错误 查看docker 日志信息
        ```
        sudo journalctl -u docker
        ```
-------------------------------- 全文完 ---------------------------------



* ### 某部署版方案简略(请略过)

    * mongo docker 快速部署
        * 配置文件目录
        ```bash

        $ sudo mkdir /data/mongo_data/mongo_conf
        ```
        * 日志目录
        ```
        $ sudo mkdir /data/mongo_data/mongo_log
        ```
        * 使用配置(上传到了公司知识库)
        ```
        $ sudo vi /data/mongo_data/mongo_conf/mongo.conf
        systemLog:
            destination: file
            path: "/data/mongo_data/mongo_log/mongodb.log"
            logAppend: true

        storage:
            journal:
                enabled: true

        processManagement:
            fork: true
        ```

    * mysql
    **版本:5.6.31**

    * mecache

    * nginx
    **目前使用的nginx 版本为 1.6.2**

    * python 环境 flask
