# 冲突处理规则、路径映射与产物包格式

> 何时加载：跨机器路径重写、冲突处理、解析产物包时。

## 冲突处理规则（每类资产详细策略）

导入端已有资产时的处理规则。默认模式（无 `--overwrite`）：

| 资产类别 | 处理策略 | 详细行为 |
|----------|----------|----------|
| **DB 表**（sessions/automations/...） | `INSERT OR IGNORE` | 同 id 的行保留目标端已有数据，只插入新行。跳过的行写入冲突报告 |
| **Skills 目录** | 按目录名 skip | 源端与目标端同名目录（如 `skill_xxx/`）跳过整个目录，不覆盖任何文件 |
| **Memory 文件** | 追加合并 | 目标端已有 `{uid}_memory.md` 时，源内容以分隔符追加到文件末尾，不删除原文 |
| **settings.json** | 浅合并，目标优先 | JSON 顶层 key：目标端已有 key 保留目标值，仅添加源端有而目标端无的 key |
| **mcp.json** | 按 server 名合并 | `mcpServers` 字典按 server name 去重，同名 server 保留目标端配置 |
| **models.json** | 按 model id 合并 | `models` 数组中按 `id` 字段去重，同 id 保留目标端设置 |
| **IDENTITY.md / SOUL.md / USER.md** | 旁路导入 | 目标端已存在时，源文件写入 `<name>.imported.md`，不污染现有身份设定 |
| **projects/*.jsonl** | 按 session id skip | 同 session id 的对话文件保留目标端已有版本 |
| **.credentials.json** | 推荐排除 | 跨机器 OAuth token 大概率失效，建议导入后用 `--no-credentials` 排除 |
| **connectors/*/connector-states.v3.json** | merge by key | 按 connector name 合并状态 |

### 冲突检测报告格式（dry-run 输出）

导入 dry-run 时输出 JSON 冲突报告，包含三类条目：

```json
{
  "conflicts": {
    "merged": [
      {"asset": "skills/", "item": "skill_2053082698440450048", "action": "skip", "reason": "目标端已存在同名目录"},
      {"asset": "memory/", "item": "15810235093_memory.md", "action": "append", "reason": "目标端已有，源内容将追加到末尾"}
    ],
    "skipped": [
      {"asset": "sessions", "item": "session_id=abc123", "action": "skip_db", "reason": "INSERT OR IGNORE: 目标端已有此行"}
    ],
    "new": [
      {"asset": "skills/", "item": "skill_new_package", "action": "create", "reason": "目标端不存在，将新增"},
      {"asset": "sessions", "item": "52 new sessions", "action": "insert", "reason": "目标端无此对话记录"}
    ]
  },
  "path_rewrites": [
    {"table": "sessions", "count": 128, "sample": "/home/alice/projects → /Users/alice/projects"}
  ],
  "dir_creates": ["/Users/alice/projects/foo", "/Users/alice/projects/bar"],
  "restart_required": true,
  "warnings": []
}
```

## 路径映射逻辑

跨机器（不同操作系统、不同用户名、不同目录布局）时，所有存储绝对路径的位置必须重写。

### 映射规则

```bash
--path-map /home/alice=/Users/alice --path-map /mnt/data=/Volumes/Data
```

- **最长前缀匹配**：路径 `/home/alice/projects/foo` 匹配第一条规则
- **多条规则**：存在多条时依次尝试，首次匹配即停
- **无匹配**：路径保持原样（写入 warnings 列表）

### 重写目标（自动执行）

| 位置 | 字段 | 示例 |
|------|------|------|
| `sessions` 表 | `cwd` 列 | `/home/alice/project` → `/Users/alice/project` |
| `workspaces` 表 | `path` 列（主键） | 同上 |
| `automations` 表 | `cwds` 列（JSON array） | 逐元素重写 |
| `automation_runs` 表 | `source_cwd` 列 | 同上 |
| `projects/<dir>/meta.json` | `cwd` 字段 | 递归 JSON 路径更新 |
| `projects/<dir>/` | 目录名本身 | `compressWorkspacePath(cwd)` 重编码 → rename 目录 |
| `settings.json` | `defaultWorkspaceRoot` | 重写默认工作区根路径 |
| `mcp.json` | `mcpServers.*.command`/`cwd` | stdio MCP 的命令和目录重写 |
| `connectors/*/mcp.json` | 同上 | 同上 |

