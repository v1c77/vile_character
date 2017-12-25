---
title: python重修之旅（一）
date: 2017-01-17 15:17:27
category: develop
tags:
- python
---
还有6个月就毕业了，才知道原来面试之前原来需要刷题什么的。怪不得之前面试我的人都是一脸看智障的样子...
本宝宝的第一个专题。第三次系统学习python。2017年计划之一。
> 年底就是爽，每天就是开开会，下午就自己疯狂coding。

<!--more-->
## 一道面试题
### > 问题：平面上有若干个点。点与点可以重合，寻找一条直线，使其能穿过最多的点。(好吧我承认这是我去面试时候的面试题。)
搬运答案。。。[这里][2]
```python
/**
 * 本代码由九章算法编辑提供。版权所有，转发请注明出处。
 * - 九章算法致力于帮助更多中国人找到好的工作，教师团队均来自硅谷和国内的一线大公司在职工程师。
 * - 现有的面试培训课程包括：九章算法班，系统设计班，算法强化班，Java入门与基础算法班，Android 项目实战班，Big Data 项目实战班，
 * - 更多详情请见官方网站：http://www.jiuzhang.com/?source=code
 */

# Definition for a point.
# class Point:
#     def __init__(self, a=0, b=0):
#         self.x = a
#         self.y = b

class Solution:
    # @param {int[]} points an array of point
    # @return {int} an integer
    def maxPoints(self, points):
        # Write your code here
        len_points = len(points)
        if len_points <= 1:
            return len_points
        max_count = 0
        for index1 in range(0, len_points):
            p1 = points[index1]
            gradients = {}
            infinite_count = 0
            duplicate_count = 0
            for index2 in range(index1, len_points):
                p2 = points[index2]
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                if 0 == dx and 0 == dy:
                    duplicate_count += 1
                if 0 == dx:
                    infinite_count += 1
                else:
                    g = float(dy) / dx
                    gradients[g] = (gradients[g] + 1 if gradients.has_key(g) else 1)
            if infinite_count > max_count:
                max_count = infinite_count
            for k, v in gradients.items():
                v += duplicate_count
                if v > max_count:
                    max_count = v
        return max_count
```


## 图的python实现

```python
from fractions import Fraction
from collections import deque


class Vertex(object):
    # 原生点 对象
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)

    __str__ = __repr__


class Edge(tuple):
    # 继承自建tuple类型并重写new方法
    def __new__(cls, e1, e2):
        return tuple.__new__(cls, (e1, e2))

    def __repr__(self):
        return "Edge(%s, %s)" % (repr(self[0]), repr(self[1]))


class Graph(dict):

    def __init__(self, vs=[], es=[]):
        """ 建立一个新的图，(vs)为顶点vertices列表，(es)为边缘edges列表 """
        for v in vs:
            self.add_vertex(v)
        for e in es:
            self.add_edge(e)

    def add_vertex(self, v):
        """ 添加顶点 v:  使用字典结构"""
        self[v] = {}

    def add_edge(self, e):
        """ 添加边缘 e: e 为一个元组(v,w)
            在两个顶点 w 和 v 之间添加成员e ，如果两个顶点之间已有边缘，则替换之 """
        v, w = e
        # 由于一条边会产生两个项目，因此该实现代表了一个无向图
        self[v][w] = e
        self[w][v] = e

    def get_edge(self, v1, v2):
        """ 接收两个顶点，则返回这条边，否则返回None """
        try:
            return self[v1][v2]
        except:
            return None

    def vertices(self):
        """ 返回图中所有顶点的列表 """
        return self.keys()

    def edges(self):
        """ 返回图中边的列表 """
        es = set()  # 为了避免返回重复的边，设为集合
        for v1 in self.vertices():
            for v2 in self.vertices():
                es.add(self.get_edge(v2, v1))

        es.discard(None)  # 若集合中存在None元素,则删除 无向图可以不用写这步
        return list(es)


    def add_all_edges(self, vs=None):
        """ 从一个无边的图开始，通过在各个顶点间添加边来生成一个完全图
            输入为目标顶点的列表，如果为None,则对所有的点进行全联结 """
        if vs is None:
            vs = self.vertices()
        for v1 in vs:
            for v2 in vs:
                if v1 is v2:
                    continue  # 假设不存在单顶点连通
                self.add_edge(Edge(v1, v2))

    def bfs(self):
        """
        广度优先搜索
        """
        # parents 记录所有可达节点与对应的父节点，这里是一个字典，我们将其 可达节点 作为 key，而将其 父节点 作为 value
        # query_queue 是用来存放待探索节点的 to-do 列表，这里是一个 FIFO


        node = self.vertices()[0]
        parents, query_queue = {node: None}, deque([node])

        while query_queue:
            # 总是从 FIFO 的左侧弹出待探索的节点
            q_node = query_queue.popleft()

            for neighbor in self.out_vertices(q_node):
                if neighbor in parents:
                    continue

                # 记录探索到的邻居节点及其父节点
                parents[neighbor] = q_node

                # 将其邻居节点推入 to-do 列表
                query_queue.append(neighbor)

        #如果想只得到点的话 可以
        # return prints.key()

        return parents

    def out_vertices(self, v):
        """ 接受一个Vertex并返回邻近顶点（通过一条边连接到给定节点的节点）的列表 """
        return self[v].keys()

    def out_edges(self, v):
        """ 接受一个Vertex并返回连接到给定节点的边的列表 """
        return self[v].values()
```




