
param(
    [int]$Value = 87
)

$ErrorActionPreference = 'Stop'

# --- Logging ---
$LogDir = Join-Path $env:USERPROFILE '.openvino\log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile = Join-Path $LogDir "vram-$LogTimestamp.log"
Add-Content $LogFile "[$(Get-Date)] Log initialized."

function Write-Log($msg) { Add-Content $LogFile "[$(Get-Date)] $msg" }

Write-Log "run.ps1 started with value: $Value"

# value 0 means: query and return the current system setting
if ($Value -eq 0) {
    $RegPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\MemoryManager'
    $RegName = 'SystemPartitionCommitLimitPercentage'
    $Current = (Get-ItemProperty -Path $RegPath -Name $RegName -ErrorAction SilentlyContinue).$RegName
    if ($null -eq $Current) {
        Write-Host "当前未设置 GPU 内存限制, 使用系统默认值"
        Write-Log "Current value not set; using system default."
    } else {
        Write-Host "当前 GPU 内存限制为 $Current%"
        Write-Log "Current value: $Current"
    }
    exit 0
}

# check the value range 13-87
if ($Value -lt 13 -or $Value -gt 87) {
    Write-Host "GPU内存限制设置失败, 只支持13%-87%之间的值"
    Write-Log "Invalid value: $Value. Valid range is 13-87."
    exit 1
}

# --- AIPC Check ---
$PlatformExe = Join-Path $PSScriptRoot '..\bin\platform.exe'
Write-Log "Resolved PLATFORM_EXE=$PlatformExe"
if (-not (Test-Path $PlatformExe)) {
    Write-Log 'platform.exe was not found; skipping AIPC check (dev mode).'
    Write-Host 'WARN: bin\platform.exe missing; skipping AIPC check.'
} else {
    $IsAipc = & $PlatformExe --is-aipc
    Write-Log "platform --is-aipc returned $IsAipc"
    if ($IsAipc -ne '1') {
        Write-Log 'This machine is not an Intel AIPC platform.'
        Write-Host 'This skill requires an Intel AIPC platform.'
        exit 1
    }
}


# --- Run the VBScript to set the registry key with admin privileges ---
Start-Process powershell -ArgumentList "Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\MemoryManager' -Name 'SystemPartitionCommitLimitPercentage' -Value $Value" -Verb RunAs
Write-Host "GPU内存限制已更改, 请问需要重启电脑以生效吗?"
exit 0