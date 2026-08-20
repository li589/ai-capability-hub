#!/bin/bash
#
# 七陌会话洞察 MCP Skill 配置脚本
#
# 功能：
#   1. 检查 mcporter 是否已安装，未安装则通过 npm 自动安装
#   2. 检查七陌 MCP 服务配置状态（token 是否已写入）
#   3. 将用户自填的 Token 写入 mcporter 本地配置
#   4. 验证 MCP 连接是否正常
#
# 用法（供 AI Agent 调用）：
#
#   第一步：检查 mcporter 与服务状态（立即返回，不阻塞）
#     bash ./setup.sh qimo_check_status
#     输出：
#       READY                       -> mcporter 已装 + token 已配，可直接执行用户任务
#       NEED_TOKEN                  -> mcporter 已装但 token 未配，需执行 qimo_set_token
#       NEED_MCPORTER               -> mcporter 未安装，脚本会自动尝试安装
#       ERROR:*                     -> 告知用户对应错误
#
#   第二步：写入用户自填的 Token
#     bash ./setup.sh qimo_set_token <七陌Token>
#     输出：
#       TOKEN_READY                 -> Token 写入成功，可直接执行用户任务
#       ERROR:missing_token         -> 未提供 token 参数
#       ERROR:save_token_failed     -> Token 写入配置失败
#
#   第三步：验证连接（可选，配置后自动执行一次）
#     bash ./setup.sh qimo_check
#     输出：
#       CONN_OK                     -> 连接正常，返回 catalog 列表
#       ERROR:conn_failed           -> 连接失败，检查 token 或网络
#       ERROR:unauthorized          -> Token 无效或过期
#
#   交互式配置向导（人工排查时使用）：
#     bash ./setup.sh setup
#
# 直接执行（无参数）显示用法：
#   bash ./setup.sh
#

# ── 全局配置 ──────────────────────────────────────────────────────────────────
_QM_MCP_URL="${QIMO_MCP_URL:-https://mcp-ykfdoris.7moor.com/mcp}"
_QM_SERVICE_NAME="qimo-conversation-insights"
_QM_TRANSPORT="http"
_QM_MCPORTER_VERSION="0.9.0"

# ── 确保 cli-connector-packages 下有 mcporter shim（一次性，跨会话生效）────────
# 原理：该目录在沙箱默认 PATH 里且可写；shim 持久存在后，每个新进程都能直接 mcporter call，
#       不再受"export PATH 仅当前进程有效"的限制。shim 动态查找隔离工作区真实 mcporter 转发。
_qm_ensure_shim() {
    local shim_dir="$HOME/.workbuddy/binaries/node/cli-connector-packages"
    local shim="$shim_dir/mcporter"
    [[ -x "$shim" ]] && return 0
    mkdir -p "$shim_dir" 2>/dev/null || return 1
    cat > "$shim" << 'SHIM_EOF'
#!/bin/sh
REAL=""
for d in \
  "$HOME/.workbuddy/binaries/node/mcporter09/node_modules/.bin" \
  "$HOME/.workbuddy/binaries/node/mcporter"*/node_modules/.bin \
  "$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin"; do
  if [ -x "$d/mcporter" ]; then REAL="$d/mcporter"; break; fi
done
if [ -z "$REAL" ]; then echo "ERROR:mcporter_not_found - 隔离工作区未找到 mcporter" >&2; exit 127; fi
exec "$REAL" "$@"
SHIM_EOF
    chmod +x "$shim" && return 0 || return 1
}

# ── 检查 mcporter 是否可用，不可用则自动修复（建 shim / 兜底 npm install）─────
_qm_check_mcporter() {
    # 1) 已在 PATH（shim 已存在或平台已注入）→ 直接用
    if command -v mcporter &>/dev/null; then return 0; fi

    # 2) 不在 PATH → 先确认隔离工作区有没有真实 mcporter
    local has_real=0
    for p in \
      "$HOME/.workbuddy/binaries/node/mcporter09/node_modules/.bin/mcporter" \
      "$HOME/.workbuddy/binaries/node/mcporter"*/node_modules/.bin/mcporter \
      "$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin/mcporter"; do
        [[ -x "$p" ]] && { has_real=1; break; }
    done

    # 3) 全新机器：隔离工作区没有 → npm install 兜底
    if [[ $has_real -eq 0 ]]; then
        echo "⚠️  未找到 mcporter，正在安装..."
        if command -v npm &>/dev/null; then
            npm install -g "mcporter@${_QM_MCPORTER_VERSION}" 2>&1 | tail -3
        else
            echo "ERROR:no_npm - 未找到 npm，请先安装 Node.js (>=20.11.0) 后重试"
            return 1
        fi
    fi

    # 4) 创建 shim（一次性，之后跨会话跨调用都生效，新会话 command -v 直接命中）
    if _qm_ensure_shim; then
        if command -v mcporter &>/dev/null; then
            echo "✅ mcporter shim 已就绪（跨会话持久）"
            return 0
        fi
    fi
    echo "ERROR:mcporter_not_found"
    return 1
}

