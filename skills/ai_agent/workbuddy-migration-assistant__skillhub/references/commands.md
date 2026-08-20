# 命令接口明细

> 何时加载：构造 `export` / `import` / `info` 命令时。

## 导出命令

```bash
python scripts/export.py \
    --source ~/.workbuddy \
    --output ~/Desktop/wb-migration.zip \
    [--with-workspaces] \
    [--no-conversations] \
    [--no-credentials] \
    [--workspace-exclude-pattern <glob>] \
    [--workspace-size-limit <bytes>] \
    [--dry-run]
```

| 参数 | 说明 |
|------|------|
| `--source <path>` | 源端 WorkBuddy 根目录（国内版：`~/.workbuddy/`） |
| `--output <path>` | 输出 zip 路径，缺省 `./wb-migration-{timestamp}.zip` |
| `--with-workspaces` | 一并打包产物包（对话目录文件）。缺省不打包 |
| `--no-conversations` | 不打包对话记录（projects/*.jsonl），大幅缩小主包 |
| `--no-credentials` | 不打包 `.credentials.json`（推荐跨机器时启用） |
| `--all-users` | 导出所有 user_id 的资产（默认：只导出当前登录用户） |
| `--workspace-include <path>` | 显式指定要打包的工作区目录路径，可重复 |
| `--format <zip\|tar.gz>` | **v0.4.0** 输出格式（默认 zip）。tar.gz 对文本数据压缩更好 |
| `--exclude-session-id <id>` | 排除指定 session，可重复。默认自动排除当前迁移会话 |
| `--workspace-exclude-pattern <glob>` | 追加排除模式，支持目录名+`/`、文件名、路径三种格式 |
| `--workspace-size-limit <bytes>` | 单目录大小上限，默认 5 GB，超限自动跳过 |
| `--dry-run` | 预览模式：输出 JSON 计划但不写文件 |

## 导入命令

```bash
python scripts/import.py \
    --package ~/Desktop/wb-migration.zip \
    --target ~/.workbuddy \
    [--workspaces-package ~/Desktop/wb-migration-workspaces.zip] \
    [--workspace-destination <dir>] \
    [--path-map /home/alice=/Users/alice] \
    [--target-os darwin] \
    [--overwrite] \
    [--no-conversations] \
    [--no-credentials] \
    [--skip-db] \
    [--skip-skills] \
    [--skip-configs] \
    [--dry-run]
```

| 参数 | 说明 |
|------|------|
| `--package <path>` | **必填**，主包 zip 路径 |
| `--target <path>` | 目标端根目录，`auto` 自动探测 |
| `--auto-map` | **v0.2.0** 自动检测源/目标平台差异，生成 path-map + uid-map 规则（零配置跨平台迁移） |
| `--target-user-id <uuid>` | `--auto-map` 时目标 DB 为空时指定目标 user_id |
| `--no-validate` | 跳过恢复后数据完整性校验 |
| `--workspaces-package <path>` | 产物包 zip 路径（如有） |
| `--workspace-destination <dir>` | 产物文件解压目标目录，缺省 `~/wb-imported-workspaces/` |
| `--path-map <old>=<new>` | 路径前缀映射，跨 OS/用户名时必用，可重复指定多条 |
| `--target-os <os>` | 目标 OS（darwin/win32/linux），自动推断路径分隔符 |
| `--overwrite` | 冲突时覆盖（默认只合并不覆盖），自动备份 `.bak-<ts>` |
| `--no-conversations` | 即使包里有对话记录也不导入 |
| `--no-credentials` | 即使包里有凭证也不导入 |
| `--skip-db`、`--skip-skills`、`--skip-configs` | 精细排除某类资产 |
| `--dry-run` | 预览模式：输出冲突检测报告，不实际写入 |

## 检视命令（v0.3.0）

```bash
python scripts/info.py --package ~/Desktop/wb-migration.zip

# JSON 输出（机器可读）
python scripts/info.py --package ~/Desktop/wb-migration.zip --json
```

导入前检视迁移包内容：源平台信息、DB 统计（session 数、user_id 数）、资产清单、跨平台检测与 `--auto-map` 建议。**不修改任何数据**。

## 环境预检（每次操作前必做）

1. 按优先级检测 Python：
   - ① WorkBuddy managed Python
   - ② 系统 python/python3
2. 验证版本 >= 3.8
3. 验证 SQLite：`<python> -c "import sqlite3; print(sqlite3.sqlite_version)"`
