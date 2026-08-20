# 文档完整导航地图

所有 references/ 文件的职责和加载时机，确保每个文件都有明确的到达路径。

## 主诊断文档（直接由能力索引触发）

| 文件 | 职责 | 触发时机 |
|------|------|---------|
| `disk-space.md` | 磁盘空间分析与清理完整流程 | 磁盘满、inode 不足 |
| `disk-partition.md` | 分区创建/管理流程 | 新磁盘、分区扩容 |
| `disk-filesystem.md` | 文件系统格式化/挂载/修复 | mkfs、fsck、fstab 问题 |
| `disk-lvm.md` | LVM 逻辑卷操作 | 扩容、快照、pvresize |
| `disk-health.md` | SMART 检测、坏块扫描 | 磁盘故障预测 |
| `network-check.md` | 连通性逐层排查 | ping 不通、端口不通 |
| `network-latency.md` | 丢包与延迟诊断入口（含路由规则）| 丢包、延迟高 |
| `cpu-flamegraph.md` | 火焰图采样与生成主流程 | CPU 热点、火焰图 |
| `syscall-hotspot.md` | 系统调用采集与分析主流程 | 系统调用慢、strace |
| `sched-latency.md` | 调度延迟采集与分析主流程 | 调度延迟、唤醒延迟 |
| `irq-balance.md` | 中断均衡诊断主流程 | 软中断不均、NET_RX 集中 |
| `fs-latency.md` | 文件系统 IO 延迟诊断 | fsync 慢、ext4 慢 |
| `file-io-trace.md` | 进程 IO 追踪 | 进程 IO 高、fd 泄漏 |
| `oom-killer.md` | OOM 事件分析主流程 | 进程被杀、内存不足 |
| `memory-leak.md` | 内存泄漏诊断主流程 | RSS 增长、内存不释放 |
| `system-log.md` | 系统日志分析 | dmesg 报错、journalctl |
| `service-status.md` | 服务状态与启动排查 | systemctl 失败 |
| `time-sync.md` | 时间同步配置与排查 | 时间不对、NTP |
| `package-version.md` | 软件包版本与更新管理 | 升级、安全更新 |
| `repo-source.md` | 软件源配置与切换 | yum 源、换源 |
| `security-baseline.md` | 等保三级检查与加固主流程 | 等保、安全加固 |
| `tencentos-cve-query.md` | CVE 查询主流程（脚本调用）| CVE、漏洞查询 |
| `kdump-check.md` | kdump 配置与排查 | kdump、vmcore |
| `tencentos-docs.md` | 产品文档查询 | TencentOS 版本、迁移 |

## 子流程/工具参考文档（由主文档内部导航触发）

| 文件 | 职责 | 触发时机 |
|------|------|---------|
| `network-packet-loss.md` | 丢包域完整诊断流程（Module 1~7）| `network-latency.md` 路由到丢包场景 |
| `network-latency-diag.md` | 延迟域完整诊断流程（Module 1~6）| `network-latency.md` 路由到延迟场景 |
| `network-nettrace.md` | nettrace 工具完整用法参考 | 需要 nettrace 丢包监控/故障诊断/延迟分析时 |
| `network-faq-latency.md` | 延迟域 FAQ + 操作参考 + 命令速查 | 延迟诊断中需要 FAQ 解答或配置参考时 |
| `network-faq-packet-loss.md` | 丢包域 FAQ + 操作参考 + 命令速查 | 丢包诊断中需要 FAQ 解答或配置参考时 |
| `cpu-flamegraph-guide.md` | 火焰图使用指南（含 Java/D状态案例）| 需要用户友好的操作指引，或遇到 Java/D状态场景 |
| `cpu-flamegraph-perf.md` | perf 原生三步生成法（高级用户）| perf-prof 不可用时的降级方案 |
| `cpu-flamegraph-examples.md` | 常用触发场景示例 Prompt | 用户描述的场景不易直接匹配关键词时参考 |
| `flamegraph-install.md` | FlameGraph 工具安装指南 | 用户需要安装 flamegraph.pl 时 |
| `irq-balance-guide.md` | 中断均衡六步排查指南（含案例）| 需要用户友好的操作指引 |
| `irq-balance-perf.md` | perf-prof 中断分析命令参考 | 执行 hrcount/multi-trace/profile 命令时 |
| `irq-balance-examples.md` | 中断均衡场景示例 | 场景匹配参考 |
| `sched-latency-guide.md` | 调度延迟使用指南（含案例）| 需要用户友好的操作指引，或 cgroup 限流场景 |
| `syscall-hotspot-guide.md` | 系统调用分析使用指南（含案例）| 需要用户友好的操作指引，或 epoll/futex 场景 |
| `memory-leak-indicators.md` | 内存泄漏判定指标知识库 | 分析 VmRSS/VmAnon/SUnreclaim 等指标时 |
| `memory-leak-guide.md` | 内存泄漏排查指南 | 需要用户友好的操作指引 |
| `oom-kernel-patterns.md` | OOM 日志特征库与根因分类 | 解析 dmesg OOM 日志时 |
| `oom-metrics-guide.md` | OOM 诊断指标说明 | 分析内存指标与 OOM 关联时 |
| `security-baseline-guide.md` | 等保加固概述（37项/双模式/风险分级）| 用户需了解加固范围或使用方式时 |
| `security-checklist.md` | 安全检查项清单 | check 模式执行时比对参考 |
| `common-instructions.md` | 通用诊断指令与输出规范 | 多个模块共用的通用指令参考 |
| `performance-common.md` | 性能分析通用知识 | 性能类模块共用的基础概念和工具 |
| `network-latency-guide.md` | 网络延迟排查使用指南 | 需要用户友好的网络延迟操作指引时 |
| `tencentos-cve-guide.md` | CVE 查询使用指南 | 需要用户友好的 CVE 查询操作指引时 |

