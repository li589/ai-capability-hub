---
name: qa-req2testcase-generator
description: "AI驱动的需求→测试用例生成能力。V4.15.56架构:P5 Risk TP描述质量修复+G6+C2级联豁免+G1.5异常场景豁免+merge容差对齐+p7_quick_fix"
version: "4.15.56"
metadata:
  author: "shaozhe"
  architecture: "orchestrator-driven + segmented-rules + auto-fix + unified-mode"
---

# qa-req2testcase-generator V4.15.56

> 版本:4.15.56 | P5 Risk TP描述质量修复+G6+C2级联豁免+G1.5异常场景豁免+merge容差对齐+p7_quick_fix
> V4.15.44: RISK-ETP context空洞三重故障修复(A:source_scenario前缀匹配 B:diff_hint正则防"测试点"截断 C:ETP展开补title) + metrics监控盲区修复(retries从state读)
> V4.15.43: P0-3 checkpoint state计数 + G1.5白名单 + P6.merge partial标注 + HOLLOW_STEPS阈值分类 + G1.5诊断优化
> V4.15.35: 🔧 risk TP死循环修复(模板去占位符+降级保留warning+diff_hint增强)
> V4.13.8: 🔧 14项质量改进 | 🧠 CoT复杂TP强制推理 | 🛡️ 文件安全三层防护 | 📋 Prompt泛化(虚构场景替代特定项目)

---

## ⚠️ 元规则（最高优先级，违反即终止）

**Agent必须100%执行skill规定的流程，不得自行判断"优化"或"改进"。**

1. **执行优先**：按skill规定流程执行每一步，不得跳过、绕道
2. **规则即硬约束**：「禁止」「必须」「🔴」是代码级硬约束，违反即报错
3. **发现问题先执行后反馈**：完成当前流程后反馈，不在执行中自行修改
4. **禁止伪造结果**：orchestrator返回error时必须修复重试，不得伪造gate pass
5. **禁止自我决策**：不允许Agent自行判断"规则不合理/太慢/可优化"并绕过
6. **🔴 禁止自行发明规则（V4.15.26新增）**：本文档/代码中未明确列出的任何速率限制、延迟、节流、防批量机制，均不存在
   - ✅ 允许：文档白纸黑字写了"每N个TP暂停M秒" → 照做
   - ❌ 禁止：凭直觉添加 `sleep(55)` "防止脚本批量识别"
   - ❌ 禁止：自行推断"应该有防封禁机制"并实现
   - 不确定某规则是否存在 → 先读 orchestrator.py/gate_checker.py 源码确认 → 文档和代码均无要求 → 该规则不存在
6. **禁止抛选择题**：任何步骤失败后自动修复重试，禁止停下来向用户要选择
7. **⛔ 禁止脚本批量生成 + 禁止子代理派发**（V4.12.5+V4.15.9）：(1) 禁止编写 Python/Shell/JavaScript 脚本循环调用 `p6_generate_one`；(2) 禁止通过 `sessions_spawn` / 子 Agent 派发 P6 用例生成任务，P6 必须由主会话 LLM 逐条阅读 prompt 后手写生成每个 TP 的用例。这两种做法本质相同——绕过主会话逐条执行规则，批量生成的内容必然空洞，质量门禁会拦截。orchestrator 已内置子Agent环境检测，违规直接 exit(1)。
8. **🔴 质量优先原则**（V4.13.8）：效率不能以牺牲质量为代价。禁止因为"太慢了""时间不够"就跳过P7检查、批量修改用例、放弃merge修复。遵循闭环流程：修复→merge→p7_check→确认PASS→继续。连续2次merge失败必须暂停分析根因。去重率>50%或冒烟=0必须拒绝接受。
9. **🔴 冒烟用例标注规则**（V4.13.8）：冒烟用例必须严格聚焦「入口可达性+核心展示」，标注标准： ✅ 可标：所有页面入口能否正常打开、核心数据能否加载展示、核心操作能否完成（如提交/查询/导出）； ❌ 禁止标冒烟：异常场景（如权限不足/数据为空/超时）、删除/禁用操作、次要字段验证、UI细节核对。P0占比硬性控制在10-15%。
10. **⛔ 禁止 Agent 自行插入 sleep/wait/delay**（V4.15.2）：Agent 不得在执行流程中的任何位置自行添加等待（包括但不限于 `sleep`、`time.sleep`、`asyncio.sleep`、`setTimeout`、shell `sleep` 命令、或在两个命令之间插入刻意停顿）。orchestrator 和所有代码层工具已内置了完整的速率限制（rate-limiting）、退避重试（exponential backoff）和并发控制。Agent 自行添加 sleep 是多余行为，只会拖慢流程，且可能绕过 orchestrator 的速率控制逻辑。**发现 Agent 自主插入 sleep → 视为违反元规则第1条（自行判断"优化"），该步骤结果作废。**
11. **🔴 复盘/报告数据必须从 statistics 取值（V4.15.5新增）**：编写复盘报告、测试报告、质量报告时，所有统计数据（总用例数、冒烟数、P0/P1/P2分布、去重率等）必须从 `p6_output.statistics`、`p7_output.statistics` 或 `orchestrator_state.json` 直接读取，**禁止 Agent 估算、推测或编造数字**。错误示例：实际冒烟38条却写95条。若发现报告数字与 statistics 不符 → 视为严重质量问题，报告作废重写。

