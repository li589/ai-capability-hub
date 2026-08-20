# 能力索引（24 项）

## 磁盘与存储（5 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `disk-space` | 磁盘空间分析与清理 | 磁盘满、空间不足、No space、inode、du、df、日志清理 | `references/disk/disk-space.md` |
| `disk-partition` | 磁盘分区管理 | 分区、fdisk、parted、GPT、MBR、新磁盘 | `references/disk/disk-partition.md` |
| `disk-filesystem` | 文件系统管理 | 格式化、挂载、fstab、fsck、mkfs、ext4、xfs | `references/disk/disk-filesystem.md` |
| `disk-lvm` | LVM 逻辑卷管理 | LVM、扩容、lvextend、pvcreate、快照 | `references/disk/disk-lvm.md` |
| `disk-health` | 磁盘健康检测 | SMART、坏块、磁盘寿命、NVMe、I/O error | `references/disk/disk-health.md` |

## 网络（3 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `network-check` | 网络连通性诊断 | ping不通、端口不通、DNS、防火墙、路由、ssh连不上 | `references/network/network-check.md` |
| `network-latency` | 网络丢包与延迟 | 丢包、延迟高、RTT、网络慢、重传、ethtool、nettrace、网络抖动、TCP重传、Ring Buffer、softnet、conntrack满、conntrack table full、drop reason、eBPF网络诊断、报文跟踪、协议栈延迟、ping延迟正常但应用慢、传输速度慢、首次连接慢、ARP、拥塞窗口、BDP、TCP缓冲区、Nagle、偶发延迟、持续延迟、时段型延迟、网卡错误、rx dropped、吞吐低 | `references/network/network-latency.md`（主入口，自动路由到丢包/延迟子文件） |
| — | 丢包排查子文件 | Ring Buffer溢出、softnet backlog溢出、conntrack满、kfree_skb、dropwatch | `references/network/network-packet-loss.md` |
| — | 延迟排查子文件 | mtr逐跳、TCP拥塞恢复、bufferbloat、队列延迟、softirq积压、GRO、ARP解析延迟 | `references/network/network-latency-diag.md` |

## 性能分析（7 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `cpu-flamegraph` | CPU 火焰图 | 火焰图、CPU热点、perf-prof profile、调用栈、Java进程CPU高、JVM性能、JIT、进程CPU占用高、nginx热点、D状态、进程阻塞、task-state、dwarf栈回溯、内核态热点、用户态热点、kmalloc调用路径、缺页异常、flamegraph.pl、folded文件、SVG火焰图、优化前后对比、perf-prof安装、FlameGraph安装 | `references/performance/cpu-flamegraph.md` |
| `syscall-hotspot` | 系统调用热点 | 系统调用慢、strace、perf trace、syscall、futex延迟、epoll_wait延迟、系统调用报错、errno、IO系统调用、进程hang住、系统调用频率、系统调用耗时 | `references/performance/syscall-hotspot.md` |
| `sched-latency` | 进程调度延迟 | 调度延迟、rundelay、抢占、唤醒延迟、P99延迟毛刺、cgroup CPU限流、CPU quota、RD状态、NUMA调度、进程响应慢但CPU不高、容器变慢、调度延迟监控 | `references/performance/sched-latency.md` |
| `irq-balance` | 中断均衡排查 | 软中断、硬中断、中断不均、ksoftirqd、RSS哈希不均、NET_RX集中、网络吞吐上不去、网卡队列、RPS、RFS、irqbalance、hrcount、softirqs、中断亲和性、ethtool队列配置 | `references/performance/irq-balance.md` |
| `fs-latency` | 文件系统IO延迟 | 文件IO慢、fsync慢、page cache、ext4慢、t-ops | `references/performance/fs-latency.md` |
| `file-io-trace` | 进程文件IO追踪 | 进程IO高、iowait、IO追踪、fd泄漏 | `references/performance/file-io-trace.md` |
| `oom-killer` | OOM 事件诊断 | OOM、进程被杀、内存不足、oom-killer、cgroup内存限制、Memory cgroup out of memory、page allocation failure、kswapd、Swap耗尽、oom_score_adj、多进程内存竞争 | `references/memory/oom-killer.md` |

## 内存（1 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `memory-leak` | 内存泄漏诊断 | 内存泄漏、RSS增长、内存不释放、memleak、VmRSS持续增长、VmAnon增长、Private_Dirty、Pss、SUnreclaim、内核slab泄漏、文件描述符泄漏、fd_count增长、内存碎片、Java堆泄漏、jmap、OOM预测 | `references/memory/memory-leak.md` |

## 系统管理（5 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `system-log` | 系统日志分析 | 日志、journalctl、dmesg、报错、日志清理 | `references/system/system-log.md` |
| `service-status` | 服务状态管理 | 服务起不来、systemctl、启动失败、开机自启 | `references/system/service-status.md` |
| `time-sync` | 时间同步管理 | 时间不对、NTP、chrony、时区、时间同步 | `references/system/time-sync.md` |
| `package-version` | 软件包版本管理 | 软件版本、安全更新、升级、rpm、dnf | `references/system/package-version.md` |
| `repo-source` | 软件源配置 | yum源、dnf源、pip源、npm源、换源、镜像 | `references/system/repo-source.md` |

## 安全（2 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `security-baseline` | 等保三级安全加固 | 等保、安全加固、安全基线、GB/T 22239、身份鉴别、访问控制、安全审计、入侵防范、SELinux加固、SSH加固、密码策略、账户管理、防火墙配置、check模式、harden模式、R1高风险、安全检查 | `references/security/security-baseline.md` |
| `tencentos-cve-query` | CVE 漏洞查询 | CVE、漏洞、安全公告、TSSA、OCSA、OpenCloudOS安全公告、批量CVE查询、TS2漏洞、TS3漏洞、TS4漏洞、OC7漏洞、OC8漏洞、OC9漏洞 | `references/security/tencentos-cve-query.md` |

## 故障恢复（1 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `kdump-check` | kdump 配置与排查 | kdump、vmcore、crashkernel、panic、crash | `references/recovery/kdump-check.md` |

## 产品文档（1 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `tencentos-docs` | 产品文档实时查询 | TencentOS版本、维护周期、CentOS迁移、产品特性 | `references/docs/tencentos-docs.md` |
