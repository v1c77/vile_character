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

### abstract_factory / 抽象工厂

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

{{< codeblock lang="python" >}}
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
{{< codeblock lang="python" >}}
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
{{< /codeblock >}}

### factory / 工厂模式
抽象工厂和工厂模式在python实现中的区别大概只是有没有继承关系了。。。
同样的，工厂方法也是用来实现通用接口。比如说下面这种多国语言翻译的例子。
{{< codeblock lang="python" >}}
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
{{< /codeblock >}}

### lazy_evaluation	/ 惰性求值
Delays the eval of an expr until its value is needed and avoids repeated evals.

表达式计算延迟到调用时，同时避免重复计算
{{< codeblock lang="python" >}}

import functools

class cached_property(object):
    def __init__(self, function):
        self.function = function
        functools.update_wrapper(self, function)

    def __get__(self, obj, type_):
        if obj is None:
            return self
        val = self.function(obj)
        obj.__dict__[self.function.__name__] = val
        return val

{{< /codeblock >}}

The cached_property(a.k.a lazy_property) is a decorator which convert a func
into a lazy evaluation property. The first time property accessed, the func
is called to get result and then the value is used the next time you access
the property.

eg:
{{< codeblock lang="python" >}}

class LogHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    @cached_property
    def load_log_file(self):
        with open(self.file_path) as f:
            # the file is to big that I have to cost 2s to read all file
            return f.read()

log_handler = LogHandler('./sys.log')
# only the first time call will cost 2s.
print(log_handler.load_log_file)
# return value is cached to the log_handler obj.
print(log_handler.load_log_file)

{{< /codeblock >}}

### pool /池模式
预初始化一批对象并保持可用状态。
pool模式常用来提供各种服务连接，比如各大数据库提供的ConnectionPool, python内建的
threadingPools。

{{< codeblock lang="python" >}}
import queue


class ObjPool:

    def __init__(self, queue, auto_get=False):
        self._queue = queue
        self.item = self._queue.get() if auto_get else None

    def __enter__(self):
        if self.item is None:
            self.item = self._queue.get()
            return self.item

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.item is not None:
            self._queue.put(self.item)
            self. item = None

    def __del__(self):
        if self.item is not None:
            self._queue.put(self.item)
            self. item = None


my_queue = queue.Queue(maxsize=20)

my_queue.put('huahua')
my_queue.put('dandan')


def do_sth_in_queue(myqueue):
    with ObjPool(myqueue) as obj:
        print(f'inside {obj}')
    out_item = myqueue.get()
    print(f'outside {out_item}')
    myqueue.put(out_item)
    while True:
        with ObjPool(myqueue) as obj:
            print(f'inside {obj}')


do_sth_in_queue(my_queue)
# inside huahua
# inside dandan
# inside huahua
# inside dandan
# inside huahua
# inside dandan
# ...
{{< /codeblock >}}

### protopype / 原型
通过clone原型来创建新的实例。似乎并没有人用过。。。
{{< codeblock lang="python">}}
class Prototype(object):

    value = 'default'

    def clone(self, **attrs):
        """Clone a prototype and update inner attributes dictionary"""
        # Python in Practice, Mark Summerfield
        obj = self.__class__()
        obj.__dict__.update(attrs)
        return obj
{{< /codeblock >}}

------------------------生成模式---------------------------

### adapter / 适配器
我想起了10年前家里用的万能充：万能充总是能通过改变自己的接口形状来适应不同的手机电池。

{{< codeblock lang="python" >}}
class Dog(object):

    def __init__(self):
        self.name = "Dog"

    def bark(self):
        return "woof!"


class Cat(object):

    def __init__(self):
        self.name = "Cat"

    def meow(self):
        return "meow!"


class Human(object):

    def __init__(self):
        self.name = "Human"

    def speak(self):
        return "'hello'"


class Car(object):

    def __init__(self):
        self.name = "Car"

    def make_noise(self, octane_level):
        return "vroom{0}".format("!" * octane_level)


