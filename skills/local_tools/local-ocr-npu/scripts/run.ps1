param(
    [Parameter(Position=0)]
    [string]$InputPath,
    [string]$Device = ''
)

$ErrorActionPreference = 'Stop'

# Allow HTTPS regardless of certificate validation (handles corporate SSL inspection)
try {
    Add-Type -TypeDefinition @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class PpocrTrustAll : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint sp, X509Certificate cert, WebRequest req, int err) { return true; }
}
"@
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object PpocrTrustAll
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
} catch { }

# Use system proxy with default credentials (required for corporate networks e.g. Intel)
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials

# ===========================================================================
#  Configuration — paths default to skill root (bin\ / models\).
#  Override via environment variables or edit defaults below.
# ===========================================================================
$SkillRoot          = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ModelsRoot         = Join-Path $env:USERPROFILE '.openvino\models'
$DefaultDevice      = if ($env:OCR_DEVICE)       { $env:OCR_DEVICE }       else { 'npu' }
$DefaultPpOcrExe    = if ($env:PPOCR_EXE)        { $env:PPOCR_EXE }        else { Join-Path $SkillRoot 'bin\ppocr.exe' }
$DefaultDetModelDir = if ($env:DET_MODEL_DIR)     { $env:DET_MODEL_DIR }    else { Join-Path $ModelsRoot 'PP-OCRv5_server_det_ov' }
$DefaultRecModelDir = if ($env:REC_MODEL_DIR)     { $env:REC_MODEL_DIR }    else { Join-Path $ModelsRoot 'PP-OCRv5_server_rec_ov' }
$DetModelName       = if ($env:DET_MODEL_NAME)    { $env:DET_MODEL_NAME }   else { 'PP-OCRv5_server_det' }
$RecModelName       = if ($env:REC_MODEL_NAME)    { $env:REC_MODEL_NAME }   else { 'PP-OCRv5_server_rec' }
$RecBatchSize       = if ($env:REC_BATCH_SIZE)    { $env:REC_BATCH_SIZE }   else { '1' }
$RecScoreThresh     = if ($env:REC_SCORE_THRESH)  { $env:REC_SCORE_THRESH } else { '0.0' }

# ModelScope is primary; HuggingFace is the fallback
$MsRepoUrl   = if ($env:MS_REPO_URL)       { $env:MS_REPO_URL }       else { 'https://modelscope.cn/models/FionaGu1019/PaddleOCR-OpenVINO/resolve/master' }
$HfRepoUrl   = if ($env:HF_REPO_URL)       { $env:HF_REPO_URL }       else { 'https://huggingface.co/Fiona1019/PaddleOCR-OpenVINO/resolve/main' }
$BinAssetName = 'ppocr-windows-x64.zip'
# ===========================================================================

$EffectiveDevice = if ($Device) { $Device } else { $DefaultDevice }
$PpOcrExe        = $DefaultPpOcrExe
$DetModelDir     = $DefaultDetModelDir
$RecModelDir     = $DefaultRecModelDir

# --- Logging ---
$LogDir = Join-Path $env:USERPROFILE '.openvino\log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile = Join-Path $LogDir "ocr-npu-$LogTimestamp.log"
Add-Content $LogFile "[$(Get-Date)] Log initialized. SkillRoot=$SkillRoot"
function Write-Log($msg) { Add-Content $LogFile "[$(Get-Date)] $msg" }

# --- Argument check ---
if (-not $InputPath) {
    Write-Host 'Usage: scripts\run.ps1 "<image_file_or_directory>" [-Device cpu|npu|gpu]'
    exit 1
}

Write-Log "run.ps1 started: InputPath='$InputPath' Device='$EffectiveDevice'"
Write-Host "========================================"
Write-Host " Local NPU OCR"
Write-Host "========================================"

# ===========================================================================
#  STEP 1 -- Environment check
# ===========================================================================
Write-Host ""
Write-Host "[1/4] Checking environment..."

$PlatformExe = Join-Path $SkillRoot 'bin\platform.exe'

