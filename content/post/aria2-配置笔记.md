---
title: aria2 配置笔记
date: 2017-01-18
categories:
- develop
tags:
- aria2c
- docker
---

这里的天堂天空的颜色犹如地狱之火，但它仍然是天堂。---Lolita

> 注意：此文很可能只适用于mac ！！！---> 更新于某一天，现在因为用了docker 可能还是用于别的环境的。。。。

<!--more-->

{{< alert info >}}
 配置文件什么的不改 ==路径== 是不能用的！！
{{< /alert >}}

## 单纯安装&配置 aria2
1. 命令行`brew install aria2` 即可。2017年1月10日安装时版本为1.30。
2.配置。（之前copy了个几个貌似很权威的配置文件，结果能不能用 ）乖乖看了遍文档，照着几个大佬的配置文档自己写了一个，勉强能用了。
[aria2.conf][1]内容如下。

```
# 文件保存路径。
dir=/Users/vici/Downloads
# 为了启动后继续下载之前的文件 承接 save-session
input-file=/Users/vici/.aria2/session.dat
# 日志地址
log=/tmp/aria2_log.log
# 最高并行下载任务
max-concurrent-downloads=15
# 同服务器最多线程连接数
max-connection-per-server=15
# 校验文件完整性
check-integrity=true
# 断点续传
continue=true

# BitTorrent/Metalink Options
# 当下载的是一个种子(以.torrent结尾)时, 自动开始BT任务, 默认:true
#follow-torrent=true
# 本地节点查找
bt-enable-lpd=true
# 指定在多文件种子中最多能够打开的文件个数（火影忍者全集种子什么的）
bt-max-open-files=16
# 单个种子最大连接数
bt-max-peers=16
#dht-file-path=/opt/var/aria2/dht.dat
#dht-file-path6=/opt/var/aria2/dht6.dat
# 文档里说是设置dht使用的udp监听端口
#dht-listen-port=6801
#enable-dht6=true
# BT监听端口, 当端口被屏蔽时使用, 默认:6881-6999
#listen-port=51413
max-overall-upload-limit=0K
# 种子分享达到一定级别停止做种
seed-ratio=0

# RPC Options
# 启用rpc
enable-rpc=true
# 允许远程连接，所有来源的连接
rpc-allow-origin-all=true
# 允许非外部访问
rpc-listen-all=true
# 监听6800端口
rpc-listen-port=6800
# 设置的RPC授权令牌, v1.18.4新增功能, 取代 --rpc-user 和 --rpc-passwd 选项
#rpc-secret=<TOKEN>

# Advanced Options
# 启用守护进程。
daemon=true
# 禁用ipv6下载
disable-ipv6=true
#enable-mmap=true
# 保存旧任务
force-save=true
# 开始下载后是否预留文件大小的空间。默认为预留模式，保护磁盘mac需要注释这个配置！！
#file-allocation=prealloc
# 日志级别
log-level=warn
# 限制下载速度
# max-overall-download-limit=0K
# 配合input-file设置。
save-session=/Users/vici/.aria2/session.dat
# 下载失败后重新下载设置，默认为true
#always-resume=true
# 单个文件最大线程数
split=10
# 假设文件大小为30mb，min-split-size设置为10mb。则使用3个来源站。，文件大小为15则使用俩。
min-split-size=10M

#百度盘
user-agent=netdisk;5.2.6;PC;PC-Windows;6.2.9200;WindowsBaiduYunGuanJia
referer=http://pan.baidu.com/disk/home
```
3. 试着运行`aria2c --conf-path=/路径/aria2.conf`然后 用 yAAw 什么的UI试用一波。
稳妥起见 可以把 配置文件里面的 `deamon` 改为 false。

4. 如果很幸运的走到了这一步，接着写个deamon脚本 加载到mac的launchctl里。
`touch ~/Library/LaunchAgents/local.Aria2.plist`

- 在里面写入如下信息。
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">


