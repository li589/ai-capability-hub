# 工作流程

## Step 0: 安装依赖工具（首次执行）

当触发本 skill 时，**首先执行以下命令安装所有诊断工具依赖**（`|| true` 确保部分失败不中断，安装后继续 Step 1）：

```bash
# 根据 TencentOS 版本选择包管理器：TS2=yum, TS3/TS4=dnf
if grep -qE '^VERSION_ID="2' /etc/os-release 2>/dev/null; then
    PKG_MGR=yum
else
    PKG_MGR=dnf
fi
# 性能分析工具
$PKG_MGR install -y perf-prof perf bpftrace sysstat || true
# 网络诊断工具
$PKG_MGR install -y tcpdump nettrace mtr ethtool iperf3 dropwatch || true
# 存储诊断工具
$PKG_MGR install -y smartmontools nvme-cli fio blktrace iotop || true
# 内存与调试工具
$PKG_MGR install -y valgrind bcc-tools gdb crash || true
# 系统调用与进程追踪
$PKG_MGR install -y strace lsof cflow || true
# 系统服务工具
$PKG_MGR install -y kexec-tools chrony || true
# 基础运行时依赖（脚本所需）
$PKG_MGR install -y python3 bc wget || true
# TencentOS 专用工具（fs-latency 模块核心依赖）
$PKG_MGR install -y tencentos-tools || true
# FlameGraph 工具集（CPU 火焰图模块需要 flamegraph.pl）
if ! command -v flamegraph.pl &>/dev/null; then
    git clone --depth 1 https://github.com/brendangregg/FlameGraph.git /opt/FlameGraph 2>/dev/null || true
    [ -d /opt/FlameGraph ] && ln -sf /opt/FlameGraph/flamegraph.pl /usr/local/bin/ && ln -sf /opt/FlameGraph/stackcollapse-perf.pl /usr/local/bin/ || true
fi
```

## Step 1: 理解用户意图

### 意图边界（必须先判断，命中即拒绝）

本 skill **仅服务于 TencentOS Server 运维诊断**（24 项能力：磁盘/网络/性能/内存/系统/安全/CVE 等）。请求与这 24 项能力无关时，**立即拒绝并退出**，不要尝试编排诊断步骤、不要调用任何工具。

| 非运维场景类别 | 典型关键词/特征 |
|---------------|----------------|
| 应用/Web 开发 | Web 前端、Vue/React、小程序、H5 页面、UI 优化、CSS、表单交互 |
| 网站建设/CMS | 网站搭建、WordPress、内容编辑、SEO、模板套用 |
| 业务代码/数据建模 | 业务逻辑、CRUD、ORM、SQL 表设计、API 接口设计 |
| 移动端开发 | iOS、Android、React Native、Flutter |
| 数据分析/AI 训练 | 模型训练、特征工程、数据清洗（注：GPU **故障诊断**仍属本 skill） |
| 通用咨询 | 编程语言教学、算法实现、产品需求讨论 |

**拒绝模板**（命中即输出此模板，禁止进入后续 Step）：

> 该请求不在 **TencentOS Server 运维诊断** 范围内。本 skill 覆盖磁盘/网络/性能/内存/系统管理/安全/CVE 共 24 项运维能力。建议：
> - 切换到通用对话模式处理开发/建站类需求；
> - 若有运维问题（如"磁盘满"、"CPU 跑满"、"网络延迟高"等），请直接描述故障现象。

### 模块匹配

确认请求属于运维诊断范围后，从 **能力索引表**（`guides/capability-index.md`）中匹配 1~3 个最相关的模块。

**匹配策略**：
1. 先根据关键词缩小到大类（如"磁盘满" → 磁盘与存储）
2. 再在子模块中定位具体能力（如"磁盘满" → `disk-space`）
3. 如果用户意图模糊，选择最可能的模块并在诊断中确认

## Step 2: 加载模块详细文档

找到目标模块后，**必须先读取对应的 references/ 文件**，获取完整的诊断步骤和命令参考。

**加载方式**：
```
Read: references/<module-id>.md
```

例如用户问"磁盘空间不足"：
```
Read: references/disk/disk-space.md
```

## Step 3: 执行诊断

按照模块文档中的诊断步骤执行。遵循以下原则：

### 危险操作管控 ⚠️ — Agent 禁止直接执行，仅提供命令文本由用户手动确认运行

| 类别 | 禁止直接执行的典型命令 |
|------|----------------------|
| 重启/关机/崩溃·磁盘破坏 | `reboot` `shutdown` `echo c>/proc/sysrq-trigger` · `mkfs.*` `dd if=/dev/zero` `wipefs` · `fdisk`/`parted`写操作 · `pvcreate` `lvremove` `vgremove` `pvremove` |
| 文件系统·引导·网络·GPU | `fsck` `e2fsck` `xfs_repair` · `grub2-mkconfig` `dracut -f` `update-initramfs` · `systemctl stop sshd` `iptables -F` · `nvidia-smi -r` `nvidia-smi -e 1` |
| 关键文件删除·属性变更 | `rm -rf /` `rm -rf /*` `rm -rf <目录>` `rm -f /etc/ld.so.preload` `rm -f /etc/cloud/cloud-init.disabled` · `chattr` |

### 失败重试与策略升级（禁止重复输出相同失败内容）

每个诊断步骤维护"失败计数"。**同一步骤连续失败时必须切换策略，不得重复同一指令或同一错误说明**。

| 失败次数 | 处理动作 |
|---------|---------|
| 第 1 次失败 | 检查输入与环境：参数格式、依赖工具是否安装（参考 Step 0）、文件/路径权限是否充足 |
| 第 2 次失败 | **切换降级方案**：如 `perf-prof` → `perf` 原生命令、`nettrace` → `tcpdump`+解析、专用脚本 → 通用命令组合；不得重复第 1 次的指令 |
| 第 3 次失败 | **停止重试**，向用户列出已尝试的方案与失败原因，建议提供更多信息或联系人工 |

### 云 API 权限不足时的降级路径

调用腾讯云 API（CVM、监控、CLB 等）失败时按以下优先级处理：

1. **明确告知最小权限**：列出该 API 名称与所需的最小只读权限（例：`cvm:DescribeInstances`、`monitor:GetMonitorData`），让用户在 CAM 中精确补齐。
2. **切换接入方式**：
   - **首选**：SSH 直连目标实例执行等价 shell 命令（实例侧诊断不依赖云 API）
   - **备选**：监控/日志类 API 之间互相替代（如 Cloud Monitor 不可用时改用实例 metrics）
   - **兜底**：给出腾讯云控制台的手动操作路径（菜单点击步骤）
3. **避免相同权限重试**：连续 2 次同类权限错误必须切换到上述方案，不得反复用同一 AK/SK 重试同一接口。

### 通用信息收集（首次连接时执行一次）

```bash
uname -r && cat /etc/os-release | head -3
uptime && free -h
df -h | head -10
```

### TencentOS 版本差异速查

| 操作 | TencentOS 2 | TencentOS 3/4 |
|------|-------------|---------------|
| 包管理器 | `yum` | `dnf`（`yum` 为别名） |
| 默认防火墙 | iptables | firewalld |
| 网络管理 | network-scripts | NetworkManager |
| NTP 服务 | ntpd | chronyd |
| 连接查看 | netstat | ss |
| 日志轮转 | cron 触发 | systemd timer |
| cgroup | v1 | v1(TS3) / v2(TS4) |
| 性能工具安装 | `yum install` | `dnf install` |

## Step 4: 输出结果

按照模块文档中定义的报告格式输出诊断结论和建议。
