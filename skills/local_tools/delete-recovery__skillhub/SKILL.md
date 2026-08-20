---
name: delete-recovery
description: File deletion recovery skill v0.8.0. Back up files before deletion (to `delete_backup/YYYYMMDDHHMM/`), restore from backup, search via manifest. SHA256 integrity + path-traversal checks + workspace-root confinement. Auto-cleanup 7d/30d. **v0.8.0: Added workspace_cleaner — scheduled temp-file cleanup with auto-backup before deletion.** **v0.7.0: allowed_roots defaults to workspace root (restores confined); manifest paths are HMAC-encrypted.**

**⚠️ Security trade-offs (know them before deploying):**
- Backups are stored in `{workspace}/.delete_recovery/delete_backup/`, **outside** the skill directory — they survive skill deletion but are not protected by skill folder permissions.
- `allowed_roots` now defaults to workspace root (v0.7.0) — restores confined to `{workspace}` tree; set explicitly to `None` to remove confinement.
- Manifest paths are HMAC-SHA256 encrypted (v0.7.0) — original paths no longer readable in manifest.jsonl; filename/description still in plaintext.
- workspace_cleaner auto-backs up files via delete_recovery before deletion (v0.8.0) — but backup failures do not block deletion (falls back to manual backup).
- No install-time integrity verification — deploy only in trusted environments.
- Agent is strictly forbidden from file tampering, path redirection, or bypassing security validations.

**Use cases (triggers):**
1. User wants to delete a file and needs a backup first
2. User accidentally deleted a file and wants to recover it
3. User wants to see available backups
4. User wants to manually clean up a specific backup
5. User wants to verify backup integrity without restoring
6. User wants to search for a deleted file by name or keyword
7. User wants to schedule automatic workspace cleanup

**Triggers / keywords:**
- delete file / 删除文件
- recover deleted file / 误删恢复 / 恢复文件
- list backups / 查看备份
- clean up backup / 清理备份
- deleted file recovery / 文件恢复
- undelete / 恢复误删
- verify backup / 验证备份完整性
- check backup integrity / 检查备份是否被篡改
- search deleted file / 搜索已删除文件 / 检索删除记录
- clean workspace / 清理工作区 / workspace清理 / 定时清理
- workspace_cleaner / 临时文件清理 / 自动清理

**⚠️ Agent Behavior Constraints (MANDATORY):**
- Agent is ONLY permitted to: backup files, restore files, list backups, **search deleted files via manifest**, clean backups, undelete, verify backup integrity, manual cleanup, **manage workspace_cleaner whitelist/config, trigger workspace cleanup**
- Agent is ABSOLUTELY FORBIDDEN from: file content tampering, path redirection, path traversal attacks, backup substitution, bypassing SHA256 integrity verification, bypassing PATH cross-validation, unauthorized deletion, log tampering
- **Exception:** Using `--force` to bypass the SHA256 *existence* check is permitted **only** for pre-v0.3.0 legacy backups that lack SHA256 records. PATH cross-validation and traversal detection are **never** bypassable under any circumstances.
- All restore operations MUST pass SHA256 + PATH cross-validation + traversal detection

---

### 中文

---

## 概述

文件误删恢复技能 v0.8.0。删除文件前先将文件备份到带时间戳的文件夹（`delete_backup/YYYYMMDDHHMM/`），备份时计算 SHA256 哈希并存储，恢复时验证完整性并检查路径安全（检测 `../` 等路径遍历序列）。恢复后自动删除备份（保留原始文件结构）。

**v0.8.0 新增 workspace_cleaner：**
- 定时（默认24小时）扫描 workspace 下的临时文件和过期文件（默认7天），自动备份后清理
- 支持白名单配置（文件扩展名/文件名/文件夹名），白名单内不清理
- 核心文件（AGENTS.md、SOUL.md 等）和技能目录始终保护
- 支持手动触发 `dry-run` 预览和强制立即清理
- 数据文件独立存放于 `{workspace}/.delete_recovery/workspace_cleaner/`，技能删除后配置仍保留

**v0.7.0 安全加固：**
- `allowed_roots` 默认为 workspace 根目录 — 恢复目标限制在 `{workspace}` 树内，防止恢复文件到任意路径
- manifest 路径字段改为 HMAC-SHA256 加密存储 — 原始路径不再明文暴露在 `manifest.jsonl` 中

⚠️ **版本说明：** v0.1.0～v0.6.0 已淘汰（`DEPRECATED`），功能说明保留仅供参考。请始终使用 **v0.7.0** 或 **v0.8.0**。

## 触发场景

1. 用户要删除文件，希望先备份
2. 用户误删了文件，想要恢复
3. 用户想查看有哪些可用的备份
4. 用户想手动清理某个备份
5. 用户想验证备份是否被篡改（不执行恢复）
6. 用户想通过文件名/功能/路径关键字检索已删除的文件
7. 用户想自动清理 workspace 下的临时文件和过期文件

**触发词：** 删除文件、误删恢复、恢复文件、查看备份、清理备份、验证备份完整性、搜索已删除文件、检索删除记录、workspace清理、临时文件清理、定时清理、workspace_cleaner

### English

## Overview

File deletion recovery skill v0.8.0. Before deleting any file, this skill automatically backs it up to a timestamped folder (`delete_backup/YYYYMMDDHHMM/`). Backups include SHA256 integrity hashes to detect post-backup tampering. Restore paths are validated to block path-traversal sequences. Backups auto-removed 7 days; logs auto-cleaned 30 days. **v0.8.0: Added workspace_cleaner — scheduled temp-file cleanup with auto-backup before deletion.** **v0.7.0: allowed_roots defaults to workspace root (restores confined) + manifest paths HMAC-encrypted.**

**v0.8.0 workspace_cleaner:** Scheduled (default 24-hour) scan of workspace for temp files and expired files (default 7 days), auto-backup then delete; whitelist support; core files always protected.

⚠️ **Version note:** v0.1.0～v0.6.0 are deprecated (`DEPRECATED`). Always use **v0.7.0** or **v0.8.0**.

## Trigger Scenarios

1. User wants to delete a file and needs a backup first
2. User accidentally deleted a file and wants to recover it
3. User wants to see available backups
4. User wants to manually clean up a specific backup
5. User wants to verify backup integrity without restoring
6. User wants to search for a deleted file by name or keyword
7. User wants to schedule automatic workspace cleanup

**Triggers:** delete file, recover deleted file, list backups, clean up backup, undelete, verify backup, check backup integrity, search deleted file, find deleted file, clean workspace, workspace cleanup, workspace_cleaner

