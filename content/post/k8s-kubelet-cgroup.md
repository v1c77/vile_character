---

title: "kubelet Cgroup 管理流程"
date: 2020-01-14T11:35:58+08:00
categories:
- develop
tag: k8s 
keywords:
- k8s
- kubelet
- cgroup
#thumbnailImage: //example.com/image.jpg
---

新年第一个flag: 春节期间《缺氧》能解决气体和液体供应问题。
<!--more-->

> 本文基于 k8s 近期 release, git: commit 70132b0f130acc0bed193d9ba59dd186f0e634cf (HEAD, tag: v1.17.0)

## 前言：寻找可能性 ---- 混编 VM 与 Pod cgroup
想象 k8s 可以同时管理 VM 资源了
如何将 vm 资源的cpu，内存配置抽象成 cgroup 并使用 kubelet CgroupManager 统一管理?

##  kubelet 的 Cgroup 管理模型

kubelet 作为 k8s 系统中各个节点的“话事者”，其 `ContainerManger` 模块包揽了所有的 cgroup 管理工作。
ContainerManager 将 Pod 的 cgroup 模型做了层次分离： container -> Pod -> Qos -> Node。

### Node level
节点层面 主要聚焦于 cgroup 横向分配， 通过隔离不同类型 的 cgroup 进行抽象。
```
                        Node Capacity
                    ---------------------------
                    |     kube-reserved       |
                    |-------------------------|
                    |     system-reserved     |
                    |-------------------------|
                    |    eviction-threshold   |
                    |-------------------------|
                    |                         |
                    |      allocatable        |
                    |   (available for pods)  |
                    |                         |
                    |                         |
                    ---------------------------
```
默认情况下 节点粒度的管理 分配了 k8s 服务组件的 cgroup， 系统非内核 进程 cgroup， 还有 pod 资源的 cgroup.

{{< codeblock "server.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/cmd/kubelet/app/server.go#L709" "cmd/kuelet/app/server.go" >}}
kubeDeps.ContainerManager, err = cm.NewContainerManager(
    kubeDeps.Mounter,
    kubeDeps.CAdvisorInterface,
    cm.NodeConfig{
        RuntimeCgroupsName:    s.RuntimeCgroups, // `runtime-cghroups`  配置, 创建和运行容器运行时的 cgroup 的绝对名称
        SystemCgroupsName:     s.SystemCgroups, // cgroup 的绝对名称，用于所有尚未放置在根目录下某 cgroup 内的非内核进程。空值表示不指定 cgroup。回滚该参数需要重启机器。
        KubeletCgroupsName:    s.KubeletCgroups, // 用于创建和运行 kubelet 的 cgroup 的绝对名称。
        ContainerRuntime:      s.ContainerRuntime,
        CgroupsPerQOS:         s.CgroupsPerQOS,  // 将 Pod 按照不同的 QOS 优先级进行 cgroup 拆分。
        CgroupRoot:            s.CgroupRoot,
        CgroupDriver:          s.CgroupDriver,
        KubeletRootDir:        s.RootDirectory,
        ProtectKernelDefaults: s.ProtectKernelDefaults,
        NodeAllocatableConfig: cm.NodeAllocatableConfig{ // 节点可分配 resource 计算结构体
            KubeReservedCgroupName:   s.KubeReservedCgroup,   // k8s 自身服务 所在 cgroup
            SystemReservedCgroupName: s.SystemReservedCgroup, // 操作系统非内核进程外的其他进程所在cgroup
            EnforceNodeAllocatable:   sets.NewString(s.EnforceNodeAllocatable...), // `enforce-node-allocatable` 参数设置，
            KubeReserved:             kubeReserved,
            SystemReserved:           systemReserved,
            ReservedSystemCPUs:       reservedSystemCPUs, // 预留给节点其他无关进程的 cpu.
            HardEvictionThresholds:   hardEvictionThresholds,
        },
        QOSReserved:                           *experimentalQOSReserved,
        ExperimentalCPUManagerPolicy:          s.CPUManagerPolicy,
        ExperimentalCPUManagerReconcilePeriod: s.CPUManagerReconcilePeriod.Duration,
        ExperimentalPodPidsLimit:              s.PodPidsLimit,
        EnforceCPULimits:                      s.CPUCFSQuota,
        CPUCFSQuotaPeriod:                     s.CPUCFSQuotaPeriod.Duration,
        ExperimentalTopologyManagerPolicy:     s.TopologyManagerPolicy,
    },
    s.FailSwapOn,
    devicePluginEnabled,
    kubeDeps.Recorder)
{{</ codeblock >}}

通过如上 模块设计， Pod 的 allocatable resource 可以通过简单的减法运算得出

> `allocatable = NodeCapacity - [kube-reserved] - [system-reserved] - [eviction-threshold]`


我们的测试集群目前配置如下：
- CgroupDriver : systemd
- SystemCgroups: /system.slice
- KubeletCgroups: /system.slice
- SystemReservedCgroups:  /system.slice
- KubeReservedCgroups: /system.slice/kubelet.service

额外的：
- VM 相关 cgroup 配置位于  /system.slice/machine.slice， 需要纳入 node的 统一管理。 