# ── 从 mcporter config get 读取当前 Authorization Token ──────────────────────
# 输出：token 字符串（空则表示服务未注册或 Token 未配置）
_qm_get_token() {
    local output
    output=$(mcporter config get "$_QM_SERVICE_NAME" 2>/dev/null) || return 1

    # 从输出中提取 Authorization 头的 Bearer 值
    local token
    token=$(echo "$output" | grep -i '^\s*Authorization:' | sed 's/.*Bearer[[:space:]]*//' | tr -d '[:space:]')
    echo "$token"
}

# ── 将 Token 写入 mcporter 配置 ───────────────────────────────────────────────
# 用法：_qm_save_token <token>
_qm_save_token() {
    echo "🔧 配置 mcporter..."

    local token="$1"
    [[ -z "$token" ]] && return 1

    # 构建 mcporter config add 命令
    mcporter config add "$_QM_SERVICE_NAME" "$_QM_MCP_URL" \
        --transport "$_QM_TRANSPORT" \
        --header "Authorization=Bearer $token" \
        --scope home

    local rc=$?
    if [[ $rc -ne 0 ]]; then
        return 1
    fi

    echo ""
    echo "✅ 配置完成！"
    echo ""

    echo "🧪 验证配置..."
    if mcporter list 2>&1 | grep -q "$_QM_SERVICE_NAME"; then
        echo "✅ qimo-conversation-insights 配置验证成功！"
        echo ""
        mcporter list | grep -A 1 "$_QM_SERVICE_NAME" || true
    else
        echo "⚠️  qimo-conversation-insights 配置验证失败，请检查网络或 Token 是否有效"
    fi

    echo ""
    echo "─────────────────────────────────────"
    echo "🎉 设置完成！"
    echo ""
    echo "📖 配置详情："
    echo "   URL:         $_QM_MCP_URL"
    echo "   传输协议:    http (mcporter --transport http)"
    echo "   服务名:      $_QM_SERVICE_NAME"
    echo ""
    echo "📖 MCP Tools 调用示例："
    echo ""
    echo "   # 查询 catalog 列表"
    echo "   mcporter call \"$_QM_MCP_URL\" \"get_catalog_list\" --args '{}'"
    echo ""
    echo "   # 执行只读 SQL"
    echo "   mcporter call \"$_QM_MCP_URL\" \"exec_query\" --args '{\"sql\":\"SELECT 1\"}'"
    echo ""
    return 0
}

# ── 检查七陌服务状态 ──────────────────────────────────────────────────────────
# 返回值：
#   0 = 服务正常可用（有 Token）
#   1 = 服务未注册（mcporter list 中找不到）
#   2 = Token 为空或未配置
_qm_check_service() {
    if ! mcporter list 2>/dev/null | grep -q "$_QM_SERVICE_NAME"; then
        return 1
    fi

    local token
    token=$(_qm_get_token)
    local rc=$?

    if [[ $rc -ne 0 ]]; then
        return 1
    fi

    if [[ -z "$token" ]]; then
        return 2
    fi

    return 0
}

# ── 主入口函数 A：检查 mcporter 与服务状态（立即返回，不阻塞）────────────────
#
# AI Agent 第一步调用此函数：
#   READY           mcporter 已装 + token 已配，直接执行用户任务
#   NEED_TOKEN      mcporter 已装但 token 未配，需执行 qimo_set_token
#   NEED_MCPORTER   mcporter 未安装（脚本会自动尝试安装，安装成功后改返回 NEED_TOKEN）
#   ERROR:*         错误信息
#
qimo_check_status() {
    _qm_check_mcporter || {
        echo "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    _qm_check_service
    local status=$?

    case $status in
        0)
            echo "READY"
            return 0
            ;;
        1|2)
            echo "NEED_TOKEN"
            return 0
            ;;
    esac
}