<plist version="1.0">
<dict>
<key>RunAtLoad</key>
<true/>
<key>Label</key>
<string>aria2</string>
<key>ProgramArguments</key>
<array>
<string>/usr/local/aria2/bin/aria2c</string>
<string>--conf-path=/Users/vici/.aria2/aria2.conf</string>
</array>
</dict>
</plist>
```
- 运行 `launchctl load ~/Library/LaunchAgents/local.Aria2.plist`
- 重启 试一试。不行的话。。。。。。。。。。。。。。。。。。。。。。。。就算了。

## 使用docker 一次性配置 webui-aria2及 aria2服务。

最好还是看看 https://github.com/ziahamza/webui-aria2 的说明。
1. 拉源码，进入工作目录

```bash
git clone https://github.com/ziahamza/webui-aria2.git
cd webui-aria2
```
2. 如果你想将webui的默认语言改为中文。。。 而且像我一样找不到配置文件的套路（第二次更新）
可以在index.html的最后添加：

```javascript

<script>
  window.onload = function(){
    $(".flag-icon-cn").click()
  }
</script>

```

3. 修改Dockerfile （其实就改了一行。。。将 goreman setup 中的aria2启动部分做一些修改）

```Dockerfile
FROM debian:8

# less priviledge user, the id should map the user the downloaded files belongs to
RUN groupadd -r dummy && useradd -r -g dummy dummy -u 1000

