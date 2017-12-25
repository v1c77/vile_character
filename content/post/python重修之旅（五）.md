---
title: python重修之旅（五）
date: 2017-09-19
categories:
- develop
tag: python
coverImage: //qiniu.heyuhua.com/Free-cross-wallpaper-desktop.png
coverCaption: "Free cross and sun raise"
coverMeta: in
coverSize: partial
---

> In code we trust. --BitCoin
<!--more-->

<!-- toc -->

## numpy.rollaxis 的另类理解方式

### rollaxis 实例

in[1]:

```python
%matplotlib inline
import matplotlib.pyplot as plt
import numpy as np
import scipy.misc
```

in[2]:

```python
b = scipy.misc.imread('magic.png')
```

in[3]:

```python
b.dtype
```

out[3]:

```
dtype('uint8')
```

in[4]:

```python
toimage(b)
```

out[4]:

![png](http://qiniu.heyuhua.com/output_5_0.png)

in[5]:

```python
b.shape
```

out[5]:

```
(810, 572, 4)
```

in[6]: 该操作与 `c = np.swapaxes(b, 0, 1)` 等效

```python
c = np.rollasix(b, 1)
```

in[7]:

```python
c.shape
```

out[7]:

```
(572, 810, 4)
```

in[8]:

```python
toimage(c)
```

out[9]:

![png](http://qiniu.heyuhua.com/output_7_0.png)

## gevent 记录

gevent ， 一个传统的协程 网络io库。

它的 的event loop 使用 libev：

libev库是一个基于Reactor模型的网络io库,  可以调用多个平台的 multiplexing I/O（即多路复用模式的网络io）模块，比如 linux 的epoll，mac 的select ，freebsd 的kqueue。

Reactor网络模型同时处理大量的数据链接，十分适合当前互联网产品环境下的多链接访问情景。python的gevent使用情景也大抵如此。

> 如果能忍受那一堆宏定义，可以去试着读下libev的源码。

### 常用的gevent 开发模式

#### 一. 起手式：gevent.monkey

****
