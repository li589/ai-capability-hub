param(
    [switch]$SkipCleanup
)

$ErrorActionPreference = 'Stop'

# --- Configuration ---
$SkillName  = 'local-ocr-npu'
$ScriptDir  = $PSScriptRoot
$RunScript  = Join-Path $ScriptDir 'run.ps1'

# Test images are expected in this directory.
# Place at least one sample image there before running tests.
$TestImagesDir = Join-Path $env:USERPROFILE '.openvino\tests'

$TestCases = @(
    @{
        Name       = 'OCR single image (NPU)'
        InputPath  = Join-Path $TestImagesDir 'test_ocr.jpg'
        Device     = 'npu'
        ExpectExit = 0
    },
    @{
        Name       = 'OCR single image (CPU fallback)'
        InputPath  = Join-Path $TestImagesDir 'test_ocr.jpg'
        Device     = 'cpu'
        ExpectExit = 0
    },
    @{
        Name       = 'OCR directory of images'
        InputPath  = $TestImagesDir
        Device     = 'npu'
        ExpectExit = 0
    }
)

# --- Helpers ---
$PassCount = 0
$FailCount = 0

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

function Test-Prerequisites {
    Write-TestHeader 'Checking prerequisites'
    $allGood = $true
    $singleImagePath = Join-Path $TestImagesDir 'test_ocr.jpg'
    if (-not (Test-Path $singleImagePath)) {
        Write-Host "  [MISSING] $singleImagePath" -ForegroundColor Red
        Write-Host '            Place a test image at this path before running tests.' -ForegroundColor Yellow
        $allGood = $false
    } else {
        Write-Host "  [OK] $singleImagePath" -ForegroundColor Green
    }
    if (-not $allGood) {
        Write-Host ''
        Write-Host '  Prerequisites not satisfied.' -ForegroundColor Red
        exit 1
    }
}

# --- Main ---
Write-TestHeader "Running tests for: $SkillName"
Test-Prerequisites

foreach ($tc in $TestCases) {
    Write-Host ''
    Write-Host "--- Test: $($tc.Name) ---" -ForegroundColor White
    Write-Host "    InputPath: $($tc.InputPath)"
    Write-Host "    Device:    $($tc.Device)"

    $output = & $RunScript $tc.InputPath -Device $tc.Device 2>&1 | Out-String
    $exitCode = $LASTEXITCODE

    $passed = ($exitCode -eq $tc.ExpectExit)
    Write-TestResult $tc.Name $passed "Exit code: $exitCode (expected $($tc.ExpectExit))"
    if ($passed) { $PassCount++ } else { $FailCount++ }

    if (-not $passed) {
        Write-Host '    Output:' -ForegroundColor Yellow
        $output -split "`n" | Select-Object -First 20 | ForEach-Object { Write-Host "      $_" -ForegroundColor Yellow }
    }
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
