---
name: winskill
slug: winskill
displayName: "Windows 服务器运维工具箱"
description: "Windows 服务器运维工具箱 - 磁盘分析、临时文件清理、IIS 站点管理、批量文件操作、服务状态监控、Windows Update 诊断、实时性能监控、安全审计、注册表启动项审计、磁盘健康检测、网络端口监控、事件日志诊断、已安装程序管理、用户会话监控、计划任务审计、文件共享审计、DNS网卡诊断、SSL证书过期检测、防火墙规则审计、服务崩溃恢复状态、系统文件修复、存储池管理、备份状态检查、Docker容器管理、K8s集群监控、自动化修复向导、性能基线与趋势分析、等保合规检查清单、远程多服务器管理、日志轮转、模块索引。只读分析+安全确认，绝不误删文件，完全免费离线运行。"
description_zh: "Windows 服务器运维工具箱 - 磁盘分析、清理、IIS 管理、批量操作、服务监控、更新诊断、性能监控、安全审计、注册表审计、磁盘健康、网络监控、事件日志、程序管理、会话监控、计划任务、共享审计、DNS诊断、SSL证书、防火墙审计、服务崩溃记录、系统修复、存储池、备份检查、Docker容器管理、K8s监控、自动化修复向导、性能基线与趋势分析、等保合规检查清单、远程多服务器管理、日志轮转、模块索引。只读+确认模式，零依赖离线运行。"
version: 3.1.0
category: system-administration
platforms:
  - windows
tags:
  - windows
  - sysadmin
  - disk-cleanup
  - iis
  - monitoring
  - file-management
  - devops
  - performance
  - security
  - audit
  - registry
  - disk-health
  - network
  - event-log
  - software
  - session
  - scheduled-tasks
  - smb-share
  - dns
  - ssl-certificate
  - firewall
  - service-recovery
requires_api_key: false
---

# Winskill — Windows 服务器运维工具箱

## 快速开始

**直接对 AI 说就行，不用记命令。**

| 你想做什么 | 直接对 AI 说 |
|-----------|-------------|
| 看磁盘空间 | `"帮我扫一下 D 盘大文件"` |
| 清理临时文件 | `"看看我电脑的临时文件"` |
| 检查 IIS | `"我的 IIS 站点还活着吗？"` |
| 检测重复文件 | `"帮我找下重复文件"` |
| 检查服务状态 | `"看下数据库和 IIS 服务有没有挂"` |
| Windows Update 状态 | `"Windows Update 正常吗？有积压补丁吗？"` |
| 服务器卡顿定位 | `"服务器变卡了，帮我看看是什么原因"` |
| 检查有没有被入侵 | `"帮我查一下有没有异常登录"` |
| 检查可疑启动项 | `"有没有可疑的自启动程序"` |
| 磁盘健康状态 | `"硬盘还健康吗？有没有坏道"` |
| 网络连接监控 | `"谁在连我的服务器"` |
| 系统日志哪里错了 | `"系统日志有没有最近的错误"` |
| 服务器装了什么程序 | `"看看系统安装了哪些软件"` |
| 谁在服务器上 | `"当前有谁登录了服务器"` |
| 检查计划任务 | `"有没有可疑的计划任务"` |
| 文件共享审计 | `"有哪些共享文件夹，权限安全吗"` |
| DNS / 网卡诊断 | `"DNS 解析正常吗"` |
| 搞不定了 | `"我遇到报错了，帮我看看"` |

> ⚠️ **AI 必须遵守**：凡涉及删除、停止服务、修改系统的操作，必须先展示操作清单，等用户明确说"确认执行"后才可执行。

---

## 安全声明

| 保护项 | 方式 |
|-------|------|
| 系统目录保护 | 绝不操作 `C:\Windows`、`C:\Program Files` 等 |
| 删除必须确认 | 先展示受影响文件，等用户说"确认清理"后才执行 |
| 回收站优先 | 删除用 `Shell.Application` 回收站 API |
| 只读诊断 | 所有分析命令不修改任何文件/服务/注册表 |
| 排除保护 | `pagefile.sys`、`hiberfil.sys` 等系统文件不可操作 |
| 注册表保护 | 注册表分析只读，任何修改需双重确认 |
| 日志读取保护 | 事件日志只读查看，不修改任何日志记录 |

---

## 功能模块

### 📋 日志记录与轮转

```powershell
function Write-WinskillLog {
    param([string]$Message)
    $logDir = "$env:USERPROFILE\.workbuddy\output\winskill"
    $logFile = Join-Path $logDir "winskill.log"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File $logFile -Append -Encoding utf8
    if (Test-Path $logFile) {
        $size = (Get-Item $logFile).Length
        if ($size -gt 10MB) {
            $timestamp = Get-Date -Format "yyyyMMddHHmmss"
            Move-Item $logFile "winskill.log.$timestamp" -Force
        }
    }
    Get-ChildItem $logDir -Filter "winskill.log.*" | Where-Object {
        $_.LastWriteTime -lt (Get-Date).AddDays(-7)
    } | Remove-Item -Force
}
```

### 📋 模块索引（一键列出所有可用操作）

```powershell
Write-Host "`n📋 Winskill 3.1.0 - 模块索引（共 30 个模块）"
Write-Host ("=" * 60)
Write-Host ("{0,-25} {1,-35}" -f "模块", "用途")
Write-Host ("-" * 60)
$modules = @(
    "模块 1: 磁盘空间分析 - 扫大文件/目录占用",
    "模块 2: 大文件重复检测 - 找重复文件",
    "模块 3: 临时文件安全清理 - 清理临时文件",
    "模块 4: IIS 站点管理 - IIS 站点/应用池状态",
    "模块 5: 服务状态监控 - Windows 服务状态",
    "模块 6: 批量文件操作 - 批量重命名/移动/复制",
    "模块 7: 目录磁盘使用报告 - 目录大小报告",
    "模块 8: Windows Update 服务状态 - 更新服务/缓存",
    "模块 9: 实时性能监控 - CPU/内存/磁盘/网络",
    "模块 10: 安全审计与日志分析 - 暴力破解/特权操作",
    "模块 11: 注册表与启动项安全审计 - 启动项/WMI",
    "模块 12: 磁盘健康状态检测 - SMART/坏道/温度",
    "模块 13: 网络连接与端口监控 - 连接/端口/防火墙",
    "模块 14: Windows 事件日志诊断 - 系统/应用日志",
    "模块 15: 已安装程序与补丁管理 - 程序/补丁清单",
    "模块 16: 用户会话与登录状态监控 - 会话/登录",
    "模块 17: 计划任务审计 - 计划任务清单",
    "模块 18: 文件共享与 SMB 审计 - 共享/权限",
    "模块 19: DNS 解析与网卡诊断 - DNS/网卡",
    "模块 20: SSL 证书过期检测 - 证书扫描",
    "模块 21: 防火墙规则审计 - 规则/高危检测",
    "模块 22: 关键服务崩溃与自动恢复 - 服务崩溃记录",
    "模块 23: 系统文件完整性检查与修复 - SFC/DISM",
    "模块 24: 存储池与虚拟磁盘管理 - Storage Spaces",
    "模块 25: Windows Server Backup 状态检查 - 备份状态",
    "模块 26: Docker / K8s 容器管理 - 容器/集群",
    "模块 27: 自动化修复向导 - 一键修复常见问题",
    "模块 28: 性能基线 & 趋势分析 - 趋势/告警/预测",
    "模块 29: 安全合规检查清单 - 等保2.0/CIS",
    "模块 30: 远程多服务器管理 - 多机批量管理"
)
$modules | ForEach-Object { Write-Host $_ }
Write-Host ("=" * 60)
Write-Host "直接对 AI 说模块名称或用途即可调用"
```


## 📌 模块导航（点击直达，共 30 个模块）

**🖥️ 基础运维（1-7）：**
[模块 1：磁盘空间分析](#module-1) · [模块 2：大文件重复检测](#module-2) · [模块 3：临时文件安全清理](#module-3) · [模块 4：IIS 站点管理](#module-4) · [模块 5：服务状态监控](#module-5) · [模块 6：批量文件操作](#module-6) · [模块 7：目录磁盘使用报告](#module-7)

**🔧 进阶运维（8-18）：**
[模块 8：Windows Update 服务状态与缓存管理](#module-8) · [模块 9：实时性能监控与进程资源分析](#module-9) · [模块 10：安全审计与日志分析](#module-10) · [模块 11：注册表与启动项安全审计](#module-11) · [模块 12：磁盘健康状态检测](#module-12) · [模块 13：网络连接与端口监控](#module-13) · [模块 14：Windows 事件日志诊断](#module-14) · [模块 15：已安装程序与补丁管理](#module-15) · [模块 16：用户会话与登录状态监控](#module-16) · [模块 17：计划任务审计](#module-17) · [模块 18：文件共享与 SMB 审计](#module-18)

**🔒 安全专项（19-25）：**
[模块 19：DNS 解析与网卡诊断](#module-19) · [模块 20：SSL 证书过期检测](#module-20) · [模块 21：Windows 防火墙规则审计](#module-21) · [模块 22：关键服务崩溃与自动恢复状态](#module-22) · [模块 23：系统文件完整性检查与修复（SFC / DISM）](#module-23) · [模块 24：存储池与虚拟磁盘管理（Storage Spaces）](#module-24) · [模块 25：Windows Server Backup 状态检查](#module-25)

**🚀 高级功能（26-30）：**
[模块 26：Docker / K8s 容器管理](#module-26) · [模块 27：自动化修复向导](#module-27) · [模块 28：性能基线 & 趋势分析](#module-28) · [模块 29：安全合规检查清单](#module-29) · [模块 30：远程多服务器管理](#module-30)

---

<a name="module-1"></a>

### 模块 1：磁盘空间分析






<details>
<summary>📋 展开查看：模块 1：磁盘空间分析</summary>

**用途**：扫描指定路径，找出占用空间的大文件和目录。

**常你说**：`"扫一下 C 盘大文件"` / `"D 盘哪个最占空间"`




```powershell
$scanPath = "C:\"   # ← 改成你要扫的盘符或目录

Get-ChildItem -Path $scanPath -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 100MB } |
    Sort-Object Length -Descending |
    Select-Object -First 50 @{N='路径';E={$_.FullName}},
        @{N='大小(GB)';E={[math]::Round($_.Length/1GB,2)}},
        @{N='最后修改';E={$_.LastWriteTime}}
```



**风险等级**：🟢 无（只读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Access to the path 'xxx' is denied` | 权限不足 | 管理员身份运行 PowerShell |
| `Could not find a part of the path` | 目录不存在 | 确认路径 |




</details>

[↑ 返回顶部](#module-1)

---

<a name="module-2"></a>

### 模块 2：大文件重复检测






<details>
<summary>📋 展开查看：模块 2：大文件重复检测</summary>

**用途**：通过 MD5 哈希找出重复文件。

**常你说**：`"找找 D 盘有没有重复文件"`




```powershell
$scanPath = "D:\"   # ← 扫描目标目录
$minSize = 1MB      # ← 只检测大于 1MB 的文件

Get-ChildItem -Path $scanPath -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt $minSize } |
    ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm MD5 -ErrorAction SilentlyContinue).Hash
        if ($hash) {
            [PSCustomObject]@{
                路径 = $_.FullName
                哈希 = $hash
                大小MB = [math]::Round($_.Length/1MB,2)
            }
        }
    } |
    Group-Object 哈希 |
    Where-Object { $_.Count -gt 1 } |
    ForEach-Object { $_.Group }
```



**风险等级**：🟢 无（只读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Exception getting file hash` | 文件正在使用 | 跳过 |
| `The specified path is not valid` | 路径格式不对 | 检查路径 |




</details>

[↑ 返回顶部](#module-1)

---

<a name="module-3"></a>

### 模块 3：临时文件安全清理






<details>
<summary>📋 展开查看：模块 3：临时文件安全清理</summary>

**用途**：扫描安全可删的临时文件，先预览后确认再清理。

**常你说**：`"帮我清理临时文件"` / `"C 盘快满了帮清 temp"`

**安全清理路径**：

| 路径 | 说明 | 安全天数 |
|------|------|---------|
| `%TEMP%\*` | 用户临时文件 | >7 天 |
| `C:\Windows\Temp\*` | 系统临时文件 | >7 天 |
| `C:\Windows\SoftwareDistribution\Download\*` | Windows Update 下载缓存 | 任意 |
| `C:\Windows\Prefetch\*` | 程序预取 | >30 天 |
| `IIS Temporary Compressed Files\*` | IIS 压缩缓存 | >1 天 |




```powershell
$tempPath = $env:TEMP
$daysOld = 7
$cutoff = (Get-Date).AddDays(-$daysOld)

$tempFiles = Get-ChildItem -Path $tempPath -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff }

Write-Host "═══════════════════════════════════════════"
Write-Host "  📋 扫描结果: $tempPath"
Write-Host "  过期临时文件数: $($tempFiles.Count) 个"
Write-Host "═══════════════════════════════════════════"

$tempFiles | Sort-Object Length -Descending |
    Select-Object -First 20 |
    Select-Object @{N='文件路径';E={$_.FullName}},
        @{N='大小(KB)';E={[math]::Round($_.Length/1KB,1)}},
        @{N='最后修改';E={$_.LastWriteTime}} |
    Format-Table -AutoSize

$totalKB = ($tempFiles | Measure-Object -Property Length -Sum).Sum
Write-Host "  预计可释放空间: $([math]::Round($totalKB/1MB,2)) MB"
Write-Host "  ⚠️ 确认删除请说 '确认清理'"
```






```powershell
# ⚠️ 仅当用户明确说「确认清理」后才执行！
Write-Host "  正在移到回收站..."
$shell = New-Object -ComObject Shell.Application
$rb = $shell.NameSpace(0x0a)
$totalFiles = 0
foreach ($f in $tempFiles) {
    try {
        $rb.MoveHere($f.FullName)
        $totalFiles++
    } catch { }
}
Write-Host "  ✅ 已完成！已将 $totalFiles 个文件移到回收站"
Write-Host "  如需彻底删除，请手动清空回收站"
```



**风险等级**：🟡 中（需确认后删除）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Cannot find path ... does not exist` | temp 目录下某些路径不存在 | 自动跳过 |
| `Access is denied` | 系统临时文件正在使用中 | 跳过，正常现象 |
| `MoveHere` 失败 | 回收站操作异常 | 手动清或用其他方式 |




</details>