function Test-NpuPresent {
    try {
        $npu = Get-PnpDevice -ErrorAction SilentlyContinue |
               Where-Object { $_.FriendlyName -match 'NPU|Neural' -and $_.Status -eq 'OK' } |
               Select-Object -First 1
        return ($null -ne $npu)
    } catch { return $false }
}

if (-not (Test-Path $PlatformExe)) {
    if ($EffectiveDevice -eq 'npu') {
        $hasNpu = Test-NpuPresent
        Write-Log "WMI NPU detected: $hasNpu"
        if ($hasNpu) {
            Write-Host "  [OK] Intel NPU detected (WMI)"
        } else {
            Write-Host "  [WARN] No Intel NPU found -- falling back to CPU"
            $EffectiveDevice = 'cpu'
            Write-Log 'Device overridden to CPU (no NPU via WMI).'
        }
    }
} else {
    $IsAipc = & $PlatformExe --is-aipc
    Write-Log "platform --is-aipc returned $IsAipc"
    if ($IsAipc -ne '1') {
        if ($EffectiveDevice -eq 'npu') {
            Write-Host "  [WARN] Not an Intel AIPC platform -- falling back to CPU"
            $EffectiveDevice = 'cpu'
            Write-Log 'Device overridden to CPU.'
        }
    } else {
        Write-Host "  [OK] Intel AIPC platform detected (NPU available)"
    }
}

# --- Validate input path ---
if (-not (Test-Path $InputPath)) {
    Write-Host "  [ERROR] Input path does not exist: $InputPath"
    exit 1
}
Write-Host "  [OK] Device: $($EffectiveDevice.ToUpper())  |  Input: $InputPath"

# ===========================================================================
#  DOWNLOAD -- on first install, download runtime + models synchronously,
#  showing a progress message and waiting until it finishes before continuing.
# ===========================================================================
$BinDir       = Split-Path $PpOcrExe -Parent
$downloadLog  = Join-Path $SkillRoot 'download.log'

$needBin = -not (Test-Path (Join-Path $BinDir 'openvino.dll'))
$needDet = -not (Test-Path $DetModelDir)
$needRec = -not (Test-Path $RecModelDir)

