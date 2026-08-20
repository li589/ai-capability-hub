# C盘临时文件清理脚本
# 安全清理Windows临时文件、缓存、回收站等

param(
    [switch]$CleanUserTemp = $true,
    [switch]$CleanSystemTemp = $true,
    [switch]$CleanPrefetch = $true,
    [switch]$CleanRecycleBin = $true,
    [switch]$CleanBrowserCache = $true,
    [switch]$CleanWindowsUpdateCache = $false,
    [switch]$CleanDnsCache = $true,
    [switch]$DryRun = $false
)

$totalCleaned = 0
$cleanupResults = @()

function Clean-Path {
    param(
        [string]$TargetPath,
        [string]$Description,
        [int]$DaysOld = 0
    )

    if (-not (Test-Path $TargetPath)) {
        Write-Host "[$Description] 路径不存在，跳过: $TargetPath" -ForegroundColor Gray
        return
    }

    try {
        if ($DaysOld -gt 0) {
            $items = Get-ChildItem -Path $TargetPath -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$DaysOld) }
        } else {
            $items = Get-ChildItem -Path $TargetPath -Recurse -File -ErrorAction SilentlyContinue
        }

        $size = ($items | Measure-Object -Property Length -Sum).Sum
        $count = ($items | Measure-Object).Count

        if ($count -eq 0) {
            Write-Host "[$Description] 无需清理" -ForegroundColor Gray
            return
        }

        if ($DryRun) {
            Write-Host "[$Description] [预览] 将清理 $count 个文件，释放 $([math]::Round($size / 1MB, 2)) MB" -ForegroundColor Yellow
        } else {
            $items | Remove-Item -Force -ErrorAction SilentlyContinue
            Write-Host "[$Description] 已清理 $count 个文件，释放 $([math]::Round($size / 1MB, 2)) MB" -ForegroundColor Green
            $script:totalCleaned += $size
        }

        $script:cleanupResults += [PSCustomObject]@{
            Description = $Description
            FileCount = $count
            SizeMB = [math]::Round($size / 1MB, 2)
        }
    }
    catch {
        Write-Host "[$Description] 清理时出错: $_" -ForegroundColor Red
    }
}

function Clean-PathDirect {
    param(
        [string]$TargetPath,
        [string]$Description
    )

    if (-not (Test-Path $TargetPath)) {
        Write-Host "[$Description] 路径不存在，跳过" -ForegroundColor Gray
        return
    }

    try {
        $items = Get-ChildItem -Path $TargetPath -ErrorAction SilentlyContinue
        $totalSize = 0
        $totalCount = 0

        # 先用robocopy做空目录镜像（绕过路径过长限制）再删除
        $tempEmpty = [System.IO.Path]::GetTempFileName()
        Remove-Item $tempEmpty -Force -ErrorAction SilentlyContinue
        New-Item -ItemType Directory -Path $tempEmpty -Force | Out-Null

        $nullDir = Join-Path $env:TEMP "empty_$(Get-Random)"
        New-Item -ItemType Directory -Path $nullDir -Force | Out-Null

        foreach ($item in $items) {
            try {
                $itemSize = (Get-ChildItem -Path $item.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
                $totalSize += $itemSize
                $totalCount++
                if (-not $DryRun) {
                    robocopy $nullDir $item.FullName /MIR /R:1 /W:1 /NJH /NJS /NDL /NP | Out-Null
                    Remove-Item $item.FullName -Force -Recurse -ErrorAction SilentlyContinue
                }
            }
            catch {}
        }

        Remove-Item $nullDir -Force -ErrorAction SilentlyContinue

        if ($DryRun) {
            Write-Host "[$Description] [预览] 将清理 $totalCount 个项目，释放 $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor Yellow
        } else {
            Write-Host "[$Description] 已清理 $totalCount 个项目，释放 $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor Green
            $script:totalCleaned += $totalSize
        }

        $script:cleanupResults += [PSCustomObject]@{
            Description = $Description
            FileCount = $totalCount
            SizeMB = [math]::Round($totalSize / 1MB, 2)
        }
    }
    catch {
        Write-Host "[$Description] 清理时出错: $_" -ForegroundColor Red
    }
}

Write-Host "=== C盘临时文件清理 ===" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "[预览模式] 仅显示将被清理的内容，不实际删除" -ForegroundColor Yellow
}
Write-Host ""

# 用户临时文件
if ($CleanUserTemp) {
    Clean-Path -TargetPath $env:TEMP -Description "用户临时文件" -DaysOld 7
}

# 系统临时文件
if ($CleanSystemTemp) {
    Clean-Path -TargetPath "C:\Windows\Temp" -Description "系统临时文件" -DaysOld 7
}

# Prefetch
if ($CleanPrefetch) {
    Clean-Path -TargetPath "C:\Windows\Prefetch" -Description "预读取缓存" -DaysOld 7
}

# 回收站
if ($CleanRecycleBin) {
    Write-Host "[回收站]" -ForegroundColor White
    if (-not $DryRun) {
        try {
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            Write-Host "[回收站] 已清空" -ForegroundColor Green
        }
        catch {
            Write-Host "[回收站] 清空时出错: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "[回收站] [预览] 将清空" -ForegroundColor Yellow
    }
}

# 浏览器缓存
if ($CleanBrowserCache) {
    $browserPaths = @(
        "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
        "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
        "$env:APPDATA\Mozilla\Firefox\Profiles"
    )
    foreach ($bp in $browserPaths) {
        if (Test-Path $bp) {
            Clean-Path -TargetPath $bp -Description "浏览器缓存: $bp"
        }
    }
}

# Windows更新缓存
if ($CleanWindowsUpdateCache) {
    Write-Host "注意: 清理Windows更新缓存后无法卸载已安装的更新" -ForegroundColor Yellow
    Clean-PathDirect -TargetPath "C:\Windows\SoftwareDistribution\Download" -Description "Windows更新缓存"
}

# DNS缓存
if ($CleanDnsCache) {
    if (-not $DryRun) {
        try {
            Clear-DnsClientCache
            Write-Host "[DNS缓存] 已清除" -ForegroundColor Green
        }
        catch {
            Write-Host "[DNS缓存] 清除时出错: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "[DNS缓存] [预览] 将清除" -ForegroundColor Yellow
    }
}

Write-Host ""
if (-not $DryRun -and $totalCleaned -gt 0) {
    Write-Host "总计清理释放: $([math]::Round($totalCleaned / 1MB, 2)) MB" -ForegroundColor Green
} elseif ($DryRun) {
    Write-Host "预览完成。去除 -DryRun 参数后执行实际清理。" -ForegroundColor Yellow
} else {
    Write-Host "未发现需要清理的文件。" -ForegroundColor Gray
}
Write-Host "=== 清理完成 ===" -ForegroundColor Cyan