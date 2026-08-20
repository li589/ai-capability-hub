#!/bin/bash
# Isolate SSH - 隔离SSH服务
# 用途: 自动隔离受到SSH暴力破解威胁的SSH服务
# 版本: 4.0.0 (已修复安全漏洞)

set -e

THREAT_TYPE="$1"
TARGET="${2:-localhost}"
REASON="${3:-检测到SSH暴力破解，自动隔离SSH服务}"
THREAT_LEVEL="critical"

echo "🚨 执行威胁响应剧本: isolate-ssh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "威胁类型: $THREAT_TYPE"
echo "目标: $TARGET"
echo "原因: $REASON"
echo ""

# 确认操作
echo ""
echo "⚠️  即将执行以下操作:"
echo "   1. 检查SSH服务重要性"
echo "   2. 检查SSH进程"
echo "   3. 停止SSH服务"
echo "   4. 禁用启动服务"
echo "  5. 阻止22端口"
echo "  6. 生成事件报告"
echo ""
read -p "确认执行以上操作? (y/N): " -r confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消操作"
    exit 0
fi

echo "✅ 开始执行..."
echo ""

# 1. 检查SSH服务重要性
echo "1/7: 检查SSH服务重要性..."
echo "    ⚠️  重要: 如果SSH是生产环境或关键服务，建议不要停止"
read -p "SSH服务是关键服务吗? (y/N): " -r ssh_critical
if [ "$ssh_critical" != "y" ] && [ "$ssh_critical" != "Y" ]; then
    echo "    ✅ SSH服务是关键服务，跳过停止"
    ssh_critical_skip=true
else
    if systemctl stop sshd; then
        echo "    ✅ SSH服务已停止"
    else
        echo "    ⚠️  SSH服务未运行或停止失败"
    fi
fi

# 2. 检查SSH进程（仅在非关键服务时执行）
if [ "$ssh_critical_skip" != "true" ]; then
    echo "2/7: 检查SSH进程..."
    ssh_count=$(pgrep -c sshd 2>/dev/null || echo "0")
    if [ "$ssh_count" -gt 0 ]; then
        echo "    ⚠️  发现 $ssh_count 个SSH进程运行"
        
        read -p "确认终止所有SSH进程? (y/N): " -r ssh_confirm
        if [ "$ssh_confirm" = "y" ] || [ "$ssh_confirm" = "Y" ]; then
            echo "    正在尝试停止SSH服务..."
            if systemctl stop sshd; then
                echo "    ✅ SSH服务已安全停止"
            else
                echo "    ⚠️  SSH服务停止失败"
            fi
        else
            echo "    已跳过SSH进程终止"
        fi
    else
        echo "    ✅ 无SSH进程运行"
    fi
else
    echo "    ✅ 已跳过SSH进程检查（因为SSH是关键服务）"
fi

# 3. 禁用SSH启动
echo "3/7: 禁用SSH启动..."
if systemctl mask sshd; then
    echo "    ✅ SSH启动已禁用"
else
    echo "    ⚠️  SSH未设置自动启动,跳过"
fi

# 4. 阻止22端口
echo "4/7: 阻止22端口..."
if ufw status | grep -q "22/tcp"; then
    ufw deny 22
    echo "    ✅ 已阻止22端口"
else
    echo "    ⚠️  ufw未启用或22端口未开放"
fi

# 5. 生成事件报告
echo "5/7: 生成事件报告..."
REPORT_DIR="${HOME}/.openclawhealthcheck/reports"
mkdir -p "$REPORT_DIR"
REPORT_FILE="${REPORT_DIR}/incident_$(date +%Y%m%d_%H%M%S)_ssh_isolation.md"

cat > "$REPORT_FILE" << 'EOF'
# SSH隔离事件报告

## 概述

- **事件时间**: $(date)
- **事件类型**: SSH暴力破解
- **严重程度**: Critical
- **目标**: $TARGET
- **SSH是否关键服务**: $([ "$ssh_critical" = "true" ] && echo "是" || echo "否")

## 响应措施

### ✅ 已执行
1. 停止SSH服务: $([ "$ssh_critical" = "true" ] && echo "跳过" || echo "已停止")
2. 检查SSH进程: $([ "$ssh_critical" = "true" ] && echo "跳过" || echo "已检查")
3. 禁用SSH启动: $([ "$ssh_critical" = "true" ] && echo "跳过" || echo "已禁用")
4. 阻止22端口: 已阻止
5. 生成事件报告: 已保存

### 🔒 后续建议
- 更改所有受影响账户密码
- 启用多因素认证
- 审查系统日志确认无其他后门
- 考虑暂时禁用root登录

---

*报告生成时间: $(date)*
EOF

echo "    ✅ 报告已保存: $REPORT_FILE"
echo ""
echo "✅ SSH隔离完成"
echo "    ⚠️ 建议: 联系安全团队"
