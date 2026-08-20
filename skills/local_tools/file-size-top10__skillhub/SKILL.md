# File Size Top 10 - OpenClaw Skill

在 Windows 系统中快速找出指定目录下按文件大小排序的前 10 大文件。

## 功能特点

- 🚀 快速扫描指定目录下的所有文件
- 📊 自动排序并显示 Top 10 最大文件
- 🎨 彩色输出，直观显示文件大小比例
- 📁 支持自定义扫描深度
- 💾 支持多种大小单位显示（自动/MB/GB）
- 🔌 输出 JSON 格式，便于 OpenClaw 解析

## 使用方法

### 基本用法
```powershell
# 扫描当前目录
./run.ps1

# 扫描指定目录
./run.ps1 -path "C:\Users"

# 扫描并限制深度为 2 层
./run.ps1 -path "D:\Projects" -depth 2

# 使用 GB 单位显示
./run.ps1 -unit "GB"


run.ps1 内容
#!/usr/bin/env pwsh
# file-size-top10 - Find top 10 largest files in Windows system

param(
    [string]$path = ".",
    [int]$depth = -1,
    [string]$unit = "auto"
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 格式化文件大小
function Format-FileSize {
    param([long]$Bytes, [string]$Unit = "auto")
    
    if ($Unit -eq "auto") {
        switch ($Bytes) {
            { $_ -ge 1TB } { "{0:N2} TB" -f ($_ / 1TB); break }
            { $_ -ge 1GB } { "{0:N2} GB" -f ($_ / 1GB); break }
            { $_ -ge 1MB } { "{0:N2} MB" -f ($_ / 1MB); break }
            { $_ -ge 1KB } { "{0:N2} KB" -f ($_ / 1KB); break }
            default { "$_ B" }
        }
    }
    elseif ($Unit -eq "MB") {
        "{0:N2} MB" -f ($Bytes / 1MB)
    }
    elseif ($Unit -eq "GB") {
        "{0:N2} GB" -f ($Bytes / 1GB)
    }
    else {
        "$Bytes B"
    }
}

# 显示 Banner
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "  文件大小 Top 10 扫描工具" "Cyan"
Write-ColorOutput "========================================`n" "Cyan"

# 解析并验证路径
try {
    $resolvedPath = Resolve-Path $path -ErrorAction Stop
    Write-ColorOutput "扫描目录: $resolvedPath" "Yellow"
    Write-ColorOutput "扫描深度: $(if ($depth -eq -1) { '无限制' } else { $depth })`n" "Yellow"
}
catch {
    Write-ColorOutput "错误: 路径 '$path' 不存在或无法访问" "Red"
    exit 1
}

# 开始扫描
Write-ColorOutput "正在扫描文件（这可能需要一些时间）..." "Green"
$startTime = Get-Date

# 构建 Get-ChildItem 参数
$getChildItemParams = @{
    Path = $resolvedPath
    File = $true
    ErrorAction = "SilentlyContinue"
}

if ($depth -ne -1) {
    $getChildItemParams.Depth = $depth
}

# 获取所有文件并计算大小
$files = Get-ChildItem @getChildItemParams | ForEach-Object {
    try {
        $size = $_.Length
        if ($size -gt 0) {
            [PSCustomObject]@{
                Path = $_.FullName
                Size = $size
                LastModified = $_.LastWriteTime
                Name = $_.Name
            }
        }
    }
    catch {
        # 跳过无法访问的文件
    }
}

# 排序并取前 10
$top10 = $files | Sort-Object Size -Descending | Select-Object -First 10
$totalFiles = $files.Count
$totalSize = ($files | Measure-Object -Property Size -Sum).Sum

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

# 输出统计信息
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "扫描完成！" "Green"
Write-ColorOutput "总文件数: $totalFiles" "White"
Write-ColorOutput "总大小: $(Format-FileSize -Bytes $totalSize)" "White"
Write-ColorOutput "耗时: $([math]::Round($duration, 2)) 秒" "White"
Write-ColorOutput "========================================`n" "Cyan"

# 输出 Top 10 表格
if ($top10.Count -eq 0) {
    Write-ColorOutput "未找到任何文件。" "Yellow"
    exit 0
}

Write-ColorOutput "【 Top 10 最大文件 】`n" "Magenta"

# 计算最大文件大小用于进度条显示
$maxSize = if ($top10.Count -gt 0) { $top10[0].Size } else { 1 }

# 表格头
Write-ColorOutput ("{0,-4} {1,12} {2,15} {3,-50}" -f "排名", "大小(B)", "可读大小", "文件路径") "Cyan"
Write-ColorOutput ("{0,-4} {1,12} {2,15} {3,-50}" -f "----", "--------", "--------", "--------") "Gray"

$rank = 1
foreach ($file in $top10) {
    $sizeHuman = Format-FileSize -Bytes $file.Size -Unit $unit
    $relativePath = $file.Path.Replace($resolvedPath, "").TrimStart('\')
    if ([string]::IsNullOrEmpty($relativePath)) {
        $relativePath = $file.Name
    }
    
    # 根据排名设置颜色
    $color = switch ($rank) {
        1 { "Red" }
        2 { "Yellow" }
        3 { "Magenta" }
        default { "White" }
    }
    
    # 显示文件大小进度条
    $barLength = [math]::Min(20, [math]::Floor(($file.Size / $maxSize) * 20))
    $progressBar = "[" + ("█" * $barLength) + ("░" * (20 - $barLength)) + "]"
    
    Write-ColorOutput ("{0,-4} {1,12:N0} {2,15} {3,-50}" -f $rank, $file.Size, $sizeHuman, $relativePath) $color
    Write-ColorOutput ("      {0}" -f $progressBar) "Gray"
    
    $rank++
}

# 输出 JSON 格式（供 OpenClaw 解析）
Write-ColorOutput "`n---JSON_OUTPUT_START---" "Gray"
$jsonOutput = @{
    skill = "file-size-top10"
    scan_path = $resolvedPath.ToString()
    total_files = $totalFiles
    total_size_bytes = $totalSize
    total_size_human = (Format-FileSize -Bytes $totalSize)
    scan_duration_seconds = [math]::Round($duration, 2)
    top10 = @()
}

foreach ($file in $top10) {
    $jsonOutput.top10 += @{
        rank = $jsonOutput.top10.Count + 1
        size_bytes = $file.Size
        size_human = Format-FileSize -Bytes $file.Size -Unit $unit
        path = $file.Path
        name = $file.Name
        last_modified = $file.LastModified.ToString("yyyy-MM-dd HH:mm:ss")
    }
}

Write-Output ($jsonOutput | ConvertTo-Json -Depth 10)
Write-ColorOutput "---JSON_OUTPUT_END---" "Gray"

Write-ColorOutput "`n扫描完成！" "Green"