## socket




## thread／process
> 文字部分详见小明明 线程篇 和进程篇

### threading
> 当前代码版本-----》[这里][3]

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by vici on 22/01/2017
import threading
import platform
import time
import logging
from Queue import Queue
from random import randint

__doc__ = """ 抄董伟明,官方文档，廖雪峰 bogo  。。。。 threading 实验结果记录

"""

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) |||| %(message)s',)


def timeit(func):
    """一个简单的函数时间装饰器"""
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print('{} COST: {}'.format(func.__name__, end-start))
    return wrapper


def show_thread_itself(arg):
    print("threading {} is running! ".format(threading.current_thread().getName()))

    for i in xrange(5):
        print('Thread {} >>> {}'.format(threading.current_thread().getName(), i))
        time.sleep(1)

    print("Thread {} end".format(threading.current_thread().getName()))

    pass


def fib(n):
    if n <= 2:
        return 1
    return fib(n-1) + fib(n-2)


@timeit
def nothread():
    fib(34)
    fib(34)


@timeit
def withthread():
    for i in xrange(2):
        t = threading.Thread(target=fib, args=(34,))
        t.start()

    main_thread = threading.current_thread()

    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()


balance = 1000
lock = threading.Lock()


def change_balance():
    global balance
    balance += 1000
    balance -= 1000


def money_laundering(num):
    for i in xrange(num):
        change_balance()


def money_laundering_priveate(num):
    for i in xrange(num):
        lock.acquire()
        try:
            change_balance()
        finally:
            lock.release()


