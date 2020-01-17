---

title: "从kubelet Cgroup 管理流程入手"
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

上述代码中 `m.cgroupManager.Create(containerConfig` 可以完成 pod 级别的 cgroup创建， 至此我们的 pod cgroup container 已经初具雏形。

```shell
[root@node1]# tree /sys/fs/cgroup/cpu -d
/sys/fs/cgroup/cpu
├── kubepods
│   ├── besteffort
│   │   ├── pode098d78945a4d359594f9c27066aa202
│   │   │   ├── 5fca7a73d4b5c7e7a6c35415e2bfeb5533c5fc1d1b4aa80bc4cb641213ee29a3
│   │   │   └── b10831a7a2cf4e96ff6b186396e9e393e5b02aa8c447e988cc6cca5172fc5c89
│   │   └── podfc7fbc35-bb79-4a33-80a0-371d438f221e
│   │       ├── 07703a4a76b926c8432c3a8ab50b69b8dfd2891733a09d830fc1a08f8a8e0a1c
│   │       └── 3a7550ae2bd7784bc7f74fa0288d361e6d569595a0ba237bb63cdd5468073316
│   └── burstable
│       ├── pod420984c2d6d62f72216bba6857bc368b
│       │   ├── 5f734d0677fb4dd0f3e3dd3647be6ad19ec728fd3e28860c6023ea6efb7fc331
│       │   └── 93cd418eaddf86be58b200c109674a36cc04fee0eccfae4a7838a1b0e6a4f978
│       ├── pod4ebb633e-f8ba-43ee-94c7-1cf8c9105555
│       │   └── 1bc40d00174d3ea84f4fce14d734a45115e72e4af394bd7d684d9691e7749995
│       ├── podcd4bc68a-faf3-4c08-8d07-57d25a68ee1b
│       │   ├── 62ba8b7c6e1afc62d16b65e0d0ae9f82254260815025ecb6c863fa82c9ea5e8e
│       │   └── c7aca0c0fdf230a6378e3325f03242ff561ec95e7f62b3b852f2877af0235792
│       ├── podd4f2a7d434e44edd8e4a0960111bda9f
│       │   ├── 08d95544fcd3a5631c5a6a550d42bcddf8319cfb1fbe7f2482d969fc19356466
│       │   └── a7a39f33fddce54c64c4a6d0bf4b499fe3d6b3d7c7f5fc0d54445ade5cad24b1
│       ├── pode8486b59c2c8408b07026a560746b02c
│       │   ├── b9fb9af9f1c5991786c6457f5b33c90ee8e33a3d68605d409b7a2c30d5565699
│       │   └── f7f6773069032faa45ef3fc62fe337127fe40795ebc3758d03e149376d18d3da
│       ├── pode86c3e73-a96e-4ae8-9ff6-fd401cf5c9aa
│       │   ├── 4ad31b5ea0ad5743eeb67628c3bf9275d2131f2132a4bbe7081c05f63c6604ea
│       │   └── 5f31deed41c58dbc0a0530b964926968d272e846cf9d91452c40797ace7fb90a
│       └── podf27baf8c-6c71-4f3a-9445-0c63eb33d586
│           ├── 1ae1d0d1fb0d44652c8ad8ef2d782628ec04a7b0e6e5718ea6788af178505ba2
│           └── 5e898be28b1cb5ccb7f9f52eddee06c114d7d42b951b256da5544128093216be
├── machine.slice
│   └── machine-qemu\\x2d18\\x2dvm123.scope
│       ├── emulator
│       └── vcpu0
├── system.slice
└── user.slice
```
> `machine.slice` 是 libvirt 针对每个 qemu 进程生成的 cgroup管理空间.  我们意在将其纳入 k8s cgoup 统计范围内。



### Container level 

上述 Node level 发生在 kubelet 的 SyncPod 函数执行过程中， 同样的， container 相关的 cgroup创建 也是在这之后。

故事仍然要从pod 创建请求开始， 从 入口处的 kubelet   `syncLoop`  -> `syncLoopIteration` -> `HandlePodAddtions` -> `dispatchWork` -> `UpdatePod` -> `managePodLoop` -> `SyncPod` -> `kl.containerRuntime.SyncPod`

进入 真正创建  container流程，

