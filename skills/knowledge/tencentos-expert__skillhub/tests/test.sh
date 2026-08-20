#!/bin/bash
#
# TencentOS Expert Skill — 统一测试脚本
# 验证整合后的 Skill 结构完整性
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "${SCRIPT_DIR}")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "${GREEN}  ✓ $1${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}  ✗ $1${NC}"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; WARN=$((WARN+1)); }

echo "=========================================="
echo " TencentOS Expert Skill — 完整性测试"
echo "=========================================="

# ==========================================
# 测试 1：核心文件存在性
# ==========================================
echo ""
echo -e "${BLUE}[1] 核心文件检查${NC}"

for file in "SKILL.md" "skill.yaml"; do
    if [[ -f "${SKILL_DIR}/${file}" ]]; then
        pass "${file} 存在"
    else
        fail "${file} 不存在"
    fi
done

# ==========================================
# 测试 2：skill.yaml 字段验证
# ==========================================
echo ""
echo -e "${BLUE}[2] skill.yaml 验证${NC}"

for field in "name:" "display_name:" "version:" "category:" "description:"; do
    if grep -q "^${field}" "${SKILL_DIR}/skill.yaml" 2>/dev/null; then
        pass "字段 ${field} 存在"
    else
        fail "缺少字段: ${field}"
    fi
done

# 2.1 — yaml 语法可解析（python3 PyYAML 优先，否则降级到 grep 校验）
if python3 -c "import yaml" 2>/dev/null; then
    if python3 -c "import yaml,sys; yaml.safe_load(open('${SKILL_DIR}/skill.yaml'))" 2>/dev/null; then
        pass "skill.yaml 语法可被 PyYAML 解析"
    else
        fail "skill.yaml 语法错误（PyYAML 解析失败）"
    fi
else
    warn "未安装 PyYAML，跳过语法解析检查"
fi

# 2.2 — capabilities 段：≥24 项 + 必填字段齐全
# 注：id 字段是 list item 首字段（"  - id:"），单独通过 CAP_COUNT 验证；
#     其余字段缩进 4 空格（"    name:"），用 EXPECTED_CAP_FIELDS 验证
EXPECTED_CAP_FIELDS=("name:" "domain:" "mode:" "requires_confirmation:" "primary_reference:")
if grep -q "^capabilities:" "${SKILL_DIR}/skill.yaml"; then
    pass "skill.yaml 含 capabilities 段"
    CAP_COUNT=$(grep -cE '^  - id:' "${SKILL_DIR}/skill.yaml")
    if [[ "$CAP_COUNT" -ge 24 ]]; then
        pass "capabilities 包含 ${CAP_COUNT} 项（≥24）"
    else
        fail "capabilities 仅 ${CAP_COUNT} 项（期望 ≥24）"
    fi
    for f in "${EXPECTED_CAP_FIELDS[@]}"; do
        # 至少应该出现 ≥24 次（每个 capability 一次）
        FIELD_COUNT=$(grep -cE "^    ${f}" "${SKILL_DIR}/skill.yaml")
        if [[ "$FIELD_COUNT" -ge 24 ]]; then
            pass "capabilities 必填字段 ${f}（${FIELD_COUNT} 次出现）"
        else
            fail "capabilities 字段 ${f} 仅 ${FIELD_COUNT} 次（期望 ≥24）"
        fi
    done
else
    fail "skill.yaml 缺少 capabilities 段"
fi

# 2.3 — forbidden_commands / credentials_policy / retry_policy 三个治理段
for sec in "forbidden_commands:" "credentials_policy:" "retry_policy:" "cloud_api_fallback:"; do
    if grep -q "^${sec}" "${SKILL_DIR}/skill.yaml"; then
        pass "治理段 ${sec} 存在"
    else
        fail "缺少治理段 ${sec}"
    fi
done

# 2.4 — capabilities 引用的 primary_reference 文件全部存在
MISSING_PRIMARY=0
while read -r ref; do
    [[ -z "$ref" ]] && continue
    if [[ ! -f "${SKILL_DIR}/${ref}" ]]; then
        fail "primary_reference 文件缺失: ${ref}"
        MISSING_PRIMARY=$((MISSING_PRIMARY+1))
    fi
done < <(grep -E '^    primary_reference:' "${SKILL_DIR}/skill.yaml" | awk '{print $2}')
if [[ "$MISSING_PRIMARY" -eq 0 ]]; then
    pass "所有 primary_reference 文件均存在"
fi


