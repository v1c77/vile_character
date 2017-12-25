---
title: 'python 的坑 '
date: 2016-12-15 16:17:05
category:
- develop
tags:
- python
---

生死怎能看淡, 不服就是要干
<!--more-->

## 一. 亲身经历

> python 是我第一个拿出10分认真的态度去学习的语言.

但是可能需要12分的认真。因为周围毕竟还有一些十分认真的人在尝试着用她解决问题。之前零零散散的坑笔记也懒得往过搬了。

> ## python2： 对 *range* 的想法

* 于 2016年12月15日16:26:12
    - 一个小时前CTO大人（以下简称杰哥）过来找我说一个很奇怪的问题：同一个脚本检索两台数据库，一台国内一台国外，国外的没出问题，国内的时不时报错。
      （讲道理我的第一反应是...觉得国外的服务器香一些。。。）

    - 登到监控服务器 vi+ pdb 一顿调试，问题出在了神奇的地方：


```python
# python伪代码

with open('file/to/path', 'r') as f:
    localfsize = getsize(f)
    for i in range(1, localfsize, 1):
        f.seek(size-i)
        # dosomething..,
        pass
```
第一次运行 `for i in range` 就报出memeryError，很自然的想到是range.

因为python2 的range 返回的还是一个完整的数组， 而推荐使用的`xrange` 返回的是一个生成器，占用内存空间更小.

一开始我是拒绝的，因为之前一直都是懒的多写那个`x`,因为本屁民觉得在2016年的今天，一个多占了几mb内存的range并不可能发生内存溢出错误

像我们这种土豪公司，开发机都是4核8线程 64g内存，怎么可能运行个脚本会发生内存错误？

它真的发生了：

这个故事发生在一个十分尴尬的环境，杰哥把脚本跑在了他自己的开车服务器（aws大流量1g内存1核），
整个脚本的流程是开两个线程，分别从国内集群和国外集群的log_db上查询 >> 增量追加到内部处理log。

一个本地日志文件大概是300mb-1g不等的样子。
没错，日志很大，,但又恰好都没有到造成内存溢出的程度，所以就愉快的继续运行了，到了`range` 这里，localfilesize刚好是一个千万级别的整形数字（假设为1kw），即使是按c的计算方法，不考虑堆栈大小，在内存重要占用空间为：
```python
# 顺便说一句python 3.6 新功能:写长数字时可以在中间加下划线`_` ,方便阅读
4 × 1000_0000 = 4000_0000B = 40000KB = 40MB

```
同事脑补了触发memoryERROR 两种可能:1. 这个大数组挤爆了栈空间  | 2. 它成了挤爆内存的最后一根稻草

* 于 2016年12月15日20:54:08

上面的脑补不是很靠谱，刚才又做了一堆测试，发现了更多的问题。

* 测试过程

    - 偷了台实验室的计算服务器 :D
```python
# 测试range 占用内存函数
from sys import getsizeof
foo1 = lambda x:getsizeof(range(int(10**x)))
```
```bash
# 返回的数字与实际最高内存占用出入很大, 另开一个shell 监控memory
watch -n 0.01  "free -m"
```

![辛苦的见证啊][1]

`foo1(x)` 结果：

| `x`的值 |       运行时最高占用 |
| :---: | ------------: |
|  10   | 'memoryError' |
|   9   |      31138_mb |
|   8   |       3111_mb |
|   7   |          77mb |


* 跟之前口算的理想大小40mb 没差, 可以接受

* 然后给foo1 做一些修改：

```python
from sys import getsizeof
foo2 = lambda x:getsizeof(range(0, int(10**x), 1))

```
`foo2(x)` 结果：

| `x`的值 |       运行时最高占用 |
| :---: | ------------: |
|  10   | 'memoryError' |
|   9   |      31138_mb |
|   8   |       3111_mb |
|   7   |         235mb |


**比较两次 `foo(7)` 可怕的事情发生了， range 生成同一内容的两种调用方法会有两种内存占用。 **

> 至于国外集群不出问题的原因， 国外服务器一天生产的log 比较少，所以文件也比较小。so ...