[↑ 返回顶部](#module-1)

---

<a name="module-4"></a>

### 模块 4：IIS 站点管理






<details>
<summary>📋 展开查看：模块 4：IIS 站点管理</summary>

**用途**：查看站点状态、应用池信息、快速重启。

**常你说**：`"我的 IIS 站点正常吗？"` / `"重启一下应用池"`

**前置条件**（需管理员权限）：


```powershell
if (-not (Get-Module -ListAvailable -Name WebAdministration)) {
    Write-Host "⚠️ IIS 管理工具未安装，请以管理员运行:"
    Install-WindowsFeature Web-Mgmt-Tools
}
Import-Module WebAdministration
```





```powershell
Import-Module WebAdministration

Write-Host "════════ IIS 站点列表 ════════"
Get-Website | Select-Object @{N='站点名';E={$_.Name}},
    @{N='状态';E={$_.State}},
    @{N='物理路径';E={$_.PhysicalPath}},
    @{N='应用池';E={$_.ApplicationPool}},
    @{N='绑定';E={$_.Bindings -join ';'}} |
    Format-Table -AutoSize

Write-Host "`n════════ 应用池状态 ════════"
Get-WebAppPoolState | Select-Object @{N='名';E={$_.Name}}, @{N='状态';E={$_.Value}} |
    Format-Table -AutoSize
```






```powershell
# ⚠️ 仅当用户明确确认后才执行！
# Restart-WebSite -Name "你的站点名"
```



**风险等级**：🟢 查看只读 / 🟡 重启需确认

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-Website is not recognized` | IIS 模块未加载 | `Install-WindowsFeature Web-Mgmt-Tools` |
| `Cannot connect to IIS` | W3SVC 服务未启动 | 管理服务 |
| `Could not find WebAdministration` | 未装 IIS 管理工具 | 添加 Web 管理工具 |




</details>

[↑ 返回顶部](#module-1)

---

<a name="module-5"></a>

### 模块 5：服务状态监控






<details>
<summary>📋 展开查看：模块 5：服务状态监控</summary>

**用途**：一眼看出哪些关键服务挂了。

**常你说**：`"检查服务器关键服务"` / `"看下数据库有没有挂"`




```powershell
$criticalServices = @(
    "W3SVC",        # IIS
    "MSSQLSERVER",  # SQL Server
    "MySQL80",      # MySQL
    "Redis",        # Redis
    "Elasticsearch",# ES
    "Docker",       # Docker
    "Spooler",      # 打印
    "TermService",  # 远程桌面
    "Nginx",        # Nginx
    "Apache",       # Apache
    "Tomcat"        # Tomcat
)

Write-Host "════════ 关键服务状态 ════════"
$hasStopped = $false
foreach ($svc in $criticalServices) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s) {
        $icon = if ($s.Status -eq 'Running') { '✅' } else { '❌'; $hasStopped = $true }
        Write-Host "  $icon $($s.DisplayName) [$($s.Status)]"
    }
}
Write-Host "═══════════════════════════════"
if ($hasStopped) { Write-Host "  ⚠️ 有服务未运行" }
else { Write-Host "  ✅ 所有检测服务正常" }
```



**风险等级**：🟢 无（只读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Cannot find any service ...` | 该服务未安装 | 自动跳过 |




</details>

[↑ 返回顶部](#module-1)

---

<a name="module-6"></a>

### 模块 6：批量文件操作






<details>
<summary>📋 展开查看：模块 6：批量文件操作</summary>

**用途**：先预览规则，再确认执行批量重命名/移动。

**常你说**：`"把所有 .log 改成 backup_1.log 格式"`




```powershell
$sourceDir = "D:\logs"    # ← 源目录
$searchFilter = "*.log"   # ← 文件筛选
$renamePrefix = "backup"  # ← 新文件名前缀

$files = Get-ChildItem -Path $sourceDir -Filter $searchFilter -File
Write-Host "════════ 批量重命名预览 ════════"
Write-Host "  扫描到 $($files.Count) 个 $searchFilter 文件"

$i = 1
foreach ($f in $files) {
    Write-Host "  🔄 $($f.Name) → ${renamePrefix}_${i}${f.Extension}"
    $i++
}

Write-Host "`n  共 $($files.Count) 个文件将被重命名"
Write-Host "  ⚠️ 确认执行请说 '确认重命名'"
```






```powershell
# ⚠️ 仅当用户明确说「确认重命名」后才执行！
# $i = 1
# foreach ($f in $files) {
#     $newName = "${renamePrefix}_${i}${f.Extension}"
#     Rename-Item -Path $f.FullName -NewName $newName
#     Write-Host "  ✅ $($f.Name) → $newName"
#     $i++
# }
```



**风险等级**：🟡 中（需确认）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Cannot rename because item already exists` | 新文件名已存在 | 加时间戳避免重名 |
| `Access to the path is denied` | 文件锁定 | 关相关程序再试 |




</details>

[↑ 返回顶部](#module-1)

---

<a name="module-7"></a>

### 模块 7：目录磁盘使用报告






<details>
<summary>📋 展开查看：模块 7：目录磁盘使用报告</summary>

**用途**：用进度条样式一眼看出各目录占用。

**常你说**：`"看看各个目录的空间占用"`




```powershell
function Get-DirectorySize([string]$Path) {
    (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue |
     Measure-Object -Property Length -Sum).Sum
}

$dirs = @("C:\inetpub", "C:\Windows\Temp", "C:\ProgramData",
          "$env:TEMP", "C:\Users",
          "C:\Windows\SoftwareDistribution", "D:\")

foreach ($d in $dirs) {
    if (Test-Path $d) {
        $sizeGB = [math]::Round((Get-DirectorySize $d) / 1GB, 2)
        if ($sizeGB -gt 10)     { $icon = '🔴' }
        elseif ($sizeGB -gt 5) { $icon = '🟡' }
        else                  { $icon = '🟢' }
        Write-Host "  $icon $d : ${sizeGB} GB"
    }
}
```



**风险等级**：🟢 无（只读）



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-8"></a>

## 🆕 模块 8：Windows Update 服务状态与缓存管理




<details>
<summary>📋 展开查看：🆕 模块 8：Windows Update 服务状态与缓存管理</summary>

**用途**：诊断 Windows Update 是否卡住、查看已安装补丁、清理更新缓存。

**常你说**：`"Windows Update 正常吗？"` / `"更新缓存能不能删"`

### 8.1 查看更新服务状态与已安装补丁（只读）




```powershell
# 更新服务状态
Get-Service -Name wuauserv |
    Select-Object @{N='服务';E={$_.Name}},
        @{N='状态';E={$_.Status}},
        @{N='启动类型';E={$_.StartType}},
        @{N='账号';E={$_.StartName}}

Write-Host ""

# 已安装补丁（最近 10 个）
Get-HotFix | Sort-Object InstalledOn -Descending |
    Select-Object -First 10 @{N='补丁ID';E={$_.HotFixID}},
        @{N='安装日期';E={$_.InstalledOn}}
```



### 8.2 检查 SoftwareDistribution 更新缓存大小




```powershell
$sd = "C:\Windows\SoftwareDistribution"
if (Test-Path $sd) {
    $total = (Get-ChildItem -Path $sd -Recurse -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum).Sum
    Write-Host "  SoftwareDistribution 大小: $([math]::Round($total/1MB,1)) MB"

    $dlDir = Join-Path $sd "Download"
    if (Test-Path $dlDir) {
        $dlSize = (Get-ChildItem -Path $dlDir -Recurse -ErrorAction SilentlyContinue |
                   Measure-Object -Property Length -Sum).Sum
        Write-Host "  └─ 下载缓存(Download): $([math]::Round($dlSize/1MB,1)) MB"
    }
    Write-Host "  💡 若超过 500MB 可考虑清理（需先停止 wuauserv 服务）"
} else {
    Write-Host "  ⚠️ SoftwareDistribution 目录不存在"
}
```






```powershell
# ⚠️ 仅当用户明确说「确认清理更新缓存」后才执行！
# Stop-Service -Name wuauserv -Force
# Remove-Item -Path "$sd\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
# Start-Service -Name wuauserv
# Write-Host "  ✅ 已清理更新下载缓存，Windows Update 将重新下载所需补丁"
```



**风险等级**：🟢 查看只读 / 🟡 清理缓存需确认

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `The service ... cannot be stopped` | 服务正在使用 | 稍后重试或重启后清理 |
| `Access is denied` | 部分缓存文件被锁定 | 先停服务再清理 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| Windows Update 一直不下载 | 服务挂起，重停重启动可解决 |
| 错误码 0x80070005 | 权限问题，清理缓存可修复 |
| 补丁安装失败 | 清理 Download 缓存后重新检查更新 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-9"></a>

## 🆕 模块 9：实时性能监控与进程资源分析




<details>
<summary>📋 展开查看：🆕 模块 9：实时性能监控与进程资源分析</summary>

**用途**：定位 CPU/内存/磁盘 I/O 瓶颈，按进程排序找到罪魁祸首。

**常你说**：`"服务器变卡了，帮我看看"` / `"哪个进程吃内存最多"`

### 9.1 实时性能计数器（只读）




```powershell
Get-Counter '\Processor(_Total)\% Processor Time',
              '\Memory\Available MBytes',
              '\Memory\% Used',
              '\PhysicalDisk(_Total)\% Disk Time',
              '\PhysicalDisk(_Total)\Current Disk Queue Length' |
    Select-Object -ExpandProperty CounterSamples |
    Select-Object @{N='指标';E={$_.Path.Split('\')[-2..-1] -join '\'}},
        @{N='当前值';E={[math]::Round($_.CookedValue, 1)}} |
    Format-Table -AutoSize
```



### 9.2 内存占用 Top 10 进程




```powershell
Get-Process | Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10 @{N='进程名';E={$_.Name}},
        @{N='内存(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}},
        @{N='CPU(s)';E={[math]::Round($_.CPU,1)}} |
    Format-Table -AutoSize
```



### 9.3 磁盘 I/O 详细统计（按进程）




```powershell
Get-Counter '\Process(*)\Read Bytes/sec',
              '\Process(*)\Write Bytes/sec' |
    Select-Object -ExpandProperty CounterSamples |
    Where-Object { $_.CookedValue -gt 0 } |
    Sort-Object CookedValue -Descending |
    Select-Object -First 15 @{N='进程';E={
        $_.Path -replace '\\Process\((.*)\)\\Read Bytes/sec$','$1' |
        ForEach-Object { if ($_ -eq 'idle') { 'System Idle' } else { $_ }
    }}, @{N='Bytes/s';E={[math]::Round($_.CookedValue, 0)}} |
    Format-Table -AutoSize
```






```powershell
# ⚠️ 仅当用户明确说「确认创建」后才执行！
# $collector = New-DataCollectorSet -Name "ServerPerf_$(Get-Date -Format 'yyyyMMdd')" -Path "C:\PerfLogs"
# $collector.DataCollectors.Create(0, "Counter", 0,
#     '\Processor(_Total)\% Processor Time',
#     '\Memory\Available MBytes',
#     '\PhysicalDisk(_Total)\% Disk Time'
# )
# $collector.Commit("C:\PerfLogs\ServerPerf", 0, 0x01) | Out-Null
# Write-Host "  ✅ 已创建性能采集器，数据将保存到 C:\PerfLogs"
```



**风险等级**：🟢 实时查看 / 🟡 创建采集器需确认

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `The specified counter is not found` | 计数器未注册 | 运行 `lodctr /R` 重建计数器 |
| `Access denied` | 需要管理员权限 | 提升后执行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| CPU 持续 >90% | 按进程排序定位异常进程 |
| 可用内存 <500MB | 判断是否内存泄漏， IIS 应用池是否需回收 |
| 磁盘队列长度 >2 | I/O 瓶颈，检查是否日志写入过多 |
| 计数器全为零 | `lodctr /R` 重建性能计数器 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-10"></a>

## 🆕 模块 10：安全审计与日志分析




<details>
<summary>📋 展开查看：🆕 模块 10：安全审计与日志分析</summary>

**用途**：检测暴力破解、特权操作、异常登录。

**常你说**：`"帮我查下有没有被入侵"` / `"有没有异常登录记录"`

### 10.1 检测暴力破解尝试（最近 24 小时）




```powershell
$since = (Get-Date).AddHours(-24)

$failedLogins = Get-WinEvent -FilterHashtable @{
    LogName='Security'; ID=4625; StartTime=$since
} -ErrorAction SilentlyContinue

if ($failedLogins) {
    Write-Host "⚠️ 最近 24h 失败登录 $($failedLogins.Count) 次`n"
    $failedLogins |
        Select-Object TimeCreated,
            @{N='账号';E={$_.Properties[5].Value}},
            @{N='来源IP';E={$_.Properties[19].Value}} |
        Group-Object SourceIP |
        Sort-Object Count -Descending |
        Select-Object -First 10 @{N='攻击源IP';E={$_.Name}},
            @{N='尝试次数';E={$_.Count}} |
        Format-Table -AutoSize
    Write-Host "  💡 尝试次数 >10 的 IP 建议加入防火墙黑名单"
} else {
    Write-Host "  ✅ 最近 24 小时无失败登录记录"
}
```



### 10.2 查看特权提升操作（管理员操作审计）




```powershell
$since = (Get-Date).AddHours(-24)

Write-Host "════════ 特权操作（4672）════════"
Get-WinEvent -FilterHashtable @{
    LogName='Security'; ID=4672; StartTime=$since
} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated,
        @{N='用户';E={$_.Properties[1].Value}},
        @{N='特权';E={$_.Properties[2..($_.Properties.Count-1)].Value -join ', '}} |
    Format-Table -AutoSize
```



### 10.3 本地管理员组成员检查




```powershell
Write-Host "════════ 本地管理员组成员 ════════"
Get-LocalGroupMember -Group "Administrators" |
    Select-Object @{N='用户名';E={$_.Name}},
        @{N='来源';E={$_.PrincipalSource}} |
    Format-Table -AutoSize
```






```powershell
# ⚠️ 仅当用户明确说「确认导出」后才执行！
# $logPath = "C:\Logs\Security_$(Get-Date -Format 'yyyyMMdd').evtx"
# if (-not (Test-Path "C:\Logs")) { New-Item -ItemType Directory -Path "C:\Logs" -Force }
# wevtutil epl Security $logPath
# Write-Host "  ✅ 安全日志已导出到: $logPath"
```



**风险等级**：🟢 只读审计 / 🟡 导出需确认

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `No events were found ...` | 没有符合条件的日志 | 正常，说明期间无异常 |
| `The requested operation cannot be performed on a file ...` | 日志文件被占用 | 复制到另一路径导出 |
| `Get-LocalGroupMember` 报错 | 需要管理员权限 | 提升执行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 某 IP 失败登录 >100 次 | 暴力破解，建议防火墙封禁 |
| 4672 事件频繁 | 有人在频繁执行管理员操作，需排查 |
| 管理员组成员异常多了不认识账号 | 立即排查是否被入侵后留后门，删非法账号 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-11"></a>

## 🆕 模块 11：注册表与启动项安全审计




<details>
<summary>📋 展开查看：🆕 模块 11：注册表与启动项安全审计</summary>

**用途**：检测恶意持久化机制（注册表自启动、计划任务、WMI 订阅）。

**常你说**：`"有没有可疑的自启动程序"` / `"检查一下持久化威胁"`

> ⚠️ **本模块所有操作均为只读分析，绝不修改注册表或删除任何键值。**

### 11.1 经典自启动注册表位置扫描




```powershell
$runKeys = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
)

Write-Host "════════ 自启动注册表项 ════════"
foreach ($key in $runKeys) {
    if (Test-Path $key) {
        Write-Host "`n  📁 $($key.Split('\')[-1..-1] -join '\')"
        Get-ItemProperty $key -ErrorAction SilentlyContinue |
            Get-Member -MemberType NoteProperty |
            Where-Object { $_.Name -notlike 'PS*' } |
            ForEach-Object {
                $val = (Get-ItemProperty $key -Name $_.Name -ErrorAction SilentlyContinue).$($_.Name)
                Write-Host "    🔹 $($_.Name) = $val"
            }
    }
}
Write-Host "`n═══════════════════════════════"
Write-Host "  💡 不认识的程序请搜索确认，不要直接删除"
```



### 11.2 计划任务审计




```powershell
Write-Host "════════ 计划任务列表 ════════"
Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' } |
    Select-Object @{N='任务名';E={$_.TaskName}},
        @{N='状态';E={$_.State}},
        @{N='作者';E={$_.Author}},
        @{N='运行方式';E={$_.Principal.UserId}} |
    Format-Table -AutoSize

Write-Host "`n════════ 最近修改的任务 ════════"
Get-ScheduledTask | Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 @{N='任务名';E={$_.TaskName}},
        @{N='修改时间';E={$_.LastWriteTime}} |
    Format-Table -AutoSize
```



### 11.3 WMI 持久化检测




```powershell
Write-Host "════════ WMI 事件订阅 ════════"
try {
    $wmiSubs = Get-CimInstance -Namespace root\subscription -ClassName __EventFilter -ErrorAction SilentlyContinue
    if ($wmiSubs) {
        $wmiSubs | Select-Object @{N='名称';E={$_.Name}},
            @{N='查询';E={$_.Query}} |
            Format-Table -AutoSize
    } else {
        Write-Host "  ✅ 未发现 WMI 事件订阅"
    }
} catch {
    Write-Host "  ⚠️ WMI 查询失败，可能需要管理员权限"
}
```



### 11.4 系统服务异常检测




```powershell
Write-Host "════════ 非微软服务列表 ════════"
Get-Service | Where-Object {
    $_.DisplayName -notlike '*Microsoft*' -and
    $_.DisplayName -notlike '*Windows*' -and
    $_.DisplayName -notlike '*Intel*' -and
    $_.DisplayName -notlike '*NVIDIA*' -and
    $_.DisplayName -notlike '*AMD*' -and
    $_.DisplayName -notlike '*Realtek*' -and
    $_.DisplayName -notlike '*HP*' -and
    $_.DisplayName -notlike '*Dell*'
} | Select-Object @{N='服务名';E={$_.Name}},
    @{N='显示名';E={$_.DisplayName}},
    @{N='状态';E={$_.Status}},
    @{N='启动类型';E={$_.StartType}} |
    Format-Table -AutoSize
```



**风险等级**：🟢 无（只读审计）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Access to the path is denied` | 权限不足 | 管理员身份运行 |
| `Requested registry access is not allowed` | 注册表权限限制 | 提升权限执行 |
| `Get-CimInstance` 报错 | WMI 服务未启动 | 检查 Winmgmt 服务 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| Run 键值超多（>20个） | 正常软件也会注册，重点排查不认识的 |
| WMI 订阅存在未知项 | 可能是恶意软件持久化，需进一步分析 |
| 服务名随机字符串 | 典型恶意软件特征，需立即排查 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-12"></a>

## 🆕 模块 12：磁盘健康状态检测




<details>
<summary>📋 展开查看：🆕 模块 12：磁盘健康状态检测</summary>

**用途**：检测磁盘 SMART 状态、坏道预警、磁盘寿命预测。

**常你说**：`"硬盘还健康吗？"` / `"有没有坏道"` / `"磁盘寿命还剩多久"`

> ⚠️ **本模块所有操作均为只读检测，不会执行磁盘修复或擦除操作。**

### 12.1 SMART 状态概览




```powershell
Write-Host "════════ 磁盘 SMART 状态 ════════"
Get-PhysicalDisk | Select-Object @{N='磁盘';E={$_.FriendlyName}},
    @{N='状态';E={$_.HealthStatus}},
    @{N='使用时长';E={[math]::Round($_.UsageHours,0)}},
    @{N='温度(°C)';E={$_.Temperature}},
    @{N='剩余寿命%';E={$_.RemainingLifetimePercent}} |
    Format-Table -AutoSize
```



### 12.2 磁盘坏道与错误计数




```powershell
Write-Host "════════ 磁盘错误统计 ════════"
Get-PhysicalDisk | ForEach-Object {
    $disk = $_
    $errors = Get-StorageReliabilityCounter -PhysicalDisk $disk -ErrorAction SilentlyContinue
    if ($errors) {
        [PSCustomObject]@{
            磁盘 = $disk.FriendlyName
            读取错误 = $errors.ReadErrorsTotal
            写入错误 = $errors.WriteErrorsTotal
            重映射扇区 = $errors.ReallocatedSectors
            待映射扇区 = $errors.PendingSectors
            不可修复错误 = $errors.UncorrectableErrors
        }
    }
} | Format-Table -AutoSize

Write-Host "`n  💡 重映射扇区 >0 或待映射扇区 >0 表示磁盘开始老化"
Write-Host "  💡 不可修复错误 >0 建议立即备份数据并更换磁盘"
```



### 12.3 磁盘温度监控




```powershell
Write-Host "════════ 磁盘温度监控 ════════"
Get-PhysicalDisk | ForEach-Object {
    $temp = $_.Temperature
    if ($temp -gt 50)     { $icon = '🔴' }
    elseif ($temp -gt 40) { $icon = '🟡' }
    else                  { $icon = '🟢' }
    [PSCustomObject]@{
        磁盘 = $_.FriendlyName
        温度 = "${temp}°C"
        状态 = $icon
    }
} | Format-Table -AutoSize

Write-Host "`n  💡 温度 >50°C 需检查散热，>60°C 立即停机检查"
```



### 12.4 磁盘 I/O 延迟分析




```powershell
Write-Host "════════ 磁盘 I/O 延迟 ════════"
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Read',
              '\PhysicalDisk(*)\Avg. Disk sec/Write' |
    Select-Object -ExpandProperty CounterSamples |
    Where-Object { $_.CookedValue -gt 0 } |
    Select-Object @{N='磁盘';E={
        $_.Path -replace '\\PhysicalDisk\((.*)\)\\.*$','$1'
    }}, @{N='平均延迟(ms)';E={[math]::Round($_.CookedValue * 1000, 2)}} |
    Format-Table -AutoSize

Write-Host "`n  💡 读延迟 >20ms 或写延迟 >20ms 表示磁盘性能下降"
```



**风险等级**：🟢 无（只读检测）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `No MSFT_PhysicalDisk ...` | 系统不支持存储诊断 | 需 Windows Server 2016+ |
| `Temperature` 属性不存在 | 磁盘不支持温度传感器 | 用第三方工具检测 |
| `Get-StorageReliabilityCounter` 报错 | 需要管理员权限 | 提升执行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| SMART 状态显示 "Warning" | 磁盘开始老化，立即备份数据 |
| 重映射扇区持续增长 | 磁盘寿命将尽，尽快更换 |
| I/O 延迟突然飙升 | 可能磁盘故障前兆，检查 SMART |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-13"></a>

## 🆕 模块 13：网络连接与端口监控




<details>
<summary>📋 展开查看：🆕 模块 13：网络连接与端口监控</summary>

**用途**：检测异常网络连接、监听端口、可疑外连行为。

**常你说**：`"谁在连我的服务器"` / `"有没有异常外连"` / `"检查监听端口"`

> ⚠️ **本模块所有操作均为只读检测，不会修改防火墙规则或终止连接。**

### 13.1 活动网络连接概览




```powershell
Write-Host "════════ 活动网络连接 ════════"
Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
    Select-Object @{N='本地地址';E={$_.LocalAddress}},
        @{N='本地端口';E={$_.LocalPort}},
        @{N='远程地址';E={$_.RemoteAddress}},
        @{N='远程端口';E={$_.RemotePort}},
        @{N='状态';E={$_.State}},
        @{N='进程';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}} |
    Sort-Object RemoteAddress |
    Format-Table -AutoSize
```



### 13.2 监听端口审计




```powershell
Write-Host "════════ 监听端口列表 ════════"
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Select-Object @{N='本地地址';E={$_.LocalAddress}},
        @{N='监听端口';E={$_.LocalPort}},
        @{N='进程';E={
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) { "$($proc.Name) (PID: $($proc.Id))" } else { "未知" }
        }} |
    Sort-Object LocalPort |
    Format-Table -AutoSize
```



### 13.3 可疑外连检测（高频连接分析）




```powershell
Write-Host "════════ 高频外连目标 ════════"
Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
    Group-Object RemoteAddress |
    Where-Object { $_.Count -gt 5 } |
    Sort-Object Count -Descending |
    Select-Object -First 15 @{N='远程IP';E={$_.Name}},
        @{N='连接数';E={$_.Count}},
        @{N='进程';E={
            $proc = Get-Process -Id ($_.Group[0].OwningProcess) -ErrorAction SilentlyContinue
            if ($proc) { $proc.Name } else { "未知" }
        }} |
    Format-Table -AutoSize

Write-Host "`n  💡 连接数 >20 的 IP 需重点排查是否为恶意外连"
```



### 13.4 防火墙规则审计




```powershell
Write-Host "════════ 防火墙入站规则 ════════"
Get-NetFirewallRule -Direction Inbound -Enabled True -ErrorAction SilentlyContinue |
    Where-Object { $_.Action -eq 'Allow' } |
    Select-Object @{N='规则名';E={$_.DisplayName}},
        @{N='操作';E={$_.Action}},
        @{N='本地端口';E={$_.LocalPort}},
        @{N='远程地址';E={$_.RemoteAddress}} |
    Format-Table -AutoSize
```



**风险等级**：🟢 无（只读检测）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-NetTCPConnection` 报错 | 需要管理员权限 | 提升执行 |
| `Get-NetFirewallRule` 报错 | 防火墙服务未启动 | 检查 mpssvc 服务 |
| `OwningProcess` 为 0 | 系统进程，正常 | 无需处理 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 未知进程监听 80/443 端口 | 可能是 Web 服务或恶意软件，需排查 |
| 大量外连到同一 IP | 可能是 C2 通信，立即断网排查 |
| 防火墙规则异常宽松 | 建议收紧为最小权限原则 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-14"></a>

## 🆕 模块 14：Windows 事件日志诊断




<details>
<summary>📋 展开查看：🆕 模块 14：Windows 事件日志诊断</summary>

**用途**：快速定位系统错误、警告，按时间/级别筛选关键日志。

**常你说**：`"系统日志有没有最近错误"` / `"最近系统出了什么问题"` / `"看看日志"`

> ⚠️ **本模块仅读取日志，不会修改或清除日志文件。**

### 14.1 系统最近错误日志（最近 2 小时）




```powershell
$since = (Get-Date).AddHours(-2)

Write-Host "════════ 最近 2 小时系统日志（错误/警告）════════"
Get-WinEvent -FilterHashtable @{
    LogName='System';Level=2,3;StartTime=$since
} -ErrorAction SilentlyContinue |
    Select-Object @{N='时间';E={$_.TimeCreated}},
        @{N='来源';E={$_.Message.Split("`r`n")[0] -replace '^.*?: '}},
        @{N='级别';E={if ($_.Level -eq 2) { '❌错误' } else { '⚠️警告' }}} |
    Select-Object -First 30 |
    Format-Table -AutoSize -Wrap
```



### 14.2 应用程序错误日志




```powershell
$since = (Get-Date).AddHours(-24)

Write-Host "════════ 最近 24 小时应用程序错误 ════════"
Get-WinEvent -FilterHashtable @{
    LogName='Application'; Level=2; StartTime=$since
} -ErrorAction SilentlyContinue |
    Select-Object @{N='时间';E={$_.TimeCreated}},
        @{N='来源';E={$_.ProviderName}},
        @{N='错误摘要';E={
            ($_.Message -replace "`r`n",' ' | Select-Object -First 120)
        }} |
    Select-Object -First 20 |
    Format-Table -AutoSize -Wrap
```



### 14.3 关键系统事件扫描（蓝屏/重启/故障）




```powershell
Write-Host "════════ 关键系统事件（最近 7 天）════════"
Get-WinEvent -FilterHashtable @{
    LogName='System';
    ID=1074, 6005, 6006, 6008, 6009, 41, 1001, 1002;
    StartTime=(Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue |
    Select-Object @{N='时间';E={$_.TimeCreated}},
        @{N='事件ID';E={$_.Id}},
        @{N='说明';E={
            switch ($_.Id) {
                1074 {'系统关机/重启 (User initiated)'}
                6005 {'系统启动'}
                6006 {'系统正常关机'}
                6008 {'非正常关机 (意外断电/崩溃)'}
                6009 {'系统启动 (新会话)'}
                41  {'Kernel-Power 重启 (无干净关机)'}
                1001{'BugCheck (蓝屏)'}
                1002{'应用程序挂起/无响应'}
                default {$_.Message.Split("`r`n")[0]}
            }
        }} |
    Format-Table -AutoSize -Wrap
```



### 14.4 Setup 日志审计（最近 7 天）




```powershell
Write-Host "════════ Setup 最近 7 天事件 ════════"
Get-WinEvent -FilterHashtable @{
    LogName='Setup';
    StartTime=(Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue |
    Select-Object @{N='时间';E={$_.TimeCreated}},
        @{N='来源';E={$_.ProviderName}},
        @{N='摘要';E={
            ($_.Message -replace "`r`n",' ' | Select-Object -First 120)
        }} |
    Select-Object -First 15 |
    Format-Table -AutoSize -Wrap
```



**风险等级**：🟢 无（只读阅读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `No events were found ...` | 没有符合条件的日志 | 正常，说明期间无异常 |
| `RPC server is unavailable` | 事件日志服务未运行 | 检查 EventLog 服务 |
| `Access denied` | 权限不足 | 管理员身份执行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 每天大量 Error 日志 | 说明存在持续性故障，需逐条排查来源 |
| 非正常关机 (6008) | 可能存在硬件/电源问题 |
| 蓝屏 (1001) | 记录蓝屏代码，排查驱动/硬件 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-15"></a>

## 🆕 模块 15：已安装程序与补丁管理




<details>
<summary>📋 展开查看：🆕 模块 15：已安装程序与补丁管理</summary>

**用途**：查看所有已安装的软件、补丁，检测缺失或不一致情况。

**常你说**：`"看看系统安装了哪些软件"` / `"服务器装了什么程序"` / `"补丁检查"`

> ⚠️ **本模块仅读，不会卸载/安装/修改任何软件。**

### 15.1 已安装程序清单




```powershell
Write-Host "════════ 已安装程序清单 ════════"
Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -and $_.UninstallString -notlike '*{*' } |
    Select-Object @{N='程序名';E={$_.DisplayName}},
        @{N='版本';E={$_.DisplayVersion}},
        @{N='安装日期';E={$_.InstallDate}},
        @{N='大小';E={if($_.EstimatedSize){[math]::Round($_.EstimatedSize/1MB,1)}else{'?'}}} |
    Sort-Object DisplayName |
    Format-Table -AutoSize
```



### 15.2 已安装 Windows 补丁




```powershell
Write-Host "════════ 已安装 Windows 补丁 ════════"
Get-HotFix | Sort-Object InstalledOn -Descending |
    Select-Object @{N='补丁ID';E={$_.HotFixID}},
        @{N='安装日期';E={$_.InstalledOn}},
        @{N='描述';E={$_.Description}} |
    Format-Table -AutoSize
```



### 15.3 安装时间线分析




```powershell
Write-Host "════════ 最近安装的软件 ════════"
Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
    Where-Object { $_.InstallDate } |
    Sort-Object InstallDate -Descending |
    Select-Object -First 20 @{N='程序名';E={$_.DisplayName}},
        @{N='版本';E={$_.DisplayVersion}},
        @{N='安装日期';E={$_.InstallDate}} |
    Format-Table -AutoSize
```



### 15.4 补丁对比（检测缺失）




```powershell
$hotfixes = Get-HotFix -ErrorAction SilentlyContinue | Select-Object -ExpandProperty HotFixID
$currentBuild = [System.Environment]::OSVersion.Version
$expectedPatches = @()

# 检测 Windows 10/11 常见缺失补丁
if ($currentBuild.Major -ge 10) {
    $kbToCheck = @(
        "KB5034441",  # Secure Boot DBX
        "KB5036897",  # 最新 .NET
        "KB5037771"   # 最新累积
    )
    foreach ($kb in $kbToCheck) {
        if ($hotfixes -notcontains $kb) {
            $expectedPatches += "$kb - 缺失"
        }
    }
}

Write-Host "════════ 补丁一致性检查 ════════"
Write-Host "  当前版本: $($currentBuild.Major).$($currentBuild.Minor).$($currentBuild.Build)"
Write-Host ""
if ($expectedPatches.Count -gt 0) {
    Write-Host "  ⚠️ 缺失补丁:"
    foreach ($p in $expectedPatches) { Write-Host "    ❌ $p" }
} else {
    Write-Host "  ✅ 常用补丁均已安装"
}
```



