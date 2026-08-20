> 🔴 元规则：禁止伪造结果 | 禁止连段执行(本段结束必须⏸️) | 禁止抛选择题
> 📋 来源：SKILL.md 段落5 | 版本 V4.15.22
> 🔴🔴🔴 resume后第一步必须检查TP文件完整性：若actual < expected - 3，须先执行 p6_verify_files 确认缺失列表，再执行 p6_merge。**禁止跳过验证直接merge。**

## 🔴🔴🔴 P6 第一铁律：禁止子代理/并行（违反即终止段落，强制 restart_from P6）

**你当前在主会话中执行P6。主会话 === 你本人。你不是调度者，你是执行者。**

| 禁止行为 | 后果 |
|---------|------|
| ⛔ 使用 sessions_spawn 创建子代理 | 立即终止，p6_tp_list 检测到后标记 P6_CORRUPTED，必须 restart |
| ⛔ 使用 subagents 工具分发 P6 任务 | 同上 |
| ⛔ 说"太慢了用子代理并行" | 同上 — 慢不是理由，质量优先于速度 |
| ⛔ 以任何形式把 p6_generate_one 分派给其他 session | 同上 |

**正确做法：你，且只有你，逐条阅读 prompt → 手写生成 JSON → p6_generate_one --save。**

---

## 前置依赖
- 段落4已完成：P3+P4+P5全部通过
- Gate: P5 gate pass必须存在
- P6使用**逐条生成流程**，Agent作为LLM每条独立生成

---

**🔴 核心约束:**
- ⛔ **禁止抛选择题**：任何失败后自动处理
- ⛔ **禁止子Agent执行P6**：代码层已检测，子Agent直接exit
- ⛔ **禁止跳过p6_generate_one**：每条必须走 generate_one → Agent生成 → generate_one --save
- ⛔ **禁止中途停止**：必须执行完全部TP后才 p6_merge
- ⛔ **禁止手写脚本绕过流程**：禁止直接写 tp_*.json 文件
- **⛔ 禁止 Agent 自行插入 sleep（V4.15.2）**：TP 循环中禁止在任何位置插入 sleep/wait/delay。orchestrator 已内置速率控制。Agent 插入 sleep 是多余行为，拖慢流程且绕过代码层速率逻辑。违规即视为违反元规则第1条。

**🚨 P6 三大红线:**

| # | 红线 | 正确做法 |
|---|------|----------|
| ⓵ | **禁止子Agent执行P6** | 主会话直接执行 |
| ⓶ | **禁止跳过LLM prompt直接套模板** | 必须走 p6_tp_list → p6_generate_one → **Agent完整阅读prompt并生成JSON** → p6_generate_one --save |
| ⓷ | **禁止手工forge gate文件** | gate只能由p6_merge自动生成，手工伪造会被HMAC验签拒绝 |

---

**🔴 段间验证:**
```
exec: python3 "$ORCH" --action status
```
确认P5的gate pass存在。

---

## 🔴 前置动作 — P6 预检清单（逐项检查，全部打勾后才开始逐条生成）V4.12.7

□ 1. 读取P6 prompt规则:
   ```
   read prompts/P6_testcase_generation.md
   ```
   → 理解步骤具体性要求、禁止词清单、期望结果量化规则

□ 2. 读取P5测试点数据:
   ```
   read {DATA_DIR}/p5_output.json
   ```
   → 提取每个TP的description/related_rules/ui_elements等结构化信息

□ 3. 确认 --agent-output 参数的正确用法:
   ⛔ 禁止：传入成品用例JSON（如模板占位符"进入功能页面执行测试点"）
   ✅ 正确：让Agent作为LLM阅读prompt后生成JSON

**🚨 --agent-output 不是"直接注入成品用例"，而是"Agent=LLM阅读prompt后的生成结果"。**
任何包含"进入功能页面执行测试点"/"验证操作结果"/"页面或数据发生相应变化"等模板短语的agent-output，
代码层会直接reject（V4.12.2占位符检测）。

以上3项全部打勾 → 开始逐条生成

---

## V4.12.1 逐条生成流程

**🔴 前置依赖：已完成上述「前置动作」3步（已读P6 prompt + P5数据 + 理解参数用法）**

```
exec: python3 "$ORCH" --action p6_tp_list
```
→ 获得 tp_list、total、estimated_minutes、estimated_range

