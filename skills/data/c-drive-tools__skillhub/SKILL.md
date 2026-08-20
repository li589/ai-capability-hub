---
name: c-drive-tools
slug: c-drive-tools
displayName: 轻C·C盘空间释放专家
version: v2.0.3
description: C盘系统扫描、修复与优化工具集。当用户需要：(1) 分析C盘空间占用（找出大文件/大目录）、(2) 清理C盘临时文件/垃圾文件释放空间、(3) 修复Windows系统文件（SFC/DISM）、(4) 优化C盘存储空间时使用。触发关键词：C盘满了、C盘空间、清理C盘、C盘扫描、SFC、DISM、系统文件修复、磁盘优化、系统修复。
---

# C-Drive Tools Skill

本 skill 提供 C 盘空间分析、临时文件清理、系统文件修复三大功能，通过 PowerShell 脚本实现。

## 运行环境要求

- Windows 10/11
- PowerShell 5.1+（系统自带）
- 系统文件修复（`repair_system_files.ps1`）需要**管理员权限**
- 清理/分析脚本在标准用户权限下可运行（部分路径可能访问受限）

## 脚本说明

### 1. 空间分析 — `scripts/analyze_space.ps1`

分析 C 盘空间占用情况，找出空间消耗大户。

```powershell
# 默认分析C盘，显示Top20大目录
powershell -ExecutionPolicy Bypass -File scripts/analyze_space.ps1

# 指定分析路径
powershell -ExecutionPolicy Bypass -File scripts/analyze_space.ps1 -Path "C:\" -TopN 30

# 包含系统目录分析
powershell -ExecutionPolicy Bypass -File scripts/analyze_space.ps1 -IncludeSystemFiles
```

输出内容：
- C 盘总容量/已用/可用/使用率
- 顶级目录大小排行（Top N）
- 大于 100MB 的大文件列表
- 常见占用位置（下载、桌面、临时目录、休眠文件等）

### 2. 临时文件清理 — `scripts/clean_temp_files.ps1`

安全清理各类临时文件和缓存，**默认不删除系统关键文件**。

```powershell
# 预览模式（不实际删除，只显示将要清理的内容）
powershell -ExecutionPolicy Bypass -File scripts/clean_temp_files.ps1 -DryRun

# 执行清理（默认清理：用户临时文件、系统临时、Prefetch、回收站、浏览器缓存、DNS缓存）
powershell -ExecutionPolicy Bypass -File scripts/clean_temp_files.ps1

# 同时清理Windows更新缓存（注意：清理后无法卸载已安装的更新）
powershell -ExecutionPolicy Bypass -File scripts/clean_temp_files.ps1 -CleanWindowsUpdateCache
```

清理项目（默认启用/可选）：
| 项目 | 默认 | 参数控制 |
|------|:----:|---------|
| 用户临时文件（7天前） | [是] | `-CleanUserTemp` |
| 系统临时文件（7天前） | [是] | `-CleanSystemTemp` |
| Prefetch 预读取缓存（7天前） | [是] | `-CleanPrefetch` |
| 回收站 | [是] | `-CleanRecycleBin` |
| 浏览器缓存（Chrome/Edge/Firefox） | [是] | `-CleanBrowserCache` |
| DNS 客户端缓存 | [是] | `-CleanDnsCache` |
| Windows 更新缓存 | [否] | `-CleanWindowsUpdateCache`（需显式指定）|

**安全策略：**
- 默认只清理 7 天前的临时文件，避免误删正在使用的文件
- Windows 更新缓存默认不清理，需显式指定 `-CleanWindowsUpdateCache`
- 支持 `-DryRun` 预览模式，实际删除前建议先预览

### 3. 系统文件修复 — `scripts/repair_system_files.ps1`

使用 DISM + SFC 修复损坏的 Windows 系统文件，**必须以管理员身份运行**。