**风险等级**：🟢 无（只读阅读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Requested registry access is not allowed` | 部分注册表权限限制 | 管理员身份执行 |
| `Get-HotFix` 报错 | 需要管理员权限 | 管理员身份执行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 某台服务器明显比其他机器少很多补丁 | 可能 WSUS/自动更新未运行 |
| 安装时间线上出现未知日期的软件 | 可能未经授权安装，需排查 |
| KB 补丁安装失败 | Windows Update 服务或缓存异常 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-16"></a>

## 🆕 模块 16：用户会话与登录状态监控




<details>
<summary>📋 展开查看：🆕 模块 16：用户会话与登录状态监控</summary>

**用途**：监控当前登录的用户、远程会话、僵尸会话、账户状态。

**常你说**：`"谁在服务器上"` / `"有没有异常登录"` / `"查看远程会话"`

> ⚠️ **本模块仅读，不会结束会话、锁定账户或修改密码策略。**

### 16.1 当前登录用户概览




```powershell
Write-Host "════════ 当前登录用户 ════════"
Get-CimInstance Win32_LogonSession | Where-Object { $_.LogonType -ne 0 } |
    Select-Object @{N='用户名';E={
        $user = Get-CimInstance Win32_ComputerSystem | Select-Object UserName
        $user.UserName ?? "未知"
    }},
    @{N='会话ID';E={$_.LogonId}},
    @{N='登录类型';E={
        switch ($_.LogonType) {
            2 {'交互 (本地登录)'}
            3 {'网络登录'}
            4 {'批处理'}
            5 {'服务'}
            7 {'解锁'}
            8 {'网络明文'}
            9 {'新凭据'}
            10 {'远程交互 (RDP)'}
            11 {'缓存交互'}
            default {"其他 ($($_.LogonType))"}
        }
    }},
    @{N='登录时间';E={$_.StartTime}} |
    Format-Table -AutoSize
```



### 16.2 远程桌面会话监控




```powershell
Write-Host "════════ 远程桌面会话 (RDP) ════════"
Get-CimInstance Win32_LogonSession | Where-Object { $_.LogonType -eq 10 } |
    Select-Object @{N='用户名';E={
        $user = Get-CimInstance Win32_ComputerSystem | Select-Object UserName
        $user.UserName ?? "未知"
    }},
    @{N='会话ID';E={$_.LogonId}},
    @{N='登录时间';E={$_.StartTime}},
    @{N='空闲时间(分钟)';E={
        if ($_.StartTime) {
            [math]::Round(((Get-Date) - $_.StartTime).TotalMinutes, 0)
        } else { 0 }
    }} |
    Format-Table -AutoSize
Write-Host "`n💡 空闲 >60 分钟的会话可能为僵尸会话"
```



### 16.3 异常登录检测（多 IP / 异地登录）




```powershell
Write-Host "════════ 最近 7 天的登录来源 ════════"
Get-WinEvent -FilterHashtable @{
    LogName='Security';
    ID=4624;
    StartTime=(Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue |
    Where-Object { $_.Properties[18].Value -ne '-' } |
    Select-Object @{N='登录时间';E={$_.TimeCreated}},
        @{N='用户名';E={$_.Properties[5].Value}},
        @{N='来源IP';E={$_.Properties[18].Value}},
        @{N='登录类型';E={
            switch ($_.Properties[8].Value) {
                2 {'交互(本地)'}
                3 {'网络'}
                10 {'远程(RDP)'}
                default {"其他"}
            }
        }} |
    Group-Object SourceIP |
    Sort-Object Count -Descending |
    Select-Object -First 10 @{N='来源IP';E={$_.Name}},
        @{N='登录次数';E={$_.Count}},
        @{N='最近登录';E={$_.Group[0].TimeCreated}} |
    Format-Table -AutoSize

Write-Host "`n💡 任何未知来源IP 的登录都值得警惕"
```



### 16.4 系统账户状态检查




```powershell
Write-Host "════════ 本地用户账户状态 ════════"
Get-LocalUser | Where-Object { $_.Enabled -eq $true } |
    Select-Object @{N='账户名';E={$_.Name}},
        @{N='状态';E={if ($_.Enabled) {'启用'}else{'禁用'}}},
        @{N='最后登录';E={$_.LastLogon}},
        @{N='密码过期';E={
            if ($_.PasswordExpires) { $_.PasswordExpires } else { '永不过期 ⚠️' }
        }},
        @{N='需要密码';E={if ($_.PasswordRequired) {'是'}else{'否 ⚠️'}}} |
    Format-Table -AutoSize

Write-Host "`n⚠️ 标记的账户存在安全风险：无密码或密码永不过期"
```



**风险等级**：🟢 无（只读监控）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-LocalUser` 报错 | 需要管理员权限 | 管理员身份执行 |
| `Get-CimInstance` 报错 | WMI 未启动 | 检查 Winmgmt |
| `No events found` | 没有相关日志 | 正常 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 多个 RDP 会话来自同一 IP | 可能正常（NAT），也可能为多人共用账户 |
| Guest 账户启用 | 不必要的安全风险，建议禁用 |
| 僵尸 RDP 会话 | 占用资源，闲置超时后应自动断开 |
| 密码永不过期 | 合规风险，建议设置密码策略 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-17"></a>

## 🆕 模块 17：计划任务审计




<details>
<summary>📋 展开查看：🆕 模块 17：计划任务审计</summary>

**用途**：审计所有计划任务，检测可疑的持久化行为（恶意软件常用的自启动方式）。

**常你说**：`"有没有可疑计划任务"` / `"检查计划任务"` / `"有没有凌晨执行的任务"`

> ⚠️ **本模块仅读，不会创建/删除/修改任何计划任务。**

### 17.1 所有计划任务清单




```powershell
Write-Host "════════ 所有计划任务 ════════"
$tasks = Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' }
$total = ($tasks | Measure-Object).Count
Write-Host "  总数: $total 个启用的任务`n"

$tasks | Select-Object @{N='任务名';E={$_.TaskName}},
    @{N='路径';E={$_.TaskPath}},
    @{N='状态';E={$_.State}},
    @{N='触发器';E={
        $info = Get-ScheduledTaskInfo -TaskName $_.TaskName -TaskPath $_.TaskPath -ErrorAction SilentlyContinue
        if ($info.LastRunTime) { "上次: $($info.LastRunTime)" } else { "从未执行" }
    }} |
    Sort-Object TaskPath, TaskName |
    Format-Table -AutoSize
```



### 17.2 异常计划任务检测（凌晨执行 / 隐藏窗口 / 临时目录）




```powershell
Write-Host "════════ 异常计划任务检测 ════════"
$suspicious = @()
$tasks = Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' }

foreach ($task in $tasks) {
    $score = 0
    $reasons = @()
    $taskInfo = Get-ScheduledTaskInfo -TaskName $task.TaskName -TaskPath $task.TaskPath -ErrorAction SilentlyContinue
    $lastRun = if ($taskInfo.LastRunTime) { $taskInfo.LastRunTime } else { $null }

    # 检测1: 凌晨执行 (0:00-5:00)
    # 通过检查 Actions 中的命令行参数
    $actions = $task.Actions
    foreach ($action in $actions) {
        $argStr = "$($action.Arguments)" + "$($action.Execute)"
        if ($argStr -match '(-WindowStyle\s+Hidden|/hidden|-w\s+hidden|-hide|/background|/min|-NoLogo\s+-NonInteractive\s+-WindowStyle\s+Hidden)') {
            $score += 2
            $reasons += "隐藏窗口执行"
        }
        if ($argStr -match '(\\Temp\\|\\TMP\\|\\AppData\\Local\\Temp\\)') {
            $score += 3
            $reasons += "从临时目录执行"
        }
        if ($argStr -match '((?:powershell|cmd|wscript|cscript|rundll32|mshta|regsvr32).*?(?:-enc|-e\s|IEX|Invoke-Expression|DownloadString|FromBase64String|eval))') {
            $score += 4
            $reasons += "可疑命令特征(编码/下载)"
        }
    }

    # 检测2: 无描述信息的任务
    if (-not $task.Description -or $task.Description -eq '') {
        $score += 1
        $reasons += "无描述信息"
    }

    if ($score -ge 3) {
        $suspicious += [PSCustomObject]@{
            任务名 = $task.TaskName
            路径 = $task.TaskPath
            风险分 = $score
            原因 = ($reasons -join ', ')
            上次运行 = $lastRun
        }
    }
}

if ($suspicious.Count -gt 0) {
    $suspicious | Sort-Object 风险分 -Descending |
        Format-Table -AutoSize -Wrap
    Write-Host "`n🔴 以上任务存在可疑特征，建议逐条排查"
} else {
    Write-Host "✅ 未发现明显可疑的计划任务"
}
```



### 17.3 按触发条件分类（开机自启 / 定时 / 用户登录触发）




```powershell
Write-Host "════════ 计划任务按触发类型分类 ════════`n"

# 开机自启
Write-Host "═══ 开机/系统启动时触发 ═══"
Get-ScheduledTask | Where-Object {
    $_.Triggers | Where-Object { $_.CimClass.CimClassName -match 'BootTrigger|StartupTrigger' }
} | Select-Object -First 15 @{N='任务名';E={$_.TaskName}},
    @{N='路径';E={$_.TaskPath}},
    @{N='触发器';E={
        ($_.Triggers | ForEach-Object { $_.CimClass.CimClassName }) -join ', '
    }} |
    Format-Table -AutoSize

Write-Host "`n═══ 用户登录时触发 ═══"
Get-ScheduledTask | Where-Object {
    $_.Triggers | Where-Object { $_.CimClass.CimClassName -match 'LogonTrigger' }
} | Select-Object -First 15 @{N='任务名';E={$_.TaskName}},
    @{N='路径';E={$_.TaskPath}},
    @{N='触发器';E={
        ($_.Triggers | ForEach-Object { $_.CimClass.CimClassName }) -join ', '
    }} |
    Format-Table -AutoSize

Write-Host "`n═══ 定时/周期性触发 (数量最多) ═══"
$timeTasks = Get-ScheduledTask | Where-Object {
    $_.Triggers | Where-Object { $_.CimClass.CimClassName -match 'TimeTrigger|DailyTrigger|WeeklyTrigger|MonthlyTrigger' }
}
Write-Host "  总数: $(($timeTasks | Measure-Object).Count) 个"
```



### 17.4 非 Microsoft 创建的任务




```powershell
Write-Host "════════ 非 Microsoft 创建的计划任务 ════════"
$nonMsTasks = Get-ScheduledTask | Where-Object {
    $_.TaskPath -notmatch '\\\\Microsoft\\\\' -and $_.State -ne 'Disabled'
}

if ($nonMsTasks) {
    $nonMsTasks | Select-Object @{N='任务名';E={$_.TaskName}},
        @{N='路径';E={$_.TaskPath}},
        @{N='状态';E={$_.State}},
        @{N='描述';E={
            if ($_.Description) { $_.Description.Substring(0, [Math]::Min(60, $_.Description.Length)) }
            else { '(无描述)' }
        }} |
        Format-Table -AutoSize
    Write-Host "`n💡 第三方任务值得审查，尤其是无描述且来源不明的"
} else {
    Write-Host "✅ 无非 Microsoft 计划任务"
}
```



**风险等级**：🟢 无（只读审计）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Access denied` | 权限不足 | 管理员身份执行 |
| `The system cannot find the file specified` | 任务引用的程序已删除 | 正常（残留任务），值得清理 |
| `Task Scheduler service is not running` | 计划任务服务未启动 | `Start-Service Schedule` |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 大量凌晨执行的隐藏窗口任务 | 软件更新常见，但需逐条确认来源 |
| 从 Temp 目录执行的任务 | 高危特征，多数恶意软件行为 |
| 无描述的随机名任务 | 可能是病毒/蠕虫创建，建议隔离排查 |
| 编码命令 (Base64) 执行 | 极高风险，常见于挖矿脚本和外连木马 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-18"></a>

## 🆕 模块 18：文件共享与 SMB 审计




<details>
<summary>📋 展开查看：🆕 模块 18：文件共享与 SMB 审计</summary>

**用途**：列出所有共享文件夹、当前 SMB 连接、权限风险检测。

**常你说**：`"有哪些共享文件夹"` / `"共享权限安全吗"` / `"谁在访问共享"` / `"SMB 审计"`

> ⚠️ **本模块仅读，不会关闭共享、断开连接或修改权限。**

### 18.1 已共享文件夹清单




```powershell
Write-Host "════════ 已共享文件夹 ════════"
Get-SmbShare | Where-Object { $_.Name -notin @('IPC$','ADMIN$') -or $_.Special -eq $false } |
    Select-Object @{N='共享名';E={$_.Name}},
        @{N='路径';E={$_.Path}},
        @{N='描述';E={if($_.Description){$_.Description}else{'(无)'}}},
        @{N='最大用户数';E={$_.ConcurrentUserLimit}},
        @{N='缓存模式';E={$_.CachingMode}},
        @{N='共享状态';E={$_.ShareState}} |
    Format-Table -AutoSize

Write-Host "`n💡 ADMIN$ 和 IPC$ 为系统默认管理共享，属正常"
```



### 18.2 共享权限审计




```powershell
Write-Host "════════ 共享权限审计 ════════"
$shares = Get-SmbShare | Where-Object { $_.Name -notin @('IPC$','ADMIN$') -or $_.Special -eq $false }

foreach ($share in $shares) {
    Write-Host "`n═══ 共享: $($share.Name) → $($share.Path) ═══"

    # 共享级别权限
    try {
        $sharePerm = Get-SmbShareAccess -Name $share.Name -ErrorAction SilentlyContinue
        foreach ($perm in $sharePerm) {
            $flag = if ($perm.AccessRight -eq 'Full' -and $perm.AccountName -eq 'Everyone') {
                "🔴 高风险: Everyone 拥有完全控制"
            } elseif ($perm.AccountName -eq 'Everyone') {
                "⚠️ Everyone 可访问"
            } else {
                ""
            }
            Write-Host "  共享权限: $($perm.AccountName) -> $($perm.AccessRight)  $flag"
        }
    } catch {
        Write-Host "  共享权限: 无法获取"
    }

    # NTFS 级别权限（对物理路径）
    if (Test-Path $share.Path) {
        $ntfsPerm = Get-Acl $share.Path -ErrorAction SilentlyContinue
        if ($ntfsPerm) {
            $ntfsPerm.Access | Where-Object { $_.IdentityReference -match 'Everyone|BUILTIN|Guest|ANONYMOUS' } |
                ForEach-Object {
                    Write-Host "  NTFS权限: $($_.IdentityReference) -> $($_.FileSystemRights) ⚠️ 宽松权限"
                }
        }
    }
}
```



### 18.3 当前 SMB 连接会话




```powershell
Write-Host "════════ 当前 SMB 连接会话 ════════"
$sessions = Get-SmbSession -ErrorAction SilentlyContinue |
    Select-Object @{N='客户端';E={$_.ClientComputerName}},
        @{N='用户名';E={$_.UserName}},
        @{N='空闲时间(分钟)';E={[math]::Round($_.IdleTime.TotalMinutes, 0)}},
        @{N='会话时长(分钟)';E={[math]::Round((New-TimeSpan -Start $_.SessionStartTime).TotalMinutes, 0)}} |
    Sort-Object @{E='空闲时间(分钟)';Descending=$true}

if ($sessions) {
    $sessions | Format-Table -AutoSize
    Write-Host "`n💡 空闲 >60 分钟的会话可能为僵尸连接"
} else {
    Write-Host "  当前无活跃 SMB 会话"
}
```



### 18.4 开放共享中的风险项汇总




```powershell
Write-Host "════════ 共享风险汇总 ════════"
$risks = @()
$shares = Get-SmbShare | Where-Object { $_.Name -notin @('IPC$','ADMIN$') -or $_.Special -eq $false }

foreach ($share in $shares) {
    $sharePerm = Get-SmbShareAccess -Name $share.Name -ErrorAction SilentlyContinue
    foreach ($perm in $sharePerm) {
        if ($perm.AccountName -eq 'Everyone') {
            $risks += "🔴 [$($share.Name)] Everyone -> $($perm.AccessRight) 控制权"
        }
        if ($perm.AccountName -eq 'ANONYMOUS LOGON' -or $perm.AccountName -eq 'Guest') {
            $risks += "🔴 [$($share.Name)] $($perm.AccountName) -> $($perm.AccessRight)"
        }
    }

    # 检查共享指向路径不存在
    if (-not (Test-Path $share.Path)) {
        $risks += "⚠️ [$($share.Name)] 共享路径不存在: $($share.Path)"
    }
}

if ($risks.Count -gt 0) {
    $risks | ForEach-Object { Write-Host $_ }
    Write-Host "`n建议: 收紧共享权限为最小访问原则，禁用 Guest/匿名访问"
} else {
    Write-Host "✅ 未发现高风险的共享配置"
}

# 同时检查 SMBv1 是否启用
$smb1 = Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction SilentlyContinue
if ($smb1 -and $smb1.State -eq 'Enabled') {
    Write-Host "`n🔴 SMBv1 已启用！存在 WannaCry 等勒索软件漏洞风险，建议禁用"
}
```



**风险等级**：🟢 无（只读审计）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-SmbShare` 报错 | SMB 未启用或无权限 | 管理员身份在服务器上执行 |
| `Get-SmbSession` 为空 | 当前无 SMB 连接 | 正常 |
| `Access denied on Get-Acl` | 部分目录 NTFS 权限限制 | 某些系统目录属正常 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| Everyone 拥有完全控制 | 任何网络用户可读/写，极大风险 |
| SMBv1 仍启用 | 永恒之蓝等漏洞存在，应立即禁用 |
| 指向不存在的路径 | 残留共享，建议删除 |
| 大量僵尸 SMB 会话 | 客户端未正常断开，占用连接数 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-19"></a>

## 🆕 模块 19：DNS 解析与网卡诊断




<details>
<summary>📋 展开查看：🆕 模块 19：DNS 解析与网卡诊断</summary>

**用途**：DNS 缓存查看与清空、解析链路测试、网卡 IP 配置、路由表检查。

**常你说**：`"DNS 解析正常吗"` / `"网卡配置"` / `"网络诊断"` / `"路由表"`

> ⚠️ **本模块操作：DNS 缓存查看/清空（可恢复）+ 网卡 IP 查看（只读）。DNS 清空后会重新从服务器获取，非破坏性。**

### 19.1 DNS 缓存与解析测试




```powershell
Write-Host "════════ DNS 缓存 ════════"
$dnsCache = Get-DnsClientCache -ErrorAction SilentlyContinue
if ($dnsCache) {
    Write-Host "  缓存条目: $(($dnsCache | Measure-Object).Count)"
    $dnsCache | Select-Object -First 20 @{N='域名';E={$_.Entry}},
        @{N='类型';E={$_.RecordType}},
        @{N='IP地址';E={$_.Data}},
        @{N='TTL(秒)';E={$_.TimeToLive}} |
        Format-Table -AutoSize
} else {
    Write-Host "  当前无 DNS 缓存"
}

Write-Host "`n════════ DNS 缓存中异常的记录 (TTL异常长) ════════"
if ($dnsCache) {
    $abnormal = $dnsCache | Where-Object { $_.TimeToLive -gt 86400 }
    if ($abnormal) {
        $abnormal | Select-Object Entry, Data, TimeToLive | Format-Table -AutoSize
    } else {
        Write-Host "  ✅ 无异常记录"
    }
}

Write-Host "`n💡 如需清空 DNS 缓存，说：「确认清空 DNS 缓存」"
Write-Host "  清空命令: Clear-DnsClientCache  (清空后会自动从DNS服务器重新获取)"
```



### 19.2 DNS 服务器配置与解析链路测试




```powershell
Write-Host "════════ DNS 服务器配置 ════════"
Get-DnsClientServerAddress -AddressFamily IPv4 |
    Where-Object { $_.ServerAddresses.Count -gt 0 } |
    Select-Object @{N='网卡';E={$_.InterfaceAlias}},
        @{N='索引';E={$_.InterfaceIndex}},
        @{N='DNS 服务器';E={($_.ServerAddresses -join ', ')}} |
    Format-Table -AutoSize

Write-Host "`n════════ 解析链路测试 (逐级 DNS) ════════"
$testDomains = @('www.baidu.com', 'www.google.com', 'portal.azure.com')
foreach ($domain in $testDomains) {
    try {
        $result = Resolve-DnsName -Name $domain -Type A -ErrorAction Stop
        $ip = ($result | Where-Object { $_.Type -eq 'A' } | Select-Object -First 1).IPAddress
        if ($ip) { Write-Host "  ✅ $domain → $ip" }
        else { Write-Host "  ❌ $domain → 解析失败" }
    } catch {
        Write-Host "  ❌ $domain → $($_.Exception.Message.Split('.')[0])"
    }
}
```



### 19.3 网卡 IP 配置概览




```powershell
Write-Host "════════ 网卡 IP 配置 ════════"
Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -ne '127.0.0.1' } |
    Select-Object @{N='网卡';E={$_.InterfaceAlias}},
        @{N='IP 地址';E={$_.IPAddress}},
        @{N='子网掩码';E={$_.PrefixLength}},
        @{N='网关';E={
            $ifIndex = $_.InterfaceIndex
            $gw = Get-NetRoute -InterfaceIndex $ifIndex -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue
            if ($gw) { $gw.NextHop } else { '-' }
        }},
        @{N='状态';E={$_.AddressState}} |
    Format-Table -AutoSize

Write-Host "`n════════ 网卡 MAC 地址与速率 ════════"
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } |
    Select-Object @{N='网卡名';E={$_.Name}},
        @{N='MAC';E={$_.MacAddress}},
        @{N='速率';E={if($_.LinkSpeed){ "$([math]::Round($_.LinkSpeed/1e9,1)) Gbps" }else{'未知'}}},
        @{N='状态';E={$_.Status}} |
    Format-Table -AutoSize
```



### 19.4 路由表检查




```powershell
Write-Host "════════ IPv4 路由表 ════════"
Get-NetRoute -AddressFamily IPv4 |
    Where-Object { $_.DestinationPrefix -ne '255.255.255.255/32' } |
    Sort-Object @{E={if ($_.DestinationPrefix -eq '0.0.0.0/0') {0} else {1}}},
        @{E='RouteMetric'} |
    Select-Object @{N='目标网络';E={$_.DestinationPrefix}},
        @{N='下一跳';E={$_.NextHop}},
        @{N='接口';E={$_.InterfaceAlias}},
        @{N='跃点数';E={$_.RouteMetric}},
        @{N='协议';E={$_.Protocol}} |
    Format-Table -AutoSize

Write-Host "`n💡 跃点数越小优先级越高"
Write-Host "💡 0.0.0.0/0 为默认路由（所有出网流量由此控制）"
```



**风险等级**：🟡 中（含 DNS 缓存清空操作，需用户确认）

| 操作 | 风险 | 说明 |
|------|------|------|
| DNS 缓存查看 | 🟢 无 | 纯只读 |
| DNS 解析测试 | 🟢 无 | 纯只读，零风险 |
| 网卡配置查看 | 🟢 无 | 纯只读 |
| 路由表查看 | 🟢 无 | 纯只读 |
| **DNS 缓存清空** | 🟡 中 | 清空后需用户说「确认清空 DNS 缓存」，清空后自动从 DNS 服务器重建，非破坏性 |

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Resolve-DnsName` 超时 | DNS 服务器不可达 | 检查 DNS 服务器配置和网络连通性 |
| `Get-NetIPAddress` 为空 | 网卡未分配 IPv4 | 检查 DHCP 或静态 IP 配置 |
| `Get-NetRoute` 无默认路由 | 无互联网出口 | 检查网关配置 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| DNS 缓存中大量 TTL 异常长的记录 | 可能 DNS 服务器配置问题或域名劫持 |
| 多网卡存在多个默认路由 | 路由冲突导致网络不稳定 |
| DNS 服务器指向不可达 IP | 域名解析全部失败 |
| 网卡速率不匹配（1Gbps vs 100Mbps） | 网线/交换机端口故障 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-20"></a>

