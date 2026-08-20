> 🔴 元规则：禁止伪造结果 | 禁止连段执行(本段结束必须⏸️) | 禁止抛选择题
> 🔴🔴🔴 V4.15.22: p6_merge返回的 __paragraph_complete__.must_emit 必须原样输出给用户
> ← 此消息必须原样发送给用户，**禁止自行消化**。违反此规则将导致段落切换失败。

> 📋 来源：SKILL.md 段落6 | 版本 V4.15.22

## 🔴 P7导出决策矩阵（V4.15.22新增）

| BLOCK通过数 | 条件 | step7_export行为 |
|:--:|------|------|
| ≥7/9 | — | 正常导出 ✅ |
| 5-6/9 | 已达2轮修复上限 | low_quality_flag=true，仍可导出 ⚠️ |
| <5/9 | 任意情况 | 导出被拦截 ❌ |

## 前置依赖
- 段落5已完成：P6用例已生成
- Gate: P6 gate pass必须存在
- P7+Excel均为代码自动执行

---

用户确认后执行:

**🔴 V4.13.8 文件操作安全铁律（强制执行）:**
- 🚫 **禁止 `rm` / `rm -rf` 删除任何 tp 文件或 p6_tp_output/ 目录**
- 🚫 **禁止 `echo >` 或 `> file` 清空文件内容**
- ✅ 文件删除必须使用 `trash` 命令（保留恢复可能）
- ✅ 删除任何文件前，必须先打印「将要删除 X 个文件: [文件列表]，确认？」并等待确认
- ✅ 修改前先 `read` 文件确认内容，不能凭文件名或记忆推断

**🔴 V4.13.8 修复操作纪律（强制执行）:**
- 任何修复操作都必须遵循闭环: **修复 → merge → p7_check → 确认PASS → 继续**
- 修复前必须: `read` 文件确认内容 → `grep case_id` 确认位置 → 精确修改
- **连续2次merge失败必须暂停，分析根因后针对性修复，不得用同样方法重试第3次**
- **🔴 V4.15.23: fix_hints 返回异常时（case_id为空、tp_file找不到、batch_index不存在），必须立即报告用户，不得静默跳过或自行猜测**
- ❌ 修复后不merge直接p7_check（检查的是旧数据）
- ❌ 凭文件名推断tp_index对应关系（tp_035.json ≠ TP-035）
  - 🔴 V4.15.23 TP文件映射规则：**文件 tp_{N:03d}.json 对应 P5 中的 TP-{N+1}**（tp_index = TPN - 1）
  - 例：tp_000.json → TP-001 / tp_035.json → TP-036 / tp_072.json → TP-073
  - 定位TP文件：先 grep case_id 确认 → 再 read 目标文件

**🔴 V4.15.26: 15 TP checkpoint 强制暂停机制:**
- orchestrator 在连续生成15个TP后自动触发 `CHECKPOINT_REQUIRED` → `exit(3)`
- Agent 必须执行 `python3 $ORCH --action p6_resume` 解锁
- ⚠️ 这不是建议，是代码硬控 — 强行继续会直接被拒绝
- p6_resume 会自动清理 `.p6_checkpoint` 文件并重置计数

**🔴 V4.15.38: 会话压缩后强制进度校验（不可跳过）**
如果本次会话经历过压缩（历史摘要中有进度描述），在继续生成前必须执行：
```
exec: python3 "$ORCH" --action p6_verify_progress
```
- 该命令对比文件系统与 orchestrator_state.json 的 TP 数量
- 如果 state_count < fs_count → 说明压缩回滚了状态，从 state 记录的进度继续
- ❌ 禁止依赖压缩摘要中的"已完成TP-N"描述判断进度
- ✅ 必须以 p6_verify_progress 或 orchestrator_state.json 的 p6_completed_tp_indices 为准

**🔴 V4.15.26: Gate pass JSON 格式（手工创建时务必参照）:**
```json
{
  "step": "P7",
  "task_id": "task_20260622_132015",
  "status": "PASS",
  "summary": "...",
  "validated_at": "2026-06-22T14:31:02+08:00"
}
```
- ⚠️ `source_action` 由 `_write_signed_gate` **自动注入**（手工创建易遗漏）
- ⚠️ `hmac` 字段由 orchestrator 自动计算（签名覆盖除hmac外的所有字段 + 虚拟的 `_task_id`）
- ⚠️ 手工创建 gate pass 时，必须用 `python3 $ORCH --action p7_code_check` 让代码生成，不要手写

