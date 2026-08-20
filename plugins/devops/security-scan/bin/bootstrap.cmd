@echo off
setlocal EnableExtensions DisableDelayedExpansion
REM Minimal Windows bootstrap: download one Qoder-style ZIP and install its executable.
REM Runtime dependency: built-in Windows PowerShell only.

if defined QODERSEC_HOME goto use_qodersec_home
if defined CODESEC_HOME goto use_codesec_home
set "CHOME=%USERPROFILE%\.qodersec"
goto home_ready
:use_qodersec_home
set "CHOME=%QODERSEC_HOME%"
goto home_ready
:use_codesec_home
set "CHOME=%CODESEC_HOME%"
:home_ready

if /I "%QODER_SITE%"=="CN" goto china_site
set "VERSION=%QODERSEC_CLI_VERSION_GLOBAL%"
if not defined VERSION set "VERSION=%CODESEC_CLI_VERSION_GLOBAL%"
set "BUCKET_URL=https://qoder-ide.oss-accelerate.aliyuncs.com/security/qodersec"
goto version_ready
:china_site
set "VERSION=%QODERSEC_CLI_VERSION_CN%"
if not defined VERSION set "VERSION=%CODESEC_CLI_VERSION_CN%"
set "BUCKET_URL=https://static.qoder.com.cn/security/qodersec"
:version_ready
if not defined VERSION echo [bootstrap] ERROR: qodersec CLI version is not set >&2
if not defined VERSION exit /b 1

set "NATIVE_ARCH=%PROCESSOR_ARCHITEW6432%"
if not defined NATIVE_ARCH set "NATIVE_ARCH=%PROCESSOR_ARCHITECTURE%"
if /I "%NATIVE_ARCH%"=="ARM64" set "ARCH=arm64"
if /I "%NATIVE_ARCH%"=="AMD64" set "ARCH=amd64"
if not defined ARCH echo [bootstrap] ERROR: unsupported Windows architecture %NATIVE_ARCH% >&2
if not defined ARCH exit /b 1

set "BIN_DIR=%CHOME%\bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%" >nul 2>nul
if not exist "%BIN_DIR%\." echo [bootstrap] ERROR: cannot create %BIN_DIR% >&2
if not exist "%BIN_DIR%\." exit /b 1

set "DOWNLOAD=%BIN_DIR%\qodersec.download.zip"
set "EXTRACT_DIR=%BIN_DIR%\qodersec.download"
set "EXTRACTED=%EXTRACT_DIR%\codesec-cli.exe"
set "QODERSEC_DOWNLOAD_URL=%BUCKET_URL%/%VERSION%/codesec-cli-windows-%ARCH%.zip"
set "QODERSEC_DOWNLOAD_OUT=%DOWNLOAD%"
set "QODERSEC_EXTRACT_DIR=%EXTRACT_DIR%"
del /q "%DOWNLOAD%" >nul 2>nul
rmdir /s /q "%EXTRACT_DIR%" >nul 2>nul

echo [bootstrap] Downloading %QODERSEC_DOWNLOAD_URL%
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL_EXE%" set "POWERSHELL_EXE=powershell.exe"
"%POWERSHELL_EXE%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing -Uri $env:QODERSEC_DOWNLOAD_URL -OutFile $env:QODERSEC_DOWNLOAD_OUT; Expand-Archive -LiteralPath $env:QODERSEC_DOWNLOAD_OUT -DestinationPath $env:QODERSEC_EXTRACT_DIR -Force; Unblock-File -LiteralPath (Join-Path $env:QODERSEC_EXTRACT_DIR 'codesec-cli.exe') -ErrorAction SilentlyContinue"
if errorlevel 1 goto download_failed
if not exist "%EXTRACTED%" goto download_failed

echo [bootstrap] Verifying %EXTRACTED%
"%EXTRACTED%" version
if errorlevel 1 goto verification_failed
move /y "%EXTRACTED%" "%BIN_DIR%\qodersec.exe" >nul 2>nul
if errorlevel 1 goto install_failed
set "CHANNEL=global"
if /I "%QODER_SITE%"=="CN" set "CHANNEL=cn"
set "VERSION_FILE=%BIN_DIR%\qodersec-version.json"
> "%VERSION_FILE%" echo {
>> "%VERSION_FILE%" echo   "version": "%VERSION%",
>> "%VERSION_FILE%" echo   "channel": "%CHANNEL%",
>> "%VERSION_FILE%" echo   "updated_at": "unknown"
>> "%VERSION_FILE%" echo }
if not exist "%VERSION_FILE%" goto metadata_failed
del /q "%DOWNLOAD%" >nul 2>nul
rmdir /s /q "%EXTRACT_DIR%" >nul 2>nul

echo [bootstrap] Done
exit /b 0

:download_failed
del /q "%DOWNLOAD%" >nul 2>nul
rmdir /s /q "%EXTRACT_DIR%" >nul 2>nul
echo [bootstrap] ERROR: download failed >&2
exit /b 1

:verification_failed
echo [bootstrap] ERROR: downloaded executable failed version check >&2
echo [bootstrap] Preserved executable for diagnostics: %EXTRACTED% >&2
exit /b 1

:install_failed
del /q "%DOWNLOAD%" >nul 2>nul
rmdir /s /q "%EXTRACT_DIR%" >nul 2>nul
echo [bootstrap] ERROR: cannot replace qodersec.exe; another process may be using it >&2
exit /b 1

:metadata_failed
echo [bootstrap] ERROR: cannot write %VERSION_FILE% >&2
exit /b 1
