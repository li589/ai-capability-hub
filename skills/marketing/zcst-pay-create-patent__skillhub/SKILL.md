---
name: zcst-pay-create-patent
description: 科技专利写作，面向企业研发团队、高校科研人员、科研院所及专利代理机构，将发明构思转化为专利申请书初稿。支持技术方案梳理、权利要求与说明书撰写、附图说明、LaTeX公式生成，并交付Markdown和Word文档。
---

# 科技专利写作

## 从发明构思到专利申请书初稿

ScholarForce AI 面向企业研发团队、高校科研人员、科研院所、科技成果转化团队、专利代理机构、产业园区和创新服务平台，将技术方案梳理、相关学术文献理解、技术差异化分析、权利要求布局、说明书撰写、附图说明和 Word 排版交付串联为一条自动化专利写作工作流。


## 适用场景

- 企业研发部门提高专利初稿产出效率；
- 高校课题组、科研院所整理科研成果；
- 科技成果转化团队梳理技术交底；
- 专利代理机构进行前置材料整理和初稿辅助；
- 产业园区、创新服务平台提供专利写作辅助能力。

## 核心特色

- 从发明名称、技术问题、核心技术方案和应用场景出发，辅助整理专利技术交底；
- 对相关学术论文和专利资料进行多源检索、理解、去重和相关性排序，辅助识别技术共识与差异化方向；
- 围绕技术方案进行权利要求布局，生成权利要求书和说明书初稿；
- 软件类技术可生成带步骤编号（如 S101、S102）的流程图方案；
- 机械类技术可生成带零件标号（如 10、20、30）的结构示意图方案；
- 涉及算法、模型或控制方法时，可生成问题形式化定义、目标函数、约束条件、复杂度分析等 LaTeX 数学表达；
- 输出 Markdown 正文、Word（DOCX）申请书初稿、权利要求、说明书、附图说明和可用的下载链接；
- 在生成流程末端进行 AI 生成痕迹检查、术语一致性检查和合规性辅助审计，提升初稿的可审查性。

相关文献、专利检索、附图生成和公式分析能力取决于上游服务的实际可用数据源与返回结果。检索结果、技术事实、文献引用、公式推导、附图标号和申请文件格式仍需由专业人员复核；本 Skill 不保证专利授权或正式申报结果。

## 价格与生成周期

单次价格为 **9.9 元**。使用商户服务完成支付、创建专利任务和最长 30 分钟的短请求轮询；典型生成周期约为 15 分钟，实际时间取决于技术方案复杂度、检索范围、附图生成和上游服务状态。

如果任务明确生成失败，服务会进入退款处理流程。退款以微信支付和商户服务返回的最终状态为准；退款处理中应保留原订单并继续查询，不能重复支付或创建新订单。


## 收集输入

整理并展示以下字段：

- `message`：必填，最多 500 字符。简洁包含专利名称或主题、技术领域、现有问题、技术方案、关键结构或步骤、有益效果和实施方式。
- `patent_type`：必填；用户未指定或无法判断时使用 `auto`。
- `email`：选填；未提供时使用空字符串，请求始终包含该字段。

`patent_type` 只允许 `auto`、`software`、`mechanical`、`process`。只接受纯文本，不上传附件。不得虚构实验数据、性能指标、发明人或申请人信息。

信息不足时，一次性询问技术问题、核心方案、关键步骤或结构及预期效果。调用前展示最终三个参数，取得用户明确确认。该确认授权把技术方案和邮箱发送给商户服务并创建 9.9 元支付订单，但不等同于支付授权。

未取得确认时停止，并使用：

```text
⚠️ 危险操作检测！
操作类型：提交付费专利生成请求
影响范围：将技术方案和邮箱字段发送给外部商户服务，并创建 9.9 元微信支付订单
风险评估：支付成功后会创建专利任务并消耗服务额度，技术方案将发送给专利生成服务处理

请确认是否继续？请明确回复“确认”或“继续”。
```

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已安装 `weixinpay` 插件：

- 已安装：继续提供付费服务。
- 未安装：提示“当前 Agent 暂不支持微信支付付费能力”，终止流程。

## 工作流程

### 第一步：请求资源

