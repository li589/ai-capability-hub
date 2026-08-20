# C盘空间分析脚本
# 分析C盘空间占用情况，找出大文件和占用空间多的目录

param(
    [string]$Path = "C:\",
    [int]$TopN = 20,
    [switch]$IncludeSystemFiles = $false
)

Write-Host "=== C盘空间分析报告 ===" -ForegroundColor Cyan
Write-Host ""

# 获取C盘总体信息
$drive = Get-PSDrive -Name C -PSProvider FileSystem
Write-Host "C盘总容量: $([math]::Round($drive.Used + $drive.Free, 2)) GB"
Write-Host "C盘已用: $([math]::Round($drive.Used, 2)) GB"
Write-Host "C盘可用: $([math]::Round($drive.Free, 2)) GB"
Write-Host "使用率: $([math]::Round($drive.Used / ($drive.Used + $drive.Free) * 100, 1))%"
Write-Host ""

# 分析各顶级目录大小
Write-Host "=== 顶级目录大小分析 ===" -ForegroundColor Yellow
$topDirs = Get-ChildItem -Path $Path -Directory -ErrorAction SilentlyContinue | Where-Object {
    $IncludeSystemFiles -or $_.Name -notmatch "^(Windows|ProgramData|System Volume Information|\$Recycle.Bin)$"
}

$dirSizes = @()
foreach ($dir in $topDirs) {
    Write-Host "正在计算: $($dir.Name) ..." -ForegroundColor Gray
    try {
        $size = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $dirSizes += [PSCustomObject]@{
            Name = $dir.Name
            Path = $dir.FullName
            SizeGB = [math]::Round($size / 1GB, 2)
            SizeMB = [math]::Round($size / 1MB, 2)
        }
    }
    catch {
        $dirSizes += [PSCustomObject]@{
            Name = $dir.Name
            Path = $dir.FullName
            SizeGB = 0
            SizeMB = 0
        }
    }
}

$dirSizes | Sort-Object SizeGB -Descending | Select-Object -First $TopN | Format-Table -AutoSize
Write-Host ""

# 查找大文件（>100MB）
Write-Host "=== 查找大文件 (>100 MB) ===" -ForegroundColor Yellow
try {
    $largeFiles = Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 100MB } | Select-Object -First 30
    if ($largeFiles) {
        $largeFiles | Select-Object Name, @{Name="Size(MB)"; Expression={[math]::Round($_.Length / 1MB, 2)}}, FullName | Sort-Object Length -Descending | Format-Table -AutoSize
    } else {
        Write-Host "未找到大于100MB的文件。" -ForegroundColor Gray
    }
}
catch {
    Write-Host "扫描大文件时出错: $_" -ForegroundColor Red
}
Write-Host ""

# 分析常见占用位置
Write-Host "=== 常见占用位置分析 ===" -ForegroundColor Yellow
$commonPaths = @(
    "$env:USERPROFILE\Downloads",
    "$env:USERPROFILE\Desktop",
    "$env:USERPROFILE\Videos",
    "$env:USERPROFILE\Pictures",
    "C:\Windows\Temp",
    "$env:TEMP",
    "C:\hiberfil.sys",
    "C:\pagefile.sys",
    "C:\swapfile.sys"
)

foreach ($p in $commonPaths) {
    if (Test-Path $p) {
        if ((Get-Item $p) -is [System.IO.FileInfo]) {
            $file = Get-Item $p
            Write-Host "$p : $([math]::Round($file.Length / 1GB, 2)) GB"
        } else {
            $size = (Get-ChildItem -Path $p -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Write-Host "$p : $([math]::Round($size / 1GB, 2)) GB"
        }
    }
}

Write-Host ""
Write-Host "=== 分析完成 ===" -ForegroundColor Green
