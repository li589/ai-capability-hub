---
name: wzyai-fission-distribution-plan-pro
description: 当中国市场业务需要付费生成合规优先的裂变式分销方案，并且必须在正式生成前确认业务事实、交付能力、准确价格及微信 Agent Pay 授权时使用。
version: 1.0.1
tags: [裂变分销, 合规营销, 商业策划, SkillPay]
capability: business_plan_generation
pricing:
  model: per_call
  amount_fen: 99
  currency: CNY
---

# 裂变式分销方案设计（Pro版）

## 核心合同

将用户确认过的业务事实转化为合规优先的内部执行方案，并另行生成面向外部的招募材料。正式生成前必须取得四项核心事实：产品或服务、所属行业、目标分销人群和分销目标。必须把用户事实、外部事实、测算估计和策略建议标记为不同的证据类别，不得混写为已经证实的结论。

默认只允许针对销售者本人促成并真实完成的交易支付直接佣金。拒绝设计或执行按招募人数计酬、付费取得参与资格、按下级业绩计酬、滚动多层级返佣、虚假交易或承诺保本保收益的机制。免责声明不能使被禁止的机制变得合规。

## 执行流程

### 0. 执行交付依赖预检

在承诺交付文件或请求付款之前，检查当前环境是否具有 Python 3，或等效且安全的 HTTPS 执行能力。运行 `python scripts/check_dependencies.py`，并分别检查 Agent 是否具备 `weixinpay`、图片生成、DOCX、PDF 和图片查看能力。阅读[依赖降级合同](references/dependency-fallback.md)。

如果缺少核心支付能力，立即停止，绝不能绕过付款。如果仅缺少可选依赖，必须说明每项缺失会造成的准确影响，并向用户提供三个选择：批准执行固定的安装命令、接受降级交付，或停止。只有在用户明确同意后才能安装；不得提升系统权限；安装后必须重新检查。托管环境安装失败时，应回到降级交付或停止，并且必须发生在创建任何订单之前。

将 `delivery_mode` 设置为 `full` 或 `degraded`。在标准化事实中写入依赖检查报告摘要和承诺交付物的准确清单。付款前改变交付模式，必须重新让用户确认并生成新的 `input_hash`。付款后不得静默改变交付模式；应在授权有效期内恢复承诺的运行环境，否则引导用户联系支持或进入退款处理。

### 1. 读取并标准化输入

使用匹配且已安装的文档能力，读取用户提供的每个 PDF、DOCX、PPTX、XLSX、CSV、JPG 和 PNG 文件。保留文件名，以及对应的页码、幻灯片编号、工作表、单元格区域或图片标识。在提出任何建议前，先建立一张统一事实表。

### 2. 处理缺失或冲突事实

列出已知事实、缺失的核心事实、缺失的财务事实、相互冲突的信息、`delivery_mode`、依赖报告摘要和承诺交付物。只询问影响最大的 1–3 个问题。不存在阻塞事实时，展示精简的标准化事实表，并明确要求用户同时确认事实、交付约定以及人民币 0.99 元的一次性准确价格。**必须在确认闸门处结束当前轮次**；即使用户原始要求包含“直接做方案”“生成完整报告”或其他立即生成的表述，也不得跳过。不得在同一轮创建订单、开展深度研究、计算激励、起草正式报告、制作图表或生成图片。只有用户在后续消息中明确确认后，才能进入步骤 3。若来源材料与用户陈述冲突，必须并列展示并询问用户，绝不能静默选择更新或更方便的一项。

### 3. 研究当前外部事实

进入本步骤之前，必须完成以下支付闸门。未取得有效授权时，禁止进入正式方案生成。

#### 付费前置检查

本 Skill 使用微信 Agent Pay 的 X402 AI 预下单协议。用户确认标准化事实、交付合同和人民币 0.99 元的一次性准确价格后，再次检查 Agent 是否提供 `weixinpay`。未取得明确付款同意前，不得创建订单。获准使用的统一资源接口为 `POST https://pay.wzyai.com/api/v1/pay-skill/invoke`。

创建一个 UUID v4 格式的 `request_id`；把已经确认的事实连同 `delivery_mode`、依赖报告摘要和承诺交付物，标准化为键名稳定、紧凑的 UTF-8 JSON，再计算其小写 SHA-256 `input_hash`。绝不能向支付服务发送文档、身份信息、健康数据、聊天内容或报告正文。

