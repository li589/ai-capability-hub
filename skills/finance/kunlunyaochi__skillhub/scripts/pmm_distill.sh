#!/bin/bash
# ═══════════════════════════════════════════════════════════
# PMM 全自动蒸馏引擎 9.2.9 — 每个AI体均可一键执行
# 14层: 寻踪→织网→归藏→还原→鉴伪→合流→断矛→贯络→革故→追本→纳芥→封箓→系命→炼金→凝丹→通变→取舍
#
# ⚠️ 行为声明：
#   非 --dry-run 模式下，蒸馏引擎会自动：
#   1. 标记冗余记录为软删除（auto_dedup，基于标题前缀去重）
#   2. 标记已知过时记录为软删除（auto_resolve，基于硬编码模式匹配）
#   3. 写入蒸馏报告到 memory/pmm-distill-*.md
#   使用 --dry-run 可预览即将执行的操作，不产生实际变更。
# ═══════════════════════════════════════════════════════════

readonly VERSION="9.2.9"

# grep 无匹配返回 1 是正常行为，不用严格模式
USER_ID="2"
DRY_RUN=false

# 解析参数
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --user-id=*) USER_ID="${arg#*=}" ;;
    esac
done
# 工作区路径 — 按 user_id 映射（同服务器上两个AI体并存，按ID不按目录）
case "$USER_ID" in
    2) WORK_DIR="/root/.lightclaw/workspace" ;;    # 瑶池
    3) WORK_DIR="/root/.openclaw/workspace" ;;     # 昆仑
    *) 
       # 其他AI体：检测目录
       if [ -d "/root/.lightclaw/workspace" ]; then WORK_DIR="/root/.lightclaw/workspace"
       elif [ -d "/root/.openclaw/workspace" ]; then WORK_DIR="/root/.openclaw/workspace"
       else WORK_DIR="${HOME}/workspace"
       fi ;;
esac
MEMORY_FILE="${WORK_DIR}/MEMORY.md"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="${WORK_DIR}/memory/pmm-distill-${TIMESTAMP}.md"

G='\033[0;32m'; Y='\033[1;33m'; N='\033[0m'
log()  { echo -e "${G}[蒸馏]${N} $*"; }
warn() { echo -e "${Y}[警告]${N} $*"; }
step() { echo -e "\n${G}═══ $* ═══${N}"; }

# ─── 层1-4: 扫描 ───
scan_all() {
    step "层1-4: 寻踪→织网→入库→还原 扫描记忆"
    
    LOCAL_LINES=$(wc -l < "$MEMORY_FILE" 2>/dev/null || echo "0")
    LOCAL_KB=$(du -k "$MEMORY_FILE" 2>/dev/null | cut -f1 || echo "0")
    IRON_LAWS=$(grep -cE '^[0-9]+\. \*\*' "$MEMORY_FILE" 2>/dev/null || echo "0")
    HOOKS=$(grep -cE '^\| .+ \| [0-9]{4} \| .+ \|' "$MEMORY_FILE" 2>/dev/null || echo "0")
    echo "  本地: ${LOCAL_LINES}行/${LOCAL_KB}KB | 铁律${IRON_LAWS}条 | 钩子${HOOKS}条"
    
    cat > /tmp/pmm_scan.php << PHPEOF
<?php
require '/www/wwwroot/kunlunyaochi/config.php';
\$db = db(); \$tbl = getMemoriesTable(${USER_ID});
try {
    \$rows = \$db->query("SELECT domain,COUNT(*) as cnt,SUM(is_encrypted) as enc FROM \$tbl WHERE is_deleted=0 GROUP BY domain ORDER BY cnt DESC")->fetchAll();
    \$total = array_sum(array_column(\$rows,'cnt'));
    echo "  远程(user_id=${USER_ID}): \${total}条, ".count(\$rows)."域\\n";
    foreach (\$rows as \$r) {
        \$enc = \$r['enc'] > 0 ? "(加密\${r['enc']})" : "";
        echo "    \${r['domain']}: \${r['cnt']}\${enc}\\n";
    }
} catch(Exception \$e) { echo "  远程不可达\\n"; }
PHPEOF
    php /tmp/pmm_scan.php 2>/dev/null
    rm -f /tmp/pmm_scan.php
}

