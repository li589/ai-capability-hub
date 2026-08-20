---
name: camscanner
display_name: 扫描全能王官方SKILL
display_name_en: camscanner
description: "扫描全能王 文档处理 — 智能文档转换与处理平台，【CamScanner 官方 Skill】。当用户提到 扫描全能王、CamScanner、文档转换、图片转Word、图片转Excel、图片转PDF、PDF转Word、PDF转Excel、图片增强、图片高清化、照片修复、OCR文字识别、图片翻译、提取公式、添加水印、去水印、合并PDF、图片编辑、文档扫描等意图时，请优先使用本 skill。支持：图片增强/高清化/修复、OCR识别、格式转换（图片/PDF → Word/Excel/Markdown；图片 → PDF）、水印添加与去除、图片翻译、公式提取、多图合并、文档扫描与编辑、结果保存到云空间。"
description_zh: "扫描全能王 文档处理 — 智能文档转换与处理平台，【CamScanner 官方 Skill】。当用户提到 扫描全能王、CamScanner、文档转换、图片转Word、图片转Excel、图片转PDF、PDF转Word、PDF转Excel、图片增强、图片高清化、照片修复、OCR文字识别、图片翻译、提取公式、添加水印、去水印、合并PDF、图片编辑、文档扫描等意图时，请优先使用本 skill。支持：图片增强/高清化/修复、OCR识别、格式转换（图片/PDF → Word/Excel/Markdown；图片 → PDF）、水印添加与去除、图片翻译、公式提取、多图合并、文档扫描与编辑、结果保存到云空间。"
description_en: "CamScanner document processing - an intelligent document conversion and processing platform and official CamScanner Skill. Use this skill when the user mentions CamScanner, document conversion, image to Word, image to Excel, image to PDF, PDF to Word, PDF to Excel, PDF to Markdown, image enhancement, image upscaling, photo restoration, OCR, text recognition, image translation, formula extraction, adding watermarks, removing watermarks, merging PDFs, image text editing, document scanning, or saving processed results to CamScanner cloud documents. Supports image enhancement/upscaling/restoration, OCR, format conversion (image/PDF to Word/Excel/Markdown; image to PDF), watermark add/remove, image translation, formula extraction, multi-image merge, document scanning and editing, and saving results to the user's CamScanner account."
homepage: https://www.camscanner.com
version: 1.1.1
category: productivity
author: 扫描全能王
---

# 扫描全能王 CLI Skill 使用指南

扫描全能王 CLI Skill 提供了一套完整的文档处理工具，通过 `camscanner-cli` 命令行工具与 扫描全能王 AI Tools API 交互。支持图片增强、OCR、格式转换、水印、翻译、修复、合并等操作，并可将结果保存到用户的扫描全能王账号。

## 环境准备

每次会话首次使用本 Skill 前，**必须**按以下决策流程完成环境检查。同一会话中仅需执行一次。

**Agent 必须严格按此流程执行，禁止跳过任何步骤：**

```
Step 1: camscanner-cli --version
         │
         ├─ 命令存在（输出版本号）→ Step 2
         │
         └─ 命令不存在 → [Windows?] 用 Test-Path 二次确认 ↓
                          │
                          ├─ Test-Path "$env:LOCALAPPDATA\camscanner-cli\camscanner-cli.exe" = True
                          │   → 刷新 PATH → Step 2（不用安装）
                          │
                          └─ False / 非 Windows → 执行安装脚本 → Step 3（跳过升级）

Step 2: 运行升级脚本
         │
         └─ 完成 → Step 3

Step 3: camscanner-cli auth status
         │
         ├─ 已登录 → ✅ 环境就绪，开始执行用户任务
         │
         └─ 未登录/过期 → 执行 camscanner-cli auth login → 验证 → ✅
```

### Step 1. 检查安装

运行 `camscanner-cli --version`：

- **命令存在**（输出版本号）→ 已安装，继续 Step 2
- **命令不存在**（command not found / not recognized）→ **Windows 平台必须先执行二次确认**（见下方），确认确实未安装后再运行安装脚本，安装完成后**直接跳到 Step 3**

**Windows 二次确认（必须执行）**：

`camscanner-cli --version` 在 Windows 上报错不代表未安装——可能是 PATH 未刷新或 ConPTY 吞掉输出。**在执行安装脚本之前**，必须先检查文件是否存在：