end.


> ## 为什么我的super报错？

* 于 2016年12月16日15:06:31

- 问题代码：
```python
class A:
    def __init__(self):
        pass


class B(a):
    def __init__(self):
        super(B, self).__init__()

c = B()
```

上述代码会报`TypeError: super() argument 1 must be type, not classobj`错误

* 解决办法 `class A:` 旧的类型写法已经被弃用， 改用`class A(object)` 万事大吉

    - 刚才我在想，为什么我不会范这个错误? 因为我已经懒到了根本不会写class...
      这就是我的*BOP* 编程思想： __Bed Oriented Programming__




## 二. 搬运wtfpyhon项目 + 自评

> 项目地址： [wtfpy](https://github.com/satwikkansal/wtfpython)  该项目使用DO WHAT THE FUCK YOU WANT 开源协议。所以应该在不获取授权的情况下搬运应该是没什么事的。
>
> python 2的wft尽量少写。

1. ### 字符编码

```Ipython
In [2]: 'value' == 'valuе'
Out[2]: False
```

坑比指数 ⭐️

虽然看起来很魔幻，但是现实生活中能打出两个e的几率其实感觉相当低。必经我特么连cyrillic 码是啥都不知道。。。

2. ### 缩进 | py-version < 3

```python
def square(x):
    """
    A simple function to calculate square of a number by addition.
    """
    sum_so_far = 0
    for counter in range(x):
        sum_so_far = sum_so_far + x
  return sum_so_far
```

上面的代码会输出 10而不会输出想象的 100

坑比指数⭐️

这码在idea里甚至会报错。。。就算vim党一般在配置里也会显式区分tab与spcace的区别（1tab=4space or 2space）

原因：在python2 的解释器中，1tab = 8space，所以return语句进入了for循环。python3已修复。

3. ### python的hash特性

坑比指数⭐️⭐️

eg：

```python
some_dict = {}
some_dict[5.5] = "Ruby"
some_dict[5.0] = "JavaScript"
some_dict[5] = "Python"
```

magic:

```
some_dict[5.0] == some_dict[5] == "python"
```

>  "javascript"终究会被python无情碾压  ;D

python的 list 使用 下标的hash作为实际索引，同时使用hash的还有equal。

如果你希望 `5.0 == 5` 这个判断句在python中是成立的，就需要接受 hash(5.0) == hash(5)。

同时也应该能接受 javascript被python碾压的结果。

4. ### 生成器  for x in y if z

坑比指数⭐️⭐🌟

eg:

```python
array = [1, 8, 15]
g = (x for x in array if array.count(x) > 0)
array = [2, 8, 22]
```

Output:

```
In [3]: print(list(g))
In [4]: 8
```

在generator语法中， in 后面的对象是在声明时被确定的，而 if 后面的语句则会在生成器被执行时才被确定。所以`point(list(g))`等价于：

```Python
print([x for x in [1, 8, 15] if [2, 8, 22].count(x) > 0])
```

5. ### dict迭代中编辑

坑比指数：⭐️🌟

就在看wftpython 前一天，还收到一个想学python的前端同事抱怨：

```python
# 为什么下面的语句会报错？！
a = {'a':1, 'b'=2}
for i in a.keys():
  a.pop(i)
```

哈哈哈哈这事就这么过去吧。（这个锅python是不能背的）

wtfpy中的eg：

```Python
x = {0: None}

for i in x:
    del x[i]
    x[i+1] = None
    print(i)
```

output:

```
0
1
2
3
4
5
6
7
```

tips：永远不曾要尝试在iter dict时尝试添加和修改key.



6. ### List的迭代中编辑

   坑比指数⭐️🌟

   eg:

   ```python
   list_1 = [1, 2, 3, 4]
   list_2 = [1, 2, 3, 4]
   list_3 = [1, 2, 3, 4]
   list_4 = [1, 2, 3, 4]

   for idx, item in enumerate(list_1):
       del item

   for idx, item in enumerate(list_2):
       list_2.remove(item)

   for idx, item in enumerate(list_3[:]):
       list_3.remove(item)

   for idx, item in enumerate(list_4):
       list_4.pop(idx)
   ```

   output:

   ```python
   >>> list_1
   [1, 2, 3, 4]
   >>> list_2
   [2, 4]
   >>> list_3
   []
   >>> list_4
   [2, 4]
   ```

逐个分析：

​	list_1 的 enumrate的迭代中, del item 只是删除了 list中对象的副本。所以并不会变。

​	list\_2和list\_4在遍历的第一步删除数字`1`后list的内容变成了`[2, 3, 4]` .这些剩余的元素下标会顺延，比如 2的下标会变成0， 3的变成1，所以，当第二次遍历时，index 为 1的元素3将会被删除。



7. ### 字符串联结

```python
def add_string_with_plus(iters):
    s = ""
    for i in range(iters):
        s += "xyz"
    assert len(s) == 3*iters

def add_string_with_format(iters):
    fs = "{}"*iters
    s = fs.format(*(["xyz"]*iters))
    assert len(s) == 3*iters

def add_string_with_join(iters):
    l = []
    for i in range(iters):
        l.append("xyz")
    s = "".join(l)
    assert len(s) == 3*iters

def convert_list_to_string(l, iters):
    s = "".join(l)
    assert len(s) == 3*iters
```

```
>>> timeit(add_string_with_plus(10000))
100 loops, best of 3: 9.73 ms per loop
>>> timeit(add_string_with_format(10000))
100 loops, best of 3: 5.47 ms per loop
>>> timeit(add_string_with_join(10000))
100 loops, best of 3: 10.1 ms per loop
>>> l = ["xyz"]*10000
>>> timeit(convert_list_to_string(l, 10000))
10000 loops, best of 3: 75.3 µs per loop
```

耗时天壤之别。但是坑比等级：⭐️

* 大三找实习的时候就有hr叔叔问过我你喜欢用什么做字符串联结。本萌新立马说 用➕。然后那个面试没过。加号的慢是因为 python中的str为不可变对象。加法作为一个双目运算符，每次做一次字符串联结都要创建一次新str对象。当对多个string进行联结时，比如 ‘’aa‘’ +''bb''+"cc", 会首先生成中间变量 ”aabb“,在由“aabb”+"cc" 得到随后的 “aabbcc”

* python内置的字符串填充工具  `.format` 和 `%`在做长字符串处理时效率很高, 但是在处理短字符串时表现欠佳。

* 使用join是最好的选择，一次join只会创建一次对象，多目运算神清气爽。

* 再给join创建 字符串数组的时候 不要使用append，list的动态扩容内存开销极大。

  ​

8. ### 字符串滞留

```python
>>> a = "some_string"
>>> id(a)
140420665652016
>>> id("some" + "_" + "string") # Notice that both the ids are same.
140420665652016
# using "+", three strings:
>>> timeit.timeit("s1 = s1 + s2 + s3", setup="s1 = ' ' * 100000; s2 = ' ' * 100000; s3 = ' ' * 100000", number=100)
0.25748300552368164
# using "+=", three strings:
>>> timeit.timeit("s1 += s2 + s3", setup="s1 = ' ' * 100000; s2 = ' ' * 100000; s3 = ' ' * 100000", number=100)
0.012188911437988281
```

坑比等级：⭐️

同样是没什么卵用的字符串机制。在进行多次重复三字符串联结时，使用 += 要比单纯的两个加号快很多。因为在使用+=时 等号右面的`s2+s3`对象并不会销毁。

9. ### else的扭曲之处

```Python
 def does_exists_num(l, to_find):
      for num in l:
          if num == to_find:
              print("Exists!")
              break
      else:
          print("Does not exist")
```

```python
>>> some_list = [1, 2, 3, 4, 5]
>>> does_exists_num(some_list, 4)
Exists!
>>> does_exists_num(some_list, -1)
Does not exist
```

for-else会在for循环内无break发生后触发else.

同理 try-except-else 无脑三连在try中语句正确执行后才会触发else.

坑壁指数：⭐️

10. ### 是是非非——is

```python
>>> a = 256
>>> b = 256
>>> a is b
True

>>> a = 257
>>> b = 257
>>> a is b
False

>>> a = 257; b = 257
>>> a is b
True
```

坑比指数：⭐️⭐️⭐️⭐️

`is` 与  `==`  的区别在于, 前者比较的是操作数是否为同一对象，即检查操作数id， 后者考量的是对象的数值是否相等，比如说使用 hash。

这里的现象涉及到了python的实现，当python启动时，整型数字中 -5 到 256的所有数字都会以对象形式预分配到内存中。所以 当 a，b为256 时， 他们都是一个`256`对象的引用, `a is b`返回True。

而当创建一个 大于256的数字时，则会生成一个新的integer对象。那么第二段case返回False也就理所应当了。

最后的True则涉及到另一个python的实现。当在一行初始化赋值多个变量时，同一值只会被创建一次。`a = 257; b = 257`, `c, d= 257, 257 `这里 `a is b`,`c is d` 都会被判True。

11. ### 循环内的闭包

```python
funcs = []
results = []
for x in range(7):
    def some_func():
        return x
    funcs.append(some_func)
    results.append(some_func())

funcs_results = [func() for func in funcs]
```

```python
>>> results
[0, 1, 2, 3, 4, 5, 6]
>>> funcs_results
[6, 6, 6, 6, 6, 6, 6]

```

坑比指数：⭐️⭐️✨

定义在循环中的闭包 如果使用外部循环变量，闭包将会绑定该变量而不是变量值。所以在循环结束后调用闭包时，闭包内使用的循环变量是其遍历结束时的值。

```Python
funcs = []
for x in range(7):
    def some_func(x=x):
        return x
    funcs.append(some_func)
```

这种局部函数的写法更加妥当。

12. ##被调戏的自加##

input:

```python
a = [1, 2, 3, 4]
b = a
a = a + [5, 6, 7, 8]
```

Output:

```python
>>> a
[1, 2, 3, 4, 5, 6, 7, 8]
>>> b
[1, 2, 3, 4]
```

嗯，似乎是正常的。下面是核爆现场。

Input：

```python
a = [1, 2, 3, 4]
b = a
a += [5, 6, 7, 8]
```

Output:

```python
>>> a
[1, 2, 3, 4, 5, 6, 7, 8]
>>> b
[1, 2, 3, 4, 5, 6, 7, 8]
```

坑比指数 ⭐️⭐️⭐️✨

`a = a + [5, 6, 7, 8]` 会生成一个新list赋值给a, 此时的b就成了旧的a对象的唯一引用。

`a += [5, 6, 7, 8]` 会产生不同的结果是因为这里list的自加实现 使用了extend 直接在原list上添加新对象。 所以 这里a和b此时还是指向的同一个list。

13. ### 不可变对象被玩弄###

同样是利用了上一条 list 的 自加实现。

```python
>>> another_tuple = ([1, 2], [3, 4], [5, 6])
>>> another_tuple[2] += [99, 999]
TypeError: 'tuple' object does not support item assignment
>>> another_tuple
([1, 2], [3, 4], [5, 6, 1000, 99, 999])
```

坑比指数：⭐️⭐️⭐️⭐️

这个是连环坑。首先这个自加会被执行并赋值，同时还会报tuple不可变的错误。

我觉得这就是个大bug。。。

14. #### 消失的外部变量###

```python
e = 7
try:
    raise Exception()
except Exception as e:
    pass
```

```python
>>> print(e)
NameError: name 'e' is not defined
```

坑比指数：⭐️

虽然很奇葩。但是如果按照规范coding是不会犯这种错误的。

这个现象涉及到expect as 语法的实现逻辑，当离开except 上下文时，会有一个隐式的del 语句将e删除.

一个正常的except语句：

```python
except E as N:
    foo
```

会被解析成酱：

```Python
except E as N:
    try:
        do_any_thing_you_like
    finally:
        del N
```



（挑着翻译看心情。插眼 2017.09.05， 第二次更新 2017.09.18）

[1]: http://qiniu.heyuhua.com/2016-12-15%2021-42-21%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE.png	" "