```powershell
# 以管理员身份运行
Start-Process powershell "-ExecutionPolicy Bypass -File `"scripts/repair_system_files.ps1`"" -Verb RunAs
```

修复步骤（按顺序自动执行）：
1. `DISM /Online /Cleanup-Image /StartComponentCleanup` — 清理组件存储
2. `DISM /Online /Cleanup-Image /CheckHealth` — 检查组件存储健康状态
3. `DISM /Online /Cleanup-Image /ScanHealth` — 扫描镜像完整性，如有损坏自动执行 `/RestoreHealth`
4. `SFC /scannow` — 扫描并修复系统文件

## 使用流程

### 场景一：C盘空间不足

1. **先分析**：运行 `analyze_space.ps1` 找出空间占用大户
2. **再清理**：用 `clean_temp_files.ps1 -DryRun` 预览，确认后执行实际清理
3. **汇报结果**：告知用户清理释放的空间量，以及进一步建议（如迁移大文件、关闭休眠文件等）

### 场景二：系统异常/怀疑系统文件损坏

1. 以管理员身份运行 `repair_system_files.ps1`
2. 等待 DISM + SFC 完成（可能需要 5-20 分钟，视系统情况而定）
3. 根据输出判断是否需要进一步操作（如无法修复，建议用安装介质修复）

### 场景三：定期维护

建议每月运行一次清理脚本（不含 `-CleanWindowsUpdateCache`），保持系统整洁。

## 注意事项

- **休眠文件 `hiberfil.sys`**：占用空间较大（约内存的 75%），如需释放，可运行 `powercfg -h off`（需管理员），但会失去休眠功能
- **页面文件 `pagefile.sys`**：不建议手动删除，系统会自动管理；如需调整大小，通过"系统属性 → 高级 → 性能设置 → 高级 → 虚拟内存"配置
- **DISM 修复需要联网**：`/RestoreHealth` 参数会从 Windows Update 下载修复源，确保网络连接正常
- **SFC 完成后建议重启**：修复的系统文件在下次启动时才完全生效

## 进一步释放C盘空间的建议

分析/清理完成后，如空间仍不足，可向用户建议：
1. 禁用休眠：`powercfg -h off`（需管理员，可释放数 GB）
2. 清理 Windows 更新备份：`dism /Online /Cleanup-Image /SPSuperseded`（需管理员）
3. 迁移虚拟内存到其他盘
4. 使用"存储感知"自动清理（Windows 10/11 内置）
5. 卸载不常用的大软件（用 Geek Uninstaller 等工具彻底清理）

---

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v2.0.3** | 2026-06-21 | 追加「🔌如何让本技能常驻生效」指南 |
| v2.0.2 | 2026-06-21 | 首次发布；追加「🔌如何让本技能常驻生效」指南 |
## 🔌 如何让本技能常驻生效（无需触发词）

> 你是否希望打开对话窗口时，这个技能就自动生效，不需要每次说触发词？
> 按以下步骤操作即可。

### 方法：写入 AGENTS.md 的强制前置规则

在你的 workspace 的 `AGENTS.md` 文件中，添加以下内容（放在 `## Tools & Skills` 部分之后）：

```markdown
### 🔒 轻C-C盘空间释放专家 任务 → 自动加载本技能

当任务涉及 **C盘空间/磁盘清理/大文件/临时文件/系统优化** 等任何相关操作时：

1. **必须先读取** `~/.qclaw/skills/c-drive-tools/SKILL.md` 全文
2. **严格执行本技能的所有铁律和规则**
3. 改完必须验证结果
```

### 为什么这样做有效？

- `AGENTS.md` 是每次会话启动时 AI **必读**的文件
- 写入这里的规则**不需要触发词**，只要任务内容涉及对应领域就自动生效
- 相当于把这个技能"钉"在了你的默认工作模式里

### 多个技能可以同时常驻

你可以在 `AGENTS.md` 中为多个技能分别写强制前置规则，它们互不冲突。
AI 会根据当前任务类型自动判断该加载哪个技能。

> 💡 **提示**：如果你不确定怎么写，直接告诉 AI：
> "把 轻C-C盘空间释放专家 也加进 AGENTS.md 的强制前置规则里"
> AI 会帮你自动完成。