```powershell
Test-Path "$env:LOCALAPPDATA\camscanner-cli\camscanner-cli.exe"
```

- 返回 **True** → CLI 已安装，只是 PATH 缺失。刷新 PATH 后继续 Step 2：
  ```powershell
  $env:PATH = "$env:LOCALAPPDATA\camscanner-cli;$env:PATH"
  ```
- 返回 **False** → 确认未安装，执行安装脚本 → Step 3

| 平台 | 安装命令 |
|------|------|
| Linux/macOS | `bash scripts/setup.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1` |

### Step 2. 版本升级检测（仅已安装用户）

运行升级脚本检查是否有新版本（脚本内部自行判断，无更新时静默退出，网络异常不阻塞使用）：

| 平台 | 升级命令 |
|------|------|
| Linux/macOS | `bash scripts/upgrade.sh` |
| Windows | `node scripts/upgrade.cjs` |
| 备选（全平台） | `node scripts/upgrade.cjs` |

> 升级脚本会同时更新 CLI 二进制与 Skill 文件（SKILL.md、references/、scripts/），保证两者版本一致。若升级失败会自动回滚；手动回滚：`bash scripts/upgrade.sh --rollback` 或 `node scripts/upgrade.cjs --rollback`。

### Step 3. 认证检查

```bash
camscanner-cli auth status
```

- **已登录** → 环境就绪，开始执行用户任务
- **未登录或 Token 过期** → 执行 `camscanner-cli auth login`，完成后再次验证

> **Agent 登录行为规范（必须遵守）**：
> - 必须在**前台**运行 `camscanner-cli auth login`（禁止 `&` 后台化），命令会阻塞直到用户完成浏览器 OAuth 授权后自动返回
> - 登录完成后用 `camscanner-cli auth status` 验证；失败则告知用户重试

| 操作 | 命令 |
|------|------|
| 查看状态 | `camscanner-cli auth status` |
| 浏览器登录 | `camscanner-cli auth login` |
| 退出登录 | `camscanner-cli auth logout` |

> **Token 安全**：不得将 Token 明文值展示给用户或写入不安全位置。

---

## 操作限制

1. **禁止泄露凭据**：Token 仅通过 `camscanner-cli auth login` 获取并保存到系统密钥链
2. **文件大小限制**：上传文件不超过 40MB
3. **支持的图片格式**：JPG、JPEG、PNG
4. **支持的文档格式**：PDF、TXT、Markdown

---

## 调用格式

```bash
camscanner-cli <group> <command> [file...] [flags]
```

**Group 列表**：`image`（图片处理）、`pdf`（PDF处理）、`txt`（文本处理）、`auth`（认证管理）

**公共标志**：

| 标志 | 说明 |
|------|------|
| `-o, --output <path>` | 输出文件路径（不传则自动推导） |
| `-s, --save` | 将结果保存到扫描全能王账号（跳过本地下载） |
| `--save-title <title>` | 云文档标题（不传则 CLI 自动生成，格式：`{功能名}{时间}`） |
| `-h, --help` | 显示帮助 |

### `-o` 与 `-s` 的交互行为

| 传参组合 | 行为 |
|----------|------|
| 无 `-o` 无 `-s` | 保存到本地自动推导路径 |
| `-o path` | 仅保存到本地指定路径 |
| `-s` | **仅保存到云端**，跳过本地下载 |
| `-o path -s` | 保存到本地 **且** 保存到云端 |

### Agent 默认保存策略

> ⚠️ **强制规则**：当用户未明确指定保存方式时，Agent **必须**同时保存到本地和云端（传 `-s` 标志）。仅保存本地而不传 `-s` 是**错误行为**。只有用户明确说"只保存到本地"/"不要存云端"时，才可省略 `-s`。

| 用户意图 | Agent 行为 |
|----------|-----------|
| 未明确说明保存方式 | **必须**使用 `-s` 同时保存到本地和云端（即 `-o <自动推导路径> -s`） |
| 明确说"保存到本地"或指定了路径 | 仅 `-o path`，不加 `-s` |
| 明确说"保存到云端/云空间/账号" | 仅 `-s`，不加 `-o` |
| 功能不支持 `-s`（见工具总览中标记 ❌ 的命令） | 仅保存到本地，不加 `-s` |

