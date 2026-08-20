# 架构设计

## 项目概述

TencentOS Expert Skills 是一个单 Skill 运维技能库（`tencentos-expert`），旨在帮助 AI 助手快速定位和解决 TencentOS Server 系统问题。

## 设计原则

### 1. 单 Skill 聚合设计

所有 22 项运维能力统一在一个 Skill 中管理：
- `SKILL.md` 作为唯一入口，包含能力索引和路由规则
- `references/` 目录存放各模块的详细诊断文档
- `scripts/` 目录存放辅助采集和分析脚本

### 2. 按需加载

AI 不会一次性加载所有文档，而是：
1. 先读取 `SKILL.md` 获取能力索引和路由规则
2. 根据用户问题匹配 1~3 个模块
3. 按需加载对应的 `references/<module-id>.md`

### 3. 优雅降级

脚本设计遵循优雅降级原则：
- 公共函数库找不到时使用内联 fallback
- 工具未安装时提示安装方法并继续可用部分
- `set -euo pipefail` + `|| true` 保证部分失败不中断整体

## 目录结构

```
tencentos-expert-skills/
├── SKILL.md                    # Skill 主入口（能力索引 + 路由规则 + Step 0~4）
├── README.md                   # 项目说明
├── CONTRIBUTING.md             # 贡献指南
├── references/                 # 模块详细诊断文档（48 个 .md 文件）
│   ├── disk-space.md           # 磁盘空间分析
│   ├── network-latency.md      # 网络延迟主入口
│   ├── cpu-flamegraph.md       # CPU 火焰图主流程
│   ├── common-instructions.md  # 通用诊断指令
│   ├── performance-common.md   # 性能分析通用知识
│   └── ...                     # 更多模块文档
├── scripts/                    # 辅助脚本
│   ├── common.sh               # 公共函数库（日志、颜色）
│   ├── output.sh               # 输出格式化
│   ├── collect_memory_leak.sh  # 内存泄漏数据采集
│   ├── collect_and_analyze.sh  # OOM 数据采集与分析
│   ├── cve_xml_server.py       # CVE XML 查询工具
│   ├── install-deps.sh         # 依赖安装脚本
│   └── ...                     # 更多脚本
├── docs/                       # 开发文档
│   ├── architecture.md         # 本文件
│   ├── developer-handbook.md   # 开发者手册
│   ├── skill-development-guide.md
│   └── best-practices.md
└── tests/                      # 评估与测试
    └── test.sh                 # 测试脚本
```

## 文件命名约定

### references/ 命名规则

- 主诊断文档：`<module-id>.md`（如 `disk-space.md`、`cpu-flamegraph.md`）
- 子流程文档：`<module-id>-<子功能>.md`（如 `cpu-flamegraph-perf.md`、`irq-balance-guide.md`）
- 工具参考：`<module-id>-<工具名>.md`（如 `network-nettrace.md`）
- FAQ/速查：`<module-id>-faq-<域>.md`（如 `network-faq-latency.md`）

### scripts/ 命名规则

- Shell 脚本：`<功能描述>.sh`（如 `collect_memory_leak.sh`）
- Python 脚本：`<功能描述>.py`（如 `parse_oom_events.py`）
- 公共库：`common.sh`、`output.sh`

## 开发流程

```
编写/修改 references/*.md 或 scripts/* → 本地验证 → PR Review → 合并
```

## 版本管理

- Skill 版本定义在 `SKILL.md` frontmatter 的 `version` 字段中
- 遵循语义化版本 (SemVer)
- 当前版本：2.0.0