class Adapter(object):
    """
    Adapts an object by replacing methods.
    Usage:
    dog = Dog
    dog = Adapter(dog, dict(make_noise=dog.bark))
    >>> objects = []
    >>> dog = Dog()
    >>> print(dog.__dict__)
    {'name': 'Dog'}
    >>> objects.append(Adapter(dog, make_noise=dog.bark))
    >>> print(objects[0].original_dict())
    {'name': 'Dog'}
    >>> cat = Cat()
    >>> objects.append(Adapter(cat, make_noise=cat.meow))
    >>> human = Human()
    >>> objects.append(Adapter(human, make_noise=human.speak))
    >>> car = Car()
    >>> car_noise = lambda: car.make_noise(3)
    >>> objects.append(Adapter(car, make_noise=car_noise))
    >>> for obj in objects:
    ...     print('A {} goes {}'.format(obj.name, obj.make_noise()))
    A Dog goes woof!
    A Cat goes meow!
    A Human goes 'hello'
    A Car goes vroom!!!
    """

    def __init__(self, obj, **adapted_methods):
        """We set the adapted methods in the object's dict"""
        self.obj = obj
        self.__dict__.update(adapted_methods)

    def __getattr__(self, attr):
        """All non-adapted calls are passed to the object"""
        return getattr(self.obj, attr)

    def original_dict(self):
        """Print original object dict"""
        return self.obj.__dict__
{{< /codeblock >}}

### bridge / 桥接模式
桥接的使用集中在频繁更换实现方法时。用于把容易拆分的实现抽象成接口。然后挑选使用。

{{< codeblock lang="python" >}}
# ConcreteImplementor 1/2
class DrawingAPI1(object):

    def draw_circle(self, x, y, radius):
        print('API1.circle at {}:{} radius {}'.format(x, y, radius))


# ConcreteImplementor 2/2
class DrawingAPI2(object):

    def draw_circle(self, x, y, radius):
        print('API2.circle at {}:{} radius {}'.format(x, y, radius))


# Refined Abstraction
class CircleShape(object):

    def __init__(self, x, y, radius, drawing_api):
        self._x = x
        self._y = y
        self._radius = radius
        self._drawing_api = drawing_api

    # low-level i.e. Implementation specific
    def draw(self):
        self._drawing_api.draw_circle(self._x, self._y, self._radius)

    # high-level i.e. Abstraction specific
    def scale(self, pct):
        self._radius *= pct


def main():
    shapes = (
        CircleShape(1, 2, 3, DrawingAPI1()),
        CircleShape(5, 7, 11, DrawingAPI2())
    )

    for shape in shapes:
        shape.scale(2.5)
        shape.draw()


if __name__ == '__main__':
    main()

### OUTPUT ###
# API1.circle at 1:2 radius 7.5
# API2.circle at 5:7 radius 27.5
{{< /codeblock >}}

### composite / 组合模式
一种表达树形结构的方法,恕在下才疏学浅，还没有注意到生产代码中的类似用例。
贴一段 soucemaking上的用例：
{{< codeblock lang="python" >}}
import abc


class Component(metaclass=abc.ABCMeta):
    """
    Declare the interface for objects in the composition.
    Implement default behavior for the interface common to all classes,
    as appropriate.
    Declare an interface for accessing and managing its child
    components.
    Define an interface for accessing a component's parent in the
    recursive structure, and implement it if that's appropriate
    (optional).
    """

    @abc.abstractmethod
    def operation(self):
        pass


class Composite(Component):
    """
    Define behavior for components having children.
    Store child components.
    Implement child-related operations in the Component interface.
    """

    def __init__(self):
        self._children = set()

    def operation(self):
        for child in self._children:
            child.operation()

    def add(self, component):
        self._children.add(component)

    def remove(self, component):
        self._children.discard(component)


class Leaf(Component):
    """
    Represent leaf objects in the composition. A leaf has no children.
    Define behavior for primitive objects in the composition.
    """

    def operation(self):
        pass


def main():
    leaf = Leaf()
    composite = Composite()
    composite.add(leaf)
    composite.operation()


if __name__ == "__main__":
    main()
{{< /codeblock >}}

### faced / 门面
可以叫它总闸模式： 一个独立的模块单独负责所有子对象的运行。
举个极其抽象的例子：
{{< codeblock lang="python" >}}
def runner():
    a = lambda: "task a"
    b = lambda: "task b"
    c = lambda: "task c"
    tasks = [a, b, c]
    task_ret = [task() for task in tasks]
    print(task_ret)
{{< /codeblock >}}

### flyweight / 享元
通过与其他相似的对象共享数据来达到节省内存的目的。
{{< codeblock lang="python">}}
# -*- coding: utf-8 -*-

"""
*References:
http://codesnipers.com/?q=python-flyweights
http://yloiseau.net/articles/DesignPatterns/flyweight/
*TL;DR80
Minimizes memory usage by sharing data with other similar objects.
"""

import weakref


