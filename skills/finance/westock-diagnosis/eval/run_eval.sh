#!/bin/bash
# 持仓诊断端到端评测脚本
# 对每个 case 清除 session 后开新 openclaw session，保存 agent 输出、脚本输出和轨迹数据
#
# Session 隔离策略：
#   --session-id 不会创建新 session，所有调用都路由到 agent:main:main
#   因此在每个 case 运行前，删除该 session 的 JSONL 文件和 sessions.json 中的条目
#   迫使 gateway 在下次 agent 调用时创建全新的 session

set -euo pipefail

EVAL_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$(cd "$EVAL_DIR/../scripts" && pwd)/diagnose.py"
SESSION_DIR="/projects/.openclaw/agents/main/sessions"
SESSION_STORE="$SESSION_DIR/sessions.json"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
RESULT_DIR="$EVAL_DIR/results/$TIMESTAMP"

mkdir -p "$RESULT_DIR"

echo "=== 持仓诊断评测 $TIMESTAMP ==="
echo ""

# Backup original session state
BACKUP_DIR="$RESULT_DIR/_session_backup"
mkdir -p "$BACKUP_DIR"
cp "$SESSION_STORE" "$BACKUP_DIR/sessions.json.orig" 2>/dev/null || true

# Function: reset main session to force a new one on next agent call
reset_main_session() {
  python3 -c "
import json, os, glob

store_path = '$SESSION_STORE'
session_dir = '$SESSION_DIR'

# Read sessions.json
with open(store_path) as f:
    store = json.load(f)

main_key = 'agent:main:main'
if main_key in store:
    old_id = store[main_key].get('sessionId', '')
    if old_id:
        jsonl = os.path.join(session_dir, f'{old_id}.jsonl')
        if os.path.exists(jsonl):
            os.remove(jsonl)
    del store[main_key]
    with open(store_path, 'w') as f:
        json.dump(store, f, indent=2)
"
}

# Case config: filename | cash | description
CASES=(
  "case_01_balanced.json|100000|均衡分散组合"
  "case_02_concentrated.json|50000|单只重仓"
  "case_03_single_sector.json|50000|全科技股"
  "case_04_deep_loss.json|30000|深度套牢"
  "case_05_big_profit.json|50000|大幅盈利"
  "case_06_no_cost.json|50000|无成本价"
  "case_07_market_value_only.json|50000|只有市值和盈亏"
  "case_08_mixed_market.json|80000|A股+港股混合"
  "case_09_no_code.json|50000|只有名称没有代码"
  "case_10_full_position.json|0|满仓无现金"
)

SUMMARY="# 评测结果汇总 ($TIMESTAMP)\n\n"
SUMMARY+="| Case | 场景 | 脚本 | Agent | 调了脚本？ | 诊断标记 |\n"
SUMMARY+="|------|------|------|-------|-----------|----------|\n"

PASS=0
FAIL=0