# ─── 层5: 辩伪 ───
verify_truth() {
    step "层5: 鉴伪 交叉验证"
    
    cat > /tmp/pmm_verify.php << 'PHPEOF'
<?php
require '/www/wwwroot/kunlunyaochi/config.php';
$db = db(); $tbl = getMemoriesTable(UID_PLACEHOLDER);
$stale = 0;

// 8767端口未标注下线
$rows = $db->query("SELECT id,title FROM $tbl WHERE is_deleted=0 AND (content LIKE '%8767%' OR title LIKE '%8767%') AND content NOT LIKE '%废弃%' AND content NOT LIKE '%下线%' AND content NOT LIKE '%07-24%'")->fetchAll();
foreach ($rows as $r) { echo "  ⚠️ ID={$r['id']}: 8767引用未标注下线\n"; $stale++; }

// Qwen声称可用
$rows = $db->query("SELECT id,title FROM $tbl WHERE is_deleted=0 AND (content LIKE '%Qwen%可用%' OR content LIKE '%使用 Qwen%') AND content NOT LIKE '%弃用%' AND content NOT LIKE '%移除%'")->fetchAll();
foreach ($rows as $r) { echo "  ⚠️ ID={$r['id']}: Qwen引用未标注已弃用\n"; $stale++; }

// yaochi-a2a.service 未标注下线
$rows = $db->query("SELECT id,title FROM $tbl WHERE is_deleted=0 AND content LIKE '%yaochi-a2a.service%' AND content NOT LIKE '%inactive%' AND content NOT LIKE '%下线%' AND content NOT LIKE '%合并%'")->fetchAll();
foreach ($rows as $r) { echo "  ⚠️ ID={$r['id']}: yaochi-a2a未标注下线\n"; $stale++; }

file_put_contents('/tmp/pmm_stale.txt', $stale);
PHPEOF
    sed -i "s/UID_PLACEHOLDER/${USER_ID}/" /tmp/pmm_verify.php
    php /tmp/pmm_verify.php 2>/dev/null
    
    local s=$(cat /tmp/pmm_stale.txt 2>/dev/null || echo "0")
    [ "$s" -eq 0 ] && echo "  ✅ 无矛盾" || warn "发现 ${s} 条矛盾"
    rm -f /tmp/pmm_verify.php /tmp/pmm_stale.txt
}

# ─── 层6: 去重 ───
auto_dedup() {
    step "层6: 归并 去重"
    
    if $DRY_RUN; then
        cat > /tmp/pmm_dedup.php << PHPEOF
<?php
require '/www/wwwroot/kunlunyaochi/config.php';
\$c = db()->query("SELECT COUNT(*) FROM ".getMemoriesTable(${USER_ID})." WHERE is_deleted=0 AND domain='general'")->fetchColumn();
echo "  general域: \$c 条 (dry-run不删除)\\n";
PHPEOF
        php /tmp/pmm_dedup.php 2>/dev/null
        rm -f /tmp/pmm_dedup.php
        return
    fi
    
    cat > /tmp/pmm_dedup.php << 'PHPEOF'
<?php
require '/www/wwwroot/kunlunyaochi/config.php';
$db = db(); $tbl = getMemoriesTable(UID_PLACEHOLDER);
$del = 0;
$groups = $db->query("SELECT SUBSTR(title,1,60) as grp, COUNT(*) as cnt FROM $tbl WHERE is_deleted=0 AND domain='general' GROUP BY grp HAVING cnt > 3")->fetchAll();
foreach ($groups as $g) {
    $ids = $db->query("SELECT id FROM $tbl WHERE is_deleted=0 AND domain='general' AND title LIKE '".addslashes($g['grp'])."%' ORDER BY created_at DESC LIMIT 999999 OFFSET 3")->fetchAll(PDO::FETCH_COLUMN);
    foreach ($ids as $id) { $db->query("UPDATE $tbl SET is_deleted=1 WHERE id=$id"); $del++; }
}
echo "  已清理 $del 条冗余\n";
PHPEOF
    sed -i "s/UID_PLACEHOLDER/${USER_ID}/" /tmp/pmm_dedup.php
    php /tmp/pmm_dedup.php 2>/dev/null
    rm -f /tmp/pmm_dedup.php
}

