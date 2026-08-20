---
name: baobiao-structure-bid-text
description: "甄别文本属于标讯、拟在建、非项目或异常信息，推理招中标分类，并从标题和正文抽取结构化字段。用于标讯文本清洗、项目识别、公告分类、训练数据加工、字段抽取和招投标内容标准化。"
---

# 招投标文本结构化与项目甄别

## 目标

按“先甄别、再分类、后结构化”的顺序处理标题与正文，输出机器可用结果、原始模型响应和校验问题。避免把非项目文本强行结构化为招投标项目。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 保留原始标题和正文，不在调用前补写不存在的项目名称、金额、公司或日期。
- 模型返回值可能是 JSON 字符串或结构化文本。先尝试解析；解析失败时保留原文并报告格式问题，不得自行补齐。
- 批量处理时逐条保留状态、错误和模型用量，单条失败不污染其他结果。

## 收集输入

必须获得标题和正文。可选接收目标字段清单、输出 JSON Schema、金额单位规则、电话号码规则、分类范围、批次编号和是否保留原文。

## 执行流程

1. 调用项目信息甄别接口，判断为标讯信息、拟在建信息、非项目信息或异常信息。
2. 若为非项目信息或异常信息，停止结构化，输出甄别结果和原因。
3. 若为标讯信息，调用分类推理接口，获取招中标信息分类。
4. 调用 LLM 招中标项目信息结构化接口。用户提供字段规则时写入 system 消息；未提供时使用最小规则：字段无证据时返回空值，金额统一为人民币元，座机仅在正文可判断区号时补全。
5. 解析 `choices[0].message.content`。校验 JSON、字段类型、金额单位、日期格式、电话号码、公司角色和原文证据。
6. 输出原始模型结果与标准化结果，列出缺失字段、冲突字段和低置信字段。

## 接口

### 项目信息甄别

`POST /outer-gateway/bid/projectDiscrimination`

请求体：`{"title": "标题", "content": "正文"}`。读取 `data.response`、`data.status` 和 `data.time`。只有甄别结果支持时才进入后续步骤。

### 招中标分类推理

`POST /outer-gateway/bid/categoryReasoning`

请求体：`{"title": "标题", "content": "正文"}`。读取 `data.response`。分类以接口结果为准，不从标题关键词自行替换。

### LLM 结构化

`POST /outer-gateway/bid/ztbAiStructureInfo`

```json
{
  "messages": [
    {
      "role": "system",
      "content": "从原文抽取指定字段；无证据返回空值；金额统一为人民币元；只输出合法JSON。"
    },
    {
      "role": "user",
      "content": "标题：<标题>\n正文：<正文>"
    }
  ],
  "max_tokens": 2048,
  "temperature": 0,
  "top_p": 1
}
```

读取 `choices[].message.content` 和 `usage`。默认使用 `temperature=0` 保持稳定。

## 校验规则

- 每个结构化字段必须能在原文找到证据，或明确标记为模型推断。
- 万元转元时乘以 10000；币种不明确时不要默认人民币。
- 同一公告出现多个标段、金额或主体时使用数组，不强行合并。
- 采购人、供应商、代理机构、投标人和中标人角色不得混淆。
- 分类接口和正文语义冲突时同时保留两者并标记人工复核。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 招中标信息分类推理(references/category-reasoning.md)
- LLM 招中标项目信息结构化(references/ztb-ai-structure-info.md)
- 枚举值与码表(references/enums-and-code-tables.md)

本次提供的 `Parameter-Description.md` 未包含 `/bid/projectDiscrimination` 的详细输入输出段。调用项目信息甄别时沿用本 Skill 中的现有接口约定，并明确标记详细参数文档缺失，不得自行补造字段。

## 输出格式

输出单条或批次处理汇总，字段包括：甄别类型、分类结果、结构化 JSON、原始模型响应、证据摘录、校验状态、缺失字段、冲突字段、模型用量和处理时间。不得只返回经过润色的自然语言摘要。