## 文档路径映射（完整）

| 模块 ID | references/ 路径 | scripts/ 路径 |
|---------|-----------------|---------------|
| disk-space | `references/disk/disk-space.md` | — |
| disk-partition | `references/disk/disk-partition.md` | — |
| disk-filesystem | `references/disk/disk-filesystem.md` | — |
| disk-lvm | `references/disk/disk-lvm.md` | — |
| disk-health | `references/disk/disk-health.md` | — |
| network-check | `references/network/network-check.md` | — |
| network-latency | `references/network/network-latency.md` + `references/network/network-packet-loss.md` + `references/network/network-latency-diag.md` + `references/network/network-nettrace.md` + `references/network/network-faq-latency.md` + `references/network/network-faq-packet-loss.md` + `references/network/network-latency-guide.md` | `scripts/network-latency-monitor.sh` |
| cpu-flamegraph | `references/performance/cpu-flamegraph.md` + `references/performance/cpu-flamegraph-perf.md` + `references/performance/cpu-flamegraph-guide.md` + `references/performance/cpu-flamegraph-examples.md` + `references/performance/flamegraph-install.md` | — |
| syscall-hotspot | `references/performance/syscall-hotspot.md` + `references/performance/syscall-hotspot-guide.md` | — |
| sched-latency | `references/performance/sched-latency.md` + `references/performance/sched-latency-guide.md` | `scripts/sched-latency-monitor.sh` |
| irq-balance | `references/performance/irq-balance.md` + `references/performance/irq-balance-perf.md` + `references/performance/irq-balance-guide.md` + `references/performance/irq-balance-examples.md` | — |
| fs-latency | `references/performance/fs-latency.md` | `scripts/fs-latency-collect.sh`, `scripts/install-deps.sh` |
| file-io-trace | `references/performance/file-io-trace.md` | `scripts/file-io-trace.sh` |
| oom-killer | `references/memory/oom-killer.md` + `references/memory/oom-kernel-patterns.md` + `references/memory/oom-metrics-guide.md` | `scripts/collect_and_analyze.sh`, `scripts/parse_oom_events.py` |
| memory-leak | `references/memory/memory-leak.md` + `references/memory/memory-leak-indicators.md` + `references/memory/memory-leak-guide.md` | `scripts/collect_memory_leak.sh`, `scripts/parse_memory_leak.py` |
| system-log | `references/system/system-log.md` | — |
| service-status | `references/system/service-status.md` | — |
| time-sync | `references/system/time-sync.md` | — |
| package-version | `references/system/package-version.md` | — |
| repo-source | `references/system/repo-source.md` | — |
| security-baseline | `references/security/security-baseline.md` + `references/security/security-checklist.md` + `references/security/security-baseline-guide.md` | `scripts/tos_security_harden.sh` |
| tencentos-cve-query | `references/security/tencentos-cve-query.md` + `references/security/tencentos-cve-guide.md` | `scripts/cve_xml_server.py` |
| kdump-check | `references/recovery/kdump-check.md` | — |
| tencentos-docs | `references/docs/tencentos-docs.md` | — |
| （通用） | `references/_common/common-instructions.md` + `references/performance/performance-common.md` | `scripts/common.sh`, `scripts/output.sh` |