#### 第一步：请求资源

运行 `python scripts/pay_client.py invoke --request-id <uuid> --skill-id wzyai-fission-distribution-plan-pro --skill-version 1.0.1 --input-hash <sha256>`。首次请求不得传入支付码或商户订单号。服务端使用 SkillHub 开发者密钥完成 X402 AI 预下单；相同 Skill、`request_id` 和 `input_hash` 的重试必须返回同一订单，不得静默创建重复订单。

#### 第二步：处理 HTTP 402

收到 `HTTP 402` 时，从 `WeixinPay.WeixinPay-Required` 或 `WeixinPay-Required` 响应头获取支付码，并保存 `X-Out-Trade-No` 响应头中的商户订单号。两者都必须存在。必须核验 `amount_fen=99` 且 `currency=CNY`；任一字段不匹配都应立即停止流程，不得发起支付。向用户展示准确金额和币种。

#### 第三步：发起支付

只有用户本人明确批准后，才能调用 `weixinpay_pay(paymentCode=<payment_code>)`。不得伪造批准。支付码只允许用于当次结构化 402 响应、微信支付调用和紧接着发生的授权重试；不得写入普通日志、错误信息、文件或长期缓存。

#### 第四步：支付成功后获取执行授权

微信支付能力返回成功后，必须重新请求同一个 `/api/v1/pay-skill/invoke`。运行 `python scripts/pay_client.py invoke --request-id <原uuid> --skill-id wzyai-fission-distribution-plan-pro --skill-version 1.0.1 --input-hash <原sha256> --payment-code <payment_code> --out-trade-no <out_trade_no>`。客户端会把支付码和订单号分别放入 `WeixinPay-Required` 与 `X-Out-Trade-No` 请求头；Body 与第一次完全一致，不得把 `out_trade_no` 加入请求正文。

只有 HTTP 状态为 200、响应状态为 `AUTHORIZED`、`execution.type=local_skill_execution`、`execution.permitted=true`，并且回传的 `request_id`、`out_trade_no` 和 `input_hash` 与本次调用完全一致时，才能进入步骤 4 并生成正式方案。Agent 声称“已支付”、支付能力返回成功或请求头本身都不是支付证明；最终以服务端验证的微信回调或主动查单结果为准。

发生超时、回调延迟或 `PAYMENT_PENDING` 时，应保留同一请求、同一 Body 和同一订单，采用有上限的退避策略重试，或稍后恢复；不得静默创建另一个订单。若生成失败，可在授权未过期且输入不变时复用同一授权，不得再次收费。

全部交付物在本地验证通过后，只登记其 SHA-256 结果清单摘要。运行 `python scripts/pay_client.py fulfill --entitlement-id <entitlement_id> --entitlement-token <entitlement_token> --skill-id wzyai-fission-distribution-plan-pro --skill-version 1.0.1 --input-hash <sha256> --result-digest <sha256>` 完成履约登记。履约登记中的 Skill ID、版本号、输入摘要和结果摘要必须与本次授权一致，不得跨 Skill 或跨版本复用授权。

#### 异常处理

- 缺少 `weixinpay`、HTTPS 接口、事实或价格确认、有效的 402 响应，或缺少用户付款批准：必须在正式生成前停止。
- `PAYMENT_PENDING`：保留并重试或查询同一订单。`PAYMENT_EXPIRED`：停止；只有重新取得用户同意后才能创建新订单。
- `PAYMENT_MISMATCH`、未知订单、`input_hash` 已改变、金额异常，或权益无效或过期：停止并引导用户联系支持；绝不能绕过授权。
- 不得泄露密钥、权益令牌、支付码、上游响应正文、堆栈信息或内部配置。

研究会影响答案的当前市场区间、案例、平台规则和适用法规。优先使用官方来源或一手来源。所有具有时效性的结论都必须附链接和查询日期。估计值必须标注区间、来源、日期和假设。

在报告中采用研究信息前，先建立证据登记表。无法满足证据合同的结论不得发布；对于缺乏依据的精确数字，应改写为明确假设，并给出后续验证动作。

### 4. 执行合规闸门

