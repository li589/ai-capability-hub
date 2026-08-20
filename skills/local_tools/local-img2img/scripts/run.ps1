param(
    [Parameter(Position=0)]
    [string]$ImagePath,

    [Parameter(Position=1)]
    [string]$UserPrompt
)

$ErrorActionPreference = 'Stop'

# --- Logging ---
$LogDir = Join-Path $env:USERPROFILE '.openvino\log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile = Join-Path $LogDir "img2img-client-$LogTimestamp.log"
Add-Content $LogFile "[$(Get-Date)] Log initialized."

function Write-Log($msg) { Add-Content $LogFile "[$(Get-Date)] $msg" }

Write-Log "run.ps1 started with image: $ImagePath prompt: $UserPrompt"

if (-not $ImagePath) {
    Write-Log 'No image path argument provided.'
    Write-Host 'Usage: scripts\run.ps1 "<image-path>" "<prompt>"'
    Write-Host '       scripts\run.ps1 --continue'
    exit 1
}

if ($ImagePath -eq '--continue') {
    Write-Host 'Resuming pending request ...'
} else {
    if (-not $UserPrompt) {
        Write-Log 'No prompt argument provided.'
        Write-Host 'Usage: scripts\run.ps1 "<image-path>" "<prompt>"'
        Write-Host '       scripts\run.ps1 --continue'
        exit 1
    }
    if (-not (Test-Path -LiteralPath $ImagePath -PathType Leaf)) {
        Write-Log "Image path not found: $ImagePath"
        Write-Host "ERROR: image path not found: $ImagePath"
        exit 1
    }
    $ImagePath = (Resolve-Path -LiteralPath $ImagePath).Path
    Write-Host "Received image: $ImagePath"
    Write-Host "Received prompt: $UserPrompt"
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
if ($ImagePath -eq '--continue') {
    Write-Log 'Skipping scripts\install-env.ps1 for --continue.'
} else {
    Write-Log 'Running scripts\install-env.ps1.'
    Write-Host 'Setting up Python environment...'
    & "$SkillRoot\scripts\install-env.ps1" -SkillRoot $SkillRoot
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
    Write-Log 'scripts\install-env.ps1 completed successfully.'
}

Write-Host 'Python environment is ready. Launching client.py (Please be patient, it may take some time for the first use.) ...'

# --- Launch client.py ---
if ($ImagePath -eq '--continue') {
    Write-Log 'Launching scripts\client.py --continue.'
    & $VenvPy scripts\client.py --continue
} else {
    Write-Log "Launching scripts\client.py --image-path `"$ImagePath`" -i `"$UserPrompt`"."
    & $VenvPy scripts\client.py --image-path $ImagePath -i $UserPrompt
}
$exitCode = $LASTEXITCODE
Write-Log "scripts\client.py exited with code $exitCode"
Pop-Location
exit $exitCode

