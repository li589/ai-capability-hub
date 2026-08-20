---
name: tencentos-expert
display_name: TencentOS Server 全栈运维诊断
author: kaeyahuang@tencent.com
level: product
description: >
  TencentOS Server 全栈运维诊断，根据用户的自然语言描述，自动识别需要的能力接口，查询能力实现，使用具体能力解决客户问题。
  覆盖磁盘空间/分区/文件系统/LVM/健康检测、网络连通性/丢包/延迟排查、CPU火焰图/系统调用热点/调度延迟/中断均衡/文件IO延迟/进程IO追踪分析、内存泄漏/OOM诊断、系统日志/服务管理/时间同步/软件包/软件源管理、kdump配置与故障排查、等保三级安全基线检查与加固、CVE漏洞查询、产品文档实时查询。共24项能力，渐进式按需加载。
  触发词：磁盘满、磁盘空间、分区、格式化、挂载、fstab、LVM、扩容、SMART、坏块、ping不通、端口不通、DNS、丢包、延迟、网络慢、RTT、火焰图、CPU热点、perf、系统调用、调度延迟、中断不均衡、软中断、文件IO慢、fsync慢、page cache、IO延迟、进程IO、iotop、内存泄漏、OOM、进程被杀、内存不足、日志、journalctl、dmesg、服务启动失败、systemctl、时间不对、NTP、chrony、时区、yum源、dnf、pip源、npm源、软件包版本、安全更新、CVE、kdump、vmcore、crashkernel、等保、安全加固、安全基线、TencentOS文档、版本信息、CentOS迁移。
version: 2.1.0
---

# TencentOS Server 全栈运维诊断

覆盖 24 项运维能力，按需加载，不撑爆上下文。

## 适用边界（命中即拒绝，不要继续加载子文档）

本 skill **仅服务于 TencentOS Server 运维诊断**。请求与运维无关时立即拒绝，**禁止**进入下方任何子文档：

| 不属于本 skill 的请求 | 处理 |
|---------------------|------|
| Web/小程序/移动端开发、UI/前端优化 | 拒绝 |
| 网站建设、CMS、内容编辑、SEO | 拒绝 |
| 业务代码、数据建模、应用 SQL 设计 | 拒绝 |
| AI 模型训练、数据分析（GPU 故障诊断除外） | 拒绝 |
| 通用编程教学、产品需求讨论 | 拒绝 |

**拒绝模板**：「该请求不在 TencentOS Server 运维诊断范围内，本 skill 覆盖磁盘/网络/性能/内存/系统/安全/CVE 共 24 项运维能力。建议切换通用对话模式，或重新描述具体的运维故障现象（如磁盘满、CPU 跑满、网络延迟高等）。」

完整边界列表见 `guides/workflow.md` Step 1。

## 凭证保护（强制约束）

> 🔐 用户提供 SSH 密码或私钥时：
>
> AI **绝不**：读取 `~/.ssh/id_*` 文件、复述用户粘贴的密码或密钥、把凭证写入脚本/日志/commit。
> AI **必须**：登录目标主机由用户自己完成（本地 ssh-agent 或 ssh 命令），AI 只生成 `ssh user@host` 模板；用户粘贴明文凭证时立即提醒已泄漏并指引轮换（重新生成密钥并替换 `authorized_keys`）。

## 快速入口

触发本 Skill 后，按以下顺序加载指导文档：

1. **工作流程** → `Read: guides/workflow.md`
2. **能力索引** → `Read: guides/capability-index.md`
3. **场景路由**（按现象匹配模块）→ `Read: guides/scenario-routing.md`
4. **文档导航**（查找子文档路径）→ `Read: guides/doc-map.md`

## 加载策略

- **首次触发**：加载 `guides/workflow.md`（含依赖安装和诊断步骤）+ `guides/capability-index.md`（模块匹配）
- **匹配到模块后**：加载对应的 `references/<module-id>.md`
- **按现象路由**：参考 `guides/scenario-routing.md`
- **查子文档**：参考 `guides/doc-map.md`

## 重要注意事项

1. **不要一次性加载所有 references/**——只加载用户问题匹配的 1~3 个模块文档
2. **脚本路径替换规则**：文档中出现 `<SKILL_DIR>` 的地方，替换为本 skill 目录的实际绝对路径（即 `SKILL.md` 所在目录）
3. **perf-prof 优先**：性能分析类模块优先使用 perf-prof，不可用时按文档中的降级方案使用 perf 原生命令
4. **索引中找不到匹配时**：可用 Grep 在 references/ 目录中搜索用户描述的关键词
5. **多个模块关联时**：按主要问题加载主模块，相关模块的文档路径在每个模块末尾的"相关技能"中列出

## 目录结构

```
├── SKILL.md              ← 入口（本文件）
├── guides/               ← Skill 工作指导（工作流、索引、路由）
│   ├── workflow.md
│   ├── capability-index.md
│   ├── scenario-routing.md
│   └── doc-map.md
├── references/           ← 具体诊断步骤文档（按业务域分子目录）
│   ├── _common/          ← 跨模块共享指引
│   ├── disk/             ← 5 文件：空间/分区/文件系统/LVM/健康
│   ├── network/          ← 8 文件：连通性/延迟/丢包/FAQ
│   ├── performance/      ← 16 文件：火焰图/调度/中断/IO 等
│   ├── memory/           ← 6 文件：内存泄漏/OOM
│   ├── system/           ← 5 文件：日志/服务/时间/包/源
│   ├── security/         ← 5 文件：等保基线/CVE 查询
│   ├── recovery/         ← 1 文件：kdump
│   └── docs/             ← 1 文件：产品文档
└── scripts/              ← 诊断脚本
    ├── cve_xml_server.py
    ├── parse_oom_events.py
    └── ...
```