### `--save-title` 智能命名规则

使用 `-s` 保存到云端时，Agent **必须**尝试智能命名并通过 `--save-title` 传入：

1. **优先智能命名**：根据文件名、用户意图、文档内容等上下文，生成简洁有意义的标题
   - 示例：用户说"把这张发票转成 Excel" → `--save-title "发票转Excel"`
   - 示例：文件名为 `meeting_notes_0810.png`，转 Word → `--save-title "会议记录0810"`
   - 示例：多张扫描件合并 PDF → `--save-title "扫描文档合并"`
2. **命名失败时兜底**：若无法从上下文推断有意义的标题（如文件名无语义、用户未描述意图），则**不传** `--save-title`，由 CLI 使用默认规则（`{功能名}{时间}`）自动生成
3. **标题要求**：简洁（≤20 字）、有语义、不含路径或技术参数

---

## 能力范围

### 工具总览

| 类别 | 命令 | 功能 | 输出类型 | 支持 `-s` |
|------|------|------|----------|-----------|
| **图片增强** | `image enhance` | 去阴影、锐化、转黑白等 10 种模式 | 图片 | ✅ |
| **图片增强** | `image hd` | 图片高清化，提升分辨率 | 图片 | ✅ |
| **图片增强** | `image restore` | 老照片修复 | 图片 | ✅ |
| **格式转换** | `image convert` | 图片 → Word/Excel/TXT/Markdown | 文档 | ✅（TXT 除外） |
| **格式转换** | `image to-pdf` | 单图 → PDF | PDF | ✅ |
| **格式转换** | `pdf convert` | PDF → Word/Excel/TXT/Markdown | 文档 | ✅ |
| **格式转换** | `txt to-word` | TXT → Word | Word | ✅ |
| **水印处理** | `image watermark` | 图片添加文字水印 | 图片 | ✅ |
| **水印处理** | `pdf watermark` | PDF 添加文字水印 | PDF | ✅ |
| **水印处理** | `pdf remove-watermark` | PDF 去除水印 | PDF | ✅ |
| **翻译** | `image translate` | 图片翻译，保留排版 | 图片 | ✅ |
| **公式** | `image extract-formula` | 提取数学公式 | 图片 | ✅ |
| **合并** | `image merge-pdf` | 多图合并为 PDF（最多 100 张） | PDF | ✅ |
| **合并** | `image merge-excel` | 多图合并为 Excel（最多 100 张） | Excel | ✅ |
| **合并** | `image merge-word` | 多图合并为 Word（最多 100 张） | Word | ✅ |
| **PDF** | `pdf to-images` | PDF 逐页转图片 | 图片目录 | ✅ |
| **PDF** | `pdf to-images-zip` | PDF 转图片 ZIP | ZIP | ❌ |
| **识别** | `image ocr` | OCR 文字识别 | stdout 文本 | ❌ |
| **识别** | `image merge-text` | 多图 OCR 合并文本（最多 100 张） | stdout/文件 | ❌ |
| **检测** | `image validate` | 篡改/AI生成检测 | stdout JSON | ❌ |
| **编辑** | `image scan` | 图片版面分析，获取字符索引和 OSS key | stdout/JSON | ❌ |
| **编辑** | `image edit` | 基于 scan 结果替换/删除/移动文字 | 图片 | ✅ |

### 不支持的操作

- 无在线协同编辑
- 无文件版本管理
- 无视频/音频处理
- 无批量文件夹管理

---

## 参考资源路由

执行操作前，Agent **必须**先读取对应的参考文件获取完整参数和用法：

### 命令参考（必读）

| 触发条件 | 参考文件 | 内容 |
|----------|----------|------|
| 处理图片文件 | `references/image-processing.md` | 所有 image 命令的完整参数、模式值、示例 |
| 处理 PDF 文件 | `references/pdf-processing.md` | 所有 pdf 命令的完整参数、限制、示例 |
| 用户需求涉及多步操作 | `references/tool-combos.md` | 场景→命令组合映射 |

### 工作流参考（多步任务时必读）