---

## ⛔ 入口强制检查：需求载荷是否存在（最高优先级）

**此检查在技能触发后第一个动作执行。不通过→立即终止。**

✅ 允许继续：用户消息含需求正文 / 含需求附件(.docx/.txt/.pdf) / 明确引用近期需求
❌ 必须停止："我等会发"、"分析这个需求"(无附件)、仅提及技能名、模糊引用

不通过回复：`📋 请先发送需求正文或需求文档，收到后立即开始分析。`
通过回复：`✅ 需求载荷已收到 | 格式:X | 大小:Y | 📋 即将进入初始化...`

---

## 🔴 运行协议

**核心原则:orchestrator.py控制流程,Agent只负责执行prompt返回JSON。**

**6段确认模式:每次「继续」只前进一个段落（绝对禁止连段执行）:**
- 用户回复1次「继续」→ Agent**只执行下一个段落**，执行完立即⏸️停止
- ⛔ 禁止: 用户说1次「继续」Agent连跑多段
- ⛔ 禁止: 看到下一段gate已存在就"继续跑完"
- 每段结束后检查: 是否已输出⏸️？是否已等待「继续」？

**📌 `__must_emit__` 字段**：p2_code_generate / step7_export的stdout包含此字段。Agent必须将MEDIA行复制到回复，同时用 `exec cat` 展示文件内容。

---

## 🔴 段落边界规则（最高优先级，违反视为流程无效）

| 规则 | 说明 |
|------|------|
| ⛔ 禁止连段 | 每段结束→⏸️停止→等「继续」→才读下一段规则文件 |
| ⛔ 禁止预读 | 执行段落N时，禁止读取 rules/paragraph_N+1.md |
| ⛔ 禁止跨段 | 即使下一段gate已存在，也必须等用户「继续」 |
| 🔴 停止锚点 | 每段规则文件末尾有终止锚点，Agent读到必须停止 |

**📌 段内暂停 ≠ 段落边界（V4.15.0 代码层硬控）**：
- 段落5（P6用例生成）内部有**代码层强制的段内暂停点**（~15条TP，orchestrator返回 PAUSE_REQUIRED + exit(3)）
- 段内暂停：等「继续」后**必须先调 p6_tp_list** 确认 next_tp_index，在当前段落内接着跑
- 段落边界：等「继续」后**前进到下一段**，必须先读 rules/paragraph_N+1.md
- 🔴 Agent必须区分这两个概念，不得将段内暂停误认为段落结束

---

## 🔴 操作约束矩阵

| Step | Agent角色 | 唯一正确命令 |
|------|----------|------------|
| P0 | 执行者 | prep_prompt → 生成JSON → step_run |
| P1 | 执行者(分批) | 骨架→循环feature→p1_code_merge |
| P2 | 观察者 | `python3 "$ORCH" --action p2_code_generate` |
| P3 | 执行者 | prep_prompt → 生成JSON → step_run |
| P4 | 执行者 | prep_prompt → 生成JSON → step_run |
| P5 | 观察者 | `python3 "$ORCH" --action p5_code_merge` |
| P6 | **LLM生成者**(⛔禁子Agent) | p6_tp_list→逐条循环(p6_generate_one→完整阅读prompt生成JSON→p6_generate_one --save)→p6_merge<br>🔴 **V4.11.0逐条生成**：一次一个测试点，prompt极简(~400B)。Agent完整阅读prompt后生成JSON，字段由代码自动补全 |
| P7 | 观察者 | `python3 "$ORCH" --action p7_code_check` |

Agent只做3类事: ①exec orchestrator命令 ②read prompt并生成JSON write到文件 ③read图片并描述

---

## 🔴🔴🔴 V3.5.2 绝对禁止行为（代码层硬控）