**🔴 段间验证(必须先执行):**
```
exec: python3 "$ORCH" --action status
```
确认P6的gate pass存在。如不存在,必须重新执行段落5。

**Step 1: P7质量门禁(V3.3.1: 代码自动校验,无需Agent生成JSON)**
```
exec: python3 "$ORCH" --action p7_code_check
```
→ 代码自动读p5_output.json+p6_output.json,执行C1-C9+C7.1全部11项校验
→ 自动生成p7_output.json + p7_report.html + P7.pass.json
→ ❌ 禁止用step_run --step P7,会被拒绝

---

**🔴🔴🔴 Step 1b: P7失败自动修复（Agent按fix_hints逐项修复，禁止抛选择题）**

读取 p7_output.json，检查 `p7_gate_pass` 字段:

**✅ P7通过**: 自动进入 Step 2 Excel导出。

**❌ P7失败**: 读取 `fix_strategy` 和 `fix_hints` 字段，按以下策略自动执行：

| fix_strategy | 条件(coverage) | Agent动作 | 重试 |
|-------------|:--:|------|:--:|
| `local_repair` | ≥10% | 读fix_hints→逐类修复→p6_merge→重跑P7 | 2轮 |
| `restart_p6` | <10% | restart_from P6 全量重跑 | 1次 |
| 2轮修复后仍失败 | — | 标记low_quality→继续Excel导出 | — |

**修复执行流程（Agent自动，不询问用户）:**

```
1. 读 p7_output.json → 提取 fix_hints 数组

2. 对每种 action 逐类处理（按顺序：generate_missing→fix_step_expected→fix_vague→fix_forbidden）:

   📍 action=generate_missing:
     🔴 V4.15.43: 生成前先检查TP文件是否存在且内容有效:
       - 如果 p6_tp_output/tp_{tp_index:03d}.json 已存在且 testcases 非空 → 跳过生成,输出WARNING "TP文件已存在但merge未计入(可能跨TP去重),建议检查P6 prompt差异化后重试"
       - 如果文件不存在或testcases为空 → 正常生成
     exec: python3 "$ORCH" --action p6_generate_one --tp-index {N}
     → 生成用例JSON → exec: python3 "$ORCH" --action p6_generate_one --tp-index {N} --save --agent-output '...'

   📍 action=fix_vague_expected / fix_forbidden / fix_step_expected:
     对fix_hints中的每个case:
       read {data_dir}/p6_tp_output/tp_{tp_index:03d}.json
       → 找到对应case_id → 修改fields → 用json覆盖写入原tp文件

3. 全部修复完成后:
   exec: python3 "$ORCH" --action p6_merge
   → 重新聚合所有TP文件（含新增）

4. 重跑P7:
   exec: python3 "$ORCH" --action p7_code_check
   → 如果PASS → Step 2 Excel
   → 如果FAIL → 第2轮修复 → 仍FAIL → low_quality → Excel
```

🔴 **元规则**: 全自动执行，禁止抛选择题(1/2/3)给用户。
🔴 最多2轮修复。达到上限仍失败 → 标记low_quality → 继续Step 2。
🔴🔴🔴 **导出铁律(V4.13.3): step7_export返回error时必须报告用户，禁止自行写CSV/Python脚本替代。违反=终止段落。**

---

**Step 2: Excel导出 + 评审推送**
```
exec: python3 "$ORCH" --action step7_export
```
→ 🔴 step7_export会校验P6用例数量底线 + P7 gate pass(必须由p7_code_check生成)
→ V4.0.0: 导出成功后自动推送用例到云端评审工具(如已配置),返回cloud_review字段
→ ⚠️ 如果P7失败且重试已达上限(low_quality_flag=true)，step7_export可能仍被拒绝
→ 此时输出: ⚠️ P7未通过但已达重试上限，用例已标记low_quality，请人工审查
**⚠️ MEDIA指令是发送文件给用户的优先方式。但如果路径为远程路径(/root/等)，需追加兜底。不输出=用户收不到文件。**
**⚠️ 评审链接是V4.0.0闭环的关键环节,必须展示给用户。**

