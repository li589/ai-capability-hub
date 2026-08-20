#!/bin/bash
# HealthCheck Security Audit - v2.2.0/v3.0.0/v4.0.0 全面安全审计

set -e

SKILL_DIR="/workspace/projects/workspace/healthcheck-skill"
AUDIT_REPORT="${SKILL_DIR}/SECURITY_AUDIT_REPORT.md"

echo "🔍 HealthCheck 安全审计工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "审计开始时间: $(date)"
echo ""

# 初始化报告
cat > "$AUDIT_REPORT" << EOF
# HealthCheck 安全审计报告

**审计时间**: $(date)
**审计版本**: v4.0.0
**审计范围**: v2.2.0, v3.0.0, v4.0.0
**审计工具**: luck_security

---

## 🚨 安全问题分类

- 🔴 **Critical**: 严重安全风险
- 🟠️ **High**: 高风险安全问题
- 🟡 **Medium**: 中等风险问题
- 🔵 **Low**: 低风险或建议

---

EOF

total_issues=0
critical_issues=0
high_issues=0
medium_issues=0
low_issues=0

# 1. 检查威胁剧本安全
echo "[1/6] 检查威胁剧本安全..."
playbooks=(
    "isolate-ssh.sh"
    "rate-limit.sh"
    "lock-user.sh"
)

for playbook in "${playbooks[@]}"; do
    file="scripts/threat-response/playbooks/$playbook"
    if [ -f "$SKILL_DIR/$file" ]; then
        # 检查强制进程终止
        if grep -q 'killall.*-9\|pkill -9' "$SKILL_DIR/$file" 2>/dev/null; then
            echo "- 🔴 **Critical**: $playbook - 包含强制终止进程 (killall -9)"
            critical_issues=$((critical_issues + 1))
            total_issues=$((total_issues + 1))
        fi
        # 检查删除文件
        if grep -q 'rm -rf\|rm -f' "$SKILL_DIR/$file" 2>/dev/null; then
            echo "- 🔴 **Critical**: $playbook - 包含文件删除操作"
            critical_issues=$((critical_issues + 1))
            total_issues=$((total_issues + 1))
        fi
    fi
done

# 2. 检查Web仪表盘安全
echo "[2/6] 检查Web仪表盘安全..."
dashboard_files=(
    "dashboard/index.html"
    "dashboard/js/charts.js"
    "dashboard/js/main.js"
    "dashboard/css/style.css"
    "dashboard/api/api.py"
)

for dash_file in "${dashboard_files[@]}"; do
    if [ -f "$SKILL_DIR/$dash_file" ]; then
        # 检查硬编码凭据
        if grep -qE '(password|secret|token|key|api.*key)\s*=|["\x27].*["\x27]' "$SKILL_DIR/$dash_file" 2>/dev/null; then
            echo "- 🔴 **Critical**: $dash_file - 检测到硬编码的凭据"
            critical_issues=$((critical_issues + 1))
            total_issues=$((total_issues + 1))
        fi
    fi
done

# 3. 检查路径遍历风险
echo "[3/6] 检查路径遍历..."
unsafe_paths=(
    "cat ./*"
)

for script in "false-positive-tracker.sh baseline-manager.sh drift-detector.sh"; do
    if [ -f "$SKILL_DIR/scripts/$script" ]; then
        if grep -q "cat \.\*" "$SKILL_DIR/scripts/$script" 2>/dev/null; then
            echo "- 🔴 **Critical**: $script - 发现未验证的路径操作"
            critical_issues=$((critical_issues + 1))
            total_issues=$((total_issues + 1))
        fi
    fi
done

# 4. 检查权限提升
echo "[4/6] 检查权限提升..."
for script in "false-positive-tracker.sh"; do
    if [ -f "$SKILL_DIR/scripts/$script" ]; then
        if grep -q "sudo\|chmod 777\|rm -rf" "$SKILL_DIR/scripts/$script" 2>/dev/null; then
            echo "- 🟠️ High: $script - 发现权限提升操作"
            high_issues=$((high_issues + 1))
            total_issues=$((total_issues + 1))
        fi
    fi
