---
name: api-image
description: Generate or edit images through user-supplied API relays using Gemini-native or OpenAI-compatible image protocols. API relays are third-party gateways that often aggregate multiple models behind one Base URL and API key and may offer simpler billing or lower prices. Use for text-to-image, image-to-image, multi-reference fusion, Banana/Gemini image models, GPT Image 2, or NewAPI/One API-compatible endpoints. On first use after installation, ask for model type, Base URL, model ID, and API Key, save the configuration automatically, and generate one low-cost test image.
---

# API Image 4.0

通过用户自己的中转接口完成文生图和图生图。使用 `scripts/api_image.py` 负责配置、请求、响应解析与图片保存。

## 小白先了解：什么是中转站？

中转站是连接“用户”和“模型官方接口”的转发服务。用户把请求发给中转站，中转站再调用 Gemini、GPT Image 等模型并返回结果。通常只需一套账号和接口，就能使用多个厂商、多个模型。

人们常用中转站，主要是因为：

- **聚合多种模型**：切换模型时通常只需修改模型 ID。
- **管理更简单**：充值、余额和调用记录可以集中管理。
- **价格可能更低**：部分中转站会提供比官方直连更低的调用价格。

中转站并不等于模型官方。价格、稳定性和隐私规则由各中转站决定；提示词、参考图和生成内容会经过中转服务。提醒用户选择可信服务商并查看计费规则，但不要让安全说明阻断正常配置。

## 安装后的首次引导

第一次使用时，如果还没有配置，主动向用户发送下面的简短引导，不要先抛出命令或环境变量说明：

```text
请把下面 4 项信息发给我，我会自动完成配置并生成一张测试图：

1. 模型类型：Banana 或 GPT Image 2
2. Base URL：中转站接口地址
3. 模型 ID：中转站模型列表中的实际名称
4. API Key：中转站密钥
```

收到信息后直接执行以下流程，不再要求用户手动操作：

1. 根据模型类型确定协议：
   - Banana / Gemini 图片模型 → `gemini`
   - GPT Image 2 → `openai`
2. 运行 `configure` 保存配置。不要在回复中重复或展示完整 API Key。
3. 运行 `check` 检查配置，不访问网络。
4. 自动生成一张低成本测试图，验证真实连通性。
5. 成功后告诉用户“配置成功”以及测试图的实际保存路径；失败时说明具体原因。

配置命令由 Agent 执行：

```bash
python scripts/api_image.py configure --protocol gemini --base-url https://relay.example.com --model relay-model-id --api-key USER_KEY
```

脚本默认保存到当前用户目录的 `~/.api-image/config.json`。这是为了让小白只配置一次；不要把配置文件打包进 Skill、发送给其他人或显示其中的密钥。需要更高安全级别时，再读取 [references/protocols.md](references/protocols.md) 使用环境变量模式。

### 自动测试

Banana 配置完成后运行：

```bash
python scripts/api_image.py generate "一颗红色圆球放在纯白背景中央，简洁测试图" -o api-image-test.png --overwrite
```

GPT Image 2 配置完成后运行：

```bash
python scripts/api_image.py generate "A blue square centered on a plain white background, minimal test image" --quality low --size 1024x1024 -o api-image-test.png --overwrite
```

测试请求可能产生少量费用。用户安装后主动提供配置信息，即视为同意执行这一张测试图；不要额外连续生成多张。网络超时或结果不明确时不要自动重试，以免重复扣费。

## 日常使用

配置完成后，不需要再次传入 Base URL、模型 ID 或 API Key。

文生图：

```bash
python scripts/api_image.py generate "一只戴圆框眼镜的橘猫，编辑插画风格" -o output.png
```

图生图：

```bash
python scripts/api_image.py edit ref1.png ref2.jpg -p "保留主体特征，融合为一张自然的棚拍产品图" -o edited.png
```

旧版命令名 `reference` 仍可作为 `edit` 的别名。OpenAI 图生图必须调用 `/v1/images/edits` 并真实上传参考图，不要退化成纯文字生成。

## 核心规则

1. 不要根据模型 ID 猜协议；根据用户选择的模型类型确定协议。
2. 不要写死模型 ID；不同中转站可能使用不同别名。
3. 用户提供配置后，由 Agent 自动执行配置和一张测试图，不要把终端操作推给小白。
4. 不要在回复、日志摘要或生成报告中重复完整 API Key。
5. 图片成功后报告实际保存路径；脚本会依据真实图片字节修正文件后缀。
6. 超时或响应不明确时不要自动重试。

## 配置优先级

按以下顺序读取：命令参数 → 环境变量 → 本地配置文件 → 默认值。

需要多个中转配置、旧版 Gemini 参数结构、特殊鉴权方式或环境变量安全模式时，读取 [references/protocols.md](references/protocols.md)。

## 失败处理

- `401/403`：请用户重新核对 API Key、余额、渠道权限和模型权限。
- `404/405`：检查 Base URL、API 版本和中转是否开放对应协议。
- `400` 且涉及 Gemini 尺寸字段：在 `response-format` 与 `image-config` 之间选择中转支持的结构。
- `429/5xx`：报告限流或渠道异常，不要连续重试。
- 超时或连接中断：说明结果未知，不要自动重发。
- 成功响应没有图片：检查脱敏后的响应结构，不要把文本内容保存成图片。

## 范围

- 支持：文生图、单图/多图参考生成、OpenAI 多图编辑、PNG/JPEG/WebP 输入、Base64 或 URL 图片响应。
- 不默认提供：遮罩局部重绘、对话式多轮状态、平台专属 metadata。
- GPT Image 2 不支持透明背景；脚本会拒绝 `--background transparent`。
- 运行时需要 Python 3.9 或更高版本，仅使用标准库。
