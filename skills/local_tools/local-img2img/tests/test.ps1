param(
    [switch]$CleanEnv,
    [switch]$CleanModels,
    [switch]$SkipCleanup
)

$ErrorActionPreference = 'Stop'

# --- Configuration ---
$SkillName = 'local-img2img'
$VenvDir = Join-Path $env:USERPROFILE ".openvino\venv\img2img"
$ModelsDir = Join-Path $env:USERPROFILE ".openvino\models"
$TempDir = Join-Path $env:USERPROFILE ".openvino\temp\img2img"
$PendingFile = Join-Path $env:USERPROFILE ".openvino\img2img-pending-request.json"
$PipeName = '\\.\pipe\img2img'
$DistDir = Split-Path -Parent $PSScriptRoot
$ScriptsDir = Join-Path $DistDir 'scripts'
$RunScript = Join-Path $ScriptsDir 'run.ps1'

$TestCases = @(
    @{
        Name        = 'Generate image from Chinese prompt'
        ImagePath   = "$PSScriptRoot\dog.png"
        Prompt      = '把图中的小狗改成一只戴草帽的小猫'
        ExpectExit  = 0
    },
    @{
        Name        = 'Generate image from English prompt'
        ImagePath   = "$PSScriptRoot\girl.jpg"
        Prompt      = 'Change the girl in the picture to Japanese anime style.'
        ExpectExit  = 0
    },
    @{
        Name        = 'Generate image with detailed description'
        ImagePath   = "$PSScriptRoot\street.jpg"
        Prompt      = '把图中的街道改成赛博朋克风格，增加霓虹灯和飞行汽车'
        ExpectExit  = 0
    }
)

# --- Helpers ---
$PassCount = 0
$FailCount = 0
$Results = @()

function Write-TestHeader($msg) {
    Write-Host ''
    Write-Host ('=' * 60) -ForegroundColor Cyan
    Write-Host " $msg" -ForegroundColor Cyan
    Write-Host ('=' * 60) -ForegroundColor Cyan
}

function Write-TestResult($name, $passed, $detail) {
    if ($passed) {
        Write-Host "  [PASS] $name" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $name" -ForegroundColor Red
        if ($detail) { Write-Host "         $detail" -ForegroundColor Yellow }
    }
}

function Stop-Server {
    Write-Host "  Shutting down $SkillName server..." -ForegroundColor Gray
    $VenvPy = Join-Path $VenvDir 'Scripts\python.exe'
    if (Test-Path $VenvPy) {
        $clientPy = Join-Path $ScriptsDir 'client.py'
        & $VenvPy $clientPy --server-shutdown 2>$null
        Start-Sleep -Seconds 2
    }
}

function Clean-Environment {
    Write-TestHeader "Cleaning environment for $SkillName"
    Stop-Server
    if (Test-Path $VenvDir) {
        Write-Host "  Removing venv: $VenvDir"
        Remove-Item $VenvDir -Recurse -Force
    }
    if (Test-Path $TempDir) {
        Write-Host "  Removing temp: $TempDir"
        Remove-Item $TempDir -Recurse -Force
    }
    if (Test-Path $PendingFile) {
        Write-Host "  Removing pending request file"
        Remove-Item $PendingFile -Force
    }
    Write-Host "  Environment cleaned." -ForegroundColor Green
}

function Clean-Models {
    Write-TestHeader "Cleaning models for $SkillName"
    Stop-Server
    $imgModels = Get-ChildItem $ModelsDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'img2img|stable-diffusion|sd-|flux' }
    foreach ($m in $imgModels) {
        Write-Host "  Removing model: $($m.FullName)"
        Remove-Item $m.FullName -Recurse -Force
    }
    Write-Host "  Models cleaned." -ForegroundColor Green
}

# --- Main ---
if ($CleanEnv) {
    Clean-Environment
    if (-not $SkipCleanup) { exit 0 }
}

if ($CleanModels) {
    Clean-Models
    if (-not $SkipCleanup) { exit 0 }
}

Write-TestHeader "Running tests for: $SkillName"

foreach ($tc in $TestCases) {
    Write-Host ''
    Write-Host "--- Test: $($tc.Name) ---" -ForegroundColor White
    Write-Host "    Prompt: $($tc.Prompt)"

    $output = & $RunScript $tc.ImagePath "$($tc.Prompt)" 2>&1 | Out-String
    $exitCode = $LASTEXITCODE

    $passed = ($exitCode -eq $tc.ExpectExit)
    Write-TestResult $tc.Name $passed "Exit code: $exitCode (expected $($tc.ExpectExit))"

    if ($passed) { $PassCount++ } else { $FailCount++ }
    $Results += @{ Name = $tc.Name; Passed = $passed; Exit = $exitCode; Output = $output }
}

# --- Summary ---
Write-Host ''
Write-TestHeader "Test Summary: $SkillName"
Write-Host "  Total:  $($PassCount + $FailCount)"
Write-Host "  Passed: $PassCount" -ForegroundColor Green
Write-Host "  Failed: $FailCount" -ForegroundColor $(if ($FailCount -gt 0) { 'Red' } else { 'Green' })
Write-Host ''

if ($FailCount -gt 0) { exit 1 }
exit 0

