# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# Logging Functions - 日志记录函数库
# 版本: 4.0.0
# 用途: 提供统一的日志记录接口

LOG_DIR="${HOME}/.openclawhealthcheck/logs"
LOG_FILE="${LOG_DIR}/healthcheck.log"
AUDIT_LOG="${LOG_DIR}/audit.log"

# 初始化日志目录
init_logging() {
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        chmod 700 "$LOG_DIR"
    fi

    # 创建日志文件
    if [ ! -f "$LOG_FILE" ]; then
        touch "$LOG_FILE"
        chmod 600 "$LOG_FILE"
    fi

    if [ ! -f "$AUDIT_LOG" ]; then
        touch "$AUDIT_LOG"
        chmod 600 "$AUDIT_LOG"
    fi
}

# 记录日志
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # 输出到控制台
    case "$level" in
        "ERROR")
            echo "❌ [$timestamp] $message" >&2
            ;;
        "WARNING")
            echo "⚠️  [$timestamp] $message" >&2
            ;;
        "INFO")
            echo "ℹ️  [$timestamp] $message" >&2
            ;;
        "SUCCESS")
            echo "✅ [$timestamp] $message" >&2
            ;;
        *)
            echo "📝 [$timestamp] $message" >&2
            ;;
    esac

    # 写入日志文件
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# 记录审计日志
audit_log() {
    local action="$1"
    local user="${2:-$(whoami)}"
    local details="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # 写入审计日志
    echo "[$timestamp] $user | $action | $details" >> "$AUDIT_LOG"

    # 同时记录到主日志
    log "AUDIT" "用户 $user 执行操作: $action"
}

# 记录安全事件
security_log() {
    local event_type="$1"
    local severity="$2"
    local details="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # 写入审计日志（安全事件）
    echo "[$timestamp] [SECURITY] [$severity] $event_type | $details" >> "$AUDIT_LOG"

    # 同时记录到主日志
    log "SECURITY" "安全事件: $event_type (严重程度: $severity)"
}

# 获取最近的日志
get_recent_logs() {
    local lines="${1:-20}"

    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 获取最近的审计日志
get_recent_audit() {
    local lines="${1:-20}"

    if [ -f "$AUDIT_LOG" ]; then
        tail -n "$lines" "$AUDIT_LOG"
    else
        echo "审计日志不存在: $AUDIT_LOG"
    fi
}

# 清理旧日志（保留最近30天）
cleanup_old_logs() {
    local days="${1:-30}"

    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "*.log" -type f -mtime +$days -delete
        log "INFO" "已清理 $days 天前的旧日志文件"
    fi
}

# 导出函数
export -f init_logging
export -f log
export -f audit_log
export -f security_log
export -f get_recent_logs
export -f get_recent_audit
export -f cleanup_old_logs