# webui + aria2
RUN apt-get update \
	&& apt-get install -y aria2 busybox curl \
	&& rm -rf /var/lib/apt/lists/*

ADD . /webui-aria2

# gosu install latest
RUN GITHUB_REPO="https://github.com/tianon/gosu" \
  && LATEST=`curl -s  $GITHUB_REPO"/releases/latest" | grep -Eo "[0-9].[0-9]*"` \
  && curl -L $GITHUB_REPO"/releases/download/"$LATEST"/gosu-amd64" > /usr/local/bin/gosu \
  && chmod +x /usr/local/bin/gosu

# goreman supervisor install latest
RUN GITHUB_REPO="https://github.com/mattn/goreman" \
  && LATEST=`curl -s  $GITHUB_REPO"/releases/latest" | grep -Eo "v[0-9]*.[0-9]*.[0-9]*"` \
  && curl -L $GITHUB_REPO"/releases/download/"$LATEST"/goreman_linux_amd64.tar.gz" > goreman.tar.gz \
  && tar -xvzf goreman.tar.gz && mv /goreman_linux_amd64/goreman /usr/local/bin/goreman && rm -R goreman*

# goreman setup
RUN echo "web: gosu dummy /bin/busybox httpd -f -p 8080 -h /webui-aria2\nbackend: gosu dummy /usr/bin/aria2c --conf-path=/data/.aria2/aria2.conf" > Procfile

# aria2 downloads directory
VOLUME /data

# aria2 RPC port, map as-is or reconfigure webui
EXPOSE 6800/tcp

# webui static content web server, map wherever is convenient
EXPOSE 8080/tcp

CMD ["start"]
ENTRYPOINT ["/usr/local/bin/goreman"]
```
4. 生成镜像。

```
# 从dockerfile生成镜像
docker build -t yourname/webui-aria2 .
```

5.  准备数据卷
趁着生成镜像的时候 你可以开一个新的terminal，在 你的用户目录 新建一个aria2文件夹，及子文件，结构如下：
```
aria2
└── .aria2
    ├── aria2.conf
    ├── aria2.log
    └── session.txt
```


6. 并且修改配置文件 `aria2.conf`

文档中说明了几个重要文件在容器中的存放地点。
```
/data/.aria2/session.txt  (空文件。存放未下载完成的任务)
/data/.aria2/aria2.log    (空文件，记录日志)
/data/.aria2/aria2.conf   (aria2的日志)
/data/.downloads/        (文件下载地址。)
```
所以对原来的配置做了一点点改动来适应docker( [这个][2]可以直接用 )

```
# 文件保存路径。
dir=/data/.downloads
# 为了启动后继续下载之前的文件 承接 save-session
input-file=/data/.aria2/session.txt
# 日志地址
log=/data/.aria2/aria2.log
# 最高并行下载任务
max-concurrent-downloads=15
# 同服务器最多线程连接数
max-connection-per-server=15
# 校验文件完整性
check-integrity=true
# 断点续传
continue=true

# BitTorrent/Metalink Options
# 当下载的是一个种子(以.torrent结尾)时, 自动开始BT任务, 默认:true
#follow-torrent=true
# 本地节点查找
bt-enable-lpd=true
# 指定在多文件种子中最多能够打开的文件个数（火影忍者全集种子什么的）
bt-max-open-files=16
# 单个种子最大连接数
bt-max-peers=16
dht-file-path=/data/.aria2/dht.dat
#dht-file-path6=/opt/var/aria2/dht6.dat
# 文档里说是设置dht使用的udp监听端口
dht-listen-port=6801
#enable-dht6=true
# BT监听端口, 当端口被屏蔽时使用, 默认:6881-6999
listen-port=6802
max-overall-upload-limit=0K
# 种子分享达到一定级别停止做种
seed-ratio=0

# RPC Options
# 启用rpc
enable-rpc=true
# 允许远程连接，所有来源的连接
rpc-allow-origin-all=true
# 允许非外部访问
rpc-listen-all=true
# 监听6800端口
rpc-listen-port=6800
# 设置的RPC授权令牌, v1.18.4新增功能, 取代 --rpc-user 和 --rpc-passwd 选项
#rpc-secret=<TOKEN>

# Advanced Options
# 启用守护进程。
daemon=true
# 禁用ipv6下载
disable-ipv6=true
#enable-mmap=true
# 保存旧任务
force-save=true
# 开始下载后是否预留文件大小的空间。默认为预留模式，保护磁盘mac需要注释这个配置！！
#file-allocation=prealloc
# 日志级别
log-level=warn
# 限制下载速度
# max-overall-download-limit=0K
# 配合input-file设置。
save-session=/data/.aria2/session.txt
# 下载失败后重新下载设置，默认为true
#always-resume=true
# 单个文件最大线程数
split=10
# 假设文件大小为30mb，min-split-size设置为10mb。则使用3个来源站。，文件大小为15则使用俩。
min-split-size=10M

#百度盘
user-agent=netdisk;5.2.6;PC;PC-Windows;6.2.9200;WindowsBaiduYunGuanJia
referer=http://pan.baidu.com/disk/home
```


7.  生成容器(需要改路径！)

```
docker run --restart=always -d -v /Users/vici/aria2/:/data -v /Users/vici/Downloads/aria2_dl:/data/.downloads -p 6800-6802:6800-6802 -p 9100:8080 --name="webui-aria2" vici/webui-aria2-debain
```
其中 `Users/vici/Downloads/aria2_dl`为我下载文件的存放地址。`/Users/vici/aria2`为之前新建的相关文件目录（记得改）。


成果应该是这样子滴：
![webui-aria2][3]

。。。全文完。。。
----------------


## 让人抓狂的lowb想法：用mac自带的apache部署web-ui

为了保持web ui能保持deamon，感觉可以使用mac自带的apache服务器。（测试时候可以用python -m simplehtttpserver 或者node.js）

1. 前期测试: 查看版本 试运行  打开浏览器 http://localhost

```
# 查看版本
sudo apachectl -v
# 启动
sudo apachectl start
# 浏览
open http://localhost
```
2. 开启虚拟主机。 配置网站。
    - 在终端运行`sudo vi /etc/apache2/httpd.conf`，打开Apche的配置文件
    - 在httpd.conf中找到`#Include /private/etc/apache2/extra/httpd-vhosts.conf`，去掉前面的“＃”，保存并退出。
    - 运行`sudo apachectl restart`

    - 运行 `sudo vi /etc/apache2/extra/httpd-vhosts.conf`

    你会看到两段配置信息 类似'<VirtuaHost *:80>....'什么的。这两个主机是不存在的。所以此时访问localhost会提示403错误：`Forbidden
You don't have permission to access /index.php on this server`. 网上的大佬说用# 注释掉就好。

    >  事实证明apache 的方法真的是很lowb。什么 user Root 乱七八糟的搞了半天，丢雷楼某黑。 是我想多了。还是乖乖的用docker。


[1]: ./aria2.conf
[2]: ./aria2-docker.conf
[3]: http://qiniu.heyuhua.com/2017-01-19%2014webui-aria2.png