### QOS level
在上一节 Node 相关配置中， `--cgroup-per-qos` 配置（默认为 true） 会生成该层级的 Cgroup 配置。

目前 QOS 共分为 3 种。

qos 级别

- Guaranteed【老板（我要的都是我的）】：pod 里每个容器都必须设定 `request` 和 `limit`，并且值必须相同 
- Burstable  【洗碗工（底薪+提成）】：pod 里至少有一个容器的 cpu 或者 memory 设置了 `request` 值
- BestEffort【切格瓦拉（能偷到的都是我的）】：POD 的所有容器都没有指定CPU和内存的 `request` 和 `limit`

初始化过程发生在  `kl.containerLogManager.Start() > setupNode` 过程：

```golang
	// Setup top level qos containers only if CgroupsPerQOS flag is specified as true
	if cm.NodeConfig.CgroupsPerQOS {
		if err := cm.createNodeAllocatableCgroups(); err != nil {
			return err
		}
		err = cm.qosContainerManager.Start(cm.getNodeAllocatableAbsolute, activePods)
		if err != nil {
			return fmt.Errorf("failed to initialize top level QOS containers: %v", err)
		}
	}
```
```createNodeAllocatableCgroups``` 会初始化 一个 `system.slice/kubepods.slice` cgroup, 用于放置 pod 资源

```go
	// Top level for Qos containers are created only for Burstable
	// and Best Effort classes
	qosClasses := map[v1.PodQOSClass]CgroupName{
		v1.PodQOSBurstable:  NewCgroupName(rootContainer, strings.ToLower(string(v1.PodQOSBurstable))),
		v1.PodQOSBestEffort: NewCgroupName(rootContainer, strings.ToLower(string(v1.PodQOSBestEffort))),
	}

    // ...

    // Store the top level qos container names
	m.qosContainersInfo = QOSContainersInfo{
		Guaranteed: rootContainer,
		Burstable:  qosClasses[v1.PodQOSBurstable],
		BestEffort: qosClasses[v1.PodQOSBestEffort],
	}
```

初始化后 `Burstable` 和 `BestEffort`类型的pod cgroup 会被生成在， `/system.slice/kubepods.slice` 下。

而  `guaranteed` 类型 pod 会直接 运行在  /system.slice/kubepods.slice 下.

这里发生了 kubelet 层的第一次  cgroup 设置： `BestEffort`其中的 cpu.shares 被设置为minShares(=2).

表示 在 cpu高负载情况下， BestEffort. Pod 将会享有 pod中最少的的cpu时间段。



同时，在containerManager start 之后， 还会有一个常驻go程   循环执行 `UpdateCgroups()`:

```go
func (m *qosContainerManagerImpl) UpdateCgroups() error {
	m.Lock()
	defer m.Unlock()

	qosConfigs := map[v1.PodQOSClass]*CgroupConfig{
		v1.PodQOSBurstable: {
			Name:               m.qosContainersInfo.Burstable,
			ResourceParameters: &ResourceConfig{},
		},
		v1.PodQOSBestEffort: {
			Name:               m.qosContainersInfo.BestEffort,
			ResourceParameters: &ResourceConfig{},
		},
	}

	// update the qos level cgroup settings for cpu shares
	if err := m.setCPUCgroupConfig(qosConfigs); err != nil {
		return err
	}

	// update the qos level cgroup settings for huge pages (ensure they remain unbounded)
	if err := m.setHugePagesConfig(qosConfigs); err != nil {
		return err
	}

	if utilfeature.DefaultFeatureGate.Enabled(kubefeatures.QOSReserved) {
		for resource, percentReserve := range m.qosReserved {
			switch resource {
			case v1.ResourceMemory:
				m.setMemoryReserve(qosConfigs, percentReserve)
			}
		}

		updateSuccess := true
		for _, config := range qosConfigs {
			err := m.cgroupManager.Update(config)
			if err != nil {
				updateSuccess = false
			}
		}
		if updateSuccess {
			klog.V(4).Infof("[ContainerManager]: Updated QoS cgroup configuration")
			return nil
		}

		// If the resource can adjust the ResourceConfig to increase likelihood of
		// success, call the adjustment function here.  Otherwise, the Update() will
		// be called again with the same values.
		for resource, percentReserve := range m.qosReserved {
			switch resource {
			case v1.ResourceMemory:
				m.retrySetMemoryReserve(qosConfigs, percentReserve)
			}
		}
	}

	for _, config := range qosConfigs {
		err := m.cgroupManager.Update(config)
		if err != nil {
			klog.Errorf("[ContainerManager]: Failed to update QoS cgroup configuration")
			return err
		}
	}

	klog.V(4).Infof("[ContainerManager]: Updated QoS cgroup configuration")
	return nil
}

```



该流程保证了 kubepod 相关meta配置不被串改。



### Pod level

上两层的 cgroup 配置 大多属于模块划分相关的内容， Pod level 的 cgroup 配置 则更接近于 k8s 需要着重了解的一层。

 {{< codeblock "kubelet.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/pkg/kubelet/kubelet.go#L1617" "pkg/kubelet/kueblet.go" >}}

