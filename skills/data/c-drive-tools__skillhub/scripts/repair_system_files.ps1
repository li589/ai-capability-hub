# 系统文件修复脚本
# 使用 SFC 和 DISM 工具修复 Windows 系统文件
# 需要管理员权限

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Write-Host "=== Windows 系统文件修复 ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Admin)) {
    Write-Host "警告: 此脚本需要管理员权限才能运行SFC和DISM。" -ForegroundColor Red
    Write-Host "请以管理员身份重新运行此脚本。" -ForegroundColor Yellow
    exit 1
}

# Step 1: 清理组件存储
Write-Host "[Step 1/4] 清理组件存储..." -ForegroundColor Yellow
try {
    $result = Start-Process -FilePath "dism.exe" -ArgumentList "/Online /Cleanup-Image /StartComponentCleanup" -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\dism_component.log" -RedirectStandardError "$env:TEMP\dism_component_err.log"
    $output = Get-Content "$env:TEMP\dism_component.log" -Raw -ErrorAction SilentlyContinue
    if ($result.ExitCode -eq 0) {
        Write-Host "组件存储清理完成。" -ForegroundColor Green
    } else {
        Write-Host "组件存储清理完成(退出码: $($result.ExitCode))。" -ForegroundColor Yellow
        Write-Host $output -ForegroundColor Gray
    }
}
catch {
    Write-Host "清理组件存储失败: $_" -ForegroundColor Red
}
Write-Host ""

# Step 2: 检查系统健康状态
Write-Host "[Step 2/4] 检查系统健康状态..." -ForegroundColor Yellow
try {
    $result = Start-Process -FilePath "dism.exe" -ArgumentList "/Online /Cleanup-Image /CheckHealth" -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\dism_check.log" -RedirectStandardError "$env:TEMP\dism_check_err.log"
    $output = Get-Content "$env:TEMP\dism_check.log" -Raw -ErrorAction SilentlyContinue
    Write-Host $output -ForegroundColor White
    if ($result.ExitCode -eq 0) {
        Write-Host "组件存储健康检查通过。" -ForegroundColor Green
    } else {
        Write-Host "组件存储存在损坏(退出码: $($result.ExitCode))。" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "健康检查失败: $_" -ForegroundColor Red
}
Write-Host ""

# Step 3: 扫描镜像健康
Write-Host "[Step 3/4] 扫描并检查镜像健康..." -ForegroundColor Yellow
try {
    $result = Start-Process -FilePath "dism.exe" -ArgumentList "/Online /Cleanup-Image /ScanHealth" -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\dism_scan.log" -RedirectStandardError "$env:TEMP\dism_scan_err.log"
    $output = Get-Content "$env:TEMP\dism_scan.log" -Raw -ErrorAction SilentlyContinue
    Write-Host $output -ForegroundColor White
    if ($result.ExitCode -eq 0) {
        Write-Host "镜像扫描通过，未发现损坏。" -ForegroundColor Green
    } else {
        Write-Host "镜像存在损坏，需要修复(退出码: $($result.ExitCode))。" -ForegroundColor Red
        Write-Host "尝试进行修复..." -ForegroundColor Yellow

        $repairResult = Start-Process -FilePath "dism.exe" -ArgumentList "/Online /Cleanup-Image /RestoreHealth" -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\dism_restore.log" -RedirectStandardError "$env:TEMP\dism_restore_err.log"
        $repairOutput = Get-Content "$env:TEMP\dism_restore.log" -Raw -ErrorAction SilentlyContinue
        Write-Host $repairOutput -ForegroundColor White
        if ($repairResult.ExitCode -eq 0) {
            Write-Host "DISM 镜像修复成功。" -ForegroundColor Green
        } else {
            Write-Host "DISM 修复失败(退出码: $($repairResult.ExitCode))。" -ForegroundColor Red
            Write-Host "建议检查Windows Update服务是否正常，或使用安装介质进行修复。" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "镜像扫描失败: $_" -ForegroundColor Red
}
Write-Host ""

# Step 4: SFC 系统文件检查
Write-Host "[Step 4/4] SFC 系统文件检查..." -ForegroundColor Yellow
try {
    $result = Start-Process -FilePath "sfc.exe" -ArgumentList "/scannow" -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\sfc_scan.log" -RedirectStandardError "$env:TEMP\sfc_scan_err.log"
    $output = Get-Content "$env:TEMP\sfc_scan.log" -Raw -ErrorAction SilentlyContinue
    Write-Host $output -ForegroundColor White

    $errOutput = Get-Content "$env:TEMP\sfc_scan_err.log" -Raw -ErrorAction SilentlyContinue
    if ($errOutput) { Write-Host $errOutput -ForegroundColor Gray }

    if ($result.ExitCode -eq 0) {
        Write-Host "SFC 扫描完成，未发现任何完整性冲突。" -ForegroundColor Green
    } else {
        Write-Host "SFC 发现问题并已修复(退出码: $($result.ExitCode))。" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "SFC扫描失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 系统文件修复完成 ===" -ForegroundColor Cyan
Write-Host "提示: 如果SFC修复了系统文件，建议重启系统使更改生效。" -ForegroundColor Yellow