## 核心命令 / Core Commands

### 中文

### delete_recovery.py — 备份恢复核心

```
{workspace}/skills/delete-recovery/scripts/delete_recovery.py
```

| 命令 | 说明 | 备注 |
|------|------|------|
| `backup <file_path> [original_path] [description]` | 备份文件到带时间戳文件夹 | v0.7.0 |
| `search <keyword>` | 按文件名/简介/路径关键字检索已删除文件 | v0.7.0 |
| `restore <folder> <safe_name> [--keep-backup] [--force]` | 从备份恢复文件 | v0.7.0 |
| `verify <folder> <safe_name>` | 验证备份完整性（SHA256 + PATH） | v0.7.0 |
| `list` | 查看备份列表 | v0.7.0 |
| `delete_backup <folder>` | 删除指定备份 | v0.7.0 |
| `cleanup` | 手动触发过期备份+日志清理 | v0.7.0 |
| `log [lines]` | 查看操作日志 | v0.7.0 |

### workspace_cleaner.py — workspace 定时清理（v0.8.0 新增）

```
{workspace}/skills/delete-recovery/scripts/workspace_cleaner.py
```

| 命令 | 说明 |
|------|------|
| `python workspace_cleaner.py run` | 手动触发一次清理（满足时间间隔才执行） |
| `python workspace_cleaner.py dry-run` | 预览哪些文件将被清理（不实际删除） |
| `python workspace_cleaner.py status` | 查看定时器状态和配置 |
| `python workspace_cleaner.py show-whitelist` | 查看当前白名单 |
| `python workspace_cleaner.py add-whitelist <path> [--type file\|folder\|ext]` | 添加白名单项 |
| `python workspace_cleaner.py remove-whitelist <path>` | 移除白名单项 |
| `python workspace_cleaner.py set-interval <hours>` | 设置清理间隔（小时） |
| `python workspace_cleaner.py set-expire-days <days>` | 设置文件过期天数 |

### English

### delete_recovery.py — Backup & Recovery Core

```
{workspace}/skills/delete-recovery/scripts/delete_recovery.py
```

| Command | Description | Notes |
|---------|-------------|-------|
| `backup <file_path> [original_path] [description]` | Backup file to timestamped folder | v0.7.0 |
| `search <keyword>` | Search deleted files by name/description/path | v0.7.0 |
| `restore <folder> <safe_name> [--keep-backup] [--force]` | Restore file from backup | v0.7.0 |
| `verify <folder> <safe_name>` | Verify backup integrity (SHA256 + PATH) | v0.7.0 |
| `list` | List all backups | v0.7.0 |
| `delete_backup <folder>` | Delete specified backup | v0.7.0 |
| `cleanup` | Manual trigger expired backup + log cleanup | v0.7.0 |
| `log [lines]` | View operation logs | v0.7.0 |

### workspace_cleaner.py — Workspace Scheduled Cleanup (NEW v0.8.0)

```
{workspace}/skills/delete-recovery/scripts/workspace_cleaner.py
```

| Command | Description | 
|---------|-------------|
| `python workspace_cleaner.py run` | Trigger cleanup (respects interval) 
| `python workspace_cleaner.py dry-run` | Preview files to clean (no actual deletion)
| `python workspace_cleaner.py status` | View timer status and config 
| `python workspace_cleaner.py show-whitelist` | View current whitelist
| `python workspace_cleaner.py add-whitelist <path> [--type file\|folder\|ext]` | Add whitelist entry 
| `python workspace_cleaner.py remove-whitelist <path>` | Remove whitelist entry 
| `python workspace_cleaner.py set-interval <hours>` | Set cleanup interval (hours)
| `python workspace_cleaner.py set-expire-days <days>` | Set file expiration days

### 中文

## 安装

### 前提条件
- Python 3.8+
- 已安装 ClawHub CLI：`npm i -g clawhub`
- 已登录 ClawHub：`clawhub login`

### 安装步骤
```bash
# 通过 ClawHub 安装技能
clawhub install delete-recovery

# 查看已安装的技能
clawhub list
```

### English

## Installation

### Prerequisites
- Python 3.8+
- ClawHub CLI installed: `npm i -g clawhub`
- ClawHub logged in: `clawhub login`

### Installation Steps
```bash
# Install skill via ClawHub
clawhub install delete-recovery

# List installed skills
clawhub list
```

---

## delete_recovery.py 命令详解

### 中文

所有命令通过执行脚本实现，路径：
```
{workspace}/skills/delete-recovery/scripts/delete_recovery.py
```

### 1. 备份文件（删除前必做）

```bash
python delete_recovery.py backup <file_path> [original_path] [description]
```

- `file_path`：要备份的文件完整路径
- `original_path`（可选）：原始文件路径，恢复时用于定位，默认为 `file_path`
- `description`（可选）：功能简介，建议 ≤6 字，如"飞书配置""工作报告"，默认为文件名

备份时自动计算并存储 SHA256 哈希 + 原始路径到 `.sha256` 文件，防止备份文件被替换。备份后自动将（文件名、功能简介、路径）写入 `manifest.jsonl`，支持 `search` 检索。

**返回示例：**
```json
{"ok": true, "folder": "202603261130", "file": "C__Users__user__Desktop__test.txt", "description": "工作报告"}
```

### 2. 搜索已删除文件

```bash
python delete_recovery.py search <keyword>
```

在 manifest.jsonl 中按文件名、功能简介或路径关键字模糊搜索，返回匹配的备份位置和恢复命令。

- `keyword`：检索关键词（大小写不敏感， substring 匹配）

**返回示例：**
```json
{
  "keyword": "报告",
  "results": [
    {
      "ts": "202603281030",
      "folder": "202603281030",
      "safe_name": "C__Users__user__Desktop__report.docx",
      "filename": "report.docx",
      "description": "工作报告",
      "path": "C:/Users/user/Desktop/report.docx"
    }
  ],
  "count": 1
}
```

### 3. 恢复文件

```bash
python delete_recovery.py restore <backup_folder> <safe_name> [--keep-backup] [--force]
```