---

**🔴🔴🔴 段落6 终止锚点（逐项检查，缺一不可）:**

□ 1. Step 2 Excel导出成功:
   → step7_export 返回 ok，excel_path 存在

□ 2. 🔴🔴🔴 MUST_EMIT MEDIA 输出:
   → step7_export 返回 `__must_emit__` 字段 → **原样复制**到回复中(独占一行)
   → 格式: `MEDIA:{data_dir}/test_cases.xlsx`
   → 这是全流程最后一道工序，缺失则用户永远收不到文件

□ 3. 🔴 兜底展示 P7报告内容:
   ```
   exec: cat {data_dir}/p7_report.txt | head -30
   ```
   → 将输出展示给用户

□ 4. 展示P7质量门禁结果摘要:
   → 通过/不通过/警告数量

□ 5. 展示评审推送结果:
   → 链接（cloud_review.review_url）或失败原因（cloud_review.message）
   → 这是 V4.0.0 闭环的关键环节，必须展示给用户

□ 6. 执行 confirm_emit 确认（V4.12.7新增 — orchestrator硬拦截）:
   ```
   exec: python3 "$ORCH" --action confirm_emit --step step7
   ```
   → 确认 MEDIA 已输出。返回 ok 则全流程完成。

以上6项全部完成 → 段落6结束，全流程完成
缺任何一项 → 段落6未完成，补充缺失项
🚫 禁止以"MEDIA指令已发送"等文字描述替代实际输出MEDIA行
🚫 禁止在其他内容中间夹杂MEDIA，必须独占一行

## 用户交互指令

| 用户输入 | 含义 |
|---------|------|
| 继续/好的/下一步/go | 执行下一段 |
| 查看进度 | exec orchestrator.py --action status |
| 从P{N}重新开始 | exec: python3 "$ORCH" --action restart_from --step P{N} |
| 取消/停止 | 终止流程,保留已完成产物 |
| 重试推送 | exec: python3 "$ORCH" --action retry_push |

## 断点续跑

用户发送"继续"时,如果当前任务有未完成步骤:
```
exec: python3 "$ORCH" --action resume
→ 获得 next_step,从对应段落继续
```

## 错误处理

| 错误 | 处理 |
|------|------|
| orchestrator返回error | 输出错误信息,🔴 不允许回退到手动模式,必须修复后重试 |
| orchestrator返回gate_blocked | 检查前置步骤是否完成 |
| orchestrator返回guard_failed | 重新生成JSON重试(最多1次) |
| orchestrator返回quality_failed | 按retry_hint重新执行对应步骤 |

## 引用文件

| 路径 | 说明 |
|------|------|
| tools/orchestrator.py | 核心流程控制器,15+个action,参数自动化,HMAC签名,云端评审推送 |
| tools/truncation_guard.py | 四级截断检测+原子写入+HMAC签名 |
| tools/export_excel.py | Excel导出(21列公司标准) |
| tools/export_markdown.py | Markdown降级导出 |
| tools/export_p0p1.py | P0/P1结构化报告导出(MD+HTML) |
| tools/export_prd_review.py | PRD审查结果Excel导出 |
| tools/p5_prepare.py | P5测试点合并预处理 |
| tools/p6_templates.py | P6模板整理(11套category模板,统一流程辅助) |
| tools/image_extract.py | docx图片抽取(python-docx) |
| tools/image_understand.py | 图片理解调度(vision/OCR/context_only三级降级) |
| tools/image_ocr.py | OCR引擎封装 |
| tools/image_enhance.py | 图片理解增强聚合 |
| tools/model_detect.py | 模型能力检测(视觉能力+预处理) |
| tools/test_px_pipeline.py | 图片处理管线集成测试 |
| tools/image_api_server/server.py | 腾讯云图片理解API服务端(Flask) |
| references/orchestrator_protocol.md | Agent↔orchestrator交互协议 |
| references/onboarding.md | Onboarding检查+交互流程 |
| references/step0-px.md | Step 0+PX详细指令(prompt参考源) |
| references/step1-4.md | P0-P5详细指令(prompt参考源) |
| references/step5-7.md | P6-P7+Excel详细指令(prompt参考源) |
| prompts/P0_requirement_structuring.md | P0需求结构化Prompt |
| prompts/P0.5_prd_quality_review.md | P0.5 PRD质量审查Prompt |
| prompts/P0_prd_review_enhance.md | P0 PRD审查增强Prompt |
| prompts/P1_feature_tree_generation.md | P1功能点树Prompt（一shot模式） |
| prompts/P1_skeleton.md | P1骨架Prompt（分批v4.8.9） |
| prompts/P1_feature_scenario.md | P1单feature场景Prompt（分批v4.8.9） |
| prompts/P2_test_point_draft.md | P2测试点草稿Prompt |
| prompts/P3_risk_identification.md | P3风险识别Prompt |
| prompts/P4_pci_identification.md | P4 PCI识别Prompt |
| prompts/P5_test_point_merge.md | P5测试点合并Prompt |
| prompts/P5a_batch_merge.md | P5a批量合并Prompt |
| prompts/P6_testcase_generation.md | P6用例生成Prompt |
| prompts/P6_api_rules.md | P6 API测试规则Prompt |
| prompts/PX_image_understand.md | PX图片理解Prompt |
| prompts/PX_ocr_extract.md | PX OCR提取Prompt |
| config/project_domain_mapping.json | 项目→业务域映射配置(v2.0: 10组项目关键词+16个同义词+12域知识库映射) |
| user_knowledge/preferences.json | 用户偏好配置(PRD审查/输出格式/默认域) |
| user_knowledge/model_vision_override.json | 模型视觉能力覆盖配置 |
| **知识库由云端API实时同步** | `_sync_knowledge_from_cloud()` 按需拉取，本地无缓存文件 |
| CHANGELOG.md | 版本变更记录 |
| RELEASE_NOTES.md | 发布说明 |