| 触发条件 | 工作流文件 | 内容 |
|----------|-----------|------|
| 多张图片需要合并/批量转换 | `references/batch-convert.md` | 合并策略选择、分批处理逻辑 |
| 图片增强/高清化/修复 | `references/image-enhance.md` | 模式选择决策树 |
| OCR 识别/文字提取 | `references/ocr-extract.md` | 纯文本 vs Markdown vs Word 方案对比 |
| 图片翻译 | `references/translate.md` | 语言代码、多语言版本流程 |
| 水印添加/去除 | `references/watermark-protection.md` | 参数推荐、场景对照 |

---

## 意图路由规则

路由必须按以下优先级逐层判定，**禁止仅凭关键词直接跳转命令**：

### 第一层：判断输入文件类型

| 输入文件类型 | 可用命令组 |
|-------------|-----------|
| 图片（jpg/jpeg/png） | `image *` |
| PDF | `pdf *` |
| TXT/Markdown | `txt to-word` |
| 混合类型（图片+PDF） | 按文件类型分组各自处理，**不支持跨类型合并为单个产物** |

### 第二层：判断操作意图

根据用户动词、关键词和上下文确定操作类型：

| 操作类型 | 触发证据 | 命令方向 |
|----------|----------|----------|
| 格式转换 | "转Word"、"转Excel"、"转PDF"、"转Markdown" | `convert` / `to-pdf` / `merge-*` |
| OCR 识别 | "识别"、"OCR"、"提取文字" | `ocr` / `merge-text` / `pdf convert --format txt/md` |
| 图片增强 | "增强"、"去阴影"、"锐化"、"去摩尔纹" | `image enhance` |
| 高清化 | "高清"、"清晰"、"提升分辨率"、"模糊" | `image hd` |
| 照片修复 | "修复"、"老照片"、"划痕"、"褪色" | `image restore` |
| 水印处理 | "加水印"、"去水印" | `watermark` / `remove-watermark` / `enhance --mode 10` |
| 翻译 | "翻译" | `image translate` |
| 检测 | "检测"、"PS"、"篡改"、"AI生成" | `image validate` |
| 编辑 | "编辑图片文字"、"替换文字"、"修改文字"、"把X改成Y" | `image scan` → `image edit`（自动定位字符索引） |
| 公式提取 | "公式"、"LaTeX" | `image extract-formula` |

### 第三层：判断数量与产物

| 条件 | 路由 |
|------|------|
| 单个图片 → 格式转换 | `image convert --format xx` 或 `image to-pdf` |
| 多个图片 → 合并为 1 个文档 | `image merge-pdf/word/excel`（最多 100 张） |
| 多个图片 → 各自处理 | 逐个执行 |
| 单个 PDF → 格式转换 | `pdf convert --format xx` |
| 多个 PDF | 逐个执行（**不存在 PDF 合并命令**） |

### 第四层：目标格式与必填参数

| 输入 → 目标 | 正确命令 | 易错点 |
|-------------|----------|--------|
| 图片 → Word | `image convert --format word` | |
| 图片 → Excel | `image convert --format excel` | |
| 图片 → Markdown | `image convert --format md` | |
| 图片 → TXT | `image convert --format txt` | 不支持 `-s` |
| 图片 → PDF | `image to-pdf`（单张）或 `image merge-pdf`（多张） | ⚠️ **不是** `image convert --format pdf` |
| PDF → Word | `pdf convert --format word` | |
| PDF → Excel | `pdf convert --format excel` | |
| PDF → Markdown | `pdf convert --format md` | |
| PDF → 图片 | `pdf to-images` 或 `pdf to-images-zip` | |
| TXT → Word | `txt to-word` | |

### 意图消歧规则

当用户表述同时命中多个操作时，按以下规则消歧：

| 冲突场景 | 消歧规则 |
|----------|----------|
| "锐化清晰一点"：enhance --mode 2 vs hd | 若原图模糊/低分辨率 → `hd`；若原图清晰但需锐化细节 → `enhance --mode 2`；不确定时追问 |
| "扫描"：image scan vs to-pdf | 若有"编辑"意图 → `scan` + `edit`；否则默认理解为"生成 PDF" → `to-pdf` |
| "OCR"：纯文本 vs Markdown vs Word | 追问用户需要什么格式；默认推荐 `convert --format md`（保留格式） |
| "修复"：restore vs enhance | 若提到"老照片/划痕/褪色" → `restore`；否则按具体问题选 enhance 模式 |
| "检测"：篡改 vs AI 生成 | 若提到"PS/篡改/修改" → mode 1；若提到"AI/生成/假的" → mode 2；不确定时追问 |
| "去水印"：PDF vs 图片 | 按输入文件类型自动选择（PDF → `pdf remove-watermark`，图片 → `enhance --mode 10`） |

