---
title: python 重修之旅（四）
date: 2017-07-21 16:28:18
categories:
- develop
tags:
- python
---

> 我有一万个理由不用vim&emacs

<!--more-->
<!-- toc -->
## 一. weakref   — 弱引用

weakref 模块 让我们可以在coding时 为对象添加弱引用

*referent*： 一个被弱引用的对象

相对一个hard reference(强引用）来说 ，对象的弱引用无法让对象保持活动态：当对象的剩余引用全部引用为弱引用时，gc可以销毁该弱引用对象并释放内存空间。另一个特性是，在该对象被完全销毁前，你仍然可以放肆的调用它。（当然你不会知道它返回的到底是该对象还是一个错误。。。）

弱引用的主要被用来设计 放置大对象的映射表／缓存空间。

举个栗子：

​    🌰

ʕ •ᴥ•ʔ

如果有很多庞大的二进制图形对象，而你希望将每个图像与一个名字做关联。如果使用传统的dict字典来映射name : image， 或者 image : name, 这些图形对象将会一直被保持在内存中。于是乎 `WeakKeyDictionary` 和 `WeakValueDictionary` 类型应运而生。他们分别支持 对于 dict 中 key值和value的weakref。（让 image 在一个WeakKeyDictionary 字典中充当key| 让 image 在 WeakValueDictionary字典中充当value）

在 python 3.4 中 weakref 添加了一个注册清理函数的回调入口 `finalize`(def finalize(fund, *arg, **kargs)) . 这个回调会在弱引用对象被gc时调用。 类似于\_\_del\_\_ magic 方法，该回调的异常可以在标准输出中显示，但是不能被传播。

## 二. unittest.mock — 虚假对象

`unittest.mock` 大多被应用在python的测试中。你可以将程序中的某些部分用mock对象进行替换，并断言／定制其表现。

Python3.5内置了mock模块（unites.mock), 其常用 方式为 指定返回值（reaturn_value）, 指定hook返回函数 `side_effect`, 和 上下文控制方法 `mock.patch`。

在工作项目中，同事们采用了 pytest搭建集成测试环境，其中的`monkeypatch`工作原理与mock相似。但monkeypatch更局限于对指定模块或对象进行patch，mock的丰富接口还可以应用在项目的profile及其他更多应用场景中。

## 三. collections 高级容器数据类型

python2.7时期的 collections 包括  `nametuple`, `deque`, `ChainMap` , `Counter`,`OrderDict`,`defaultdict`, 在 python3中添加了`UserDict`, `UserList`,` UserString`三个类型 。

### 1. ChainMap（链表映射）

ChainMap总会让人想到数据结构。然后想起大一写c链表的美好时光。当然也会想起iteratortools 的 chain。

ChainMap 可以快速的对多个传入的dict 或map 进行 链接link，返回一个可以当作单一单元的对象。

当没有映射被传入时，ChainMap会默认返回空dict。

所有传入的映射都会被储存在一个列表中，可以使用ChainMap的`maps`  属性进行查看和编辑。如果该列表中的元素被更改， chainmap由于对该属性的依赖，其展示内容也会相应改变。

```python
from Collection import ChainMap
b = ChainMap(locals(), globals())
b.new_child() == ChainMap({}, *b.maps)  # True
```

​					

### 2. Counter（计数器）

有时候你会觉得找工作的时候面试官问的问题都特别简单，比如说问到文件的词频统计，可能只会想到用dict或者collections.defaultdict 来维护一个计数字典。

The pythonic way should be：

```python
import re
from collections import Counter
# 哈姆莱特戏剧的词频
words = re.findall(r'\w+', open('hamlet.txt').read().lower())
assert Counter(words).most_common(10) == \
[('the', 1143), ('and', 966), ('to', 762), ('of', 669), ('i', 631),
 ('you', 554),  ('a', 546), ('my', 514), ('hamlet', 471), ('in', 451)]
```

Counter的dict接口设计在请求访问不存在key对应value时并不会抛出KeyError异常，而是会返回`0`.

```Python
counts = Counter(['a', 'a', 'b'])
assert counts['c'] == 0  # True
```

三个实用方法 python3.1+。

