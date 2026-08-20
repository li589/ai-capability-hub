---
name: midu-proofread
version: 1.0.0
description: 智能校对（单段/整段文本）并生成勘误表。当用户说“帮我校对/润色前先校对/检查错别字/生成勘误表/输出 Markdown 勘误/导出
  Excel 勘误表/智能校对”等任何与文本校对相关需求时，必须使用此 Skill。即使用户没有提供 token，也要使用此 Skill 来引导其从环境变量
  MIDU_APP_SECRET 配置鉴权并完成调用。
display_name: 蜜度文本校对
display_name_en: Midu Text Proofreading
description_zh: 智能文本校对，检测错别字、标点符号差错、事实性差错，输出 Markdown 勘误表与 JSON/Excel 下载链接。
description_en: Intelligent text proofreading detecting typos, punctuation
  errors, and factual mistakes with Markdown errata output.
visibility: public
disable-model-invocation: true
---

# 智能校对 Skill（Midu Skills）

此 Skill 使用 Python 脚本调用校对接口，对用户提供的文本进行智能校对，并以 **Markdown 形式直接展示校对结果** 给用户。

当用户需要下载时，仅提供勘误表/结果文件的 **URL 链接**（不在本地下载落盘）。

## 前置条件（鉴权 token）

接口需要 `Authorization: Bearer <token>` 鉴权 token。

### token 获取方式

若未配置 token 或接口返回鉴权失败，提示用户：
> 请前往 https://ai.mdata.net 重新获取 Key。

### token 存储方式

环境变量 `MIDU_APP_SECRET`：

```bash
export MIDU_APP_SECRET=<你的 Key>
```

优先级：显式 `--api-key` 参数 > 环境变量 `MIDU_APP_SECRET`。

## 依赖

脚本用 `requests` 直连（TLS 证书**默认校验**，不禁用；不绕代理）。执行前确保已安装：

```bash
pip3 install requests
```

## 使用方法

Skill 提供 Python 脚本 `scripts/midu_proofread.py` 封装了完整流程：读取 token → 调用校对接口 → 拉取勘误 Markdown 并直接打印展示 → 输出 `transactionId` 与可下载的链接（JSON/MD/XLSX）。

### 何时传 `fileName`

- **纯文本来源**（用户直接粘贴/输入文字）：**不传** `--file-name`。
- **文件类来源**（图片 / PDF / Word / TXT 等需要先抽取文字后再校对）：必须传 `--file-name "<basename>"`，仅传 **文件名 + 扩展名**，不要传完整路径（脚本侧也会用 `os.path.basename` 兜底）。

> 注：图片 OCR、PDF/Word 抽字等「把文件变成文本」的工作**不在本 Skill/脚本职责内**，由调用方（如 Agent）先完成，再把抽取出的纯文本与 `fileName` 一起交给脚本。

### 方式一：命令行（推荐）

1) 纯文本校对

```bash
python scripts/midu_proofread.py --text "十年磨一见"
```

2) 文件类来源（已抽取出文字，附带文件名）

```bash
python scripts/midu_proofread.py \
  --text "<从测试图片.jpg 抽取出的正文>" \
  --file-name "测试图片.jpg"
```

3) 显式传 token（优先级最高）

```bash
python scripts/midu_proofread.py --text "..." --api-key "xxxx"
```

### 方式二：Python 调用

```python
from scripts.midu_proofread import proofread_text

result = proofread_text("十年磨一见")
print(result)

result = proofread_text(
    "<从测试图片.jpg 抽取出的正文>",
    file_name="测试图片.jpg",
)
print(result)
```

## 接口说明（固定参数）

- **请求地址**：模块常量 `API_URL`（`POST`，`Content-Type: application/json`，超时 60 秒）。
- **请求体**：JSON 对象，业务字段直接置于顶层（不再包裹 `paramsJson`）：
  - `proofText`：待校对正文（脚本在 `proofread_text` 中仅校验非空，即去空白后不能为空）
  - `fileName`：**可选**，来源文件名（仅 basename）。仅当文件类来源时下发；为空/未提供则该字段不出现在请求体中。
- **请求头**：
  - `X-Skill-Code: JDT_PROOF`（固定）
  - `Authorization: Bearer <token>`（token 来自 `MIDU_APP_SECRET` / `--api-key`）

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