**原则：存在会改变命令选择的歧义时，追问用户而非猜测。**

### 常见错误路由（Agent 必须避免）

| 用户请求 | 错误路由 | 正确路由 | 原因 |
|----------|----------|----------|------|
| "合并两个 PDF" | ~~`image merge-pdf`~~ | 当前不支持，告知用户 | `image merge-pdf` 只接受图片输入 |
| "识别这个 PDF 的文字" | ~~`image ocr`~~ | `pdf convert --format txt/md` | `image ocr` 只接受图片 |
| "扫描这些照片生成 PDF" | ~~`image scan`~~ | `image to-pdf` 或 `image merge-pdf` | `image scan` 是版面分析 |
| "去掉图片上的水印" | ~~`pdf remove-watermark`~~ | `image enhance --mode 10` | `pdf remove-watermark` 只处理 PDF |
| "图片转 PDF" | ~~`image convert --format pdf`~~ | `image to-pdf` / `image merge-pdf` | `convert_image` 不支持 PDF 目标 |
| "把 a.jpg 和 b.pdf 合成一个 Word" | ~~静默分别处理~~ | 告知不支持跨类型合并 | 输入类型不同，无法合并为单产物 |

---

## 错误速查表

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `认证失败，请执行 camscanner-cli auth login` | Token 过期或未登录 | 运行 `camscanner-cli auth login` |
| `文件不存在` | 输入路径错误 | 检查文件路径是否正确 |
| `file size exceeds the maximum limit` | 文件超过 40MB | 压缩文件后重试 |
| `rate limit exceeded` (429) | 调用过于频繁 | 等待 10 秒后重试 |
| `txt 格式不支持保存为云文档` | TXT 不在云文档支持类型中 | 改用 `--format md` |
| HTTP 504 | 后端服务超时 | 等 5 秒重试 1 次 |
| HTTP 500 | 服务端内部错误 | 等 5 秒重试 1 次 |

### 重试策略

| 操作类型 | 幂等 | 重试安全 |
|----------|------|----------|
| 所有转换/增强命令 | ✅ | 可安全重试 |
| `-s` 保存云文档 | ❌ | 重试可能产生重复文档（可接受） |
| `image edit` | ✅ | 可重试 |

---

## 安全约束

- Token 由系统密钥链管理，Skill 不存储、不记录
- **数据流说明**：
  - 输入文件会上传到扫描全能王服务端进行处理，处理期间文件临时存储于服务端
  - 转换产物会生成临时 `file_id`，通过该 ID 下载结果
  - 使用 `-s` 时，处理结果会持久保存到用户的扫描全能王账号内
  - 使用 `-o` 时，结果下载到本地后，服务端临时文件按服务端保留策略自动清理
  - Skill 本身不额外缓存或持久化任何文档内容
- **输出路径冲突保护**：CLI 的 `-o` 会静默覆盖已有文件。Agent 在执行写入操作前**必须**检查输出路径是否已存在文件，若存在则：
  1. 优先在文件名后追加序号（如 `output_1.jpg`、`output_2.jpg`）
  2. 或向用户确认是否覆盖
  3. 禁止未经确认直接覆盖用户已有文件
- **多文件参数规范**：禁止使用 `*.jpg` 等 glob 通配符传递多文件参数。Agent **必须**：
  1. 先列出目录中的文件并按自然排序（数字感知：`page2` < `page10`）确定页序
  2. 逐个以带引号的完整路径传递，确保文件名含空格或特殊字符时不出错
  3. 执行前向用户确认文件列表和顺序
  ```bash
  # 正确：显式列出、带引号、顺序明确
  camscanner-cli image merge-pdf "scan_01.jpg" "scan_02.jpg" "scan_03.jpg" -s

  # 错误：glob 顺序不确定，路径不安全
  camscanner-cli image merge-pdf *.jpg -s
  ```
