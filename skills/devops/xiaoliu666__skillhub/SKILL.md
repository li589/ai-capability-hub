---
name: cdrive-cleaner
description: |
  C盘清理与数据迁移专家。当用户说"C盘满了"、"清理C盘"、"C盘转移"、"搬家到D盘"、"磁盘空间不足"、
  "red disk"、"drive full"、"move to D drive" 时触发。
  核心能力：扫描C盘大户目录 → robocopy搬移到D盘 → 创建NTFS Junction软链接实现零配置迁移。
  不适用于：普通文件删除、系统优化、卸载软件（那些是别的领域）。
---

# C盘清理迁移

## 原则

1. **先扫描，再动手** — 别瞎删
2. **搬移 > 删除** — 优先移到 D 盘，不丢数据
3. **软链接无缝** — 用 `mklink /J`，程序无感知，环境变量不用改
4. **备份再删** — 搬完重命名源目录为 `.bak`，确认能用再删

## 核心流程

### 1. 扫描 → 2. 提案 → 3. 用户确认 → 4. 逐个搬运

```
scan.ps1          → 找出 > 50MB 的目录
↓
列出可搬迁目标，让用户勾选
↓
migrate.ps1       → robocopy + mklink /J
↓
删除 .bak 备份
```

## 可安全搬迁的目录

### AppData\Roaming (通过 %APPDATA%)

典型大户：
- **Trae CN / TRAE SOLO CN** — AI IDE 缓存，各 4~7GB
- **CodeBuddy CN** — 编程助手
- **Tencent** — 微信/QQ 数据
- **WPS / Kingsoft** — WPS 办公，关掉 WPS 后搬
- **Code / QQ / 等**

搬法：`%APPDATA%\xxx` → `D:\UserData\Roaming\xxx`

### AppData\Local (通过 %LOCALAPPDATA%)

典型大户：
- **ms-playwright** — Playwright 浏览器，2GB+
- **微信开发者工具**
- **Google** — AndroidStudio 等
- **uv / pip / npm** 缓存

搬法：`%LOCALAPPDATA%\xxx` → `D:\UserData\Local\xxx`

### 用户根目录隐藏文件夹

`%USERPROFILE%\.*` （点开头的隐藏目录）

典型大户：
- `.lingma` — 灵码 AI，3GB+
- `.vscode` — VS Code 插件
- `.cache` — 各类缓存（pip/npm/yarn）
- `.trae-cn` / `.trae` — AI IDE
- `.codex` / `.codebuddy*` / `.marscode` / `.codegeex`

搬法：`%USERPROFILE%\\.xxx` → `D:\UserData\Profile\xxx`

## 搬不动的目录（跳过，别死磕）

- **AppData\Local\Microsoft** — UsrClass.dat（用户注册表）、Edge WebCache 被系统锁死，即使重启
- 任何 `Rename-Item` 被拒绝 → 标记为"跳过"，别浪费时间

## 搬运命令模板

基本命令（直接用，不用改）：
```powershell
# robocopy 复制
robocopy "C:\源路径" "D:\目标路径" /E /COPY:DAT /DCOPY:T /R:1 /W:1

# 改名 + 建链接
Rename-Item "C:\源路径" "源目录.bak" -Force
cmd /c "mklink /J `"C:\源路径`" `"D:\目标路径`""

# 验证成功 → 删备份
cmd /c "rmdir /s /q `"C:\源路径.bak`""
```

⚠️ 不要用 `/COPYALL`（需要审计权限会报错），不要用 `/MIR`（会删 D 盘已有文件）。

## 机器人脚本

- `scripts/scan.ps1` — 扫描 C 盘大户目录
- `scripts/migrate.ps1` — 单目录迁移（robocopy + junction）

## 常见坑

| 问题 | 处理 |
|------|------|
| 文件被占用 | 关闭对应程序（WPS/QQ 等），重试 |
| `/COPYALL` 权限不足 | 改成 `/COPY:DAT` |
| 路径过长 | 用 `cmd /c rmdir /s /q` 代替 PowerShell Remove-Item |
| 安全策略拦截删除 | 逐条确认，别试图绕过 |
| Microsoft 目录搬不动 | 直接跳过，不用纠结 |

## 话术风格

直白、简洁、给结论。
- ✅ "这俩各 5GB，你也不怎么用，搬 D 盘。"
- ✅ "搬完了，C 盘从 85% 降到 52%，腾出 40GB。"
- ❌ 不堆术语，不写废话
