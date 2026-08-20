---
name: user-research
description: "Skill for user-research work across the product lifecycle — planning studies, designing interviews and surveys, and turning behavioral data into experience insights. Triggers on 用户调研 / 用户研究 / user research, 用户访谈 / interview guide, 问卷 / survey / questionnaire, 用户行为分析 / behavior analysis, 体验洞察 / UX insight. Governs scope framing, method selection, artifact structuring, and evidence discipline for each sub-scenario."
---

# User Research

Produce credible, decision-useful research. Every claim traces to evidence — a quote, an event, a survey response — never to assumption. When evidence is thin, say so. Be concise: an analyst-grade table or one quantified line beats a paragraph of hedging.

## 0. Response Mode — match effort to the ask

Read what the user actually wants before deciding how much to frame.

- **Direct artifact ask** (“写份问卷”, “给我访谈提纲”, “帮我做个 NPS 表”) → produce the artifact directly. Infer objective and audience from context, add at most one line of assumptions, and deliver. Do **not** open with the full Why/What/Who framing or the question table.
- **Open research ask** (“帮我调研 X”, “想搞清楚用户为什么流失”) → frame first (§1), then design.
- **Default deliverable is a Markdown (`.md`) file — always, unless the user explicitly asks for another format.** Do not reach for HTML / PDF / DOCX / PPTX / Feishu on your own; when unsure, deliver Markdown (see §5, §6). In the Markdown output, do **not** use `trae_ref` reference links — use plain Markdown links or inline text instead.

Ask a question only when a missing detail would flip the method or the deliverable; otherwise infer and proceed.

## 1. Frame Before You Design (open asks only)

Pin down three things, phrased as plain questions. They also open the deliverable as a short **摘要**:

1. **为什么做（Why）** — 这次调研要帮团队定什么决策？没有要服务的决策，调研只是表演。
2. **研究目的（What）** — 最核心的一个问题，措辞要让答案能改变下一步动作。
3. **研究谁（Who）** — 研究谁、如何招募、多少人（定性看深度，定量看显著性 §2）。

Render the core question as a focused table — one bold primary question, ≤2–3 sub-questions, each tied to the decision it serves. Cut any row that would not change the decision.

| # | 研究问题 | 关联决策 | 方法 | 判断标准 |
| --- | --- | --- | --- | --- |
| **主** | **<单一核心问题>** | <决策> | <方法> | <怎样的答案算数> |
| 1 | <子问题> | … | … | … |

Match method to question: **qualitative** for *why/how*, **quantitative** for *how many/how much*. Most questions want both — qual to generate hypotheses, quant to size them. Pick only the methods the primary question needs; go deep on those, skip the rest.

| Method | Best for | Type |
| --- | --- | --- |
| User interviews | Why / how behind a behavior | Qual |
| Usability testing | Where a design breaks down | Qual |
| Surveys | How many, how much, at scale | Quant |
| Behavioral / funnel analysis | What happened, where drop-off occurs | Quant |
| NPS / CSAT | Loyalty & satisfaction + driver verbatims | Mixed |
| A/B test | Causal effect of a change | Quant |

## 2. Sample Sizing — always quantify

State sample-size reasoning in numbers, not adjectives. Give the target N *and* the confidence/precision it buys.

**Quantitative (surveys / metrics).** For a proportion, `n = z²·p(1−p) / e²` (use p=0.5 for the safe max). At 95% confidence (z=1.96), p=0.5:

| Margin of error | N (whole population) |
| --- | --- |
| ±3% | ~1,067 |
| ±4% | ~600 |
| ±5% | ~384 (round to 400) |
| ±7% | ~196 |

- **Sub-group floor:** any cut you plan to analyze needs **N≥50** (rough ±14% at 95%); prefer ≥100. Allocate proportionally across segments, then top up small-but-strategic segments to hit the floor.
- **Detecting a difference/lift** (A/B, before/after): size for the *minimum detectable effect*, not a fixed N. Smaller effects need larger N; state the MDE and power (default 80%).
- Report it as one line, e.g. *“95% 置信度、±4% 误差，整体 N=600；按人群比例分配，最小子群 N≥50 以支持子群分析。”*

**Qualitative.** Saturation lands around **5–8 users per distinct segment**; usability testing surfaces ~85% of issues with **5 users**. More segments → more sessions, not deeper-per-segment.

## 3. Research Plan (one page, only for open asks)

- **Objective & decision** — the §1 摘要 + question table, and the decision they feed.
- **Method & rationale** — chosen approach and why it fits.
- **Participants** — segment, recruit criteria, target N with the §2 justification, screener logic.
- **Instruments** — the guide / survey / analytics query you will run.
- **Analysis approach** — how raw data becomes findings.
- **Risks** — recruiting, bias, representativeness — with a mitigation for each.

## 4. Interviews & Surveys

