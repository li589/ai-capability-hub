:; exec "$(dirname "$0")/security-scan-settings.sh" "$@" #
@echo off
call "%~dp0qodersec-launch.cmd" review settings --platform=qoder --format=json
exit /b %ERRORLEVEL%