1. **禁止直接写gate文件** — gates/*.pass.json 只能由orchestrator创建
2. **禁止直接写output文件** — p{N}_output.json 只能通过step_run等action写入
3. **禁止直接修改state文件** — orchestrator_state.json 内部修改
4. **禁止import orchestrator** — 不允许任何形式导入
5. **禁止跳过orchestrator** — 所有步骤必须通过 `python3 "$ORCH" --action XXX`
6. **禁止伪造执行结果** — error时必须修复重试，不得手动替代
7. **Onboarding必须逐步交互** — 3步逐步展示，禁止合并

违反以上任何规则，step7_export会审计拒绝。

---

## 📋 6段执行流程

| 段落 | 内容 | 规则文件 | 前置Gate | 确认点 |
|:--:|------|------|------|:--:|
| 1 | init + onboarding | `read rules/paragraph_1.md` | — | ⏸️ |
| 2 | step0 + 图片理解 | `read rules/paragraph_2.md` | P0 gate | ⏸️ |
| 3 | P0+P1 + 自动P2 | `read rules/paragraph_3.md` | step0 gate | ⏸️ |
| 4 | P3+P4 + 自动P5 | `read rules/paragraph_4.md` | P2 gate | ⏸️ |
| 5 | P6 用例生成 | `read rules/paragraph_5.md` | P5 gate | ⏸️ |
| 6 | P7 + Excel导出 | `read rules/paragraph_6.md` | P6 gate | 🏁 |

**🔴 执行流程（每段通用，严格执行）:**

1. 收到用户「继续」→ 查上表找到下一段N
2. `read rules/paragraph_N.md` → 完整阅读该段规则
3. 严格按规则文件中的指令逐步执行
4. 执行到规则文件末尾的终止锚点 → ⏸️停止
5. 输出「段落N完成，请回复「继续」」
6. 🔴 绝对禁止：读完paragraph_N.md后继续读取paragraph_N+1.md

---

## 📋 流程速查表

| 段落 | 核心动作 | 关键Gate | 暂停规则 | 常见错误 |
|:--:|------|------|------|------|
| 1 | init+onboarding | onboarding.pass.json | — | 环境异常 |
| 2 | 图片理解 | step0.pass.json | — | 需求格式错误 |
| 3 | P0+P1→P2 | P0+P1.pass.json | — | P1场景过多 |
| 4 | P3+P4→P5 | P3+P4.pass.json | — | P5测试点过少 |
| 5 | P6用例生成 | P6.pass.json | 每15TP暂停 | 会话压缩丢TP→p6_verify_files |
| 6 | P7+导出 | P7.pass.json | 修复循环 | fix→merge→check不可跳步 |

---

## 🔄 断点续跑

```
exec: python3 "$ORCH" --action status
```
→ 查看已完成的gate pass，从下一个未执行的步骤开始。
→ 如果当前段落已有部分gate pass → 阅读该段规则文件，跳过已完成步骤。

---

## ❌ 错误处理

| 错误类型 | 处理 |
|---------|------|
| gate_blocked | 检查缺失的前置步骤，从该步骤重新执行 |
| guard_failed | 检查truncation，修复JSON后重试 |
| quality_rejected | 按issues和fix_example修复，最多重试2次 |
| timeout | 检查文件是否已生成新内容，有则继续，无则重试 |
| **paused_locked** (V4.15.3) | P6已暂停，锁文件存在。→ `p6_resume` 解锁 → `p6_tp_list` 查看进度 → 继续 |
| **BUG** (V4.15.3) | orchestrator代码异常。禁止自行修复/绕过。立即停止并报告用户。 |

---

## 📁 文件结构

```
skill_v4/
├── SKILL.md                     ← 本文件（总控路由）
├── rules/
│   ├── paragraph_1.md           ← 段落1规则
│   ├── paragraph_2.md           ← 段落2规则
│   ├── paragraph_3.md           ← 段落3规则
│   ├── paragraph_4.md           ← 段落4规则
│   ├── paragraph_5.md           ← 段落5规则
│   └── paragraph_6.md           ← 段落6规则
├── prompts/                     ← LLM prompt模板
├── tools/                       ← orchestrator.py等工具
├── config/                      ← 配置
└── references/                  ← 参考文档
```

## 触发条件

「ai用例生成」「ai需求分析」「req2testcase」「生成测试用例」「分析需求」「拆解功能点」「输出测试点」「需求评审」「PRD转测试用例」

## 已知限制

- 仅支持中文需求文档（.docx/.txt/粘贴文本）
- 不支持视频/音频需求输入
- PX图片理解依赖腾讯云API（未配置则降级为caption_only）