直接调用以下商户支付服务；不要直接调用上游专利接口，也不要只访问域名根路径：

```http
POST https://skillpay.digicarbon.cn/api/skills/zcst-pay-create-patent/resource
Content-Type: application/json
```

Body 必须使用以下结构；`email` 未提供时传空字符串：

```json
{
  "input": {
    "message": "<message>",
    "patent_type": "<patent_type>",
    "email": "<email>"
  }
}
```

首次请求不得携带 `X-Out-Trade-No`，服务应返回 HTTP 402。在支持 Python 的环境中，可以执行 `scripts/request_paid_patent.py` 实现完全相同的 POST 请求；脚本只是 HTTP 调用实现，不能替代本节定义的接口、Header 和 Body 契约。

### 第二步：处理 402 响应

收到 HTTP 402 后，提取并保存以下两个值，缺少任意一个都必须停止：

- Header `WeixinPay-Required`（支付码）；兼容读取 Body `WeixinPay.WeixinPay-Required`。
- Header `X-Out-Trade-No`（商户订单号）；兼容读取 Body `out_trade_no`。

### 第三步：发起支付

将 `WeixinPay-Required` 的值作为 `paymentCode` 调用 `weixinpay_pay`，由用户完成独立支付授权。保存原始 Body、支付码和订单号，不要仅凭 Agent 文本判断支付成功。

### 第四步：支付成功后获取资源（⚠️ 必须执行）

支付成功后必须重新调用同一个完整地址：

```http
POST https://skillpay.digicarbon.cn/api/skills/zcst-pay-create-patent/resource
Content-Type: application/json
WeixinPay-Required: <第二步保存的支付码>
X-Out-Trade-No: <第二步保存的订单号>
```

Body 必须与第一次请求完全一致：

```json
{
  "input": {
    "message": "<原始message>",
    "patent_type": "<原始patent_type>",
    "email": "<原始email>"
  }
}
```

不得修改参数、创建新订单或并发运行。若返回 HTTP 202 且 `code=FULFILLMENT_IN_PROGRESS`，优先按照响应头 `Retry-After`、其次按照 Body 的 `retry_after` 等待；使用完全相同的地址、两个 Header 和 Body 顺序轮询，最长 1800 秒。HTTP 202 不是失败，也不是重新创建任务或重新支付的理由。

在支持 Python 的环境中，使用原参数执行 `scripts/request_paid_patent.py`，并传入 `--payment-code`、`--out-trade-no` 和 `--response-file`；脚本会完成上述支付后重试和短轮询。中断后仍使用原参数、原订单号和原响应文件路径恢复，禁止重新创建任务。

## 本地交付

商户服务返回 HTTP 200 且 Body `code=SUCCESS` 后，执行：

```powershell
& "<python-path>" "<skill-dir>/scripts/deliver_patent.py" `
  --response-file "<workspace>/work/pay-patent-response.json" `
  --expected-out-trade-no "<out_trade_no>" `
  --output-dir "<workspace>/outputs"
```

交付脚本原样保存响应中的 Markdown，并从受信任的官方地址下载 DOCX，不发送 API Key。向用户提供 Markdown、DOCX 和响应 JSON 的绝对可点击路径，不要把完整专利正文重复粘贴到聊天中。

提醒用户：“专利内容由自动化服务生成，正式申请前应由专利代理师或专业人员核验技术事实、权利要求范围、附图、格式及可专利性。”

## 异常处理

- `NOT_PAID`：保留原订单，短暂等待后原样重试。
- `FULFILLMENT_IN_PROGRESS`：脚本自动继续轮询，不并发调用。
- 网络中断：保留原订单，禁止重新支付或创建新订单。
- `REFUNDING`：保留原订单，稍后原样查询退款状态。
- `REFUNDED`：告知用户已退款并停止。
- `ORDER_NOT_PAYABLE`：确认用户未支付后才允许创建新订单。
- `DELIVERY_STATE_UNAVAILABLE` 或 `FULFILLMENT_STATE_UNAVAILABLE`：使用原订单稍后重试，不重新支付。
- DOCX 下载失败：保留响应 JSON 和已生成 Markdown，稍后重新运行交付脚本。
- 其他失败：报告稳定错误码和公开消息，不伪造专利内容。
