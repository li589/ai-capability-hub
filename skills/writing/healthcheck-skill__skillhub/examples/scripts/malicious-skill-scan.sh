#!/bin/bash
# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"

# Malicious Skill Scanner - 恶意技能扫描脚本
# 版本: v2.2.0
# 用途: 演示如何独立扫描已安装技能

set -e

echo "🦠 OpenClaw 恶意技能扫描器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "扫描时间: $(date)"
echo ""

# 已知恶意技能数据库
KNOWN_MALICIOUS_SKILLS=(
    "solana-wallet-tracker:窃取加密货币钱包:ClawHavoc"
    "phantom-wallet-monitor:窃取Phantom钱包:ClawHavoc"
    "wallet-tracker-pro:窃取钱包私钥:ClawHavoc"
    "youtube-summarize-pro:植入Atomic Stealer木马:ClawHavoc"
    "youtube-video-downloader:窃取浏览器数据:ClawHavoc"
    "polymarket-trader:窃取交易凭证:ClawHavoc"
    "bybit-trading:恶意代码执行:GitHub投毒"
    "linkedin-job-application:植入AuthTool木马:官方仓库投毒"
    "clawhub:仿冒域名投毒:ClawHavoc"
    "clawhubb:仿冒域名投毒:ClawHavoc"
    "clawhub1:仿冒域名投毒:ClawHavoc"
    "crypto-wallet-monitor:窃取加密货币:ClawHavoc"
    "openclaw-agent:恶意软件分发:GitHub投毒"
    "auth-tool:窃取认证信息:GitHub投毒"
)

# 可疑关键词
SUSPICIOUS_PATTERNS=(
    "curl.*\|.*bash"
    "curl.*\|.*sh"
    "wget.*\|.*bash"
    "wget.*\|.*sh"
    "base64.*decode.*exec"
    "atob.*exec"
    "nc -e"
    "ncat -e"
    "bash -i"
    "/dev/tcp/"
    "eval.*\$("
    "eval-safe-placeholder"
    "crypto.*wallet"
    "solana.*wallet"
    "phantom.*wallet"
    "steal.*key"
    "exfiltrate"
)

