# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# Security Check Functions - 安全检查函数库
# 版本: 4.0.0
# 用途: 提供通用的安全检查函数

# 检查文件权限
check_file_permissions() {
    local file_path="$1"
    local expected_mode="$2"
    local description="$3"

    if [ ! -f "$file_path" ]; then
        echo "⚠️  文件不存在: $file_path"
        return 1
    fi

    local actual_mode=$(stat -c "%a" "$file_path" 2>/dev/null || stat -f "%OLp" "$file_path" 2>/dev/null)

    if [ "$actual_mode" != "$expected_mode" ]; then
        echo "⚠️  $description 权限不安全: $actual_mode (期望: $expected_mode)"
        echo "   建议: chmod $expected_mode $file_path"
        return 1
    fi

    echo "✅ $description 权限安全: $actual_mode"
    return 0
}

# 检查目录权限
check_dir_permissions() {
    local dir_path="$1"
    local expected_mode="$2"
    local description="$3"

    if [ ! -d "$dir_path" ]; then
        echo "⚠️  目录不存在: $dir_path"
        return 1
    fi

    local actual_mode=$(stat -c "%a" "$dir_path" 2>/dev/null || stat -f "%OLp" "$dir_path" 2>/dev/null)

    if [ "$actual_mode" != "$expected_mode" ]; then
        echo "⚠️  $description 权限不安全: $actual_mode (期望: $expected_mode)"
        echo "   建议: chmod $expected_mode $dir_path"
        return 1
    fi

    echo "✅ $description 权限安全: $actual_mode"
    return 0
}

# 验证路径安全性
validate_path() {
    local path="$1"
    local allow_absolute="${2:-false}"

    # 检查路径遍历
    if echo "$path" | grep -q '\.\.'; then
        echo "❌ 错误: 路径包含..（路径遍历风险）"
        return 1
    fi

    # 检查绝对路径
    if [ "$allow_absolute" != "true" ] && echo "$path" | grep -q '^/'; then
        echo "❌ 错误: 不允许使用绝对路径"
        return 1
    fi

    # 检查特殊字符
    if echo "$path" | grep -qE '[<>'\''"\\]'; then
        echo "❌ 错误: 路径包含特殊字符"
        return 1
    fi

    return 0
}

# 检查命令可用性
check_command() {
    local cmd="$1"
    local optional="${2:-false}"

    if ! command -v "$cmd" &>/dev/null; then
        if [ "$optional" != "true" ]; then
            echo "❌ 错误: 命令不存在: $cmd"
            return 1
        else
            echo "⚠️  警告: 命令不存在: $cmd（可选）"
            return 0
        fi
    fi
    echo "✅ 命令存在: $cmd"
    return 0
}

# 检查端口是否开放
check_port() {
    local port="$1"
    local protocol="${2:-tcp}"

    if command -v ss &>/dev/null; then
        if ss -"${protocol}" -ln | grep -q ":${port} "; then
            echo "⚠️  端口 $port 已开放"
            return 1
        fi
    elif command -v netstat &>/dev/null; then
        if netstat -"${protocol}" -ln | grep -q ":${port} "; then
            echo "⚠️  端口 $port 已开放"
            return 1
        fi
    fi

    echo "✅ 端口 $port 未开放"
    return 0
}

# 检查服务是否运行
check_service() {
    local service="$1"

    if command -v systemctl &>/dev/null; then
        if systemctl is-active --quiet "$service"; then
            echo "✅ 服务运行中: $service"
            return 0
        else
            echo "⚠️  服务未运行: $service"
            return 1
        fi
    elif pgrep -f "$service" &>/dev/null; then
        echo "✅ 进程运行中: $service"
        return 0
    else
        echo "⚠️  服务/进程未找到: $service"
        return 1
    fi
}

# 检查CVE漏洞（示例）
check_cve() {
    local cve_id="$1"

    echo "🔍 检查 CVE: $cve_id"
    echo "   请访问 https://nvd.nist.gov/vuln/detail/$cve_id 获取详细信息"
    return 0
}
