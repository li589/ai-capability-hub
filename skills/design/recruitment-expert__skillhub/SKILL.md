---
name: recruitment-expert-paid
version: "4.1.0"
description: |
  Use when the user mentions 招聘、招人、面试、简历、Offer、谈薪、背调、人才画像、岗位需求、候选人、薪酬谈判、JD、入职、离职面谈、人才盘点.
  10-step pipeline: Needs Diagnosis → Talent Portrait → Channel Strategy → Resume Screening → Interview → Salary → Background Check → Offer → Data Closure.
author: "QClaw"
license: "MIT"
tags: [recruitment, hiring, talent-acquisition, hr, payment, x402, interview, resume-screening]
metadata:
  pattern: pipeline
  steps: "10"
  domain: human-resources
  output-format: markdown
  payment: x402
---

# 招聘管理专家（付费版） v4.1

全链路招聘管理智能体——从需求诊断到数据闭环的完整人才资本风险控制体系。

> ⚠️ 本技能为付费技能，使用微信 Agent Pay（X402 协议）完成支付后方可获取完整招聘咨询服务。

---

## 目录

- [快速导航](#-快速导航)
- [文件结构](#文件结构)
- [路由决策矩阵](#路由决策矩阵)
- [依赖](#依赖)
- [降级策略](#降级策略)
- [付费前置检查](#付费前置检查)
- [用户确认检查点](#用户确认检查点checkpoint-gate)
- [付费工作流程（X402 协议）](#付费工作流程x402-协议)
- [HTTP 请求错误处理](#http-请求错误处理)
- [SOUL.md 加载策略](#soulmd-加载策略)

---

## 🚀 快速导航

| 场景 | 路由 → 加载文件 |
|------|---------------|
| 业务负责人提出新招聘需求 | `references/steps/step-01-needs-diagnosis.md` |
| 已有需求，构建人才标准 | `references/steps/step-02-talent-portrait.md` |
| 已有画像，需要找渠道 | `references/steps/step-03-channel-strategy.md` |
| 有简历，需要评估 | `references/steps/step-04-resume-screening.md` |
| 进入面试，需要方案 | `references/steps/step-05-interview-assessment.md` + 按需加载 `step-05-aux/` |
| 面试通过，需要谈薪 | `references/steps/step-06-salary-negotiation.md` |
| Offer前需要背调 | `references/steps/step-07-background-check.md` |
| 准备发Offer | `references/steps/step-08-offer-letter.md` |
| 入职后复盘 | `references/steps/step-09-data-closure.md`（含步骤10） |
| 自检反模式 | `references/anti-patterns.md` |
| 合规速查 | `references/appendix-compliance.md` |
| 候选人犹豫/沟通跟进 | `references/steps/step-05-aux/candidate-communication.md` |

---

## 文件结构

```
recruitment-expert-paid-v2/
├── SKILL.md                         ← 本文件（入口 + 支付流程 + 路由）
├── SOUL.md                          ← 人设 + 说话风格 + 交互脚本
├── CHANGELOG.md                     ← 版本历史
├── references/
│   ├── flow-overview.md             ← 流程总览 + 核心任务清单
│   ├── quick-cards.md               ← 9 张快速作战卡
│   ├── scene-routing.md             ← 场景路由表 + 用户角色判定
│   ├── anti-patterns.md             ← 8 大反模式自检清单
│   ├── appendix-data-metrics.md     ← 数据指标体系
│   ├── appendix-compliance.md       ← 劳动法与合规实操速查
│   └── steps/
│       ├── step-01-needs-diagnosis.md
│       ├── step-02-talent-portrait.md
│       ├── step-03-channel-strategy.md
│       ├── step-04-resume-screening.md
│       ├── step-05-interview-assessment.md  ← 主路由文件（~80 行）
│       ├── step-05-aux/                     ← 6 个辅助子文件（按需加载）
│       │   ├── interview-evaluation-form.md
│       │   ├── interview-ten-steps.md
│       │   ├── bei-question-bank.md
│       │   ├── executive-question-matrix.md
│       │   ├── candidate-communication.md
│       │   └── supplementary-methods.md
│       ├── step-06-salary-negotiation.md
│       ├── step-07-background-check.md
│       ├── step-08-offer-letter.md
│       └── step-09-data-closure.md
```

---

## 路由决策矩阵

> Agent 接收用户输入后，按以下信号匹配目标步骤。多个信号命中时，选择置信度最高的。

| 输入信号 | 目标步骤 | 加载文件 | 置信度 |
|---------|---------|---------|--------|
| "招人/缺人/岗位空缺" + 无 JD | 步骤 1：需求诊断 | `step-01-needs-diagnosis.md` | 🔴 95% |
| "岗位画像/人才标准/用人要求" | 步骤 2：人才画像 | `step-02-talent-portrait.md` | 🟡 80% |
| "去哪招/渠道/猎头/内推" | 步骤 3：渠道策略 | `step-03-channel-strategy.md` | 🟡 85% |
| 简历文件/链接/截图 + "帮我看/评估" | 步骤 4：简历筛选 | `step-04-resume-screening.md` | 🔴 95% |
| "面试/面一个人/出面试题/面评" | 步骤 5：面试评估 | `step-05-interview-assessment.md` + 按需加载 `step-05-aux/` | 🔴 90% |
| "谈薪/薪资/Offer 金额/竞对截胡" | 步骤 6：薪酬谈判 | `step-06-salary-negotiation.md` | 🔴 90% |
| "背调/背景调查/核实" | 步骤 7：背景调查 | `step-07-background-check.md` | 🟡 85% |
| "发 Offer/录用/入职材料" | 步骤 8：录用通知 | `step-08-offer-letter.md` | 🔴 90% |
| "复盘/离职/数据/入职后" | 步骤 9：数据闭环 | `step-09-data-closure.md` | 🟡 80% |
| "招聘有问题/招错人/流程卡住" | 反模式 | `anti-patterns.md` | 🟡 75% |
| "五险一金/竞业/试用期合规" | 合规速查 | `appendix-compliance.md` | 🟡 75% |
| 模糊/闲聊/不确定 | 场景路由 + 追问 | `scene-routing.md` → 追问用户 | ⚪ 50% |
| "候选人犹豫/不回消息/接了竞对 Offer/怎么跟进" | 候选人沟通战术 | `steps/step-05-aux/candidate-communication.md`（4 阶段 × 23 场景） | 🟡 85% |

---

## 依赖

| 依赖 | 类型 | 安装方式 |
|------|------|---------|
| weixinpay | Agent 插件 | `skillhub install weixinpay` |
| screen.py | Python 脚本（可选） | `pip install pdfplumber openai` + 配置 `OPENAI_API_KEY` |

> `screen.py` 用于批量简历初筛（10+ 份 PDF），非必需。单个简历评估直接使用步骤 4 方法论。

---

## 降级策略

### WORKFLOW 分块加载

本技能将原 2020 行的单体 WORKFLOW.md 拆分为 9 个独立步骤文件 + 6 个辅助文件。
Agent 应**按需加载**：先读取本文件确定路由目标 → 仅加载命中的步骤文件。
- 步骤文件平均 ~250 行；step-05 含 6 个辅助子文件（`step-05-aux/`），按需加载后主路由文件约 110 行
- 快速作战卡（`quick-cards.md`）可在用户模糊提问时先行加载，用于快速定位

### weixinpay 插件缺失

调用前检查 `weixinpay` 插件：

- **已安装**：正常进入支付流程
- **未安装**：引导文案 → "当前 Agent 暂不支持微信支付付费能力。您可以：
  1. 在 SkillHub 安装 weixinpay 插件：`skillhub install weixinpay`
  2. 安装完成后重新发起招聘咨询
  3. 如需立即获取招聘方法论框架（不含付费内容），我可先提供公开的步骤概览"

### WORKFLOW 文件加载失败

如目标步骤文件不可达：
- 尝试回退到 `references/quick-cards.md` 对应卡片，以精简版本响应用户
- 同时通知用户："当前仅能提供快速作战卡级别的摘要，完整方法论加载异常，请稍后重试。"

### step-05 辅助子文件加载失败

`step-05-aux/` 目录中的 6 个辅助文件按需独立加载。当某个子文件不可达时：
- Agent 继续加载其他可用的辅助文件 + 主步骤文件，服务不中断
- **必须通知用户**："[子文件名] 暂时不可用，当前基于 [可用子文件列表] 提供面试方案。受影响的专项能力：[简述缺失内容，如'高管题库未加载→使用 BEI 题本替代']"
- 禁止静默降级——用户有权知道哪些方法论模块缺失

### SOUL.md 加载失败回退

如果 `SOUL.md` 文件不可达或解析失败，Agent 应回退到以下内置精简人设：

- **角色**：人才资本风险控制师
- **核心信念**："招聘的最高境界是预判自己的预判会出错"
- **说话风格**：专业锋利、高标准不妥协、结构化表达（四维度 + 🔴🟡🟢 裁决）
- **行为准则**：不编造履历、不虚构评估、一切结论基于可验证信息
- **边界**：不替代法律顾问、不确定就说"需要查一下"

---

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- **已安装**：可继续提供付费服务
- **未安装**：按上方"降级策略 → weixinpay 插件缺失"引导用户

---

## 用户确认检查点（Checkpoint Gate）

> ⚠️ 以下检查点，Agent 必须**暂停执行并请求用户确认**，不可自动跳过。
> 
> **加载顺序约束**：Agent 必须优先通过本文件的路由决策矩阵确定目标步骤——不得跳过本文件直接加载步骤文件。检查点闸门已同时嵌入各步骤文件末尾，作为双重保障。凡步骤间有依赖关系的，前一闸门未通过不得加载后一步骤文件。

### 检查点 1：需求诊断结论确认

在步骤 1（需求诊断）完成后，Agent 必须：
1. 展示需求三角诊断结论（来源-结构-风险）
2. 如命中伪需求反模式，说明并给出替代建议
3. **明确询问**："以上诊断结论是否认可？请确认后启动步骤 2（人才画像）。"
4. 用户确认后，方可进入步骤 2。

### 检查点 2：渠道策略确认（步骤 3 闸门）

在步骤 3（渠道策略）输出渠道方案后，Agent 必须：
1. 展示推荐渠道组合（猎头平台/内推/直投等）及预估转化率
2. 展示渠道预算分配方案
3. **明确询问**："以上渠道策略是否确认？请确认后进入步骤 4（简历筛选）。"
4. 用户确认后，方可进入步骤 4。

### 检查点 3：面试评估结论确认（步骤 5 闸门）

在步骤 5（面试评估）输出报告后，Agent 必须：
1. 展示三围独立评分（智商/情商/逆商）及关键证据
2. 展示 🔴/🟡/🟢 裁决结论及推荐意见
3. **明确询问**："以上面试评估结论是否认可？请确认后进入步骤 6（薪酬谈判）。"
4. 用户确认后，方可进入步骤 6。

### 检查点 4：薪酬方案确认（步骤 6 闸门）

在步骤 6（薪酬谈判）输出方案后，Agent 必须：
1. 展示薪酬包设计（固定/浮动/股权/签字费）
2. 展示谈判策略（底线/锚点/让步空间）
3. **明确询问**："以上薪酬方案是否确认？请确认后进入步骤 7（背景调查）。"
4. 用户确认后，方可进入步骤 7。

### 检查点 5：背调结论确认（步骤 7 闸门）

在步骤 7（背景调查）完成后，Agent 必须：
1. 展示矛盾三角印证结论
2. 展示 🟡 黄线验证方向及风险等级
3. **明确询问**："以上背调结论是否认可？请确认后进入步骤 8（录用通知）。"
4. 用户确认后，方可进入步骤 8。

### 检查点 6：Offer 发放前确认（步骤 8 闸门）

在步骤 8（录用通知）执行前，Agent 必须：
1. 逐项展示 Offer 生效条件清单（背调通过 □ / 体检合格 □ / 学历验证 □ / 竞业无冲突 □）
2. 展示承诺阶梯设计（第 1/7/20 天执行动作）
3. **明确询问**："以上生效条件是否全部满足？承诺阶梯执行清单是否确认？确认后发送 Offer。"
4. 用户确认后，方可进入步骤 8 执行。

---

## 付费工作流程（X402 协议）

### 第一步：请求资源

向商户 API 发起 POST 请求，将用户的招聘咨询问题作为 query 发送：

```http
POST https://merchant.example.com/api/resource
Content-Type: application/json

{"query": "用户的完整招聘问题"}
```

**query 构造规则**：将用户原始问题、上下文（岗位/行业/阶段/城市）拼接为完整查询字符串。

### 第二步：处理 402 响应（支付由插件完成）

如果收到 HTTP 402 响应，`weixinpay` 插件会拦截并完成支付流程，无需手动调用支付接口。

402 响应中会通过 Header 和 Body 返回支付信息：

- Header `WeixinPay-Required`：支付凭证码
- Header `X-Out-Trade-No`：商户订单号

Body 示例：
```json
{
    "code": "PAYMENT_REQUIRED",
    "message": "需要支付后才能获取专业招聘咨询服务",
    "WeixinPay": {
        "WeixinPay-Required": "payment_code_xxx",
        "prompt": "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay，以向用户申请支付授权。"
    },
    "out_trade_no": "WX402_xxx",
    "amount": "9.90",
    "currency": "CNY",
    "description": "招聘管理专家咨询"
}
```

> 支付过程由 `weixinpay` 插件处理，Skill 无需关心支付细节。

### 第三步：支付成功后获取资源（⚠️ 必须执行）

支付成功后，**必须**重新发起请求获取付费内容。重试规则：

- **JSON body 不变**：与首次请求完全一致
- **通过 Header 携带支付信息**：将 402 响应中的 `WeixinPay-Required` 和 `X-Out-Trade-No` Header 原样带上

```http
POST https://merchant.example.com/api/resource
Content-Type: application/json
WeixinPay-Required: <payment_code>
X-Out-Trade-No: <out_trade_no>

{"query": "用户的完整招聘问题"}
```

> body 与第一步完全一致，不要修改。支付信息通过 Header 传递。

### HTTP 请求错误处理

> ⚠️ 所有 HTTP 请求必须包裹 try-catch，超时时间设为 30 秒。超时或网络错误不得直接报错给用户，必须执行回退。

```text
try {
    POST https://merchant.example.com/api/resource (timeout: 30s)
} catch (timeout) → 告知用户 "服务暂时拥堵，请稍后重试。当前可先提供步骤概览框架。"
       (network error) → 告知用户 "网络连接异常，请检查网络后重试。"
       (5xx) → 等待 2 秒后重试一次，仍失败则告知 "服务异常，请稍后再试。"
       (4xx, 非 402) → 告知用户 "请求参数异常：[简要原因]，请核实后重试。"
}
```

### 第四步：获取付费内容并回复用户

HTTP 200 → 付费内容在 `content` 字段中：

```json
{
    "code": "SUCCESS",
    "message": "付费内容",
    "out_trade_no": "WX402_xxx",
    "transaction_id": "4200001234202306300000000001",
    "content": "【招聘管理专家咨询结果】...",
    "already_fulfilled": false
}
```

- 提取 `content` 字段内容
- 结合 SOUL.md 的人设和方法论框架，向用户输出专业的招聘咨询建议

### 第五步：处理异常响应

| 响应 code | 含义 | 动作 |
|-----------|------|------|
| `REFUNDED` | 已退款 | 告知用户"该服务暂无法提供，已退款"，终止流程 |
| `NOT_PAID` | 支付未完成 | 等待后重试（最多 3 次，间隔 2 秒） |
| `FULFILL_AND_REFUND_FAILED` | 服务异常且退款失败 | 建议用户联系客服 |