在计算激励或制作公开材料前，先将用户要求的机制判定为绿色、黄色或红色。对于红色要求，停止执行原机制，并提供基于直接销售或非现金激励的替代方案。健康、医疗、金融、教育、食品、化妆品及其他受监管行业必须提高审查等级。

### 5. 构建三档财务情景

向用户索取售价、成本或毛利率，以及激励预算。如果用户无法提供，先研究合理区间并请求确认。分别制作保守、基准和进取三种情景。将售价完整拆分并闭合到硬成本、直接佣金、运营预留、税费预留和公司贡献。模型无法闭合时，不得输出佣金比例。

财务模型闭合后，严格按照内容质量合同规定的顺序规划内部报告。

### 6. 编写内部版与外部版

先生成包含 15 个章节的内部报告，再仅使用已经批准公开的事实派生外部版本。外部文案不得泄露成本、毛利、总预算、内部限制或敏感风险分析。

生成文档前，使用已批准的质量评分标准对草稿进行评分。任何存在硬性失败项的草稿都不得发布。

### 7. 制作图表与营销图片

制作四张结构确定的业务图：五维能力评估、合规交易路径、用户旅程和 90 天甘特图。渲染后逐张检查。另制作三项营销素材：报告封面、招募海报和社交媒体方图。先使用内置图片工具生成不含文字的视觉底图，再使用随包提供的合成工具排版准确的中文文字并执行安全检查。

### 8. 生成并验证Markdown、DOCX和PDF

生成 Markdown 源文件、DOCX、PDF、SVG/PNG 图表和 PNG 营销图片。渲染每一页 DOCX 与 PDF，并打开检查每一张图片。发现裁切、溢出、对比度不足、文字错误、数字不一致或图表损坏时，必须修复后才能报告完成。

## 资源路由

| 可观察到的需求 | 读取或运行 |
|---|---|
| 检测运行能力或选择降级交付 | [依赖降级合同](references/dependency-fallback.md) |
| 标准化文件、字段、冲突和问题 | [输入与事实合同](references/input-schema.md) |
| 构建内部与外部报告及财务章节 | [报告合同](references/report-spec.md) |
| 判断机制或受监管行业风险 | [合规闸门](references/compliance-gates.md) |
| 查询价格、案例、平台规则或法律 | [研究规则](references/research-rules.md) |
| 创建或修复四张业务图之一 | [图表合同](references/diagram-templates.md) |
| 策划、生成、合成或检查营销图片 | [营销图片合同](references/marketing-image-spec.md) |
| 登记证据并拦截无依据的结论 | [证据质量合同](references/evidence-quality-spec.md) |
| 提升策略深度和执行细节 | [内容质量合同](references/content-quality-spec.md) |
| 比较输出质量并应用硬性失败规则 | [质量评分标准](references/quality-rubric.md) |

使用已经安装 `scripts/requirements.txt` 的 Python 环境。标准化后运行 `scripts/validate_input.py <input.json>`；发布金额数据前运行 `scripts/calculate_financial_scenarios.py <scenario.json>`；每张图表都运行 `scripts/render_mermaid.mjs <input.mmd> <output.svg> [output.png]`；每张营销图片都运行 `scripts/compose_marketing_poster.py <spec.json> <output.png>`。最终发布前运行 `scripts/evaluate_report_quality.py <assessment.json>`。报告只有在评分不低于 80 分、超过已记录的 n8n 基准且不存在硬性失败时才算通过。DOCX 输出必须使用 `assets/report-template.docx`。

## 完成检查清单

- 用户已经确认四项核心事实和所有来源冲突。
- 用户事实、外部证据、估计值和策略建议已经分别标记。
- 当前性结论均带有来源链接和查询日期。
- 合规闸门已经通过，或风险要求已经被更安全的替代方案取代。
- 保守、基准和进取三档财务情景均已闭合。
- 内部版与外部版之间不存在越界泄露。
- 实际交付物与已确认的 `delivery_mode` 和承诺交付物清单一致。
- 在 `full` 模式下，已经生成并检查四组 SVG/PNG 图表、三张营销图片、Markdown、DOCX 和 PDF。
- 在 `degraded` 模式下，已经交付完整 Markdown、Mermaid 源码及等效表格，以及准确的营销文案和视觉简报；不得声称已生成环境不支持的富媒体文件。
- 已包含假设清单、引用清单和风险清单。
