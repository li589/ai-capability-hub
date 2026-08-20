# TencentOS Expert Skills

TencentOS Server 全栈运维诊断技能，帮助运维人员快速定位和解决系统问题。

## 📋 能力列表（References）

原 24 个独立 Skills 已归一为单一 Skill，各能力以 `references/` 文档形式按需加载。

> 📁 自 `ab0387b` 起 references/ 已按业务域分到 9 个子目录（disk/ network/ performance/ memory/ system/ security/ recovery/ docs/ _common/）。

### 磁盘与存储（5 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| disk-space | [disk/disk-space.md](references/disk/disk-space.md) | 磁盘空间分析 |
| disk-partition | [disk/disk-partition.md](references/disk/disk-partition.md) | 磁盘分区管理 |
| disk-filesystem | [disk/disk-filesystem.md](references/disk/disk-filesystem.md) | 文件系统管理 |
| disk-lvm | [disk/disk-lvm.md](references/disk/disk-lvm.md) | LVM 逻辑卷管理 |
| disk-health | [disk/disk-health.md](references/disk/disk-health.md) | 磁盘健康检测 |

### 网络诊断（2 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| network-check | [network/network-check.md](references/network/network-check.md) | 网络连通性诊断 |
| network-latency | [network/network-latency.md](references/network/network-latency.md) | 丢包与延迟排查 |

### 性能分析（6 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| cpu-flamegraph | [performance/cpu-flamegraph.md](references/performance/cpu-flamegraph.md) | CPU 火焰图分析 |
| syscall-hotspot | [performance/syscall-hotspot.md](references/performance/syscall-hotspot.md) | 系统调用热点 |
| sched-latency | [performance/sched-latency.md](references/performance/sched-latency.md) | 调度延迟分析 |
| irq-balance | [performance/irq-balance.md](references/performance/irq-balance.md) | 中断均衡分析 |
| fs-latency | [performance/fs-latency.md](references/performance/fs-latency.md) | 文件系统 I/O 延迟 |
| file-io-trace | [performance/file-io-trace.md](references/performance/file-io-trace.md) | 进程 I/O 追踪 |

### 内存诊断（2 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| memory-leak | [memory/memory-leak.md](references/memory/memory-leak.md) | 内存泄漏诊断 |
| oom-killer | [memory/oom-killer.md](references/memory/oom-killer.md) | OOM 事件分析 |

### 系统管理（5 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| system-log | [system/system-log.md](references/system/system-log.md) | 系统日志分析 |
| service-status | [system/service-status.md](references/system/service-status.md) | 服务状态管理 |
| time-sync | [system/time-sync.md](references/system/time-sync.md) | 时间同步管理 |
| package-version | [system/package-version.md](references/system/package-version.md) | 软件包版本查询 |
| repo-source | [system/repo-source.md](references/system/repo-source.md) | 软件源配置 |

### 安全合规（2 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| security-baseline | [security/security-baseline.md](references/security/security-baseline.md) | 等保安全基线检查 |
| tencentos-cve-query | [security/tencentos-cve-query.md](references/security/tencentos-cve-query.md) | CVE 漏洞查询 |

### 故障恢复（1 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| kdump-check | [recovery/kdump-check.md](references/recovery/kdump-check.md) | kdump 配置与排查 |

### 文档查询（1 项）

| 能力 | 文档 | 说明 |
|------|------|------|
| tencentos-docs | [docs/tencentos-docs.md](references/docs/tencentos-docs.md) | TencentOS 文档查询 |

### 通用约束（_common/，所有模块共享）

| 文档 | 说明 |
|------|------|
| [_common/common-instructions.md](references/_common/common-instructions.md) | 跨模块通用约束 |

## 🏗️ 项目结构

```
tencentos-expert-skills/
├── README.md                    # 项目说明
├── CONTRIBUTING.md              # 贡献指南
├── LICENSE                      # GPL-2.0-only 许可证
├── SKILL.md                     # 主 Skill 文件（路由 + 安全规则）
├── skill.yaml                   # 治理契约（命令清单 / 触发关键词 / 引用清单）
├── guides/                      # SKILL.md 拆分后的子文档
│   ├── capability-index.md
│   ├── doc-map.md
│   ├── scenario-routing.md
│   └── workflow.md
├── references/                  # 详细诊断文档（按业务域分子目录）
│   ├── _common/                 # 通用约束、凭证规范
│   ├── disk/
│   ├── network/
│   ├── performance/
│   ├── memory/
│   ├── system/
│   ├── security/
│   ├── recovery/
│   └── docs/
├── scripts/                     # 诊断脚本
│   ├── collect_and_analyze.sh
│   ├── cve_xml_server.py
│   ├── parse_oom_events.py
│   ├── parse_memory_leak.py
│   └── ...
├── tests/                       # 测试用例
│   └── test.sh
└── docs/                        # 开发文档
    ├── developer-handbook.md
    ├── skill-development-guide.md
    ├── best-practices.md
    └── architecture.md
```

### 渐进式加载设计

```
Layer 0: 安全规则 + 版本差异表（始终加载）
         ↓
Layer 1: 能力索引 + 关键词匹配（~200 行，始终加载）
         ↓
Layer 2: references/ 详细文档（按需加载）
```

## 🔧 使用方式

### 安装为用户级 Skill（全局可用）

```bash
# 用户级 skills 目录
mkdir -p ~/.codebuddy/skills/tencentos-expert

# 复制主文件
cp SKILL.md ~/.codebuddy/skills/tencentos-expert/

# 复制引用文档和脚本
cp -r references/ ~/.codebuddy/skills/tencentos-expert/
cp -r scripts/ ~/.codebuddy/skills/tencentos-expert/
```

### 验证安装

在 CodeBuddy 中验证：

1. 打开 CodeBuddy 的 **Craft 模式**
2. 描述问题，如 *"帮我查看磁盘空间使用情况"*
3. CodeBuddy 会自动匹配并加载对应能力进行诊断

## 🚀 开发指南

### 添加新能力

1. 在 `references/` 目录创建新的文档文件（如 `references/<capability-name>.md`）
2. 在 `SKILL.md` 的能力索引表和文档路径映射中添加新条目
3. 如需脚本支持，在 `scripts/` 目录添加脚本
4. 运行测试：`bash tests/test.sh`

### 文档规范

- [开发者手册](docs/developer-handbook.md) - **推荐首先阅读**
- [Skill 开发指南](docs/skill-development-guide.md)
- [最佳实践](docs/best-practices.md)
- [架构设计](docs/architecture.md)

## 📚 参考资料

### TencentOS 官方文档

- [TencentOS Server 产品文档](https://cloud.tencent.com/document/product/1397/72777)

### TencentOS 版本说明

| 版本 | 包管理器 | 说明 |
|-----|---------|------|
| TencentOS 2 | yum | 长期支持版本 |
| TencentOS 3 | dnf | 长期支持版本 |
| TencentOS 4 | dnf | 独立版本 |

## 🔄 CI/CD

本项目使用 [Gitee Go](https://gitee.com/help/articles/4295) 进行持续集成：

- 提交 PR 时自动运行格式验证
- 自动运行测试用例
- 配置文件：`.gitee/pipelines/skill-validation.yml`

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程。

### 贡献步骤

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/add-new-capability`
3. 开发并测试
4. 提交变更：`git commit -m 'feat: 添加 xxx 诊断能力'`
5. 推送分支：`git push origin feature/add-new-capability`
6. 创建 Pull Request

## 📄 许可证

本项目采用 [GPL-2.0-only 许可证](LICENSE)。
