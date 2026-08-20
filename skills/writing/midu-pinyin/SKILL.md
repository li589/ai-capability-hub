---
name: midu-pinyin
description: 中文拼音注音（逐字标音），生成可渲染的 HTML ruby 注音、汉字拼音对照文本、纯拼音三种形态。当用户说“给这段中文标拼音/注音/加拼音/生成拼音对照/带拼音的文章/拼音在上汉字在下/多音字怎么读/汉语拼音标注”等任何与中文注音相关的需求时，必须使用此 Skill。即使用户没有提供 token，也要使用此 Skill 来引导其配置环境变量 MIDU_APP_SECRET（未设置时提醒其前往蜜度官网注册获取）并完成调用。注意与“校对/纠错别字”区分——那是 midu-proofread，本 Skill 只做注音。
version: "1.0.0"
license: "JDT"
metadata: {}
display_name: "蜜度拼音注音"
display_name_en: "Midu Pinyin Annotation"
description_zh: "中文逐字拼音注音，生成 HTML ruby 注音、汉字拼音对照、纯拼音三种形态，正确处理多音字。"
description_en: "Character-by-character pinyin annotation generating HTML ruby, Han-pinyin pairs, and pure pinyin forms with polyphone disambiguation."
visibility: "public"
---

# 拼音注音 Skill（Midu Skills）

此 Skill 使用 Python 脚本调用拼音注音接口，对用户提供的中文文本**逐字注音**，并按固定顺序展示三种形态：HTML ruby 注音效果、汉字拼音对照、纯拼音。

## 前置条件（鉴权 token）

接口需要 `Authorization: Bearer <token>` 鉴权 token。

### token 存储方式

token 统一从环境变量 **`MIDU_APP_SECRET`** 读取；`--api-key` 显式参数可覆盖（优先级最高）。

```bash
export MIDU_APP_SECRET=<你的 Key>
```

### 未设置时的引导

若用户未设置 `MIDU_APP_SECRET`，或接口返回鉴权失败（HTTP 401/403、`apiKey 有误`），提示用户：
> 请前往蜜度官网 https://ai.mdata.net 注册并获取 Key，然后配置环境变量 `MIDU_APP_SECRET`。

## 使用方法

Skill 提供 Python 脚本 `scripts/midu_pinyin.py`，封装完整流程：读取 token → 调用注音接口 → 打印 `transactionId`/`charCount` 与三种注音形态 → **生成统一样式的注音预览页**（默认写入临时目录：mac `/tmp`、Windows `%TEMP%`）。

### 方式一：命令行（推荐）

```bash
python scripts/midu_pinyin.py --text "春天刚来的时候，城市里的风还有一点凉。"
```

脚本默认把预览页生成到**临时目录**（mac 为 `/tmp`，Windows 为系统临时目录 `%TEMP%`；文件名带 `transactionId` 避免多次调用互相覆盖），并在 stdout 打印其绝对路径。常用参数：

- `--html-out <path>`：指定预览页输出路径（默认 mac 写 `/tmp`、Windows 写 `%TEMP%`）。
- `--no-html`：不生成预览页。
- `--api-key "xxxx"`：显式传 token（优先级最高）。

> **预览页务必用脚本生成，不要自己手写 HTML。** ruby 注音的排版有个常见坑：相邻汉字的拼音比汉字宽时会糊成一片。脚本内置的样式已经把每个字包成 `inline-block` 并居中、留白来规避它。各智能体若各自拼 HTML，样式不统一且容易踩这个坑，所以统一交给脚本。

### 方式二：Python 调用

```python
from scripts.midu_pinyin import annotate_text

result = annotate_text("春天刚来的时候，城市里的风还有一点凉。")
print(result.ruby_html)       # HTML ruby 注音
print(result.annotated_text)  # 汉字(拼音) 对照
print(result.pinyin_text)     # 纯拼音
```

## 接口说明（固定参数）

- **请求地址**：模块常量 `API_URL`（`POST`，`Content-Type: application/json`，超时 60 秒）。
- **请求体**：JSON 对象，业务字段置于顶层：
  - `text`：待注音正文（脚本仅校验非空，去空白后不能为空；接口侧上限 5000 字）
- **请求头**：
  - `X-Skill-Code: JDT_PHON_ANNOT`（固定）
  - `Authorization: Bearer <token>`（token 来自环境变量 `MIDU_APP_SECRET` 或 `--api-key` 参数）

## 结果说明与展示规则

成功返回（`code == '0000'`）的 `data` 必含三个字段：

- `rubyHtml`：HTML ruby 注音，形如 `<ruby>春<rt>chūn</rt></ruby>...`，渲染后拼音在上、汉字在下。
- `annotatedText`：汉字与拼音对照，形如 `春(chūn) 天(tiān) 的(de) ...`，标点/换行原样保留。
- `pinyinText`：纯拼音，空格分隔，形如 `chūn tiān de ...`，不含标点。

顶层还有 `transactionId`（日志 ID，用于排查）与 `charCount`（注音总字数）。

**展示规则（每次成功调用都必须按此顺序，不可调换、不可省略其一）**：

0. **【强制】展示脚本生成的预览页绝对路径**——每次成功调用都必须把 stdout 里的 `pinyin_preview.html` 绝对路径单独、显眼地展示给用户（例如「注音预览页已生成：`/abs/path/pinyin_preview.html`」），引导其打开查看真实排版效果。此项不可省略。
1. **注音效果只通过预览页呈现，绝不输出 HTML**——**任何环境下都禁止向用户输出 `rubyHtml` 原文、`<ruby>`/`<rt>` 等 HTML 标签或代码块**，也不要自己另写 HTML 代替。`rubyHtml` 仅供脚本生成预览页内部使用。用户要看「拼音在上·汉字在下」的真实效果，一律引导其打开第 0 步的预览页绝对路径。
2. **再展示 `annotatedText`**——汉字与拼音逐字对照的文本，方便边读边对。
3. **最后展示 `pinyinText`**——纯拼音串。
4. 一并展示 `transactionId`，便于事后排查。

> 为什么这样定：① 预览页路径是用户拿到真实排版的唯一入口，必须每次强制给出，否则终端用户看不到效果。② HTML 标签/源码对用户无价值且干扰阅读——注音效果一律通过预览页路径呈现，任何环境都不粘贴 HTML 标签文本。③ 固定顺序：先给路径与最终效果，再给对照文本逐字核对，纯拼音作为可复制补充；倒序或缺项都会削弱阅读体验。