{{< codeblock "kuberuntime_manager.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/ppkg/kubelet/kuberuntime/kuberuntime_manager.go#L640" "pkg/kubelet/kuberuntime/kuberuntime_manager.go#L640" >}}
// SyncPod syncs the running pod into the desired pod by executing following steps:
//
//  1. Compute sandbox and container changes.
//  2. Kill pod sandbox if necessary.
//  3. Kill any containers that should not be running.
//  4. Create sandbox if necessary.
//  5. Create ephemeral containers.
//  6. Create init containers.
//  7. Create normal containers.
// TODO(yuhua): 创建container 之处。
func (m *kubeGenericRuntimeManager) SyncPod(pod *v1.Pod, podStatus *kubecontainer.PodStatus, pullSecrets []v1.Secret, backOff *flowcontrol.Backoff) (result kubecontainer.PodSyncResult)
{{</codeblock>}}

containerRuntime.SyncPod 主要内容涉及到 如下几个步骤

- 计算 sandbox 和 container 变化
- 删除无用sandbox
- 删除无用 容器
- 创建沙箱
- 创建 一次性容器
- 创建 初始化容器
- 创建 其他容器。

上述前4步都与 cgroup无关，这里最后的三个创建步骤 都使用了 一些公用逻辑。

{{< codeblock "kuberuntime_manager.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/pkg/kubelet/kuberuntime/kuberuntime_manager.go#L780" "pkg/kubelet/kuberuntime/kuberuntime_manager.go#L780" >}}
// Helper containing boilerplate common to starting all types of containers.
// typeName is a label used to describe this type of container in log messages,
// currently: "container", "init container" or "ephemeral container"
start := func(typeName string, container *v1.Container) error {
	startContainerResult := kubecontainer.NewSyncResult(kubecontainer.StartContainer, container.Name)
	result.AddSyncResult(startContainerResult)

isInBackOff, msg, err := m.doBackOff(pod, container, podStatus, backOff)
if isInBackOff {
	startContainerResult.Fail(err, msg)
	klog.V(4).Infof("Backing Off restarting %v %+v in pod %v", typeName, container, format.Pod(pod))
	return err
}

klog.V(4).Infof("Creating %v %+v in pod %v", typeName, container, format.Pod(pod))
// NOTE (aramase) podIPs are populated for single stack and dual stack clusters. Send only podIPs.
if msg, err := m.startContainer(podSandboxID, podSandboxConfig, container, pod, podStatus, pullSecrets, podIP, podIPs); err != nil {
	startContainerResult.Fail(err, msg)
	// known errors that are logged in other places are logged at higher levels here to avoid
	// repetitive log spam
	switch {
	case err == images.ErrImagePullBackOff:
		klog.V(3).Infof("%v start failed: %v: %s", typeName, err, msg)
	default:
		utilruntime.HandleError(fmt.Errorf("%v start failed: %v: %s", typeName, err, msg))
	}
	return err
}
{{</codeblock>}}

这里只需要关注 `startContainer` 相关逻辑：

{{< codeblock "kuberuntime_manager.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/pkg/kubelet/kuberuntime/kuberuntime_container.go#L95" "pkg/kubelet/kuberuntime/kuberuntime_container.go#L95" >}}
// startContainer starts a container and returns a message indicates why it is failed on error.
// It starts the container through the following steps:
// * pull the image
// * create the container
// * start the container
// * run the post start lifecycle hooks (if applicable)
func (m *kubeGenericRuntimeManager) startContainer(podSandboxID string, podSandboxConfig *runtimeapi.PodSandboxConfig, container *v1.Container, pod *v1.Pod, podStatus *kubecontainer.PodStatus, pullSecrets []v1.Secret, podIP string, podIPs []string) (string, error)
{{</codeblock>}}

这里的 `podSandboxConfig` 包含以下字段：

```go
Linux                *LinuxPodSandboxConfig `protobuf:"bytes,8,opt,name=linux,proto3" json:"linux,omitempty"`
```

{{< codeblock "kuberuntime_manager.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/staging/src/k8s.io/cri-api/pkg/apis/runtime/v1alpha2/api.pb.go#L796" "staging/src/k8s.io/cri-api/pkg/apis/runtime/v1alpha2/api.pb.go#L796" >}}
// LinuxPodSandboxConfig holds platform-specific configurations for Linux
// host platforms and Linux-based containers.
type LinuxPodSandboxConfig struct {
	// Parent cgroup of the PodSandbox.
	// The cgroupfs style syntax will be used, but the container runtime can
	// convert it to systemd semantics if needed.
	CgroupParent string `protobuf:"bytes,1,opt,name=cgroup_parent,json=cgroupParent,proto3" json:"cgroup_parent,omitempty"`
	// LinuxSandboxSecurityContext holds sandbox security attributes.
	SecurityContext *LinuxSandboxSecurityContext `protobuf:"bytes,2,opt,name=security_context,json=securityContext,proto3" json:"security_context,omitempty"`
	// Sysctls holds linux sysctls config for the sandbox.
	Sysctls              map[string]string `protobuf:"bytes,3,rep,name=sysctls,proto3" json:"sysctls,omitempty" protobuf_key:"bytes,1,opt,name=key,proto3" protobuf_val:"bytes,2,opt,name=value,proto3"`
	XXX_NoUnkeyedLiteral struct{}          `json:"-"`
	XXX_sizecache        int32             `json:"-"`
}
{{</codeblock>}}

这里可以看到  CgroupParent 限制了 cgroup创建的 父路径。 至此 k8s 层的cgroup创建过程结束。

创建结束后的  cgroup拓扑参考 Node章节结果。



## 其他相关特性

### CPUSet

 当 VM 与 Pod 进行混合编排， 虚拟化语义中的 vcpu pin  可以使用  cgroup 的 cpu_set 作为 功能映射

k8s 中 feature Gate   `CPUManager ` 负责 管理  容器的 cpu set 设置  该功能 在 k8s 1.8 进入 alpha, 在 1.10 后 beta， 目前 （k8s 1.17） 仍然属于 beta 状态。 

#### CPU Manager工作流

CPU Manager为满足条件的Container分配指定的CPUs时，会尽量按照CPU Topology来分配，也就是考虑CPU Affinity，按照如下的优先顺序进行CPUs选择：（Logic CPUs就是Hyperthreads）

1.  如果Container请求的Logic CPUs数量不小于单块CPU Socket中Logci CPUs数量，那么会优先把整块CPU Socket中的Logic CPUs分配给该Container。 
2.  如果Container剩余请求的Logic CPUs数量不小于单块物理CPU Core提供的Logic CPUs数量，那么会优先把整块物理CPU Core上的Logic CPUs分配给该Container。 
3.  Container剩余请求的Logic CPUs则从按照如下规则排好序的Logic CPUs列表中选择： 
   - number of CPUs available on the same socket
   - number of CPUs available on the same core

#### Discovering CPU topology

CPU Manager能正常工作的前提，是发现Node上的CPU Topology，Discovery这部分工作是由cAdvisor完成的。

在cAdvisor的MachineInfo中通过Topology会记录cpu和mem的Topology信息。其中Topology的每个Node对象就是对应一个CPU Socket。

#### 创建容器

对于满足前面提到的满足static policy的Container创建时，kubelet会为其按照约定的cpu affinity来为其挑选最优的CPU Set。Container的创建时CPU Manager工作流程大致如下：

1. Kuberuntime调用容器运行时去创建该Container。

2. Kuberuntime将该Container交给CPU Manager处理。

3. CPU Manager为Container按照static policy逻辑进行处理。

4. CPU Manager从当前Shared Pool中挑选“最佳”Set拓扑结构的CPU，对于不满足Static Policy的Contianer，则返回Shared Pool中所有CPUS组成的Set。

5. CPU Manager将对该Container的CPUs分配情况记录到Checkpoint State中，并且从Shared Pool中删除刚分配的CPUs。

6. CPU Manager再从state中读取该Container的CPU分配信息，然后通过UpdateContainerResources cRI接口将其更新到Cpuset Cgroups中，包括对于非Static Policy Container。

7. Kuberuntime调用容器运行时Start该容器。

   

该过程入口处于 上一章节的 Container level 中的 `startContainer` 函数：
{{< codeblock "kuberuntime_manager.go" "golang" "https://github.com/kubernetes/kubernetes/blob/v1.17.0/pkg/kubelet/kuberuntime/kuberuntime_container.go#L134" "pkg/kubelet/kuberuntime/kuberuntime_container.goo#L134" >}}

	// TODO(yuhua): 设置 CPUset
	err = m.internalLifecycle.PreStartContainer(pod, container, containerID)
	if err != nil {
		s, _ := grpcstatus.FromError(err)
		m.recordContainerEvent(pod, container, containerID, v1.EventTypeWarning, events.FailedToStartContainer, "Internal PreStartContainer hook failed: %v", s.Message())
		return s.Message(), ErrPreStartHook
	}
{{</codeblock>}}






## 写在最后

  libvirt 已经实现了完整的 cgroup 抽象， 但是缺少完整的 cgroup 管理流程，如果想要通过 cgroup将 vm  资源抽象 并与  Pod 的资源做统一管理， 我们在前端 （kubelet） 及  对应的 后端 （VRI） 设计完整的   cgroup 操作流程。


### 参考:

1. [  k8s ](https://github.com/kubernetes/kubernetes)
2. [  cpu manager ](https://cloud.tencent.com/developer/article/1402119)
3. [ libvirt cgroups ](https://libvirt.org/cgroups.html)