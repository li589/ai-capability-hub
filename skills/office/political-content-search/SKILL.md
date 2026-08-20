---
name: political-content-search
version: 1.0.0
description: 调用接口进行时政内容检索。触发词：检索时政内容、搜索政策文件、查询会议内容、调用
  https://api.midu.com/ability/skill/jdt/political/search。若用户未提供 token，引导其从环境变量
  MIDU_APP_SECRET 配置鉴权并完成调用。
license: JDT
metadata:
  openclaw:
    emoji: ""
    requires:
      bins:
        - python3
      env:
        - MIDU_APP_SECRET
      primaryEnv: MIDU_APP_SECRET
display_name: 蜜度时政内容检索
display_name_en: Midu Political Content Search
description_zh: 检索时政内容、政策文件、会议信息，覆盖地方政府官网、官方媒体、学习强国等权威信源，按类目分类展示。
description_en: Search political content, policy documents, and meeting info
  across authoritative government and media sources.
visibility: public
disable-model-invocation: true
---

# 时政内容检索 Skill

此 Skill 使用 Python 脚本调用检索接口，对用户提供的关键词进行时政内容检索，并以 **JSON 形式直接展示检索结果** 给用户。

> **依赖**：脚本用 `requests` 直连（TLS 证书默认校验，不禁用）。执行前确保已安装：`pip3 install requests`。

## 前置条件（鉴权 token）

接口需要 `Authorization: Bearer <token>` 鉴权。

### token 获取方式

若未配置 token 或接口返回鉴权失败，提示用户：

请前往 https://ai.mdata.net 重新获取 Key。

### token 存储方式

环境变量 `MIDU_APP_SECRET`

### 异常情况处理

| 异常类型 | 表现 | 处理方式 |
|---------|------|---------|
| 鉴权失败 | 接口返回 401 或提示 token 无效 | 提示用户配置 `MIDU_APP_SECRET` 环境变量 |
| 网络连接失败 | 脚本提示 `Connection refused` | 检查网络连接是否正常，或稍后重试 |
| 接口超时 | 60 秒内未返回结果 | 提示用户稍后重试，或检查服务状态 |
| 空结果或无 `formattedContent` | 接口返回但无有效内容 | 降级展示原始 JSON 响应，不报错 |
| keyword 为空 | 用户未提供关键词 | 脚本会抛出错误，提示 `keyword 不能为空` |

## 执行流程与检查点

1. **关键词确认**：执行检索前，确认用户提供的 `keyword` 不为空。若为空，提示用户补充后再执行。
2. **鉴权状态确认**：调用脚本前，若未检测到 `MIDU_APP_SECRET`，先提示用户配置，确认后再执行。
3. **结果异常确认**：若接口返回空结果或 `formattedContent` 为空，向用户说明情况，确认是否重试或更换关键词。

## 使用方法

Skill 提供 Python 脚本 `scripts/political_search.py` 封装了完整流程：读取 token → 调用检索接口 → 提取 `formattedContent` → 标准化换行符与 URL → 直接输出结果。

### Step 1 — 准备输入

- **keyword**（必需）：用户提供的关键词，脚本仅校验非空。
- **token**（必需）：确保 `MIDU_APP_SECRET` 环境变量已配置。

### Step 2 — 调用脚本

**方式 A：命令行（推荐）**

```bash
# 基本调用
python scripts/political_search.py --keyword "三中会议"

# 显式传 token（优先级最高）
python scripts/political_search.py --keyword "三中会议" --api-key "your-api-key"
```

**方式 B：Python 调用**

```python
from scripts.political_search import search_content

result = search_content("三中会议")
print(result.formatted_content)  # 优先输出格式化内容
```

### Step 3 — 处理输出

脚本自动完成以下处理：
1. 提取 `formattedContent` 字段
2. 将纯文本 URL 转换为 Markdown 链接
3. 标准化换行符（`\r\n` → `\n`）

若未找到 `formattedContent`，则降级输出原始 JSON。

