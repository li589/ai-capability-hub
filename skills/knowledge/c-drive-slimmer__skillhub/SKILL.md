---
name: c-drive-slimmer
description: "Windows C盘瘦身专家，扫描并清理注册表残留、系统垃圾、软件缓存、大文件和卸载残留。当用户提到C盘清理、磁盘空间不足、C盘瘦身、系统垃圾、缓存清理、注册表清理、磁盘空间不足、释放空间、电脑卡慢、磁盘爆满时使用。"

metadata:
  version: "1.0.0"
  author: "catpaw-user"
  tags: "windows,disk-cleanup,cache,registry,system"
---

# C盘瘦身专家

Windows C盘全维度扫描与安全清理工具。分6个维度扫描，交互式确认后执行清理。

## 工作流程

```
扫描(6维度) → 分类汇总展示 → 用户选择清理范围 → 执行清理 → 验证结果
```

## 扫描6维度

### 维度1: 卸载注册表残留

扫描3个卸载注册表位置，找出安装路径(InstallLocation)已不存在的条目：
- `HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*`
- `HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*`
- `HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*`

再扫描SOFTWARE下无对应卸载条目的残留键（黑名单匹配：360/Baidu/Sogou/Thunder/Kingsoft等）。

### 维度2: 残留Windows服务

扫描已停止且可执行文件不存在的服务：
```powershell
Get-CimInstance Win32_Service | Where-Object { $_.PathName -match '^[A-Za-z]:\\' -and $_.State -eq 'Stopped' -and -not (Test-Path $exePath) }
```

### 维度3: 系统垃圾与临时文件

| 路径 | 说明 |
|------|------|
| `$env:LOCALAPPDATA\Temp` | 用户临时文件 |
| `C:\Windows\Temp` | 系统临时文件 |
| `C:\Windows\SoftwareDistribution\Download` | Windows Update下载缓存 |
| `C:\Windows\Logs` | 系统日志 |
| `*\Explorer\thumbcache_*.db` | 缩略图缓存 |
| `$env:LOCALAPPDATA\CrashDumps` | 崩溃转储 |
| `$env:LOCALAPPDATA\D3DSCache` | D3D着色器缓存 |
| `$env:LOCALAPPDATA\Microsoft\Windows\INetCache` | IE/Edge网络缓存 |
| 回收站 | `Clear-RecycleBin -Force` |

### 维度4: 软件缓存

按以下优先级扫描，只报告 >5MB 的目录：

| 优先级 | 缓存类型 | 典型路径 | 清理策略 |
|--------|---------|---------|---------|
| 高 | npm | `AppData\Local\npm-cache`, `AppData\Roaming\npm-cache` | 删除内容 |
| 高 | yarn | `AppData\Local\yarn\Cache` | 删除内容 |
| 高 | pnpm | `AppData\Local\pnpm-cache` | 删除内容 |
| 高 | pip | `AppData\Local\pip\Cache` | 删除内容 |
| 高 | uv | `AppData\Local\uv\cache` | 删除内容 |
| 高 | Conda | `~\.conda\pkgs` | 删除内容 |
| 高 | Maven | `~\.m2\repository` 或 settings.xml 中 localRepository | 清SNAPSHOT/lastUpdated |
| 高 | JetBrains | `AppData\Local\JetBrains` | 删除内容 |
| 高 | Playwright | `AppData\Local\ms-playwright` | 保留最新版，删旧版 |
| 中 | VS Code | `AppData\Roaming\Code\{Cache,CachedData,CachedExtensionVSIXs,logs}` | 删除内容 |
| 中 | Chrome | `Google\Chrome\User Data\Default\{Cache,Code Cache,Service Worker,GPU*}` | 删除内容，保留书签/密码 |
| 中 | Edge | `Microsoft\Edge\User Data\Default\{Cache,Code Cache,GPU*}` | 删除内容 |
| 中 | BeeWare | `AppData\Local\BeeWare` | 删除内容 |
| 中 | WPS | `AppData\Roaming\Kingsoft\*\{addons\pool,log,cache,update}` | 删除内容，保留用户文件 |
| 低 | Docker | `AppData\Local\Docker\wsl`, `~\.docker\desktop` | 需确认不再使用 |
| 低 | Android SDK | `AppData\Local\Android\Sdk\.temp` | 仅临时文件 |

