---
title: python重修之旅（三）tornado异步&协程
date: 2017-03-09 10:22:19
category: develop
tags:
- python
---

{{< alert warning >}}
该博文内容缺失
{{< /alert >}}

<!--more-->

## `yield` 写法 的 coroutines
强烈推荐 [David Beazley][1]的文章。注意因为此演讲为上古秘制，所以有些过气语法。。。
后面的操作系统我没有看。只看了到part 6

举个栗子： tail -f 在python中的实现

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by vici on 09/03/2017
#  python tail -f | understand coroutines

import time


# coroutine decorator
def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr
    return start


def follow(thefile, target):
    print "start tail"
    thefile.seek(0, 2)
    """
    seek(x, y ) the default is 0, means file beginning, 1 => current position
    , 2=> end of file
    """
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        print("[+] get 1 new line")
        target.send(line)


@coroutine
def printer():
    while True:
        line = (yield)
        print line,


if __name__ == '__main__':
    import platform
    print platform.python_version()
    f = open("1", 'rb')
    print f.readline()
    printt = printer()
    follow(f, printt)

```








[1]: http://www.dabeaz.com/coroutines/Coroutines.pdf
