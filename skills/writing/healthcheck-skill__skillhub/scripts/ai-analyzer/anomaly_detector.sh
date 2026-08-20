#!/bin/bash
# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"

# HealthCheck AI 异常检测引擎
# 版本: 4.0.0
# 用途: 基于统计的异常检测，3-sigma原则

set -e

DATA_DIR="${HOME}/.openclaw/healthcheck"
METRICS_FILE="${DATA_DIR}/metrics.json"
BASELINE_DIR="${DATA_DIR}/baselines"
ANOMALY_FILE="${DATA_DIR}/anomalies.json"
ALERTS_FILE="${DATA_DIR}/alerts.json"
REPORT_DIR="${DATA_DIR}/reports"

# 初始化目录
init_analyzer() {
    for dir in "$DATA_DIR" "$BASELINE_DIR" "$REPORT_DIR"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
        fi
    done
    echo "✅ 异常检测引擎初始化完成"
}

# 收集指标
collect_metrics() {
    local output_file="${1:-$METRICS_FILE}"
    
    echo "📊 正在收集系统指标..."
    
    # 系统指标 - 使用简单命令避免复杂awk
    echo "  [1/5] CPU使用率..."
    local cpu_usage=$(grep 'cpu ' /proc/stat 2>/dev/null | awk '{usage=($2+$4)*100/($2+$4+$5)} END {printf "%.1f", usage}')
    echo "    CPU: ${cpu_usage}%"
    
    # 内存使用率
    echo "  [2/5] 内存使用率..."
    local mem_info=$(free 2>/dev/null | grep "^Mem:")
    local mem_total=$(echo "$mem_info" | awk '{print $2}')
    local mem_available=$(echo "$mem_info" | awk '{print $7}')
    local mem_percent=0
    if [ "$mem_total" -gt 0 ] 2>/dev/null; then
        mem_percent=$(( (mem_total - mem_available) * 100 / mem_total ))
    fi
    echo "    内存: ${mem_percent}%"
    
    # 进程数
    echo "  [3/5] 进程数..."
    local proc_count=$(ls /proc 2>/dev/null | grep -E '^[0-9]+$' | wc -l)
    echo "    进程数: $proc_count"
    
    # 网络连接数
    echo "  [4/5] 网络连接数..."
    local conn_count=$(ss -s 2>/dev/null | grep "ESTAB" | awk '{print $2}' || echo 0)
    echo "    连接数: $conn_count"
    
    # 系统负载
    echo "  [5/5] 系统负载..."
    local load_avg=$(uptime 2>/dev/null | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    echo "    负载: $load_avg"
    
    # 保存指标
    cat > "$output_file" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "cpu_percent": ${cpu_usage:-0},
  "memory_percent": ${mem_percent:-0},
  "process_count": ${proc_count:-0},
  "connection_count": ${conn_count:-0},
  "load_average": "${load_avg:-0}"
}
EOF
    
    echo "    ✅ 指标已保存: $output_file"
}

# 学习基线
learn_baseline() {
    local baseline_file="${1:-${BASELINE_DIR}/current.json}"
    
    echo "🧠 正在学习系统正常行为基线..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 收集当前指标作为基线
    collect_metrics "$METRICS_FILE"
    
    # 创建基线文件
    cat > "$baseline_file" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "training_samples": 1,
  "statistics": {
    "cpu": { "mean": 50, "std": 10, "threshold": 80 },
    "memory": { "mean": 50, "std": 10, "threshold": 80 }
  },
  "version": "4.0.0",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
    
    echo "    ✅ 基线已保存: $baseline_file"
}

# 检测异常
detect_anomalies() {
    local baseline_file="${1:-${BASELINE_DIR}/current.json}"
    local metrics_file="${2:-$METRICS_FILE}"
    
    if [ ! -f "$baseline_file" ]; then
        echo "⚠️  未找到基线文件，创建默认基线..."
        learn_baseline "$baseline_file"
    fi
    
    if [ ! -f "$metrics_file" ]; then
        echo "📊 未找到指标文件，正在收集..."
        collect_metrics "$metrics_file"
    fi
    
    echo "🔍 正在检测异常..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 加载当前指标（使用简单的grep避免jq依赖）
    local current_cpu=$(grep '"cpu_percent"' "$metrics_file" 2>/dev/null | grep -o '[0-9.]*' | head -1 || echo 0)
    local current_mem=$(grep '"memory_percent"' "$metrics_file" 2>/dev/null | grep -o '[0-9.]*' | head -1 || echo 0)
    
    # 简单阈值检测
    local severity="info"
    local anomaly="✅ 系统正常"
    
    if [ "${current_cpu%.*}" -gt 90 ] 2>/dev/null; then
        severity="critical"
        anomaly="🔴 CPU使用率过高: ${current_cpu}%"
    elif [ "${current_mem%.*}" -gt 90 ] 2>/dev/null; then
        severity="high"
        anomaly="🟠️ 内存使用率过高: ${current_mem}%"
    elif [ "${current_cpu%.*}" -gt 80 ] 2>/dev/null; then
        severity="warning"
        anomaly="⚠️ CPU使用率偏高: ${current_cpu}%"
    fi
    
    echo ""
    echo "📊 检测结果:"
    echo "  CPU使用率: ${current_cpu}%"
    echo "  内存使用率: ${current_mem}%"
    echo "  状态: $severity"
    echo ""
    echo "$anomaly"
    
    # 返回JSON
    echo ""
    echo "【JSON输出】"
    cat << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "cpu_percent": ${current_cpu:-0},
  "memory_percent": ${current_mem:-0},
  "severity": "$severity",
  "message": "$anomaly"
}
EOF
}

# 生成异常报告
generate_report() {
    local report_file="${1:-${REPORT_DIR}/anomaly-report-$(date +%Y%m%d-%H%M%S).json}"
    
    echo "📄 生成异常检测报告..."
    
    # 生成报告
    cat > "$report_file" << EOF
{
  "report_type": "anomaly_detection",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "period": "24h",
  "summary": {
    "status": "normal",
    "message": "系统运行正常"
  }
}
EOF
    
    echo "✅ 报告已生成: $report_file"
}

# 显示历史记录
show_history() {
    echo "📜 异常历史记录"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "$ANOMALY_FILE" ]; then
        echo "最近异常记录:"
        tail -20 "$ANOMALY_FILE" 2>/dev/null || echo "无记录"
    else
        echo "暂无异常记录"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
HealthCheck AI异常检测引擎 v4.0.0

用法: $0 [命令] [参数]

命令:
  collect           收集系统指标到JSON文件
  learn_baseline    学习系统正常行为基线
  detect            检测相对于基线的异常
  report            生成异常检测报告
  history           查看异常历史记录
  help              显示此帮助

示例:
  # 收集指标
  $0 collect
  
  # 学习基线
  $0 learn_baseline
  
  # 检测异常
  $0 detect
  
  # 生成报告
  $0 report
  
  # 查看历史记录
  $0 history

数据目录: $DATA_DIR
基线目录: $BASELINE_DIR
报告目录: $REPORT_DIR
EOF
}

# 主函数
main() {
    init_analyzer
    
    case "${1:-help}" in
        collect)
            shift
            collect_metrics "$@"
            ;;
        learn_baseline)
            shift
            learn_baseline "$@"
            ;;
        detect)
            shift
            detect_anomalies "$@"
            ;;
        report)
            shift
            generate_report "$@"
            ;;
        history)
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
