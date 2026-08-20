<#
.SYNOPSIS
    七陌会话洞察 MCP Skill 配置脚本（Windows PowerShell 版）

.DESCRIPTION
    功能：
      1. 检查 mcporter 是否已安装，未安装则通过 npm 自动安装
      2. 检查七陌 MCP 服务配置状态（token 是否已写入）
      3. 将用户自填的 Token 写入 mcporter 本地配置
      4. 验证 MCP 连接是否正常

.USAGE
    供 AI Agent 调用：

    第一步：检查 mcporter 与服务状态（立即返回，不阻塞）
      powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_check_status
      输出：
        READY                       -> mcporter 已装 + token 已配，可直接执行用户任务
        NEED_TOKEN                  -> mcporter 已装但 token 未配，需执行 qimo_set_token
        ERROR:*                     -> 告知用户对应错误

    第二步：写入用户自填的 Token
      powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_set_token <七陌Token>
      输出：
        TOKEN_READY                 -> Token 写入成功
        ERROR:missing_token         -> 未提供 token 参数
        ERROR:save_token_failed     -> 写入配置失败

    第三步：验证连接（可选，配置后自动执行一次）
      powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_check
      输出：
        CONN_OK                     -> 连接正常，返回 catalog 列表
        ERROR:conn_failed           -> 连接失败
        ERROR:unauthorized          -> Token 无效或过期

    交互式配置向导：
      powershell -ExecutionPolicy Bypass -File setup.ps1 setup

    无参数显示用法：
      powershell -ExecutionPolicy Bypass -File setup.ps1
#>

param(
    [Parameter(Position = 0)]
    [string]$Command,

    [Parameter(Position = 1)]
    [string]$Token
)

# ── 全局配置 ──────────────────────────────────────────────────────────────────
if ($env:QIMO_MCP_URL) {
    $script:QmMcpUrl = $env:QIMO_MCP_URL
} else {
    $script:QmMcpUrl = "https://mcp-ykfdoris.7moor.com/mcp"
}
$script:QmServiceName = "qimo-conversation-insights"
$script:QmTransport = "http"
$script:QmMcporterVersion = "0.9.0"

# ── 确保 cli-connector-packages 下有 mcporter shim（一次性，跨会话生效）────────
# 原理：该目录在沙箱默认 PATH 里且可写；shim 持久存在后，每个新进程都能直接 mcporter call。
#       .cmd 必须用 ASCII 编码写入，UTF-16 会让 cmd.exe 解析乱码。
function Invoke-QmEnsureShim {
    $shimDir = "$env:USERPROFILE\.workbuddy\binaries\node\cli-connector-packages"
    $shim = "$shimDir\mcporter.cmd"
    if (Test-Path $shim) { return $true }
    New-Item -ItemType Directory -Force -Path $shimDir | Out-Null
    $content = @'
@echo off
setlocal enabledelayedexpansion
set "REAL="
if exist "%USERPROFILE%\.workbuddy\binaries\node\mcporter09\node_modules\.bin\mcporter.cmd" set "REAL=%USERPROFILE%\.workbuddy\binaries\node\mcporter09\node_modules\.bin\mcporter.cmd"
if not defined REAL (
  for /d %%d in ("%USERPROFILE%\.workbuddy\binaries\node\mcporter*") do (
    if exist "%%~d\node_modules\.bin\mcporter.cmd" set "REAL=%%~d\node_modules\.bin\mcporter.cmd"
  )
)
if not defined REAL (
  if exist "%USERPROFILE%\.workbuddy\binaries\node\workspace\node_modules\.bin\mcporter.cmd" set "REAL=%USERPROFILE%\.workbuddy\binaries\node\workspace\node_modules\.bin\mcporter.cmd"
)
if not defined REAL (
  echo ERROR:mcporter_not_found 1>&2
  exit /b 127
)
call "%REAL%" %*
'@
    Set-Content -Path $shim -Value $content -Encoding ASCII
    return (Test-Path $shim)
}

# ── 检查 mcporter 是否可用，不可用则自动修复（建 shim / 兜底 npm install）─────
function Invoke-QmCheckMcporter {
    # 1) 已在 PATH（shim 已存在或平台已注入）→ 直接用
    if (Get-Command mcporter -ErrorAction SilentlyContinue) { return $true }

    # 2) 不在 PATH → 确认隔离工作区有没有真实 mcporter
    $hasReal = $false
    $candidates = @(
        "$env:USERPROFILE\.workbuddy\binaries\node\mcporter09\node_modules\.bin\mcporter.cmd",
        "$env:USERPROFILE\.workbuddy\binaries\node\workspace\node_modules\.bin\mcporter.cmd"
    )
    foreach ($p in $candidates) { if (Test-Path $p) { $hasReal = $true; break } }

    # 3) 全新机器：隔离工作区没有 → npm install 兜底
    if (-not $hasReal) {
        Write-Output "⚠️  未找到 mcporter，正在安装..."
        $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
        if ($npmCmd) {
            & npm install -g "mcporter@$($script:QmMcporterVersion)" 2>&1 | Select-Object -Last 3
        } else {
            Write-Output "ERROR:no_npm - 未找到 npm，请先安装 Node.js (>=20.11.0) 后重试"
            return $false
        }
    }

    # 4) 创建 shim（一次性，之后跨会话跨调用都生效）
    if (Invoke-QmEnsureShim) {
        if (Get-Command mcporter -ErrorAction SilentlyContinue) {
            Write-Output "✅ mcporter shim 已就绪（跨会话持久）"
            return $true
        }
    }
    Write-Output "ERROR:mcporter_not_found"
    return $false
}