if ($needBin -or $needDet -or $needRec) {
    $dlScript = Join-Path $PSScriptRoot 'download.ps1'
    Write-Host ""
    Write-Host "  [DL] 首次安装: 正在下载运行时和模型 (~200 MB), 请稍候..."
    Write-Host "       进度日志: $downloadLog"
    Write-Log "Synchronous download starting via download.ps1."

    & $dlScript -SkillRoot $SkillRoot `
                -HfRepoUrl $HfRepoUrl `
                -MsRepoUrl $MsRepoUrl `
                -BinAssetName $BinAssetName `
                -DetModelDir $DetModelDir `
                -RecModelDir $RecModelDir

    Write-Host "  [DL] 下载完成, 继续运行..."
    Write-Log "Synchronous download finished; continuing."
}

# ===========================================================================
#  STEP 2 -- Validate runtime (ppocr.exe + DLLs)
# ===========================================================================
Write-Host ""
Write-Host "[2/4] Checking OCR runtime..."

if (-not (Test-Path $PpOcrExe)) {
    Write-Host "  [ERROR] ppocr.exe not found: $PpOcrExe"
    Write-Host "          Download from: https://github.com/$GithubRepo/releases/latest"
    exit 1
}
Write-Host "  [OK] ppocr.exe ready ($([math]::Round((Get-Item $PpOcrExe).Length/1KB,0)) KB)"
Write-Log "ppocr.exe resolved: $PpOcrExe"

# ===========================================================================
#  STEP 3 -- Validate models
# ===========================================================================
function Download-ModelDir {
    param([string]$ModelName, [string]$DestDir)
    Write-Host "  [...] Downloading model $ModelName (first-time install)..."
    Write-Log "Auto-download model: $ModelName -> $DestDir"
    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null

    $apiUrl = "https://huggingface.co/api/models/Fiona1019/PaddleOCR-OpenVINO"
    try {
        $modelInfo = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 30
        $siblings = $modelInfo.siblings | Where-Object { $_.rfilename -like "$ModelName/*" }
    } catch {
        Write-Log "HF API failed: $_  Using static file list."
        $siblings = $null
    }

    if (-not $siblings) {
        $knownFiles = @('inference.xml', 'inference.bin', 'inference.yml')
        if ($ModelName -match '_det_') { $knownFiles += 'inference_960.xml' }
        if ($ModelName -match '_rec_') {
            $knownFiles += @('inference_320.xml','inference_480.xml','inference_640.xml',
                             'inference_800.xml','inference_1280.xml')
        }
        $siblings = $knownFiles | ForEach-Object { [pscustomobject]@{ rfilename = "$ModelName/$_" } }
    }

    $downloaded = 0; $failed = 0
    foreach ($s in $siblings) {
        $fileName = Split-Path $s.rfilename -Leaf
        $destFile  = Join-Path $DestDir $fileName
        $ok = $false
        foreach ($url in @("$HfRepoUrl/$($s.rfilename)", "$MsRepoUrl/$($s.rfilename)")) {
            try {
                $ProgressPreference = 'SilentlyContinue'
                Invoke-WebRequest -Uri $url -OutFile $destFile -TimeoutSec 300 -UseBasicParsing
                $ProgressPreference = 'Continue'
                Write-Log "  OK: $fileName"
                $ok = $true; break
            } catch { Write-Log "  FAIL: $fileName from $url : $_" }
        }
        if ($ok) { $downloaded++ } else { $failed++; Write-Host "  [WARN] Failed to download: $fileName" }
    }

    if ($failed -gt 0) {
        Write-Host "  [WARN] Model $ModelName incomplete ($failed file(s) failed)"
        Write-Host "         Manual download: https://huggingface.co/Fiona1019/PaddleOCR-OpenVINO"
    } else {
        Write-Host "  [OK] Model downloaded: $ModelName ($downloaded files)"
    }
    Write-Log "Model download done: $ModelName  ok=$downloaded  fail=$failed"
}

$needDownloadDet = -not (Test-Path $DetModelDir)
$needDownloadRec = -not (Test-Path $RecModelDir)

if ($needDownloadDet -or $needDownloadRec) {
    Write-Host ""
    Write-Host "[3/4] Downloading OCR models (first-time install, ~176 MB)..."
    New-Item -ItemType Directory -Path $ModelsRoot -Force | Out-Null
    if ($needDownloadDet) { Download-ModelDir -ModelName (Split-Path $DetModelDir -Leaf) -DestDir $DetModelDir }
    if ($needDownloadRec) { Download-ModelDir -ModelName (Split-Path $RecModelDir -Leaf) -DestDir $RecModelDir }
} else {
    Write-Host ""
    Write-Host "[3/4] Checking OCR models..."
    Write-Host "  [OK] Det model: $(Split-Path $DetModelDir -Leaf)"
    Write-Host "  [OK] Rec model: $(Split-Path $RecModelDir -Leaf)"
}

if (-not (Test-Path $DetModelDir)) {
    Write-Host "  [ERROR] Det model not found: $DetModelDir"
    exit 1
}
if (-not (Test-Path $RecModelDir)) {
    Write-Host "  [ERROR] Rec model not found: $RecModelDir"
    exit 1
}

# --- Add bin to PATH so DLLs are found ---
$PpOcrDir = Split-Path $PpOcrExe -Parent
$env:PATH = "$PpOcrDir;$env:PATH"

# --- Prepare output dir ---
$SavePath = Join-Path $env:TEMP 'ocr_npu_skill_output'
if (Test-Path $SavePath) { Remove-Item $SavePath -Recurse -Force }
New-Item -ItemType Directory -Path $SavePath | Out-Null
Write-Log "Output dir: $SavePath"

# ===========================================================================
#  STEP 4 -- Run OCR
# ===========================================================================
Write-Host ""
Write-Host "[4/4] Running OCR..."
$inputName = Split-Path $InputPath -Leaf
if ((Get-Item $InputPath).PSIsContainer) { $inputName = "$inputName (directory)" }
Write-Host "  Input: $inputName  |  Device: $($EffectiveDevice.ToUpper())  |  Model: $DetModelName + $RecModelName"
if ($EffectiveDevice -eq 'npu') {
    Write-Host "  Note: first NPU run compiles model (~27s); subsequent runs ~0.3s"
}
Write-Log "Running ppocr.exe: device=$EffectiveDevice input=$InputPath"
$t0 = Get-Date

Push-Location $PpOcrDir
# Convert absolute paths to relative (avoids long-path crash in ppocr.exe)
$RelDetModelDir = Resolve-Path -Relative $DetModelDir
$RelRecModelDir = Resolve-Path -Relative $RecModelDir
$RelInputPath   = Resolve-Path -Relative $InputPath
$RelSavePath    = Resolve-Path -Relative $SavePath
& $PpOcrExe ocr `
    "--input=$RelInputPath" `
    "--text_detection_model_name=$DetModelName" `
    "--text_detection_model_dir=$RelDetModelDir" `
    "--text_recognition_model_name=$RecModelName" `
    "--text_recognition_model_dir=$RelRecModelDir" `
    "--device=$EffectiveDevice" `
    "--text_recognition_batch_size=$RecBatchSize" `
    "--text_rec_score_thresh=$RecScoreThresh" `
    "--save_path=$RelSavePath"
$ExitCode = $LASTEXITCODE
Pop-Location
Write-Log "ppocr.exe exited: code=$ExitCode"

# Auto-retry on CPU if NPU failed
if ($ExitCode -ne 0 -and $EffectiveDevice -eq 'npu') {
    Write-Host "  [WARN] NPU inference failed (exit $ExitCode) -- retrying on CPU..."
    Write-Log "NPU failed; retrying on CPU."
    $EffectiveDevice = 'cpu'
    if (Test-Path $SavePath) { Remove-Item $SavePath -Recurse -Force }
    New-Item -ItemType Directory -Path $SavePath | Out-Null
    Push-Location $PpOcrDir
    $RelDetModelDir = Resolve-Path -Relative $DetModelDir
    $RelRecModelDir = Resolve-Path -Relative $RecModelDir
    $RelInputPath   = Resolve-Path -Relative $InputPath
    $RelSavePath    = Resolve-Path -Relative $SavePath
    & $PpOcrExe ocr `
        "--input=$RelInputPath" `
        "--text_detection_model_name=$DetModelName" `
        "--text_detection_model_dir=$RelDetModelDir" `
        "--text_recognition_model_name=$RecModelName" `
        "--text_recognition_model_dir=$RelRecModelDir" `
        "--device=cpu" `
        "--text_recognition_batch_size=$RecBatchSize" `
        "--text_rec_score_thresh=$RecScoreThresh" `
        "--save_path=$RelSavePath"
    $ExitCode = $LASTEXITCODE
    Pop-Location
    Write-Log "CPU retry exited: code=$ExitCode"
}

$elapsed = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)

if ($ExitCode -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] OCR failed (exit code $ExitCode) | ${elapsed}s | $($EffectiveDevice.ToUpper())"
    Write-Host "  Log: $LogFile"
    if (Test-Path $SavePath) { Remove-Item $SavePath -Recurse -Force }
    exit $ExitCode
}

# --- Print results ---
$TxtFiles = Get-ChildItem $SavePath -Filter '*.txt' -ErrorAction SilentlyContinue
$lineCount = 0
Write-Host ""
Write-Host "------------------------------------------------------------------------"
if ($TxtFiles.Count -eq 0) {
    Write-Host '[no text found]'
} else {
    foreach ($f in $TxtFiles) {
        if ($TxtFiles.Count -gt 1) { Write-Host "-- $($f.BaseName) --" }
        $lines = Get-Content $f.FullName -Encoding UTF8
        $lines | ForEach-Object { Write-Host $_; $lineCount++ }
    }
}
Write-Host "------------------------------------------------------------------------"
Write-Host ""
Write-Host "[OK] OCR complete | $($TxtFiles.Count) image(s) | $lineCount line(s) | ${elapsed}s | $($EffectiveDevice.ToUpper())"
Write-Host "  Log: $LogFile"

# --- Cleanup ---
if (Test-Path $SavePath) { Remove-Item $SavePath -Recurse -Force }
Write-Log "Done. elapsed=${elapsed}s lines=$lineCount"
exit 0
