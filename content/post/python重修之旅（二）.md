---
title: python重修之旅（二）
date: 2017-03-07 16:12:52
tags:
- python
---
{{< alert warning >}}
该博文内容缺失
{{< /alert >}}

>对于一个职场新人来说，我最不愿意看到的就是办公室政治。工程师不应该是这样的。

>模块化的写作不适合我， 所以我决定把重修之旅写成游记形式。就酱。

<!--more-->

## six
python 2,3 兼容库，致力于实现文件兼容python 2.5 + 语法。
{{< codeblock "six_example.py" "python" >}}
import six

def dispatch_types(value):
    # 在 python 3中 six.integar_types == int
    # 在 python 2中 six.integar_types == set(int, lang)
    if isinstance(value, six.integer_types):
        handle_integer(value)
    # 同理python2中经典类型和新式类型被合为 six.class_types
    elif isinstance(value, six.class_types):
        handle_class(value)
    elif isinstance(value, six.string_types):
        handle_string(value)

{{< /codeblock >}}

## abc / abstract base class / 抽象基类
python3 内建库, 用来生成抽象类, python不存在真正的抽象基类，而是通过引入`abc`库实现这种
延迟实现的办法。相比之下，Java的`interface` 关键字就更为直白。
{{< tabbed-codeblock abstract_in_different_language >}}
<!-- tab java -->
/* 文件名 : NameOfInterface.java */
import java.lang.*;
//引入包

public interface NameOfInterface
{
   //任何类型 final, static 字段
   //抽象方法
}
<!-- endtab -->
<!--tab python-->
# -*- coding: utf-8 -*-
from abc import ABC, ABCMeta, abstractmethod


class MyIterable(ABC):

    @abstractmethod
    def __iter__(self):
        while False:
            yield None

    def get_iterator(self):
        return self.__iter__()

# 使用abc的metaclass创建一个基础类。
class MyIterable2(metaclass=ABCMeta):

    @abstractmethod
    def __iter__(self):
        while False:
            yield None
        # ...

    def get_iterator(self):
        return self.__iter__()


@MyIterable.register
class Iter1:
    def __getitem__(self, index):
        ...

    def __len__(self):
        ...

    def get_iterator(self):
        return iter(self)


# 等效的接口实现方法
class Iter2(MyIterable2):
    def __getitem__(self, index):
        ...

    def __len__(self):
        ...

    def get_iterator(self):
        return iter(self)

iter1 = Iter1()
print(iter1.__dict__)

print(issubclass(Iter1, MyIterable))  # True
print(isinstance(Iter1, MyIterable))  # False
print(issubclass(Iter2, MyIterable2))  # True
print(isinstance(Iter2, MyIterable2))  # False

# for i in Iter1():
#     print(i)
<!-- endtab -->
{{< /tabbed-codeblock >}}

## matplotlib

## wordcloud


## jieba 分词库




> 读“[multiprocess for human][2]”的总结

## 乱七八糟
 - 逛 hub的时候看到一个[traceback 插件][4]，支持Cocoa，python web，ruby， react。
`cursor`:
## shlex 库

## subprocess 库

## traceback 库



##  读 [python-fire][3]
python fire 是今年3月份 google 推出的新式CLI创建工具。与docopt有着完全不同的构建思路。



[1]: http://blog.csdn.net/wireless_com/article/details/60571394
[2]: https://github.com/kennethreitz/envoy/blob/master/envoy/core.py
[3]: https://github.com/google/python-fire
[4]: https://sentry.io