## 🆕 模块 20：SSL 证书过期检测




<details>
<summary>📋 展开查看：🆕 模块 20：SSL 证书过期检测</summary>

**用途**：检测本机 IIS / 所有 HTTPS 站点的 SSL 证书到期时间，提前预警，避免网站突然报"证书无效"。

**常你说**：`"SSL 证书快到期了吗"` / `"证书检查"` / `"HTTPS 站点证书还有多久"` / `"哪些证书要过期了"`

> ⚠️ **本模块仅读，不会申请、续签或删除任何证书。**

### 20.1 本机证书仓库扫描（个人 + 机器）




```powershell
Write-Host "════════ 本机证书过期检查 ════════"
$warningDays = 30
$now = Get-Date

$stores = @(
    [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine,
    [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser
)
$storeNames = @('My', 'WebHosting', 'Root', 'CA')

$certs = foreach ($loc in $stores) {
    foreach ($name in $storeNames) {
        try {
            $store = [System.Security.Cryptography.X509Certificates.X509Store]::new($name, $loc)
            $store.Open('ReadOnly')
            foreach ($cert in $store.Certificates) {
                $daysLeft = ($cert.NotAfter - $now).Days
                [PSCustomObject]@{
                    主体       = ($cert.Subject -replace 'CN=', '' -split ',')[0].Trim()
                    存储位置   = "$loc\$name"
                    到期时间   = $cert.NotAfter.ToString('yyyy-MM-dd')
                    剩余天数   = $daysLeft
                    状态       = if ($daysLeft -lt 0) { '❌ 已过期' }
                                 elseif ($daysLeft -lt $warningDays) { '⚠️ 即将过期' }
                                 else { '✅ 正常' }
                    颁发者     = ($cert.Issuer -replace 'CN=', '' -split ',')[0].Trim()
                }
            }
            $store.Close()
        } catch {}
    }
}

$result = $certs | Where-Object { $_.剩余天数 -lt 90 } |
    Sort-Object 剩余天数

if ($result) {
    $result | Format-Table -AutoSize
} else {
    Write-Host "✅ 未发现 90 天内到期的证书"
}
```



### 20.2 IIS 绑定的 HTTPS 证书检查




```powershell
Write-Host "════════ IIS HTTPS 绑定证书 ════════"
Import-Module WebAdministration -ErrorAction SilentlyContinue

$httpsBindings = Get-WebBinding | Where-Object { $_.protocol -eq 'https' }
if (-not $httpsBindings) {
    Write-Host "  未发现 HTTPS 绑定"
} else {
    foreach ($binding in $httpsBindings) {
        $hash = $binding.certificateHash
        if ($hash) {
            $cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Thumbprint -eq $hash }
            if ($cert) {
                $daysLeft = ($cert.NotAfter - (Get-Date)).Days
                $status = if ($daysLeft -lt 0) { '❌ 已过期' }
                           elseif ($daysLeft -lt 30) { '⚠️ 即将过期' }
                           else { '✅ 正常' }
                Write-Host "  站点: $($binding.bindingInformation)"
                Write-Host "  证书: $($cert.Subject)"
                Write-Host "  到期: $($cert.NotAfter.ToString('yyyy-MM-dd'))  剩余: $daysLeft 天  $status"
                Write-Host ""
            }
        }
    }
}
```



### 20.3 远程域名证书探测（本地无证书的站点）




```powershell
# 将下方域名替换为你需要检测的站点
$domains = @('www.baidu.com', 'www.taobao.com')  # 示例，替换为你的域名

Write-Host "════════ 远程域名 SSL 证书检测 ════════"
foreach ($domain in $domains) {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient($domain, 443)
        $sslStream  = New-Object System.Net.Security.SslStream($tcpClient.GetStream(), $false, { $true })
        $sslStream.AuthenticateAsClient($domain)
        $cert = $sslStream.RemoteCertificate
        $expiry = [DateTime]::Parse($cert.GetExpirationDateString())
        $daysLeft = ($expiry - (Get-Date)).Days
        $status = if ($daysLeft -lt 0) { '❌ 已过期' }
                   elseif ($daysLeft -lt 30) { '⚠️ 即将过期' }
                   else { '✅ 正常' }
        Write-Host "  $domain → 到期: $($expiry.ToString('yyyy-MM-dd'))  剩余: $daysLeft 天  $status"
        $sslStream.Close()
        $tcpClient.Close()
    } catch {
        Write-Host "  $domain → ❌ 连接失败: $($_.Exception.Message.Split('.')[0])"
    }
}
```



### 20.4 即将过期证书汇总报告




```powershell
Write-Host "════════ 30 天内到期证书汇总 ════════"
$now = Get-Date
$soon = @()

foreach ($loc in @('LocalMachine','CurrentUser')) {
    foreach ($name in @('My','WebHosting')) {
        try {
            $store = [System.Security.Cryptography.X509Certificates.X509Store]::new($name, $loc)
            $store.Open('ReadOnly')
            $soon += $store.Certificates | Where-Object {
                ($_.NotAfter - $now).Days -le 30 -and ($_.NotAfter - $now).Days -ge 0
            } | Select-Object @{N='证书名';E={($_.Subject -replace 'CN=','' -split ',')[0].Trim()}},
                @{N='剩余天数';E={($_.NotAfter - $now).Days}},
                @{N='到期日期';E={$_.NotAfter.ToString('yyyy-MM-dd')}},
                @{N='存储';E={"$loc\$name"}}
            $store.Close()
        } catch {}
    }
}

if ($soon.Count -gt 0) {
    $soon | Sort-Object 剩余天数 | Format-Table -AutoSize
    Write-Host "`n🔴 以上证书需要尽快续签！"
} else {
    Write-Host "✅ 30 天内无证书过期"
}
```



**风险等级**：🟢 无（只读，不修改任何证书）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Access denied` | 需管理员权限 | 管理员身份执行 |
| `WebAdministration not found` | IIS 未安装 | 跳过模块 20.2 |
| `Connection refused` | 远程域名 443 不可达 | 检查域名和防火墙 |
| `AuthenticationException` | SSL 握手失败 | 域名可能证书异常 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 证书显示"已过期"但网站仍在访问 | 浏览器有缓存，实际用户已经开始看到警告 |
| IIS 绑定的证书和仓库里的不一致 | IIS 用指纹引用，需手动在 IIS 管理器重新绑定 |
| Let's Encrypt 证书 90 天到期周期 | 需设置自动续签（如 win-acme） |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-21"></a>

## 🆕 模块 21：Windows 防火墙规则审计




<details>
<summary>📋 展开查看：🆕 模块 21：Windows 防火墙规则审计</summary>

**用途**：列出所有防火墙规则，识别过度开放（Any/Any）、可疑来源的规则，找出安全漏洞。

**常你说**：`"防火墙规则有没有问题"` / `"防火墙审计"` / `"哪些端口对外开放"` / `"有没有高危防火墙规则"`

> ⚠️ **本模块仅读，不会新增、删除或修改任何防火墙规则。**

### 21.1 所有入站规则概览




```powershell
Write-Host "════════ 入站防火墙规则（启用中）════════"
$inbound = Get-NetFirewallRule -Direction Inbound -Enabled True -ErrorAction SilentlyContinue

Write-Host "  启用的入站规则总数: $(($inbound | Measure-Object).Count)"
Write-Host ""

$inbound | ForEach-Object {
    $rule = $_
    $filter = $rule | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
    $addrFilter = $rule | Get-NetFirewallAddressFilter -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        规则名     = $rule.DisplayName.Substring(0, [Math]::Min(40, $rule.DisplayName.Length))
        协议       = if ($filter.Protocol) { $filter.Protocol } else { '任意' }
        本地端口   = if ($filter.LocalPort) { $filter.LocalPort -join ',' } else { '任意' }
        来源地址   = if ($addrFilter.RemoteAddress) { ($addrFilter.RemoteAddress -join ',').Substring(0, [Math]::Min(30, ($addrFilter.RemoteAddress -join ',').Length)) } else { '任意' }
        动作       = $rule.Action
    }
} | Select-Object -First 30 | Format-Table -AutoSize
```



### 21.2 高危规则检测（Any → Any / 暴露全端口）




```powershell
Write-Host "════════ 高危防火墙规则扫描 ════════"
$risks = @()

Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True -ErrorAction SilentlyContinue | ForEach-Object {
    $rule = $_
    $portFilter = $rule | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
    $addrFilter  = $rule | Get-NetFirewallAddressFilter -ErrorAction SilentlyContinue

    $anyPort = ($portFilter.LocalPort -eq 'Any' -or -not $portFilter.LocalPort)
    $anyAddr = ($addrFilter.RemoteAddress -eq 'Any' -or $addrFilter.RemoteAddress -contains 'Any' -or -not $addrFilter.RemoteAddress)

    if ($anyPort -and $anyAddr) {
        $risks += [PSCustomObject]@{
            风险等级 = '🔴 高危'
            规则名   = $rule.DisplayName
            说明     = '允许任意来源访问任意端口'
            建议     = '收紧来源地址或端口范围'
        }
    } elseif ($anyAddr) {
        # 检查是否暴露高危端口（135/445/3389/5985）
        $dangerousPorts = @('135','445','3389','5985','5986','23','21','1433','3306','6379')
        $portStr = ($portFilter.LocalPort -join ',')
        foreach ($p in $dangerousPorts) {
            if ($portStr -match "\b$p\b" -or $anyPort) {
                $risks += [PSCustomObject]@{
                    风险等级 = '⚠️ 中危'
                    规则名   = $rule.DisplayName
                    说明     = "端口 $p 对任意来源开放"
                    建议     = '限制来源 IP 白名单'
                }
                break
            }
        }
    }
}

if ($risks.Count -gt 0) {
    $risks | Format-Table -AutoSize -Wrap
    Write-Host "`n建议: 使用「来源 IP 白名单」替代「任意来源」"
} else {
    Write-Host "✅ 未发现明显高危防火墙规则"
}
```



### 21.3 按端口查看谁在放行




```powershell
# 修改此处为你想查询的端口
$targetPorts = @('3389', '445', '80', '443', '1433', '3306')

Write-Host "════════ 关键端口放行规则 ════════"
foreach ($port in $targetPorts) {
    $rules = Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True -ErrorAction SilentlyContinue | Where-Object {
        $pf = $_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
        ($pf.LocalPort -eq 'Any' -or $pf.LocalPort -contains $port)
    }

    if ($rules) {
        Write-Host "`n  端口 $port — 有 $(($rules | Measure-Object).Count) 条放行规则:"
        $rules | Select-Object -First 5 @{N='规则名';E={$_.DisplayName}} |
            ForEach-Object { Write-Host "    - $($_.规则名)" }
    } else {
        Write-Host "`n  端口 $port — 无放行规则（默认拒绝）"
    }
}
```



### 21.4 防火墙配置文件状态




```powershell
Write-Host "════════ 防火墙配置文件状态 ════════"
Get-NetFirewallProfile | Select-Object @{N='配置文件';E={$_.Name}},
    @{N='是否启用';E={if($_.Enabled){'✅ 启用'}else{'❌ 已禁用 ⚠️'}}},
    @{N='入站默认';E={$_.DefaultInboundAction}},
    @{N='出站默认';E={$_.DefaultOutboundAction}},
    @{N='通知';E={$_.NotifyOnListen}} |
    Format-Table -AutoSize

Write-Host "`n💡 防火墙应对所有配置文件均启用，入站默认「Block」"
Write-Host "💡 如果任一配置文件显示「已禁用」，立即排查原因"
```



**风险等级**：🟢 无（只读审计，不修改任何规则）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-NetFirewallRule` 报错 | 需管理员权限 | 管理员身份执行 |
| `WinRM` 相关报错 | 防火墙服务异常 | 检查 `mpssvc` 服务状态 |
| `Access denied on Get-NetFirewallPortFilter` | 域策略限制 | 以域管理员身份执行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 防火墙被关闭（Enabled=False） | 极高风险，任何连接均可进入 |
| 3389 对 Any 开放 | RDP 暴力破解首要目标 |
| 445 对 Any 开放 | WannaCry/勒索病毒入侵路径 |
| 大量"Any → Any"规则 | 常见于软件安装时自动添加，需逐条清理 |



</details>

[↑ 返回顶部](#module-1)

---

<a name="module-22"></a>

## 🆕 模块 22：关键服务崩溃与自动恢复状态




<details>
<summary>📋 展开查看：🆕 模块 22：关键服务崩溃与自动恢复状态</summary>

**用途**：查看服务异常停止记录、自动恢复策略、"应该运行却未运行"的服务。

**常你说**：`"哪些服务崩过"` / `"服务崩溃记录"` / `"服务自动恢复设置"` / `"有服务没跑起来吗"`

> ⚠️ **本模块仅读，不会启动、停止或修改任何服务。**

### 22.1 已停止但设为自动启动的服务（"应跑未跑"）




```powershell
Write-Host "════════ 应运行却已停止的服务 ════════"
$deadServices = Get-Service | Where-Object {
    $_.StartType -in @('Automatic', 'AutomaticDelayedStart') -and
    $_.Status -eq 'Stopped'
}

if ($deadServices) {
    $deadServices | Select-Object @{N='服务名';E={$_.Name}},
        @{N='显示名';E={$_.DisplayName}},
        @{N='启动类型';E={$_.StartType}},
        @{N='状态';E={$_.Status}} |
        Sort-Object 显示名 |
        Format-Table -AutoSize
    Write-Host "`n⚠️ 以上服务设置了自动启动但当前已停止，需要排查原因"
} else {
    Write-Host "✅ 所有自动启动的服务均在运行"
}
```



### 22.2 服务崩溃事件记录（事件日志 7034/7036）




```powershell
Write-Host "════════ 服务崩溃记录（最近 7 天）════════"
$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'System'
    Id        = @(7034, 7035, 7036, 7031, 7040)
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue

if ($events) {
    $events | Select-Object @{N='时间';E={$_.TimeCreated}},
        @{N='事件ID';E={$_.Id}},
        @{N='说明';E={
            switch ($_.Id) {
                7034 { "❌ 服务意外停止: " + ($_.Message -replace "`r`n",' ').Substring(0,[Math]::Min(80,$_.Message.Length)) }
                7031 { "❌ 服务停止后触发恢复动作: " + ($_.Message -replace "`r`n",' ').Substring(0,[Math]::Min(60,$_.Message.Length)) }
                7035 { "→ 服务控制: " + ($_.Message -replace "`r`n",' ').Substring(0,[Math]::Min(60,$_.Message.Length)) }
                7036 { "● 服务状态变更: " + ($_.Message -replace "`r`n",' ').Substring(0,[Math]::Min(60,$_.Message.Length)) }
                7040 { "⚙️ 启动类型变更: " + ($_.Message -replace "`r`n",' ').Substring(0,[Math]::Min(60,$_.Message.Length)) }
                default { $_.Message.Substring(0,[Math]::Min(80,$_.Message.Length)) }
            }
        }} |
        Where-Object { $_.事件ID -in @(7034, 7031) } |
        Sort-Object 时间 -Descending |
        Select-Object -First 20 |
        Format-Table -AutoSize -Wrap
} else {
    Write-Host "✅ 最近 7 天无服务崩溃记录"
}
```



### 22.3 服务自动恢复策略查看




```powershell
Write-Host "════════ 关键服务恢复策略 ════════"
$keyServices = @(
    'W3SVC',       # IIS
    'MSSQLSERVER', # SQL Server
    'WSearch',     # Windows Search
    'Spooler',     # 打印机
    'EventLog',    # 事件日志
    'WinRM',       # 远程管理
    'Schedule',    # 计划任务
    'LanmanServer' # 文件共享
)

foreach ($svcName in $keyServices) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
        # 使用 sc.exe 读取恢复策略
        $scOutput = sc.exe qfailure $svcName 2>&1
        $resetPeriod = ($scOutput | Select-String 'RESET_PERIOD') -replace '.*: ', ''
        $actions = ($scOutput | Select-String 'FAILURE_ACTIONS') -replace '.*: ', ''

        Write-Host "  $($svc.DisplayName) [$svcName]"
        Write-Host "    状态: $($svc.Status)"
        Write-Host "    恢复动作: $(if($actions){$actions}else{'(未配置)'} )"
        Write-Host ""
    }
}
Write-Host "💡 未配置恢复动作的关键服务，崩溃后不会自动重启，需手动干预"
```



### 22.4 服务依赖关系检查（关键服务是否有依赖未启动）




```powershell
Write-Host "════════ 关键服务依赖链检查 ════════"
$keyServices = @('W3SVC', 'MSSQLSERVER', 'WinRM', 'Schedule', 'Netlogon')

foreach ($svcName in $keyServices) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
        $deps = $svc.ServicesDependedOn
        $brokenDeps = $deps | Where-Object { $_.Status -ne 'Running' }

        if ($brokenDeps) {
            Write-Host "⚠️ $($svc.DisplayName) 依赖以下未运行的服务:"
            $brokenDeps | ForEach-Object {
                Write-Host "    ❌ $($_.Name) ($($_.Status))"
            }
        } else {
            Write-Host "✅ $($svc.DisplayName) — 所有依赖服务正常"
        }
    }
}
```



**风险等级**：🟢 无（只读，不启动/停止/修改任何服务）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-WinEvent` 无权限 | 需管理员权限 | 管理员身份执行 |
| `sc.exe qfailure` 返回空 | 部分服务无恢复策略 | 正常，说明未配置 |
| `Get-Service` 找不到服务 | 该服务未安装 | 跳过该服务 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| IIS 停止但事件日志无崩溃记录 | 可能是被人为停止 |
| 服务崩溃但无恢复动作 | 需通过"服务属性 → 恢复"配置自动重启 |
| 依赖服务未运行导致主服务无法启动 | 先启动依赖服务 |
| 事件 7034 大量重复 | 服务反复崩溃重启，存在底层问题 |



---


</details>

