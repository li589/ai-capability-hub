---
name: "midu-proofread-pinyin"
version: "1.0.0"
description: "智能拼音校对（单段/整段纯文本）并生成勘误表。支持'拼音行+汉字行'交替格式的自动解析与组装。输入必须为调用方提取后的纯文本，本 Skill 不处理文件读取。当用户说'拼音校对/检查拼音/拼音勘误/拼音检测'等任何与拼音校对相关需求时，必须使用此 Skill。即使用户没有提供 token，也要使用此 Skill 来引导其从环境变量 MIDU_APP_SECRET 配置鉴权并完成调用。"
license: "JDT"
metadata: {"openclaw": {"emoji": "", "requires": {"bins": ["python3"], "env": ["MIDU_APP_SECRET"], "primaryEnv": "MIDU_APP_SECRET"}}}
display_name: "蜜度拼音校对"
display_name_en: "Midu Pinyin Proofreading"
description_zh: "智能拼音校对工具，自动识别「拼音行+汉字行」交替格式并组装后送入校对，生成勘误表与多格式下载链接。"
description_en: "Intelligent pinyin proofreading with auto-detection of pinyin-Han alternating format, generating errata tables."
visibility: "public"
---

# 拼音校对 Skill（Midu Skills）

此 Skill 使用 Python 脚本调用拼音校对接口，对调用方传入的纯文本进行智能拼音校对，并以 **Markdown 形式直接展示校对结果** 给用户。

> **依赖**：脚本用 `requests` 直连（TLS 证书默认校验，不禁用）。执行前确保已安装：`pip3 install requests`。

**职责边界**：本 Skill 仅负责纯文本的拼音格式转换与校对核心逻辑，不处理文件读取、解析或格式转换。若用户上传 Word、PDF 等文件，调用方（模型）需先在内存中提取纯文本内容，再将文本传入本 Skill 处理。

**核心特性**：自动识别并解析"拼音行+汉字行"交替格式，组装为"汉字+拼音"格式后再进行校对。

当用户需要下载时，仅提供勘误表/结果文件的 **URL 链接**（不在本地下载落盘）。

## 前置条件（鉴权 token）

接口需要 `Authorization: Bearer <token>` 鉴权 token。

### token 获取方式

若未配置 token 或接口返回鉴权失败，提示用户：
> 请前往 https://ai.mdata.net 注册获取 MIDU_APP_SECRET。

### token 存储方式

通过环境变量 `MIDU_APP_SECRET` 配置。

## 执行检查点

在调用脚本前，必须依次确认以下检查点。任何一项未通过，都应**暂停执行并征求用户意见**，不可自主跳过。

| # | 检查点 | 触发条件 | 确认话术（示例） |
|---|--------|----------|----------------|
| 1 | **鉴权确认** | 环境变量 `MIDU_APP_SECRET` 未配置或为空 | "尚未配置鉴权 token，请前往 https://ai.mdata.net 注册获取 MIDU_APP_SECRET。配置完成后请告诉我，我将继续为您校对。" |
| 2 | **文本长度确认** | `proofText` 长度超过 5000 字符 | "待校对文本共 X 字符，超过 5000 字符限制。本接口不支持分段校对，请缩短文本后重试。" |
| 3 | **结果展示确认** | 接口返回成功，已展示勘误 Markdown | "勘误结果已展示。如需下载 JSON/Excel/Markdown 格式的完整结果，请告知。" |

> ⚠️ **禁止事项**：**严禁**在任一检查点未通过时自主调用脚本或伪造用户同意继续执行。

## 执行流程

当用户触发本 Skill（如说"帮我拼音校对"）时，按以下步骤执行：

### Step 1: 获取并检查鉴权 token

1. 检查环境变量 `MIDU_APP_SECRET` 是否存在
2. **触发「鉴权确认」检查点**：若未配置，提示用户前往 https://ai.mdata.net 获取，**暂停等待用户反馈**
3. 用户配置完成后，继续下一步