# ─── 层7-8: 去矛盾 ───
auto_resolve() {
    step "层7-8: 断矛+系脉 去矛盾建关联"
    $DRY_RUN && { echo "  dry-run跳过"; return; }
    
    cat > /tmp/pmm_resolve.php << 'PHPEOF'
<?php
require '/www/wwwroot/kunlunyaochi/config.php';
$db = db(); $tbl = getMemoriesTable(UID_PLACEHOLDER);
$del = 0;

// 模式1: 8767端点上线类记忆（已下线）
$ids = $db->query("SELECT id FROM $tbl WHERE is_deleted=0 AND (title LIKE '%8767%上线%' OR title LIKE '%JSON-RPC%上线%' OR title LIKE '%yaochi-a2a%端点%')")->fetchAll(PDO::FETCH_COLUMN);
foreach ($ids as $id) { $db->query("UPDATE $tbl SET is_deleted=1 WHERE id=$id"); $del++; echo "  标记 ID=$id (已下线端点)\n"; }

// 模式2: 早期分类体系v1（已被MEMORY.md覆盖）
$ids = $db->query("SELECT id,title FROM $tbl WHERE is_deleted=0 AND domain IN ('运维','技术') AND title LIKE '%分类体系%' AND created_at < '2026-07-20'")->fetchAll(PDO::FETCH_COLUMN);
foreach ($ids as $id) { $db->query("UPDATE $tbl SET is_deleted=1 WHERE id=$id"); $del++; echo "  标记 ID=$id (已被v2覆盖)\n"; }

echo $del;
PHPEOF
    sed -i "s/UID_PLACEHOLDER/${USER_ID}/" /tmp/pmm_resolve.php
    local r=$(php /tmp/pmm_resolve.php 2>/dev/null || echo "0")
    echo "  已解决 ${r} 条"
    rm -f /tmp/pmm_resolve.php
}

# ─── 层9-12: 提炼钩子 ───
auto_extract_hooks() {
    step "层9-12: 修订→追本→炼金→提纯 提炼钩子"
    
    local hook_count=$(grep -cE '^\| .+ \| [0-9]{4} \| .+ \|' "$MEMORY_FILE" 2>/dev/null || echo "0")
    echo "  蒸馏钩子: ${hook_count} 条"
    
    if $DRY_RUN; then
        grep -E '^\|.*\| *[0-9]+ *\|' "$MEMORY_FILE" 2>/dev/null | tail -5
        return
    fi
    
    # 验证钩子远程存在性
    cat > /tmp/pmm_hooks.php << 'PHPEOF'
<?php
require '/www/wwwroot/kunlunyaochi/config.php';
$db = db(); $tbl = getMemoriesTable(UID_PLACEHOLDER);
$hooks = file('MEMORY_PATH_PLACEHOLDER');
$exist = 0; $missing = 0;
foreach ($hooks as $line) {
    if (preg_match('/^\|\s*.+?\s*\|\s*(\d{4})\s*\|/', $line, $m)) {
        $id = (int)$m[1];
        $chk = $db->query("SELECT id FROM $tbl WHERE id=$id AND is_deleted=0")->fetchColumn();
        if ($chk) $exist++; else { echo "  ⚠️ ID=$id 远程不存在\n"; $missing++; }
    }
}
echo "  已验证: $exist 存在, $missing 缺失\n";
PHPEOF
    sed -i "s/UID_PLACEHOLDER/${USER_ID}/" /tmp/pmm_hooks.php
    sed -i "s|MEMORY_PATH_PLACEHOLDER|${MEMORY_FILE}|" /tmp/pmm_hooks.php
    php /tmp/pmm_hooks.php 2>/dev/null
    rm -f /tmp/pmm_hooks.php
}

# ─── 层13-14: 报告 ───
generate_report() {
    step "层13-14: 通变→取舍 生成报告"
    
    local remote_cnt=$(php -r "require '/www/wwwroot/kunlunyaochi/config.php'; echo db()->query('SELECT COUNT(*) FROM '.getMemoriesTable(${USER_ID}).' WHERE is_deleted=0')->fetchColumn();" 2>/dev/null || echo "?")
    
    cat > "$REPORT_FILE" << EOF
# PMM 全自动蒸馏报告

**AI体:** user_id=${USER_ID}  
**时间:** $(date '+%Y-%m-%d %H:%M:%S')  
**模式:** $($DRY_RUN && echo '预览' || echo '执行')

## 蒸馏统计

| 指标 | 值 |
|------|-----|
| 本地 MEMORY.md | ${LOCAL_LINES:-?}行/${LOCAL_KB:-?}KB |
| 铁律 | ${IRON_LAWS:-?}条 |
| 蒸馏钩子 | ${HOOKS:-?}条 |
| 远程记忆 | ${remote_cnt}条 |

## 本次操作

- 交叉验证：已完成
- 冗余清理：$($DRY_RUN && echo '跳过' || echo '已完成')
- 矛盾解决：$($DRY_RUN && echo '跳过' || echo '已完成')
- 钩子验证：已完成
EOF
    
    log "报告: $REPORT_FILE"
}