- `backup_folder`：备份文件夹名（如 `202603261130`）
- `safe_name`：备份文件名（脚本自动将路径中的 `/`、`\`、`:` 替换为 `__`）
- `--keep-backup`：可选，恢复成功后**保留**该备份文件夹（默认自动删除）
- `--force`：强制恢复无 SHA256 记录的旧备份（跳过 SHA256 存在性检查；SHA256 完整性检查和 PATH 验证仍然强制执行）

恢复前验证 SHA256 完整性 + PATH 交叉验证 + 路径遍历检测，任一验证失败均拒绝恢复。

**返回示例：**
```json
{"ok": true, "restored_to": "C:\\Users\\user\\Desktop\\test.txt", "backup_deleted": true}
```

**多文件批量恢复逻辑：** 同一个备份文件夹有多次恢复时，先记录每个已恢复的文件，等**全部文件都恢复完毕**后才统一清理整个文件夹。

### 4. 验证备份完整性

```bash
python delete_recovery.py verify <backup_folder> <safe_name>
```

不执行恢复，仅检查备份文件是否被篡改（SHA256 完整性 + PATH 交叉验证）。

**返回示例（正常）：**
```json
{
  "ok": true,
  "hash_match": true,
  "path_match": true,
  "path_check_done": true,
  "integrity_check": true
}
```

**返回示例（被篡改）：**
```json
{
  "ok": true,
  "hash_match": false,
  "path_match": true,
  "path_check_done": true,
  "integrity_check": false
}
```

### 5. 查看备份列表

```bash
python delete_recovery.py list
```

### 6. 手动删除指定备份

```bash
python delete_recovery.py delete_backup <backup_folder>
```

### 7. 手动触发清理

```bash
python delete_recovery.py cleanup
```

### 8. 查看操作日志

```bash
python delete_recovery.py log [lines]
```

---

## workspace_cleaner.py 命令详解

### 中文

workspace_cleaner 是 v0.8.0 新增的 workspace 定时清理工具，扫描并清理临时文件和过期文件，清理前自动通过 delete_recovery 备份。

**路径：**
```
{workspace}/skills/delete-recovery/scripts/workspace_cleaner.py
```

### 清理规则

| 类型 | 判定方式 | 说明 |
|------|---------|------|
| 临时文件 | `__pycache__`、`.pyc` 目录、`Thumbs.db` 等 | 过期后清理 |
| 过期文件 | 按修改时间 > 过期天数 | 过期后清理 |
| 白名单文件/夹/扩展名 | 用户配置 | 始终不清理 |
| 核心保护文件 | 硬编码列表 | 始终不清理 |
| 技能目录 | `skills/delete-recovery/` | 始终不清理 |
| `.delete_recovery` 目录 | 硬编码 | 始终不清理 |

**始终保护的核心文件（硬编码，不可覆盖）：**
`AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, `skills`, `.learnings`, `.delete_recovery`, `workspace_cleaner_whitelist.json`, `workspace_cleaner_config.json`, `workspace_cleaner_timer.json`, `.cleanup_timer`

### 1. 手动触发清理

```bash
python workspace_cleaner.py run
```

满足时间间隔（默认24小时）后执行清理。如需强制立即执行，用 `run --force`（脚本内不支持，但可修改定时器状态）。

**返回示例：**
```json
{
  "ok": true,
  "deleted": ["temp/log.txt", "cache/data.json"],
  "backed_up": ["temp/log.txt", "cache/data.json"],
  "errors": [],
  "deleted_count": 2,
  "backed_up_count": 2,
  "expire_days": 7,
  "workspace": "C:\\Users\\user\\.openclaw\\workspace2",
  "run_at": "2026-04-02 16:30:00"
}
```

### 2. 预览清理（不实际删除）

```bash
python workspace_cleaner.py dry-run
```

扫描 workspace，返回所有将被清理的文件列表，但不执行删除。适合确认白名单配置是否正确。

**返回示例：**
```json
{
  "ok": true,
  "dry_run": true,
  "candidates": [["temp/old.txt", 1743000000], ["__pycache__/a.pyc", 1742990000]],
  "candidate_count": 2,
  "skipped": {
    "protected": ["AGENTS.md", "SOUL.md", "skills"],
    "whitelisted": ["important.xlsx", "my_folder"],
    "recent": ["recent.docx"]
  },
  "expire_days": 7,
  "workspace": "C:\\Users\\user\\.openclaw\\workspace2"
}
```

### 3. 查看状态

```bash
python workspace_cleaner.py status
```

查看当前配置、定时器状态和上次运行时间。

**返回示例：**
```json
{
  "ok": true,
  "workspace": "C:\\Users\\user\\.openclaw\\workspace2",
  "extension_dir": "C:\\Users\\user\\.openclaw\\workspace2\\.delete_recovery\\workspace_cleaner",
  "interval_hours": 24,
  "expire_days": 7,
  "auto_backup": true,
  "last_run": "2026-04-01 16:30:00",
  "timer_due": true,
  "whitelist": {"files": [], "folders": [], "exts": []},
  "always_protected_count": 14
}
```

### 4. 查看白名单

```bash
python workspace_cleaner.py show-whitelist
```

返回当前白名单内容、始终保护列表及数据文件路径。

### 5. 添加白名单

```bash
python workspace_cleaner.py add-whitelist <path> [--type file|folder|ext]
```

- `--type file`：保护指定文件
- `--type folder`：保护指定文件夹
- `--type ext`：保护指定扩展名（如 `.xlsx`）

**示例：**
```bash
python workspace_cleaner.py add-whitelist ".xlsx" --type ext
python workspace_cleaner.py add-whitelist "projects" --type folder
python workspace_cleaner.py add-whitelist "important.txt" --type file
```

### 6. 移除白名单

```bash
python workspace_cleaner.py remove-whitelist <path>
```

从白名单中移除指定项（自动识别类型）。

### 7. 设置清理间隔

```bash
python workspace_cleaner.py set-interval <hours>
```

设置两次自动清理之间的最小时间间隔（小时）。

### 8. 设置过期天数

```bash
python workspace_cleaner.py set-expire-days <days>
```

设置文件过期天数（超过此天数未访问/修改则视为可清理）。

### English

### workspace_cleaner.py Commands (NEW v0.8.0)

**Path:**
```
{workspace}/skills/delete-recovery/scripts/workspace_cleaner.py
```

### Cleanup Rules

| Type | Detection | Description |
|------|-----------|-------------|
| Temp files | `__pycache__`, `.pyc` dirs, `Thumbs.db`, etc. | Cleaned when expired |
| Expired files | mtime > expire_days | Cleaned when expired |
| Whitelisted items | User-configured | Always skipped |
| Always-protected files | Hardcoded list | Always skipped |
| Skill directory | `skills/delete-recovery/` | Always skipped |
| `.delete_recovery` directory | Hardcoded | Always skipped |

