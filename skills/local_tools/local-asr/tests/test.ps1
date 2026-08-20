param(
    [switch]$CleanEnv,
    [switch]$CleanModels,
    [switch]$SkipCleanup
)

$ErrorActionPreference = 'Stop'

# --- Configuration ---
$SkillName = 'local-asr'
$VenvDir = Join-Path $env:USERPROFILE ".openvino\venv\asr"
$ModelsDir = Join-Path $env:USERPROFILE ".openvino\models\Qwen3-ASR-0.6B-fp16-ov"
$TempDir = Join-Path $env:USERPROFILE ".openvino\temp\asr"
$PendingFile = Join-Path $env:USERPROFILE ".openvino\asr-pending-request.json"
$PipeName = '\\.\pipe\local-asr'
$DistDir = Split-Path -Parent $PSScriptRoot
$ScriptsDir = Join-Path $DistDir 'scripts'
$RunScript = Join-Path $ScriptsDir 'run.ps1'

# --- Test Files ---
$TestFilesDir = $PSScriptRoot

$TestCases = @(
    @{
        Name        = 'Transcribe MP3 file'
        AudioPath   = Join-Path $TestFilesDir 'test.mp3'
        Language    = 'auto'
        ExpectExit  = 0
    },
    @{
        Name        = 'Transcribe MP4 video file'
        AudioPath   = Join-Path $TestFilesDir 'qgs2.mp4'
        Language    = 'auto'
        ExpectExit  = 0
    },
    @{
        Name        = 'Transcribe MP3 with Chinese language hint'
        AudioPath   = Join-Path $TestFilesDir 'test.mp3'
        Language    = 'zh'
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
    if (Test-Path $ModelsDir) {
        Write-Host "  Removing models: $ModelsDir"
        Remove-Item $ModelsDir -Recurse -Force
    }
    Write-Host "  Models cleaned." -ForegroundColor Green
}

# --- Pre-flight checks ---
function Test-Prerequisites {
    Write-TestHeader "Checking prerequisites"
    $allGood = $true
    foreach ($tc in $TestCases) {
        if (-not (Test-Path $tc.AudioPath)) {
            Write-Host "  [MISSING] Test file: $($tc.AudioPath)" -ForegroundColor Red
            $allGood = $false
        } else {
            Write-Host "  [OK] $($tc.AudioPath)" -ForegroundColor Green
        }
    }
    if (-not $allGood) {
        Write-Host ''
        Write-Host '  Some test files are missing. Please ensure they exist before running tests.' -ForegroundColor Red
        exit 1
    }
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

foreach ($tc in $TestCases) {
    Write-Host ''
    Write-Host "--- Test: $($tc.Name) ---" -ForegroundColor White
    Write-Host "    File: $($tc.AudioPath)"
    Write-Host "    Language: $($tc.Language)"

    $output = & $RunScript $tc.AudioPath $tc.Language 2>&1 | Out-String
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