### 不重写的（人工关注）

内存文件（memory/*.md）、对话正文（projects/*.jsonl）、prompt 文本中的内嵌路径 —— 这些是自然语言内容，不自动替换。导入报告中 `suspicious_path_refs` 段列出可疑位置供用户人工修改。

## 自动路径映射（--auto-map）

跨平台迁移时最大的摩擦是需要手工计算 `--path-map` 规则。`--auto-map` 解决这个问题：

```bash
# 旧：手工指定每个路径映射
python scripts/import.py --package wb.zip \
    --path-map /Users/alice=C:\Users\Alice \
    --path-map /home/alice=C:\Users\Alice \
    --target-os win32

# 新：自动检测，零配置
python scripts/import.py --package wb.zip --auto-map
```

**工作原理**：
1. 从迁移包的 `manifest.json` 读取源平台信息（OS、username、home）
2. 检测目标平台信息
3. 自动推导 home 前缀映射规则
4. 同时处理 user_id 合并（源 uid → 目标 uid）
5. 应用范围：sessions.cwd / workspaces.path / automations.cwds / projects 目录 / settings.json 等

**目标端 DB 为空时**：使用 `--target-user-id <uuid>` 显式指定目标 user_id。

## 恢复后自动校验

每次 `import.py` 完成后自动执行 5 项数据完整性检查：

| 检查项 | 检测内容 | 问题时的建议 |
|--------|----------|-------------|
| sessions | cwd 字段是否为空 | 通常为源端历史问题，可忽略 |
| workspaces | 工作区目录是否在磁盘存在 | 跨机器迁移常见，如不需可忽略 |
| projects | 对话目录是否匹配 session | 路径映射不完整，检查 `--path-map` |
| tasks | 是否存在孤儿任务组 | 可手动清理 `tasks/<session_id>/` |
| user_id | 是否多 uid 并存 | 使用 `--uid-map` 统一映射 |

使用 `--no-validate` 跳过此步骤。

## 产物包文件清单格式

产物包 `wb-migration-*-workspaces.zip` 内部结构：

```
wb-migration-20250615-0910-workspaces.zip
├── MANIFEST.json              ← 文件清单与元信息
├── 2025-06-15-09-10-42/       ← session directory（compressWorkspacePath 编码）
│   ├── report.md
│   ├── data.csv
│   └── output/
│       └── chart.png
├── project-bar/
│   ├── src/
│   │   └── main.py
│   └── README.md
└── ...
```

### MANIFEST.json 结构

```json
{
  "version": 1,
  "export_time": "2025-06-15T09:10:42+08:00",
  "source_root": "/home/alice/.workbuddy",
  "source_home": "/home/alice",
  "source_os": "linux",
  "source_hostname": "alice-thinkpad",
  "total_dirs": 23,
  "total_files": 1547,
  "total_size_bytes": 234567890,
  "excluded_patterns": ["node_modules/", ".git/", "dist/", "..."],
  "workspaces": [
    {
      "session_id": "abc123",
      "original_path": "/home/alice/projects/foo",
      "archive_path": "home-alice-projects-foo/",
      "file_count": 89,
      "size_bytes": 12345678,
      "top_level_dirs": ["src", "data", "output"]
    },
    {
      "session_id": "def456",
      "original_path": "/home/alice/WorkBuddy/2025-06-14-08-30-15",
      "archive_path": "2025-06-14-08-30-15/",
      "file_count": 12,
      "size_bytes": 456789
    }
  ],
  "caveats": {
    "env_files": 3,
    "private_keys": 2,
    "large_dirs_over_1gb": ["/home/alice/data/dataset"],
    "skipped_over_limit": []
  }
}
```