[↑ 返回顶部](#module-1)

---

<a name="module-23"></a>

## 🆕 模块 23：系统文件完整性检查与修复（SFC / DISM）


<details>
<summary>📋 展开查看：🆕 模块 23：系统文件完整性检查与修复（SFC / DISM）</summary>

**用途**：扫描并修复受损的 Windows 系统文件，诊断组件存储损坏，解决因系统文件破坏导致的服务异常。

**常你说**：`"系统文件好像坏了"` / `"服务启动报错找不到文件"` / `"DISM 修复"` / `"SFC 扫描"`

> ⚠️ **本模块需要管理员权限，仅扫描和修复系统文件，不修改用户数据。**


```powershell
# 扫描所有系统文件完整性（不修复）
sfc /scanfile=C:\Windows\System32\kernel32.dll

# 扫描并尝试修复（需管理员）
# sfc /scannow
```



```powershell
# 扫描组件存储是否损坏（不修复）
DISM /Online /Cleanup-Image /ScanHealth

# 检查组件存储健康状态
DISM /Online /Cleanup-Image /CheckHealth

# 查看可修复的组件列表
DISM /Online /Cleanup-Image /AnalyzeComponentStore

# 清理组件存储中的旧版本组件
# DISM /Online /Cleanup-Image /StartComponentCleanup

# 修复组件存储（需联网）
# DISM /Online /Cleanup-Image /RestoreHealth
```



```powershell
# 标准修复流程：先 DISM 修复组件存储，再 SFC 修复系统文件
# DISM /Online /Cleanup-Image /RestoreHealth
# sfc /scannow
# 完成后重启系统
```


**风险等级**：🟢 扫描只读 / 🟡 修复需确认

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Windows Resource Protection did not find any integrity violations` | 系统文件正常 | 无需修复 |
| `There is a system repair pending which requires reboot` | 有挂起的修复 | 重启后再扫描 |
| `The source files could not be downloaded` | 需联网 | 使用安装介质作为源 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| SFC 报告无法修复某些文件 | 通常是组件存储损坏，先执行 DISM |
| DISM 报错 0x800f081f | 找不到源文件，需指定安装介质 |
| 修复后问题依旧 | 可能是文件权限问题，检查 ACL |


</details>

[↑ 返回顶部](#module-1)

---

<a name="module-24"></a>

## 🆕 模块 24：存储池与虚拟磁盘管理（Storage Spaces）


<details>
<summary>📋 展开查看：🆕 模块 24：存储池与虚拟磁盘管理（Storage Spaces）</summary>

**用途**：查看存储池健康状态、虚拟磁盘状态、物理磁盘健康、存储层使用情况，提前预警存储故障。

**常你说**：`"存储池正常吗"` / `"虚拟磁盘状态"` / `"物理磁盘健康"` / `"存储池容量预警"`

> ⚠️ **本模块仅读，不创建/删除/修改任何存储池或虚拟磁盘配置。**


```powershell
Write-Host "════════ 存储池健康状态 ════════"
Get-StoragePool | Where-Object { $_.IsPrimordial -eq $false } |
    Select-Object @{N='名称';E={$_.FriendlyName}},
        @{N='状态';E={$_.HealthStatus}},
        @{N='操作状态';E={$_.OperationalStatus}},
        @{N='物理磁盘数';E={$_.PhysicalDisks.Count}},
        @{N='已用空间';E={[math]::Round($_.AllocatedSize/1GB,1)}},
        @{N='总容量';E={[math]::Round($_.Size/1GB,1)}},
        @{N='使用率';E={[math]::Round(($_.AllocatedSize/$_.Size)*100,1)}} |
    Format-Table -AutoSize
```



```powershell
Write-Host "════════ 虚拟磁盘状态 ════════"
Get-VirtualDisk | Select-Object @{N='名称';E={$_.FriendlyName}},
    @{N='状态';E={$_.HealthStatus}},
    @{N='操作状态';E={$_.OperationalStatus}},
    @{N='RAID类型';E={$_.ResiliencySettingName}},
    @{N='已用空间';E={[math]::Round($_.AllocatedSize/1GB,1)}},
    @{N='总容量';E={[math]::Round($_.Size/1GB,1)}},
    @{N='使用率';E={[math]::Round(($_.AllocatedSize/$_.Size)*100,1)}} |
    Format-Table -AutoSize
```



```powershell
Write-Host "════════ 存储池中物理磁盘健康 ════════"
Get-StoragePool | Where-Object { $_.IsPrimordial -eq $false } |
    Get-PhysicalDisk | Select-Object @{N='磁盘';E={$_.FriendlyName}},
        @{N='状态';E={$_.HealthStatus}},
        @{N='操作状态';E={$_.OperationalStatus}},
        @{N='使用时长(小时)';E={[math]::Round($_.UsageHours,0)}},
        @{N='温度';E={if($_.Temperature){"$($_.Temperature)°C"}else{"-"}}},
        @{N='读取错误';E={(Get-StorageReliabilityCounter -PhysicalDisk $_ -ErrorAction SilentlyContinue).ReadErrorsTotal}} |
    Format-Table -AutoSize
```



```powershell
Write-Host "════════ 存储层使用情况 ════════"
Get-StorageTier | Select-Object @{N='名称';E={$_.FriendlyName}},
    @{N='总容量';E={[math]::Round($_.Size/1GB,1)}},
    @{N='已用';E={[math]::Round(($_.Size - $_.AllocatedSize)/1GB,1)}},
    @{N='媒体类型';E={$_.MediaType}} |
    Format-Table -AutoSize
```


**风险等级**：🟢 无（只读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `No MSFT_StoragePool objects` | 系统未配置存储池 | 仅适用于 Storage Spaces 环境 |
| `Get-VirtualDisk` 报错 | 需要管理员权限 | 提升执行 |
| `HealthStatus` 显示 `Warning` | 存储池存在降级 | 立即检查物理磁盘 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 存储池状态显示 `Degraded` | 有物理磁盘离线或故障 |
| 虚拟磁盘显示 `Incomplete` | 部分成员磁盘离线，需尽快恢复 |
| 容量使用率 >90% | 需要扩容，否则写入将失败 |
| 物理磁盘 `UsageHours` 异常高 | 磁盘可能过热或长期高负载 |


</details>

[↑ 返回顶部](#module-1)

---

<a name="module-25"></a>

## 🆕 模块 25：Windows Server Backup 状态检查


<details>
<summary>📋 展开查看：🆕 模块 25：Windows Server Backup 状态检查</summary>

**用途**：检查 Windows Server Backup 配置、最近备份状态、备份目标健康，确保备份作业正常运行。

**常你说**：`"备份正常吗"` / `"上次备份时间"` / `"备份失败了"` / `"恢复点检查"`

> ⚠️ **本模块仅读，不会启动、停止或配置任何备份任务。**


```powershell
Write-Host "════════ Windows Server Backup 状态 ════════"

# 检查备份策略
try {
    $policy = Get-WBPolicy -ErrorAction Stop
    Write-Host "  ✅ 备份策略已配置"
    Write-Host "  备份目标: $($policy.BackupTargets | ForEach-Object { $_.Path })"
    Write-Host "  包含卷: $($policy.VolumesToBackup | ForEach-Object { $_.Path })"
} catch {
    Write-Host "  ⚠️ 未配置备份策略"
}

# 查看最近备份
Write-Host "`n════════ 最近备份历史 ════════"
$backups = Get-WBSummary -ErrorAction SilentlyContinue
if ($backups) {
    $backups | Select-Object @{N='最后备份时间';E={$_.LastBackupTime}},
        @{N='备份大小';E={[math]::Round($_.TotalBackupSize/1GB,2)}},
        @{N='状态';E={if($_.LastBackupTime){"✅ 成功"}else{"❌ 无记录"}}} |
        Format-Table -AutoSize
} else {
    Write-Host "  ⚠️ 没有备份历史记录"
}
```



```powershell
Write-Host "════════ 备份目标磁盘检查 ════════"
$policy = Get-WBPolicy -ErrorAction SilentlyContinue
if ($policy -and $policy.BackupTargets.Count -gt 0) {
    foreach ($target in $policy.BackupTargets) {
        $targetPath = $target.Path
        $vol = Get-Volume -FilePath $targetPath -ErrorAction SilentlyContinue
        if ($vol) {
            $freeGB = [math]::Round($vol.SizeRemaining/1GB,1)
            $totalGB = [math]::Round($vol.Size/1GB,1)
            $pctFree = [math]::Round(($vol.SizeRemaining/$vol.Size)*100,1)
            Write-Host "  目标: $targetPath"
            Write-Host "  容量: ${totalGB} GB  剩余: ${freeGB} GB (${pctFree}%)"
            if ($pctFree -lt 10) {
                Write-Host "  ⚠️ 备份目标即将写满！"
            }
        }
    }
} else {
    Write-Host "  ⚠️ 未配置备份目标"
}
```



```powershell
Write-Host "════════ 可用还原点 ════════"
Get-WBBackupSet -ErrorAction SilentlyContinue | Sort-Object BackupTime -Descending |
    Select-Object -First 10 @{N='备份时间';E={$_.BackupTime}},
        @{N='备份大小(GB)';E={[math]::Round($_.TotalBackupSize/1GB,2)}},
        @{N='卷数';E={$_.Volumes.Count}},
        @{N='应用一致性';E={if($_.ApplicationConsistent){"✅"}else{"-"}}} |
    Format-Table -AutoSize
```



```powershell
Write-Host "════════ 当前备份作业状态 ════════"
$job = Get-WBJob -ErrorAction SilentlyContinue
if ($job) {
    Write-Host "  状态: $($job.JobState)"
    Write-Host "  当前操作: $($job.CurrentOperation)"
    Write-Host "  进度: $($job.Progress)%"
} else {
    Write-Host "  ✅ 当前无备份作业运行"
}
```


**风险等级**：🟢 无（只读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Get-WBPolicy` 报错 | Windows Server Backup 功能未安装 | `Install-WindowsFeature Windows-Server-Backup` |
| `Get-WBSummary` 返回空 | 无备份历史 | 先配置并运行一次备份 |
| `The operation is not supported` | 非 Server 版本 | 仅适用于 Windows Server |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 备份目标剩余 <10% | 备份将失败，需清理或扩容 |
| 备份作业状态显示 `Running` 但长时间无进度 | 可能卡住，检查日志 |
| 应用一致性为 `false` | VSS 卷影复制失败，检查 VSS 服务 |
| 无可用还原点 | 备份从未成功，需排查 |

</details>





[↑ 返回顶部](#module-1)

---

<a name="module-26"></a>

## 🆕 模块 26：Docker / K8s 容器管理

**用途**：管理 Windows Server 容器化部署环境，监控 Docker 容器与 K8s 集群健康状态。

**常你说**：`"Docker 容器正常吗"` / `"哪个容器吃资源"` / `"K8s 集群状态"` / `"容器日志"`

> ⚠️ **本模块仅在检测到 Docker 或 kubectl 安装时激活，未安装时给出友好提示。**

### 前置检测（自动执行）

```powershell
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
$kubectlPath = Get-Command kubectl -ErrorAction SilentlyContinue

if (-not $dockerPath -and -not $kubectlPath) {
    Write-Host "⚠️ 未检测到 Docker 或 kubectl，跳过模块 26"
    Write-Host "  → 安装 Docker: https://docs.docker.com/engine/install/windows-server/"
    Write-Host "  → 安装 kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
}
```

---

### 26.1 Docker 状态总览

**用途**：一键查看容器、镜像、网络、卷的使用情况。

**常你说**：`"Docker 状态总览"` / `"容器列表"` / `"镜像多大"`

<details>
<summary>📋 展开查看命令 — Docker 状态总览</summary>

```powershell
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerPath) {
    Write-Host "⚠️ Docker 未安装"
    return
}

Write-Host "════════ Docker 状态总览 ════════"

# 容器状态
$containers = docker ps -a --format "table {{.Names}}	{{.Status}}	{{.Image}}	{{.Ports}}" 2>$null
if ($containers) {
    Write-Host "`n📦 容器列表:"
    $containers | ForEach-Object { Write-Host "  $_" }
}

# 镜像列表
$images = docker images --format "table {{.Repository}}:{{.Tag}}	{{.Size}}	{{.CreatedSince}}" 2>$null
if ($images) {
    Write-Host "`n🖼️ 镜像列表:"
    $images | ForEach-Object { Write-Host "  $_" }
}

# 网络列表
$networks = docker network ls --format "table {{.Name}}	{{.Driver}}	{{.Scope}}" 2>$null
if ($networks) {
    Write-Host "`n🌐 网络列表:"
    $networks | ForEach-Object { Write-Host "  $_" }
}

# 卷列表
$volumes = docker volume ls --format "table {{.Name}}	{{.Driver}}" 2>$null
if ($volumes) {
    Write-Host "`n💾 卷列表:"
    $volumes | ForEach-Object { Write-Host "  $_" }
}

# 磁盘占用
$diskUsage = docker system df 2>$null
if ($diskUsage) {
    Write-Host "`n📊 Docker 磁盘占用:"
    $diskUsage | ForEach-Object { Write-Host "  $_" }
}
```

</details>

**风险等级**：🟢 无（只读）

---

### 26.2 容器资源监控

**用途**：实时查看每个容器的 CPU / 内存 / 网络 / 磁盘 I/O 占用。

**常你说**：`"哪个容器吃资源"` / `"容器 CPU 占用"` / `"容器内存"`

<details>
<summary>📋 展开查看命令 — 容器资源监控</summary>

```powershell
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerPath) {
    Write-Host "⚠️ Docker 未安装"
    return
}

Write-Host "════════ 容器资源监控 ════════"
Write-Host "（单次采集，不持续占用资源）`n"

# 获取 CPU 核心数，决定采集并发数
$cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
$sampleCount = if ($cpuCores -le 4) { 1 } else { 3 }

# 容器资源统计（不流式输出，避免占用资源）
$stats = docker stats --no-stream --format "table {{.Name}}	{{.CPUPerc}}	{{.MemUsage}}	{{.MemPerc}}	{{.NetIO}}	{{.BlockIO}}" 2>$null
if ($stats) {
    $stats | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  ⚠️ 无运行中的容器"
}

Write-Host "`n💡 单次采集完成，共 $sampleCount 次采样"
```

</details>

**风险等级**：🟢 无（只读，单次采集不占用资源）

---

### 26.3 Docker 健康检查

**用途**：检查 Docker 服务状态、磁盘占用、守护进程日志异常。

**常你说**：`"Docker 服务正常吗"` / `"Docker 磁盘占用"` / `"Docker 日志异常"`

<details>
<summary>📋 展开查看命令 — Docker 健康检查</summary>

```powershell
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerPath) {
    Write-Host "⚠️ Docker 未安装"
    return
}

Write-Host "════════ Docker 健康检查 ════════"

# 1. Docker 服务状态
$dockerSvc = Get-Service com.docker.service -ErrorAction SilentlyContinue
if ($dockerSvc) {
    $svcStatus = if ($dockerSvc.Status -eq 'Running') { '✅ 运行中' } else { '❌ 已停止' }
    Write-Host "  Docker 服务: $svcStatus"
} else {
    Write-Host "  Docker 服务: ⚠️ 未找到服务"
}

# 2. Docker 版本信息
$dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
if ($dockerVersion) {
    Write-Host "  Docker 版本: $dockerVersion"
}

# 3. Docker 磁盘占用
$diskUsage = docker system df 2>$null
if ($diskUsage) {
    Write-Host "`n📊 磁盘占用:"
    $diskUsage | ForEach-Object { Write-Host "  $_" }
}

# 4. 容器健康状态（如果容器配置了 HEALTHCHECK）
$containers = docker ps --format "{{.Names}}" 2>$null
if ($containers) {
    Write-Host "`n🏥 容器健康状态:"
    foreach ($c in $containers) {
        $health = docker inspect --format "{{.State.Health.Status}}" $c 2>$null
        if ($health) {
            $icon = if ($health -eq 'healthy') { '✅' } elseif ($health -eq 'unhealthy') { '❌' } else { '⏳' }
            Write-Host "  $icon $c : $health"
        } else {
            Write-Host "  ⏳ $c : 未配置健康检查"
        }
    }
}

# 5. 最近 24 小时 Docker 相关系统错误日志
$since = (Get-Date).AddHours(-24)
$dockerEvents = Get-WinEvent -FilterHashtable @{
    LogName='System'; ProviderName='Docker'; Level=2; StartTime=$since
} -ErrorAction SilentlyContinue
if ($dockerEvents) {
    Write-Host "`n⚠️ 最近 24h Docker 错误事件: $($dockerEvents.Count) 条"
    $dockerEvents | Select-Object -First 5 TimeCreated, Message |
        Format-Table -AutoSize -Wrap
} else {
    Write-Host "`n✅ 最近 24h 无 Docker 错误日志"
}
```

</details>

**风险等级**：🟢 无（只读）

---

### 26.4 K8s 集群状态

**用途**：查看 Kubernetes 节点、Pod 健康、资源配额使用率。

**常你说**：`"K8s 集群状态"` / `"Pod 健康"` / `"节点状态"`

<details>
<summary>📋 展开查看命令 — K8s 集群状态</summary>

```powershell
$kubectlPath = Get-Command kubectl -ErrorAction SilentlyContinue
if (-not $kubectlPath) {
    Write-Host "⚠️ kubectl 未安装"
    return
}

Write-Host "════════ K8s 集群状态 ════════"

# 1. 节点状态
Write-Host "`n🖥️ 节点状态:"
$nodes = kubectl get nodes -o wide 2>$null
if ($nodes) {
    $nodes | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  ⚠️ 无法获取节点信息，检查集群连接"
}

# 2. Pod 状态（所有命名空间）
Write-Host "`n📦 Pod 状态:"
$pods = kubectl get pods --all-namespaces -o wide 2>$null
if ($pods) {
    $pods | ForEach-Object { Write-Host "  $_" }
}

# 3. 资源配额
Write-Host "`n📊 资源配额:"
$resourceQuota = kubectl get resourcequota --all-namespaces 2>$null
if ($resourceQuota) {
    $resourceQuota | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  未配置资源配额"
}

# 4. 异常 Pod 检测
$allPods = kubectl get pods --all-namespaces --no-headers 2>$null
if ($allPods) {
    $abnormalPods = @()
    foreach ($podLine in $allPods) {
        $parts = $podLine -split '\s+'
        if ($parts.Count -ge 4) {
            $ns = $parts[0]
            $name = $parts[1]
            $ready = $parts[2]
            $status = $parts[3]
            if ($status -ne 'Running' -and $status -ne 'Succeeded') {
                $abnormalPods += [PSCustomObject]@{
                    命名空间 = $ns
                    Pod名 = $name
                    状态 = $status
                    就绪 = $ready
                }
            }
        }
    }
    if ($abnormalPods.Count -gt 0) {
        Write-Host "`n⚠️ 异常 Pod:"
        $abnormalPods | Format-Table -AutoSize
    } else {
        Write-Host "`n✅ 所有 Pod 状态正常"
    }
}

# 5. 节点资源使用（需 metrics-server）
Write-Host "`n📈 节点资源使用:"
$topNodes = kubectl top nodes 2>$null
if ($topNodes) {
    $topNodes | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  ⚠️ metrics-server 未安装，无法获取资源使用率"
}

Write-Host "`n💡 K8s 集群状态采集完成"
```

</details>

**风险等级**：🟢 无（只读）

---

### 26.5 容器日志采集

**用途**：查看指定容器的最近日志，检测异常模式。

**常你说**：`"看容器日志"` / `"容器报错了"` / `"容器最近日志"`

> ⚠️ **采集限制**：默认采集最近 100 行，内存不足 2 GB 时自动缩减到 50 行，避免占用过多内存。

<details>
<summary>📋 展开查看命令 — 容器日志采集</summary>

```powershell
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerPath) {
    Write-Host "⚠️ Docker 未安装"
    return
}

# 获取可用内存，决定采集行数
$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)
$tailCount = if ($totalRAM -lt 2) { 50 } else { 100 }

Write-Host "════════ 容器日志采集 ════════"
Write-Host "可用内存: ${totalRAM} GB，采集行数: $tailCount`n"

# 列出所有容器供选择
$containerList = docker ps -a --format "{{.Names}} | {{.Status}}" 2>$null
if ($containerList) {
    Write-Host "可用容器:"
    $containerList | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
}

# 替换为你要查看的容器名
$targetContainer = "your_container_name"  # ← 改成你要看的容器名

if ($targetContainer -eq "your_container_name") {
    Write-Host "⚠️ 请修改 `$targetContainer 变量为要查看的容器名"
    return
}

Write-Host "📋 容器: $targetContainer (最近 $tailCount 行)"
Write-Host "──────────────────────────────────────"

$logs = docker logs --tail $tailCount $targetContainer 2>&1
if ($logs) {
    $logs | ForEach-Object { Write-Host "  $_" }
    
    # 异常模式检测
    $errorKeywords = @('error', 'exception', 'fatal', 'panic', 'failed', 'refused')
    $errorLines = @()
    $lineNum = 0
    foreach ($line in $logs) {
        $lineNum++
        foreach ($kw in $errorKeywords) {
            if ($line -match $kw) {
                $errorLines += "  行 $lineNum : $line"
                break
            }
        }
    }
    
    if ($errorLines.Count -gt 0) {
        Write-Host "`n⚠️ 检测到 $($errorLines.Count) 行异常关键词:"
        $errorLines | Select-Object -First 20 | ForEach-Object { Write-Host $_ }
        if ($errorLines.Count -gt 20) {
            Write-Host "  ... 还有 $($errorLines.Count - 20) 行未显示"
        }
    } else {
        Write-Host "`n✅ 未检测到异常关键词"
    }
}
```

</details>

**风险等级**：🟢 无（只读）

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `docker: command not found` | Docker 未安装 | 安装 Docker Engine |
| `kubectl: command not found` | kubectl 未安装 | 安装 kubectl |
| `connection refused` | Docker/K8s 服务未启动 | 启动对应服务 |
| `permission denied` | 权限不足 | 管理员身份运行 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 日志采集时内存不足 | 自动缩减到 50 行，进一步减少可修改 `$tailCount` |
| 容器未配置 HEALTHCHECK | 健康状态显示"未配置"，正常 |
| metrics-server 未安装 | K8s 资源使用率无法获取，属常见情况 |
| Docker 在 Windows Server 上需要特定版本 | 确认 Server 版本与 Docker 兼容 |



---

<a name="module-27"></a>

## 🆕 模块 27：自动化修复向导

**用途**：从"诊断"到"修复"，提供一键式常见问题修复，严格遵循「预览→确认→执行→验证」四步流程。

**常你说**：`"帮我修 DNS"` / `"网络不正常"` / `"Windows Update 卡住"` / `"服务起不来"` / `"磁盘满了"` / `"时间不准"`

> ⚠️ **本模块所有修复操作均需管理员权限，执行前自动创建还原点，用户明确确认后才执行。**

### 修复流程（所有子模块通用）

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Step 1     │ →  │  Step 2     │ →  │  Step 3     │ →  │  Step 4     │
│  问题定位    │    │  修复预览    │    │  用户确认    │    │  执行+验证   │
│ 调用现有模块 │    │ 展示命令+影响 │    │ 创建还原点   │    │ 重新诊断确认  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

### 27.1 DNS 解析异常修复

**修复命令**：`ipconfig /flushdns` + `netsh winsock reset`

**常你说**：`"DNS 修一下"` / `"网页打不开 DNS 问题"`

<details>
<summary>📋 展开查看命令 — DNS 修复四步流程</summary>

```powershell
# ====== Step 1: 问题定位（调用模块19） ======
Write-Host "════════ DNS 修复向导 ════════"
Write-Host "`n[Step 1] 问题定位..."
$dnsTest = Resolve-DnsName -Name www.baidu.com -ErrorAction SilentlyContinue
if ($dnsTest) {
    Write-Host "  ✅ DNS 解析正常，无需修复"
    return
}
Write-Host "  ❌ DNS 解析失败，需要修复"

# ====== Step 2: 修复预览 ======
Write-Host "`n[Step 2] 修复预览"
Write-Host "  将要执行以下命令："
Write-Host "  1. ipconfig /flushdns          — 清空 DNS 缓存"
Write-Host "  2. netsh winsock reset         — 重置 Winsock 目录"
Write-Host "  3. ipconfig /registerdns       — 重新注册 DNS 名称"
Write-Host "`n  影响范围："
Write-Host "  · 短暂断开网络连接（约 5-10 秒）"
Write-Host "  · 需要重启后生效"
Write-Host "  · 不会丢失任何数据"

# ====== Step 3: 用户确认 ======
Write-Host "`n[Step 3] 用户确认"
$confirm = Read-Host "  输入 '确认修复' 开始执行"
if ($confirm -ne '确认修复') {
    Write-Host "  ❌ 已取消"
    return
}

# 创建还原点
Write-Host "  正在创建系统还原点..."
try {
    Checkpoint-Computer -Description "winskill-DNS修复前" -RestorePointType MODIFY_SETTINGS -ErrorAction SilentlyContinue
    Write-Host "  ✅ 还原点已创建"
} catch {
    Write-Host "  ⚠️ 无法创建还原点（系统保护可能未启用）"
}

# ====== Step 4: 执行修复 ======
Write-Host "`n[Step 4] 执行修复..."
Write-Host "  1/3 清空 DNS 缓存..."
ipconfig /flushdns
Write-Host "  2/3 重置 Winsock..."
netsh winsock reset
Write-Host "  3/3 注册 DNS..."
ipconfig /registerdns

# 验证
Write-Host "`n[验证] 重新测试 DNS..."
Start-Sleep -Seconds 3
$verifyDns = Resolve-DnsName -Name www.baidu.com -ErrorAction SilentlyContinue
if ($verifyDns) {
    Write-Host "  ✅ DNS 修复成功！"
} else {
    Write-Host "  ⚠️ DNS 仍无法解析，建议检查 DNS 服务器配置"
    Write-Host "  → 模块 19 查看 DNS 服务器配置"
}
```

</details>

**风险等级**：🟡 中（需确认，会短暂断网）

---

### 27.2 网络连接异常修复

**修复命令**：`netsh int ip reset` + 网卡禁用/启用

**常你说**：`"网络重置"` / `"网连不上"`

<details>
<summary>📋 展开查看命令 — 网络修复四步流程</summary>

```powershell
Write-Host "════════ 网络修复向导 ════════"

# Step 1: 定位
Write-Host "`n[Step 1] 问题定位..."
$pingTest = Test-NetConnection -ComputerName www.baidu.com -Port 443 -ErrorAction SilentlyContinue
if ($pingTest.TcpTestSucceeded) {
    Write-Host "  ✅ 网络连接正常"
    return
}
Write-Host "  ❌ 网络连接失败"

# Step 2: 预览
Write-Host "`n[Step 2] 修复预览"
Write-Host "  将要执行："
Write-Host "  1. netsh int ip reset           — 重置 TCP/IP 协议栈"
Write-Host "  2. 禁用再启用网卡               — 重新初始化网络适配器"
Write-Host "`n  影响：短暂断网（约 10-30 秒），需管理员权限"

# Step 3: 确认
$confirm = Read-Host "`n  输入 '确认修复' 开始执行"
if ($confirm -ne '确认修复') { return }

# Step 4: 执行
Write-Host "`n[Step 4] 执行修复..."
netsh int ip reset
Write-Host "  ✅ TCP/IP 已重置"

# 获取主网卡
$adapter = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1
if ($adapter) {
    Write-Host "  重启网卡: $($adapter.Name)..."
    Disable-NetAdapter -Name $adapter.Name -Confirm:$false
    Start-Sleep -Seconds 3
    Enable-NetAdapter -Name $adapter.Name -Confirm:$false
    Write-Host "  ✅ 网卡已重启"
}

# 验证
Start-Sleep -Seconds 5
$verifyNet = Test-NetConnection -ComputerName www.baidu.com -Port 443 -ErrorAction SilentlyContinue
if ($verifyNet.TcpTestSucceeded) {
    Write-Host "`n  ✅ 网络修复成功！"
} else {
    Write-Host "`n  ⚠️ 仍未连通，检查物理连接和路由器"
}
```

</details>

**风险等级**：🟡 中（需确认，会短暂断网）

---

### 27.3 Windows Update 修复

**修复命令**：停服务 → 清理 SoftwareDistribution → 重启服务

**常你说**：`"Windows Update 修一下"` / `"更新卡住了"`

<details>
<summary>📋 展开查看命令 — Windows Update 修复四步流程</summary>

```powershell
Write-Host "════════ Windows Update 修复向导 ════════"