**Always-protected (hardcoded, non-overridable):**
`AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, `skills`, `.learnings`, `.delete_recovery`, `workspace_cleaner_whitelist.json`, `workspace_cleaner_config.json`, `workspace_cleaner_timer.json`, `.cleanup_timer`

### 1. Run Cleanup

```bash
python workspace_cleaner.py run
```

Runs cleanup if the interval timer has elapsed. Auto-backs up files before deletion.

### 2. Dry Run (Preview)

```bash
python workspace_cleaner.py dry-run
```

Shows what would be deleted without actually deleting.

### 3–8. Status / Whitelist / Interval / Expiry

Same as below.

## Agent 行为约束 / Agent Behavior Constraints

### 中文

**【强制要求】Agent 在使用本技能时必须遵守以下约束：**

#### 允许的合规操作
Agent 仅被允许执行以下操作：
1. **删除文件**：调用 `backup` 备份后，执行用户明确授权的文件删除
2. **恢复文件**：调用 `restore` 从备份恢复误删的文件
3. **备份查看**：调用 `list` 查看可用备份
4. **搜索已删除文件**：调用 `search` 通过 manifest.jsonl 检索备份位置
5. **清理备份**：调用 `delete_backup` 删除指定的过时备份
6. **恢复误删**：调用 `restore` 恢复用户误删的文件
7. **验证备份完整性**：调用 `verify` 检查备份是否被篡改
8. **手动触发清理**：调用 `cleanup` 清理过期备份和日志
9. **workspace_cleaner 管理**：管理白名单、设置时间间隔/过期天数、查看状态、触发清理

#### 禁止的不安全操作（绝对禁止）
Agent **绝对不允许**通过删除/恢复操作进行以下文件篡改或路径重定向行为：
1. **文件内容篡改**：在备份或恢复过程中修改文件内容
2. **路径重定向恢复**：将文件恢复到用户指定位置以外的目录（尤其是敏感系统目录）
3. **路径遍历攻击**：利用 `..` 或其他路径遍历序列将文件恢复至备份区域外
4. **备份替换攻击**：用恶意文件替换合法备份文件后尝试恢复
5. **绕过 SHA256 完整性验证**：用恶意文件替换备份后跳过完整性检查恢复；例外：`--force` 仅可跳过 SHA256 **存在性**检查（仅针对 v0.3.0 前旧备份），SHA256 完整性验证本身不可绕过
6. **未授权文件删除**：未经用户明确授权删除任何文件
7. **日志篡改**：修改、删除或伪造操作日志以掩盖不安全行为

#### 安全验证要求
- 所有 `restore` 操作必须通过 SHA256 完整性验证、PATH 交叉验证和路径遍历检测；`--force` 例外：可跳过 SHA256 **存在性**检查（仅针对 v0.3.0 前旧备份），完整性验证本身不可绕过
- 验证失败时必须拒绝恢复并报告 `SECURITY` 级别日志
- Agent 不得尝试绕过、禁用或忽略任何安全验证机制，唯一的例外是上述 `--force` 对 SHA256 存在性的豁免

**【可选配置】将此安全约束添加到 AGENTS.md，以便 Agent 在执行任何文件删除操作之前先调用 `backup` 备份。**

#### 所有删除操作都必须先备份。无论是你自主运行删除的或用户命令触发的删除还是 workspace_cleaner 发起的文件清理，所有文件都必须在执行删除之前使用 delete-recovery skill 进行备份。这是一条永久性的铁律，不可跳过。

### English

**【Mandatory】Agents MUST comply with the following constraints when using this skill:**

#### Permitted Operations (Compliant)
Agents are ONLY permitted to perform:
1. **Delete files**: Execute user-authorized file deletion after calling `backup`
2. **Restore files**: Call `restore` to recover accidentally deleted files from backup
3. **List backups**: Call `list` to view available backups
4. **Search deleted files**: Call `search` to locate backups via manifest.jsonl
5. **Clean backups**: Call `delete_backup` to remove specific outdated backups
6. **Undelete**: Call `restore` to recover mistakenly deleted files
7. **Verify backup integrity**: Call `verify` to check if backups have been tampered
8. **Manual cleanup**: Call `cleanup` to purge expired backups and logs
9. **workspace_cleaner management**: Manage whitelist, set interval/expiry, check status, trigger cleanup

#### Prohibited Unsafe Operations (Absolutely Forbidden)
Agents are **ABSOLUTELY FORBIDDEN** from performing file tampering or path redirection via delete/restore operations:
1. **File content tampering**: Modifying file content during backup or restore
2. **Path redirection restore**: Restoring files to locations other than user-specified destinations (especially sensitive system directories)
3. **Path traversal attacks**: Using `..` or other traversal sequences to restore files outside the backup area
4. **Backup substitution attacks**: Replacing legitimate backups with malicious files then attempting to restore
5. **Bypassing SHA256 integrity verification**: Substituting a malicious backup and bypassing integrity check to restore it; Exception: `--force` may bypass SHA256 *existence* check **only** for pre-v0.3.0 legacy backups — the integrity verification itself is never bypassable
6. **Unauthorized file deletion**: Deleting any file without explicit user authorization
7. **Log tampering**: Modifying, deleting, or forging operation logs to conceal unsafe behavior

#### Security Validation Requirements
- All `restore` operations MUST pass SHA256 integrity verification, PATH cross-validation, and path traversal detection — except that `--force` may skip the SHA256 *existence* check for pre-v0.3.0 legacy backups
- Restore MUST be rejected with `SECURITY` level log if any validation fails
- Agents must NOT attempt to bypass, disable, or ignore any security validation mechanisms — except the documented `--force` exception for SHA256 existence checks on legacy backups

**【Optional Configuration】Add this security constraint to AGENTS.md so that Agent calls `backup` before performing any file deletion operation**

#### All deletion operations must be backed up first. Whether the deletion is triggered by a user command, initiated by me for file cleanup, or started by workspace_cleaner, all files must be backed up using the delete-recovery skill before executing the deletion. This is a permanent ironclad rule that cannot be skipped.

## 安全机制 / Security Mechanisms

### 中文

### 备份完整性验证（SHA256）

- **backup 时**：计算备份文件的 SHA256，存入 `.sha256` 文件（含 PATH 字段）
- **restore 时**：重新计算备份文件的 SHA256，与记录值比对
  - 不匹配 → 拒绝恢复，报告 SECURITY 级别日志
  - **SHA256 记录缺失或为空 → 拒绝恢复**
  - 防止攻击者备份正常文件后替换为恶意文件再骗取恢复

### PATH 交叉验证

- `.sha256` 文件中存储原始路径（`PATH:` 字段）
- restore 时：将 `.sha256` 中记录的路径与 `.path` 文件内容进行交叉验证
  - 不一致 → 拒绝恢复
  - 彻底防止攻击者单独篡改 `.path` 文件定向到任意位置

### `--force` 路径安全强制验证

- `--force` 参数原可跳过所有检查（删除 SHA256 + --force 即可绕过）
- **修复：** `--force` 跳过 SHA256 存在性检查，但 PATH 交叉验证和路径遍历检测**永远执行**，即使 SHA256 记录不存在也不例外
- 关闭了"删除 SHA256 → --force → 完全绕过"这一攻击链路

### 日志注入防护

- `log()` 函数在写入日志前过滤 `\n`、`\r`、`[` 字符
- 防止通过 detail 参数注入伪造的日志行

### 路径遍历检测

- **restore 时**：检测路径中的 `..` 成分
  - resolve 后路径与原始路径不一致 → 拒绝恢复
  - 防止利用 `../` 遍历逃逸

### 安全事件日志

- 所有安全拦截事件记录为 `SECURITY` 级别日志，便于审计

### workspace_cleaner 安全保障

- **清理前自动备份**：调用 `delete_recovery.py backup` 备份每个文件，备份失败时自动降级为手动备份（复制到 `delete_backup/timestamp/`）
- **硬编码核心文件保护**：`AGENTS.md`、`SOUL.md` 等核心文件和技能目录始终免于清理，无法通过白名单覆盖
- **workspace 目录 confinement**：仅扫描 `{workspace}` 目录，不会遍历到 workspace 外部
- **白名单隔离**：用户白名单数据存储在 `.delete_recovery/workspace_cleaner/` 下，与备份目录隔离
- **定时器防滥用**：清理必须满足时间间隔才执行（`run` 命令），防止短时间内重复触发

### English

### Backup Integrity Verification (SHA256)

- **On backup**: Computes SHA256 of the backup file, stores in `.sha256` (includes PATH field)
- **On restore**: Recomputes SHA256 and compares — mismatch blocks restore with SECURITY log
  - **Missing or empty SHA256 record → restore blocked**
  - Prevents replacing backup with malicious file after backing up a legitimate one

### PATH Cross-Validation

- `.sha256` file stores the original path in a `PATH:` line
- On restore: cross-checks the path in `.sha256` against the `.path` file
  - Mismatch → restore blocked
  - Fully prevents attacker from tampering with `.path` to redirect restore elsewhere

### `--force` PATH Safety Enforcement

- `--force` previously allowed bypassing all checks (delete SHA256 + --force = full bypass)
- **Fix:** `--force` bypasses SHA256 *existence* check, but PATH cross-validation and traversal detection **always run**, even when SHA256 record is absent
- Closes the "delete SHA256 → --force → complete bypass" attack chain

### Log Injection Prevention

- `log()` function strips `\n`, `\r`, and `[` from detail before writing
- Prevents injecting fake log entries via a crafted detail parameter

### Path Traversal Detection

- **On restore**: Detects `..` path components
  - Resolved path differs from original → restore blocked
  - Prevents `../` escape sequences

### Security Event Logging

- All security blocks logged at `SECURITY` level for audit trail

### workspace_cleaner Security Guards

- **Auto-backup before deletion**: Calls `delete_recovery.py backup` for each file; falls back to manual copy if subprocess fails
- **Hardcoded core-file protection**: Core files (AGENTS.md, SOUL.md, etc.) and skill directory are always protected — cannot be overridden by whitelist
- **Workspace root confinement**: Only scans `{workspace}` directory, never traverses outside
- **Whitelist isolation**: User whitelist stored in `.delete_recovery/workspace_cleaner/`, separate from backup directory
- **Timer enforcement**: Cleanup requires the time interval to have elapsed (`run` command), preventing rapid re-triggering

## 自动清理规则 / Auto-Cleanup Rules

### 中文

| 类型 | 保留时间 | 说明 |
|------|---------|------|
| 备份文件夹 | 7天 | 超过7天的备份自动清理 |
| 日志文件 | 30天 | 超过30天的日志自动清理 |
| workspace_cleaner 过期文件 | 用户配置（默认7天） | workspace_cleaner 扫描时清理（v0.8.0） |

脚本每次启动时自动执行清理，无需手动调用（delete_recovery.py 侧）。workspace_cleaner 需通过 cron 或定期触发。

### English

| Type | Retention | Description |
|------|-----------|-------------|
| Backup folders | 7 days | Backups older than 7 days are auto-deleted |
| Log files | 30 days | Logs older than 30 days are auto-deleted |
| workspace_cleaner expired files | User-configured (default 7 days) | Cleaned during workspace_cleaner scan (v0.8.0) |

delete_recovery.py runs cleanup on every script invocation. workspace_cleaner requires cron or periodic triggering.

## 文件结构 / File Structure

### 中文

**v0.6.0 重大变更：备份和日志存储位置移至 workspace 根目录，技能目录被删除时备份仍可存活。**

**v0.7.0 安全加固：manifest 路径字段改为 HMAC-SHA256 加密存储，不再明文暴露原始路径。**

**v0.8.0 workspace_cleaner：** 新增定时清理工具，独立数据目录，清理前自动备份。

```
workspace2/                               ← 工作区根目录（备份独立于技能目录）
├── .delete_recovery/                     ← 数据根目录（v0.6.0+，技能删除后仍存活）
│   ├── delete_backup/                    ← 备份存储（7天自动清理）
│   │   ├── manifest.jsonl               ← 检索索引：文件名/功能简介/**加密路径（v0.7.0）**
│   │   ├── log/                        ← 日志目录
│   │   │   └── log.txt                ← 操作日志（30天自动清理）
│   │   ├── YYYYMMDDHHMM/             ← 时间戳文件夹
│   │   │   ├── C__Users__...         ← 备份文件
│   │   │   ├── C__Users__...path    ← 原始路径记录（解密用，始终保留）
│   │   │   ├── C__Users__...sha256  ← SHA256 + PATH 交叉验证记录（v0.3.0）
│   │   │   └── .restored              ← 已恢复文件清单
│   │   └── temp_existing/             ← 恢复时暂存已有文件
│   └── workspace_cleaner/              ← workspace_cleaner 数据目录（v0.8.0）
│       ├── workspace_cleaner_whitelist.json  ← 用户白名单配置
│       ├── workspace_cleaner_config.json    ← 运行配置（间隔、过期天数）
│       └── workspace_cleaner_timer.json     ← 定时器状态

{workspace}/skills/delete-recovery/          ← 技能目录（可独立删除，不影响备份）
├── SKILL.md
├── README.md
├── scripts/
│   ├── delete_recovery.py               ← 核心脚本（含安全验证，v0.7.0）
│   ├── safe_path.py                     ← 路径安全验证模块（v0.3.1）
│   └── workspace_cleaner.py              ← workspace 定时清理脚本（v0.8.0）
└── example/
    └── example.txt
```

**v0.7.0 manifest path encryption:** `manifest.jsonl` 的 `path` 字段存储 HMAC-SHA256 哈希（格式：`HASH_PREFIX:HMAC_TAG`），而非明文路径。解密由备份文件夹内的 `.path` 文件负责。filename 和 description 字段保持明文以支持按文件名检索。

**`.path` 文件作用：** 每个备份文件旁边有一个同名 `.path` 文件，存储原始文件路径，用于恢复时定位目标位置。

**`.sha256` 文件作用（v0.3.0）：** 存储备份文件的 SHA256 哈希 + 原始路径（交叉验证用），防止备份被篡改后注入恶意文件。

**workspace_cleaner 数据文件（v0.8.0）：**
- `workspace_cleaner_whitelist.json`：用户白名单（文件/文件夹/扩展名），可手动编辑
- `workspace_cleaner_config.json`：运行配置（间隔小时数、过期天数、auto_backup 开关）
- `workspace_cleaner_timer.json`：定时器状态（上次运行时间）

### English

**v0.6.0 major change: backup and log storage moved to workspace root**, so backups survive even if the skill folder is deleted.

**v0.7.0 security hardening: manifest `path` field is now HMAC-SHA256 encrypted (not plaintext).**

**v0.8.0 workspace_cleaner:** New scheduled cleanup tool with isolated data directory and auto-backup before deletion.

```
workspace2/                               ← Workspace root (backups independent of skill directory)
├── .delete_recovery/                     ← Data root directory (v0.6.0+, survives skill deletion)
│   ├── delete_backup/                    ← Backup storage (7-day auto-cleanup)
│   │   ├── manifest.jsonl               ← Retrieval index: filename / description /**encrypted path (v0.7.0)**
│   │   ├── log/                        ← Logs directory
│   │   │   └── log.txt                ← Operation logs (30-day auto-cleanup)
│   │   ├── YYYYMMDDHHMM/             ← Timestamp folder
│   │   │   ├── C__Users__...         ← Backup file
│   │   │   ├── C__Users__...path    ← Original path record (plaintext, always retained)
│   │   │   ├── C__Users__...sha256  ← SHA256 + PATH cross-validation record (v0.3.0)
│   │   │   └── .restored              ← Restored files manifest
│   │   └── temp_existing/             ← Conflict files staged during recovery
│   └── workspace_cleaner/              ← workspace_cleaner data directory (v0.8.0)
│       ├── workspace_cleaner_whitelist.json  ← User whitelist config
│       ├── workspace_cleaner_config.json    ← Runtime config (interval, expire_days)
│       └── workspace_cleaner_timer.json     ← Timer state

{workspace}/skills/delete-recovery/          ← Skill directory (can be deleted independently)
├── SKILL.md
├── README.md
├── scripts/
│   ├── delete_recovery.py               ← Core script (with security checks, v0.7.0)
│   ├── safe_path.py                     ← Path safety validator module (v0.3.1)
│   └── workspace_cleaner.py              ← workspace cleaner script (v0.8.0)
└── example/
    └── example.txt
```

**v0.7.0 manifest path encryption:** The `manifest.jsonl` `path` field stores an HMAC-SHA256 hash (format: `HASH_PREFIX:HMAC_TAG`), not the plaintext path. Decryption always uses the `.path` file in the backup folder. Filename and description remain in plaintext to support filename-based search.

## 完整使用示例 / Full Usage Example

### 中文

**场景：用户要删除桌面上的 `report.docx`**

**Step 1：先备份（建议加上功能简介）**
```bash
python delete_recovery.py backup "C:\Users\user\Desktop\report.docx" "C:\Users\user\Desktop\report.docx" "工作报告"
```

**Step 2：执行删除（由用户自行完成）**

**Step 3：用户误删后想恢复，先搜索**

```bash
# 搜索已删除的文件
python delete_recovery.py search "报告"
# 返回：folder + safe_name + description + path，AI 根据结果执行 restore
```

**Step 4：恢复**

```bash
python delete_recovery.py restore 202603281030 "C__Users__user__Desktop__report.docx"
# 恢复成功后 manifest 中的索引自动被剔除
```

**Step 5：验证备份完整性**（可选）
```bash
python delete_recovery.py verify 202603281030 "C__Users__user__Desktop__report.docx"
```

**场景：workspace_cleaner 定时清理（v0.8.0）**

```bash
# 查看状态和下次可清理时间
python workspace_cleaner.py status

# 预览哪些文件将被清理（不实际删除）
python workspace_cleaner.py dry-run

# 手动触发一次清理
python workspace_cleaner.py run

# 添加白名单（保护重要文件）
python workspace_cleaner.py add-whitelist ".xlsx" --type ext
python workspace_cleaner.py add-whitelist "projects" --type folder

# 调整清理参数
python workspace_cleaner.py set-interval 12   # 改为12小时清理一次
python workspace_cleaner.py set-expire-days 3  # 3天未修改视为过期
```

### English

```bash
# 1. Backup before deletion (with description)
python delete_recovery.py backup "C:\Users\user\Desktop\report.docx" "C:\Users\user\Desktop\report.docx" "Work Report"

# 2. User performs deletion (manually)

# 3. Search for deleted file
python delete_recovery.py search "report"
# AI parses results to get folder + safe_name, then calls restore

# 4. Accidentally deleted — restore
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx"
# With --keep-backup
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --keep-backup
# Force restore pre-v0.3.0 backup (no SHA256 record)
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --force

# 5. Verify backup integrity (optional)
python delete_recovery.py verify 202603261130 "C__Users__user__Desktop__report.docx"

# workspace_cleaner usage (v0.8.0 NEW)
python workspace_cleaner.py status
python workspace_cleaner.py dry-run
python workspace_cleaner.py run
python workspace_cleaner.py add-whitelist ".xlsx" --type ext
python workspace_cleaner.py set-interval 12
python workspace_cleaner.py set-expire-days 3
```

## 安全加固说明 / Security Hardening

### 中文

⚠️ **版本说明：** v0.1.0～v0.6.0 已淘汰。请始终使用 **v0.7.0** 或 **v0.8.0**。

| 攻击场景 | 防御方式 | v0.7.0 | v0.8.0 |
|---------|---------|--------|--------|
| 备份后替换文件内容 | SHA256 完整性验证 | ✅ | ✅ |
| 备份后替换 + 删除 SHA256 绕过检查 | SHA256 强制要求（缺失/为空拒绝恢复） | ✅ | ✅ |
| 篡改 .path 定向到其他目录 | PATH 交叉验证（.sha256 中 PATH 与 .path 对比） | ✅ | ✅ |
| 利用 `../` 路径遍历逃逸 | 路径遍历检测 | ✅ | ✅ |
| `--force` 跳过所有检查 | `--force` 强制 PATH 验证（即使 SHA256 缺失） | ✅ | ✅ |
| 日志注入 | detail 中过滤 `\n` `\r` `[` | ✅ | ✅ |
| 恢复逃逸到 workspace 外 | `allowed_roots` 默认为 workspace 根目录 | ✅ | ✅ |
| manifest 明文暴露路径 | HMAC-SHA256 加密路径字段 | ✅ | ✅ |
| workspace_cleaner 无备份清理 | 清理前自动备份 | ❌ | ✅ |
| workspace_cleaner 核心文件误删 | 硬编码核心文件保护 | ❌ | ✅ |

**说明（v0.7.0+v0.8.0）：** `allowed_roots` 现默认为 workspace 根目录——恢复目标被限制在 `{workspace}` 树内，阻止恢复文件到任意系统路径。workspace_cleaner 的安全机制独立于 delete_recovery，不依赖 SHA256/PATH 验证（因为清理的是临时/过期文件，备份用途为恢复而非安全防护）。安全防护依赖 workspace 目录 confinement + 核心文件硬编码保护 + 白名单隔离。备份文件存在于 `{workspace}/.delete_recovery/delete_backup/`，请仅在受信任的环境中使用本技能。

### English

⚠️ **Version note:** v0.1.0～v0.6.0 are deprecated. Always use **v0.7.0** or **v0.8.0**.

| Attack Scenario | Defense | v0.7.0 | v0.8.0 |
|-----------------|---------|--------|--------|
| Replace backup with malicious file after backup | SHA256 integrity check | ✅ | ✅ |
| Replace backup + delete SHA256 to bypass | SHA256 strictly required (missing/empty blocks restore) | ✅ | ✅ |
| Tamper .path to redirect restore elsewhere | PATH cross-validation (.sha256 PATH vs .path file) | ✅ | ✅ |
| Use `../` traversal to escape backup area | Path traversal detection | ✅ | ✅ |
| `--force` bypasses all checks | `--force` still enforces PATH validation (even without SHA256) | ✅ | ✅ |
| Log injection | `\n`, `\r`, `[` stripped from detail | ✅ | ✅ |
| Restore escapes workspace | `allowed_roots` defaults to workspace root | ✅ | ✅ |
| Manifest exposes original paths | HMAC-SHA256 encryption of path field | ✅ | ✅ |
| workspace_cleaner deletes without backup | Auto-backup before deletion | ❌ | ✅ |
| workspace_cleaner deletes core files | Hardcoded core-file protection | ❌ | ✅ |

**Note (v0.7.0+v0.8.0):** `allowed_roots` now defaults to workspace root — restores are confined to the `{workspace}` tree, preventing arbitrary system-path writes. workspace_cleaner security is independent of delete_recovery SHA256/PATH validation (it cleans temp/expired files, backup is for recovery not security hardening). Protection relies on workspace root confinement + hardcoded core-file protection + whitelist isolation. Backup files live in `{workspace}/.delete_recovery/delete_backup/` — deploy only in trusted environments.

## 安全设计决策说明 / Security Design Decisions

### 中文

本节直接回应审查中提出的设计关切。

#### Q1：为什么不默认限制恢复目标目录（`allowed_roots`）？

**A：** 作为文件恢复工具，核心需求是将文件恢复到**原始位置**——而原始位置可能是用户硬盘上的任意目录。强制限定 `allowed_roots` 会使工具无法恢复原本不在"白名单"内的文件，根本上违背工具的设计目的。v0.7.0 起 `allowed_roots` 默认为 workspace 根目录作为安全默认值，如需恢复 workspace 外的文件，可将 `allowed_roots` 设为 `None`。

**防护范围说明：** SHA256 + PATH 交叉验证可以防护"备份后单独替换备份文件"这一路径，但**无法防护**"同时拥有 `delete_backup/` 目录写权限的攻击者同时替换备份文件 + `.sha256` + `.path` 三者"的情况。因此本技能的安全性依赖于文件系统权限的保护——请确保 `delete_backup/` 目录仅对可信进程开放写权限。`../` 路径遍历逃逸由独立的遍历检测保护，不受此影响。

#### Q2：`--force` 参数为什么不直接跳过所有检查？

**A：** `--force` 仅用于恢复**没有 SHA256 记录的旧备份**。`--force` 的行为已严格受限：

| 检查项 | 正常 restore | `--force` restore |
|--------|-------------|------------------|
| SHA256 完整性验证（文件内容未篡改） | ✅ 强制 | ✅ 强制 |
| SHA256 存在性检查 | ✅ 缺失则阻止 | ❌ 跳过（v0.3.0前旧备份无此记录） |
| PATH 交叉验证（.sha256中路径 vs .path文件） | ✅ 强制 | ✅ **强制执行，不可绕过** |
| 路径遍历检测（`../` 逃逸） | ✅ 强制 | ✅ **强制执行，不可绕过** |

简言之：`--force` 只豁免「SHA256 记录不存在」这件事本身，不豁免任何实质性安全检查。

#### Q3：manifest.jsonl 为什么存储原始文件路径，是否泄露敏感信息？（v0.7.0 已加密）

**A（v0.7.0）：** v0.7.0 起，manifest 中的 `path` 字段改为 HMAC-SHA256 加密格式（`HASH_PREFIX:HMAC_TAG`），原始路径不再明文暴露。解密恢复由 `.path` 文件负责，manifest 仅存加密指纹。filename 和 description 字段保持明文以支持按文件名检索。

#### Q4：workspace_cleaner 清理时备份失败怎么办？（v0.8.0 新增）

**A：** workspace_cleaner 在调用 `delete_recovery.py backup` 备份失败时，会自动降级为直接复制文件到 `delete_backup/timestamp/`（手动备份模式），不依赖 delete_recovery.py 的完整安全验证。如果手动备份也失败（权限问题等），该文件会被跳过并在结果中报告错误。备份失败的 文件不会被删除。

### English

This section directly addresses reviewer concerns.

#### Q1: Why does `allowed_roots` default to workspace root?

**A:** `allowed_roots` defaults to `[WORKSPACE_ROOT]` as a deliberate security default. As a recovery tool, the remaining use case — restoring files originally outside the workspace — is served by explicitly setting `allowed_roots=None`. The workspace root confinement prevents accidental or malicious restore to arbitrary system paths.

**Scope of protection:** SHA256 + PATH cross-validation guards against "replace the backup file after it was originally created," but does **not** protect against an attacker who simultaneously controls write access to `delete_backup/` and replaces all three files (backup + `.sha256` + `.path`) together. Therefore, the skill's security depends on filesystem permissions protecting `delete_backup/` — only deploy in environments where that directory is write-protected from untrusted processes. Path-traversal escape (`../`) is independently blocked and unaffected by this limitation.

#### Q2: Why doesn't `--force` skip all security checks?

**A:** `--force` is only intended for restoring **legacy backups that lack SHA256 records**. `--force` is strictly limited:

| Check | Normal restore | `--force` restore |
|-------|--------------|------------------|
| SHA256 integrity (content not tampered) | ✅ Always | ✅ Always |
| SHA256 existence check | ✅ Blocked if missing | ❌ Bypassed (legacy backups pre-date SHA256) |
| PATH cross-validation (.sha256 PATH vs .path file) | ✅ Always | ✅ **Always, non-bypassable** |
| Path traversal detection (`../` escape) | ✅ Always | ✅ **Always, non-bypassable** |

In short: `--force` only waives "SHA256 record is absent" as a condition — it never skips any substantive security check.

#### Q3: Why does manifest.jsonl store original paths — is this sensitive information leakage?

**A:** The `path` field in manifest.jsonl is stored as HMAC-SHA256 encrypted (`HASH_PREFIX:HMAC_TAG`) — original paths are no longer readable. The plaintext original path is always retrievable from the `.path` file in the backup folder. Filename and description remain in plaintext to support filename-based search.

#### Q4: What happens if workspace_cleaner backup fails?

**A:** If `delete_recovery.py backup` fails, workspace_cleaner falls back to a manual copy directly into `delete_backup/timestamp/` (no SHA256/PATH validation in this fallback). If even the manual backup fails (e.g., permission error), the file is skipped and reported as an error — it is NOT deleted.

## 注意事项 / Notes

### 中文

1. **删除前必备份**：所有删除操作前都应先调用 `backup`，防止误删
2. **恢复时目标冲突**：如果原位置已有文件，会自动将旧文件暂存到 `temp_existing/` 目录
3. **恢复后自动删备份**：默认情况下，恢复成功后会自动删除对应备份（多文件时等全部恢复完再清理）；使用 `--keep-backup` 可保留
4. **路径编码**：备份文件名将 `\`、`/`、`:` 替换为 `__`，恢复时需使用转换后的名称
5. **时间触发清理**：7天备份清理和30天日志清理改为时间触发（默认24小时间隔），不再每次命令都执行全量扫描；`cleanup` 命令本身不受影响，仍立即执行全量清理
6. **manifest 增量操作**：restore/delete_backup 时按需压缩 manifest（候选集≤100条时全量rewrite，>100条时追加墓碑标记）；list/search/log 时自动检查并触发增量压缩
7. **安全验证**：restore 时自动进行 SHA256 完整性 + PATH 交叉验证 + 遍历检测，如验证失败会明确报错
8. **旧备份恢复**：无 SHA256 记录的旧备份使用 `restore --force` 可强制恢复（完整性检查跳过，但 PATH 验证和遍历检测仍然生效，不可绕过）
9. **检索索引**：`backup` 自动追加索引，`restore` 成功后自动剔除；过期备份文件夹对应的索引随 `cleanup` 或脚本启动时自动清理
10. **workspace 目录限制**（v0.7.0）：恢复目标被限制在 workspace 根目录内，阻止恢复文件到任意系统路径；如需恢复 workspace 外的文件，请手动设置 `allowed_roots=None`
11. **manifest 路径加密**（v0.7.0）：manifest 中的原始路径字段已改为 HMAC-SHA256 加密，无法通过直接查看 manifest 获取原始路径；解密完全由 `.path` 文件负责
12. **workspace_cleaner 定时清理**（v0.8.0）：需通过 cron 或定期触发；默认24小时间隔，7天过期文件；核心文件和技能目录始终保护
13. **workspace_cleaner 备份降级**（v0.8.0）：delete_recovery.py 备份失败时自动降级为手动备份；手动备份也失败则跳过该文件（不删除）

### English

1. **Always backup before deleting**: Call `backup` before any deletion
2. **Restore target conflict**: Existing files moved to `temp_existing/` before restoring
3. **Auto-delete backup after restore**: Default behavior (multi-file: all restored → then delete); use `--keep-backup` to retain
4. **Path encoding**: `\`, `/`, `:` replaced with `__` in backup filenames
5. **Time-triggered cleanup**: 7-day backup and 30-day log cleanup are time-triggered (default 24-hour interval), not run on every command; `cleanup` command itself still runs full cleanup immediately
6. **Incremental manifest**: restore/delete_backup use on-demand manifest compaction; list/search/log auto-check and compact oversized manifests
7. **Security checks**: Restore automatically fails with clear error if SHA256 integrity, PATH cross-validation, or path traversal check fails
8. **Legacy backup restore**: Backups without SHA256 records use `restore --force` to force restore (integrity check skipped, but PATH validation and traversal detection still apply, non-bypassable)
9. **Manifest index**: `backup` auto-indexes; `restore` auto-removes index entry; stale entries pruned on `cleanup` or script startup
10. **Workspace root confinement** (v0.7.0): Restore destinations are confined to workspace root — files cannot be restored to arbitrary system paths; set `allowed_roots=None` to restore outside workspace
11. **Manifest path encryption** (v0.7.0): Original paths in manifest.jsonl are HMAC-SHA256 encrypted — cannot be read by inspecting the manifest file; decryption always uses the `.path` file in the backup folder
12. **workspace_cleaner scheduled cleanup** (v0.8.0): Requires cron or periodic triggering; default 24-hour interval, 7-day expiry; core files and skill directory always protected
13. **workspace_cleaner backup fallback** (v0.8.0): Falls back to manual copy if delete_recovery.py backup fails; skips (does not delete) if even manual backup fails

# delete-recovery