### 4.1 Interview Guide
- Open with warm-up/context (“Walk me through the last time you…”), move to the core topic, close with a catch-all (“What haven’t I asked that I should have?”).
- Prefer past-behavior (“What did you do?”) over future-intent/approval (“Would you like…?”, “Is this good?”) — stated intent is a weak predictor.
- Attach probes (“Why?”, “What happened next?”, “How did that feel?”) instead of scripting every follow-up.
- Ban leading and double-barreled phrasing (“Don’t you find X frustrating?”, “How useful *and* easy was it?”).

### 4.2 Survey
- Each question maps to a research objective — drop any that answers nothing decision-relevant.
- One idea per question; balanced scales; neutral wording; randomize option order where order-bias is a risk.
- Prefer validated scales (SUS for usability, CSAT/CES for satisfaction/effort) over inventing new ones.
- Include screening logic and the demographic cuts you’ll segment by (§2 sub-group floor).
- State target N and expected precision on the survey itself (per §2).

## 5. Analysis & Insight

Apply only the methods the question calls for — this is a menu, not a checklist.

### 5.1 Decision & Switch Analysis (why users chose / switched / churned)
Reconstruct the decision; pull five things, each traced to a participant:
- **触发场景** — the concrete event that started the search (not a demographic).
- **真实动机** — the progress wanted: functional, emotional, social jobs.
- **比较对象** — every alternative actually weighed, including doing nothing.
- **真实顾虑** — anxieties and switching costs that nearly stopped them.
- **选择逻辑** — the trade-off at the moment of choice; name the one attribute that tipped it.

Behavior moves only when *push + pull(new)* outweigh *anxiety + habit(old)*.

### 5.2 Journey & Experience Mapping
Per stage: goal, action, emotion, friction. Mark moments of truth and drop-off; back every emotional dip with behavioral data (conversion, time-on-step, retries) — cite the number.

### 5.3 NPS Analysis
NPS is the verbatim mining, not the number. Produce both.
- **Score** — %Promoters(9–10) − %Detractors(0–6); always with segment breakdown and base size, never the headline alone.
- **Driver coding** — code follow-ups into themes; report each theme’s frequency and its promoter-vs-detractor skew.
- **Synthesis** — rank themes by frequency × impact; top detractor themes → hypotheses, top promoter themes → strengths to protect.
- Report against a stated baseline and time window.

### 5.4 Experience Insight
Write each insight as *observation → interpretation → implication*: what the data shows, why it likely happens, what to do. An insight the team can’t act on is a metric, not an insight. Guard against correlation-as-causation, survivorship bias, and conditioning on the outcome you’re explaining; flag artifacts.

### 5.5 Recommendation Matrix
Score needs by *importance × dissatisfaction* (underserved = high importance, low satisfaction), then place each recommendation on **Impact × Effort** (quick win / big bet / fill-in / avoid). Each states its evidence, the decision it serves, and the cost of doing nothing. Rank by expected impact, not complaint volume.

### 5.6 Interview Transcript → Report

**Only when the input is an interview transcript to summarize.** Structure it as a **progressive hierarchy** (概述 → 证据 → 行动，标题用 `4`/`4.1`/`4.1.1` 嵌套、正式名词化措辞见 §6)。Skeleton: 元信息头 → 研究概述（目标/方法/局限）→ 受访者画像 → 关键发现总结 → 详细发现（每主题：现状 → 原话+数据 → 解读）→ 痛点机会 → 改进建议（P0/P1/P2）→ 结论 → 附录（金句、方法学）。

Must carry three things: **访谈元信息**（头部 + 附录方法学，让读者能判断证据强度）、**层层递进的标题**、**后续行动**（待验证假设表、下一步研究、影响追踪闭环）。

## 6. Evidence & Delivery Discipline

- **Trace every claim** to a source (participant ID, event query, survey item). Separate observation from interpretation.
- **Right-size the caveat.** State N and its limits (§2); don’t generalize a 5-person study to the whole base.
- **Privacy.** Anonymize participants; strip PII from quotes and exports.
- **专业措辞。** 保持研究报告的客观、书面语气。
  - 不用第一人称（“我们”“我”“咱们”）。用无主语或被动/名词化表述：“我们发现用户流失” → “数据显示用户流失”“研究发现……”；“我们建议” → “建议”“推荐方案为”。
  - 标题用正式的名词化措辞，避免口语化。例：“研究内容及选择理由” → “研究范围与方法选型依据”；“怎么招人” → “样本招募标准”；“数据咋来的” → “数据采集方法”。
- **Format.** Default to a Markdown file — always, unless the user explicitly asks for another format. Do not use `trae_ref` reference links inside the Markdown; use plain Markdown links or inline text. Only when the user asks for a formatted artifact (HTML / PDF / DOCX / PPTX / Feishu doc), check available skills for one that produces that format and invoke it — don’t hand-roll it.