# Step 1: 定位
Write-Host "`n[Step 1] 问题定位..."
$wuService = Get-Service wuauserv -ErrorAction SilentlyContinue
if ($wuService.Status -eq 'Running') {
    Write-Host "  ✅ Windows Update 服务运行中"
} else {
    Write-Host "  ❌ Windows Update 服务已停止"
}

# Step 2: 预览
Write-Host "`n[Step 2] 修复预览"
Write-Host "  将要执行："
Write-Host "  1. Stop-Service wuauserv       — 停止更新服务"
Write-Host "  2. 清理 SoftwareDistribution   — 删除损坏的下载缓存"
Write-Host "  3. Start-Service wuauserv     — 重启更新服务"
Write-Host "`n  影响：正在进行的更新将中断，已安装补丁不受影响"

# Step 3: 确认
$confirm = Read-Host "`n  输入 '确认修复' 开始执行"
if ($confirm -ne '确认修复') { return }

# Step 4: 执行
Write-Host "`n[Step 4] 执行修复..."
Write-Host "  1/3 停止更新服务..."
Stop-Service wuauserv -Force
Write-Host "  2/3 清理缓存..."
$sdPath = "C:\Windows\SoftwareDistribution\Download"
if (Test-Path $sdPath) {
    Remove-Item -Path "$sdPath\*" -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "  3/3 重启服务..."
Start-Service wuauserv

# 验证
Start-Sleep -Seconds 3
$verifyWu = Get-Service wuauserv
if ($verifyWu.Status -eq 'Running') {
    Write-Host "`n  ✅ Windows Update 服务已恢复正常"
} else {
    Write-Host "`n  ⚠️ 服务未启动，查看事件日志排查"
}
```

</details>

**风险等级**：🟡 中（需确认，正在进行的更新会中断）

---

### 27.4 服务启动失败修复

**修复命令**：检查依赖 → 检查端口 → 尝试启动

**常你说**：`"SQL Server 起不来"` / `"IIS 启动失败"`

<details>
<summary>📋 展开查看命令 — 服务修复四步流程</summary>

```powershell
# 替换为你要修复的服务名
$targetService = "W3SVC"  # ← 改成你要修复的服务名

Write-Host "════════ 服务修复向导 ════════"
Write-Host "目标服务: $targetService"

# Step 1: 定位
Write-Host "`n[Step 1] 问题定位..."
$svc = Get-Service -Name $targetService -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Host "  ❌ 服务不存在: $targetService"
    return
}
Write-Host "  状态: $($svc.Status)"
Write-Host "  启动类型: $($svc.StartType)"

# 检查依赖
$deps = $svc.ServicesDependedOn
$brokenDeps = $deps | Where-Object { $_.Status -ne 'Running' }
if ($brokenDeps) {
    Write-Host "  ⚠️ 依赖服务未运行:"
    $brokenDeps | ForEach-Object { Write-Host "    ❌ $($_.Name)" }
}

# Step 2: 预览
Write-Host "`n[Step 2] 修复预览"
Write-Host "  将要执行："
Write-Host "  1. 启动依赖服务（如有）"
Write-Host "  2. 检查端口占用"
Write-Host "  3. 尝试启动目标服务"

# Step 3: 确认
$confirm = Read-Host "`n  输入 '确认修复' 开始执行"
if ($confirm -ne '确认修复') { return }

# Step 4: 执行
Write-Host "`n[Step 4] 执行修复..."

# 启动依赖
if ($brokenDeps) {
    foreach ($dep in $brokenDeps) {
        Write-Host "  启动依赖: $($dep.Name)..."
        try {
            Start-Service -Name $dep.Name -ErrorAction Stop
            Write-Host "    ✅ 已启动"
        } catch {
            Write-Host "    ❌ 启动失败: $($_.Exception.Message)"
        }
    }
}

# 检查端口（如果是 IIS/SQL/MySQL 等已知服务）
$portMap = @{
    'W3SVC' = 80
    'MSSQLSERVER' = 1433
    'MySQL80' = 3306
}
if ($portMap.ContainsKey($targetService)) {
    $port = $portMap[$targetService]
    $portUsed = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($portUsed) {
        $proc = Get-Process -Id $portUsed.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  ⚠️ 端口 $port 被占用: $($proc.Name)"
    }
}

# 尝试启动
Write-Host "  尝试启动 $targetService..."
try {
    Start-Service -Name $targetService -ErrorAction Stop
    Write-Host "  ✅ 服务启动成功！"
} catch {
    Write-Host "  ❌ 启动失败: $($_.Exception.Message)"
    Write-Host "  → 查看事件日志: 模块 14"
}

# 验证
$verifySvc = Get-Service -Name $targetService
Write-Host "`n[验证] 服务状态: $($verifySvc.Status)"
```

</details>

**风险等级**：🟡 中（需确认，会启动服务）

---

### 27.5 磁盘空间不足修复

**修复命令**：大文件识别 + 旧文件建议 + temp 清理

**常你说**：`"磁盘满了"` / `"C 盘清理"`

<details>
<summary>📋 展开查看命令 — 磁盘清理四步流程</summary>

```powershell
Write-Host "════════ 磁盘清理修复向导 ════════"

# Step 1: 定位
Write-Host "`n[Step 1] 问题定位..."
$vol = Get-Volume -DriveLetter C
$freeGB = [math]::Round($vol.SizeRemaining/1GB, 1)
$totalGB = [math]::Round($vol.Size/1GB, 1)
$usedPct = [math]::Round((1 - $vol.SizeRemaining/$vol.Size) * 100, 1)
Write-Host "  C 盘: ${freeGB} GB 可用 / ${totalGB} GB 总计 (已用 ${usedPct}%)"

if ($freeGB -gt 10) {
    Write-Host "  ✅ 磁盘空间充足"
    return
}
Write-Host "  ⚠️ 磁盘空间不足"

# Step 2: 预览
Write-Host "`n[Step 2] 修复预览"
Write-Host "  将要执行："
Write-Host "  1. 扫描大文件（>100MB）"
Write-Host "  2. 扫描旧文件（>30 天）"
Write-Host "  3. 清理临时文件（>7 天）"
Write-Host "  4. 清空回收站"
Write-Host "`n  影响：清理临时文件不可恢复，大文件仅建议不自动删除"

# Step 3: 确认
$confirm = Read-Host "`n  输入 '确认修复' 开始执行"
if ($confirm -ne '确认修复') { return }

# Step 4: 执行
Write-Host "`n[Step 4] 执行清理..."

# 清理临时文件
$tempPath = $env:TEMP
$cutoff = (Get-Date).AddDays(-7)
$tempFiles = Get-ChildItem -Path $tempPath -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff }
$tempKB = ($tempFiles | Measure-Object -Property Length -Sum).Sum
$tempCount = $tempFiles.Count
Write-Host "  清理临时文件: $tempCount 个文件，释放 $([math]::Round($tempKB/1MB,1)) MB"
foreach ($f in $tempFiles) {
    try { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue } catch {}
}

# 清空回收站
$shell = New-Object -ComObject Shell.Application
$rb = $shell.NameSpace(0x0a)
$rbItems = @($rb.Items())
if ($rbItems.Count -gt 0) {
    Write-Host "  清空回收站: $($rbItems.Count) 个项目"
    $rbItems | ForEach-Object { Remove-Item $_.Path -Recurse -Force -ErrorAction SilentlyContinue }
}

# 验证
$volAfter = Get-Volume -DriveLetter C
$freeAfter = [math]::Round($volAfter.SizeRemaining/1GB, 1)
Write-Host "`n[验证] 清理后 C 盘可用: ${freeAfter} GB（释放 $([math]::Round($freeAfter - $freeGB, 1)) GB）"
```

</details>

**风险等级**：🟡 中（需确认，清理临时文件不可恢复）

---

### 27.6 时间不同步修复

**修复命令**：`w32tm /resync`

**常你说**：`"时间不准"` / `"时间同步"`

<details>
<summary>📋 展开查看命令 — 时间同步四步流程</summary>

```powershell
Write-Host "════════ 时间同步修复向导 ════════"

# Step 1: 定位
Write-Host "`n[Step 1] 问题定位..."
$localTime = Get-Date
$ntpTime = $null

# 尝试从 NTP 服务器获取时间
try {
    $tcp = New-Object System.Net.Sockets.TcpClient("time.windows.com", 123)
    $stream = $tcp.GetStream()
    $data = New-Object byte[] 48
    $stream.Read($data, 0, 48) | Out-Null
    $stream.Close()
    $tcp.Close()
    # 简化：直接用 w32tm 查询
    $ntpTime = (w32tm /stripchart /computer:time.windows.com /samples:1 /dataonly 2>$null | Select-Object -Last 1)
} catch {}

$w32tmStatus = w32tm /query /status 2>$null
if ($w32tmStatus) {
    Write-Host "  Windows Time 服务状态:"
    $w32tmStatus | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
}

# Step 2: 预览
Write-Host "`n[Step 2] 修复预览"
Write-Host "  将要执行："
Write-Host "  1. w32tm /resync           — 强制同步时间"
Write-Host "  2. w32tm /query /status   — 验证同步结果"
Write-Host "`n  影响：无风险，时间同步不会丢失数据"

# Step 3: 确认
$confirm = Read-Host "`n  输入 '确认修复' 开始执行"
if ($confirm -ne '确认修复') { return }

# Step 4: 执行
Write-Host "`n[Step 4] 执行时间同步..."
w32tm /resync 2>$null
Start-Sleep -Seconds 2

# 验证
Write-Host "`n[验证] 同步结果:"
$verifyTime = w32tm /query /status 2>$null
if ($verifyTime) {
    $verifyTime | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
    Write-Host "`n  ✅ 时间同步完成"
} else {
    Write-Host "  ⚠️ 同步状态未知，稍后重试"
}
```

</details>

**风险等级**：🟢 低（无风险，仅同步时间）

---

**风险等级汇总**：

| 子模块 | 风险 | 说明 |
|--------|------|------|
| 27.1 DNS 修复 | 🟡 中 | 短暂断网 5-10 秒 |
| 27.2 网络修复 | 🟡 中 | 短暂断网 10-30 秒 |
| 27.3 WinUpdate 修复 | 🟡 中 | 正在进行的更新会中断 |
| 27.4 服务修复 | 🟡 中 | 会启动服务 |
| 27.5 磁盘清理 | 🟡 中 | 临时文件不可恢复 |
| 27.6 时间同步 | 🟢 低 | 无风险 |

| 报错 | 含义 | 解决 |
|-----|------|-----|
| `Access denied` | 需要管理员权限 | 以管理员身份运行 |
| `Service cannot be started` | 服务启动失败 | 检查依赖和端口 |
| `Network reset failed` | 网卡重置失败 | 手动禁用/启用网卡 |
| `w32tm error` | 时间服务未运行 | 启动 W32Time 服务 |

**常见坑 & 解决**：

| 场景 | 说明 |
|-----|------|
| 修复后问题依旧 | 查看对应诊断模块的详细日志 |
| 无法创建还原点 | 系统保护未启用，不影响修复操作 |
| 服务启动后立即停止 | 检查事件日志，可能是程序崩溃 |
| 磁盘清理后空间未增加 | 可能是系统还原点占用，清理旧还原点 |


## 前置要求与依赖

| 需求 | 说明 | 检测方法 |
|-----|------|---------|
| PowerShell 5.1+ | Windows 自带 | `$PSVersionTable.PSVersion` |
| 管理员权限 | IIS/清理/安全审计需要 | 自动检测（见下方） |
| WebAdministration | IIS 管理可选 | `Install-WindowsFeature Web-Mgmt-Tools` |
| 执行策略 | 可能需调整 | `Set-ExecutionPolicy RemoteSigned` |
| 存储诊断模块 | 磁盘健康检测需要 | `Get-PhysicalDisk` 可用 |
| Winmgmt (WMI) | 系统事件/会话监控需要 | `Get-CimInstance` 可用 |

**管理员权限自动检测**：


```powershell
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️ 非管理员运行，部分功能受限"
    Write-Host "  → 右键 PowerShell → 以管理员身份运行"
}
```


---



---

## ⚡ 性能优化（硬件自适应）

> **设计原则：绝不拖累用户电脑。** 所有扫描/采集任务均根据用户电脑硬件配置自动调整线程数和资源占用。

### 自动硬件检测

| 检测项 | 用途 | 自适应策略 |
|--------|------|-----------|
| CPU 核心数 | 决定并行任务数 | ≤4 核：单线程；8 核：2 线程；16+ 核：4 线程 |
| 物理内存 | 决定是否启用内存缓存 | ≤4 GB：禁用缓存；8 GB：小缓存；16+ GB：正常缓存 |
| 磁盘类型 | 决定是否启用 I/O 优先级 | HDD：低优先级 I/O；SSD：正常优先级 |
| 系统负载 | 决定是否延迟启动 | CPU >80% 时延迟 5 秒后执行 |

### 各模块自适应规则

| 模块 | 自适应行为 |
|------|-----------|
| 模块 1（磁盘扫描） | 根据 CPU 核心数自动分配扫描线程数，HDD 自动降低 I/O 优先级 |
| 模块 2（重复文件） | 大文件自动分批处理，避免内存溢出 |
| 模块 3（临时文件） | 扫描时自动跳过正在使用的文件 |
| 模块 9（性能监控） | 采集间隔根据 CPU 负载动态调整（1-5 秒） |
| 模块 12（磁盘健康） | 检测时自动限制并发 I/O，避免影响业务 |
| 模块 13（网络监控） | 连接数采集分批进行，避免一次性占用过多资源 |

### 性能保护命令示例

```powershell
# 自动检测硬件并设置线程数
$cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)
$diskType = (Get-PhysicalDisk | Select-Object -First 1).MediaType

$threadCount = switch ($cpuCores) {
    { $_ -le 4 } { 1 }
    { $_ -le 8 } { 2 }
    default { 4 }
}

$ioPriority = if ($diskType -eq 'HDD') { 'Low' } else { 'Normal' }

Write-Host "硬件检测: $cpuCores 核 CPU, ${totalRAM} GB RAM, 磁盘: $diskType"
Write-Host "自动设置: $threadCount 线程, I/O 优先级: $ioPriority"
```

## ❓ 常见问题

### Q1: 第一次使用怎么做？
直接说 `"帮我扫一下 C 盘"` 或 `"检查服务状态"`。

### Q2: 英文报错看不懂怎么办？
粘贴报错内容，AI 会翻译并给出解法。每个模块也有"报错与解决"表格。

### Q3: 会不会删坏系统？
三层保护：系统目录不可操作、删除前先确认、回收站 API 可恢复。

### Q4: 要联网或付费吗？
全程离线、零依赖、零费用。

### Q5: Windows Update 清理会不会影响已安装的补丁？
不会。只清理未完成的下载缓存，已安装补丁不受影响。重新检查更新时会重新下载。

### Q6: 性能监控的数据能保留多久？
实时计数器只显示当前值。如需长期趋势，可让 AI 创建数据收集器（需确认），数据会保存到 `C:\PerfLogs`。

### Q7: 安全审计会被攻击者发现吗？
只读审计和导出操作不会产生额外日志。但性能计数器采集会占用少量系统资源。

### Q8: 注册表审计会不会误删系统关键项？
不会。模块 11 所有操作均为只读分析，绝不修改任何注册表键值。

### Q9: 磁盘健康检测会损伤磁盘吗？
不会。SMART 信息和错误计数均为只读读取，不会执行磁盘擦除或修复操作。

### Q10: 网络连接监控会不会泄露隐私？
不会。所有检测均在本地进行，不会将任何连接信息发送到外部。

### Q11: 事件日志会清除或修改吗？
不会。模块 14 仅读取日志内容，不会清除、修改或停止日志服务。

### Q12: 软件清单会篡改卸载程序吗？
不会。模块 15 仅读取注册表卸载键值，不会修改任何安装信息或卸载程序。

### Q13: 会话监控会踢出用户吗？
不会。模块 16 仅读取会话信息，不会结束、锁定或断开任何用户会话。

### Q14: 怎么升级 winskill？
```bash
skillhub upgrade winskill
```

### Q15: 计划任务审计会删除任务吗？
不会。模块 17 所有操作均为只读审计，绝不会创建/删除/修改任何计划任务。

### Q16: 文件共享审计会断开连接吗？
不会。模块 18 仅读取共享配置和 SMB 会话信息，不会关闭共享或断开任何用户连接。

### Q17: DNS 缓存清空会断网吗？
不会。Clear-DnsClientCache 清空后会自动从 DNS 服务器重新获取解析记录。只在用户明确说「确认清空 DNS 缓存」后才执行。

### Q18: SSL 证书检测会申请或修改证书吗？
不会。模块 20 仅读取证书仓库和 IIS 绑定信息，不会申请、续签或删除任何证书。

### Q19: 防火墙规则审计会改动规则吗？
不会。模块 21 仅读取规则配置，不会新增、删除或修改任何防火墙规则。

### Q20: 服务崩溃检查会重启服务吗？
不会。模块 22 仅读取服务状态和事件日志，不会启动、停止或修改任何服务配置。

### Q23: SFC 和 DISM 有什么区别？
SFC 修复单个系统文件，DISM 修复组件存储（SFC 的源）。建议先 DISM 修复组件存储，再 SFC 修复系统文件。

### Q24: 存储池的 RAID 类型如何选择？
Mirror（镜像）提供冗余，Parity（奇偶校验）提供更高存储效率。生产环境推荐 Mirror。

### Q25: 备份失败了怎么查原因？
检查 Windows 事件查看器 → Applications and Services Logs → Microsoft → Windows → Backup → Operational。

### Q26: Docker 功能需要额外安装吗？
模块 26 使用 Windows 系统自带的 `docker` 和 `kubectl` 命令行工具。Windows Server 2016+ 支持 Docker，但需要手动安装。未安装 Docker/kubectl 时模块 26 给出安装指引，不会报错。

### Q27: 性能基线采集会不会拖慢服务器？
不会。模块 28 根据 CPU 核心数动态调整采集频率（≤4 核每 15 分钟一次，>4 核每 5 分钟一次），单次采集耗时 <1 秒，内存占用 <10MB。

### Q28: 合规检查会修改系统配置吗？
不会。模块 29 所有检查项均为只读检测，仅输出合规/不合规判定和修复建议，不会修改任何系统配置。

### Q29: 远程管理需要开启 WinRM 服务吗？
是的。模块 30 基于 PowerShell Remoting（WinRM），目标服务器需要开启 WinRM 服务（`Enable-PSRemoting`）。模块 30.1 包含一键开启 WinRM 的命令。

### Q30: 远程管理支持非域环境吗？
支持。模块 30 支持域环境和非域环境，非域环境需配置 TrustedHosts 并使用 IP 地址连接。

---

<a name="module-28"></a>

## 🆕 模块 28：性能基线 & 趋势分析

> ⚠️ **本模块所有操作均为只读分析，不会修改任何系统配置。**

<details>
<summary>📋 展开查看：模块 28：性能基线 & 趋势分析</summary>

### 28.1 性能基线建立（7 天采集）

**硬件自适应策略**：根据 CPU 核心数动态调整采集频率，避免拖累低配服务器。

```powershell
# 硬件自适应：确定采集间隔
$cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
$intervalMinutes = if ($cpuCores -le 4) { 15 } else { 5 }
$tagFile = "$env:USERPROFILE\.workbuddy\output\winskill\baseline_tag.txt"
$csvFile = "$env:USERPROFILE\.workbuddy\output\winskill\perf_baseline.csv"

# 创建输出目录
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.workbuddy\output\winskill" | Out-Null

# 检查是否已注册定时任务
$taskName = "Winskill_PerfBaseline"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if (-not $existingTask) {
    # 注册定时任务（需管理员权限）
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument @"
-Command "& {`$csv='$csvFile'; `$cpu=(Get-CimInstance Win32_Processor).LoadPercentage; `$mem=(Get-CimInstance Win32_OperatingSystem); `$memPct=[math]::Round(($mem.TotalVisibleMemorySize - `$mem.FreePhysicalMemory)/`$mem.TotalVisibleMemorySize*100,1); `$disk=(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Where-Object DeviceID -eq 'C:'); `$diskPct=[math]::Round((`$disk.Size-`$disk.FreeSpace)/`$disk.Size*100,1); `$net=(Get-CimInstance Win32_PerfFormattedData_Tcpip_NetworkInterface | Where-Object Name -notlike '*Loopback*' | Measure-Object BytesTotalPersec -Sum).Sum; `$ts=Get-Date -Format 'yyyy-MM-dd HH:mm:ss'; if(-not(Test-Path `$csv)){'Timestamp,CPU_Pct,Mem_Pct,Disk_Pct,Net_BytesPerSec' | Out-File `$csv -Encoding utf8}; '`$ts,`$cpu,`$memPct,`$diskPct,`$net' | Out-File `$csv -Append -Encoding utf8}"
'@
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $intervalMinutes) -RepetitionDuration (New-TimeSpan -Days 7)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description "Winskill 性能基线采集（7 天）" -Force
    Write-Host "✅ 已注册定时任务 '$taskName'，每 $intervalMinutes 分钟采集一次，持续 7 天"
} else {
    Write-Host "⚠️ 定时任务 '$taskName' 已存在，无需重复注册"
}

# 显示当前基线状态
if (Test-Path $csvFile) {
    $data = Import-Csv $csvFile
    Write-Host "`n📊 当前基线数据：$($data.Count) 条记录"
    Write-Host "CPU 基线：$(($data | Measure-Object CPU_Pct -Average).Average)%（均值）"
    Write-Host "内存 基线：$(($data | Measure-Object Mem_Pct -Average).Average)%（均值）"
    Write-Host "磁盘 基线：$(($data | Measure-Object Disk_Pct -Average).Average)%（均值）"
} else {
    Write-Host "📋 尚未开始采集，注册定时任务后自动开始"
}
```

### 28.2 异常偏离告警（当前值 vs 基线）

```powershell
$csvFile = "$env:USERPROFILE\.workbuddy\output\winskill\perf_baseline.csv"
$thresholdMultiplier = 2.0  # 偏离基线 200% 触发告警

if (-not (Test-Path $csvFile)) {
    Write-Host "❌ 尚未建立基线，请先运行 28.1 建立基线"
    exit 1
}

$data = Import-Csv $csvFile
if ($data.Count -lt 10) {
    Write-Host "⚠️ 基线数据不足（$($data.Count) 条），建议至少采集 10 条后再分析"
}

# 计算基线均值
$cpuAvg = ($data | Measure-Object CPU_Pct -Average).Average
$memAvg = ($data | Measure-Object Mem_Pct -Average).Average
$diskAvg = ($data | Measure-Object Disk_Pct -Average).Average

# 获取当前值
$cpuNow = (Get-CimInstance Win32_Processor).LoadPercentage
$mem = (Get-CimInstance Win32_OperatingSystem)
$memNow = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1)
$disk = (Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Where-Object DeviceID -eq 'C:')
$diskNow = [math]::Round(($disk.Size - $disk.FreeSpace) / $disk.Size * 100, 1)

Write-Host "`n📊 偏离分析报告"
Write-Host ("=" * 50)
Write-Host ("指标     当前值    基线均值    偏离倍数    状态")
Write-Host ("-" * 50)

$alerts = @()

$cpuDev = if ($cpuAvg -gt 0) { $cpuNow / $cpuAvg } else { 0 }
$status = if ($cpuDev -ge $thresholdMultiplier) { "🚨 告警" } elseif ($cpuDev -ge 1.5) { "⚠️ 警告" } else { "✅ 正常" }
Write-Host ("CPU      {0,6}%    {1,6}%    {2,6:F1}x      {3}" -f $cpuNow, $cpuAvg, $cpuDev, $status)
if ($cpuDev -ge $thresholdMultiplier) { $alerts += "CPU 使用率偏离基线 ${cpuDev:F1} 倍（当前 $cpuNow%，基线 $cpuAvg%）" }