def lock_is_important():
    """
    这里的lock是一种互斥的 可重获的 锁 在一个加锁thread进行完之后将会释放。
    lock 相当于信号量（Sempahore） 为 1
    """
    @timeit
    def test1():
        print('Before i go to bank ,I have {}'.format(balance))
        t1 = threading.Thread(target=money_laundering, args=(2000000,))
        t2 = threading.Thread(target=money_laundering, args=(4000000,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print("after two public_money_laundering, I have {}".format(balance))

    @timeit
    def test2():
        global balance
        balance = 2000
        print('Before i go to a new bank ,I have {}'.format(balance))
        t3 = threading.Thread(target=money_laundering_priveate, args=(3000000,))
        t4 = threading.Thread(target=money_laundering_priveate, args=(3000000,))
        t3.start()
        t4.start()
        t3.join()
        t4.join()
        print("after two private money_launderingm I have {}".format(balance))

    test1()
    test2()


def consumer_producer():
    condition = threading.Condition()

    def consumer(cond):

        t = threading.current_thread()
        print('{} start , and waiting for proc'.format(t.name))

        with cond:
            cond.wait()
            print('{} making resource avaiable to consumer'.format(t.name))

    def producer(cond):
        t = threading.current_thread()

        with cond:
            print('{} producer acaiable !'.format(t.name))
            cond.notifyAll() # 激活条件

    c1 = threading.Thread(name='cons1', target=consumer, args=(condition,))
    c2 = threading.Thread(name='cons2', target=consumer, args=(condition,))
    p = threading.Thread(name='prod', target=producer, args=(condition,))
    c1.start()
    time.sleep(1)
    c2.start()
    time.sleep(1)
    p.start()


def consumber_producer_event():
    """一个线程发送事件，其他的线程等待事件的触发  生产者消费者模型"""
    from random import randint

    TIMEOUT = 2
    eve = threading.Event()
    ll = []
    threads = []

    def consumer(event, l):
        """消费者"""
        mt = threading.currentThread()
        while 1:
            event_is_set = event.wait(TIMEOUT)
            if event_is_set:
                try:
                    integer = l.pop()
                    print('{} pop from list by {}'.format(integer, mt.name))
                    event.clear()  # 重制事件状态
                except IndexError:
                    pass  # 刚启动时容错。

    def producer(event, l):
        mt = threading.currentThread()
        while 1:
            integer = randint(10, 100)
            l.append(integer)
            print('{} is append to list by {}'.format(integer, mt.name))
            event.set()
            time.sleep(1)

        pass

    for name in ('consumer1', 'consumer2'):
        t = threading.Thread(name=name, target=consumer, args=(eve, ll))
        t.start()
        threads.append(t)

    p = threading.Thread(name='producer', target=producer, args=(eve, ll))
    p.start()
    threads.append(p)
    for t in threads:
        t.join()

    pass


def consumer_producer_queue():
    """ 有两种模式 priority 优先级模式 LIFOqueue后进先出模式。"""
    # priority 模式
    from random import random
    from Queue import PriorityQueue, LifoQueue

    q = PriorityQueue()

    def double(num):
        return num * 2

    def producer():
        while 1:
            wt = random()
            time.sleep(1)
            print('put', wt)
            q.put((double, wt))

    def consumer():
        while 1:
            task, arg = q.get()
            print arg, task(arg)
            q.task_done()

    for target in (producer, consumer):
        t = threading.Thread(target=target)
        t.start()


def consumer_producer_priqueue():
    """priority 优先级队列"""
    from random import randint
    from Queue import PriorityQueue

    pri_q = PriorityQueue()

    def triple(n):
        return n * 3

    def consumer():
        while 1:
            if pri_q.empty():
                break
            pri, target, arg = pri_q.get()
            print('[PRI: {}], {} * 3 = {}'.format(pri, arg, target(arg)))
            pri_q.task_done()
            time.sleep(1)

        pass

    def producer():
        count = 0
        while 1:
            if count > 50:
                break
            pri = randint(10, 100)
            print('put priority {} '.format(pri))
            pri_q.put((pri, triple, pri))
            count += 1
        pass

    for targ in (producer, consumer):
        t = threading.Thread(target=targ)
        t.start()
        time.sleep(1)


def daemon_and_not_daemon():

    def nd():
        logging.debug("start!")
        time.sleep(6)
        logging.debug("end!")

    def d():
        logging.debug("start")
        time.sleep(3)
        logging.debug("end")

    t = threading.Thread(target=d, name="deamon")
    nt = threading.Thread(target=nd, name='no-deamon')
    t.setDaemon(True)
    t.start()

    nt.start()
    # 论join 的重要性。
    t.join()


# threading pool && threading module programing
def quadra(strings):
    return str(strings) * 4


class Worker(threading.Thread):
    def __init__(self, queue):
        super(Worker, self).__init__()
        self._q = queue
        self.daemon = True
        self.start()

    def run(self):
        while 1:
            f, args, kwargs = self._q.get()

            try:
                print('USE {} '.format(self.name))
                print(f(*args, **kwargs))
            except Exception as e:
                print e
            self._q.task_done()
    pass


class ThreadingPool(object):

    def __init__(self, num_con=5):
        self._q = Queue(num_con)
        for _ in xrange(num_con):
            Worker(self._q)

    def add_task(self, f, *args, **kwargs):
        self._q.put((f, args, kwargs))

    def wait_complete(self):
        self._q.join()
    pass


def test_threading_pool():
    pool = ThreadingPool(10)
    for _ in xrange(1000):
        wt = randint(1, 9)
        pool.add_task(quadra, wt)
        time.sleep(1)
    pool.wait_complete()



def main():
    # nothread()
    # withthread(）
    # ----------------- no threading vs use treading-------------------------
    # show_thread_itself('no muti')
    # print('threading is running! thraead name is {}'.format(threading.current_thread().getName()))
    # t = threading.Thread(target=show_thread_itself, args=(123,), name='Do yourself')
    # t.start()
    # t.join()
    # print('threading {} end.'.format(threading.current_thread().getName()))
    # ------------------ problem on thread lock ---------------------------
    # lock_is_important()
    # ------------------ cunsumer / producter model with condition -----------------------
    # consumer_producer()
    # ------------------ cumsumer/ producter model with event -----------------
    # consumber_producer_event()
    # --------   deamon and not deamon threading   ------------------------
    # daemon_and_not_daemon()
    # ------------------ cunsumer / producter model with Queue -----------------------
    # consumer_producer_queue() # 普通队列
    # consumer_producer_priqueue()  # 优先级队列
    # ------------------ threadingpool ------------
    test_threading_pool()

    pass

if __name__ == '__main__':
    print("python version is {}".format(platform.python_version()))
    main()
    print("done!")

```

### multiprocessing 进程部分

#### mapreduce with multiprocess

> [文章搬运][4], [代码拷贝][5]


[1]: http://wenda.chinahadoop.cn/question/466
[2]: http://www.jiuzhang.com/solutions/max-points-on-a-line/#
[3]: https://github.com/woailuoli993/test/blob/660297df0614925307bb3272dde6eace19284cf0/dosth/testthread.py
[4]: https://pymotw.com/2/multiprocessing/mapreduce.html
[5]: https://github.com/woailuoli993/test/blob/master/dosth/testmapreducemultiprocess.py