`most_common(n)` 返回频度最高的前n个计数对象，及频数。

`elements()`会返回一个迭代器，如果将迭代器转化成list， 每个counter记录的元素都会在list中出现其对应的频数次数，而且无序。

```python
c = Counter(a=1, b=2)
```

`c`.elements() 可能是 abb， 也可能是 bba， 还可能是 bab。

`subtract()`  方法接收可迭代对象或映射，在原有counter对象上进行相应的减法操作。

```python
c = Counter(a=4, b=2, c=0, d=-2)
d = Counter(a=1, b=2, c=3, d=4)
c.subtract(d)
# c update to Counter({'a': 3, 'b': 0, 'c': -3, 'd': -6})
```

Counter 实现了大部分的dict接口，except：

- `fromkeys()`  并没有被实现

  - `update()`对传入的可迭代对象进行计数，将结果加入到原对象。

  ​

在python3.3+ 中， Counter 还重载了位亦或及加减运算符号。（不忍心继续抄文档了）记住： `-`跟`subtract()`不一样，  `&`取左右最小，  `|`取左右最大。 单一`+` ,`-`号起计数筛选作用。



### 3. deque（双向队列）

这玩意披着deque的羊皮干着list的活。

用法：deque([iterable[, maxlen]])

deque的特性是围绕maxlen这一参数的，所以不定义maxlen的deque还不如list。。。因为list为变长list做了内存优化，而且list下标访问更快。

讨论一下在maxlen定义了之后的情况。当deque满，向任意一端添加数据（`append`,`appendleft`） 都会导致相反方向的一端数据被pop，这一特性可以被用在类似实时交易监控，unix tail原型实现等等

内置方法：`append()`右端添加，`appendleft()`左端添加， `clear()`清空队列，`copy()`浅拷贝（new in 3.5）...

`count(x)` :记录等于 x 的元素个数。

`extend(iter)` 向队列右侧批量插入。左侧插入则有`extendleft()`

`index(x)`获取元素坐标，还可以添加start，stop参数选定查找范围。

`insert(i,x)`将元素x插入到队列的i位置。

`pop()`,`popleft()` 分别从队列右侧， 左侧去除元素，如果队列空抛出异常。

`remove(x)`删除第一个匹配到的元素x

`reverse()`反转

`rotate()` 轮转

一些官方使用实例：

Linux tail 的最简实现。

```python
log_file = open(path_to_file)
tail = deque(log_file, 10)  # 得到了文件的最后十行。
```

求滑动平均／移动平均（拓展到求卷积什么的。。）

```python
def moving_average(iterable, n=3):
    # moving_average([40, 30, 50, 46, 39, 44]) --> 40.0 42.0 45.0 43.0
    # http://en.wikipedia.org/wiki/Moving_average
    it = iter(iterable) # 转换为迭代类型
    d = deque(itertools.islice(it, n-1))  # 初始化 deque([40, 30])
    d.appendleft(0) # 填充空数据。 deque([0, 40, 30])
    s = sum(d)
    for elem in it: # it = iter([50, 46, 39, 44])
        s += elem - d.popleft()
        d.append(elem)
        yield s / float(n)
```



### 4. defaultdict （字典工厂）

一个内建数据类型 dict 的子类， 在dict的基础上重构了一个内建方法， 并添加了一个可编辑的实例变量。

some cookies

利用 defaultdict of list 将一个key-value 序列分组。

```Python
sol = [('男', 'vici'), ('女', 'Rancho'), ('中性', 'Littlekey'), ('男', 'Guido'), ('女', '某徐某xuan')]
d = defaultdict(list)
for k, v in sol:
  d[k].append(v)
assert sorted(d.items()) == [('中性', ['Littlekey']), ('女', ['Rancho', '某徐某xuan']), ('男', ['vici', 'Guido'])]
```

当dict中的某个键不存在且被调用时，defaultdict会使用默认工厂进行初始化， 比如上面的例子在进行遍历sol中的第一个元素时， d[k] 操作会生成一个空list与相应的k形成映射。

承接一下Counter的部分，本宝宝之前做文件字数统计用的就是defaultdict。。。

### 5. namedtuple（命名元组工厂）

快速实现简单结构体的不二之选。