## 已知限制

1. Agent需配合orchestrator协议,不配合时orchestrator会重试但无法强制
2. 6段确认模式需要用户回复5次"继续"(P2/P5自动执行,无需确认)
3. Excel导出依赖openpyxl
4. 图片理解依赖Agent模型的视觉能力

### ⛔ P6子Agent执行限制（V4.7.3新增）

**P6用例生成禁止通过 sessions_spawn 派发给子Agent执行**，原因：
- 子Agent有30分钟硬超时，P6每批50条用例+大量上下文读取会触发超时
- 子Agent的上下文窗口与主会话不同，无法读取所有必要文件
- 经验证：3次子Agent执行均29分59秒超时，**零产出**

**强制执行**：
- orchestrator.py 的 action_p6_* 入口已加入子Agent环境检测
- 检测到子Agent环境时直接 `exit(1)` 并返回明确错误信息
- 主会话执行P6是唯一正确路径

### 同TP多TC步骤差异化规则（V4.15.52新增）

当同一测试点(TP)包含 ≥2 条测试用例(TC)时，**禁止多TC共用完全相同的步骤文本**：
- 每个TC的步骤至少包含一个**差异化描述**（不同的操作对象/数据值/观察点）
- 示例：TC-001"执行日终同步并验证团队名称字段" vs TC-002"执行日终同步并验证协同比例字段" vs TC-003"展开员工维度sheet，观察员工列表是否为空"
- 不要仅在 expected_results 上区分，步骤也必须体现差异
- **白名单例外**：登录步骤、页面导航步骤允许共用（p7检查已排除共同前缀）

### 步骤唯一性校验规则（V4.7.3更新）

- **通用场景**：唯一步骤比例 ≥ 50%（不含登录/导航共同前缀）
- **risk_verification/exception 类用例**：放宽至 ≥ 30%（风险点天然场景单一）
- 共同前缀（登录、导航步骤）已自动排除，不参与唯一性计算

### 降级方案：Agent生成失败时的处理

当Agent连续3次生成被Gate拒绝时（非子Agent超时问题）：
1. 检查是哪个校验不通过（步骤唯一性/步骤-期望不对应/占位符等）
2. 针对性修复后重试，不要整体重写
3. 如果同一批次累计6次被拒 → 检查P5测试点description是否过于简单导致无法差异化
4. 极端情况：记录到 data_dir/quality_issues.json，手动标注后跳过（需在报告中注明）
---
🔴🔴🔴 本段执行完毕 → ⏸️ 停止 → 等待用户回复「继续」
🔴 禁止继续读取 rules/paragraph_7.md 或 SKILL.md 后续内容
