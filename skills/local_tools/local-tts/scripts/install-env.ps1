param(
    [string]$SkillRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'

$BinDir = Join-Path $SkillRoot 'bin'
$UvExe = Join-Path $BinDir 'uv.exe'
$EnvJson = Join-Path $SkillRoot 'info.json'
$MirrorIndex = 'https://pypi.tuna.tsinghua.edu.cn/simple'

if (-not (Test-Path $EnvJson)) {
    Write-Host "ERROR: info.json not found at `"$EnvJson`"."
    exit 1
}

$config = Get-Content $EnvJson -Raw | ConvertFrom-Json
$VenvName = $config.venv_name
$PythonVersion = if ($config.python_version) { $config.python_version } else { '3.11' }

$VenvDir = Join-Path $env:USERPROFILE ".openvino\venv\$VenvName"
$VenvPy = Join-Path $VenvDir 'Scripts\python.exe'

# --- Logging ---
$LogDir = Join-Path $env:USERPROFILE '.openvino\log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile = Join-Path $LogDir "install-env-$LogTimestamp.log"
Add-Content $LogFile "[$(Get-Date)] Log initialized for $SkillRoot."

function Write-Log($msg) { Add-Content $LogFile "[$(Get-Date)] $msg" }

function Get-WheelPackageInfo {
    param(
        [System.IO.FileInfo]$WheelFile
    )

    $wheelBaseName = [System.IO.Path]::GetFileNameWithoutExtension($WheelFile.Name)
    $wheelParts = $wheelBaseName -split '-'
    if ($wheelParts.Length -lt 2) {
        return $null
    }

    [PSCustomObject]@{
        PackageName = ($wheelParts[0] -replace '[-_.]+', '-').ToLowerInvariant()
        Version     = $wheelParts[1]
    }
}

function Invoke-PythonScript {
    param(
        [string]$PythonExe,
        [string]$Script,
        [string[]]$Arguments = @(),
        [switch]$SuppressStderr
    )

    $tempScript = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), ([System.IO.Path]::GetRandomFileName() + '.py'))
    try {
        Set-Content -Path $tempScript -Value $Script -Encoding ascii
        if ($SuppressStderr) {
            return & $PythonExe $tempScript @Arguments 2>$null
        }

        return & $PythonExe $tempScript @Arguments
    } finally {
        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
    }
}

function Get-InstalledPackageVersion {
    param(
        [string]$PythonExe,
        [string]$PackageName
    )

    $script = @'
import importlib.metadata
import re
import sys

def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()

target = normalize(sys.argv[1])
for distribution in importlib.metadata.distributions():
    name = distribution.metadata.get("Name")
    if name and normalize(name) == target:
        print(distribution.version)
        sys.exit(0)

sys.exit(1)
'@

    $installedVersion = Invoke-PythonScript -PythonExe $PythonExe -Script $script -Arguments @($PackageName) -SuppressStderr
    if ($LASTEXITCODE -ne 0 -or -not $installedVersion) {
        return $null
    }

    return ($installedVersion | Select-Object -First 1).Trim()
}

function Test-InstalledVersionOlderThanWheel {
    param(
        [string]$PythonExe,
        [string]$InstalledVersion,
        [string]$WheelVersion
    )

    $script = @'
import re
import sys

installed, wheel = sys.argv[1], sys.argv[2]

def split_version(value):
    parts = []
    for part in re.split(r"([0-9]+)", value.lower()):
        if not part:
            continue
        parts.append(int(part) if part.isdigit() else part)
    return parts

version_class = None
try:
    from packaging.version import Version
    version_class = Version
except Exception:
    try:
        from pip._vendor.packaging.version import Version
        version_class = Version
    except Exception:
        version_class = None

if version_class is not None:
    try:
        sys.exit(0 if version_class(installed) < version_class(wheel) else 1)
    except Exception:
        pass

sys.exit(0 if split_version(installed) < split_version(wheel) else 1)
'@

    Invoke-PythonScript -PythonExe $PythonExe -Script $script -Arguments @($InstalledVersion, $WheelVersion) | Out-Null
    return $LASTEXITCODE -eq 0
}

# --- Step 0: Ensure Microsoft Visual C++ runtime (vcruntime140 / msvcp140) ---
# PyTorch / NumPy(MKL) / OpenVINO native DLLs (e.g. torch's c10.dll) link
# against the MSVC runtime, which is a SYSTEM component that pip/uv cannot
# install (Microsoft's redistribution terms keep it out of Python wheels).
# On a fresh Windows box it is often missing, and `import torch` then fails
# with "WinError 1114: DLL initialization routine failed". We detect it and
# silently install Microsoft's official redistributable so the user does not
# have to. Best-effort: if detection says present, or the silent install needs
# privileges we don't have, we log/print guidance and continue rather than
# blocking environment setup.
function Test-VCRuntimePresent {
    # Authoritative: the VS2015-2022 x64 redist sets this registry value.
    try {
        $key = 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64'
        $v = Get-ItemProperty -Path $key -Name 'Installed' -ErrorAction Stop
        if ($v.Installed -eq 1) { return $true }
    } catch { }
    # Fallback: the runtime DLLs physically present in System32.
    $sys32 = Join-Path $env:WINDIR 'System32'
    if ((Test-Path (Join-Path $sys32 'vcruntime140.dll')) -and
        (Test-Path (Join-Path $sys32 'vcruntime140_1.dll')) -and
        (Test-Path (Join-Path $sys32 'msvcp140.dll'))) {
        return $true
    }
    return $false
}

Write-Host '[0/4] Checking Microsoft Visual C++ runtime...'
if (Test-VCRuntimePresent) {
    Write-Host '  VC++ runtime is present.'
    Write-Log 'VC++ runtime already present.'
} else {
    Write-Host '  VC++ runtime missing; downloading and installing silently...'
    Write-Log 'VC++ runtime missing; attempting silent install of vc_redist.x64.exe.'
    $vcUrl = 'https://aka.ms/vs/17/release/vc_redist.x64.exe'
    $vcExe = Join-Path $env:TEMP 'vc_redist.x64.exe'
    $downloaded = $false
    try {
        $curlExe = (Get-Command curl.exe -ErrorAction SilentlyContinue).Source
        if ($curlExe) {
            & $curlExe -fL --ssl-no-revoke -o $vcExe $vcUrl
            if ($LASTEXITCODE -eq 0 -and (Test-Path $vcExe)) { $downloaded = $true }
        }
        if (-not $downloaded) {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri $vcUrl -OutFile $vcExe
            if (Test-Path $vcExe) { $downloaded = $true }
        }
    } catch {
        Write-Log "VC++ download failed: $($_.Exception.Message)"
    }

    if ($downloaded) {
        # /install /quiet /norestart: unattended. Exit code 0 = success,
        # 1638/3010 = already-newer / reboot-required (both effectively OK).
        $proc = Start-Process -FilePath $vcExe `
            -ArgumentList '/install', '/quiet', '/norestart' `
            -Wait -PassThru -ErrorAction SilentlyContinue
        $code = if ($proc) { $proc.ExitCode } else { -1 }
        Write-Log "vc_redist.x64.exe exit code: $code"
        Remove-Item $vcExe -Force -ErrorAction SilentlyContinue
        if ($code -eq 0 -or $code -eq 3010 -or $code -eq 1638 -or (Test-VCRuntimePresent)) {
            Write-Host '  VC++ runtime installed.'
        } else {
            Write-Host '  WARN: Could not install VC++ runtime automatically (admin rights may be required).'
            Write-Host '        If startup fails with a torch DLL error (WinError 1114), install it manually:'
            Write-Host '        https://aka.ms/vs/17/release/vc_redist.x64.exe'
            Write-Log "VC++ silent install did not confirm (exit=$code)."
        }
    } else {
        Write-Host '  WARN: Could not download the VC++ runtime installer (check network).'
        Write-Host '        If startup fails with a torch DLL error (WinError 1114), install it manually:'
        Write-Host '        https://aka.ms/vs/17/release/vc_redist.x64.exe'
        Write-Log 'VC++ runtime installer download failed.'
    }
}

# --- Step 1: Ensure UV ---
Write-Host '[1/4] Checking UV installation...'
if (-not (Test-Path $UvExe)) {
    if (-not (Test-Path $BinDir)) {
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    }

    $pathUv = (Get-Command uv.exe -ErrorAction SilentlyContinue).Source
    if ($pathUv) {
        Write-Host "  Found uv.exe on PATH at `"$pathUv`". Copying to `"$UvExe`"..."
        Copy-Item $pathUv $UvExe -Force
    } else {
        Write-Host "  Downloading uv.exe..."
        Write-Log "Downloading uv.exe from https://gitcode.com/gcw_ggDjjkY3/kjfile/releases/download/download/uv.exe"

        $url = 'https://gitcode.com/gcw_ggDjjkY3/kjfile/releases/download/download/uv.exe'
        $curlExe = (Get-Command curl.exe -ErrorAction SilentlyContinue).Source
        if ($curlExe) {
            & $curlExe -fL --ssl-no-revoke -o $UvExe $url
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path $UvExe)) {
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $UvExe
            }
        } else {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $UvExe
        }
    }

    if (-not (Test-Path $UvExe)) {
        Write-Host 'ERROR: Failed to install uv.exe, please check your network connection and try again.'
        exit 1
    }
}
Write-Host "  UV is available: $UvExe"