### 维度5: 下载文件夹和大文件

扫描 `~/Downloads` 和 `~/Desktop`，列出 >50MB 的文件及最后访问时间。
重点标记 `.exe`/`.msi` 安装包（可能已安装但未删除）。

### 维度6: 不常用软件

从卸载注册表获取已安装软件列表，过滤掉：
- 系统组件（Microsoft.*/Windows SDK/NVIDIA/CUDA/Intel/AMD）
- 开发工具（VS/VSCode/Git/Java/Python/Node/Go/Android Studio/Docker）
- 安全类（不在卸载列表中则保留）

按 EstimatedSize 降序展示，标注可安全卸载的软件。

## 执行清理

### 原则

1. **必须交互确认** — 展示扫描结果后用 AskQuestion 让用户选择清理范围
2. **安全优先** — 以下操作不可执行：
   - ❌ 不删除 Windows Installer 缓存（`C:\Windows\Installer`）
   - ❌ 不删除 WinSxS 组件（用 `Dism /Online /Cleanup-Image /StartComponentCleanup` 代替）
   - ❌ 不删除浏览器书签/密码/扩展（只清Cache/ServiceWorker/GPUCache）
   - ❌ 不删除注册表中的系统键（Microsoft/Windows/Classes）
3. **内容清理优先** — 对缓存目录使用"删除内容保留目录"策略（ContentOnly=True）
4. **验证闭环** — 清理后重新扫描确认释放量

### PowerShell脚本编写规范

因终端命令不支持换行符且 `$` 符号会被转义，**必须将脚本写入 .ps1 文件再执行**：

1. 用 `write` 工具将脚本写到临时目录（如 `<workspace>/test/cleanup/`）
2. 用 `powershell -ExecutionPolicy Bypass -File "<path>.ps1"` 执行
3. 清理完成后删除临时脚本

脚本中的关键函数模式：

```powershell
# 安全删除目录内容（保留目录本身）
function Remove-CacheDir {
    param([string]$Path, [string]$Desc, [bool]$ContentOnly = $false)
    if (Test-Path $Path) {
        $sizeMB = [math]::Round(
            (Get-ChildItem $Path -Recurse -Force -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum / 1MB, 1)
        if ($ContentOnly) {
            Get-ChildItem $Path -Force -ErrorAction SilentlyContinue |
                Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# 安全删除注册表键
function Remove-RegKeySafe {
    param([string]$Path, [string]$Description)
    if (Test-Path $Path) {
        Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 安全删除服务
# sc.exe delete <ServiceName>
```

### WSL卸载（需用户明确确认）

```powershell
wsl --unregister Ubuntu-22.04
```

### Windows磁盘清理（自动全选）

```powershell
# 设置磁盘清理配置
$categories = @('Temporary Files','Update Cleanup','Thumbnail Cache',
                'Windows Error Reporting Files','Delivery Optimization Files')
foreach ($cat in $categories) {
    Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\$cat" `
        -Name 'StateFlags0099' -Value 2 -Type DWord -ErrorAction SilentlyContinue
}
Start-Process cleanmgr -ArgumentList '/sagerun:99' -Wait
```

## 输出格式

### 扫描结果展示

用Markdown表格分类展示，标注安全性：
- ✅ 可安全清理
- ⚠️ 需谨慎（可能仍在使用）
- ❌ 不建议清理

### 清理结果汇总

```
| 清理项 | 释放空间 | 状态 |
|--------|---------|------|
| npm 缓存 | 1.32 GB | ✅ |
| ... | ... | ... |

C盘空间: 清理前 X GB → 清理后 Y GB (释放 Z GB)
```

## 扫描性能注意

- 每个维度写成**独立的 .ps1 文件**分别执行，避免3分钟超时
- 避免扫描 `C:\Windows` 全目录（极大且无意义）
- `Get-ChildItem -Recurse` 对大目录可能很慢，设 >5MB 阈值过滤
- `$foreach` 变量在 `-Command` 模式下会被吞掉，必须用 `-File` 模式

## Additional Resources

- For detailed scan script templates, see [scripts/](scripts/)