# ── 主入口函数 B：写入用户自填的 Token ───────────────────────────────────────
#
# AI Agent 在拿到用户提供的七陌 Token 后调用此函数：
#   TOKEN_READY             Token 写入成功，可直接执行用户任务
#   ERROR:missing_token     未提供 token 参数
#   ERROR:save_token_failed 写入配置失败
#
# 用法：
#   bash ./setup.sh qimo_set_token <七陌Token>
#
qimo_set_token() {
    local token="$1"
    if [[ -z "$token" ]]; then
        echo "ERROR:missing_token - 请提供 token 参数，用法：bash ./setup.sh qimo_set_token <七陌Token>"
        return 1
    fi

    _qm_check_mcporter || {
        echo "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    if _qm_save_token "$token"; then
        echo "TOKEN_READY"
        return 0
    else
        echo "ERROR:save_token_failed - Token 写入配置失败"
        return 1
    fi
}

# ── 主入口函数 C：验证 MCP 连接 ───────────────────────────────────────────────
#
# 配置完成后验证连接是否正常，调用 get_catalog_list：
#   CONN_OK             连接正常，会附带 catalog 列表
#   ERROR:conn_failed   连接失败，检查网络或服务状态
#   ERROR:unauthorized  Token 无效或过期，需重新执行 qimo_set_token
#
qimo_check() {
    _qm_check_mcporter || {
        echo "ERROR:mcporter_not_found - 请先安装 Node.js 和 npm 后重试"
        return 1
    }

    echo "🧪 验证七陌 MCP 连接..."
    local response
    response=$(mcporter call "$_QM_MCP_URL" "get_catalog_list" --args '{}' 2>&1)
    local rc=$?

    if [[ $rc -ne 0 ]]; then
        echo "ERROR:conn_failed - 连接失败"
        echo "   详情: $response"
        return 1
    fi

    # 检查是否返回鉴权错误
    if echo "$response" | grep -qiE "401|unauthorized|invalid_token|token.*invalid"; then
        echo "ERROR:unauthorized - Token 无效或过期，请重新执行 qimo_set_token"
        return 1
    fi

    # 检查是否返回 Doris 后端错误
    if echo "$response" | grep -qiE "not alive|backend.*does not exist"; then
        echo "ERROR:backend_unavailable - Doris 后端不可用，数据服务故障，请联系七陌管理员"
        return 1
    fi

    echo "✅ 连接正常！"
    echo ""
    echo "📋 Catalog 列表："
    echo "$response"
    echo ""
    echo "CONN_OK"
    return 0
}

# ── 直接执行时的交互式安装流程 ───────────────────────────────────────────────
_qm_interactive_setup() {
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║   七陌会话洞察 MCP Skill 配置向导            ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""

    # 检查 mcporter
    echo "🔍 检查 mcporter..."
    if ! _qm_check_mcporter; then
        echo "❌ mcporter 安装失败，请先安装 Node.js (https://nodejs.org) 后重试"
        exit 1
    fi
    echo "✅ mcporter 已就绪"
    echo ""

    # 检查服务状态
    echo "🔍 检查七陌服务配置..."
    _qm_check_service
    local status=$?

    case $status in
        0)
            echo "✅ 七陌服务已配置且 Token 已写入！"
            echo ""
            echo "🎉 无需重新配置。是否验证连接？(y/n)"
            read -r confirm
            if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
                qimo_check
            fi
            return 0
            ;;
        1|2)
            echo "⚠️  Token 未配置，需要设置..."
            ;;
    esac

    echo ""
    echo "🔐 需要配置七陌 Token"
    echo ""
    echo "请输入您的七陌 Token（由七陌签发，绑定一个租户 account）："
    read -r token

    if [[ -z "$token" ]]; then
        echo "❌ Token 不能为空"
        exit 1
    fi

    echo ""
    echo "⏳ 正在写入配置..."
    local result
    result=$(qimo_set_token "$token")

    case "$result" in
        TOKEN_READY)
            echo ""
            echo "🎉 Token 写入成功！正在验证连接..."
            qimo_check
            ;;
        ERROR:*)
            echo ""
            echo "❌ 配置失败：$result"
            exit 1
            ;;
    esac

    return 0
}

# ── 脚本入口 ──────────────────────────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ -n "$1" ]]; then
        case "$1" in
            qimo_check_status)
                qimo_check_status
                exit $?
                ;;
            qimo_set_token)
                qimo_set_token "$2"
                exit $?
                ;;
            qimo_check)
                qimo_check
                exit $?
                ;;
            setup)
                echo "🚀 七陌会话洞察 MCP Skill 人工配置向导"
                echo ""
                _qm_interactive_setup
                ;;
            *)
                echo "ERROR:unknown_command - 未知命令: $1"
                echo "可用命令: qimo_check_status, qimo_set_token, qimo_check, setup"
                exit 1
                ;;
        esac
    else
        echo "用法："
        echo "  bash ./setup.sh qimo_check_status              # 检查 mcporter 与服务状态"
        echo "  bash ./setup.sh qimo_set_token <七陌Token>      # 写入用户自填的 Token"
        echo "  bash ./setup.sh qimo_check                      # 验证 MCP 连接"
        echo "  bash ./setup.sh setup                           # 交互式配置向导"
    fi
fi