# ==========================================
# 测试 3：SKILL.md 内容验证
# ==========================================
echo ""
echo -e "${BLUE}[3] SKILL.md 内容验证${NC}"

if [[ -s "${SKILL_DIR}/SKILL.md" ]]; then
    pass "SKILL.md 非空"
else
    fail "SKILL.md 为空"
fi

# 检查是否包含能力索引表
if grep -q "能力索引" "${SKILL_DIR}/SKILL.md"; then
    pass "包含能力索引"
else
    fail "缺少能力索引"
fi

# 检查 24 项能力覆盖（SKILL.md 重构后索引移到 guides/capability-index.md）
INDEX_FILE="${SKILL_DIR}/guides/capability-index.md"
if [[ -f "$INDEX_FILE" ]]; then
    CAPABILITY_COUNT=$(grep -cE '^\| `[a-z]' "$INDEX_FILE" 2>/dev/null || echo 0)
    if [[ "$CAPABILITY_COUNT" -ge 24 ]]; then
        pass "能力索引（guides/capability-index.md）包含 ${CAPABILITY_COUNT} 项（≥24）"
    else
        warn "能力索引仅 ${CAPABILITY_COUNT} 项（期望 ≥24）"
    fi
else
    warn "未找到 guides/capability-index.md"
fi

# 检查安全原则
if grep -q "安全" "${SKILL_DIR}/SKILL.md"; then
    pass "包含安全原则"
else
    warn "建议添加安全原则"
fi

# ==========================================
# 测试 4：references 目录验证
# ==========================================
echo ""
echo -e "${BLUE}[4] references 目录验证${NC}"

if [[ -d "${SKILL_DIR}/references" ]]; then
    REF_COUNT=$(find "${SKILL_DIR}/references" -name "*.md" -type f | wc -l | tr -d ' ')
    pass "references/ 目录存在，包含 ${REF_COUNT} 个文件"
else
    fail "references/ 目录不存在"
fi

# 检查 24 个核心模块的 reference 文件（带子目录路径）
EXPECTED_REFS=(
    "disk/disk-space.md"
    "disk/disk-partition.md"
    "disk/disk-filesystem.md"
    "disk/disk-lvm.md"
    "disk/disk-health.md"
    "network/network-check.md"
    "network/network-packet-loss.md"
    "network/network-latency.md"
    "performance/cpu-flamegraph.md"
    "performance/syscall-hotspot.md"
    "performance/file-io-trace.md"
    "performance/fs-latency.md"
    "performance/irq-balance.md"
    "performance/sched-latency.md"
    "memory/oom-killer.md"
    "memory/memory-leak.md"
    "system/system-log.md"
    "system/service-status.md"
    "system/time-sync.md"
    "system/package-version.md"
    "system/repo-source.md"
    "security/security-baseline.md"
    "security/tencentos-cve-query.md"
    "docs/tencentos-docs.md"
    "recovery/kdump-check.md"
)

MISSING_REFS=()
for ref in "${EXPECTED_REFS[@]}"; do
    if [[ -f "${SKILL_DIR}/references/${ref}" ]]; then
        pass "references/${ref}"
    else
        fail "缺少 references/${ref}"
        MISSING_REFS+=("$ref")
    fi
done

# 检查补充 reference 文件（带子目录路径）
SUPPLEMENTARY_REFS=(
    "_common/common-instructions.md"
    "performance/performance-common.md"
    "performance/cpu-flamegraph-examples.md"
    "performance/cpu-flamegraph-perf.md"
    "performance/flamegraph-install.md"
    "performance/irq-balance-examples.md"
    "performance/irq-balance-perf.md"
    "network/network-nettrace.md"
    "network/network-faq-latency.md"
    "network/network-faq-packet-loss.md"
    "memory/oom-kernel-patterns.md"
    "memory/oom-metrics-guide.md"
    "memory/memory-leak-indicators.md"
    "security/security-checklist.md"
)

echo ""
echo -e "${BLUE}[4b] 补充 reference 文件${NC}"
for ref in "${SUPPLEMENTARY_REFS[@]}"; do
    if [[ -f "${SKILL_DIR}/references/${ref}" ]]; then
        pass "references/${ref}"
    else
        warn "缺少补充文件 references/${ref}"
    fi
done

# ==========================================
# 测试 5：scripts 目录验证
# ==========================================
echo ""
echo -e "${BLUE}[5] scripts 目录验证${NC}"

