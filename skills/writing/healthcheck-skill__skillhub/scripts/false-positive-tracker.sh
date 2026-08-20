# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# False Positive Tracker - 误报率追踪系统
# 版本: v2.2.0
# 用途: 记录检测结果并计算误报率

set -e

# 配置
DATA_DIR="${HOME}/.openclaw/logs/healthcheck"
DB_FILE="${DATA_DIR}/detection-history.db"
REPORT_DIR="${DATA_DIR}/reports"

# 初始化数据目录
init_db() {
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR" "$REPORT_DIR"
    fi

    # 使用安全写入
    if [ ! -f "$DB_FILE" ]; then
        local header="# OpenClaw HealthCheck Detection History\n# 格式: TIMESTAMP|CHECK_TYPE|RISK_LEVEL|RESULT|IS_FALSE_POSITIVE|CONFIRMED_BY_USER|DETAILS\n"

        # 使用临时文件进行原子写入
        local temp_file="${DB_FILE}.$$"
        echo -e "$header" > "$temp_file"
        if [ $? -eq 0 ]; then
            mv "$temp_file" "$DB_FILE"
            echo "✅ 数据库已初始化: $DB_FILE"
        else
            rm -f "$temp_file"
            echo "❌ 数据库初始化失败"
            return 1
        fi
    fi
}

# 记录检测事件
log_detection() {
    local check_type="$1"      # 检查类型: cve, skill, config, permission
    local risk_level="$2"      # 风险等级: critical, high, medium, low
    local result="$3"          # 结果: pass, fail, warning
    local details="$4"         # 详细信息 (JSON格式)
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # 格式: TIMESTAMP|CHECK_TYPE|RISK_LEVEL|RESULT||false|DETAILS
    echo "${timestamp}|${check_type}|${risk_level}|${result}||false|${details}" >> "$DB_FILE"
    
    echo "✅ 检测已记录: ${check_type} - ${result}"
}

# 标记误报
mark_false_positive() {
    local line_number="$1"
    local is_fp="$2"           # true 或 false
    local reason="$3"          # 误报原因
    
    # 读取对应行
    local line=$(sed -n "${line_number}p" "$DB_FILE" | grep -v "^#")
    if [ -z "$line" ]; then
        echo "❌ 行号 ${line_number} 不存在"
        return 1
    fi
    
    # 更新误报标记
    local new_line=$(echo "$line" | awk -F'|' -v fp="$is_fp" -v reason="$reason" '{
        print $1"|"$2"|"$3"|"$4"|"fp"|true|"reason
    }')
    
    # 替换原行
    sed -i "${line_number}s/.*/${new_line}/" "$DB_FILE"
    
    echo "✅ 已标记为${is_fp}: 第${line_number}行"
}