class FlyweightMeta(type):

    def __new__(mcs, name, parents, dct):
        """
        Set up object pool
        :param name: class name
        :param parents: class parents
        :param dct: dict: includes class attributes, class methods,
        static methods, etc
        :return: new class
        """
        dct['pool'] = weakref.WeakValueDictionary()
        # 调用 type 的 new 方法。
        return super(FlyweightMeta, mcs).__new__(mcs, name, parents, dct)

    @staticmethod
    def _serialize_params(cls, *args, **kwargs):
        """
        Serialize input parameters to a key.
        Simple implementation is just to serialize it as a string
        """
        args_list = list(map(str, args))
        args_list.extend([str(kwargs), cls.__name__])
        key = ''.join(args_list)
        return key

    def __call__(cls, *args, **kwargs):
        key = FlyweightMeta._serialize_params(cls, *args, **kwargs)
        pool = getattr(cls, 'pool', {})

        instance = pool.get(key)
        if instance is None:
            instance = super(FlyweightMeta, cls).__call__(*args, **kwargs)
            pool[key] = instance
        return instance


def with_metaclass(meta, *bases):
    """ Provide python cross-version metaclass compatibility. """
    return meta("NewBase", bases, {})


class Card2(with_metaclass(FlyweightMeta)):

    def __init__(self, *args, **kwargs):
        pass


if __name__ == '__main__':
    # comment __new__ and uncomment __init__ to see the difference

    # Tests with metaclass
    instances_pool = getattr(Card2, 'pool')
    cm1 = Card2('10', 'h', a=1)
    cm2 = Card2('10', 'h', a=1)
    cm3 = Card2('10', 'h', a=2)
    print(f'id:{id(cm1)}, {cm1}')
    print(f'id:{id(cm2)}, {cm2}')
    print(f'id:{id(cm3)}, {cm3}')

    assert (cm1 == cm2) != cm3
    assert (cm1 is cm2) is not cm3
    assert len(instances_pool) == 2

    del cm1
    assert len(instances_pool) == 2

    del cm2
    assert len(instances_pool) == 1

    del cm3
    assert len(instances_pool) == 0
{{< /codeblock >}}

### front controtllor / 前端控制器
front controtollr 提供了一个中控平台控制和管理请求。
{{< codeblock "front_controller.py" "python" "https://github.com/faif/python-patterns/blob/master/structural/front_controller.py" "front_controller.py" >}}
# 点击右上角查看示例
{{< /codeblock >}}

### mvc&n-tier / 分层
mvc 和 n-tier 的差别就是， n-tier 模式中各模块为线性关系，而 mvc结构中，view 向controllor
发送更新信息，controllor更新model，然后view层获取model层的更新。

在应用中，我们通常用mvc，mvvc等来形容app的代码层级结构，而在基础设施搭建中，我们通常用n-tier来
描述该协议/模式的运行模式。比如网络的7层/3层结构。

**mvc**
{{< codeblock "mvc.py" "python" "https://github.com/faif/python-patterns/blob/master/structural/mvc.py" "mvc.py" >}}
# 点击右上角查看示例
{{< /codeblock >}}

**3-tier**
{{< codeblock "3-tier.py" "python" "https://github.com/faif/python-patterns/blob/master/structural/3-tier.py" "3-tier.py" >}}
# 点击右上角查看示例
{{< /codeblock >}}

### proxy / 代理
代理的核心思想是控制对一个对象的访问过程，比如网络代理，控制了网络访问的过程。

{{< codeblock "proxy.py" "python" "https://sourcemaking.com/design_patterns/proxy/python/1" "proxy.py" >}}
# 点击右上角查看源网址
"""
Provide a surrogate or placeholder for another object to control access
to it or add other responsibilities.
"""

import abc


class Subject(metaclass=abc.ABCMeta):
    """
    Define the common interface for RealSubject and Proxy so that a
    Proxy can be used anywhere a RealSubject is expected.
    """

    @abc.abstractmethod
    def request(self):
        pass


class Proxy(Subject):
    """
    Maintain a reference that lets the proxy access the real subject.
    Provide an interface identical to Subject's.
    """

    def __init__(self, real_subject):
        self._real_subject = real_subject

    def request(self):
        # ...
        self._real_subject.request()
        # ...


class RealSubject(Subject):
    """
    Define the real object that the proxy represents.
    """

    def request(self):
        pass


def main():
    real_subject = RealSubject()
    proxy = Proxy(real_subject)
    proxy.request()


if __name__ == "__main__":
    main()
{{< /codeblock >}}


-----------------------行为模式---------------------------