# uv writes normal progress (e.g. "Using CPython 3.11.14", resolver output) to
# stderr. Under $ErrorActionPreference = 'Stop', a native command writing to
# stderr is promoted to a terminating NativeCommandError IF this script's output
# is captured through a `2>&1 |` pipeline by the caller (run.ps1's test harness,
# and hosts that capture run.ps1's combined output do exactly this). That aborts
# the venv/requirements install mid-way on first run, leaving a broken venv. The
# uv steps below all check $LASTEXITCODE explicitly, so they do not rely on Stop
# semantics — switch to 'Continue' for the uv section and restore it afterwards.
$PrevErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'

# --- Step 2: Create Python venv ---
Write-Host "[2/4] Ensuring Python venv at $VenvDir ..."
if (-not (Test-Path $VenvPy)) {
    Write-Host "  Creating Python $PythonVersion virtual environment..."
    # --seed installs pip/setuptools/wheel into the venv. Required because
    # setup_extra.py installs MeloTTS via `python -m pip install` (uv venv
    # creates a pip-less environment by default, which fails with
    # "No module named pip").
    # --clear replaces any pre-existing directory. Without it, a venv creation
    # that was interrupted mid-way (leaving a dir with only .gitignore /
    # CACHEDIR.TAG and no python.exe) makes every later run fail with
    # "A directory already exists" — uv refuses to overwrite by default. The
    # outer `if (-not (Test-Path $VenvPy))` guard means we only get here when
    # the venv is missing or incomplete, so clearing is always safe.
    & $UvExe venv --clear --seed --python $PythonVersion $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ERROR: Failed to create Python virtual environment.'
        exit 1
    }
}