for entry in "${CASES[@]}"; do
  IFS='|' read -r FILE CASH DESC <<< "$entry"
  CASE_NAME="${FILE%.json}"
  CASE_DIR="$RESULT_DIR/$CASE_NAME"
  mkdir -p "$CASE_DIR"

  echo "--- $CASE_NAME: $DESC ---"

  # 1. 脚本层测试
  echo "  [1/3] 运行 diagnose.py ..."
  SCRIPT_STATUS="PASS"
  if [ "$CASH" = "0" ]; then
    CASH_ARG="--cash 0"
  else
    CASH_ARG="--cash $CASH"
  fi

  python3 "$SCRIPT_PATH" --portfolio-file "$EVAL_DIR/$FILE" $CASH_ARG \
    > "$CASE_DIR/script_output.json" 2>"$CASE_DIR/script_stderr.log" || SCRIPT_STATUS="FAIL"

  # Extract diagnostics summary
  DIAG_SUMMARY=$(python3 -c "
import json,sys
try:
    d=json.load(open('$CASE_DIR/script_output.json'))
    if 'error' in d:
        print('ERROR: '+d['error'])
    else:
        diag=d.get('diagnostics',{})
        parts=[]
        for k,v in diag.items():
            if k.endswith('_status'):
                icon={'green':'🟢','yellow':'🟡','red':'🔴','unknown':'⚪'}.get(v,'?')
                parts.append(k.replace('_status','')+icon)
        print(' '.join(parts))
except Exception as e:
    print('PARSE_ERROR')
" 2>/dev/null || echo "PARSE_ERROR")

  if [ "$SCRIPT_STATUS" = "FAIL" ]; then
    echo "  [1/3] 脚本失败"
    FAIL=$((FAIL+1))
  else
    echo "  [1/3] 脚本成功: $DIAG_SUMMARY"
  fi

  # 2. 端到端测试（openclaw agent）
  # 清除 main session，确保 agent 在全新上下文中运行
  echo "  [2/3] 重置 session 并运行 openclaw agent ..."
  reset_main_session

  PORTFOLIO_JSON=$(cat "$EVAL_DIR/$FILE")

  # Construct message: simulate user providing portfolio data as text
  MSG="请帮我诊断以下持仓（JSON格式）：\n$PORTFOLIO_JSON\n可用现金：$CASH 元"

  AGENT_STATUS="PASS"
  AGENT_OUTPUT=$(openclaw agent \
    --agent main \
    --message "$MSG" \
    --timeout 600 \
    --json 2>/dev/null) || AGENT_STATUS="FAIL"

  # Save agent output
  echo "$AGENT_OUTPUT" > "$CASE_DIR/agent_raw.json"

  # Extract text reply
  python3 -c "
import json,sys
try:
    d=json.loads(sys.stdin.read())
    payloads=d.get('result',{}).get('payloads',[])
    for p in payloads:
        if p.get('text'):
            print(p['text'])
except:
    print('PARSE_ERROR')
" <<< "$AGENT_OUTPUT" > "$CASE_DIR/agent_output.txt" 2>/dev/null

  # 3. Copy session trace (use real sessionId from agent output)
  echo "  [3/3] 保存轨迹数据 ..."
  REAL_SESSION_ID=$(python3 -c "
import json
try:
    d=json.load(open('$CASE_DIR/agent_raw.json'))
    print(d.get('result',{}).get('meta',{}).get('agentMeta',{}).get('sessionId',''))
except:
    print('')
" 2>/dev/null)

  CALLED_SCRIPT="?"
  if [ -n "$REAL_SESSION_ID" ]; then
    TRACE_FILE="$SESSION_DIR/${REAL_SESSION_ID}.jsonl"
    if [ -f "$TRACE_FILE" ]; then
      cp "$TRACE_FILE" "$CASE_DIR/session_trace.jsonl"
      if grep -q "diagnose.py" "$CASE_DIR/session_trace.jsonl" 2>/dev/null; then
        CALLED_SCRIPT="✅"
      else
        CALLED_SCRIPT="❌"
      fi
      LINES=$(wc -l < "$CASE_DIR/session_trace.jsonl")
      echo "  轨迹已保存: ${REAL_SESSION_ID}.jsonl ($LINES 行), 调用脚本: $CALLED_SCRIPT"
    else
      echo "  轨迹文件未找到: $TRACE_FILE"
    fi
  else
    echo "  无法从 agent 输出中提取 sessionId"
  fi

  if [ "$AGENT_STATUS" = "FAIL" ]; then
    echo "  [2/3] Agent 失败或超时"
    FAIL=$((FAIL+1))
  else
    echo "  [2/3] Agent 成功"
    PASS=$((PASS+1))
  fi

  # Add to summary
  SUMMARY+="| $CASE_NAME | $DESC | $SCRIPT_STATUS | $AGENT_STATUS | $CALLED_SCRIPT | $DIAG_SUMMARY |\n"
  echo ""
done

# Restore original session state (optional, comment out if you want to keep the last session)
# cp "$BACKUP_DIR/sessions.json.orig" "$SESSION_STORE"

# Write summary
echo -e "$SUMMARY" > "$RESULT_DIR/summary.md"

echo "=== 评测完成 ==="
echo "通过: $PASS / ${#CASES[@]}"
echo "失败: $FAIL / ${#CASES[@]}"
echo "结果目录: $RESULT_DIR"
echo "汇总报告: $RESULT_DIR/summary.md"