# ═══════════════════════════════════════════
main() {
    echo ""
    echo "══════════════════════════════════════"
    echo "  PMM 14层全自动蒸馏引擎 v2.0"
    echo "  AI体: user_id=${USER_ID}"
    $DRY_RUN && echo "  模式: 预览 (--dry-run)"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════"

    # 非 dry-run 模式：二次确认（防止误执行写库操作）
    if ! $DRY_RUN; then
        echo ""
        echo -e "${Y}⚠️  蒸馏引擎将执行以下操作：${N}"
        echo "  1. 扫描远程记忆并生成报告"
        echo "  2. 标记 general 域冗余记录为软删除（去重）"
        echo "  3. 标记已知过时记录为软删除（自动消解）"
        echo "  4. 验证钩子完整性并写入蒸馏报告"
        echo ""
        read -r -p "确认执行？[y/N] " confirm
        case "$confirm" in
            [yY]|[yY][eE][sS]) echo "  继续执行..." ;;
            *) echo "  已取消。使用 --dry-run 可预览即将执行的操作。"; exit 0 ;;
        esac
    fi

    scan_all
    verify_truth
    auto_dedup
    auto_resolve
    distill_with_llm    # 🆕 层9-12: LLM蒸馏 (AI体用自己的DeepSeek Key)
    auto_extract_hooks
    generate_report
    
    echo ""
    $DRY_RUN && echo "  🔍 预览完成。去掉 --dry-run 执行实际蒸馏。" || echo "  ✅ 全自动蒸馏完成。"
    echo ""
}