**🔴 TP 索引说明（V4.12.8）:**
- `tp_index`: 从 0 开始（编程惯例），用于 CLI 参数 `--tp-index N`
- `display_index`: 从 1 开始（人类可读），对应 P5 的 TP-001, TP-002...
- 文件命名: `tp_{tp_index:03d}.json`（例: tp_index=0 → tp_000.json = TP-001）

**对每个 tp_index=0,1,...,total-1 执行:**

```
Step ① 获取prompt (V4.14.1: --short精简输出):
  exec: python3 "$ORCH" --action p6_generate_one --tp-index {N} --short
  → stdout输出精简摘要（TP编号/优先级/类别/标题/context文件路径）
  → 🔴 Agent必须 read p6_tp_output/tp_{N:03d}_context.json 获取完整prompt后生成用例

Step ② 作为LLM生成用例JSON:
  → 基于prompt中的P5结构化信息（ui_elements/field_checklist/related_rules等）
  → 🔴 Agent即被prompt的LLM，完整阅读并生成5核心字段
  → 🔴🔴 V4.15.45 数量纪律（强制）: 生成前必须先读 context.json / P5数据中的 `expected_case_count` 字段，
     严格按该数量生成用例，不多不少。
     ⚠️ PCI类TP（pci_flag=true / PCI-开头）通常 expected_case_count=3，禁止习惯性只写2条。
     ✅ 生成完毕后自检: 实际case数量 == expected_case_count，不符则补齐/删减后再 --save。

Step ③ 保存:
  exec: python3 "$ORCH" --action p6_generate_one --tp-index {N} --save --agent-output '...'
  → 代码自动补全其余19列字段
  → 执行G1+G1.5+G5-intra快速检查 + V4.12.2占位符检测

Step ④ 进度报告:
  每5条: 输出 `[进度] {N+1}/{total}条完成`

**🔴🔴🔴 P6 段内暂停硬控（V4.15.3 — 代码层强制+锁文件防绕过）**

代码层每完成约15条TP（`segment_done >= 15 && remaining >= 15`）时，
`p6_generate_one --save` 返回 `status: "PAUSE_REQUIRED"` + 退出码3。
**同时写入 `.p6_pause_lock` 锁文件**，后续 `p6_generate_one` 调用会被锁文件拦截（`status: "paused_locked"` + exit(2)），
即使Agent用脚本循环也无法绕过。

Agent收到 PAUSE_REQUIRED 后的行为规范：
1. **立即停止执行当前循环**
2. 输出进度摘要（从 `pause_info` 中提取）:
   `[⏸️ 代码层暂停] {completed}/{total} TP | 本段{segment_completed}条 | 剩余{remaining}条 | next_tp_index={next_tp_index}`
3. 等待用户回复「继续」
4. ⛔ 禁止自说自话继续。禁止说"自动继续"。禁止连段。
5. ⛔ 禁止在暂停期间继续调 p6_generate_one（锁文件拦截会返回 paused_locked）

**频率限制处理（V4.15.4）**：如果 p6_generate_one 返回 rejected（频率限制），必须等待至少 60 秒后重试。不要只等几秒就重试，否则会在同一滑动窗口内反复被拒。推荐：sleep 65 秒确保窗口完全过期。

**段内暂停点 ≠ 段落边界**：暂停点只需等「继续」后继续当前段落，
不需要重新读 rules/paragraph_5.md。

**🔴🔴🔴 Resume 规范（V4.15.3 更新）**

用户说「继续」后，**必须按顺序执行以下步骤**:

**1️⃣ 解锁暂停状态（V4.15.3 新增）**:
```
exec: python3 "$ORCH" --action p6_resume
```
→ 清除 PAUSE 锁文件 (.p6_pause_lock)，解除暂停状态
→ 返回 `"status": "resumed"` 表示解锁成功
→ 若返回 `"status": "not_paused"` 说明未暂停，直接继续下一步
→ ⛔ 禁止跳过此步骤直接调 p6_tp_list（锁文件会拦截后续 p6_generate_one 返回 paused_locked）

**2️⃣ 确认当前进度**:
```
exec: python3 "$ORCH" --action p6_tp_list
```
→ 查看 `completed_count` / `pending_count` / `next_tp_index`
→ 从 `next_tp_index` 开始继续逐条 p6_generate_one
→ 如 `next_tp_index` 为 null：全部TP已完成 → 直接 `p6_merge`

⛔ 禁止: 不调 p6_resume 直接调 p6_tp_list（锁文件未清除）
⛔ 禁止: 不调 p6_tp_list 直接凭记忆从某个 tp_index 开始
⛔ 禁止: 依赖 pause_info 中的 next_tp_index 而不重新获取

**🔴 Resume 后首条用例风格锚定（V4.15.0）**

恢复后首条用例需对齐以下结构规范：
- 步骤: 数字编号 + 操作动词（点击/选择/输入/等待/验证），每步1个操作
- 期望结果: 描述可观测状态（如 "页面展示XX字段,值为YY"），禁止使用模糊词汇（"正确""正常""成功""符合预期"）
- 前置条件: 包含三要素 — 入口路径 + 账号权限 + 数据准备
- 优先级: P0(核心主链路)/P1(重要分支)/P2(辅助场景)，严格遵守10-15%冒烟比例

**🔴 重试规则:**
- quality_rejected时，读取issues+fix_hints → 修复 → 重新 --save
- 自动重试最多3次，不得向用户报告过程
- 连续3次失败 → remarks标注 `[GATE_ISSUE]`，继续下一条，不阻塞

**🔴🔴 V4.15.45 批量提交 rejection 防护（强制）:**
orchestrator 严格按 tp_index 顺序执行。批量提交多个TP时，若某个TP被 rejection（quality_rejected/G1.5/数量不足）:
- ✅ **立即停止**，不要再发后续TP
- ✅ 记录被拒的 tp_index 和原因，**下一轮提交时第一个先补发被拒TP**
- ✅ 被拒TP确认 PASS 后，才能继续发后续TP
- ⛔ 禁止: rejection 后紧跟着发后续TP（会导致 skipped_count 累加、顺序违规）
- ⛔ 禁止: 跳过被拒TP继续发后面的（会导致顺序违规，下一轮必须先补被拒TP才解锁）
- 💡 高风险TP（G1.5高频词「正常/成功/一致/正确/符合预期」、PCI类数量不足风险）建议**单条提交等PASS再发下一个**，不要混入批量。

**🔴 全部TP完成后必须执行:**
```
exec: python3 "$ORCH" --action p6_merge
```
→ 合并所有 tp_*.json → p6_output.json（兼容旧batch格式）

**🔴 P6 修复流程 SOP（V4.12.8 — 必须遵守）:**

当 P7 报告质量问题需要修复用例时:

□ 1. 确认修复源文件: **修改 tp_*.json（batch文件），不是 p6_output.json**
   → p6_output.json 是 p6_merge 的产出，会被覆盖
   → 源文件在 {data_dir}/p6_tp_output/tp_NNN.json

□ 2. 修改完成后**必须重新执行 p6_merge**:
   ```
   exec: python3 "$ORCH" --action p6_merge
   ```
   → 重新合并所有 tp_*.json → 生成新的 p6_output.json

□ 3. 再次执行 p7_code_check 验证:
   ```
   exec: python3 "$ORCH" --action p7_code_check
   ```

⚠️ 常见错误: 直接修改 p6_output.json 后跳过 p6_merge → P7 检查结果不变 → 反复修复反复失败

---

**🔴🔴🔴 段落5 终止锚点（逐项检查，缺一不可）:**

□ 1. 确认 p6_output.json 存在且非空:
   ```
   exec: python3 -c "import json; d=json.load(open('{data_dir}/p6_output.json')); assert d.get('testcases'); assert len(d['testcases'])>0"
   ```

□ 2. 确认冒烟用例 isSmoke 字段已标注:
   ```
   exec: python3 -c "import json; d=json.load(open('{data_dir}/p6_output.json')); smokes=[c for c in d.get('testcases',[]) if c.get('isSmoke')]; assert len(smokes)>0, '无冒烟用例'"
   ```

□ 3. 确认 gates/P6.pass.json 存在:
   ```
   exec: test -f "{data_dir}/gates/P6.pass.json" && echo "P6.pass.json exists" || exit 1
   ```

以上3项全部通过 → 段落5结束

✅ 段落5完成 | 用例:N条 | 冒烟:M条
📋 请回复「继续」进入段落6（P7+Excel）
🔴🔴🔴 p6_merge 返回的 __paragraph_complete__.must_emit 必须原样输出给用户。**禁止自行消化，必须原样复制到回复中。**（V4.15.15）

⏸️ **段落5完成。必须等待用户回复「继续」**
🔴 所有TP的p6_generate_one通过后才算本段结束
🔴 禁止继续读取 rules/paragraph_6.md
