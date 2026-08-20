# Background download script for local-ocr-npu skill
# Called by run.ps1 via Start-Process. Do NOT call directly.
#
# Download sources:
#   Binary  : ModelScope CDN only
#   Models  : ModelScope CDN --> HuggingFace fallback

param(
    [string]$SkillRoot,
    [string]$HfRepoUrl,
    [string]$MsRepoUrl,
    [string]$BinAssetName,
    [string]$DetModelDir,
    [string]$RecModelDir
)

$BinDir = Join-Path $SkillRoot 'bin'
$Log    = Join-Path $SkillRoot 'download.log'
$Lock   = Join-Path $SkillRoot '.downloading'

function L($msg) { Add-Content $Log "[$(Get-Date -Format 'HH:mm:ss')] $msg" }

# Trust all SSL certificates (workaround for HuggingFace SSL on some Windows)
try {
    Add-Type -TypeDefinition @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class DlTrustAll : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint sp, X509Certificate cert, WebRequest req, int err) { return true; }
}
"@
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object DlTrustAll
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
} catch { }

# Detect system proxy (handles corporate proxy e.g. Intel, MSFT internal networks)
$SystemProxy = $null
try {
    [System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
    $testUri = [System.Uri]'https://www.modelscope.cn'
    $proxyUri = [System.Net.WebRequest]::GetSystemWebProxy().GetProxy($testUri)
    if ($proxyUri -and $proxyUri.Host -ne 'www.modelscope.cn') {
        $SystemProxy = $proxyUri.AbsoluteUri
        L "System proxy detected: $SystemProxy"
    }
} catch { }

function Download-File {
    param([string[]]$Urls, [string]$OutFile)
    foreach ($url in $Urls) {
        # Build parameter sets: try with proxy first (if detected), then without
        $paramSets = @( @{ UseBasicParsing=$true; TimeoutSec=300; Uri=$url; OutFile=$OutFile } )
        if ($SystemProxy) {
            $paramSets = @(
                @{ UseBasicParsing=$true; TimeoutSec=300; Uri=$url; OutFile=$OutFile; Proxy=$SystemProxy; ProxyUseDefaultCredentials=$true },
                @{ UseBasicParsing=$true; TimeoutSec=300; Uri=$url; OutFile=$OutFile }
            )
        }
        foreach ($params in $paramSets) {
            try {
                $ProgressPreference = 'SilentlyContinue'
                Invoke-WebRequest @params
                return $true
            } catch { }
        }
    }
    return $false
}

try {
    "$(Get-Date -Format 'HH:mm:ss') Download started." | Set-Content $Log

    # -------------------------------------------------------------------------
    # 1. Download ppocr.exe + DLLs
    #    Try ModelScope CDN first (fast in CN), then GitHub
    # -------------------------------------------------------------------------
    $ovinoDll = Join-Path $BinDir 'openvino.dll'
    if (-not (Test-Path $ovinoDll)) {
        L 'Downloading ppocr.exe + DLLs...'
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
        $zip = Join-Path $env:TEMP 'ppocr-skill-dl.zip'

        $msBinUrl = "$MsRepoUrl/bin/$BinAssetName"
        L "  Downloading from ModelScope: $msBinUrl"
        $ok = Download-File -Urls @($msBinUrl) -OutFile $zip

        if ($ok) {
            Expand-Archive -Path $zip -DestinationPath $BinDir -Force
            Remove-Item $zip -Force -ErrorAction SilentlyContinue
            L 'ppocr.exe + DLLs: OK'
        } else {
            L 'ppocr.exe + DLLs: FAILED -- manual download required'
            L "  From ModelScope: https://modelscope.cn/models/FionaGu1019/PaddleOCR-OpenVINO"
        }
    } else {
        L 'ppocr.exe + DLLs: already present.'
    }

    # -------------------------------------------------------------------------
    # 2. Download models (parallel, ModelScope first)
    # -------------------------------------------------------------------------
    function Download-Model {
        param([string]$ModelName, [string]$DestDir)
        L "Downloading model: $ModelName"
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null

        $files = @('inference.xml', 'inference.bin', 'inference.yml')
        if ($ModelName -match '_det_') { $files += 'inference_960.xml' }
        if ($ModelName -match '_rec_') {
            $files += @('inference_320.xml','inference_480.xml','inference_640.xml',
                        'inference_800.xml','inference_1280.xml')
        }

        # Parallel download using jobs (one job per file)
        $jobs =         foreach ($fn in $files) {
            $destFile = Join-Path $DestDir $fn
            $urls = @("$MsRepoUrl/$ModelName/$fn", "$HfRepoUrl/$ModelName/$fn")
            Start-Job -ScriptBlock {
                param($u, $o)
                foreach ($url in $u) {
                    try {
                        $ProgressPreference = 'SilentlyContinue'
                        Invoke-WebRequest -Uri $url -OutFile $o -TimeoutSec 300 -UseBasicParsing
                        return "OK: $(Split-Path $o -Leaf)"
                    } catch { }
                }
                return "FAIL: $(Split-Path $o -Leaf)"
            } -ArgumentList $urls, $destFile
        }

        # Wait for all jobs and collect results
        $jobs | Wait-Job | ForEach-Object {
            $result = Receive-Job $_
            L "  $result"
            Remove-Job $_
        }
    }

    if (-not (Test-Path $DetModelDir)) { Download-Model (Split-Path $DetModelDir -Leaf) $DetModelDir }
    if (-not (Test-Path $RecModelDir)) { Download-Model (Split-Path $RecModelDir -Leaf) $RecModelDir }

    L 'ALL DONE -- skill ready. Re-run to start OCR.'

} catch {
    L "ERROR: $_"
} finally {
    Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