### Step 4 — 展示结果

直接、完整、逐字输出脚本返回的内容，严禁加工、改写或润色。

## 接口说明（固定参数）

- **请求地址**：模块常量 `API_URL`（`POST`，`Content-Type: application/json`，超时 60 秒）。
- **请求体**：JSON 对象：
  - `keyword`：检索关键词（脚本中仅校验非空）
  - `searchType`：检索类型（默认 0）
- **请求头**：
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>`（token 来自 `MIDU_APP_SECRET` / `--api-key`）

## 结果说明与展示规则

成功返回时，接口必然包含 `formattedContent` 字段。脚本优先提取并展示 `formattedContent` 内容。

**⚠️ 核心约束（每次成功调用都必须严格遵守）**：

1. **必须直接原样输出**：AI 必须直接、完整、逐字输出接口返回的原始内容（优先展示 `formattedContent` 字段的原始文本），严禁进行任何形式的加工、改写、润色或重排。
2. **严禁摘要/扩写**：不得对原始内容进行摘要、提炼、扩写、补充或删减。
3. **严禁格式重排**：不得重新组织段落结构、调整列表顺序、修改换行或缩进。原始文本的格式必须原样保留。
4. **Markdown 原样保留**：若接口返回的原始内容本身已是 Markdown 格式，AI 必须直接原样输出该 Markdown 文本，严禁将其转换为纯文本（plaintext）格式，同时严禁对 Markdown 内容进行任何摘要、扩写、重写或格式重排。
5. **严禁语言润色**：不得替换同义词、调整语序、翻译或进行任何语言风格上的修改。
6. **URL 处理例外**：仅允许将 `formattedContent` 中的纯文本 URL 转换为 Markdown 链接格式（如 `[https://example.com](https://example.com)`），以便用户点击跳转。此操作不改变原始文本内容，仅为增强可用性。
7. **Hash 片段保护**：原始 URL 中若包含 `#liuyan` 等 hash 片段（如 `http://.../c1002-40727920.html#liuyan`），必须确保 Markdown 链接语法完整且正确，即 `[显示文本](完整URL含hash)`。严禁让 hash 片段被误解析为 Markdown 标题或其他格式符号而导致链接断裂；同时确保 hash 片段后的内容不会被错误地截断或转换格式，保证原始数据中的 URL 在 Markdown 渲染环境下完整可用。
8. **换行符标准化**：为确保 Markdown 渲染一致性，脚本会自动将 Windows 换行符 `\r\n` 统一转换为 Unix 换行符 `\n`，避免某些渲染器因换行符差异导致格式异常（如误解析为代码块）。此操作不改变文本内容和段落结构，仅为兼容性优化。
9. **降级策略**：若未找到 `formattedContent` 字段，则降级展示原始 JSON 响应，同样严禁对 JSON 内容进行任何修改。
10. **禁止落盘**：若用户需要进一步处理结果，仅提供接口调用方式，不在用户端下载落盘。

**展示规则（每次成功调用都必须满足）**：

1. 优先以**文本形式**展示 `formattedContent` 内容。
2. `formattedContent` 中的 URL 会自动转换为 **Markdown 链接格式**（如 `[https://example.com](https://example.com)`），支持点击跳转。
3. **Hash 片段处理**：当 URL 包含 `#liuyan` 等 hash 片段时，必须确保 Markdown 链接包裹完整，如 `[http://.../c1002-40727920.html#liuyan](http://.../c1002-40727920.html#liuyan)`，避免 `#` 被 Markdown 解析器误识别为标题符号而导致链接断裂或内容截断。
4. **换行符自动标准化**：脚本会自动将 `\r\n` 转换为 `\n`，确保所有 Markdown 渲染器都能正确解析，避免因换行符差异导致的格式异常（如误解析为代码块）。
5. 若未找到 `formattedContent` 字段，则降级展示原始 JSON 响应。
6. 若用户需要进一步处理结果，仅提供接口调用方式，不在用户端下载落盘。
