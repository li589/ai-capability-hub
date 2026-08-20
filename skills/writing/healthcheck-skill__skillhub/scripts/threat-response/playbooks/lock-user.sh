#!/bin/bash
# Lock User Account - 锁定受威胁账户
# 用途: 暂止受威胁用户的系统访问
# 版本: 4.0.0 (已修复安全漏洞)

set -e

THREAT_TYPE="$1"
TARGET_USER="${2:-$USER}"
REASON="${3:$USER的账户可能已被破解或权限提升，需要锁定}"
THREAT_LEVEL="critical"

echo "🚨 执行威胁响应剧本: lock-user"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "威胁类型: $THREAT_TYPE"
echo "目标用户: $TARGET_USER"
echo "原因: $REASON"
echo ""

# 确认操作
echo ""
echo "⚠️  即将执行以下操作:"
echo "  1. 禁用账户"
echo "  2. 更改密码"
echo "  3.保存事件报告"
echo ""
read -p "确认执行以上操作? (y/N): " -r confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消操作"
    exit 0
fi

echo "✅ 开始执行..."
echo ""

# 1. 禁用账户
echo "1/4: 禁用账户..."
if id "$TARGET_USER" &> /dev/null 2>/dev/null; then
    usermod -L $TARGET_USER
    echo "    ✅ 用户 $TARGET_USER 已禁用"
else
    echo "    ⚠️  用户不存在或禁用失败"
fi

# 2. 尝试退出当前会话（安全方式）
echo "    尝试退出 $TARGET_USER 会话..."
pkill -u $TARGET_USER 2>/dev/null && echo "    ✅ 会话已退出" || echo "    ℹ️  无活跃会话"

# 3. 锁定账户（如果存在）
if id "$TARGET_USER" &> /dev/null; then
    usermod -L $TARGET_USER
    passwd -l "$TARGET_USER" 2>/dev/null | echo "    ✅ 已锁定账户密码"
fi

# 4. 保存事件报告
echo "4/4: 生成事件报告..."
REPORT_DIR="${HOME}/.openclawhealthcheck/reports"
REPORT_FILE="${REPORT_DIR}/lockout_$(date +%Y%m%d_%H%M%S)_user_${TARGET_USER}.md"

cat > "$REPORT_FILE" << 'EOF'
# 账户锁定事件报告

## 概述

- **事件时间**: $(date)
- **事件类型**: $THREAT_TYPE
- **严重程度**: $THREAT_LEVEL
- **目标用户**: $TARGET_USER

## 响应措施

### ✅ 已执行
1. 禁用账户: 已禁用
2. 强制退出会话: 已强制退出或无需强制退出
3. 锁定账户密码: 已锁定

### 🔒 后续建议
- 重置密码或重置凭证
- 联系安全团队
- 检查账户权限并移除不必要权限
- 开启多因素认证

---

*报告生成时间: $(date)*
EOF

echo "    ✅ 报告已保存: $REPORT_FILE"
echo ""
echo "✅ 账户锁定完成"
echo "    ⚠️ 建议: 联系安全团队"