if [[ -d "${SKILL_DIR}/scripts" ]]; then
    SCRIPT_COUNT=$(find "${SKILL_DIR}/scripts" -type f ! -name '.gitkeep' | wc -l | tr -d ' ')
    pass "scripts/ 目录存在，包含 ${SCRIPT_COUNT} 个文件"
else
    fail "scripts/ 目录不存在"
fi

EXPECTED_SCRIPTS=(
    "common.sh"
    "output.sh"
    "collect_and_analyze.sh"
    "collect_memory_leak.sh"
    "parse_memory_leak.py"
    "parse_oom_events.py"
    "file-io-trace.sh"
    "fs-latency-collect.sh"
    "install-deps.sh"
    "network-latency-monitor.sh"
    "sched-latency-monitor.sh"
    "tos_security_harden.sh"
    "cve_xml_server.py"
)

for script in "${EXPECTED_SCRIPTS[@]}"; do
    if [[ -f "${SKILL_DIR}/scripts/${script}" ]]; then
        pass "scripts/${script}"
    else
        fail "缺少 scripts/${script}"
    fi
done

# ==========================================
# 测试 6：Shell 脚本语法检查
# ==========================================
echo ""
echo -e "${BLUE}[6] Shell 脚本语法检查${NC}"

for script in "${SKILL_DIR}"/scripts/*.sh; do
    if [[ -f "$script" ]]; then
        if bash -n "$script" 2>/dev/null; then
            pass "语法正确: $(basename "$script")"
        else
            fail "语法错误: $(basename "$script")"
        fi
    fi
done

# ==========================================
# 测试 7：Python 脚本语法检查
# ==========================================
echo ""
echo -e "${BLUE}[7] Python 脚本语法检查${NC}"

for script in "${SKILL_DIR}"/scripts/*.py; do
    if [[ -f "$script" ]]; then
        if python3 -c "import py_compile; py_compile.compile('$script', doraise=True)" 2>/dev/null; then
            pass "语法正确: $(basename "$script")"
        else
            fail "语法错误: $(basename "$script")"
        fi
    fi
done

# ==========================================
# 测试 8：SKILL.md 与 guides/ 中引用的 references 文件是否存在
# ==========================================
echo ""
echo -e "${BLUE}[8] SKILL.md / guides/ 引用完整性${NC}"

# 扫描 SKILL.md 与所有 guides/*.md（重构后引用主要在 guides/ 中）
# 正则匹配 references/<subdir>/<file>.md（含子目录路径）
REFERENCED_FILES=$(grep -hoE 'references/[a-z_][a-z0-9_-]*/[a-z][a-z0-9_-]*\.md' \
    "${SKILL_DIR}/SKILL.md" "${SKILL_DIR}"/guides/*.md 2>/dev/null | sort -u)
if [[ -n "$REFERENCED_FILES" ]]; then
    while IFS= read -r ref; do
        if [[ -f "${SKILL_DIR}/${ref}" ]]; then
            pass "引用存在: ${ref}"
        else
            fail "引用缺失: ${ref}"
        fi
    done <<< "$REFERENCED_FILES"
else
    warn "SKILL.md / guides/ 中未发现 references/ 引用"
fi

# ==========================================
# 测试 9：总体大小检查
# ==========================================
echo ""
echo -e "${BLUE}[9] 大小与上下文控制${NC}"

SKILL_LINES=$(wc -l < "${SKILL_DIR}/SKILL.md" | tr -d ' ')
TOTAL_REF_LINES=$(find "${SKILL_DIR}/references" -name '*.md' -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "${SKILL_DIR}" | awk '{print $1}')

echo "  SKILL.md（初始加载）: ${SKILL_LINES} 行"
echo "  references/ 总行数: ${TOTAL_REF_LINES} 行"
echo "  整体目录大小: ${TOTAL_SIZE}"

if [[ "$SKILL_LINES" -le 300 ]]; then
    pass "SKILL.md 行数 ≤ 300（渐进式披露友好）"
else
    warn "SKILL.md 行数 ${SKILL_LINES} > 300，初始加载可能偏大"
fi

# ==========================================
# 汇总
# ==========================================
echo ""
echo "=========================================="
echo " 测试汇总"
echo "=========================================="
echo -e "  ${GREEN}通过: ${PASS}${NC}"
echo -e "  ${RED}失败: ${FAIL}${NC}"
echo -e "  ${YELLOW}警告: ${WARN}${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}✓ 所有必要检查通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 ${FAIL} 项必要检查失败，请修复后重试${NC}"
    exit 1
fi
