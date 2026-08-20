# Windows 启动包装：对齐 UTF-8 代码页后再调用 cli.mjs，减轻 Trae / PowerShell 5.x 中文乱码。
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CliArgs
)

$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
try { chcp 65001 | Out-Null } catch {}

# 过滤 Agent 终端可能拼入的 JS 字面量 undefined / null（部分 Agent 工具 bug）
$FilteredArgs = @($CliArgs | Where-Object { $_ -ne 'undefined' -and $_ -ne 'null' })

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& node (Join-Path $scriptDir "cli.mjs") @FilteredArgs
exit $LASTEXITCODE

