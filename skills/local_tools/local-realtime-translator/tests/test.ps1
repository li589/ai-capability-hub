param(
    [switch]$CleanEnv,
    [switch]$CleanModels,
    [switch]$SkipCleanup
)

$ErrorActionPreference = 'Stop'

# --- Configuration ---
$SkillName   = 'local-realtime-translator'
$VenvDir     = Join-Path $env:USERPROFILE ".openvino\venv\rt-translator"
$ModelsDir   = Join-Path $env:USERPROFILE ".openvino\models"
$PendingFile = Join-Path $env:USERPROFILE ".openvino\rt-translator-pending-request.json"
$DistDir     = Split-Path -Parent $PSScriptRoot
$ScriptsDir  = Join-Path $DistDir 'scripts'
$RunScript   = Join-Path $ScriptsDir 'run.ps1'
$WebUrl      = 'http://127.0.0.1:8766'

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
        $script:PassCount++
    } else {
        Write-Host "  [FAIL] $name" -ForegroundColor Red
        if ($detail) { Write-Host "         $detail" -ForegroundColor Yellow }
        $script:FailCount++
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
    if (Test-Path $VenvDir)     { Write-Host "  Removing venv: $VenvDir";     Remove-Item $VenvDir -Recurse -Force }
    if (Test-Path $PendingFile) { Write-Host "  Removing pending request file"; Remove-Item $PendingFile -Force }
    Write-Host "  Environment cleaned." -ForegroundColor Green
}

function Clean-Models {
    Write-TestHeader "Cleaning models for $SkillName"
    Stop-Server
    $m = Join-Path $ModelsDir 'Hunyuan-1.8B-Instruct-ov-int4'
    if (Test-Path $m) { Write-Host "  Removing model: $m"; Remove-Item $m -Recurse -Force }
    Write-Host "  (Framework caches under ~/.cache are left intact.)" -ForegroundColor Gray
    Write-Host "  Models cleaned." -ForegroundColor Green
}

# --- Cleanup-only modes ---
if ($CleanEnv)    { Clean-Environment; if (-not $SkipCleanup) { exit 0 } }
if ($CleanModels) { Clean-Models;      if (-not $SkipCleanup) { exit 0 } }

Write-TestHeader "Running tests for: $SkillName"

# From here on we invoke run.ps1 and capture its output with `2>&1 | Out-String`.
# run.ps1 -> install-env.ps1 shells out to uv (uv venv / uv pip), which writes
# normal progress to stderr (e.g. "Using CPython 3.11.14"). Under
# $ErrorActionPreference = 'Stop', a native command writing to stderr inside a
# `2>&1 |` pipeline is promoted to a terminating NativeCommandError — which on
# first run (when the venv is being created) aborts the whole test before any
# assertion runs. These tests judge success by exit code / output matching, not
# by Stop semantics, so switch to 'Continue' for the invocation section.
$ErrorActionPreference = 'Continue'

# --- Test 1: start the server (may need --continue on first run) ---
Write-Host ''
Write-Host '--- Test: start service ---' -ForegroundColor White
$maxContinues = 8
$started = $false
$out = & $RunScript 2>&1 | Out-String
$exit = $LASTEXITCODE
Write-Host $out
for ($i = 0; $i -lt $maxContinues -and $exit -eq 3; $i++) {
    Write-Host "  (download in progress; --continue $($i + 1)/$maxContinues)" -ForegroundColor Gray
    $out = & $RunScript --continue 2>&1 | Out-String
    $exit = $LASTEXITCODE
    Write-Host $out
}
$started = ($exit -eq 0)
Write-TestResult 'Service started (exit 0)' $started "exit code: $exit"

# --- Test 2: status reports running ---
if ($started) {
    Write-Host ''
    Write-Host '--- Test: status ---' -ForegroundColor White
    $statusOut = & $RunScript --status 2>&1 | Out-String
    Write-Host $statusOut
    Write-TestResult 'Status reports running' ($statusOut -match 'running') 'expected state=running'
}

# --- Test 3: web UI reachable ---
if ($started) {
    Write-Host ''
    Write-Host '--- Test: web UI reachable ---' -ForegroundColor White
    # The server reports state=running as soon as the pipeline thread is
    # spawned, but the HTTP server binds 8766 a moment later on its own thread.
    # Poll for readiness instead of a single fixed sleep so a slightly slow HTTP
    # bring-up doesn't fail the test.
    #
    # Probe with a raw TCP socket, NOT Invoke-WebRequest. On a machine behind a
    # corporate proxy (Internet Options ProxyEnable=1, e.g. proxy-ir.intel.com),
    # PS 5.1's Invoke-WebRequest routes even a 127.0.0.1 request through that
    # proxy, which answers 403 Forbidden. The documented bypass (nulling
    # WebRequest.DefaultWebProxy + `-Proxy $null`) is unreliable on PS 5.1 — a
    # `$null` argument is treated as "unset", so the bypass silently depends on
    # fragile DefaultWebProxy cache state and intermittently fails. A raw
    # TcpClient connects directly to the loopback address and is immune to ANY
    # proxy configuration, so it tests exactly what we care about: the local
    # HTTP server is bound on 8766 and returns 200 for "/".
    $host8766 = ([System.Uri]$WebUrl).Host
    $port8766 = ([System.Uri]$WebUrl).Port
    $reachable = $false
    $lastErr = ''
    $webDeadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $webDeadline) {
        $client = $null
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $client.Connect($host8766, $port8766)
            $stream = $client.GetStream()
            $stream.ReadTimeout = 5000
            $req = [System.Text.Encoding]::ASCII.GetBytes("GET / HTTP/1.0`r`nHost: $($host8766):$($port8766)`r`nConnection: close`r`n`r`n")
            $stream.Write($req, 0, $req.Length)
            $reader = New-Object System.IO.StreamReader($stream)
            $statusLine = $reader.ReadLine()
            if ($statusLine -match '^HTTP/\d\.\d\s+200\b') { $reachable = $true }
            else { $lastErr = "unexpected status line: $statusLine" }
        } catch {
            $lastErr = $_.Exception.Message
        } finally {
            if ($client) { $client.Close() }
        }
        if ($reachable) { break }
        Start-Sleep -Seconds 1
    }
    if (-not $reachable -and $lastErr) { Write-Host "         (last error: $lastErr)" -ForegroundColor DarkYellow }
    Write-TestResult 'Web UI responds 200' $reachable "GET $WebUrl"
}

# --- Test 4: stop ---
if ($started) {
    Write-Host ''
    Write-Host '--- Test: stop ---' -ForegroundColor White
    $stopOut = & $RunScript --stop 2>&1 | Out-String
    Write-Host $stopOut
    Start-Sleep -Seconds 2
    $statusOut = & $RunScript --status 2>&1 | Out-String
    Write-TestResult 'Server stopped' ($statusOut -match 'not running') 'expected: server not running'
}

# --- Summary ---
Write-TestHeader "Test Summary: $SkillName"
Write-Host "  Total:  $($PassCount + $FailCount)"
Write-Host "  Passed: $PassCount" -ForegroundColor Green
Write-Host "  Failed: $FailCount" -ForegroundColor $(if ($FailCount -gt 0) { 'Red' } else { 'Green' })
Write-Host ''

if (-not $SkipCleanup) { Stop-Server }
if ($FailCount -gt 0) { exit 1 }
exit 0