### Step 2: 接收并预处理文本

1. 接收用户传入的纯文本（调用方已从 Word/PDF 等提取）
2. 判断文本是否为"拼音行+汉字行"交替格式
   - 是 → 调用脚本的组装逻辑，转换为"汉字+拼音"格式
   - 否 → 按普通文本直接校对
3. **触发「文本长度确认」检查点**：统计字符数，若超过 5000 字符，拒绝执行并提示用户缩短文本

### Step 3: 调用拼音校对脚本

使用以下命令调用（推荐命令行方式）：

```bash
python scripts/midu_proofread_pinyin.py --text "待校对文本内容"
```

- `--text`: 预处理后的纯文本（支持"拼音行+汉字行"交替格式）
- `--api-key`: 可选，显式传入 token（优先级高于环境变量）
- `--file-name`: 可选，来源文件名（仅 basename）

### Step 4: 展示结果与收尾

1. 从接口返回中提取勘误 Markdown，直接展示给用户
2. **触发「结果展示确认」检查点**：询问用户是否需要下载链接
3. 若用户需要，提供 JSON/Excel/Markdown 三个下载链接
4. 展示 `transactionId`，便于事后排查

---

## 输入格式

### 输入方式

- **纯文本来源**（调用方提取后的文本）：使用 `--text` 参数。支持"拼音行+汉字行"交替格式，会自动组装为"汉字+拼音"格式后校对。

> ⚠️ **接口限制**：待校对文本长度不能超过 **5000 字符**。若文本超长，拒绝执行并提示用户缩短文本。

> 注：若用户上传 Word、PDF 等文件，调用方需先在内存中提取纯文本，再将提取后的文本作为 `--text` 参数传入。本 Skill 不参与任何文件读取操作。

#### 1. "拼音行+汉字行"交替格式（自动识别并组装）

文本中每两行一组：第一行为连续拼音，第二行为对应汉字。脚本会自动解析并组装为"汉字+拼音"格式后校对。

**示例输入**：
```
hěnjiǔyǐqián
很久以前，
tāmenxínɡyǐnɡbùlí
它们形影不离，
```

**组装后**：
```
很hěn久jiǔ以yǐ前qián，
它tā们men形xínɡ影yǐnɡ不bù离lí，
```

#### 2. 普通文本格式

如果输入不是"拼音行+汉字行"交替格式，则直接按原文进行校对。


- **纯文本来源**（调用方提取后的文本）：使用 `--text` 参数。支持"拼音行+汉字行"交替格式，会自动组装为"汉字+拼音"格式后校对。

> ⚠️ **接口限制**：待校对文本长度不能超过 **5000 字符**。若文本超长，拒绝执行并提示用户缩短文本。

> 注：若用户上传 Word、PDF 等文件，调用方需先在内存中提取纯文本，再将提取后的文本作为 `--text` 参数传入。本 Skill 不参与任何文件读取操作。

### 方式一：命令行（推荐）

#### 短文本场景（直接传参）

纯文本拼音校对（支持"拼音行+汉字行"交替格式自动组装）：

```bash
python scripts/midu_proofread_pinyin.py --text "hěnjiǔyǐqián
很久以前，"
```

显式传 token（优先级最高）：

```bash
python scripts/midu_proofread_pinyin.py --text "..." --api-key "xxxx"
```

#### 内存执行方案（Python -c）

完全无需文件落盘，适合中等长度文本（≤ 5000 字符）：

```bash
python -c "
import sys
sys.path.insert(0, 'scripts')
from midu_proofread_pinyin import proofread_text

text = '''待校对文本内容'''
result = proofread_text(text, api_key='xxxx')
print('✅ 校对完成')
print(f'transactionId: {result.urls.transaction_id}')
print(result.erratum_md)
print(f'- [JSON]({result.urls.proof_json_url})')
print(f'- [Excel]({result.urls.erratum_excel_url})')
print(f'- [MD]({result.urls.erratum_md_url})')
"
```

