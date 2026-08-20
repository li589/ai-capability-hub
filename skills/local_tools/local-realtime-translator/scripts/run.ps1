param(
    [Parameter(Position=0)]
    [string]$Command = '',
    [string]$From = 'zh',
    [string]$To = 'en'
)

$ErrorActionPreference = 'Stop'

# --- Logging ---
$LogDir = Join-Path $env:USERPROFILE '.openvino\log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile = Join-Path $LogDir "rt-translator-client-$LogTimestamp.log"
Add-Content $LogFile "[$(Get-Date)] Log initialized."
function Write-Log($msg) { Add-Content $LogFile "[$(Get-Date)] $msg" }

Write-Log "run.ps1 started: Command='$Command' From='$From' To='$To'"

# --- Resolve paths early (needed for usage/help and all branches) ---
$SkillRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Normalize the command. Empty / a language-looking token => start.
$IsControl = $Command -in @('--continue', '--status', '--server-status', '--stop', '--server-shutdown')

if ($Command -eq '--help' -or $Command -eq '-h') {
    Write-Host 'Usage:'
    Write-Host '  scripts\run.ps1                       # start realtime translator (zh -> en), open web UI'
    Write-Host '  scripts\run.ps1 -From zh -To en       # choose direction (zh<->en)'
    Write-Host '  scripts\run.ps1 --continue            # resume a first-run model download'
    Write-Host '  scripts\run.ps1 --status              # show server status + web URL'
    Write-Host '  scripts\run.ps1 --stop                # stop the server (free mic + GPU)'
    Write-Host '  scripts\run.ps1 --restart             # force-restart server (reload code/models)'
    exit 0
}

# --- AIPC Check (with WMI fallback dev mode) ---
$PlatformExe = Join-Path $PSScriptRoot '..\bin\platform.exe'
Write-Log "Resolved PLATFORM_EXE=$PlatformExe"
if (-not (Test-Path $PlatformExe)) {
    Write-Log 'platform.exe not found; skipping AIPC check (dev mode).'
    Write-Host 'WARN: bin\platform.exe missing; skipping AIPC check.'
} else {
    $IsAipc = & $PlatformExe --is-aipc
    Write-Log "platform --is-aipc returned $IsAipc"
    if ($IsAipc -ne '1') {
        Write-Log 'This machine is not an Intel AIPC platform.'
        Write-Host 'This skill requires an Intel AIPC platform.'
        exit 1
    }
    Write-Host 'Intel AIPC platform detected. Continuing ...'
}

Push-Location $SkillRoot
Write-Log "Changed working directory to $SkillRoot"

# --- Read venv config from info.json ---
$EnvJson = Join-Path $SkillRoot 'info.json'
if (-not (Test-Path $EnvJson)) {
    Write-Host 'ERROR: info.json not found.'
    Pop-Location
    exit 1
}
$Config = Get-Content $EnvJson -Raw | ConvertFrom-Json
$VenvName = $Config.venv_name
if (-not $VenvName) {
    Write-Host 'ERROR: venv_name not found in info.json.'
    Pop-Location
    exit 1
}
$VenvDir = Join-Path $env:USERPROFILE ".openvino\venv\$VenvName"
$VenvPy = Join-Path $VenvDir 'Scripts\python.exe'
Write-Log "Resolved VENV_PY=$VenvPy"

# --- Ensure environment (skip heavy setup on control ops other than --continue) ---
if ($Command -eq '--status' -or $Command -eq '--server-status' -or
    $Command -eq '--stop' -or $Command -eq '--server-shutdown') {
    Write-Log "Control op '$Command'; skipping environment setup."
} else {
    Write-Host 'Setting up Python environment...'
    & "$SkillRoot\scripts\install-env.ps1" -SkillRoot $SkillRoot
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
    Write-Log 'install-env.ps1 completed.'
}

Write-Host 'Launching controller...'

# --- Launch client.py ---
switch ($Command) {
    '--continue' {
        & $VenvPy scripts\client.py --continue --log $LogFile
    }
    { $_ -eq '--status' -or $_ -eq '--server-status' } {
        & $VenvPy scripts\client.py --server-status --log $LogFile
    }
    { $_ -eq '--stop' -or $_ -eq '--server-shutdown' } {
        & $VenvPy scripts\client.py --server-shutdown --log $LogFile
    }
    '--restart' {
        & $VenvPy scripts\client.py --restart --from $From --to $To --log $LogFile
    }
    default {
        & $VenvPy scripts\client.py --from $From --to $To --log $LogFile
    }
}
$exitCode = $LASTEXITCODE
Write-Log "client.py exited with code $exitCode"
Pop-Location
exit $exitCode
