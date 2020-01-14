---
title: "Vertical Scaling of Pods | pod热缩放"
date: 2020-01-09T11:30:34+08:00
categories:
- develop
tags:
- k8s
- proposal
keywords:
- scale
- k8s
- auto
- resource
#thumbnailImage: //example.com/image.jpg
---

这里缅怀 gonum社区的一位杰出贡献者.  Sonia Keys. 

Sonia 是一位 业余天文学家，在03年被授予太平洋天文学杰出贡献奖。Golang 狂热爱好者， golang社区 数学及图形相关项目作者。

------------------------------------------------

OCI 协议中定义了 update api，但是上层的 k8s 编排层却一直缺少了相关的 container 热更新机制。在新产品的 技术调研中， kyle发现了上述功能提案，这里详细概括之。
<!--more-->
Vertical pod auto scaler， [GKE 文档](https://cloud.google.com/kubernetes-engine/docs/concepts/verticalpodautoscaler?hl=zh-cn) 有详细的中文介绍， 社区一般将该功能简称为 VPA.  设计目的是为了能够调整 pod CPU / Memory 的request limit限制。

这里我们希望在 VPA 实现中寻找一个方式能够有所帮助，或者能给予启发。

摘抄自 GKE：

> ## 概览
>
> 垂直 Pod 自动扩缩 (VPA) 使您不必考虑为容器的 CPU 请求和内存求指定具体的值。自动调节程序可以为 CPU 和内存请求和限制建议值，也可以自动更新值。
>
> 垂直 Pod 自动扩缩提供以下好处：
>
> - 因为 Pod 完全用其所需，所以集群节点使用效率高。
> - Pod 会被安排到具有适当可用资源的节点上。
> - 您不必运行耗时的基准测试任务来确定 CPU 和内存请求的正确值。
> - 自动调节程序可以随时调整 CPU 和内存请求，而无需您执行任何操作，所以维护时间更短。

ok ，别人家的瓜只能吃到这里了。

漫长的 G站扫街环节后。。。

该功能的设计环节较为挫折，第一次参与人数较多的 讨论发生在 16年年初，隶属于 sig-node 小组，之后被重新分配到了 sig-autoscaling 小组下。 大概经过了 3年左右的开发周期。 将在近期（k8s 1.18 ）GA.  

 [设计方案][1]详细描写了技术细节。这里会挑一些重点介绍。



## 介绍



### 技术细节

- [资源计算](https://kubernetes.io/docs/user-guide/compute-resources/)
- [资源Qos](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/node/resource-qos.md)
- [准入控制](https://kubernetes.io/docs/admin/admission-controllers/)
- [外部准入控制](https://kubernetes.io/docs/admin/extensible-admission-controllers/#external-admission-webhooks)

### 目标：

1. 引入自动维护，减少维护成本。
2. 提高资源利用率，减少container OOM 发生的情况。



### 相关功能

#### HPA( Horizontal Pod Autoscaler)

横向扩展，  通过监听 cpu 压力和其他用户指定的 metric 动态缩扩。一般情况下 用户将会对无状态负载制定 HPA 方案，对有状态服务设置 VPA.

#### CA (Cluster Autoscaler)

自动进行集群大小的配置。 可以和 VPA, HPA 组成完整的自动化伸缩方案。

#### initial resources

概念性的功能，基于历史利用率指标， 可以在pod创建时给予resource建议。 VPA 会覆盖重写该功能。

#### Resource estimation 

资源预算, 旨在提高节点资源的利用率。通过临时回收容器当前未使用的资源。 可以对标虚拟化的 DMC.概念和实现。使用Node pod 短时间时序数据进行资源回收和释放。 该功能与 VPA 互补。 仍处于**设计阶段**。



### 需求

#### 功能特性

1. VPA 可以修改 POD 的资源 request/limit 
2. VPA 可以对 CPU 高负载， 内存 OOM 的事件作出相应。
3. 重启 VPA 管理下的 pod 可以遵循破坏预算功能（disruption budget）
4. VPA 可配置：用户可以制定 VPA 动态缩扩的上下限。
5. VPA 支持 pod controller,至少支持 deployment.

.....

其他:

	- 高可用的
	- 在 in-place update 功能完成后可以自动支持。（我们关注的重点之一）



###  设计

1. 添加了一个 新的 API Server资源`vertialPodAutoscaler`,  包含了一个**label selector**去筛选 pod，使用 **resources policy**控制如何将pod 的配置更新， 并且给出推荐的 pod resource 配置。
2. 一个新的组件 **VPA Recommender** ，从 `metrics-server` 响应消费集群所有的 pod 资源负载信号， 和 OOM 信号.
3. VPA Recommender **监听所有的 pods**，持续计算针对这些pod 的推荐资源用量，并**存储在 VPA 对象中**。
4. VPA Recommender 还会额外的 暴露一个同步 API ，可以获取 POD 描述， 并且返回 推荐的 资源配置。
5.  所有的Pod 资源创建请求 会经由 VPA 的 **Admission Controller**，如果pod 可以匹配到任何读经的 VPA 对象，该访问控制插件会将 pod 的 资源字段，如果 上面的 VPA recommender 不可访问， 则会降级到使用已经缓存的vpa资源。
6. 另一个独立组件 **VPA Updater**，负责实施更新 pods，如果一个 pod 使用 “`auto`”模式的 VPA 配置，则该组件可以自动决定更新其 resource 配置到推荐值。这里要求 pod资源需要隶属于其他上层抽象管理资源，如 `replicaset`等,可以在 pod因为修改配置后被销毁后重新创建。 在之后的更新中， Updater 会引入  `in-place-update` 模式, 可以绕过 上述管理资源，因其可以直接在pod不销毁的情况下进行资源修改。
7. CPA 之 控制资源的 下限，即 resource 的 request，但会将其limit设置为 infinity.  其 request 的数值根据 当前和之前运行时的 监控数据计算得出。
8. 新组件：**History Storage**，同样的， 会消费来自 API Server 的资源利用率和OOM 事件（与 Recommender  组件相同），并且将其持久化存储。  该组件被 Recommender 用作在 启动时初始化。 可以由任意数据库支持。 MVP版本使用 Prometheus, 至少对于 资源使用率的部分是这样的。

#### 架构图

![vpa-architecture](http://qiniu.heyuhua.com/blog/post/vpa-architecture.png)



[1]: https://github.com/kubernetes/community/blob/master/contributors/design-proposals/autoscaling/vertical-pod-autoscaler.md	"设计实现方案"



#### API

上面的 API  对象 `verticalPodAutoscaler`  的一些详细信息。



{{< codeblock lang="go" >}}
// VerticalPodAutoscalerSpec is the specification of the behavior of the autoscaler.
type VerticalPodAutoscalerSpec {
	// A label query that determines the set of pods controlled by the Autoscaler.
	// More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#label-selectors
	Selector *metav1.LabelSelector

	// Describes the rules on how changes are applied to the pods.
	// +optional
	UpdatePolicy PodUpdatePolicy
	
	// Controls how the autoscaler computes recommended resources.
	// +optional
	ResourcePolicy PodResourcePolicy
}

// VerticalPodAutoscalerStatus describes the runtime state of the autoscaler.
type VerticalPodAutoscalerStatus {
	// The time when the status was last refreshed.
	LastUpdateTime metav1.Time
	// The most recently computed amount of resources recommended by the
	// autoscaler for the controlled pods.
	// +optional
	Recommendation RecommendedPodResources	
	// A free-form human readable message describing the status of the autoscaler.
	StatusMessage string
}
{{< /codeblock >}}

##### Selector

指明了 哪些pod会被 VPA 控制。 也就是说 用户需要在编辑 pod时确保 label中包含了 VPA的信息。

##### Update Policy

```json
"updatePolicy" {
  "mode": "",
}				
```

模式指定。 VPA 包含三种resource 自动伸缩策略。

1. "`Initial`": VPA 只在 创建 pod时指定资源，在之后的pod生命周期中都不做修改。
2. "`Auto`"(defualt): 可以在 Pod 创建和运行时更新，包括驱逐， 重新规划（reschedule).
3. "off"：没什么卵用的开发用功能。不作为，但是会记录运行时metric.

##### Resource Policy

资源上下限。自动伸缩波动范围 threshold.


写到这里应该是差不多了。 后面的实现细节并不设计 resource in-place update 相关内容。
