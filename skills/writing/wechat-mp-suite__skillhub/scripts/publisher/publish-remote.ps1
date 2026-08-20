<#
.SYNOPSIS
    远程发布 Markdown 文章到微信公众号草稿箱（Windows PowerShell 版）
.DESCRIPTION
    读取 .env 或 wechat.env 获取微信公众号凭证，通过 curl.exe 发送文章到远程 MCP 服务发布。
    等效于 publish-remote.sh 的 Windows 版本。
.PARAMETER FilePath
    Markdown 文章路径（必填）
.PARAMETER Theme
    主题名称（可选，默认: default）
.EXAMPLE
    .\publish-remote.ps1 article.md
    .\publish-remote.ps1 article.md lapis
#>

param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$FilePath = '',

    [Parameter(Mandatory = $false, Position = 1)]
    [string]$Theme = 'default'
)

$ErrorActionPreference = 'Stop'

# ─── 颜色输出 ───────────────────────────────────────────────────
$HasColor = $Host.UI.RawUI.ForegroundColor -ne $null
function Write-Color($Text, $Color = 'White') {
    if ($HasColor) {
        Write-Host $Text -ForegroundColor $Color
    } else {
        Write-Host $Text
    }
}

# ─── 查找配置文件 ───────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir/../.."
$ConfigFiles = @(
    "$ProjectRoot/wechat.env",
    "$ProjectRoot/.env",
    "$ScriptDir/../wechat.env",
    "$ScriptDir/../.env",
    "$ScriptDir/wechat.env",
    "$ScriptDir/.env"
)

# ─── 解析 .env 文件 ─────────────────────────────────────────────
function Load-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }

    $vars = @{}
    Get-Content $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        # 跳过注释和空行
        if ($line -eq '' -or $line -match '^\s*#') { return }
        # 支持 export KEY=VALUE 和 KEY=VALUE 两种格式
        if ($line -match '^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $key = $matches[1]
            $val = $matches[2].Trim()
            # 去除引号
            if ($val -match '^"(.+)"$') { $val = $matches[1] }
            elseif ($val -match "^'(.+)'$") { $val = $matches[1] }
            $vars[$key] = $val
        }
    }
    return $vars
}

# ─── 加载凭证（优先级: .env > 环境变量 > TOOLS.md）─────────────
function Get-Credentials {
    # 1. 尝试从 .env / wechat.env 读取
    $loadedFrom = ''
    foreach ($cfg in $ConfigFiles) {
        $envVars = Load-EnvFile -Path $cfg
        if ($envVars -and $envVars['WECHAT_APP_ID'] -and $envVars['WECHAT_APP_SECRET']) {
            $script:WECHAT_APP_ID = $envVars['WECHAT_APP_ID']
            $script:WECHAT_APP_SECRET = $envVars['WECHAT_APP_SECRET']
            $loadedFrom = $cfg
            break
        }
    }

    # 2. 回退到环境变量
    if (-not $script:WECHAT_APP_ID) { $script:WECHAT_APP_ID = [Environment]::GetEnvironmentVariable('WECHAT_APP_ID') }
    if (-not $script:WECHAT_APP_SECRET) { $script:WECHAT_APP_SECRET = [Environment]::GetEnvironmentVariable('WECHAT_APP_SECRET') }
    if ($script:WECHAT_APP_ID -and $script:WECHAT_APP_SECRET -and -not $loadedFrom) {
        $loadedFrom = '环境变量'
    }

    # 3. 回退到 TOOLS.md
    if (-not $script:WECHAT_APP_ID -or -not $script:WECHAT_APP_SECRET) {
        $toolsPaths = @(
            "$env:USERPROFILE/.openclaw/workspace-xina-gongzhonghao/TOOLS.md",
            "$env:USERPROFILE/.openclaw/workspace/TOOLS.md"
        )
        foreach ($tp in $toolsPaths) {
            if (Test-Path $tp) {
                $content = Get-Content $tp -Encoding UTF8 -Raw
                if ($content -match 'export\s+WECHAT_APP_ID=(\S+)') { $script:WECHAT_APP_ID = $matches[1] }
                if ($content -match 'export\s+WECHAT_APP_SECRET=(\S+)') { $script:WECHAT_APP_SECRET = $matches[1] }
                if ($script:WECHAT_APP_ID -and $script:WECHAT_APP_SECRET) {
                    $loadedFrom = $tp
                    break
                }
            }
        }
    }

    if (-not $script:WECHAT_APP_ID -or -not $script:WECHAT_APP_SECRET) {
        Write-Color '❌ 错误: 未找到 WECHAT_APP_ID / WECHAT_APP_SECRET' Red
        Write-Host ''
        Write-Host '请通过以下任一方式配置凭证：'
        Write-Host '  1. 在项目根目录创建 .env 或 wechat.env 文件：'
        Write-Host '     WECHAT_APP_ID=your_app_id'
        Write-Host '     WECHAT_APP_SECRET=your_app_secret'
        Write-Host '  2. 设置环境变量：'
        Write-Host '     $env:WECHAT_APP_ID = "your_app_id"'
        Write-Host '     $env:WECHAT_APP_SECRET = "your_app_secret"'
        Write-Host '  3. 配置 TOOLS.md（~/.openclaw/workspace/TOOLS.md）'
        exit 1
    }

    if ($loadedFrom) {
        Write-Color "📖 凭证从 $loadedFrom 读取" Yellow
    }
}

