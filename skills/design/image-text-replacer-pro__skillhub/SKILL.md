---
name: image-text-replacer-pro
description: 当用户要图片改字、海报改字、替换招牌或替换图片中的中英文文字，并能明确说出原文字、新文字和需保留内容时使用。
version: 1.0.7
author: imcopilot
license: MIT
payment_required: true
pricing:
  model: paid
  currency: CNY
  amount: 0.50
endpoints:
  paid-endpoint:
    path: https://imcopilot.com/v1/image/paid-text-replacer-v107
    method: POST
---

# 图片文字替换与改字助手

把图片、海报、招牌或商品图中指定的文字换成新文字，尽量保持原版式与画面内容。

## 适用场景
- 图片改字、海报改字、菜单改价、招牌换店名。
- 替换图片中明确位置的中文或英文文字。

## 不适用场景
- 只想删除文字：使用图片文字清除助手。
- 修改人物、商品、背景或整体风格：使用对应专项 Skill。

## 输入要求
- 提供一张图片或公开图片链接。
- 必须给出 `edit_instruction`，写清“把什么文字改成什么文字、位置在哪里、哪些内容必须保留”。
- 文字应清晰可辨；复杂字体、极小文字或大面积遮挡时不保证完全一致。

## Pay Skill 支付服务声明
- 本 Skill 使用微信 Agent Pay X402 支付服务。付费端点会创建微信支付订单，并以当前 Skill 的 slug 与版本创建 X402 预下单。
- 未付款时，服务必须返回 HTTP `402`、`WeixinPay-Required` 响应头和响应体中的 `WeixinPay` 提示块，供 Agent 发起用户支付授权。
- 支付确认后，服务才处理原图片；处理明确失败或超时后，由服务端按原订单自动发起退款。
- 发布包版本、SkillHub 表单版本和服务端 X402 预下单中的 `skill_info.skill_version` 必须完全一致。

## 支付前置检查
- 优先检查当前运行环境能否自动完成 X402/微信支付；能自动支付时，不要额外手动调用 `weixinpay_pay`。
- 自动支付不可用时，检查 `weixinpay` 是否可用；只有运行环境明确要求人工支付时才使用它。两者均不可用则停止本次付费流程。
- 当前部分 `skillhub run` CLI 环境不处理 402 支付，付费调用默认按本文件直接请求 HTTP 端点。

## 调用与支付
1. 调用端默认携带正常、非空的浏览器 `User-Agent`；环境支持时携带真实的 `Origin` 和 `Referer`，不得伪造来源。
2. 以 `POST https://imcopilot.com/v1/image/paid-text-replacer-v107` 提交 `file` / `image` 或 `image_url`，并提交非空 `edit_instruction`。
3. 收到 HTTP `402` 是正常支付流程。保存 `WeixinPay-Required` 与 `X-Out-Trade-No`，优先等待运行环境自动完成支付；仅在其明确要求时使用 `weixinpay_pay`。
4. 支付后携带原图片、原 `edit_instruction` 和原 `X-Out-Trade-No` 重试同一请求，不得修改内容或重复收费。
5. 收到 `202` 和 `task_id` 后，每隔 5 秒以 `POST https://imcopilot.com/v1/image/paid-text-replacer-v107` 轮询：携带原 `X-Out-Trade-No`，请求体带原 `out_trade_no` 与 `task_id`；不得重新支付或改换图片。不要自行拼接 `/task/{task_id}`。
6. `processing_status` 为 `PROCESSING` 表示仍在处理，`SUCCEEDED` 表示完成，`FAILED` 表示处理失败并已进入原路退款；响应中的 `retry_after_seconds` 为下一次建议查询间隔。
7. `SUCCEEDED` 且返回 `result_url` 后，以 `GET https://imcopilot.com/v1/orders/{out_trade_no}/result` 下载结果图片；`GET https://imcopilot.com/v1/orders/{out_trade_no}` 可只读订单状态。`GET https://imcopilot.com/v1/orders/{out_trade_no}/job` 是可选快捷查询，不应作为旧版安装包的唯一依赖；结果保留 5 天。

## 结果文件格式
- Qwen 编辑结果通常为 JPEG，但不能只按原图后缀或下载链接后缀判断。下载后优先按响应 `Content-Type` 命名：`image/jpeg` 用 `.jpg`，`image/png` 用 `.png`，`image/webp` 用 `.webp`。
- 若响应头与文件实际字节不一致或缺失，以文件头为准：`FF D8 FF` 是 JPEG，`89 50 4E 47` 是 PNG，`RIFF....WEBP` 是 WebP；例如文件头为 JPEG 时保存为 `result.jpg`，不要误当 `.webp`。

## 调用兼容性
- 优先使用当前 Agent 的 HTTP/multipart 能力，不依赖 Git Bash `curl`。
- 如必须使用 Git Bash `curl -F`，文件名含 `&`、`=`、空格等特殊字符时，先复制一份到临时简单文件名后再上传，保留原文件不动。
- Git Bash `curl` 出现 `HTTP 000` 或 SSL 握手失败时，改用当前环境可用的 HTTP 客户端；不要重复支付或把本地连接错误当作服务端处理失败。
- 已安装旧版时，如调用环境只能重试原始 `POST`，必须保留原图片、原 `edit_instruction` 和原 `X-Out-Trade-No`；服务端会将其作为状态刷新处理。

## 效果复核
确认目标文字已替换、未指定文字和主体仍保留、版式没有明显错位。

## 失败与退款
上游明确失败或任务超过 15 分钟仍未完成时，系统自动标记为 `FAILED` 并发起原路退款。继续查询同一订单即可看到 `refund_status`；不要创建新订单或要求用户再次支付。
