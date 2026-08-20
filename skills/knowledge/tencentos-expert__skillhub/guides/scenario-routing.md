# 场景快速导航（按问题现象路由）

当用户描述问题现象而非直接使用关键词时，用下表定位模块：

| 问题现象 | 首选模块 | 备选模块 |
|---------|---------|---------|
| 服务 CPU 跑满，不知道热点在哪 | `cpu-flamegraph` | — |
| Java/Python/Node.js 进程 CPU 高 | `cpu-flamegraph`（加载 guide 中 Java 案例）| — |
| 进程卡住不动，ps 看到 D 状态 | `cpu-flamegraph`（task-state 分析器）| `fs-latency` |
| 某个 CPU 的 %soft 持续偏高，其他 CPU 空闲 | `irq-balance` | — |
| 网络吞吐上不去，但整体 CPU 还有余量 | `irq-balance` | `network-latency` |
| ping 延迟正常，但应用响应慢 | `network-latency`（延迟域 Module 3/6）| `syscall-hotspot` |
| 网络延迟偶尔飙高，平时正常 | `network-latency`（偶发型 M-2）| `sched-latency` |
| TCP 重传率高 | `network-latency`（延迟域）| — |
| 连接跟踪表满，新连接被丢弃 | `network-latency`（丢包域 Module 6）| — |
| 进程响应变慢，但 CPU/内存不高 | `sched-latency` | `syscall-hotspot` |
| 容器 P99 延迟飙高，CPU 使用率正常 | `sched-latency`（cgroup CPU quota）| — |
| 某接口延迟 P99/max 偶发异常高 | `syscall-hotspot`（futex/epoll_wait 毛刺）| `sched-latency` |
| 可用内存持续下降，进程内存不释放 | `memory-leak` | — |
| Java 进程内存高，GC 后不回落 | `memory-leak`（JVM 堆泄漏场景）| `oom-killer` |
| 进程突然被杀，不知道为什么 | `oom-killer` | — |
| cgroup 内容器内 OOM，但宿主机内存充足 | `oom-killer`（cgroup OOM 场景）| — |
