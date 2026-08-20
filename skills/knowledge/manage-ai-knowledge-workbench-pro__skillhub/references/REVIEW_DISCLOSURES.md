# 审核与公开披露

- 本技能会读取用户明确授权的本地目录。完整付费交付执行随包 Python 脚本；SkillHub 云端案例沙箱缺少 Python 时，仅执行随包 POSIX Shell 免费预检与结构清单脚本。
- 创建聚合结构清单后，只有用户再次确认才会访问正式 HTTPS 服务。
- 首版不发送笔记正文，不调用云端模型，不使用模型 Token。
- 本地生成目录为 `.ai-workbench/`、`AI-Knowledge/` 和 `AI-Dashboard/`；事实源默认只读。
- 不自动安装依赖、不提权、不下载远程脚本、不创建后台常驻项、不使用站外支付。
- POSIX Shell 兼容层不发送网络请求、不触发支付、不应用方案、不生成 HTML；它只输出 `SKILLHUB_FREE_PRECHECK_OK` 和本地 `STRUCTURE_MANIFEST_READY`。
- 正式 HTTPS 服务 `https://skillpay.051297.com/api/resource` 使用 SkillHub 开发者 RSA 签名调用 X402 AI 预下单；首次响应同时返回 HTTP 402、`WeixinPay-Required` 和 `X-Out-Trade-No`，支付后仅携带同一订单号和支付码重试原请求。
- Skill 明确调用 `weixinpay_pay(paymentCode=...)` 触发微信支付授权；支付结果只以微信支付回调或主动查单为准。
- 支付、方案交付、本地构建和平台审核是不同状态。
- 展示案例全部使用合成数据，并标注“合成演示数据”。
- 不宣称兼容所有智能体、绝对安全、永久更新或腾讯官方推荐。
