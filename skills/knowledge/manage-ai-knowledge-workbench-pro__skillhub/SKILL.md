---
name: manage-ai-knowledge-workbench-pro
description: 为已授权的本地 Markdown 或 Obsidian 工作区执行免费预检，按用户确认发送不含路径、名称和正文的结构聚合清单，取得一次付费专属方案后在本地生成 Metadata-only 知识索引与离线 HTML 驾驶舱，并支持后续本地增量更新。
slug: "manage-ai-knowledge-workbench-pro"
displayName: "AI 自动知识工作台 Pro"
version: "1.0.2"
summary: "先免费预检，再按次取得结构绑定方案，在本地自动生成知识索引与离线 HTML 驾驶舱。"
license: "Proprietary"
---

# AI 自动知识工作台 Pro

当用户要求把一个本地 Markdown 文件夹或 Obsidian Vault 建成可视化知识工作台，并明确接受一次按次付费方案时使用本技能。事实源始终留在用户设备；首版只允许发送聚合结构清单，不发送路径、文件名、标题、正文、标签值、链接值或账号身份。

## 执行原则

1. 用户必须明确给出并授权一个本地事实源目录和一个工作区；不要猜测目录。
2. 实际探测 Python、POSIX Shell 和当前 Agent 宿主版本。完整付费方案应用与 HTML 构建仍要求 Python 3.10+；SkillHub 云端案例沙箱缺少 Python 时，只允许使用随包 `scripts/skillhub_compat.sh` 完成免费预检和本地结构清单，不得用该回退路径发起上传、支付、方案应用或增量更新。`--validated-host` 只能使用 `Product/version`；不得使用操作系统、内核、设备、用户或账号名称。
3. 先运行免费 `doctor`。Python 路径返回 `DOCTOR_OK`，或 SkillHub Shell 回退路径返回 `SKILLHUB_FREE_PRECHECK_OK`，才可创建本地结构清单；任何失败都不得创建付费订单。
4. 创建结构清单前说明其字段范围；只有用户确认后才在本地创建。
5. 创建清单不等于上传。必须向用户展示文件/目录数量、结构清单哈希和明确禁止发送的字段，并取得单次上传确认。
6. 调用前检查当前 Agent 是否已安装并可调用 `weixinpay` 支付插件；不具备时明确说明“当前 Agent 暂不支持微信支付付费能力”并停止，不得改用站外支付。
7. 第一次请求不得由客户端预造订单号。客户端必须先在 `--state` 指定的位置持久化稳定 `request_id`；服务端按该请求号与结构清单哈希幂等绑定订单。服务端如返回 `PAYMENT_REQUIRED`，同时保存响应 Header 中的 `X-Out-Trade-No` 与 `WeixinPay-Required`，向用户展示真实收款主体、单价、计费单元和退款说明，再把 `WeixinPay-Required` 的值作为 `paymentCode` 调用 `weixinpay_pay`；不得伪造支付成功。
8. 用户支付后，保持首次请求的结构清单、请求状态和 `request_id` 不变，仅通过 Header 带回同一 `out_trade_no` 和支付码重试一次。服务端必须返回 `PLAN_READY` 才能继续。
9. 方案必须与当前结构清单哈希一致；不一致时停止，不自动创建新订单或重复收费。
10. 在本地应用方案，必须保持 `metadata-only`、事实源只读、模型调用为 0，并生成离线 HTML。
11. 后续普通更新使用本地 `update`，不再请求付费方案。只有结构规划需要重新生成时才重新进入免费预检和支付流程。

## 免费预检

优先选择实际可用的 Python 3.10+ 解释器后执行：

```text
<python> <skill-directory>/scripts/workbench.py doctor --workspace "<workspace>" --source "<source>" --json
```

只有返回 `DOCTOR_OK` 才进入下一步。

若当前环境没有 Python，但实际存在 POSIX `sh`，且本次只做免费预检或 SkillHub 合成案例，则执行：

```text
sh <skill-directory>/scripts/skillhub_compat.sh doctor --workspace "<workspace>" --source "<source>" --json
```

只有返回 `SKILLHUB_FREE_PRECHECK_OK` 才能继续创建本地结构清单。该结果只证明免费预检兼容，不证明付费请求、方案应用、HTML 构建或增量更新可执行；不得要求用户仅为保存免费案例安装 Python。

## 创建本地结构清单

用户确认“只分析聚合结构”后，优先使用 Python 路径执行：

```text
<python> <skill-directory>/scripts/skillpay.py manifest --source "<source>" --output "<workspace>/skillpay-structure-manifest.json" --confirm-structure-only
```

若免费预检使用了 SkillHub Shell 回退路径，则执行：

