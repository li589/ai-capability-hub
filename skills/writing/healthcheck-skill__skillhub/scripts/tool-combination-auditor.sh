# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# =============================================================================
# 工具组合审计脚本 v1.0
# 
# 功能：检测高风险工具组合，防止组合滥用导致的攻击面
# 来源：@xiaoshuai_fa6a29 的实战建议
#
# 危险组合检测：
#   1. 文件读取 + 网络请求 → 数据外传
#   2. 凭证读取 + API调用 → 权限提升
#   3. 进程查看 + 命令执行 → 逃逸攻击
#
# 使用方法：
#   ./tool-combination-auditor.sh              # 完整检查
#   ./tool-combination-auditor.sh --quick       # 快速检查
#   ./tool-combination-auditor.sh --report      # 生成报告
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports"
TOOL_COMBO_LOG="${REPORT_DIR}/tool-combination-audit-$(date +%Y%m%d).log"

# 创建报告目录
mkdir -p "$REPORT_DIR"

# =============================================================================
# 工具组合风险定义
# =============================================================================

declare -A DANGEROUS_COMBINATIONS=(
    ["file_read+network"]="数据外传风险"
    ["credential+api"]="权限提升风险"
    ["process+exec"]="逃逸攻击风险"
    ["file_write+sensitive"]="敏感数据写入风险"
    ["network+system"]="系统渗透风险"
)

# 高危工具关键词
declare -A TOOL_PATTERNS=(
    ["file_read"]="cat|read|grep|head|tail|less|more|view|open"
    ["file_write"]="write|append|edit|modify|create|save|tee"
    ["network_send"]="curl|wget|fetch|download|upload|post|send|http|https|socket"
    ["network_recv"]="listen|serve|accept|receive|get|fetch"
    ["credential"]="password|secret|token|key|auth|credential|env|variable"
    ["api_call"]="api|call|invoke|request|grpc|rest|webhook"
    ["process_info"]="ps|proc|process|list|status|top|pgrep"
    ["exec"]="exec|run|bash|sh|command|shell|system|popen"
    ["system_modify"]="chmod|chown|mount|iptables|ufw|service|systemctl"
)

# =============================================================================
# 辅助函数
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$TOOL_COMBO_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$TOOL_COMBO_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$TOOL_COMBO_LOG"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$TOOL_COMBO_LOG"
}

log_risk() {
    local risk_level=$1
    local message=$2
    case $risk_level in
        high)
            echo -e "${RED}[🔴 HIGH RISK]${NC} $message" | tee -a "$TOOL_COMBO_LOG"
            ;;
        medium)
            echo -e "${YELLOW}[🟡 MEDIUM RISK]${NC} $message" | tee -a "$TOOL_COMBO_LOG"
            ;;
        low)
            echo -e "${BLUE}[🔵 LOW RISK]${NC} $message" | tee -a "$TOOL_COMBO_LOG"
            ;;
    esac
}

# =============================================================================
# 检测函数
# =============================================================================