# ─── MCP 服务配置 ───────────────────────────────────────────────
$MCP_SERVER_URL = [Environment]::GetEnvironmentVariable('MCP_SERVER_URL')
if (-not $MCP_SERVER_URL) {
    # 尝试从 .env 或 wechat.env 读取 MCP_SERVER_URL
    foreach ($cfg in $ConfigFiles) {
        $envVars = Load-EnvFile -Path $cfg
        if ($envVars -and $envVars['MCP_SERVER_URL']) {
            $MCP_SERVER_URL = $envVars['MCP_SERVER_URL']
            break
        }
    }
}
if (-not $MCP_SERVER_URL) {
    $MCP_SERVER_URL = 'http://localhost:3000/api/mcp'
}

Write-Color "🌐 MCP 服务: $MCP_SERVER_URL" Cyan

# ─── 检查 curl.exe ──────────────────────────────────────────────
$CurlPath = Get-Command 'curl.exe' -ErrorAction SilentlyContinue
if (-not $CurlPath) {
    Write-Color '❌ 错误: 未找到 curl.exe。Windows 10/11 自带 curl，请确保其在 PATH 中。' Red
    exit 1
}

# ─── 参数校验 ───────────────────────────────────────────────────
if (-not $FilePath -or $FilePath -eq '') {
    Write-Color "用法: .\publish-remote.ps1 <path/to/article.md> [theme_id]" Yellow
    Write-Host   "示例: .\publish-remote.ps1 ./my-post.md lapis"
    Write-Host   ""
    Write-Host   "可用主题（theme_id）: default, lapis, phycat, ..."
    exit 1
}

if (-not (Test-Path $FilePath)) {
    Write-Color "❌ 错误: 文件不存在: $FilePath" Red
    exit 1
}

# ─── 加载凭证 ───────────────────────────────────────────────────
Get-Credentials

# ─── 上传文件到 MCP ────────────────────────────────────────────
Write-Color '🚀 上传文章到 MCP 服务...' Green
$FileName = Split-Path $FilePath -Leaf
$Content = Get-Content $FilePath -Encoding UTF8 -Raw

# JSON-encode 内容（PowerShell 方式）
$BodyObj = @{
    content  = $Content
    filename = $FileName
} | ConvertTo-Json -Compress

Write-Host "   文件: $FileName"
Write-Host "   大小: $($Content.Length) 字符"

try {
    $UploadResult = & $CurlPath.Source -s -X POST `
        "$MCP_SERVER_URL/upload_file" `
        -H 'Content-Type: application/json' `
        -d $BodyObj `
        --connect-timeout 30 `
        --max-time 120 2>&1
} catch {
    Write-Color "❌ 上传请求失败: $_" Red
    exit 1
}

# 解析响应
try {
    $UploadJson = $UploadResult | ConvertFrom-Json
} catch {
    Write-Color "❌ 无法解析上传响应: $UploadResult" Red
    exit 1
}

$FileId = $UploadJson.file_id
$ErrorMsg = $UploadJson.error

if ($ErrorMsg) {
    Write-Color "❌ 上传失败: $ErrorMsg" Red
    exit 1
}

if (-not $FileId -or $FileId -eq 'null') {
    Write-Color "❌ 上传失败: 无法从响应中解析 file_id" Red
    Write-Host "响应: $UploadResult"
    exit 1
}

Write-Color "✅ 文件上传成功！ID: $FileId" Green

# ─── 发布到微信公众号 ───────────────────────────────────────────
Write-Color '⏳ 正在发布到微信公众号草稿箱...' Green

$PublishBody = @{
    file_id          = $FileId
    theme_id         = $Theme
    wechat_app_id    = $script:WECHAT_APP_ID
    wechat_app_secret = $script:WECHAT_APP_SECRET
} | ConvertTo-Json -Compress

try {
    $PublishResult = & $CurlPath.Source -s -X POST `
        "$MCP_SERVER_URL/publish_article" `
        -H 'Content-Type: application/json' `
        -d $PublishBody `
        --connect-timeout 30 `
        --max-time 180 2>&1
} catch {
    Write-Color "❌ 发布请求失败: $_" Red
    exit 1
}

# 解析发布结果
try {
    $PublishJson = $PublishResult | ConvertFrom-Json
} catch {
    Write-Color "❌ 无法解析发布响应: $PublishResult" Red
    exit 1
}

$MediaId = $PublishJson.media_id
$PublishError = $PublishJson.error

if ($PublishError) {
    Write-Color "❌ 发布失败: $PublishError" Red
    Write-Host '💡 提示: 检查远程服务器 IP 是否已在微信公众号后台添加白名单'
    exit 1
}

if (-not $MediaId -or $MediaId -eq 'null') {
    Write-Color "❌ 发布失败: 未知响应" Red
    Write-Host "响应: $PublishResult"
    exit 1
}

Write-Color "🎉 发布成功！Media ID: $MediaId" Green
Write-Color '📱 请前往微信公众号后台草稿箱查看：' Yellow
Write-Host '   https://mp.weixin.qq.com/'
Write-Host ''
Write-Color '💡 常见问题：' Yellow
Write-Host '  1. IP 未在白名单 → 添加到公众号后台'
Write-Host '  2. Frontmatter 缺失 → 文件顶部添加 title + cover'
Write-Host '  3. API 凭证错误 → 检查 .env / wechat.env 中的凭证'
Write-Host '  4. 封面尺寸错误 → 需要 1080×864 像素'
