---
name: workbuddy-migration-assistant
version: 1.2.0
display_name: "WorkBuddy 迁移助手"
allowed-tools: Read,Write,Bash
description: >
  WorkBuddy 国内版跨机器资产迁移助手。在更换电脑时，将旧机器的全部个人资产（skills、memory、conversations、automations、
  sessions、MCP/connectors 配置、IDENTITY/SOUL/USER 等）无缝迁移到新机器。导出为两包分离架构（主包 + 产物包），
  导入默认合并不覆盖，自动处理路径映射（支持 --auto-map 零配置跨平台）和冲突检测。触发词：WorkBuddy 迁移、资产迁移、换电脑搬家、迁移助手、搬家工具、数据迁移。
---

# WorkBuddy 迁移助手

将一台旧电脑上的 WorkBuddy 国内版（`~/.workbuddy/`）全部个人资产，完整迁移到新电脑。两包分离、路径自动映射、冲突可见可控。

> **本文档只保留入口分派与关键约束**。命令参数、流程图、冲突规则、已知问题等细节按需加载 `references/`（见文末索引）。

## 快速开始

```bash
# 导出（旧电脑）
python scripts/export.py --source auto --output ~/Desktop/wb.zip

# 导入（新电脑，自动跨平台路径映射）
python scripts/import.py --package ~/Desktop/wb.zip --auto-map --dry-run
python scripts/import.py --package ~/Desktop/wb.zip --auto-map

# 检视迁移包
python scripts/info.py --package ~/Desktop/wb.zip
```

> `python` 优先使用 WorkBuddy managed Python，也可用系统 Python 3.8+。

## 适用场景

| 场景 | 说明 |
|------|------|
| **换电脑** | 旧 Mac → 新 Mac、Mac → Linux、Windows → Mac 等 |
| **备份恢复** | 导出全量备份，必要时在新机上恢复 |
| **多机同步** | 主工作机 → 备用机，保持两机资产一致 |

**不适用**：同机国内版↔海外版迁移（请使用 `WorkBuddy 资产迁移` 技能）。

## 资产范围全景

迁移覆盖 WorkBuddy 个人数据的**全部**资产类型：

```
~/.workbuddy/
├── workbuddy.db              → DB 表（sessions/automations/workspaces）
├── skills/                   → 所有已安装技能包
├── memory/                   → {uid}_memory.md 记忆文件
├── MEMORY.md                 → 根级长期记忆（5.3.3+，双轨并存）
├── settings.json             → 应用设置
├── mcp.json                  → MCP 连接器配置
├── models.json               → 模型配置
├── IDENTITY.md               → 人格身份定义
├── SOUL.md                   → 灵魂设定
├── USER.md                   → 用户信息
├── connectors/{uid}/         → 连接器状态与凭证
├── connectors/skills/        → 连接器技能包（connector-*，5.3.11+）
├── automation-backups/       → 自动化配置备份
├── brain/                    → 研究计划数据
├── todos/  plans/  deliverables/ → 任务/计划/交付物数据
├── experts/                  → 自定义专家（含专家团），4.24.0+
├── plugins/                  → 仅 known_marketplaces.json + 自建专家包(my-experts)
├── projects/                 → 所有历史对话记录（.jsonl + meta.json）
└── ~/WorkBuddy/              → 对话工作目录（代码生成产物、下载文件等）
                                  ⚡ 仅通过 --with-workspaces 打包
```

### 绝对不迁移的

| 资产 | 原因 |
|------|------|
| `binaries/`、`git-bash/` | 平台相关二进制，目标机自行构建 |
| `logs/`、`audit-log/` | 运行时日志，无迁移意义 |
| `app/cache/`、`skills-marketplace/` | 缓存，首次启动自动重建 |
| `blobs/`、`cache/`、`backup/`、`shell-snapshots/` | 二进制/运行时缓存，目标端自动重建 |
| `connectors-marketplace/`、`plugin-marketplace-state-new/`、`pending-telemetry/` | 运行时状态，目标端自动重建 |
| `edge-sync-mapping.db` | 端云同步映射，跨机后客户端重建 |
| `session_usage` 表 | 运行时用量统计 |
| `automation_delivery_outbox` / `__workbuddy_drizzle_migrations` 表 | 投递队列（含敏感 payload）/ ORM 内部记录 |
| 认证 token（`CodeBuddyExtension/Data/auth/`） | 绑定机器，跨机后失效 |
| `projects_repair_backup_*` | 客户端升级/修复自动生成的快照，每份数百 MB~GB，无迁移价值 |

## 两包分离架构

导出产出两个独立 zip，职责完全解耦：

| 包 | 文件名 | 内容 | 典型大小 | 必传 |
|----|--------|------|----------|------|
| **主包** | `wb-migration-{timestamp}.zip` | DB、Skills、Configs、Identity、Memory、Connectors、Conversations | 10-100 MB | ✅ 必须 |
| **产物包** | `wb-migration-{timestamp}-workspaces.zip` | 所有对话目录下的文件资料（代码、报告、图片、下载等） | 100 MB - 50 GB | ❌ 可选 |

**设计意图**：
- 主包小而精，可用网盘/微信快速传输
- 产物包独立传输（U盘、局域网、大文件分享），下载失败不影响主包导入
- 用户可不传产物包，仅让对话历史在新机上"可回顾但无文件"，后续按需补传

## 关键约束（每次执行必须遵守）

1. **导入前必须退出 WorkBuddy 客户端**（SQLite 写锁冲突会导致导入失败）
2. **必须排除当前迁移会话**（防止目标端出现僵尸对话）——优先级：环境变量 → 源端 DB 最新 session → `--exclude-session-id`
3. **默认合并不覆盖**（目标端已有资产保留，仅补充缺失），除非显式 `--overwrite`
4. **跨平台必做路径映射**：推荐 `--auto-map`（零配置），或手工 `--path-map` + `--target-os`
5. **导入后必须重启**：DB、models.json、settings.json 等需要重启才能生效
6. **导入前先用 dry-run 预览**：导出看计划、导入看冲突报告，确认后再正式执行
7. **推荐跨机排除凭证**：`--no-credentials`（OAuth token 跨机大概率失效），目标端到连接器面板重新授权

## Agent 调用入口分派

skill 自身不提问，由 host agent 交互。按意图关键词直接分发，不做多余预扫描：

| 用户意图 | 关键词 | 直接进入 |
|----------|--------|----------|
| 导出/备份 | 导出、备份、打包、export | 步骤 0（资产扫描）→ 流程 A |
| 导入/恢复 | 导入、恢复、import | 流程 B |
| 检视包内容 | 查看包、包里有什么、info | 流程 C |
| 未明确 | 迁移、搬家、换电脑（无方向） | 步骤 0（资产扫描）后再问 |

> 完整分派流程、步骤 0 资产扫描、流程 A/B/C：见 `references/flows.md`

## 内部参考（按需加载）

| 文件 | 何时加载 |
|------|----------|
| `references/index.md` | 需要细节时先查此索引 |
| `references/commands.md` | 构造 export/import/info 命令时 |
| `references/flows.md` | 导出/导入/检视执行时 |
| `references/conflict-pathmap.md` | 跨机路径重写、冲突处理、解析产物包时 |
| `references/known-issues.md` | 排查故障、准备回滚、核对版本时 |
| `references/asset_inventory.md` | 资产扫描/导出时（白名单数据驱动） |
| `references/workspace_excludes.md` | 产物包打包时（排除规则） |
