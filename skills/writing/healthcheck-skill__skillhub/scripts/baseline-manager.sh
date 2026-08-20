#!/bin/bash
# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"
# HealthCheck Baseline Manager - 安全基线管理
# 版本: v3.0.0
# 用途: 建立和管理系统安全基线快照

set -e

BASELINE_DIR="${HOME}/.openclaw/baselines"
CURRENT_BASELINE="${BASELINE_DIR}/current.json"

# 初始化基线目录
init_baseline_dir() {
    if [ ! -d "$BASELINE_DIR" ]; then
        mkdir -p "$BASELINE_DIR"
        echo "✅ 基线目录已创建: $BASELINE_DIR"
    fi
}

# 验证基线名称安全性
validate_baseline_name() {
    local name="$1"

    # 检查长度
    if [ ${#name} -gt 50 ]; then
        echo "❌ 错误: 基线名称过长（最大50字符）"
        return 1
    fi

    # 检查非法字符
    if echo "$name" | grep -qE '[<>'\''"\\$|&;]'; then
        echo "❌ 错误: 基线名称包含非法字符"
        return 1
    fi

    return 0
}

# 创建系统基线快照
create_baseline() {
    local name="${1:-$(date +%Y%m%d-%H%M%S)}"

    # 验证名称
    validate_baseline_name "$name" || return 1

    local baseline_file="${BASELINE_DIR}/${name}.json"

    echo "🔍 正在创建系统基线快照: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 收集系统信息
    local baseline_data='{'
    
    # 时间戳
    baseline_data+="\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
    baseline_data+="\"name\":\"${name}\","
    baseline_data+="\"hostname\":\"$(hostname)\","
    
    # 收集关键文件权限
    echo "📁 收集关键文件权限..."
    baseline_data+="\"file_permissions\":{"
    local files=(
        "${HOME}/.openclaw/config.json"
        "${HOME}/.ssh"
        "/etc/ssh/sshd_config"
    )
    local first=true
    for file in "${files[@]}"; do
        if [ -e "$file" ]; then
            if [ "$first" = true ]; then
                first=false
            else
                baseline_data+=","
            fi
            local perm=$(stat -c "%a" "$file" 2>/dev/null || echo "unknown")
            local owner=$(stat -c "%U" "$file" 2>/dev/null || echo "unknown")
            baseline_data+="\"${file}\":{\"perm\":\"${perm}\",\"owner\":\"${owner}\"}"
        fi
    done
    baseline_data+="},"
    
    # 收集网络配置
    echo "🌐 收集网络配置..."
    baseline_data+="\"network_config\":{"
    baseline_data+="\"hostname\":\"$(hostname)\","
    # 使用 tr 移除控制字符，避免 JSON 解析错误
    # 如果输出为空，使用默认值
    local interfaces_json=$(ip -j addr show 2>/dev/null | tr -d '\000-\037')
    [ -z "$interfaces_json" ] && interfaces_json='[]'
    local routes_json=$(ip -j route show 2>/dev/null | tr -d '\000-\037')
    [ -z "$routes_json" ] && routes_json='[]'
    local listeners_json=$(ss -tlnp -j 2>/dev/null | tr -d '\000-\037')
    [ -z "$listeners_json" ] && listeners_json='[]'
    baseline_data+="\"interfaces\":$interfaces_json,"
    baseline_data+="\"routes\":$routes_json,"
    baseline_data+="\"listeners\":$listeners_json"
    baseline_data+="},"
    
    # 收集用户和组
    echo "👥 收集用户信息..."
    baseline_data+="\"users\":{"
    baseline_data+="\"system\":$(cat /etc/passwd | wc -l),"
    baseline_data+="\"sudoers\":$(getent group sudo | tr ',' '\n' | wc -l),"
    baseline_data+="\"ssh_users\":$(grep -c "ssh" /etc/passwd 2>/dev/null || echo 0)"
    baseline_data+="},"
    
    # 收集服务状态
    echo "⚙️  收集服务状态..."
    # 清理控制字符，避免JSON格式错误
    local ssh_status=$(systemctl is-active sshd 2>/dev/null | tr -cd '[:print:]' || echo 'unknown')
    local fw_status=$(systemctl is-active ufw 2>/dev/null | tr -cd '[:print:]' || systemctl is-active firewalld 2>/dev/null | tr -cd '[:print:]' || echo 'unknown')
    local running_services=$(systemctl list-units --state=running --type=service 2>/dev/null | wc -l)
    baseline_data+="\"services\":{"
    baseline_data+="\"ssh\":\"${ssh_status}\","
    baseline_data+="\"firewall\":\"${fw_status}\","
    baseline_data+="\"total_running\":${running_services}"
    baseline_data+="},"
    
    # 收集SSH配置
    echo "🔑 收集SSH配置..."
    baseline_data+="\"ssh_config\":{"
    if [ -f "/etc/ssh/sshd_config" ]; then
        baseline_data+="\"password_auth\":\"$(grep -E "^PasswordAuthentication" /etc/ssh/sshd_config | awk '{print $2}' || echo 'default')\","
        baseline_data+="\"root_login\":\"$(grep -E "^PermitRootLogin" /etc/ssh/sshd_config | awk '{print $2}' || echo 'default')\","
        baseline_data+="\"port\":\"$(grep -E "^Port" /etc/ssh/sshd_config | awk '{print $2}' || echo '22')\""
    else
        baseline_data+="\"status\":\"not_found\""
    fi
    baseline_data+="}"
    
    baseline_data+='}'
    
    # 保存基线
    echo "$baseline_data" | jq . > "$baseline_file"
    
    # 更新当前基线链接
    ln -sf "$baseline_file" "$CURRENT_BASELINE"
    
    echo ""
    echo "✅ 基线快照已创建: $baseline_file"
    echo ""
    
    # 显示摘要
    echo "📊 基线摘要:"
    echo "$baseline_data" | jq -r '
        "创建时间: \(.timestamp)",
        "主机名: \(.hostname)",
        "文件权限: \( .file_permissions | keys | length) 个文件",
        "网络接口: \( .network_config.interfaces | length) 个",
        "系统用户: \(.users.system) 个",
        "运行服务: \(.services.total_running) 个"
    '
}

# 列出所有基线
list_baselines() {
    echo "📋 可用基线快照:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ ! -d "$BASELINE_DIR" ] || [ -z "$(ls -A $BASELINE_DIR/*.json 2>/dev/null)" ]; then
        echo "❌ 没有找到基线快照"
        echo "使用: baseline-manager.sh create [名称] 创建基线"
        return 1
    fi
    
    local i=1
    for baseline in "$BASELINE_DIR"/*.json; do
        if [ -f "$baseline" ]; then
            local name=$(basename "$baseline" .json)
            local timestamp=$(jq -r '.timestamp' "$baseline" 2>/dev/null || echo "unknown")
            local hostname=$(jq -r '.hostname' "$baseline" 2>/dev/null || echo "unknown")
            
            # 标记当前基线
            local current=""
            if [ "$baseline" -ef "$CURRENT_BASELINE" ]; then
                current=" (当前)"
            fi
            
            printf "%2d. %-20s  %-20s  %s%s\n" "$i" "$name" "$hostname" "$timestamp" "$current"
            i=$((i + 1))
        fi
    done
}

# 比较基线差异
compare_baselines() {
    local baseline1="$1"
    local baseline2="$2"
    
    if [ -z "$baseline1" ]; then
        echo "❌ 请指定基线文件"
        echo "用法: baseline-manager.sh compare <基线1> [基线2]"
        return 1
    fi
    
    # 如果只有一个参数，与当前基线比较
    if [ -z "$baseline2" ]; then
        baseline2="current"
    fi
    
    local file1="${BASELINE_DIR}/${baseline1}.json"
    local file2="${BASELINE_DIR}/${baseline2}.json"
    
    if [ ! -f "$file1" ]; then
        echo "❌ 基线不存在: $baseline1"
        return 1
    fi
    
    if [ ! -f "$file2" ]; then
        echo "❌ 基线不存在: $baseline2"
        return 1
    fi
    
    echo "🔍 比较基线: $baseline1 vs $baseline2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 使用jq比较
    jq --argfile old "$file1" --argfile new "$file2" -n '
        def changes:
            [$old, $new] | transpose | map({
                key: .[0].key,
                old: .[0].value,
                new: .[1].value
            }) | map(select(.old != .new));
        
        {
            timestamp: now,
            comparison: {
                baseline_old: $old.name,
                baseline_new: $new.name,
                changes_detected: (changes | length)
            }
        }
    ' 2>/dev/null || echo "⚠️  详细比较需要jq工具"
    
    # 简单文本比较
    echo ""
    echo "📊 关键差异:"
    
    # 比较文件权限
    local files_changed=$(diff <(jq -S '.file_permissions' "$file1") <(jq -S '.file_permissions' "$file2") 2>/dev/null | wc -l)
    if [ "$files_changed" -gt 0 ]; then
        echo "  📝 文件权限变化: $files_changed 项"
    fi
    
    # 比较服务状态
    local old_ssh=$(jq -r '.services.ssh' "$file1")
    local new_ssh=$(jq -r '.services.ssh' "$file2")
    if [ "$old_ssh" != "$new_ssh" ]; then
        echo "  ⚙️  SSH服务: $old_ssh → $new_ssh"
    fi
    
    # 比较用户数量
    local old_users=$(jq -r '.users.system' "$file1")
    local new_users=$(jq -r '.users.system' "$file2")
    if [ "$old_users" != "$new_users" ]; then
        echo "  👥 用户数量: $old_users → $new_users"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
HealthCheck 基线管理器 v3.0.0

用法: $0 [命令] [参数]

命令:
  create [name]           创建新的基线快照
  list                    列出所有基线快照
  compare <b1> [b2]       比较两个基线差异
  delete <name>           删除基线快照
  info <name>             显示基线详细信息
  help                    显示此帮助

示例:
  # 创建基线快照
  $0 create production-baseline
  
  # 列出所有基线
  $0 list
  
  # 比较当前系统与基线
  $0 compare production-baseline current
  
  # 查看基线详情
  $0 info production-baseline

数据存储: $BASELINE_DIR
EOF
}

# 主函数
main() {
    init_baseline_dir
    
    case "${1:-help}" in
        create)
            shift
            create_baseline "$@"
            ;;
        list|ls)
            list_baselines
            ;;
        compare|diff)
            shift
            compare_baselines "$@"
            ;;
        delete|rm)
            shift
            if [ -z "$1" ]; then
                echo "❌ 请指定要删除的基线名称"
                exit 1
            fi
            rm -f "${BASELINE_DIR}/${1}.json"
            echo "✅ 已删除基线: $1"
            ;;
        info|show)
            shift
            if [ -z "$1" ]; then
                echo "❌ 请指定基线名称"
                exit 1
            fi
            local file="${BASELINE_DIR}/${1}.json"
            if [ -f "$file" ]; then
                jq . "$file"
            else
                echo "❌ 基线不存在: $1"
                exit 1
            fi
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
