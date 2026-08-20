:; exec "$(dirname "$0")/qodersec-launch.sh" "$@" #
@echo off
setlocal EnableExtensions DisableDelayedExpansion
REM Windows launcher for the qodersec binary.
REM On Windows: cmd.exe runs this batch section, locates qodersec(.exe), execs it.
REM On Unix: the first line delegates immediately to qodersec-launch.sh.
REM Keep this file CRLF-terminated: cmd.exe corrupts LF-only polyglot parsing.
REM
REM Glue (unified under ~/.qodersec):
REM   - locate the binary in ~/.qodersec/bin/ (downloaded via bootstrap on first run)
REM   - resolve QODERSEC_HOME (default ~/.qodersec) — the ONE root for config + creds
REM     + logs + state; seed a default config.yaml there on first run from the
REM     plugin's bundled template so it persists across plugin upgrades
REM   - maps QODERSEC_HOME → CODESEC_HOME internally (Go binary reads CODESEC_HOME)
REM   - forward stdin + every argument unchanged
REM
REM Usage: qodersec-launch.cmd <qodersec args...>     (stdin is passed through)

set "_QODERSEC_LOG="

set "BIN_DIR=%~dp0"
set "PLUGIN_ROOT=%BIN_DIR%.."
REM Tell the Go binary to use qodersec-specific naming (log file, etc.)
set "CODESEC_LOG_NAME=qodersec"
REM Pinned dependency versions (updated when plugin is published)
REM Set both QODERSEC_* and CODESEC_* for Go binary compatibility
set "QODERSEC_CLI_VERSION_GLOBAL=0.8.0"
set "QODERSEC_CLI_VERSION_CN=0.8.0"
set "CODESEC_CLI_VERSION_GLOBAL=0.8.0"
set "CODESEC_CLI_VERSION_CN=0.8.0"
set "QODERCLI_VERSION_GLOBAL=1.0.45"
set "QODERCLI_VERSION_CN=1.0.45"

REM Resolve home without a parenthesized block so paths containing ! or ) remain intact.
if defined QODERSEC_HOME goto use_qodersec_home
if defined CODESEC_HOME goto use_codesec_home
set "CHOME=%USERPROFILE%\.qodersec"
goto home_resolved
:use_qodersec_home
set "CHOME=%QODERSEC_HOME%"
goto home_resolved
:use_codesec_home
set "CHOME=%CODESEC_HOME%"
:home_resolved
if not exist "%CHOME%" mkdir "%CHOME%" >nul 2>nul
if not exist "%CHOME%\." echo qodersec-launch: %CHOME% exists but is not a directory >&2
if not exist "%CHOME%\." exit /b 127
if not exist "%CHOME%\logs" mkdir "%CHOME%\logs" >nul 2>nul
set "_QODERSEC_LOG=%CHOME%\logs\qodersec.log"
if exist "%CHOME%\config.yaml" goto config_ready
if exist "%PLUGIN_ROOT%\config.yaml" copy /y "%PLUGIN_ROOT%\config.yaml" "%CHOME%\config.yaml" >nul 2>nul
if exist "%CHOME%\config.yaml" goto config_ready
if exist "%PLUGIN_ROOT%\config.yaml.example" copy /y "%PLUGIN_ROOT%\config.yaml.example" "%CHOME%\config.yaml" >nul 2>nul
:config_ready
REM Map to internal names the Go binary reads
set "QODERSEC_HOME=%CHOME%"
set "CODESEC_HOME=%CHOME%"

REM Add ~/.qodersec/bin to PATH for downloaded qodercli binaries.
set "PATH=%CHOME%\bin;%PATH%"

REM Inner qodercli must not re-enter any plugin hook path. The SDK-spawned
REM qodercli carries CODESEC_REVIEW_SUBPROCESS=1; short-circuit the launcher
REM itself before bootstrap/exec so SessionStart / review / any future hook all
REM no-op uniformly.
if not "%CODESEC_REVIEW_SUBPROCESS%"=="1" goto outer_process
if "%CODESEC_DEBUG%"=="1" >> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] skip inner subprocess
more >nul 2>nul
exit /b 0
:outer_process

if "%CODESEC_DEBUG%"=="1" >> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] exec

REM Bootstrap when missing OR when the installed qodersec version differs from
REM the version pinned by this plugin. ensure-deps only manages inner qodercli;
REM launcher owns qodersec self-updates.
set "TARGET_CLI_VERSION=%QODERSEC_CLI_VERSION_GLOBAL%"
if /I "%QODER_SITE%"=="CN" set "TARGET_CLI_VERSION=%QODERSEC_CLI_VERSION_CN%"
call :read_installed_version
if "%INSTALLED_CLI_VERSION%"=="%TARGET_CLI_VERSION%" goto run_qodersec

>> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] qodersec update current=%INSTALLED_CLI_VERSION% target=%TARGET_CLI_VERSION%
if not exist "%BIN_DIR%bootstrap.cmd" goto bootstrap_missing
>> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] bootstrap start
call "%BIN_DIR%bootstrap.cmd" >> "%_QODERSEC_LOG%" 2>&1
if errorlevel 1 goto bootstrap_failed
call :read_installed_version
if not "%INSTALLED_CLI_VERSION%"=="%TARGET_CLI_VERSION%" goto bootstrap_verification_failed
>> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] bootstrap done version=%INSTALLED_CLI_VERSION%
goto run_qodersec

:bootstrap_failed
>> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] bootstrap failed target=%TARGET_CLI_VERSION%
echo qodersec-launch: bootstrap failed for qodersec %TARGET_CLI_VERSION% >&2
exit /b 127

:bootstrap_verification_failed
>> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] bootstrap verification failed current=%INSTALLED_CLI_VERSION% target=%TARGET_CLI_VERSION%
echo qodersec-launch: expected qodersec %TARGET_CLI_VERSION%, got %INSTALLED_CLI_VERSION% >&2
exit /b 127

:bootstrap_missing
>> "%_QODERSEC_LOG%" echo [%DATE% %TIME%] [launcher] fatal: qodersec.exe not found and no bootstrap.cmd
echo qodersec-launch: qodersec.exe not found in %CHOME%\bin and no bootstrap.cmd >&2
exit /b 127

:run_qodersec
"%CHOME%\bin\qodersec.exe" %*
exit /b %ERRORLEVEL%

:read_installed_version
set "INSTALLED_CLI_VERSION="
if not exist "%CHOME%\bin\qodersec.exe" exit /b 0
set "VERSION_OUTPUT=%TEMP%\qodersec-version-%RANDOM%-%RANDOM%.tmp"
"%CHOME%\bin\qodersec.exe" version > "%VERSION_OUTPUT%" 2>nul
if errorlevel 1 goto read_installed_version_done
for /f "usebackq tokens=2" %%V in ("%VERSION_OUTPUT%") do set "INSTALLED_CLI_VERSION=%%V"
:read_installed_version_done
del /q "%VERSION_OUTPUT%" >nul 2>nul
exit /b 0
REM Unix execution was delegated by the first line; Windows always exits above.