# 计算误报率
calculate_fp_rate() {
    local check_type="$1"      # 可选: 特定检查类型或 "all"
    local days="${2:-30}"      # 默认最近30天

    # 检查数据库文件
    if [ ! -f "$DB_FILE" ]; then
        echo "❌ 数据库文件不存在: $DB_FILE"
        return 1
    fi

    # 检查jq命令
    if ! command -v jq &>/dev/null; then
        echo "⚠️  jq未安装，使用简单统计"
        return 2
    fi

    local since_date=$(date -d "-${days} days" +"%Y-%m-%d" 2>/dev/null || date -v-${days}d +"%Y-%m-%d" 2>/dev/null || echo "")

    if [ -z "$since_date" ]; then
        echo "❌ 无法计算日期"
        return 1
    fi

    # 过滤数据
    local filter=""
    if [ "$check_type" != "all" ] && [ -n "$check_type" ]; then
        filter="|${check_type}|"
    fi

    # 统计数据
    local total=0
    local confirmed_fp=0
    local confirmed_valid=0
    local pending=0

    while IFS='|' read -r timestamp check_type risk result is_fp confirmed details; do
        # 跳过注释和空行
        [[ "$timestamp" =~ ^# ]] && continue
        [ -z "$timestamp" ] && continue
        
        # 日期过滤
        local check_date="${timestamp%%T*}"
        if [[ "$check_date" < "$since_date" ]]; then
            continue
        fi
        
        # 类型过滤
        if [ -n "$filter" ] && [[ ! "$check_type" == *"$check_type"* ]]; then
            continue
        fi
        
        total=$((total + 1))
        
        if [ "$confirmed" == "true" ]; then
            if [ "$is_fp" == "true" ]; then
                confirmed_fp=$((confirmed_fp + 1))
            else
                confirmed_valid=$((confirmed_valid + 1))
            fi
        else
            pending=$((pending + 1))
        fi
    done < "$DB_FILE"
    
    # 计算误报率
    local fp_rate="0.00"
    if [ $confirmed_valid -gt 0 ] || [ $confirmed_fp -gt 0 ]; then
        local confirmed_total=$((confirmed_valid + confirmed_fp))
        fp_rate=$(awk "BEGIN {printf \"%.2f\", ($confirmed_fp / $confirmed_total) * 100}")
    fi
    
    # 输出结果
    cat << EOF
{
  "period_days": ${days},
  "check_type": "${check_type}",
  "statistics": {
    "total_detections": ${total},
    "confirmed_valid": ${confirmed_valid},
    "confirmed_false_positive": ${confirmed_fp},
    "pending_review": ${pending}
  },
  "false_positive_rate": ${fp_rate},
  "accuracy_rate": $(awk "BEGIN {printf \"%.2f\", 100 - $fp_rate}")
}
EOF
}

# 按风险等级统计
analyze_by_risk_level() {
    local days="${1:-30}"
    
    echo "{"
    echo '  "risk_level_analysis": {'
    
    local first=true
    for level in critical high medium low; do
        local stats=$(calculate_fp_rate "$level" "$days")
        local fp_rate=$(echo "$stats" | grep "false_positive_rate" | sed 's/.*: \([0-9.]*\).*/\1/')
        local total=$(echo "$stats" | grep "total_detections" | sed 's/.*: \([0-9]*\).*/\1/')
        
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        
        cat << EOF
    "${level}": {
      "total": ${total:-0},
      "false_positive_rate": ${fp_rate:-0.00}
    }
EOF
    done
    
    echo "  }"
    echo "}"
}

# 生成报告
generate_report() {
    local format="${1:-text}"   # text, json, markdown
    local days="${2:-30}"
    
    local overall_stats=$(calculate_fp_rate "all" "$days")
    local overall_fp=$(echo "$overall_stats" | grep "false_positive_rate" | sed 's/.*: \([0-9.]*\).*/\1/')
    local overall_total=$(echo "$overall_stats" | grep "total_detections" | sed 's/.*: \([0-9]*\).*/\1/')
    
    case "$format" in
        json)
            echo "$overall_stats"
            ;;
        markdown)
            cat << EOF
# HealthCheck 误报率报告

生成时间: $(date)
统计周期: 最近${days}天

## 整体统计

| 指标 | 数值 |
|------|------|
| 总检测次数 | ${overall_total} |
| 整体误报率 | ${overall_fp}% |
| 整体准确率 | $(awk "BEGIN {printf \"%.2f\", 100 - $overall_fp}")% |

## 按风险等级统计

$(analyze_by_risk_level "$days" | jq -r '.risk_level_analysis | to_entries | .[] | "- \(.key): 误报率 \(.value.false_positive_rate)% (共\(.value.total)次检测)"')

## 说明

- **误报**: 检测结果为"问题"但实际是正常情况
- **准确率**: 100% - 误报率
- 建议误报率保持在5%以下

---
生成命令: false-positive-tracker.sh --report markdown
EOF
            ;;
        *)
            # Text format
            cat << EOF
📊 HealthCheck 误报率统计报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
统计周期: 最近${days}天
生成时间: $(date)

整体统计:
  总检测次数: ${overall_total}
  整体误报率: ${overall_fp}%
  整体准确率: $(awk "BEGIN {printf \"%.2f\", 100 - $overall_fp}")%

按风险等级误报率:
$(analyze_by_risk_level "$days" | jq -r '.risk_level_analysis | to_entries | .[] | "  \(.key | ascii_upcase): \(.value.false_positive_rate)% (\(.value.total)次检测)"')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
建议: 误报率保持在5%以下为优秀水平
EOF
            ;;
    esac
}

# 显示帮助
show_help() {
    cat << EOF
HealthCheck 误报率追踪系统 v2.2.0

用法: $0 [命令] [参数]

命令:
  log <check_type> <risk_level> <result> [details]  记录检测事件
  mark <line_number> <true|false> [reason]           标记误报
  rate [check_type] [days]                          计算误报率
  report [format] [days]                            生成报告 (text/json/markdown)
  analyze [days]                                    按风险等级分析
  init                                              初始化数据库

示例:
  # 记录CVE检测事件
  $0 log cve critical fail '{"cve":"CVE-2026-25253"}'
  
  # 标记第5行为误报
  $0 mark 5 true "实际为正常配置"
  
  # 查看最近30天整体误报率
  $0 rate all 30
  
  # 生成Markdown格式报告
  $0 report markdown 30

数据存储: ${DATA_DIR}
EOF
}

# 主函数
main() {
    init_db
    
    case "${1:-help}" in
        log)
            shift
            if [ $# -lt 3 ]; then
                echo "❌ 用法: $0 log <check_type> <risk_level> <result> [details]"
                exit 1
            fi
            log_detection "$@"
            ;;
        mark)
            shift
            if [ $# -lt 2 ]; then
                echo "❌ 用法: $0 mark <line_number> <true|false> [reason]"
                exit 1
            fi
            mark_false_positive "$@"
            ;;
        rate)
            shift
            calculate_fp_rate "${1:-all}" "${2:-30}"
            ;;
        report)
            shift
            generate_report "${1:-text}" "${2:-30}"
            ;;
        analyze)
            shift
            analyze_by_risk_level "${1:-30}"
            ;;
        init)
            init_db
            echo "✅ 数据库已初始化: ${DATA_DIR}"
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