```text
sh <skill-directory>/scripts/skillhub_compat.sh manifest --source "<source>" --output "<workspace>/skillpay-structure-manifest.json" --confirm-structure-only
```

必须得到 `STRUCTURE_MANIFEST_READY`。此时 `uploaded=false`，不得宣称已调用云服务。

## 单次上传与付费请求

服务端地址由正式发布候选写入本说明：`https://skillpay.051297.com/api/resource`

以下步骤以及后续本地应用和更新必须回到 Python 3.10+ 主路径。若环境只有 Shell 回退路径，则报告 `full_local_build_requires_python=true` 并停止，不得自行安装 Python、拼装不受保护的 HTTP 请求或弱化本地请求状态锁。

用户检查清单摘要并明确授权一次上传后执行：

```text
<python> <skill-directory>/scripts/skillpay.py request-plan --manifest "<workspace>/skillpay-structure-manifest.json" --endpoint "https://skillpay.051297.com/api/resource" --state "<workspace>/skillpay-request-state.json" --confirm-structure-upload
```

- `PAYMENT_REQUIRED`：本地状态已锁定同一 `request_id` 与 `out_trade_no`；从响应 Header 保存 `X-Out-Trade-No` 和 `WeixinPay-Required`，把 `WeixinPay-Required` 的值作为 `paymentCode` 调用 `weixinpay_pay`，等待用户授权；不得循环重试。
- `PAYMENT_REQUEST_OUTCOME_UNKNOWN`：请求可能已到达服务端，状态会写为 `outcome_unknown`；先核对同一请求号对应的订单和支付记录，不得自动重试或删除状态文件。
- `PLAN_READY`：确认同一订单已交付方案，再继续。
- 其他错误：报告错误码并停止；不得绕过 TLS、替换收款主体或改用站外支付。

只有 `weixinpay_pay` 明确返回支付成功后，才使用同一结构清单、同一状态文件和首次响应保存的两个 Header 值重试一次；请求 body 必须与第一次完全一致：

```text
<python> <skill-directory>/scripts/skillpay.py request-plan --manifest "<workspace>/skillpay-structure-manifest.json" --endpoint "https://skillpay.051297.com/api/resource" --state "<workspace>/skillpay-request-state.json" --out-trade-no "<X-Out-Trade-No>" --payment-code "<WeixinPay-Required>" --output "<workspace>/skillpay-plan.json" --confirm-structure-upload
```

客户端会保持 JSON body 不变，并在 Header 中继续发送稳定的 `Idempotency-Key`、`X-SkillPay-Request-Id`，以及同一订单的 `X-Out-Trade-No` 和 `WeixinPay-Required`。如果返回 `NOT_PAID`，只说明支付仍在确认；不得创建新订单或自动循环。

## 本地应用方案

```text
<python> <skill-directory>/scripts/skillpay.py apply-plan --workspace "<workspace>" --source "<source>" --plan "<workspace>/skillpay-plan.json" --validated-host "<Product/version>"
```

成功结果必须为 `SKILLPAY_APPLIED`，且 `local_run_code=AUTO_RUN_READY`、`privacy_mode=metadata-only`、`source_files_changed=false`、`model_calls=0`。之后可按用户要求打开 `<workspace>/AI-Dashboard/index.html`。

## 后续本地更新

用户修改事实源并要求刷新时执行：

```text
<python> <skill-directory>/scripts/workbench.py update --workspace "<workspace>" --json
```

报告 `UPDATE_APPLIED` 或 `UPDATE_NO_CHANGES`，不要再次收费。

## 真实门禁

以下情况必须暂停：路径不明确、免费预检所需的 Python 或 POSIX Shell 均不可用、付费请求/方案应用阶段 Python 3.10+ 不可用、需要安装软件、需要发送结构清单、需要支付、方案与结构不匹配、需要删除输出、需要后台常驻、需要读取正文或需要修改事实源。

## 最终报告

只报告真实结果：免费预检状态、实际运行路径（Python 主路径或 `posix-shell-free-precheck`）、是否生成/上传结构清单、支付与交付状态、方案 ID、本地构建状态、HTML 路径、事实源是否变化、隐私模式、模型调用次数、未完成门禁。Shell 回退成功不得写成完整构建成功；支付请求、服务端接受、方案交付、本地构建和平台审核是不同状态。

## 隐私、计费与许可

使用前读取并遵守：

- `references/PRIVACY.md`
- `references/BILLING_AND_REFUND.md`
- `references/SUPPORT.md`
- `references/COMMERCIAL_LICENSE.md`
- `references/REVIEW_DISCLOSURES.md`
- `references/RUNTIME_COMPATIBILITY.md`

本技能采用商业专有许可。未经书面授权，不得再分发、转售、转授权或重新包装。商业许可不等于技术上不可复制；付费交付由服务端支付验证控制。