# 获取已安装技能列表
get_installed_skills() {
    local skills=()
    
    # 从openclaw命令获取
    if command -v openclaw &> /dev/null; then
        while IFS= read -r skill; do
            [ -n "$skill" ] && skills+=("$skill")
        done < <(openclaw skills list 2>/dev/null | grep -v "^Name" | awk '{print $1}' || true)
    fi
    
    # 从目录获取
    local skills_dir="${HOME}/.openclaw/skills"
    if [ -d "$skills_dir" ]; then
        for dir in "$skills_dir"/*/; do
            if [ -d "$dir" ]; then
                local skill_name=$(basename "$dir")
                if [[ ! " ${skills[@]} " =~ " ${skill_name} " ]]; then
                    skills+=("$skill_name")
                fi
            fi
        done
    fi
    
    echo "${skills[@]}"
}

# 检查技能是否在恶意列表中
check_malicious_list() {
    local skill_name="$1"
    
    for entry in "${KNOWN_MALICIOUS_SKILLS[@]}"; do
        local malicious_name=$(echo "$entry" | cut -d':' -f1)
        local risk=$(echo "$entry" | cut -d':' -f2)
        local campaign=$(echo "$entry" | cut -d':' -f3)
        
        if [[ "$skill_name" == *"$malicious_name"* ]] || [[ "$skill_name" == "$malicious_name" ]]; then
            echo "MALICIOUS:${risk}:${campaign}"
            return 0
        fi
    done
    
    echo "CLEAN"
    return 1
}

# 检查技能代码中的可疑模式
check_suspicious_patterns() {
    local skill_dir="$1"
    local skill_name=$(basename "$skill_dir")
    local found_patterns=()
    
    # 检查SKILL.md
    local skill_file="${skill_dir}/SKILL.md"
    if [ -f "$skill_file" ]; then
        for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
            if grep -riE "$pattern" "$skill_file" 2>/dev/null; then
                found_patterns+=("$pattern")
            fi
        done
    fi
    
    # 检查scripts目录
    local scripts_dir="${skill_dir}/scripts"
    if [ -d "$scripts_dir" ]; then
        for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
            if grep -riE "$pattern" "$scripts_dir" 2>/dev/null; then
                found_patterns+=("$pattern (in scripts)")
            fi
        done
    fi
    
    if [ ${#found_patterns[@]} -gt 0 ]; then
        echo "SUSPICIOUS:$(IFS=','; echo "${found_patterns[*]}")"
        return 0
    fi
    
    echo "CLEAN"
    return 1
}

# 主扫描逻辑
echo "【正在获取已安装技能列表...】"
INSTALLED_SKILLS=($(get_installed_skills))
TOTAL_COUNT=${#INSTALLED_SKILLS[@]}

echo "发现 ${TOTAL_COUNT} 个已安装技能"
echo ""

# 初始化计数器
MALICIOUS_COUNT=0
SUSPICIOUS_COUNT=0
CLEAN_COUNT=0

declare -a SCAN_RESULTS=()

# 扫描每个技能
echo "【开始扫描...】"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for skill in "${INSTALLED_SKILLS[@]}"; do
    echo ""
    echo "扫描: ${skill}"
    
    result=""
    risk_level="safe"
    details=""
    
    # 检查是否在恶意列表中
    malicious_check=$(check_malicious_list "$skill")
    if [ "$malicious_check" != "CLEAN" ]; then
        risk=$(echo "$malicious_check" | cut -d':' -f2)
        campaign=$(echo "$malicious_check" | cut -d':' -f3)
        
        echo "  🔴 [MALICIOUS] 发现已知恶意技能!"
        echo "     风险: ${risk}"
        echo "     来源: ${campaign}"
        echo "     建议: 立即删除!"
        
        MALICIOUS_COUNT=$((MALICIOUS_COUNT + 1))
        risk_level="malicious"
        details="Known malicious skill from ${campaign}: ${risk}"
        
        SCAN_RESULTS+=("{\"skill\":\"${skill}\",\"status\":\"malicious\",\"risk\":\"${risk}\",\"campaign\":\"${campaign}\"}")
        continue
    fi
    
    # 检查可疑代码模式
    skill_dir="${HOME}/.openclaw/skills/${skill}"
    if [ -d "$skill_dir" ]; then
        suspicious_check=$(check_suspicious_patterns "$skill_dir")
        if [ "$suspicious_check" != "CLEAN" ]; then
            patterns=$(echo "$suspicious_check" | cut -d':' -f2)
            
            echo "  ⚠️  [SUSPICIOUS] 发现可疑代码模式"
            echo "     模式: ${patterns}"
            echo "     建议: 人工审查"
            
            SUSPICIOUS_COUNT=$((SUSPICIOUS_COUNT + 1))
            risk_level="suspicious"
            details="Suspicious patterns detected: ${patterns}"
            
            SCAN_RESULTS+=("{\"skill\":\"${skill}\",\"status\":\"suspicious\",\"patterns\":\"${patterns}\"}")
            continue
        fi
    fi
    
    echo "  ✅ [CLEAN] 安全"
    CLEAN_COUNT=$((CLEAN_COUNT + 1))
    SCAN_RESULTS+=("{\"skill\":\"${skill}\",\"status\":\"clean\"}")
done

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 扫描结果总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "总技能数: ${TOTAL_COUNT}"
echo "🔴 恶意技能: ${MALICIOUS_COUNT}"
echo "⚠️  可疑技能: ${SUSPICIOUS_COUNT}"
echo "✅ 安全技能: ${CLEAN_COUNT}"
echo ""

if [ $MALICIOUS_COUNT -gt 0 ]; then
    echo "🚨 警告: 发现 ${MALICIOUS_COUNT} 个恶意技能!"
    echo "   请立即执行以下命令删除:"
    for result in "${SCAN_RESULTS[@]}"; do
        if [[ "$result" == *"malicious"* ]]; then
            local skill=$(echo "$result" | grep -o '"skill":"[^"]*"' | cut -d'"' -f4)
            echo "   openclaw skills remove ${skill}"
        fi
    done
fi

echo ""
echo "【JSON格式输出】"
echo "{"
echo "  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
echo "  \"total_scanned\": ${TOTAL_COUNT},"
echo "  \"malicious_count\": ${MALICIOUS_COUNT},"
echo "  \"suspicious_count\": ${SUSPICIOUS_COUNT},"
echo "  \"clean_count\": ${CLEAN_COUNT},"
echo "  \"results\": ["

first=true
for result in "${SCAN_RESULTS[@]}"; do
    if [ "$first" = true ]; then
        first=false
    else
        echo ","
    fi
    echo -n "    ${result}"
done

echo ""
echo "  ]"
echo "}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "扫描完成!"
