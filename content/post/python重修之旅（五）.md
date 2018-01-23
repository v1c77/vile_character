---
title: python重修之旅（五）
date: 2017-09-19
categories:
- develop
tag: python
autoThumbnailImage: false
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

## python常用设计模式
项目地址： https://github.com/faif/python-patterns

《松本行弘的程序世界》对三人组的《设计模式》称赞有加：

> 把普通人难以学习和吸收的内隐知识变成形式只是的功绩是无与伦比的。

在设计模式原书中一共提到23种常用的设计模式，分为三大类：生成模式（creational），
构造模式（structural）， 行为模式（behavioral）。该项目同样按照这三大类进行了分类整理，
同时还补充了一些python常用的其他场景的特用模式。

------------------------生成模式---------------------------

### 抽象工厂 / abstract_factory

最直白的就是“鸡鸭鹅狗猫都是动物”：

{{< codeblock lang="python" >}}
from abc import ABCMeta, abstractmethod

# Pet类是一个典型的抽象类, 包含了抽象方法 `speak`
# 其类方法from_name 充当了 工厂“销售“ 的角色，对于所有的Pet子类，客户想要什么就可以得到什么。
class Pet(metaclass=ABCMeta):

    @classmethod
    def from_name(cls, name):
        for sub_cls in cls.__subclasses__():
            if name == sub_cls.__name__.lower():
                return sub_cls()

    @abstractmethod
    def speak(self):
        """"""


class Kitty(Pet):
    def speak(self):
        return "Miao"


class Duck(Pet):
    def speak(self):
        return "Quak"


for name in ['kitty', 'duck']:
    pet = Pet.from_name(name)
    print("{}: {}".format(name, pet.speak()))
# kitty: Miao
# duck: Quak
{{< /codeblock >}}

### borg / 集体主义模式
emmm... https://blog.youxu.info/2010/04/29/borg/ 介绍了borg的出处。
borg就是python的singleton，但是与singleton不同的是，borg模式为多个对象共享单一状态，
而不是单一对象多个引用。

{{< codeblock lang="python">}}
class Borg(object):
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.state = 'Init'

    def __str__(self):
        return self.state

# ipython excemple
# In [2]: a = Borg()
# In [3]: b = Borg()
# In [4]: a.state
# Out[4]: 'Init'
# In [5]: b.state
# Out[5]: 'Init'
# In [6]: a.state='123'
# In [7]: b.state
# Out[7]: '123'
# In [8]: id(a)
# Out[8]: 4340743360
# In [9]: id(b)
# Out[9]: 4340673448
{{< /codeblock >}}

### builder / 建造者模式
适用于构造复杂对象, 将构造过程拆分为独立模块
{{< codeblock lang="python">}}
# copy from《Mastering Python Design Patterns》


class Computer:
    def __init__(self, serial_number):
        self.serial = serial_number
        self.memory = None
        self.cpu = None
        self.disk = None

    def __str__(self):
        return 'memory: {0} GB, cpu: {1}, disk: {2} GB'.format(
            self.memory, self.cpu, self.disk
        )


class ComputerBuilder:
    def __init__(self):
        self.computer = Computer('SN-12345555')

    def configure_memory(self, memory):
        self.computer.memory = memory

    def configure_cpu(self, cpu):
        self.computer.cpu = cpu

    def configure_disk(self, disk):
        self.computer.disk = disk


class HardwareEngineer:
    def __init__(self):
        self.builder = None

    def construct_computer(self, memory, cpu, disk):
        self.builder = ComputerBuilder()
        self.builder.configure_memory(memory)
        self.builder.configure_cpu(cpu)
        self.builder.configure_disk(disk)

    @property
    def computer(self):
        return self.builder.computer

engineer = HardwareEngineer()
engineer.construct_computer(16, 8, 500)
computer = engineer.computer
print(computer)
# memory: 16 GB, cpu: 8, disk: 500 GB
{{< /codeblock>}}

### factory / 工厂模式
抽象工厂和工厂模式在python实现中的区别大概只是有没有继承关系了。。。
同样的，工厂方法也是用来实现通用接口。比如说下面这种多国语言翻译的例子。
{{< codeblock lang="python">}}
class GreekGetter(object):

    """A simple localizer a la gettext"""

    def __init__(self):
        self.trans = dict(dog="σκύλος", cat="γάτα")

    def get(self, msgid):
        """We'll punt if we don't have a translation"""
        return self.trans.get(msgid, str(msgid))


class EnglishGetter(object):

    """Simply echoes the msg ids"""

    def get(self, msgid):
        return str(msgid)


def get_localizer(language="English"):
    """The factory method"""
    languages = dict(English=EnglishGetter, Greek=GreekGetter)
    return languages[language]()


if __name__ == '__main__':
    # Create our localizers
    e, g = get_localizer(language="English"), get_localizer(language="Greek")
    # Localize some text
    for msgid in "dog parrot cat bear".split():
        print(e.get(msgid), g.get(msgid))

### OUTPUT ###
# dog σκύλος
# parrot parrot
# cat γάτα
# bear bear
{{< /codeblock>}}