```python
People = namedtuple('People', 'name age birth school')
p = People('vici', 17, '0701', 'WHUT')
assert p == People(name='vici', age=17, birth='0701', school='WHUT')
assert p.school == 'WHUT'
assert p.age == 17
name, age, *_ = p
assert name
```

当然是用带空格的字符串来区分named_field 只是为了展示 python的强大语法糖，文档推荐使用`[name, age, birth, school]`的传参方式创建工厂。

nametuple很适合做一些结构化数据，类似sql查询，csv，sqlite3等等。

直接抄袭文档实例：

```python
EmployeeRecord = namedtuple('EmployeeRecord', 'name, age, title, department, paygrade')

import csv
for emp in map(EmployeeRecord._make, csv.reader(open("employees.csv", "rb"))):
    print(emp.name, emp.title)

import sqlite3
conn = sqlite3.connect('/companydata')
cursor = conn.cursor()
cursor.execute('SELECT name, age, title, department, paygrade FROM employees')
for emp in map(EmployeeRecord._make, cursor.fetchall()):
    print(emp.name, emp.title)

```

这里用到了一个classmethod `_make(iterable)`：从一个 iterable对象新建实例，

其他实例方法；

`_asdist()` 返回一个 orderedDict，存放字段名及其对应value.

`_replace()`修改tumple值。

`_source`该属性返回可交由`exec()`执行的基于当前python版本的python源码。

`_fields`返回包含所有字段名的tuple.可用与多个namedtuple的快速合并。

类似什么作为继承类和添加`__doc__ `的咸鱼操作懒得写了。

### 6. OrderedDict（有序字典）

就是有序字典嘛，有什么好说的凸^-^凸。难道这玩意怎么用你心里还没点b数嘛？

除了所有的dict的方法，python3.1后还添加了两个鸡肋方法`popitem()` & `move_to_end(key)`, 前者会返回并删除对象的最后一个键值对，后者会把key挪到字典最后。



### 7. UserDict, UserList, UserString 集合类型包装对象

python3之前这些类型作为单独module独立存在，在python3后被整合进collections module，其他的一些抽象Mixin class类似 `MutableMapping` 则被迁移到了`collections.abc`module.

如果想要创建一个dict的子类，直接继承dict而不要继承UserDict，你好我好大家好。

我觉得[dongweiming博客里的事件](http://www.dongwm.com/archives/UserDict%E3%80%81UserString%E3%80%81UserList%E5%AD%98%E5%9C%A8%E7%9A%84%E6%84%8F%E4%B9%89/)实在是极端。见仁见智，世界和平～

##### 不算题外的题外话：

我忍了很久了（于2017-08-09 00:27）

入职新公司后我又一次陷入了鄙视链：emacs  > vim > ide

如果有谁还敢用这种鄙视链搞我，我只想抽出我40米的长刀，让你丫先跑39米再算账。

第一次用vi类的编辑器是高中时候无聊给家里电脑装了个ubuntu, 万能的网友说nano不如vim好用，从此入了vim的坑（不过我承认这么多年过去了我vim也就是入门水平），当时久觉得这玩意真特么难用老要切换读写。连个关闭按钮都没有，bulabula...

但是后来习惯后，我觉得用vim写c要比windows上的vc6.0好用多了。大学接触了visual studio 2013／15（写c#)，JetBrains IDEA (写java 和android)，就几乎放弃使用编辑器了。

我现在写python。

我就不信你们用vim的能一个command+b跳转到 redis.lock.Lock 方法的源码， 我就不信你能删除上一行的时候下一行的缩进还能跟着自动修改。我不信你n多个项目都带virtualenv的时候还能给你一个相应版本的python console／ipython table。

我就是喜欢ide占用我cpu30%时候的样子。电脑卡只能怪你的电脑差。

用vim666的大佬本宝宝心里佩服的，但是我写代码是为了自己爽，who care why are you so diao？pycharm pro让我有飞一样的感觉，犹如激光枪，vim最多算是勾践剑，只可砍瓜切菜，而我可以把你轰杀至渣。

当然我也在pycharm里加了vim插件，有本事你打我啊。

这可能是一个互相骂傻b，然后慢慢把自己变成傻b的故事。
