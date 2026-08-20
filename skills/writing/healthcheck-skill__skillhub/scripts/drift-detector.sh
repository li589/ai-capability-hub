#!/bin/bash
# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"

# HealthCheck Drift Detector - 配置漂移检测
# 版本: v3.0.0
# 用途: 检测系统配置相对于基线的变化

set -e

BASELINE_DIR="${HOME}/.openclaw/baselines"
DRIFT_LOG="${HOME}/.openclaw/logs/drift-detection.log"
ALERT_THRESHOLD=5  # 超过5个变化则触发告警

# 初始化
init_drift_detector() {
    if [ ! -d "${HOME}/.openclaw/logs" ]; then
        mkdir -p "${HOME}/.openclaw/logs"
    fi
}

# 记录日志
log_drift() {
    local message="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$timestamp] $message" >> "$DRIFT_LOG"
}

# 检测当前系统与基线的差异
detect_drift() {
    local baseline_file="${1:-${BASELINE_DIR}/current.json}"
    
    if [ ! -f "$baseline_file" ]; then
        echo "❌ 未找到基线文件: $baseline_file"
        echo "请先创建基线: baseline-manager.sh create"
        return 1
    fi
    
    echo "🔍 检测配置漂移..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "基线: $(basename "$baseline_file")"
    echo "检测时间: $(date)"
    echo ""
    
    local drift_count=0
    local critical_changes=()
    local warning_changes=()
    local info_changes=()
    
    # 1. 检查文件权限变化
    echo "📁 检查文件权限..."
    local baseline_files=$(jq -r '.file_permissions | keys[]' "$baseline_file" 2>/dev/null)
    
    for file in $baseline_files; do
        if [ -e "$file" ]; then
            local current_perm=$(stat -c "%a" "$file" 2>/dev/null || echo "unknown")
            local baseline_perm=$(jq -r ".file_permissions[\"$file\"].perm" "$baseline_file")
            local baseline_owner=$(jq -r ".file_permissions[\"$file\"].owner" "$baseline_file")
            local current_owner=$(stat -c "%U" "$file" 2>/dev/null || echo "unknown")
            
            if [ "$current_perm" != "$baseline_perm" ]; then
                warning_changes+=("文件权限变化: $file ($baseline_perm → $current_perm)")
                drift_count=$((drift_count + 1))
                log_drift "WARNING: Permission change on $file: $baseline_perm → $current_perm"
            fi
            
            if [ "$current_owner" != "$baseline_owner" ]; then
                critical_changes+=("文件所有者变化: $file ($baseline_owner → $current_owner)")
                drift_count=$((drift_count + 1))
                log_drift "CRITICAL: Owner change on $file: $baseline_owner → $current_owner"
            fi
        else
            critical_changes+=("文件丢失: $file")
            drift_count=$((drift_count + 1))
            log_drift "CRITICAL: File missing: $file"
        fi
    done
    
    # 2. 检查网络配置变化
    echo "🌐 检查网络配置..."
    local baseline_listeners=$(jq -r '.network_config.listeners' "$baseline_file")
    local current_listeners=$(ss -tlnp 2>/dev/null | grep LISTEN | wc -l)
    local baseline_listener_count=$(echo "$baseline_listeners" | jq 'length')
    
    if [ "$current_listeners" -ne "$baseline_listener_count" ]; then
        warning_changes+=("监听端口数量变化: $baseline_listener_count → $current_listeners")
        drift_count=$((drift_count + 1))
        log_drift "WARNING: Listener count changed: $baseline_listener_count → $current_listeners"
    fi
    
    # 3. 检查新用户
    echo "👥 检查用户变化..."
    local baseline_users=$(jq -r '.users.system' "$baseline_file")
    local current_users=$(cat /etc/passwd | wc -l)
    
    if [ "$current_users" -gt "$baseline_users" ]; then
        local new_users=$((current_users - baseline_users))
        critical_changes+=("新增 $new_users 个系统用户")
        drift_count=$((drift_count + 1))
        log_drift "CRITICAL: New users detected: $new_users"
    fi
    
    # 4. 检查SSH配置变化
    echo "🔑 检查SSH配置..."
    if [ -f "/etc/ssh/sshd_config" ]; then
        local current_root_login=$(grep -E "^PermitRootLogin" /etc/ssh/sshd_config | awk '{print $2}' || echo "default")
        local baseline_root_login=$(jq -r '.ssh_config.root_login' "$baseline_file")
        
        if [ "$current_root_login" != "$baseline_root_login" ]; then
            critical_changes+=("SSH Root登录配置变化: $baseline_root_login → $current_root_login")
            drift_count=$((drift_count + 1))
            log_drift "CRITICAL: SSH PermitRootLogin changed: $baseline_root_login → $current_root_login"
        fi
    fi
    
    # 5. 检查服务状态变化
    echo "⚙️  检查服务状态..."
    local baseline_ssh=$(jq -r '.services.ssh' "$baseline_file")
    local current_ssh=$(systemctl is-active sshd 2>/dev/null || echo "unknown")
    
    if [ "$current_ssh" != "$baseline_ssh" ]; then
        warning_changes+=("SSH服务状态变化: $baseline_ssh → $current_ssh")
        drift_count=$((drift_count + 1))
        log_drift "WARNING: SSH service status changed: $baseline_ssh → $current_ssh"
    fi
    
    # 6. 检查防火墙状态
    echo "🧱 检查防火墙状态..."
    local baseline_firewall=$(jq -r '.services.firewall' "$baseline_file")
    local current_firewall=$(systemctl is-active ufw 2>/dev/null || systemctl is-active firewalld 2>/dev/null || echo "unknown")
    
    if [ "$current_firewall" != "$baseline_firewall" ] && [ "$current_firewall" = "inactive" ]; then
        critical_changes+=("防火墙服务已停止!")
        drift_count=$((drift_count + 1))
        log_drift "CRITICAL: Firewall service stopped"
    fi
    
    # 输出结果
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 漂移检测结果"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "总变化数: $drift_count"
    echo "🔴 Critical: ${#critical_changes[@]}"
    echo "🟠 Warning: ${#warning_changes[@]}"
    echo "🔵 Info: ${#info_changes[@]}"
    
    if [ $drift_count -gt 0 ]; then
        echo ""
        echo "【详细变化】"
        echo ""
        
        if [ ${#critical_changes[@]} -gt 0 ]; then
            echo "🔴 Critical级别变化:"
            for change in "${critical_changes[@]}"; do
                echo "  - $change"
            done
            echo ""
        fi
        
        if [ ${#warning_changes[@]} -gt 0 ]; then
            echo "🟠 Warning级别变化:"
            for change in "${warning_changes[@]}"; do
                echo "  - $change"
            done
            echo ""
        fi
        
        # 检查是否超过阈值
        if [ $drift_count -ge $ALERT_THRESHOLD ]; then
            echo "⚠️  变化数量超过阈值 ($ALERT_THRESHOLD)，建议立即审查!"
            echo ""
        fi
    else
        echo ""
        echo "✅ 未发现配置漂移，系统处于基线状态"
    fi
    
    # 返回JSON格式结果
    echo ""
    echo "【JSON输出】"
    cat << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "baseline": "$(basename "$baseline_file")",
  "drift_detected": $([ $drift_count -gt 0 ] && echo "true" || echo "false"),
  "drift_count": $drift_count,
  "threshold_exceeded": $([ $drift_count -ge $ALERT_THRESHOLD ] && echo "true" || echo "false"),
  "changes": {
    "critical": ${#critical_changes[@]},
    "warning": ${#warning_changes[@]},
    "info": ${#info_changes[@]}
  },
  "details": {
    "critical_changes": [$(printf '"%s",' "${critical_changes[@]}" | sed 's/,$//')],
    "warning_changes": [$(printf '"%s",' "${warning_changes[@]}" | sed 's/,$//')]
  }
}
EOF
    
    return $([ $drift_count -gt 0 ] && echo 1 || echo 0)
}

# 持续监控模式
monitor_mode() {
    local interval="${1:-300}"  # 默认5分钟
    local baseline_file="${2:-${BASELINE_DIR}/current.json}"
    
    echo "🔍 启动持续监控模式"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "检查间隔: ${interval}秒"
    echo "基线文件: $(basename "$baseline_file")"
    echo "按 Ctrl+C 停止监控"
    echo ""
    
    while true; do
        clear
        echo "HealthCheck Drift Monitor - $(date)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        if detect_drift "$baseline_file"; then
            echo ""
            echo "✅ 系统安全"
        else
            echo ""
            echo "⚠️  检测到配置漂移"
            
            # 可以在这里添加告警通知
            if command -v alert-manager.sh &> /dev/null; then
                alert-manager.sh send "配置漂移检测" "检测到系统配置相对于基线发生变化" "warning"
            fi
        fi
        
        echo ""
        echo "下次检查: $(date -d "@$(( $(date +%s) + interval ))" '+%H:%M:%S')"
        sleep "$interval"
    done
}

# 显示帮助
show_help() {
    cat << EOF
HealthCheck 漂移检测器 v3.0.0

用法: $0 [命令] [参数]

命令:
  check [baseline]        检测相对于基线的配置漂移
  monitor [interval]      持续监控模式（默认300秒）
  history                 查看漂移检测历史
  help                    显示此帮助

示例:
  # 检测一次
  $0 check
  
  # 使用特定基线检测
  $0 check production-baseline.json
  
  # 启动持续监控（每60秒检查一次）
  $0 monitor 60
  
  # 查看历史记录
  $0 history

环境变量:
  ALERT_THRESHOLD         告警阈值（默认5个变化）

日志文件: $DRIFT_LOG
EOF
}

# 查看历史
show_history() {
    if [ ! -f "$DRIFT_LOG" ]; then
        echo "❌ 没有找到漂移检测日志"
        return 1
    fi
    
    echo "📜 漂移检测历史（最近50条）"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -50 "$DRIFT_LOG"
}

# 主函数
main() {
    init_drift_detector
    
    case "${1:-check}" in
        check|detect)
            shift
            detect_drift "$@"
            ;;
        monitor|watch)
            shift
            monitor_mode "$@"
            ;;
        history|log)
            show_history
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "❌ 未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