# ── 从 mcporter config get 读取当前 Authorization Token ──────────────────────
function Get-QmToken {
    try {
        $output = & mcporter config get $script:QmServiceName 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        # 从输出中提取 Authorization 头的 Bearer 值
        $line = $output | Where-Object { $_ -match '^\s*Authorization:' } | Select-Object -First 1
        if ($line) {
            $token = $line -replace '.*Bearer\s*', '' -replace '\s*', ''
            return $token
        }
        return $null
    } catch {
        return $null
    }
}

# ── 将 Token 写入 mcporter 配置 ───────────────────────────────────────────────
function Set-QmToken {
    param([string]$Token)

    if ([string]::IsNullOrEmpty($Token)) {
        return $false
    }

    Write-Output "🔧 配置 mcporter..."

    & mcporter config add $script:QmServiceName $script:QmMcpUrl `
        --transport $script:QmTransport `
        --header "Authorization=Bearer $Token" `
        --scope home

    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    Write-Output ""
    Write-Output "✅ 配置完成！"
    Write-Output ""

    Write-Output "🧪 验证配置..."
    $listOutput = & mcporter list 2>&1
    if ($listOutput | Select-String $script:QmServiceName) {
        Write-Output "✅ qimo-conversation-insights 配置验证成功！"
        Write-Output ""
        $listOutput | Select-String -Pattern $script:QmServiceName -Context 0,1
    } else {
        Write-Output "⚠️  qimo-conversation-insights 配置验证失败，请检查网络或 Token 是否有效"
    }

    Write-Output ""
    Write-Output "─────────────────────────────────────"
    Write-Output "🎉 设置完成！"
    Write-Output ""
    Write-Output "📖 配置详情："
    Write-Output "   URL:         $($script:QmMcpUrl)"
    Write-Output "   传输协议:    http (mcporter --transport http)"
    Write-Output "   服务名:      $($script:QmServiceName)"
    Write-Output ""
    Write-Output "📖 MCP Tools 调用示例："
    Write-Output ""
    Write-Output "   # 查询 catalog 列表"
    Write-Output "   chcp 65001 >nul && mcporter call `"$($script:QmMcpUrl)`" `"get_catalog_list`" --args `"{}`""
    Write-Output ""
    Write-Output "   # 执行只读 SQL"
    Write-Output "   chcp 65001 >nul && mcporter call `"$($script:QmMcpUrl)`" `"exec_query`" --args `"{\`"sql\`":\`"SELECT 1\`"}`""
    Write-Output ""
    return $true
}

# ── 检查七陌服务状态 ──────────────────────────────────────────────────────────
# 返回值：
#   0 = 服务正常可用（有 Token）
#   1 = 服务未注册（mcporter list 中找不到）
#   2 = Token 为空或未配置
function Test-QmService {
    $listOutput = & mcporter list 2>$null
    if (-not ($listOutput | Select-String $script:QmServiceName)) {
        return 1
    }

    $token = Get-QmToken
    if ([string]::IsNullOrEmpty($token)) {
        return 2
    }

    return 0
}

# ── 主入口函数 A：检查 mcporter 与服务状态 ────────────────────────────────────
function Invoke-QmCheckStatus {
    if (-not (Invoke-QmCheckMcporter)) {
        Write-Output "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    $status = Test-QmService

    switch ($status) {
        0 {
            Write-Output "READY"
            return 0
        }
        1 {
            Write-Output "NEED_TOKEN"
            return 0
        }
        2 {
            Write-Output "NEED_TOKEN"
            return 0
        }
    }
}

# ── 主入口函数 B：写入用户自填的 Token ───────────────────────────────────────
function Invoke-QmSetToken {
    param([string]$Token)

    if ([string]::IsNullOrEmpty($Token)) {
        Write-Output "ERROR:missing_token - 请提供 token 参数，用法：powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_set_token <七陌Token>"
        return 1
    }

    if (-not (Invoke-QmCheckMcporter)) {
        Write-Output "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    if (Set-QmToken -Token $Token) {
        Write-Output "TOKEN_READY"
        return 0
    } else {
        Write-Output "ERROR:save_token_failed - Token 写入配置失败"
        return 1
    }
}

# ── 主入口函数 C：验证 MCP 连接 ───────────────────────────────────────────────
function Invoke-QmCheck {
    if (-not (Invoke-QmCheckMcporter)) {
        Write-Output "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    Write-Output "🧪 验证七陌 MCP 连接..."
    chcp 65001 > $null 2>&1
    $response = & mcporter call $script:QmMcpUrl "get_catalog_list" --args "{}" 2>&1
    $rc = $LASTEXITCODE

    if ($rc -ne 0) {
        Write-Output "ERROR:conn_failed - 连接失败"
        Write-Output "   详情: $response"
        return 1
    }

    # 检查是否返回鉴权错误
    if ($response | Select-String -Pattern "401|unauthorized|invalid_token|token.*invalid" -CaseSensitive:$false) {
        Write-Output "ERROR:unauthorized - Token 无效或过期，请重新执行 qimo_set_token"
        return 1
    }

    # 检查是否返回 Doris 后端错误
    if ($response | Select-String -Pattern "not alive|backend.*does not exist" -CaseSensitive:$false) {
        Write-Output "ERROR:backend_unavailable - Doris 后端不可用，数据服务故障，请联系七陌管理员"
        return 1
    }

    Write-Output "✅ 连接正常！"
    Write-Output ""
    Write-Output "📋 Catalog 列表："
    Write-Output $response
    Write-Output ""
    Write-Output "CONN_OK"
    return 0
}

# ── 直接执行时的交互式安装流程 ───────────────────────────────────────────────
function Invoke-QmInteractiveSetup {
    Write-Output ""
    Write-Output "╔══════════════════════════════════════════════╗"
    Write-Output "║   七陌会话洞察 MCP Skill 配置向导            ║"
    Write-Output "╚══════════════════════════════════════════════╝"
    Write-Output ""

    # 检查 mcporter
    Write-Output "🔍 检查 mcporter..."
    if (-not (Invoke-QmCheckMcporter)) {
        Write-Output "❌ mcporter 安装失败，请先安装 Node.js (https://nodejs.org) 后重试"
        exit 1
    }
    Write-Output "✅ mcporter 已就绪"
    Write-Output ""

    # 检查服务状态
    Write-Output "🔍 检查七陌服务配置..."
    $status = Test-QmService

    switch ($status) {
        0 {
            Write-Output "✅ 七陌服务已配置且 Token 已写入！"
            Write-Output ""
            $confirm = Read-Host "🎉 无需重新配置。是否验证连接？(y/n)"
            if ($confirm -eq "y" -or $confirm -eq "Y") {
                Invoke-QmCheck
            }
            return
        }
        default {
            Write-Output "⚠️  Token 未配置，需要设置..."
        }
    }

    Write-Output ""
    Write-Output "🔐 需要配置七陌 Token"
    Write-Output ""
    $token = Read-Host "请输入您的七陌 Token（由七陌签发，绑定一个租户 account）"

    if ([string]::IsNullOrEmpty($token)) {
        Write-Output "❌ Token 不能为空"
        exit 1
    }

    Write-Output ""
    Write-Output "⏳ 正在写入配置..."
    $result = Invoke-QmSetToken -Token $token

    switch -Wildcard ($result) {
        "TOKEN_READY" {
            Write-Output ""
            Write-Output "🎉 Token 写入成功！正在验证连接..."
            Invoke-QmCheck
        }
        "ERROR:*" {
            Write-Output ""
            Write-Output "❌ 配置失败：$result"
            exit 1
        }
    }
}

# ── 脚本入口 ──────────────────────────────────────────────────────────────────
if ($Command) {
    switch ($Command) {
        "qimo_check_status" {
            Invoke-QmCheckStatus
        }
        "qimo_set_token" {
            Invoke-QmSetToken -Token $Token
        }
        "qimo_check" {
            Invoke-QmCheck
        }
        "setup" {
            Write-Output "🚀 七陌会话洞察 MCP Skill 人工配置向导"
            Write-Output ""
            Invoke-QmInteractiveSetup
        }
        default {
            Write-Output "ERROR:unknown_command - 未知命令: $Command"
            Write-Output "可用命令: qimo_check_status, qimo_set_token, qimo_check, setup"
            exit 1
        }
    }
} else {
    Write-Output "用法："
    Write-Output "  powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_check_status              # 检查 mcporter 与服务状态"
    Write-Output "  powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_set_token <七陌Token>      # 写入用户自填的 Token"
    Write-Output "  powershell -ExecutionPolicy Bypass -File setup.ps1 qimo_check                      # 验证 MCP 连接"
    Write-Output "  powershell -ExecutionPolicy Bypass -File setup.ps1 setup                           # 交互式配置向导"
}