# ═══════════════════════════════════════════════════════════
# 层9-12: LLM蒸馏 (2026-08-12 新增)
# AI体用自己的 DeepSeek Key 调平台候选对 API → 逐对判定 → 回传结果
# ═══════════════════════════════════════════════════════════
distill_with_llm() {
    step "层9-12: LLM蒸馏 (自付Token)"
    
    $DRY_RUN && { echo "  dry-run跳过LLM蒸馏"; return; }
    
    local api_key=""
    local platform_url="${KYLC_PLATFORM_URL:-https://kunlunyaochi.com}"
    
    # ─── Key 来源优先级: 环境变量 > OpenClaw 框架
    if [ -n "${PMM_DEEPSEEK_KEY:-}" ]; then
        api_key="$PMM_DEEPSEEK_KEY"
    elif [ -n "${DEEPSEEK_API_KEY:-}" ]; then
        api_key="$DEEPSEEK_API_KEY"
    fi
    
    if [ -z "$api_key" ]; then
        echo "  跳过: 未找到 DeepSeek API Key (设置 DEEPSEEK_API_KEY)"
        return
    fi
    
    # ─── 确定平台认证头
    local auth_header=""
    if [ -n "${KYLC_API_KEY:-}" ]; then
        auth_header="X-Kunlun-Key: ${KYLC_API_KEY}"
    else
        # 尝试从 IDENTITY.md 提取昆仑令
        if [ -f "${WORK_DIR}/IDENTITY.md" ]; then
            local talisman=$(grep -oP 'KLYC-PMM-[a-f0-9]{32}' "${WORK_DIR}/IDENTITY.md" 2>/dev/null | head -1)
            [ -n "$talisman" ] && auth_header="X-Kunlun-Key: ${talisman}"
        fi
    fi
    
    if [ -z "$auth_header" ]; then
        echo "  跳过: 未找到平台认证凭据"
        return
    fi
    
    # ─── ① 请求候选对
    local task_resp=$(curl -s --max-time 10 -X POST "${platform_url}/api/klyc_distill_candidates.php"         -H "${auth_header}"         -H "Content-Type: application/json"         -d '{"limit":20}' 2>/dev/null)
    
    local task_id=$(echo "$task_resp" | jq -r '.task_id // empty' 2>/dev/null)
    if [ -z "$task_id" ]; then
        local err=$(echo "$task_resp" | jq -r '.error // "请求失败"' 2>/dev/null)
        echo "  候选对API失败: ${err}"
        return
    fi
    echo "  task: ${task_id}"
    
    # ─── ② 轮询结果（最多3次，间隔3秒）
    local candidates_json=""
    for i in 1 2 3; do
        sleep 3
        local status_resp=$(curl -s --max-time 10 "${platform_url}/api/klyc_distill_candidates_status.php?task_id=${task_id}"             -H "${auth_header}" 2>/dev/null)
        local status=$(echo "$status_resp" | jq -r '.status // "queued"' 2>/dev/null)
        
        if [ "$status" = "done" ]; then
            candidates_json="$status_resp"
            break
        elif [ "$status" = "failed" ]; then
            echo "  候选对生成失败: $(echo $status_resp | jq -r '.error // "unknown"' 2>/dev/null)"
            return
        fi
    done
    
    if [ -z "$candidates_json" ]; then
        echo "  候选对未就绪（超时），下次心跳再试"
        return
    fi
    
    local total=$(echo "$candidates_json" | jq -r '.total // 0')
    echo "  候选对: ${total}"
    [ "$total" -eq 0 ] && return
    
    # ─── ③ 逐对调 DeepSeek 判定
    local tmpfile="/tmp/pmm_distill_results_$$.json"
    echo "[" > "$tmpfile"
    local processed=0
    
    echo "$candidates_json" | jq -c '.candidates[]' 2>/dev/null | while read pair; do
        local pair_id=$(echo "$pair" | jq -r '.pair_id')
        local keep_id=$(echo "$pair" | jq -r '.memory_a.id')
        local remove_id=$(echo "$pair" | jq -r '.memory_b.id')
        local title_a=$(echo "$pair" | jq -r '.memory_a.title' | sed 's/"/\"/g')
        local title_b=$(echo "$pair" | jq -r '.memory_b.title' | sed 's/"/\"/g')
        local content_a=$(echo "$pair" | jq -r '.memory_a.content' | sed 's/"/\"/g')
        local content_b=$(echo "$pair" | jq -r '.memory_b.content' | sed 's/"/\"/g')
        
        # ─── 拼蒸馏 prompt（复用 PHP 版模板）
        local prompt_data=$(jq -n --arg ta "$title_a" --arg tb "$title_b" --arg ca "$content_a" --arg cb "$content_b" '{
            model: "deepseek-v4-pro",
            messages: [
                {role: "system", content: "你是记忆蒸馏引擎。判断两条AI体记忆的关系。只输出JSON。"},
                {role: "user", content: "判断两条AI体记忆的关系:
A(\($ta)): \($ca)
B(\($tb)): \($cb)
输出JSON: {"rel":"identical|overlap|related|unrelated","conf":0.XX,"merged":"合并文本(仅identical/overlap时)","reason":"理由(50字内)"}"}
            ],
            temperature: 0.1,
            max_tokens: 500
        }')
        
        local llm_resp=$(curl -s --max-time 30 -X POST "https://api.deepseek.com/v1/chat/completions"             -H "Authorization: Bearer ${api_key}"             -H "Content-Type: application/json"             -d "$prompt_data" 2>/dev/null)
        
        local llm_content=$(echo "$llm_resp" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
        if [ -z "$llm_content" ]; then
            continue
        fi
        
        # 解析 JSON
        local llm_json=$(echo "$llm_content" | grep -oP '\{[^}]*\}' | head -1)
        [ -z "$llm_json" ] && continue
        
        local rel=$(echo "$llm_json" | jq -r '.rel // "related"' 2>/dev/null)
        local conf=$(echo "$llm_json" | jq -r '.conf // 0' 2>/dev/null)
        local merged=$(echo "$llm_json" | jq -r '.merged // ""' 2>/dev/null)
        local reason=$(echo "$llm_json" | jq -r '.reason // ""' 2>/dev/null)
        
        # 构建结果条目 (用 jq 避免 bash 转义问题)
        local entry=$(jq -n             --arg pid "$pair_id"             --argjson kid "$keep_id"             --argjson rid "$remove_id"             --arg rel "$rel"             --argjson conf "$conf"             --arg merged "$merged"             --arg reason "$reason"             '{pair_id: $pid, keep_id: $kid, remove_id: $rid, rel: $rel, conf: $conf, merged: $merged, reason: $reason}')
        
        # 追加到临时文件
        if [ $processed -gt 0 ]; then
            echo "," >> "$tmpfile"
        fi
        echo "$entry" >> "$tmpfile"
        processed=$((processed + 1))
        [ $processed -ge 20 ] && break
    done
    
    echo "]" >> "$tmpfile"
    
    # ─── ④ 回传结果
    if [ $processed -gt 0 ] && [ -f "$tmpfile" ]; then
        local final_results=$(cat "$tmpfile")
        rm -f "$tmpfile"
        
        local result_resp=$(curl -s --max-time 10 -X POST "${platform_url}/api/klyc_distill_result.php"             -H "${auth_header}"             -H "Content-Type: application/json"             -d "{"results":${final_results}}" 2>/dev/null)
        
        local merged_count=$(echo "$result_resp" | jq -r '.merged // 0' 2>/dev/null)
        local conflict_count=$(echo "$result_resp" | jq -r '.conflicts // 0' 2>/dev/null)
        echo "  LLM蒸馏完成: 判定${processed}对, 合并${merged_count}, 冲突${conflict_count}"
    fi
}

main "$@"
