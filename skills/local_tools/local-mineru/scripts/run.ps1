#Requires -Version 5.1
<#
.SYNOPSIS
  Local document parsing entry point for Intel AIPC.

.DESCRIPTION
  Thin wrapper around client.py. Uses the shared server-dog for long-lived
  MinerU2.5-Pro inference. Accepts standard CLI arguments:

      run.ps1 <input> [output_dir] [--continue] [--check] [--server-status] [--server-shutdown]

  Exit codes follow the skill convention (0/1/2/3). See SKILL.md.
#>

param(
    [Parameter(Position=0)]
    [string]$InputFile = "",
    [Parameter(Position=1)]
    [string]$OutputDir = "",
    [switch]$Continue,
    [switch]$Check,
    [switch]$ServerStatus,
    [switch]$ServerShutdown
)

$ErrorActionPreference = 'Stop'

# --- Logging ---
$LogDir = Join-Path $env:USERPROFILE '.openvino\log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile = Join-Path $LogDir "mineru-client-$LogTimestamp.log"
Add-Content $LogFile "[$(Get-Date)] Log initialized."

function Write-Log($msg) { Add-Content $LogFile "[$(Get-Date)] $msg" }

Write-Log "run.ps1 started with arguments: Input=$InputFile Output=$OutputDir Cont=$Continue Chk=$Check Status=$ServerStatus Shutdown=$ServerShutdown"

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

# --- Setup paths ---
$SkillRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $SkillRoot
Write-Log "Changed working directory to $SkillRoot"

$EnvJson = Join-Path $SkillRoot 'info.json'
if (-not (Test-Path $EnvJson)) {
    Write-Log "ERROR: info.json not found at `"$EnvJson`"."
    Write-Host "ERROR: info.json not found."
    Pop-Location
    exit 1
}
$Config = Get-Content $EnvJson -Raw | ConvertFrom-Json
$VenvName = $Config.venv_name
if (-not $VenvName) {
    Write-Log "ERROR: venv_name not found in info.json."
    Write-Host "ERROR: venv_name not found in info.json."
    Pop-Location
    exit 1
}

$VenvDir = Join-Path $env:USERPROFILE ".openvino\venv\$VenvName"
$VenvPy = Join-Path $VenvDir 'Scripts\python.exe'
Write-Log "Resolved VENV_PY=$VenvPy"

# --- Ensure environment ---
if ($Continue) {
    Write-Log 'Skipping scripts\install-env.ps1 for --continue.'
} else {
    Write-Log 'Running scripts\install-env.ps1.'
    Write-Host 'Setting up Python environment...'
    & "$SkillRoot\scripts\install-env.ps1" -SkillRoot $SkillRoot
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
    Write-Log 'scripts\install-env.ps1 completed successfully.'
}

# --- --check short-circuit ---
if ($Check) {
    $ModelRoot = Join-Path $env:USERPROFILE (".openvino\\models\\" + $Config.models[0].dir_name)
    $RequiredFile = $Config.models[0].required_files[0]
    $RequiredPath = Join-Path $ModelRoot $RequiredFile
    if (Test-Path $RequiredPath) {
        Write-Host "Setup check passed:"
        Write-Host "  Platform: AIPC verified"
        Write-Host "  Python venv: $VenvDir"
        Write-Host "  Model: ready"
    } else {
        Write-Host "Setup check passed (model will download on first parse):"
        Write-Host "  Platform: AIPC verified"
        Write-Host "  Python venv: $VenvDir"
        Write-Host "  Model: not yet downloaded (will be fetched on first parse, 5-15 min)"
    }
    Write-Log "Setup check completed."
    Pop-Location
    exit 0
}

# --- Validate input ---
if (-not $Continue -and -not $ServerStatus -and -not $ServerShutdown -and -not $InputFile) {
    Write-Host "Usage: scripts\run.ps1 <input> [output_dir] [--continue]"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  scripts\run.ps1 C:\docs\report.pdf C:\output\"
    Write-Host "  scripts\run.ps1 D:\scan.png"
    Write-Host "  scripts\run.ps1 C:\docs\pdfs\              # batch: parse all PDF/images in folder"
    Write-Host "  scripts\run.ps1 C:\docs\pdfs\ C:\output\"
    Write-Host "  scripts\run.ps1 --continue"
    Pop-Location
    exit 1
}

Write-Host 'Python environment is ready. Launching client.py (Please be patient, it may take some time for the first use.) ...'

# --- Launch client.py ---
if ($ServerStatus) {
    Write-Log "Launching scripts\client.py --server-status"
    & $VenvPy scripts\client.py --server-status --log $LogFile
    $exitCode = $LASTEXITCODE
} elseif ($ServerShutdown) {
    Write-Log "Launching scripts\client.py --server-shutdown"
    & $VenvPy scripts\client.py --server-shutdown --log $LogFile
    $exitCode = $LASTEXITCODE
} elseif ($Continue) {
    Write-Log "Launching scripts\client.py --continue"
    & $VenvPy scripts\client.py --continue --log $LogFile
    $exitCode = $LASTEXITCODE
} else {
    $ClientArgs = @('scripts\client.py', '-i', $InputFile)
    if ($OutputDir) { $ClientArgs += @('-o', $OutputDir) }
    $ClientArgs += @('--log', $LogFile)
    Write-Log "Launching client: $VenvPy $($ClientArgs -join ' ')"
    & $VenvPy @ClientArgs
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 3) {
        Write-Host ""
        Write-Host "Model is downloading, run again to continue:"
        Write-Host "  scripts\run.ps1 --continue"
    }
}
Write-Log "scripts\client.py exited with code $exitCode"
Pop-Location
exit $exitCode
