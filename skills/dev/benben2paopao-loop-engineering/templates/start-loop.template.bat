@echo off
chcp 65001 >nul
REM ============================================================
REM  start-loop.bat  —  LOOP 一键启动器
REM  任务:{{TASK_TITLE}}
REM  生成时间:由 loop-engineering skill 自动生成
REM ============================================================

echo.
echo ==========================================================
echo   Loop Engineering — {{TASK_TITLE}}
echo ==========================================================
echo.
echo  [1] 检查 LOOP 文件...
echo.

set LOOP_DIR=%~dp0
echo  LOOP 目录: %LOOP_DIR%
echo  项目目录: {{PROJECT_PATH}}
echo.

if not exist "%LOOP_DIR%GOAL.md"   ( echo [缺失] GOAL.md   & goto :error )
if not exist "%LOOP_DIR%RULES.md"  ( echo [缺失] RULES.md  & goto :error )
if not exist "%LOOP_DIR%STATE.md"  ( echo [缺失] STATE.md  & goto :error )
if not exist "%LOOP_DIR%PROMPT.md" ( echo [缺失] PROMPT.md & goto :error )

echo  [OK] GOAL.md
echo  [OK] RULES.md
echo  [OK] STATE.md
echo  [OK] PROMPT.md
echo.
echo ==========================================================
echo   操作指引
echo ==========================================================
echo.
echo  1) 等下会用记事本打开 PROMPT.md
echo  2) 复制文件中两条 "===" 之间的全部内容
echo  3) 粘贴到 OpenCode 对话框,回车执行
echo  4) LOOP 会跑一轮,跑完会问你要不要继续
echo.
echo  PS: 想看 LOOP 现在做到哪了,直接打开 STATE.md
echo      想查看本任务规则,打开 RULES.md
echo      想修改任务目标,打开 GOAL.md
echo.
pause

REM 用记事本打开 PROMPT.md 方便复制
notepad "%LOOP_DIR%PROMPT.md"

goto :eof

:error
echo.
echo  LOOP 文件不完整,请检查 %LOOP_DIR% 目录
echo.
pause
