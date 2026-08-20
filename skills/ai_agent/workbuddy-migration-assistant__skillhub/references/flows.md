# 导出 / 导入 / 检视流程

> 何时加载：执行导出、导入、检视时。

## 导出流程

```
用户触发迁移请求
        │
        ▼
┌──────────────────┐
│ 1. 资产扫描      │  检测 ~/.workbuddy/ 资产
│    统计各资产量   │  skills / sessions / memory / configs
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. 向用户确认    │  展示资产清单 + 询问范围
│    - 是否带对话？ │  - 对话记录（可能很大）
│    - 是否带文件？ │  - 工作区产物（--with-workspaces）
│    - 排除凭证？   │  - .credentials.json（--no-credentials）
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. dry-run 预览  │  输出 JSON 计划：
│                  │  - 主包大小预估
│                  │  - 产物包大小预估（如有）
│                  │  - 敏感物提示（.env/私钥/.git/大文件）
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. 用户确认后    │  正式导出 → 产生 zip(s)
│    正式导出      │  告知路径、大小、下一步
└──────────────────┘
```

**关键行为**
- 主包必含：DB（sessions/automations/workspaces 表）、技能包目录、内存文件、配置文件、身份文件、连接器状态、对话记录（projects/*.jsonl）
- 产物包可选：仅 `--with-workspaces` 时产出
- 当前对话排除：自动跳过正在执行迁移的 session（防止目标端出现僵尸对话）
- 默认排除大型垃圾：`node_modules/`、`.git/`、`dist/`、`__pycache__/`、`.venv/`、`*.sqlite`、`*.log` 等
- 敏感物提示：dry-run 显式列出 .env、私钥、secrets 文件数量，用户决定是否手动排除

### 跳过执行中的会话

迁移时将自动获当前 session ID（按优先级）：
1. 环境变量 `WORKBUDDY_CURRENT_SESSION_ID` 或 `CODEBUDDY_SESSION_ID`
2. 源端 DB 查询：`SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1`
3. 用户通过 `--exclude-session-id <id>` 显式传入

## 导入流程

```
用户拿到迁移包
        │
        ▼
┌──────────────────┐
│ 1. 检测目标端     │  检测新机 ~/.workbuddy/ 状态
│                  │  列出已有资产、确认是空端还是已有数据
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. 确认路径映射   │  跨 OS/用户名时：
│                  │  --path-map /home/old=/Users/new
│                  │  --target-os darwin
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. dry-run 预览  │  输出冲突检测报告：
│                  │  - 哪些资产将合并
│                  │  - 哪些因目标已有而跳过
│                  │  - 路径重写预览
│                  │  - 目录创建计划
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. 用户确认后    │  正式导入
│    正式导入      │  输出结果报告 + 重启提示
└──────────────────┘
```

**关键行为**
- 导入前必须退出 WorkBuddy 客户端（SQLite 写锁冲突会导致导入失败）
- 默认合并不覆盖：目标端已有资产保留，仅补充缺失
- 路径自动重写：DB 内 `sessions.cwd`、`workspaces.path`、`automations.cwds`、`projects/*.meta.json` 中的旧路径全部按 `--path-map` 替换
- 目录自动创建：导入后在磁盘上 `mkdir -p` 创建缺失的工作目录，确保历史对话可打开
- 导入后必须重启：DB 修改、models.json、settings.json 等需要重启才能生效

## Agent 调用流程

skill 自身不提问，由调用它的 host agent 负责跟用户交互。

### 入口分派（首先执行）

根据用户意图关键词直接分发到对应流程，**不做多余的预扫描**：

| 用户意图 | 关键词 | 直接进入 |
|----------|--------|----------|
| 导出/备份 | 导出、备份、打包、export | 步骤 0（资产扫描）→ 流程 A |
| 导入/恢复 | 导入、恢复、import | 流程 B |
| 检视包内容 | 查看包、包里有什么、info | 流程 C |
| 未明确 | 迁移、搬家、换电脑（无方向） | 步骤 0（资产扫描）后再问 |

### 步骤 0：资产扫描（导出、未明确意图时执行）

**在向用户提任何问题之前**，先静默完成以下扫描：

1. **检测端情况**：检查 `~/.workbuddy/` 是否存在且符合 WorkBuddy root 特征（含 `workbuddy.db` 或 `settings.json` 或 `skills/` 或 `memory/`）

2. **扫描以下资产**（快速 shell 命令统计）：
   - **Skills**：`ls <root>/skills/ | wc -l` 个技能包
   - **Memory**：`ls <root>/memory/` 文件列表及大小
   - **对话记录**：`ls <root>/projects/ | wc -l` 个 session
   - **配置文件**：settings.json、mcp.json、models.json 是否存在
   - **身份文件**：IDENTITY.md、SOUL.md、USER.md 是否存在
   - **工作区文件**：列出对话目录数量及总大小（可能较大，可仅列数量+预估大小）
   - **v0.3.0 新增资产**：tasks/、teams/、sessions/、local_storage/、traces/、file-history/、experts/ 是否存在及大小

2.5 **检测多 uid**：
   ```bash
   <python> -c "import sqlite3; conn=sqlite3.connect('<db>'); cur=conn.execute('SELECT DISTINCT user_id FROM sessions'); print([r[0] for r in cur.fetchall()])"
   ```

3. **展示资产概览**（组织成清单呈现给用户）：
   ```
   📦 WorkBuddy 国内版（~/.workbuddy/）
   ├── Skills：200 个技能包
   ├── Memory：1 个文件，共 42 KB
   ├── 对话记录：343 个 session
   ├── 配置文件：settings.json ✓  mcp.json ✓  models.json ✓
   ├── 身份文件：IDENTITY.md ✓  SOUL.md ✓  USER.md ✓
   ├── 工作区文件：33 个目录，共约 1.2 GB
   └── 新增资产：experts/ N个 tasks/ 4组 teams/ 1组 sessions/ 2个
   ```

4. **展示完资产概览后，一次性问清楚**：
   - **迁移范围**：是否包含对话记录、工作区文件、凭证
   - **如有多 uid**：是否一并导出

### 流程 A：导出（备份或跨机器）

1. **环境预检**：确认 Python >= 3.8
2. 根据用户选择构造 export 命令参数：
   - 不要对话 → `--no-conversations`；要工作区文件 → `--with-workspaces`
   - 不带凭证 → `--no-credentials`（推荐跨机启用）
   - **排除当前对话**：获取方式 → 环境变量 `WORKBUDDY_CURRENT_SESSION_ID` 或 `CODEBUDDY_SESSION_ID`，或查询源端 DB `SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1`，通过 `--exclude-session-id <id>` 传入
3. dry-run 预览 → 解析 JSON，**重点呈现**：
   - 主包预估大小
   - `caveats` 里的敏感物清单（.env、私钥数等）——**默认会被带走，agent 必须主动告知**
4. 用户确认后正式导出 → 输出 zip 路径与大小

### 流程 B：导入

1. **环境预检**：确认 Python >= 3.8
2. **确认迁移包**：路径 + 是否有产物包
3. **先用 `info.py` 检视**（推荐）：运行 `python scripts/info.py --package <path>` 展示包内容概览
4. **确认路径映射**：
   - 同平台 → 无需映射
   - 跨平台 → 推荐 `--auto-map`（零配置），或手工 `--path-map`
5. dry-run 预览：运行 `import.py --dry-run`，呈现冲突检测报告
6. 用户确认后正式导入：
   - **导入前必须退出 WorkBuddy 客户端**
   - 推荐：`import.py --package wb.zip --auto-map`
   - 即使没有 `--workspaces-package`，也会自动创建缺失的工作区目录
7. 导入后自动校验（v0.2.0），输出问题清单

### 流程 C：检视迁移包

```bash
python scripts/info.py --package <path>
```

直接运行展示包内容，无需预检。agent 可主动建议用户在导入前先用此命令了解包内容。

### 排除当前对话（重要）

执行迁移时，正在运行的 session **必须排除**，防止目标端出现僵尸对话。

获取当前 session ID（按优先级）：
1. 环境变量 `WORKBUDDY_CURRENT_SESSION_ID` 或 `CODEBUDDY_SESSION_ID`
2. 源端 DB：`SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1`
3. 通过 `--exclude-session-id <id>` 传给导出脚本

> `export.py` 也会自动读取环境变量，但显式传入更可靠。

### 重启提示

导入完成后 stdout 自动打印哪些需要重启、哪些已热加载。

## 完成后的操作

导入完成后，根据冲突检测报告：

1. **重启 WorkBuddy 客户端**（涉及 DB、models.json、settings.json、SOUL.md 等）
2. **检查 `.imported.md` 文件**（IDENTITY.md、SOUL.md、USER.md 如有冲突，人工合并）
3. **重新授权 MCP 连接器**（OAuth token 跨机器失效，需到 connector 面板逐一重新授权）
4. **清理备份**：`.bak-<ts>` 备份文件不自动删除，确认无误后自行清理
