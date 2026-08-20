param(
    [switch]$CleanEnv,
    [switch]$CleanModels,
    [switch]$SkipCleanup,
    [switch]$IncludeCapture,   # also exercise the no-path auto-capture flow (needs an interactive desktop)
    [int]$MaxContinue = 6      # max `run.ps1 --continue` retries while the model is still downloading
)

$ErrorActionPreference = 'Stop'

# --- Configuration ---
$SkillName = 'local-screenshot-qa'
$VenvDir = Join-Path $env:USERPROFILE ".openvino\venv\local-screenshot-qa"
$ModelsDir = Join-Path $env:USERPROFILE ".openvino\models\Qwen3-VL-4B-Instruct-int4-ov"
$TempDir = Join-Path $env:USERPROFILE ".openvino\temp\screenshot-qa"
$PendingFile = Join-Path $env:USERPROFILE ".openvino\screenshot-qa-pending-request.json"
$PipeName = '\\.\pipe\local-screenshot-qa'
$DistDir = Split-Path -Parent $PSScriptRoot
$ScriptsDir = Join-Path $DistDir 'scripts'
$RunScript = Join-Path $ScriptsDir 'run.ps1'

# --- Test fixtures (bundled next to this script) ---
# run.ps1 takes ONE positional string: "<question> <image_path>". client.py's
# _split_input picks the whitespace token that ends in an image extension as the
# image, the rest is the question. Keep fixture paths space-free.
$TestCases = @(
    @{
        Name       = 'Error screenshot, Chinese question'
        Question   = '看看这张报错截图说了什么'
        Image      = Join-Path $PSScriptRoot 'shot.png'
        ExpectExit = 0
    },
    @{
        Name       = 'Bar chart, Chinese question'
        Question   = '这张图表展示了什么内容？'
        Image      = Join-Path $PSScriptRoot 'chart.png'
        ExpectExit = 0
    },
    @{
        Name       = 'Flow diagram, English question'
        Question   = 'Describe what this diagram shows.'
        Image      = Join-Path $PSScriptRoot 'diagram.png'
        ExpectExit = 0
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
    if (Test-Path $ModelsDir) {
        Write-Host "  Removing models: $ModelsDir"
        Remove-Item $ModelsDir -Recurse -Force
    }
    Write-Host "  Models cleaned." -ForegroundColor Green
}

# --- Pre-flight checks ---
function Test-Prerequisites {
    Write-TestHeader "Checking prerequisites"
    if (-not (Test-Path $RunScript)) {
        Write-Host "  [MISSING] run.ps1: $RunScript" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] $RunScript" -ForegroundColor Green
    $allGood = $true
    foreach ($tc in $TestCases) {
        if (-not (Test-Path $tc.Image)) {
            Write-Host "  [MISSING] Test image: $($tc.Image)" -ForegroundColor Red
            $allGood = $false
        } else {
            Write-Host "  [OK] $($tc.Image)" -ForegroundColor Green
        }
    }
    if (-not $allGood) {
        Write-Host ''
        Write-Host '  Some bundled test images are missing.' -ForegroundColor Red
        exit 1
    }
}

# Invoke run.ps1 exactly as the host (a user) would, with one combined string.
# If the model is still downloading (exit 3), resume with `--continue` until it
# finishes or the retry budget runs out — so a cold runner can self-heal.
function Invoke-Run($inputStr) {
    $output = & $RunScript "$inputStr" 2>&1 | Out-String
    $code = $LASTEXITCODE
    Write-Host $output
    $tries = 0
    while ($code -eq 3 -and $tries -lt $MaxContinue) {
        $tries++
        Write-Host "    Model download in progress; resuming (--continue $tries/$MaxContinue)..." -ForegroundColor Yellow
        $output = & $RunScript '--continue' 2>&1 | Out-String
        $code = $LASTEXITCODE
        Write-Host $output
    }
    return $code
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
Test-Prerequisites

# Optional 4th case: no image path -> client.py auto-captures the primary screen.
# Off by default because it needs an interactive desktop (fails on a headless /
# session-0 runner). Enable with -IncludeCapture on an AIPC with a live session.
if ($IncludeCapture) {
    $TestCases += @{
        Name       = 'Auto-capture current screen (no path)'
        Question   = '看看我现在屏幕上是啥'
        Image      = ''
        ExpectExit = 0
    }
}

foreach ($tc in $TestCases) {
    Write-Host ''
    Write-Host "--- Test: $($tc.Name) ---" -ForegroundColor White
    if ($tc.Image) {
        $inputStr = "$($tc.Question) $($tc.Image)"
    } else {
        $inputStr = $tc.Question
    }
    Write-Host "    Input: $inputStr"

    $exitCode = Invoke-Run $inputStr

    $passed = ($exitCode -eq $tc.ExpectExit)
    Write-TestResult $tc.Name $passed "Exit code: $exitCode (expected $($tc.ExpectExit))"

    if ($passed) { $PassCount++ } else { $FailCount++ }
    $Results += @{ Name = $tc.Name; Passed = $passed; Exit = $exitCode }
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