// Create Cgroups for the pod and apply resource parameters
// to them if cgroups-per-qos flag is enabled.
// TODO(yuhua): pod cgroup 创建
pcm := kl.containerManager.NewPodContainerManager()
// If pod has already been terminated then we need not create
// or update the pod's cgroup
if !kl.podIsTerminated(pod) {
   // When the kubelet is restarted with the cgroups-per-qos
   // flag enabled, all the pod's running containers
   // should be killed intermittently and brought back up
   // under the qos cgroup hierarchy.
   // Check if this is the pod's first sync
   firstSync := true
   for _, containerStatus := range apiPodStatus.ContainerStatuses {
      if containerStatus.State.Running != nil {
         firstSync = false
         break
      }
   }
   // Don't kill containers in pod if pod's cgroups already
   // exists or the pod is running for the first time
   podKilled := false
   if !pcm.Exists(pod) && !firstSync {
      if err := kl.killPod(pod, nil, podStatus, nil); err == nil {
         podKilled = true
      }
   }
   // Create and Update pod's Cgroups
   // Don't create cgroups for run once pod if it was killed above
   // The current policy is not to restart the run once pods when
   // the kubelet is restarted with the new flag as run once pods are
   // expected to run only once and if the kubelet is restarted then
   // they are not expected to run again.
   // We don't create and apply updates to cgroup if its a run once pod and was killed above
   if !(podKilled && pod.Spec.RestartPolicy == v1.RestartPolicyNever) {
      if !pcm.Exists(pod) {
         if err := kl.containerManager.UpdateQOSCgroups(); err != nil {
            klog.V(2).Infof("Failed to update QoS cgroups while syncing pod: %v", err)
         }
         if err := pcm.EnsureExists(pod); err != nil {
            kl.recorder.Eventf(pod, v1.EventTypeWarning, events.FailedToCreatePodContainer, "unable to ensure pod container exists: %v", err)
            return fmt.Errorf("failed to ensure that the pod: %v cgroups exist and are correctly applied: %v", pod.UID, err)
         }
      }
   }
}

{{</codeblock>}}

上述流程我们需要关注的是 如下几个流程

>  syncPod  -> kl.containerManager.NewPodContainerManager() -> pcm.Exists(pod) -> kl.containerManager.UpdateQOSCgroups()



`NewPodContainerManager` 并没有实质性的cgroup操作，紧跟着的判断 `Exists(pod)`-> `GetPodContainerName`函数调用会尝试获取 当前 pod应当存在的 cgroup路径。并检查 pod 对应cgroup的存在。

如果发现不存在  对应cgroup 则进入创建流程 【创建cgroup 发生在 pod其他资源创建前】，  即 `UpdateQOSChroups`:

还函数会进行：

- `setCPUCgroupConfig`  比如说保证 BestEffort  pod cpu share =2; 计算 Burst.slice 路径 cpu shares 设置应该为  **所有 burstable_pod_CPU_request** 的和。

* `setMemoryReserve` 取决于是否开启了特性功能 **QOSReserved**, 该功能会为  **Burstable** 和 **BestEffort** pod slice 设置 可用内存上限， 基于实时计算的各个类型的 pod的 内存使用状况。  【暂定默认关闭】
* `setHugePagesConfig` 根据功能开关设置 hugepage 用量。【暂定默认关闭】

上述动作完成后 将会执行 pod 粒度 的 cgroup  创建， 更新操作 `EnsureExists` 



 {{< codeblock "pod_container_manager_linux.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/pkg/kubelet/cm/pod_container_manager_linux.go#L76" "pkg/kubelet/cm/pod_container_manager_linux.go#L76" >}}
// EnsureExists takes a pod as argument and makes sure that
// pod cgroup exists if qos cgroup hierarchy flag is enabled.
// If the pod level container doesn't already exist it is created.
func (m *podContainerManagerImpl) EnsureExists(pod *v1.Pod) error {
	podContainerName, _ := m.GetPodContainerName(pod)
	// check if container already exist
	alreadyExists := m.Exists(pod)
	if !alreadyExists {
		// Create the pod container
		containerConfig := &CgroupConfig{
			Name:               podContainerName,
			ResourceParameters: ResourceConfigForPod(pod, m.enforceCPULimits, m.cpuCFSQuotaPeriod),
		}
		if utilfeature.DefaultFeatureGate.Enabled(kubefeatures.SupportPodPidsLimit) && m.podPidsLimit > 0 {
			containerConfig.ResourceParameters.PidsLimit = &m.podPidsLimit
		}
		if err := m.cgroupManager.Create(containerConfig); err != nil {
			return fmt.Errorf("failed to create container for %v : %v", podContainerName, err)
		}
	}
	// Apply appropriate resource limits on the pod container
	// Top level qos containers limits are not updated
	// until we figure how to maintain the desired state in the kubelet.
	// Because maintaining the desired state is difficult without checkpointing.
	if err := m.applyLimits(pod); err != nil {
		return fmt.Errorf("failed to apply resource limits on container for %v : %v", podContainerName, err)
	}
	return nil
}
{{</codeblock>}}