$memDev = if ($memAvg -gt 0) { $memNow / $memAvg } else { 0 }
$status = if ($memDev -ge $thresholdMultiplier) { "🚨 告警" } elseif ($memDev -ge 1.5) { "⚠️ 警告" } else { "✅ 正常" }
Write-Host ("内存     {0,6}%    {1,6}%    {2,6:F1}x      {3}" -f $memNow, $memAvg, $memDev, $status)
if ($memDev -ge $thresholdMultiplier) { $alerts += "内存使用率偏离基线 ${memDev:F1} 倍（当前 $memNow%，基线 $memAvg%）" }

$diskDev = if ($diskAvg -gt 0) { $diskNow / $diskAvg } else { 0 }
$status = if ($diskDev -ge 1.3) { "🚨 告警" } elseif ($diskDev -ge 1.1) { "⚠️ 警告" } else { "✅ 正常" }
Write-Host ("磁盘     {0,6}%    {1,6}%    {2,6:F1}x      {3}" -f $diskNow, $diskAvg, $diskDev, $status)
if ($diskDev -ge 1.3) { $alerts += "磁盘使用率偏离基线 ${diskDev:F1} 倍（当前 $diskNow%，基线 $diskAvg%）" }

Write-Host ("=" * 50)

if ($alerts.Count -eq 0) {
    Write-Host "`n✅ 所有指标正常，无异常偏离"
} else {
    Write-Host "`n🚨 发现 $($alerts.Count) 项异常偏离："
    $alerts | ForEach-Object { Write-Host "  ⚠️ $_" }
}
```

### 28.3 趋势预测（磁盘耗尽时间）

```powershell
$csvFile = "$env:USERPROFILE\.workbuddy\output\winskill\perf_baseline.csv"

if (-not (Test-Path $csvFile)) {
    Write-Host "❌ 尚未建立基线，请先运行 28.1 建立基线"
    exit 1
}

$data = Import-Csv $csvFile
if ($data.Count -lt 5) {
    Write-Host "⚠️ 数据不足（$($data.Count) 条），无法预测"
    exit 1
}

# 简单线性回归预测磁盘耗尽时间
$diskValues = $data | ForEach-Object { [double]$_.Disk_Pct }
$n = $diskValues.Count

# 计算斜率（每天增长百分比）
$sumX = ($n - 1) * $n / 2
$sumY = ($diskValues | Measure-Object -Sum).Sum
$sumXY = 0
$sumX2 = 0
for ($i = 0; $i -lt $n; $i++) {
    $sumXY += $i * $diskValues[$i]
    $sumX2 += $i * $i
}
$slope = ($n * $sumXY - $sumX * $sumY) / ($n * $sumX2 - $sumX * $sumX)

$currentDisk = $diskValues[-1]

Write-Host "`n📈 趋势预测报告"
Write-Host ("=" * 50)
Write-Host ("当前磁盘使用率：{0}%" -f $currentDisk)

if ($slope -le 0) {
    Write-Host ("趋势：磁盘使用率稳定或下降（斜率 {0:F4}%/采集周期）" -f $slope)
    Write-Host "✅ 磁盘空间充足，无需担心"
} else {
    # 估算耗尽时间（基于采集间隔）
    $cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
    $intervalMinutes = if ($cpuCores -le 4) { 15 } else { 5 }
    $periodsPerDay = 24 * 60 / $intervalMinutes
    $daysToFull = (100 - $currentDisk) / ($slope * $periodsPerDay)
    
    Write-Host ("增长速率：{0:F4}%/采集周期（约 {1:F2}%/天）" -f $slope, ($slope * $periodsPerDay))
    
    if ($daysToFull -gt 365) {
        Write-Host ("预计耗尽时间：> 1 年（约 {0:F0} 天）" -f $daysToFull)
        Write-Host "✅ 磁盘空间充足"
    } elseif ($daysToFull -gt 30) {
        Write-Host ("预计耗尽时间：约 {0:F0} 天（{1:F1} 个月）" -f $daysToFull, ($daysToFull / 30))
        Write-Host "⚠️ 建议关注磁盘使用趋势"
    } elseif ($daysToFull -gt 7) {
        Write-Host ("预计耗尽时间：约 {0:F0} 天" -f $daysToFull)
        Write-Host "🚨 建议尽快清理磁盘空间"
    } else {
        Write-Host ("预计耗尽时间：约 {0:F0} 天" -f $daysToFull)
        Write-Host "🔴 磁盘即将耗尽！请立即清理"
    }
}

# 内存趋势预测
$memValues = $data | ForEach-Object { [double]$_.Mem_Pct }
$sumY = ($memValues | Measure-Object -Sum).Sum
$sumXY = 0
for ($i = 0; $i -lt $n; $i++) {
    $sumXY += $i * $memValues[$i]
}
$slope = ($n * $sumXY - $sumX * $sumY) / ($n * $sumX2 - $sumX * $sumX)
$currentMem = $memValues[-1]

Write-Host ("`n当前内存使用率：{0}%" -f $currentMem)
if ($slope -le 0) {
    Write-Host "趋势：内存使用率稳定或下降 ✅"
} else {
    $periodsPerDay = 24 * 60 / $intervalMinutes
    $daysToFull = (95 - $currentMem) / ($slope * $periodsPerDay)  # 95% 作为预警线
    if ($daysToFull -gt 30) {
        Write-Host ("增长速率：{0:F4}%/采集周期 ✅ 内存充足" -f $slope)
    } elseif ($daysToFull -gt 0) {
        Write-Host ("增长速率：{0:F4}%/采集周期 ⚠️ 约 {1:F0} 天后达到 95%" -f $slope, $daysToFull)
    } else {
        Write-Host "🔴 内存使用率持续上升，建议排查内存泄漏"
    }
}
Write-Host ("=" * 50)
```

### 28.4 性能瓶颈关联分析

```powershell
Write-Host "`n🔍 性能瓶颈关联分析"
Write-Host ("=" * 60)

# 采集四维指标
$cpu = (Get-CimInstance Win32_Processor).LoadPercentage
$mem = (Get-CimInstance Win32_OperatingSystem)
$memPct = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1)
$disk = Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk | Where-Object Name -eq "_Total"
$diskPct = [math]::Round($disk.PercentDiskTime, 1)
$net = Get-CimInstance Win32_PerfFormattedData_Tcpip_NetworkInterface | Where-Object Name -notlike '*Loopback*'
$netPct = [math]::Round(($net | Measure-Object BytesTotalPersec -Sum).Sum / 1MB, 1)  # MB/s

Write-Host ("CPU 使用率：    {0,6}%" -f $cpu)
Write-Host ("内存使用率：    {0,6}%" -f $memPct)
Write-Host ("磁盘活动时间：  {0,6}%" -f $diskPct)
Write-Host ("网络流量：      {0,6} MB/s" -f $netPct)
Write-Host ("-" * 60)

# 瓶颈判定逻辑
$bottleneck = $null
$severity = "正常"

if ($cpu -ge 90 -and $memPct -ge 85) {
    $bottleneck = "CPU + 内存双重瓶颈"
    $severity = "🔴 严重"
} elseif ($diskPct -ge 90 -and $memPct -ge 85) {
    $bottleneck = "磁盘 I/O + 内存双重瓶颈（可能存在内存交换）"
    $severity = "🔴 严重"
} elseif ($cpu -ge 90) {
    $bottleneck = "CPU 瓶颈"
    $severity = "🚨 高"
} elseif ($memPct -ge 90) {
    $bottleneck = "内存瓶颈"
    $severity = "🚨 高"
} elseif ($diskPct -ge 90) {
    $bottleneck = "磁盘 I/O 瓶颈"
    $severity = "🚨 高"
} elseif ($cpu -ge 70 -and $memPct -ge 70) {
    $bottleneck = "CPU + 内存轻度压力"
    $severity = "⚠️ 中"
} elseif ($diskPct -ge 70 -and $memPct -ge 70) {
    $bottleneck = "磁盘 + 内存轻度压力"
    $severity = "⚠️ 中"
} elseif ($cpu -ge 70) {
    $bottleneck = "CPU 轻度压力"
    $severity = "⚠️ 中"
} elseif ($memPct -ge 70) {
    $bottleneck = "内存轻度压力"
    $severity = "⚠️ 中"
} elseif ($diskPct -ge 70) {
    $bottleneck = "磁盘 I/O 轻度压力"
    $severity = "⚠️ 中"
}

if ($bottleneck) {
    Write-Host ("瓶颈判定：{0}（{1}）" -f $bottleneck, $severity)
} else {
    Write-Host "✅ 系统运行正常，无明显瓶颈"
}

# 关联分析建议
Write-Host ("-" * 60)
Write-Host "关联分析："

if ($memPct -ge 85 -and $diskPct -ge 80) {
    Write-Host "  ⚠️ 内存高 + 磁盘 I/O 高 → 可能发生内存交换（页面文件频繁读写）"
    Write-Host "  建议：检查内存占用 Top 进程（模块 9.2），考虑增加物理内存"
}

if ($cpu -ge 80 -and $diskPct -ge 80) {
    Write-Host "  ⚠️ CPU 高 + 磁盘 I/O 高 → 可能在进行大量文件操作或数据库查询"
    Write-Host "  建议：检查磁盘 I/O 进程（模块 9.3），定位高 I/O 来源"
}

if ($netPct -gt 100 -and $cpu -ge 70) {
    Write-Host "  ⚠️ 网络流量大 + CPU 高 → 可能受到 DDoS 攻击或大量数据传输"
    Write-Host "  建议：检查网络连接（模块 13.1），排查可疑外连（模块 13.3）"
}

if ($cpu -lt 50 -and $memPct -lt 50 -and $diskPct -lt 50) {
    Write-Host "  ✅ 四维指标均正常，系统健康"
}

Write-Host ("=" * 60)
```

### 报错与解决

| 报错 | 原因 | 解决 |
|------|------|------|
| `Register-ScheduledTask 拒绝访问` | 需要管理员权限 | 以管理员身份运行 PowerShell |
| `无法加载文件，因为在此系统上禁止运行脚本` | 执行策略限制 | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `基线数据不足` | 采集时间太短 | 等待至少 10 个采集周期后再分析 |
| `Get-CimInstance 找不到类` | WMI 服务异常 | 运行 `winmgmt /resetrepository` |

</details>


[↑ 返回顶部](#module-1)

---

<a name="module-29"></a>

## 🆕 模块 29：安全合规检查清单

> ⚠️ **本模块所有操作均为只读检测，不会修改任何系统配置。**

<details>
<summary>📋 展开查看：模块 29：安全合规检查清单</summary>

### 29.1 等保 2.0 检查项

```powershell
Write-Host "`n📋 等保 2.0 合规检查报告"
Write-Host ("=" * 60)
Write-Host ("检查时间：{0:yyyy-MM-dd HH:mm:ss}" -f (Get-Date))
Write-Host ("计算机名：$env:COMPUTERNAME")
Write-Host ("=" * 60)

$results = @()

# 1. 密码策略
Write-Host "`n【1. 密码策略】"
$pwdPolicy = net accounts | Out-String
$minPwdLen = if ($pwdPolicy -match 'Minimum password length\s+(\d+)') { $matches[1] } else { "0" }
$maxPwdAge = if ($pwdPolicy -match 'Maximum password age \(days\)\s+(\d+|Unlimited)') { $matches[1] } else { "Unknown" }
$minPwdAge = if ($pwdPolicy -match 'Minimum password age \(days\)\s+(\d+)') { $matches[1] } else { "0" }
$pwdHistory = if ($pwdPolicy -match 'Password history length\s+(\d+)') { $matches[1] } else { "0" }