> **优点**：无临时文件、安全性高、执行快速  
> **限制**：超长文本仍可能受命令行长度限制

### 方式二：Python 调用

```python
from scripts.midu_proofread_pinyin import proofread_text

# 纯文本（支持"拼音行+汉字行"交替格式自动组装）
result = proofread_text("hěnjiǔyǐqián\n很久以前，")
print(result)
```

---

## ⚠️ 禁止事项

**严禁创建临时 `.py` 脚本文件**（如 `temp_proofread_pinyin.py`），原因如下：
- ❌ 硬编码 API Key 存在泄露风险
- ❌ 污染工作区目录结构
- ❌ 增加出错概率和维护成本
-  违反"不落盘"设计原则

**正确做法**：优先使用上述"方式一"中的三种命令行方案。

## 接口说明

### 拼音校对接口

- **请求地址**：`https://api.midu.com/ability/skill/jdt/proof/pinyin`
- **请求方式**：`POST`，`Content-Type: application/json`，超时 60 秒
- **请求体**：JSON 对象，业务字段直接置于顶层：
  - `proofText`：待校对正文（脚本在 `proofread_text` 中仅校验非空）
  - `fileName`：**可选**，来源文件名（仅 basename）。仅当文件类来源时下发；为空/未提供则该字段不出现在请求体中
- **请求头**：
  - `X-Skill-Code: JDT_PROOF`（固定）
  - `Authorization: Bearer <token>`

## 结果说明与展示规则

成功返回（`code == '0000'`）必含：
- `data.proofResultJsonUrl`：校对结果 JSON URL
- `data.erratumExcelUrl`：勘误表 Excel URL
- `data.erratumMdUrl`：勘误 Markdown URL
- `transactionId`：日志 ID，用于排查问题
- `charCount`：本次校对总字数（与 `code` 同级，位于响应顶层）

**展示规则（每次成功调用都必须满足）**：

1. 直接以 Markdown 形式展示从 `erratumMdUrl` 拉取的勘误内容（不落盘下载）。
2. **必须完整列出三个下载链接**：`proofResultJsonUrl` / `erratumExcelUrl` / `erratumMdUrl`，不可省略、不可合并、不可仅展示其中一个。
3. **必须展示 `transactionId`**，便于事后排查。
4. 用户需要下载时，仅引导其打开上述链接，**不在本地下载落盘**。

## 异常处理

| 异常场景 | 处理策略 |
|----------|----------|
| **鉴权失败（401/403）** | 提示用户 token 无效，引导前往 https://ai.mdata.net 重新获取，**暂停执行等待用户反馈**。 |
| **网络超时/连接失败** | 提示用户网络异常，建议检查网络后重试，**暂停执行等待用户反馈**。 |
| **文本为空或仅空白字符** | 拒绝执行，提示用户传入有效文本。 |
| **文本超过 5000 字符** | 触发「文本长度确认」检查点，拒绝执行并提示用户缩短文本。 |
| **接口返回非 `0000` 且非鉴权错误** | 打印 API 返回的 `code` 和 `msg` 给用户，不再进行额外查询。 |
| **组装拼音失败** | 若无法识别为"拼音行+汉字行"格式，按普通文本直接校对，不报错。 |

### Important Notes

- **Error handling**: 请求失败时优先检查网络、JSON 格式、token 是否正确。若 API 已返回明确结果，不要进行额外的无意义后续查询。
- **Timeout**: 校对可能需要较长时间，建议保持超时在 120 秒或更高。
- **Session Management**: 支持环境变量 `MIDU_APP_SECRET` 配置。
- **Retry 策略**: 网络超时或连接失败时，可提示用户重试一次；若仍失败则放弃并告知用户。鉴权失败不重试。