# Self-heal: ensure pip is present in the venv even when we DID NOT just create
# it. The --seed flag above only runs on the create branch, so a venv built by
# an OLDER install-env.ps1 (before --seed was added) is reused as-is and stays
# pip-less. setup_extra.py then fails every `python -m pip install` with
# "No module named pip" and MeloTTS/TTS silently never installs. Probe pip on
# every run and seed it on demand so pre-existing pip-less venvs recover without
# a full rebuild. Cheap when pip is already there (one --version call).
& $VenvPy -m pip --version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '  pip missing from venv (older uv venv had no --seed); installing pip...'
    Write-Log 'pip missing from venv; seeding pip via uv pip install.'
    & $UvExe pip install --python $VenvPy pip --index-url $MirrorIndex
    if ($LASTEXITCODE -ne 0) {
        Write-Host '  Tsinghua mirror failed, retrying pip install from official PyPI...'
        & $UvExe pip install --python $VenvPy pip
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ERROR: Failed to install pip into the venv.'
        Write-Log 'ERROR: Failed to seed pip into the venv.'
        exit 1
    }
}
Write-Host "  Python venv is ready."

# --- Step 3: Install requirements.txt ---
Write-Host '[3/4] Installing requirements...'
$RequirementsFile = Join-Path $SkillRoot 'requirements.txt'
$WheelsDir = Join-Path $SkillRoot 'wheels'
Write-Log "Installing requirements from $RequirementsFile with wheels from $WheelsDir"