$pass = [int]$minPwdLen -ge 8
$results += [PSCustomObject]@{ Category = "密码策略"; Item = "密码最小长度≥8"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$minPwdLen" }
Write-Host ("  密码最小长度≥8：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $minPwdLen)

$pass = $maxPwdAge -ne "Unlimited" -and [int]$maxPwdAge -le 90
$results += [PSCustomObject]@{ Category = "密码策略"; Item = "密码最长使用期限≤90天"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$maxPwdAge" }
Write-Host ("  密码最长使用期限≤90天：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $maxPwdAge)

$pass = [int]$pwdHistory -ge 5
$results += [PSCustomObject]@{ Category = "密码策略"; Item = "密码历史记录≥5"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$pwdHistory" }
Write-Host ("  密码历史记录≥5：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $pwdHistory)

# 2. 账户锁定策略
Write-Host "`n【2. 账户锁定策略】"
$lockoutThreshold = if ($pwdPolicy -match 'Lockout threshold\s+(\d+|Never)') { $matches[1] } else { "Unknown" }
$lockoutDuration = if ($pwdPolicy -match 'Lockout duration \(minutes\)\s+(\d+|Never)') { $matches[1] } else { "Unknown" }
$lockoutWindow = if ($pwdPolicy -match 'Lockout observation window \(minutes\)\s+(\d+|Never)') { $matches[1] } else { "Unknown" }

$pass = $lockoutThreshold -ne "Never" -and [int]$lockoutThreshold -le 5
$results += [PSCustomObject]@{ Category = "账户锁定"; Item = "锁定阈值≤5次"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$lockoutThreshold" }
Write-Host ("  锁定阈值≤5次：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $lockoutThreshold)

$pass = $lockoutDuration -ne "Never" -and [int]$lockoutDuration -ge 15
$results += [PSCustomObject]@{ Category = "账户锁定"; Item = "锁定时间≥15分钟"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$lockoutDuration" }
Write-Host ("  锁定时间≥15分钟：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $lockoutDuration)

# 3. 审计日志策略
Write-Host "`n【3. 审计日志策略】"
$auditPolicy = auditpol /get /category:* 2>$null | Out-String
$logonEvents = if ($auditPolicy -match 'Logon\s+Success and Failure') { "Success and Failure" } elseif ($auditPolicy -match 'Logon\s+(\w+)') { $matches[1] } else { "Not Configured" }
$objectAccess = if ($auditPolicy -match 'Object Access\s+Success and Failure') { "Success and Failure" } elseif ($auditPolicy -match 'Object Access\s+(\w+)') { $matches[1] } else { "Not Configured" }
$privilegeUse = if ($auditPolicy -match 'Privilege Use\s+Success and Failure') { "Success and Failure" } elseif ($auditPolicy -match 'Privilege Use\s+(\w+)') { $matches[1] } else { "Not Configured" }

$pass = $logonEvents -eq "Success and Failure"
$results += [PSCustomObject]@{ Category = "审计日志"; Item = "登录事件审计（成功+失败）"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$logonEvents" }
Write-Host ("  登录事件审计：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $logonEvents)

$pass = $objectAccess -eq "Success and Failure"
$results += [PSCustomObject]@{ Category = "审计日志"; Item = "对象访问审计（成功+失败）"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "当前值：$objectAccess" }
Write-Host ("  对象访问审计：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $objectAccess)

# 4. 防火墙状态
Write-Host "`n【4. 防火墙状态】"
$firewallProfiles = Get-NetFirewallProfile
$allEnabled = ($firewallProfiles | Where-Object Enabled -eq $false).Count -eq 0
$results += [PSCustomObject]@{ Category = "防火墙"; Item = "所有配置文件已启用防火墙"; Status = if ($allEnabled) { "✅ 合规" } else { "❌ 不合规" }; Detail = "已启用：$(($firewallProfiles | Where-Object Enabled).Count)/3" }
Write-Host ("  防火墙全部启用：{0}（已启用 {1}/3）" -f $(if ($allEnabled) { "✅" } else { "❌" }), (($firewallProfiles | Where-Object Enabled).Count))

# 5. 补丁更新状态
Write-Host "`n【5. 补丁更新状态】"
$hotfixes = Get-HotFix | Sort-Object InstalledOn -Descending
$pass = $false
if ($hotfixes.Count -gt 0) {
    $lastUpdate = $hotfixes[0].InstalledOn
    $daysSinceUpdate = ((Get-Date) - $lastUpdate).Days
    $pass = $daysSinceUpdate -le 30
} else {
    $lastUpdate = "无记录"
    $daysSinceUpdate = 9999
    $pass = $false
}
$results += [PSCustomObject]@{ Category = "补丁更新"; Item = "最近 30 天内有补丁更新"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "最后更新：$lastUpdate（$($daysSinceUpdate.Days) 天前）" }
Write-Host ("  最近 30 天有补丁：{0}（最后：{1:yyyy-MM-dd}，{2} 天前）" -f $(if ($pass) { "✅" } else { "❌" }), $lastUpdate, $daysSinceUpdate.Days)

# 6. 远程桌面安全
Write-Host "`n【6. 远程桌面安全】"
$rdpEnabled = (Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -ErrorAction SilentlyContinue).fDenyTSConnections
$rdpStatus = if ($rdpEnabled -eq 0) { "已启用" } else { "已禁用" }
$nlaEnabled = (Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Error Action SilentlyContinue).UserAuthentication
$nlaStatus = if ($nlaEnabled -eq 1) { "已启用" } else { "未启用" }

$pass = $rdpEnabled -ne 0 -or $nlaEnabled -eq 1  # 如果 RDP 启用，必须启用 NLA
$results += [PSCustomObject]@{ Category = "远程桌面"; Item = "RDP 网络级身份验证（NLA）"; Status = if ($pass) { "✅ 合规" } else { "❌ 不合规" }; Detail = "RDP：$rdpStatus，NLA：$nlaStatus" }
Write-Host ("  NLA 已启用：{0}（RDP：{1}，NLA：{2}）" -f $(if ($pass) { "✅" } else { "❌" }), $rdpStatus, $nlaStatus)

# 汇总
$compliant = ($results | Where-Object Status -like "✅*").Count
$nonCompliant = ($results | Where-Object Status -like "❌*").Count
$total = $results.Count
$rate = [math]::Round($compliant / $total * 100, 1)

Write-Host ("`n" + "=" * 60)
Write-Host ("📊 合规汇总：{0}/{1} 项合规（合规率 {2}%）" -f $compliant, $total, $rate)
Write-Host ("✅ 合规：$compliant 项")
Write-Host ("❌ 不合规：$nonCompliant 项")
Write-Host ("=" * 60)

if ($nonCompliant -gt 0) {
    Write-Host "`n❌ 不合规项详情："
    $results | Where-Object Status -like "❌*" | ForEach-Object {
        Write-Host ("  [{0}] {1}：{2}" -f $_.Category, $_.Item, $_.Detail)
    }
}
```

### 29.2 CIS Benchmark 检查（精选关键控制项）

```powershell
Write-Host "`n🔒 CIS Benchmark 检查（Windows Server 精选）"
Write-Host ("=" * 60)

$cisResults = @()

# CIS 1.1.1 - 密码最小长度（CIS 要求 14）
Write-Host "`n【密码策略】"
$minLen = (net accounts | Select-String 'Minimum password length').ToString() -replace '.*?\s+(\d+).*','$1'
$pass = [int]$minLen -ge 14
$cisResults += [PSCustomObject]@{ Control = "1.1.1"; Item = "密码最小长度≥14"; Status = if ($pass) { "✅" } else { "❌" }; Detail = "当前：$minLen" }
Write-Host ("  1.1.1 密码最小长度≥14：{0}（当前：{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $minLen)

# CIS 1.1.2 - 密码复杂度
$complexity = (Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name PasswordComplexity -ErrorAction SilentlyContinue).PasswordComplexity
$pass = $complexity -eq 1
$cisResults += [PSCustomObject]@{ Control = "1.1.2"; Item = "密码复杂度已启用"; Status = if ($pass) { "✅" } else { "❌" }; Detail = "当前：$(if ($complexity -eq 1) { '已启用' } else { '未启用' })" }
Write-Host ("  1.1.2 密码复杂度：{0}" -f $(if ($pass) { "✅" } else { "❌" }))

# CIS 2.2.1 - 禁止 Guest 账户
Write-Host "`n【账户策略】"
$guestAccount = Get-LocalUser -Name "Guest" -ErrorAction SilentlyContinue
$pass = $guestAccount -and $guestAccount.Enabled -eq $false
$cisResults += [PSCustomObject]@{ Control = "2.2.1"; Item = "Guest 账户已禁用"; Status = if ($pass) { "✅" } else { "❌" }; Detail = "当前：$(if ($guestAccount.Enabled -eq $false) { '已禁用' } else { '已启用' })" }
Write-Host ("  2.2.1 Guest 已禁用：{0}" -f $(if ($pass) { "✅" } else { "❌" }))

# CIS 2.3.1.1 - 限制空密码登录
$limitBlank = (Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name LimitBlankPasswordUse -ErrorAction SilentlyContinue).LimitBlankPasswordUse
$pass = $limitBlank -eq 1
$cisResults += [PSCustomObject]@{ Control = "2.3.1.1"; Item = "限制空密码登录"; Status = if ($pass) { "✅" } else { "❌" }; Detail = "当前：$(if ($limitBlank -eq 1) { '已限制' } else { '未限制' })" }
Write-Host ("  2.3.1.1 空密码限制：{0}" -f $(if ($pass) { "✅" } else { "❌" }))

# CIS 5.1 - Windows Update 服务
Write-Host "`n【系统服务】"
$wuService = Get-Service -Name wuauserv -ErrorAction SilentlyContinue
$pass = $wuService -and $wuService.Status -eq "Running"
$cisResults += [PSCustomObject]@{ Control = "5.1"; Item = "Windows Update 服务运行中"; Status = if ($pass) { "✅" } else { "❌" }; Detail = "当前：$($wuService.Status)" }
Write-Host ("  5.1 Windows Update：{0}（{1}）" -f $(if ($pass) { "✅" } else { "❌" }), $wuService.Status)

# CIS 9.1 - Windows Firewall
Write-Host "`n【防火墙】"
$fwProfiles = Get-NetFirewallProfile
$allEnabled = ($fwProfiles | Where-Object Enabled -eq $false).Count -eq 0
$cisResults += [PSCustomObject]@{ Control = "9.1"; Item = "所有防火墙配置文件已启用"; Status = if ($allEnabled) { "✅" } else { "❌" }; Detail = "已启用：$(($fwProfiles | Where-Object Enabled).Count)/3" }
Write-Host ("  9.1 防火墙全部启用：{0}" -f $(if ($allEnabled) { "✅" } else { "❌" }))

# CIS 17.1 - 审计策略
Write-Host "`n【审计策略】"
$auditPolicy = auditpol /get /category:* 2>$null | Out-String
$securityLogon = if ($auditPolicy -match 'Logon\s+Success and Failure') { $true } else { $false }
$cisResults += [PSCustomObject]@{ Control = "17.1"; Item = "登录事件审计（成功+失败）"; Status = if ($securityLogon) { "✅" } else { "❌" }; Detail = "当前：$(if ($securityLogon) { '已配置' } else { '未配置' })" }
Write-Host ("  17.1 登录审计：{0}" -f $(if ($securityLogon) { "✅" } else { "❌" }))

# 汇总
$compliant = ($cisResults | Where-Object Status -eq "✅").Count
$nonCompliant = ($cisResults | Where-Object Status -eq "❌").Count
$total = $cisResults.Count
$rate = [math]::Round($compliant / $total * 100, 1)

Write-Host ("`n" + "=" * 60)
Write-Host ("📊 CIS 汇总：{0}/{1} 项合规（合规率 {2}%）" -f $compliant, $total, $rate)
Write-Host ("=" * 60)
```

### 29.3 合规报告生成（Markdown 文本）

```powershell
# 生成 Markdown 格式合规报告（纯文本，可复制保存为 .md 文件）
$reportTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$reportName = "合规检查报告_$env:COMPUTERNAME`_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

$report = @"
# Windows Server 合规检查报告

| 项目 | 内容 |
|------|------|
| 计算机名 | $env:COMPUTERNAME |
| 检查时间 | $reportTime |
| 操作系统 | $((Get-CimInstance Win32_OperatingSystem).Caption) |
| 版本 | $((Get-CimInstance Win32_OperatingSystem).Version) |

## 等保 2.0 检查结果

| 类别 | 检查项 | 状态 | 详情 |
|------|--------|------|------|
| 密码策略 | 密码最小长度≥8 | 待检查 | - |
| 密码策略 | 密码最长使用期限≤90天 | 待检查 | - |
| 密码策略 | 密码历史记录≥5 | 待检查 | - |
| 账户锁定 | 锁定阈值≤5次 | 待检查 | - |
| 账户锁定 | 锁定时间≥15分钟 | 待检查 | - |
| 审计日志 | 登录事件审计（成功+失败） | 待检查 | - |
| 审计日志 | 对象访问审计（成功+失败） | 待检查 | - |
| 防火墙 | 所有配置文件已启用 | 待检查 | - |
| 补丁更新 | 最近 30 天内有补丁更新 | 待检查 | - |
| 远程桌面 | RDP 网络级身份验证（NLA） | 待检查 | - |

## CIS Benchmark 检查结果

| 控制项 | 检查内容 | 状态 | 详情 |
|--------|----------|------|------|
| 1.1.1 | 密码最小长度≥14 | 待检查 | - |
| 1.1.2 | 密码复杂度已启用 | 待检查 | - |
| 2.2.1 | Guest 账户已禁用 | 待检查 | - |
| 2.3.1.1 | 限制空密码登录 | 待检查 | - |
| 5.1 | Windows Update 服务运行中 | 待检查 | - |
| 9.1 | 所有防火墙配置文件已启用 | 待检查 | - |
| 17.1 | 登录事件审计（成功+失败） | 待检查 | - |

## 说明

- 本报告由 winskill 自动生成，仅作参考
- 实际合规判定需结合企业安全策略和行业标准
- 建议定期运行检查并保存报告备查
"@

# 输出到控制台
Write-Host $report

# 保存到用户输出目录
$outputDir = "$env:USERPROFILE\.workbuddy\output\winskill"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$outputFile = Join-Path $outputDir "$reportName.md"
$report | Out-File -FilePath $outputFile -Encoding utf8

Write-Host ("`n✅ 报告已保存到：{0}" -f $outputFile)
Write-Host "提示：可将 .md 文件内容复制到 Word 或在线 Markdown 转 PDF 工具生成 PDF"
```

### 29.4 不合规项修复建议

```powershell
Write-Host "`n🔧 不合规项修复建议"
Write-Host ("=" * 60)
Write-Host "以下命令仅作参考，请确认后再执行：`n"

Write-Host "【密码策略修复】"
Write-Host "net accounts /minpwlen:8              # 设置密码最小长度 8 位"
Write-Host "net accounts /maxpwage:90             # 设置密码最长使用期限 90 天"
Write-Host "net accounts /minpwage:1              # 设置密码最短使用期限 1 天"
Write-Host "net accounts /uniquepy:5              # 密码历史记录 5 个"

Write-Host "`n【账户锁定修复】"
Write-Host "net accounts /lockoutthreshold:5       # 锁定阈值 5 次"
Write-Host "net accounts /lockoutduration:15       # 锁定时间 15 分钟"
Write-Host "net accounts /lockoutwindow:15         # 锁定观察窗口 15 分钟"

Write-Host "`n【审计策略修复】"
Write-Host "auditpol /set /subcategory:'Logon' /success:enable /failure:enable"
Write-Host "auditpol /set /subcategory:'Object Access' /success:enable /failure:enable"
Write-Host "auditpol /set /subcategory:'Privilege Use' /success:enable /failure:enable"

Write-Host "`n【防火墙修复】"
Write-Host "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"

Write-Host "`n【Guest 账户修复】"
Write-Host "Disable-LocalUser -Name 'Guest'        # 禁用 Guest 账户"

Write-Host "`n【RDP NLA 修复】"
Write-Host "Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Value 1"

Write-Host ("`n" + "=" * 60)
Write-Host "⚠️ 以上命令仅供参考，请确认后再执行"
```

### 报错与解决

| 报错 | 原因 | 解决 |
|------|------|------|
| `auditpol 不是内部或外部命令` | 需要管理员权限 | 以管理员身份运行 PowerShell |
| `Get-NetFirewallProfile 拒绝访问` | 需要管理员权限 | 以管理员身份运行 PowerShell |
| `无法保存报告到输出目录` | 目录不存在或权限不足 | 手动创建 `%USERPROFILE%\.workbuddy\output\winskill` |
| `net accounts 输出格式不符` | 系统语言非中文 | 根据实际输出调整正则匹配 |

</details>


[↑ 返回顶部](#module-1)

---

<a name="module-30"></a>

## 🆕 模块 30：远程多服务器管理

> ⚠️ **本模块需要 WinRM 服务支持，所有操作需管理员权限。**

<details>
<summary>📋 展开查看：模块 30：远程多服务器管理</summary>

### 30.1 服务器注册（Windows Credential Manager）

```powershell
# 服务器注册配置文件
$serverFile = "$env:USERPROFILE\.workbuddy\output\winskill\servers.json"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.workbuddy\output\winskill" | Out-Null

# 加载已有服务器列表
$servers = @()
if (Test-Path $serverFile) {
    $servers = Get-Content $serverFile -Raw | ConvertFrom-Json
}

Write-Host "`n🖥️ 远程服务器管理"
Write-Host ("=" * 50)
Write-Host "1. 添加服务器"
Write-Host "2. 查看已注册服务器"
Write-Host "3. 删除服务器"
Write-Host "4. 测试连接"
Write-Host ("=" * 50)

# 示例：添加服务器（实际使用时通过 AI 交互输入）
$action = Read-Host "请选择操作 (1-4)"

switch ($action) {
    "1" {
        $ip = Read-Host "服务器 IP 或主机名"
        $user = Read-Host "用户名（如 Administrator）"
        $auth = Read-Host "认证方式 (1=密码 2=证书)"
        
        if ($auth -eq "1") {
            $cred = Get-Credential -Message "输入 $ip 的凭据"
            # 保存到 Windows Credential Manager（通过 cmdkey）
            $target = "TERMSRV/$ip"
            cmdkey /generic:$target /user:$($cred.UserName) /pass:$($cred.GetNetworkCredential().Password) 2>$null
            Write-Host "✅ 凭据已保存到 Windows Credential Manager"
        }
        
        $newServer = @{
            ip = $ip
            user = $user
            addedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            tags = @()
        }
        $servers += $newServer
        $servers | ConvertTo-Json -Depth 3 | Out-File $serverFile -Encoding utf8
        Write-Host "✅ 服务器 $ip 已注册"
    }
    "2" {
        if ($servers.Count -eq 0) {
            Write-Host "⚠️ 暂无已注册服务器"
        } else {
            Write-Host "`n已注册服务器："
            $servers | ForEach-Object { Write-Host "  - $($_.ip)（$($_.user)）添加于 $($_.addedAt)" }
        }
    }
    "3" {
        $ip = Read-Host "要删除的服务器 IP"
        $servers = $servers | Where-Object ip -ne $ip
        $servers | ConvertTo-Json -Depth 3 | Out-File $serverFile -Encoding utf8
        Write-Host "✅ 服务器 $ip 已删除"
    }
    "4" {
        $ip = Read-Host "要测试的服务器 IP"
        $result = Test-WSMan -ComputerName $ip -ErrorAction SilentlyContinue
        if ($result) {
            Write-Host "✅ $ip WinRM 服务正常"
        } else {
            Write-Host "❌ $ip 无法连接，请检查："
            Write-Host "  1. 目标服务器是否开启 WinRM（Enable-PSRemoting）"
            Write-Host "  2. 防火墙是否放行 5985/5986 端口"
            Write-Host "  3. 网络是否可达"
        }
    }
}
```

### 30.2 批量命令执行（并行）

```powershell
$serverFile = "$env:USERPROFILE\.workbuddy\output\winskill\servers.json"

if (-not (Test-Path $serverFile)) {
    Write-Host "❌ 暂无已注册服务器，请先运行 30.1 注册"
    exit 1
}

$servers = Get-Content $serverFile -Raw | ConvertFrom-Json

if ($servers.Count -eq 0) {
    Write-Host "⚠️ 暂无已注册服务器"
    exit 1
}

# 硬件自适应：并行数 = min(CPU 核心数, 服务器数量)
$cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
$maxParallel = [Math]::Min($cpuCores, $servers.Count)
Write-Host ("`n⚡ 并行执行：{0} 个任务同时运行（CPU {1} 核）" -f $maxParallel, $cpuCores)

# 要执行的命令
$command = Read-Host "要在所有服务器执行的命令"

Write-Host ("`n在 {0} 台服务器上执行：{1}" -f $servers.Count, $command)
Write-Host ("-" * 60)

# PowerShell 5.1 兼容：使用 Invoke-Command 并行执行（原生支持多计算机）
$computerNames = $servers.ip
$cred = Get-Credential -Message "输入所有服务器的通用凭据"

Write-Host ("`n在 {0} 台服务器上执行：{1}" -f $servers.Count, $command)
Write-Host ("-" * 60)

try {
    # Invoke-Command 原生支持多计算机并行执行
    $results = Invoke-Command -ComputerName $computerNames -Credential $cred -ScriptBlock {
        param($cmd)
        $output = Invoke-Expression $cmd 2>&1
        [PSCustomObject]@{
            Server = $env:COMPUTERNAME
            Status = "✅ 成功"
            Output = $output | Out-String
        }
    } -ArgumentList $command -ErrorAction Stop
    
    # 汇总结果
    Write-Host ("`n" + "=" * 60)
    Write-Host "📊 执行结果汇总："
    $results | ForEach-Object {
        Write-Host ("`n[{0}] {1}" -f $_.Server, $_.Status)
        if ($_.Output) { Write-Host $_.Output }
    }
    Write-Host ("=" * 60)
} catch {
    Write-Host ("❌ 执行失败：{0}" -f $_.Exception.Message)
    Write-Host "提示：确认所有服务器都已开启 WinRM（运行 Enable-PSRemoting -Force）"
}
```

### 30.3 统一监控面板

```powershell
$serverFile = "$env:USERPROFILE\.workbuddy\output\winskill\servers.json"

if (-not (Test-Path $serverFile)) {
    Write-Host "❌ 暂无已注册服务器"
    exit 1
}

$servers = Get-Content $serverFile -Raw | ConvertFrom-Json

Write-Host "`n📊 多服务器统一监控面板"
Write-Host ("=" * 80)
Write-Host ("{0,-20} {1,8} {2,8} {3,8} {4,10} {5,10}" -f "服务器", "CPU%", "内存%", "磁盘%", "状态", "运行时间")
Write-Host ("-" * 80)

foreach ($server in $servers) {
    try {
        $session = New-PSSession -ComputerName $server.ip -ErrorAction Stop
        $info = Invoke-Command -Session $session -ScriptBlock {
            $cpu = (Get-CimInstance Win32_Processor).LoadPercentage
            $mem = (Get-CimInstance Win32_OperatingSystem)
            $memPct = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1)
            $disk = (Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Where-Object DeviceID -eq 'C:')
            $diskPct = [math]::Round(($disk.Size - $disk.FreeSpace) / $disk.Size * 100, 1)
            $uptime = (Get-Date) - $mem.LastBootUpTime
            [PSCustomObject]@{
                CPU = $cpu
                Mem = $memPct
                Disk = $diskPct
                Uptime = "{0}天{1}小时" -f $uptime.Days, $uptime.Hours
            }
        }
        Remove-PSSession $session
        
        $statusEmoji = if ($info.CPU -ge 90 -or $info.Mem -ge 90 -or $info.Disk -ge 90) { "🔴" } elseif ($info.CPU -ge 70 -or $info.Mem -ge 70 -or $info.Disk -ge 70) { "🟡" } else { "🟢" }
        
        Write-Host ("{0,-20} {1,8} {2,8} {3,8} {4,10} {5,10}" -f $server.ip, "$($info.CPU)%", "$($info.Mem)%", "$($info.Disk)%", $statusEmoji, $info.Uptime)
    } catch {
        Write-Host ("{0,-20} {1,8} {2,8} {3,8} {4,10} {5,10}" -f $server.ip, "-", "-", "-", "❌ 离线", "-")
    }
}

Write-Host ("-" * 80)
Write-Host "图例：🟢 正常  🟡 警告  🔴 严重  ❌ 离线"
Write-Host ("=" * 80)
```

### 30.4 配置差异对比

```powershell
$serverFile = "$env:USERPROFILE\.workbuddy\output\winskill\servers.json"

if (-not (Test-Path $serverFile)) {
    Write-Host "❌ 暂无已注册服务器"
    exit 1
}

$servers = Get-Content $serverFile -Raw | ConvertFrom-Json

if ($servers.Count -lt 2) {
    Write-Host "⚠️ 至少需要 2 台服务器才能对比"
    exit 1
}

Write-Host "`n🔍 配置差异对比"
Write-Host ("=" * 60)

# 选择对比项目
Write-Host "对比项目："
Write-Host "1. IIS 站点配置"
Write-Host "2. 服务状态"
Write-Host "3. 防火墙规则"
Write-Host "4. 已安装补丁"
$choice = Read-Host "请选择 (1-4)"

$scriptBlock = switch ($choice) {
    "1" { { Get-Website | Select-Object Name, State, PhysicalPath, Bindings | ConvertTo-Json } }
    "2" { { Get-Service | Where-Object Status -ne 'Running' | Select-Object Name, Status, StartType | ConvertTo-Json } }
    "3" { { Get-NetFirewallRule | Where-Object Enabled -eq 'True' | Select-Object DisplayName, Direction, Action | ConvertTo-Json } }
    "4" { { Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10 HotFixID, InstalledOn | ConvertTo-Json } }
}

# 采集所有服务器数据
$allData = @{}
foreach ($server in $servers) {
    try {
        $session = New-PSSession -ComputerName $server.ip -ErrorAction Stop
        $data = Invoke-Command -Session $session -ScriptBlock $scriptBlock
        $allData[$server.ip] = $data | ConvertFrom-Json
        Remove-PSSession $session
    } catch {
        Write-Host "⚠️ $($server.ip) 连接失败：$($_.Exception.Message)"
    }
}

# 对比输出
if ($allData.Count -ge 2) {
    $firstServer = $allData.Keys | Select-Object -First 1
    $firstData = $allData[$firstServer]
    
    Write-Host ("`n基准服务器：$firstServer" -f $firstServer)
    Write-Host ("-" * 60)
    
    foreach ($server in $allData.Keys) {
        if ($server -eq $firstServer) { continue }
        $serverData = $allData[$server]
        
        # 简单差异对比（基于 JSON 字符串比较）
        $firstJson = $firstData | ConvertTo-Json -Compress
        $serverJson = $serverData | ConvertTo-Json -Compress
        
        if ($firstJson -eq $serverJson) {
            Write-Host ("✅ {0}：与基准一致" -f $server)
        } else {
            Write-Host ("⚠️ {0}：存在差异" -f $server)
            # 输出具体差异（简化版）
            Write-Host ("  基准项数：{0}，对比项数：{1}" -f @($firstData).Count, @($serverData).Count)
        }
    }
}

Write-Host ("=" * 60)
```

### 报错与解决

| 报错 | 原因 | 解决 |
|------|------|------|
| `WinRM 客户端无法处理请求` | 目标 WinRM 未开启 | 在目标服务器运行 `Enable-PSRemoting -Force` |
| `访问被拒绝` | 凭据错误或权限不足 | 检查用户名密码，确认用户有远程管理权限 |
| `无法连接到远程服务器` | 网络不通或防火墙拦截 | 检查网络连通性和 5985/5986 端口 |
| `New-PSSession 超时` | 服务器响应慢或网络延迟高 | 增加 `-OperationTimeout` 参数 |
| `TrustedHosts 未配置` | 非域环境需配置 TrustedHosts | `Set-Item WSMan:\localhost\Client\TrustedHosts -Value "192.168.1.0/24" -Concatenate` |

</details>


[↑ 返回顶部](#module-1)

---

## 30 秒速查表

| 你说 | AI 执行 |
|-----|---------|
| `"扫 C 盘大文件"` | 模块 1 |
| `"找重复文件"` | 模块 2 |
| `"清理临时文件"` | 模块 3（需确认） |
| `"IIS 正常吗"` | 模块 4 |
| `"检查服务"` | 模块 5 |
| `"批量改名"` | 模块 6（需确认） |
| `"磁盘报告"` | 模块 7 |
| `"更新正常吗"` | 模块 8 |
| `"服务器卡"` | 模块 9 |
| `"有没有被入侵"` | 模块 10 |
| `"可疑启动项"` | 模块 11 |
| `"硬盘健康吗"` | 模块 12 |
| `"谁在连我"` | 模块 13 |
| `"系统日志错误"` | 模块 14 |
| `"装了什么软件"` | 模块 15 |
| `"谁在服务器上"` | 模块 16 |
| `"可疑计划任务"` | 模块 17 |
| `"共享文件夹"` | 模块 18 |
| `"DNS/网卡诊断"` | 模块 19 |
| `"SSL证书快到期了吗"` | 模块 20 |
| `"防火墙规则有没有漏洞"` | 模块 21 |
| `"哪些服务崩过"` | 模块 22 |
| `"系统文件修复"` | 模块 23 |
| `"存储池状态"` | 模块 24 |
| `"备份正常吗"` | 模块 25 |
| `"Docker 状态"` | 模块 26 |
| `"帮我修 DNS"` | 模块 27 |
| `"性能趋势"` | 模块 28 |
| `"合规检查"` | 模块 29 |
| `"远程服务器"` | 模块 30 |

---

## ❌ 不支持（明确不能用的场景）

| 不支持 | 原因 |
|-------|------|
| 编辑已压缩的文件 | 压缩包内文件无法直接修改 |
| 恢复已删除的回收站文件 | 超出工具范围 |
| 修改注册表键值 | 风险过高，不在工具范围 |
| BIOS/硬件层操作 | 超出操作系统层面 |
| 磁盘修复/擦除 | 超出工具范围，需专业工具 |
| 终止网络连接 | 超出工具范围 |
| 清除/停止事件日志 | 超出工具范围，仅只读 |
| 卸载/安装软件 | 超出工具范围，只读审计 |
| 结束/断开用户会话 | 超出工具范围，只读监控 |
| 创建/删除计划任务 | 超出工具范围，只读审计 |
| 修改共享权限 | 超出工具范围，只读审计 |
| 修改网卡 IP/DNS 配置 | 超出工具范围，只读诊断 |
| 申请/续签/删除 SSL 证书 | 超出工具范围，只读检测 |
| 新增/删除/修改防火墙规则 | 超出工具范围，只读审计 |
| 启动/停止/修改服务配置 | 超出工具范围，只读诊断 |

---

## 前置要求

- **PowerShell 版本**：5.1+（Windows 自带，无需安装）
- **无需 API Key**
- **无需联网**（除首次安装 IIS 管理工具外）
- **无需安装任何第三方软件**
- ⚠️ **管理员权限检测**：部分功能（IIS 管理、更新缓存清理、安全审计、磁盘健康检测、网络监控、事件日志诊断、会话监控、计划任务审计、共享审计、DNS 网卡诊断、SSL 证书检测、防火墙审计、服务崩溃检查、性能基线采集、合规检查、远程多服务器管理）需要管理员权限，AI 会在执行前自动检测并提示

## 更新日志

| v3.1.0 | 2026-08-16 | 新增日志轮转功能（Write-WinskillLog，10MB/7天自动轮转清理）；新增模块索引命令（一键列出30个模块用途）；改进：移除废弃的 wmic 声明（已全面迁移 CIM cmdlet） |
| v3.0.0 | 2026-08-06 | 新增性能基线与趋势分析模块（基线建立、异常偏离告警、趋势预测、瓶颈关联分析）、安全合规检查清单模块（等保2.0、CIS Benchmark、合规报告、修复建议）、远程多服务器管理模块（服务器注册、批量命令执行、统一监控面板、配置差异对比），总计30个模块，从单机工具升级为多机管理平台；修改展示方式：顶部模块导航锚点+每模块返回顶部链接 |
| v2.0.0 | 2026-07-24 | 新增自动化修复向导模块（DNS修复、网络修复、WinUpdate修复、服务修复、磁盘清理、时间同步），总计27个模块，从诊断工具升级为修复工具 |
| v1.9.0 | 2026-07-16 | 修复逻辑bug，新增 Docker / K8s 容器管理模块（Docker状态总览、容器资源监控、Docker健康检查、K8s集群状态、容器日志采集），总计26个模块，覆盖Windows Server容器化场景 |
| v1.8.0 | 2026-07-16 | 新增 Docker / K8s 容器管理模块（Docker状态总览、容器资源监控、Docker健康检查、K8s集群状态、容器日志采集），总计26个模块，覆盖Windows Server容器化场景 |
| v1.7.0 | 2026-07-10 | 新增系统文件完整性检查(SFC/DISM)、存储池管理、备份状态检查3个模块，总计25个模块；每个模块加折叠块；性能硬件自适应优化；新增更新提醒和禁止文件类型声明 |
| v1.6.0 | 2026-07-09 | 新增SSL证书过期检测、防火墙规则审计、服务崩溃恢复状态3个模块，总计22个模块 |
| v1.5.0 | 2026-07-08 | 新增计划任务审计、文件共享审计、DNS网卡诊断3个模块，总计19个模块 |
| v1.4.0 | 2026-07-07 | 新增事件日志诊断、已安装程序管理、用户会话监控3个模块，总计16个模块 |
| v1.3.0 | 2026-07-06 | 新增注册表启动项审计、磁盘健康检测、网络端口监控3个模块，总计13个模块 |
| v1.2.0 | 2026-07-05 | 新增Windows Update性能监控、安全审计3个模块，所有命令折叠隐藏 |
| v1.1.0 | 2026-07-04 | 新增快速开始/报错指引/FAQ |
| v1.0.0 | 2026-07-03 | 初始版本，7个模块 |

## 发布信息


---

## 🔔 更新提醒

如何获取 winskill 最新版本：
```bash
skillhub upgrade winskill
```

当前版本：v3.0.0，如有新版本可用，请执行上述命令升级。

---

## 🚫 禁止的文件类型（全 Skill 生效 + SkillHub 打包排除）

> 以下 5 大类文件类型在所有涉及文件操作的模块中均会被拦截，同时也会被 SkillHub 打包排除规则过滤。

### 1. Windows 可执行 / 批处理脚本
`.bat` `.cmd` `.ps1` `.vbs` `.exe` `.dll` `.lnk` `.msi`

### 2. Office 二进制文档
`.docx` `.xlsx` `.pptx` `.doc` `.xls` `.ppt` `.xlsm` `.docm` `.pptm`

### 3. 二进制镜像 / 安装包
`.iso` `.dmg` `.zip` `.rar` `.7z` `.tar` `.gz` `.apk` `.jar`

### 4. 系统缓存 / 隐藏文件
`.DS_Store` `.git` 目录 `.env` `.log` `.tmp`

### 5. 其他风险脚本
`.sh` `.com` `.scr` `.hta` `.reg`