# 检测文件读取工具
detect_file_read_tools() {
    log_info "=== 检测文件读取相关工具 ==="
    
    local findings=()
    
    # 检查常见的文件读取工具使用记录
    if grep -rqE "(${TOOL_PATTERNS[file_read]})" "$SCRIPT_DIR" 2>/dev/null; then
        local count=$(grep -rE "(${TOOL_PATTERNS[file_read]})" "$SCRIPT_DIR" 2>/dev/null | wc -l)
        findings+=("在脚本中发现 $count 处文件读取操作")
    fi
    
    # 检查 OpenClaw 工具调用日志（如果有权限）
    if [ -r /tmp/openclaw/tools.log ] 2>/dev/null; then
        local tool_count=$(grep -cE "(${TOOL_PATTERNS[file_read]})" /tmp/openclaw/tools.log 2>/dev/null || echo "0")
        if [ "$tool_count" -gt 0 ]; then
            findings+=("工具调用日志中发现 $tool_count 次文件读取")
        fi
    fi
    
    if [ ${#findings[@]} -gt 0 ]; then
        log_warn "文件读取工具检测结果："
        for finding in "${findings[@]}"; do
            echo "  - $finding"
        done
        return 1
    else
        log_success "未检测到可疑的文件读取模式"
        return 0
    fi
}

# 检测网络请求工具
detect_network_tools() {
    log_info "=== 检测网络请求相关工具 ==="
    
    local findings=()
    
    # 检查网络请求模式
    if grep -rqE "(${TOOL_PATTERNS[network_send]})" "$SCRIPT_DIR" 2>/dev/null; then
        local count=$(grep -rE "(${TOOL_PATTERNS[network_send]})" "$SCRIPT_DIR" 2>/dev/null | wc -l)
        findings+=("在脚本中发现 $count 处网络请求操作")
    fi
    
    # 检查配置文件中的外部 URL
    if [ -f "$SCRIPT_DIR/../config/settings.json" ] 2>/dev/null; then
        local url_count=$(grep -cE "https?://" "$SCRIPT_DIR/../config/settings.json" 2>/dev/null || echo "0")
        if [ "$url_count" -gt 0 ]; then
            findings+=("配置文件中发现 $url_count 个外部 URL")
        fi
    fi
    
    if [ ${#findings[@]} -gt 0 ]; then
        log_warn "网络请求工具检测结果："
        for finding in "${findings[@]}"; do
            echo "  - $finding"
        done
        return 1
    else
        log_success "未检测到可疑的网络请求模式"
        return 0
    fi
}

# 检测凭证访问模式
detect_credential_access() {
    log_info "=== 检测凭证访问模式 ==="
    
    local findings=()
    
    # 检查凭证相关模式
    if grep -rqE "(${TOOL_PATTERNS[credential]})" "$SCRIPT_DIR" 2>/dev/null; then
        local count=$(grep -rE "(${TOOL_PATTERNS[credential]})" "$SCRIPT_DIR" 2>/dev/null | wc -l)
        findings+=("在脚本中发现 $count 处凭证访问操作")
    fi
    
    # 检查环境变量中的敏感信息
    local env_sensitive=$(env | grep -cE "(API|KEY|TOKEN|SECRET|PASSWORD|PRIVATE)" || echo "0")
    if [ "$env_sensitive" -gt 0 ]; then
        findings+=("环境变量中发现 $env_sensitive 个敏感变量")
    fi
    
    if [ ${#findings[@]} -gt 0 ]; then
        log_warn "凭证访问检测结果："
        for finding in "${findings[@]}"; do
            echo "  - $finding"
        done
        return 1
    else
        log_success "未检测到可疑的凭证访问模式"
        return 0
    fi
}

# =============================================================================
# 危险组合检测
# =============================================================================

check_dangerous_combinations() {
    log_info "=== 检测危险工具组合 ==="
    
    local risk_found=0
    
    # 组合1：文件读取 + 网络请求 → 数据外传
    log_info "检测组合1：文件读取 + 网络请求（数据外传风险）"
    local file_read_active=false
    local network_active=false
    
    if grep -rqE "(${TOOL_PATTERNS[file_read]})" "$SCRIPT_DIR" 2>/dev/null; then
        file_read_active=true
    fi
    
    if grep -rqE "(${TOOL_PATTERNS[network_send]})" "$SCRIPT_DIR" 2>/dev/null; then
        network_active=true
    fi
    
    if $file_read_active && $network_active; then
        log_risk "high" "🔴 发现数据外传风险：文件读取 + 网络请求组合"
        echo "  建议："
        echo "    1. 确认文件读取的目的和范围"
        echo "    2. 检查网络请求的目标地址"
        echo "    3. 考虑添加数据脱敏处理"
        echo "    4. 记录所有文件和网络操作"
        risk_found=$((risk_found + 1))
    else
        log_success "未发现数据外传风险组合"
    fi
    
    # 组合2：凭证读取 + API调用 → 权限提升
    log_info "检测组合2：凭证读取 + API调用（权限提升风险）"
    local cred_active=false
    local api_active=false
    
    if grep -rqE "(${TOOL_PATTERNS[credential]})" "$SCRIPT_DIR" 2>/dev/null; then
        cred_active=true
    fi
    
    if grep -rqE "(${TOOL_PATTERNS[api_call]})" "$SCRIPT_DIR" 2>/dev/null; then
        api_active=true
    fi
    
    if $cred_active && $api_active; then
        log_risk "high" "🔴 发现权限提升风险：凭证读取 + API调用组合"
        echo "  建议："
        echo "    1. 确认API调用的授权范围"
        echo "    2. 使用最小权限的凭证"
        echo "    3. 添加API调用审计日志"
        echo "    4. 考虑使用临时凭证"
        risk_found=$((risk_found + 1))
    else
        log_success "未发现权限提升风险组合"
    fi
    
    # 组合3：进程查看 + 命令执行 → 逃逸攻击
    log_info "检测组合3：进程查看 + 命令执行（逃逸攻击风险）"
    local proc_active=false
    local exec_active=false
    
    if grep -rqE "(${TOOL_PATTERNS[process_info]})" "$SCRIPT_DIR" 2>/dev/null; then
        proc_active=true
    fi
    
    if grep -rqE "(${TOOL_PATTERNS[exec]})" "$SCRIPT_DIR" 2>/dev/null; then
        exec_active=true
    fi
    
    if $proc_active && $exec_active; then
        log_risk "high" "🔴 发现逃逸攻击风险：进程查看 + 命令执行组合"
        echo "  建议："
        echo "    1. 确认命令执行的上下文"
        echo "    2. 使用受限的 shell 环境"
        echo "    3. 添加命令白名单"
        echo "    4. 监控异常的命令执行模式"
        risk_found=$((risk_found + 1))
    else
        log_success "未发现逃逸攻击风险组合"
    fi
    
    return $risk_found
}

# =============================================================================
# 生成报告
# =============================================================================

generate_report() {
    log_info "=== 生成工具组合审计报告 ==="
    
    local report_file="${REPORT_DIR}/tool-combination-report-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "report_type": "tool_combination_audit",
  "timestamp": "$(date -Iseconds)",
  "environment": {
    "hostname": "$(hostname)",
    "user": "$(whoami)",
    "script_dir": "$SCRIPT_DIR"
  },
  "findings": {
    "file_read_tools": $(detect_file_read_tools >/dev/null 2>&1; echo $?),
    "network_tools": $(detect_network_tools >/dev/null 2>&1; echo $?),
    "credential_access": $(detect_credential_access >/dev/null 2>&1; echo $?),
    "dangerous_combinations": $(check_dangerous_combinations >/dev/null 2>&1; echo $?)
  },
  "recommendations": [
    "定期检查工具调用日志",
    "使用最小权限原则",
    "添加工具调用审计",
    "实施网络访问控制"
  ],
  "log_file": "$TOOL_COMBO_LOG"
}
EOF
    
    log_success "报告已生成：$report_file"
    echo "$report_file"
}

# =============================================================================
# 主流程
# =============================================================================

main() {
    local mode="${1:-full}"
    
    echo "========================================================================"
    echo "         工具组合安全审计 - Tool Combination Security Audit"
    echo "========================================================================"
    echo "时间：$(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================================================"
    echo ""
    
    # 初始化日志
    echo "工具组合审计开始" > "$TOOL_COMBO_LOG"
    
    case $mode in
        --quick|-q)
            log_info "执行快速检查模式"
            detect_file_read_tools
            detect_network_tools
            detect_credential_access
            ;;
        --report|-r)
            log_info "生成完整审计报告"
            detect_file_read_tools
            detect_network_tools
            detect_credential_access
            check_dangerous_combinations
            generate_report
            ;;
        *)
            log_info "执行完整审计"
            detect_file_read_tools
            detect_network_tools
            detect_credential_access
            check_dangerous_combinations
            ;;
    esac
    
    echo ""
    echo "========================================================================"
    echo "                         审计完成"
    echo "========================================================================"
    echo "详细日志：$TOOL_COMBO_LOG"
    echo ""
}

# 执行主流程
main "$@"