if (Test-Path $RequirementsFile) {
    $RequirementsShaFile = Join-Path $VenvDir 'requirements.sha'
    $RequirementsHash = (Get-FileHash -Path $RequirementsFile -Algorithm SHA256).Hash
    $ExistingRequirementsHash = if (Test-Path $RequirementsShaFile) { (Get-Content $RequirementsShaFile -Raw).Trim() } else { '' }

    if ($ExistingRequirementsHash -eq $RequirementsHash) {
        Write-Host '  requirements.txt unchanged. Skipping install.'
        Write-Log 'requirements.txt unchanged. Skipping install.'
    } else {
        $basePipArgs = @('pip', 'install', '--python', $VenvPy, '-r', $RequirementsFile)
        if (Test-Path $WheelsDir) {
            $basePipArgs += '--find-links'
            $basePipArgs += $WheelsDir
        }

        Write-Host "  Installing from requirements.txt (Tsinghua mirror)..."
        Write-Log "Installing from requirements.txt with args: $($basePipArgs -join ' ') --index-url $MirrorIndex"
        & $UvExe @basePipArgs --index-url $MirrorIndex
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  Tsinghua mirror failed, retrying from official PyPI...'
            Write-Log '  Tsinghua mirror failed, retrying from official PyPI...'
            & $UvExe @basePipArgs
            if ($LASTEXITCODE -ne 0) {
                Write-Host 'ERROR: Failed to install requirements.'
                Write-Log 'ERROR: Failed to install requirements.'
                exit 1
            }
        }

        Set-Content -Path $RequirementsShaFile -Value $RequirementsHash -Encoding ascii
    }
} else {
    Write-Host '  No requirements.txt found. Skipping.'
}
Write-Log "Finished installing requirements."

# --- Step 4: Install extra .whl files ---
Write-Host '[4/4] Installing extra wheel files...'
if (Test-Path $WheelsDir) {
    $whlFiles = Get-ChildItem (Join-Path $WheelsDir '*.whl') -ErrorAction SilentlyContinue
    if ($whlFiles) {
        foreach ($whl in $whlFiles) {
            $wheelInfo = Get-WheelPackageInfo -WheelFile $whl
            $shouldInstallWheel = $true

            if ($wheelInfo) {
                $installedVersion = Get-InstalledPackageVersion -PythonExe $VenvPy -PackageName $wheelInfo.PackageName
                if (-not $installedVersion) {
                    Write-Host "  $($wheelInfo.PackageName) is not installed. Installing $($whl.Name)..."
                } elseif (Test-InstalledVersionOlderThanWheel -PythonExe $VenvPy -InstalledVersion $installedVersion -WheelVersion $wheelInfo.Version) {
                    Write-Host "  $($wheelInfo.PackageName) $installedVersion is older than wheel $($wheelInfo.Version). Installing $($whl.Name)..."
                } else {
                    Write-Host "  $($wheelInfo.PackageName) $installedVersion is already newer than or equal to wheel $($wheelInfo.Version). Skipping."
                    $shouldInstallWheel = $false
                }
            } else {
                Write-Host "  Unable to parse package info from $($whl.Name). Installing."
            }

            if (-not $shouldInstallWheel) {
                continue
            }

            Write-Host "  Installing $($whl.Name) (Tsinghua mirror for deps)..."
            & $UvExe pip install --python $VenvPy $whl.FullName --index-url $MirrorIndex --find-links $WheelsDir
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Tsinghua mirror failed for $($whl.Name), retrying from official PyPI..."
                & $UvExe pip install --python $VenvPy $whl.FullName --find-links $WheelsDir
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "ERROR: Failed to install $($whl.Name)."
                    exit 1
                }
            }
        }
    } else {
        Write-Host '  No wheel files found. Skipping.'
    }
} else {
    Write-Host '  No wheels directory found. Skipping.'
}

# Restore the caller's error handling now that the uv (stderr-noisy) steps are done.
$ErrorActionPreference = $PrevErrorActionPreference

Write-Host ''
Write-Host 'Environment setup complete.'
exit 0