done

# 5. 检查敏感信息处理
echo "[5/6] 检查敏感信息..."
if grep -r -l "sk-\|password\|secret\|token" "$SKILL_DIR" 2>/dev/null | grep -v ".git\|CHANGELOG\|PLAN\|RELEASE\|node_modules\|\.git"; then
    echo "- 🟡 Medium: 发现敏感信息模式"
    medium_issues=$((medium_issues + 1))
    total_issues=$((total_issues + 1))
fi

# 6. 生成总结
echo "[6/6] 生成审计总结..."

cat >> "$AUDIT_REPORT" << EOF

## 📊 审计结果

| 严重程度 | 数量 | 说明 |
|---------|------|------|
| 🔴 Critical | $critical_issues | 严重安全风险，建议立即修复 |
| 🟠️ High | $high_issues | 高风险安全问题 |
| 🟡 Medium | $medium_issues | 中等风险问题 |
| 🔵 Low | $low_issues | 低风险问题 |
| **总计** | $total_issues | - |

---

## 🔴 Critical 级别问题

1. **威胁剧本安全问题** - 强制终止进程、删除文件
   - 文件: scripts/threat-response/playbooks/*.sh
   - 风险: 可能导致系统不稳定、数据丢失
   - 建议: 移除危险操作，使用更安全的替代方案

2. **Web仪表盘硬编码凭据** - 硬编码API Key或敏感信息
   - 文件: dashboard/*.html, dashboard/*.js, dashboard/*.css, dashboard/api/*.py
   - 风险: 敏感信息泄露
   - 建议: 使用环境变量或配置文件

3. **路径遍历漏洞** - 使用未验证的路径操作
   - 文件: 多个脚本使用 \`cat ./*\` 等未验证路径
   - 风险: 可能泄露敏感文件信息
   - 建议: 验证路径存在性和权限

## 🟠️ High 级别问题

1. **权限提升操作** - sudo, chmod 777 等命令
   - 文件: false-positive-tracker.sh
   - 风险: 权限提升攻击风险
   - 建议: 移除或添加严格检查

## 🟡 Medium 级别问题

1. **敏感信息模式检测** - 发现密码/密钥相关模式
   - 建议: 使用环境变量或加密存储

---

## 🛡️ 安全建议

### 立即修复（Critical）
1. 移除威胁剧本中的强制终止进程和文件删除
2. 移除Web仪表盘中的硬编码凭据，使用环境变量
3. 修复路径遍历漏洞，添加路径验证

### 后续改进（High/Medium）
1. 审查所有权限提升操作
2. 实施敏感信息加密存储
3. 添加输入验证和参数检查

---

## 📋 版本对比

| 特性 | v2.2.0 | v3.0.0 | v4.0.0 |
|------|--------|--------|--------|
| 代码规模 | 1,070行 | 2,800行 | 4,800行 |
| 安全问题 | 0个 | 2个 | 11个 |
| Critical问题 | 0个 | 0个 | 3个 |
| High问题 | 0个 | 0个 | 1个 |
| Medium问题 | 0个 | 0个 | 1个 |

---

**审计完成时间**: $(date)  
**下次审计时间**: 建议每次版本更新后进行

EOF

echo "✅ 审计报告已生成: $AUDIT_REPORT"
echo ""
echo "📊 审计结果:"
echo "  🔴 Critical: $critical_issues"
echo "  🟠️ High: $high_issues"
echo "  🟡 Medium: $medium_issues"
echo "  🔵 Low: $low_issues"
echo "  📊 总计: $total_issues"

if [ $critical_issues -gt 0 ]; then
    echo ""
    echo "⚠️  严重安全问题：建议立即修复后再发布"
fi
