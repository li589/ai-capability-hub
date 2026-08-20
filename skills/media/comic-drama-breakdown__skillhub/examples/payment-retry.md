# SkillPay 首次调用与支付后重试

发送前，将 `{{invocationId}}` 替换为本次调用新生成的 UUID v4。支付完成后，使用同一个 URL、同一个请求 body 和同一个 invocation ID，并原样回传 402 响应中的两枚支付 Header。

```http
### 1. 首次调用：只返回 402，不扣款，也不执行 upstream
POST https://skillpay.zha-ji.cn/api/skillpay/v1/skills/comic-drama-breakdown/invoke
Content-Type: application/json
X-SkillPay-Invocation-Id: {{invocationId}}

{
  "schema_version": "1.0",
  "source_text": "林夏在深夜办公室发现合同被人替换，她决定追查真相并保护团队。",
  "genre": "都市悬疑",
  "visual_style": "电影感写实",
  "target_duration_seconds": 60,
  "language": "zh-CN",
  "constraints": {
    "max_characters": 8,
    "max_scenes": 8,
    "max_storyboards": 12
  }
}

### 2. 将 402 的 WeixinPay-Required 交给支付插件；授权成功后原样回传两枚 Header
POST https://skillpay.zha-ji.cn/api/skillpay/v1/skills/comic-drama-breakdown/invoke
Content-Type: application/json
X-SkillPay-Invocation-Id: {{invocationId}}
WeixinPay-Required: <exact-value-from-402-response-header>
X-Out-Trade-No: <exact-value-from-402-response-header>

{
  "schema_version": "1.0",
  "source_text": "林夏在深夜办公室发现合同被人替换，她决定追查真相并保护团队。",
  "genre": "都市悬疑",
  "visual_style": "电影感写实",
  "target_duration_seconds": 60,
  "language": "zh-CN",
  "constraints": {
    "max_characters": 8,
    "max_scenes": 8,
    "max_storyboards": 12
  }
}
```
