<div align="right">

[English](#english) | **[中文](#中文)**

</div>

---

# yescan-office-qoder

[![ClawHub Downloads](https://img.shields.io/badge/ClawHub-837%20downloads-blue?logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)](https://clawhub.ai/mozhihuidage/yescan-transoffice-universal)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![QoderWork](https://img.shields.io/badge/QoderWork-Agent%20Skill-orange)](https://qoder.com)

由**夸克扫描王**提供的图片转 Office / PDF 技能，支持将图片、截图或扫描件转换为可编辑的 Word、Excel 或 PDF 文档，尽量还原原始版式。

本技能是 [QoderWork](https://qoder.com) Agent Skill，可在 QoderWork 桌面端安装并通过自然语言调用。

> 📦 ClawHub 主页：[mozhihuidage/yescan-transoffice-universal](https://clawhub.ai/mozhihuidage/yescan-transoffice-universal)

---

## 功能特性

- **图片转 Excel** — 复杂表格、合并单元格、财务报表等场景，输出可编辑 `.xlsx`
- **图片转 Word** — 合同、长文、产品说明书等图文混排内容，输出 `.docx`
- **图片转 PDF** — 手写笔记、设备铭牌、白板草图等，输出标准 `.pdf`
- **版式还原** — 保留原始排版、段落结构与字体样式

## 支持的转换场景（scene）

共 3 个场景，Agent 按下表顺序匹配，命中第一个即停止。

| # | 场景名称 | Scene 标识 | 触发意图 |
|---|---|---|---|
| 1 | 图片转 Excel | `image-to-excel` | 将含表格/数据/报表的图片转为 `.xlsx` |
| 2 | 图片转 Word | `image-to-word` | 将图片/截图/扫描件转为 `.docx` |
| 3 | 图片转 PDF | `image-to-pdf` | 将图片/截图/扫描件转为 `.pdf` |

## 安装前提

### 1. 获取密钥

本技能需要**夸克扫描王开放平台**的 API Key（AI Agent 接入类型）。

前往 [scan.quark.cn/business](https://scan.quark.cn/business) 开发者后台：

1. 注册 / 登录（手机号）
2. 进入「业务中心」→「密钥管理」
3. 创建 Key，选择 **AI Agent 接入**（Key ID 前缀为 `AI_`）
4. 复制 Key 值

### 2. 配置密钥（推荐写入配置文件）

将 Key 写入 `~/.yescan_env`，技能每次执行会自动读取，无需重启会话：

**Linux / macOS**
```bash
echo 'SCAN_WEBSERVICE_KEY=<your_api_key_here>' > ~/.yescan_env
```

**Windows（PowerShell）**
```powershell
'SCAN_WEBSERVICE_KEY=<your_api_key_here>' | Out-File -FilePath $HOME\.yescan_env -Encoding utf8
```

> 也可以使用 QoderWork 内置的 `yescan-key-setup` 技能自动完成注册和配置。

## 使用方式

安装本技能后，在 QoderWork 中直接用自然语言调用即可：

```
帮我把这张财务报表截图转换成 Excel 文件
把这张会议记录的拍照图片转成 Word 文档
把这张合同照片处理一下,转成清晰的 PDF 存档
```

Agent 会根据意图自动匹配对应的 scene 并调用底层脚本。

### 底层命令行接口

```bash
python3 scripts/scan.py --scene "image-to-excel" --url "https://example.com/table.jpg"
python3 scripts/scan.py --scene "image-to-word" --path "/local/path/to/contract.png"
python3 scripts/scan.py --scene "image-to-pdf" --base64 "<base64 编码的图片数据>"
```

支持的输入方式：URL、本地文件路径、Base64 编码。

## 输出格式

脚本执行成功后，标准输出返回 JSON 对象，包含转换结果文件的下载链接或 Base64 数据。

当 API 响应中包含 `FileBase64` 字段时，底层脚本会自动将其解码并保存为本地文件，同时在返回的 JSON `data` 中追加 `path` 字段（如 `"/tmp/xx.docx"`），方便后续直接访问。

## 约束与限制

- 单张图片大小不超过 **5 MB**
- 支持的图片格式：`jpg / jpeg / png / gif / bmp / webp / tiff / wbmp`
- 每次调用处理单一转换意图，不支持同时输出多种格式
- 图片数据会发送至 `scan-business.quark.cn` 进行处理，不会永久保存
- 转换结果文件保存至 `/tmp`，持续存在直到手动清理

## 目录结构

```
yescan-office-qoder/
├── SKILL.md                          # 技能定义（QoderWork Agent 读取）
├── scripts/
│   ├── scan.py                       # 主执行脚本（Python 3.9+）
│   ├── file_saver.py                 # Base64 文件自动保存模块
│   └── common/                       # 公共工具模块
├── evals/                            # 评测用例
├── references/                       # 参考文档
└── LICENSE                           # MIT License
```

## 相关链接

- [夸克扫描王开放平台](https://scan.quark.cn/business) — 密钥申请、API 文档
- [ClawHub 技能页](https://clawhub.ai/mozhihuidage/yescan-transoffice-universal) — 安装、下载量、评分
- [QoderWork](https://qoder.com) — Agent 运行环境
- [yescan-ai GitHub Org](https://github.com/yescan-ai) — 更多技能

## 许可证

[MIT License](LICENSE)

---

<a id="english"></a>

# yescan-office-qoder

[![ClawHub Downloads](https://img.shields.io/badge/ClawHub-837%20downloads-blue?logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)](https://clawhub.ai/mozhihuidage/yescan-transoffice-universal)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![QoderWork](https://img.shields.io/badge/QoderWork-Agent%20Skill-orange)](https://qoder.com)

An image-to-Office/PDF conversion skill powered by **Quark Scan King**. Converts images, screenshots, or scanned documents into editable Word, Excel, or PDF files with high-fidelity layout restoration.

This is a [QoderWork](https://qoder.com) Agent Skill — install it in the QoderWork desktop app and invoke it with natural language.

> 📦 ClawHub page: [mozhihuidage/yescan-transoffice-universal](https://clawhub.ai/mozhihuidage/yescan-transoffice-universal)

---

## Features

- **Image to Excel** — Complex tables, merged cells, financial reports → editable `.xlsx`
- **Image to Word** — Contracts, long-form text, product manuals with mixed text/graphics → `.docx`
- **Image to PDF** — Handwritten notes, equipment nameplates, whiteboard sketches → standard `.pdf`
- **Layout Restoration** — Preserves original formatting, paragraph structure, and font styles

## Supported Scenes

3 scenes in total. The agent matches in the order listed below and stops at the first hit.

| # | Scene Name | Scene ID | Trigger |
|---|---|---|---|
| 1 | Image to Excel | `image-to-excel` | Convert images containing tables / data / reports to `.xlsx` |
| 2 | Image to Word | `image-to-word` | Convert images / screenshots / scans to `.docx` |
| 3 | Image to PDF | `image-to-pdf` | Convert images / screenshots / scans to `.pdf` |

## Prerequisites

### 1. Get an API Key

This skill requires an API Key (AI Agent type) from the **Quark Scan King Open Platform**.

Visit the [scan.quark.cn/business](https://scan.quark.cn/business) developer console:

1. Register / log in (phone number)
2. Go to **Business Center** → **Key Management**
3. Create a key, select **AI Agent** (Key ID prefix: `AI_`)
4. Copy the key value

### 2. Configure the Key (Recommended: Config File)

Write the key to `~/.yescan_env`. The skill reads it automatically on each run — no session restart required.

**Linux / macOS**
```bash
echo 'SCAN_WEBSERVICE_KEY=<your_api_key_here>' > ~/.yescan_env
```

**Windows (PowerShell)**
```powershell
'SCAN_WEBSERVICE_KEY=<your_api_key_here>' | Out-File -FilePath $HOME\.yescan_env -Encoding utf8
```

> Alternatively, use the built-in `yescan-key-setup` skill in QoderWork for automated registration and configuration.

## Usage

After installing the skill, invoke it with natural language in QoderWork:

```
Convert this financial report screenshot to an Excel file
Turn this photo of meeting notes into a Word document
Process this contract photo and convert it to a clean PDF for archiving
```

The agent will automatically match the appropriate scene and invoke the underlying script.

### CLI Interface

```bash
python3 scripts/scan.py --scene "image-to-excel" --url "https://example.com/table.jpg"
python3 scripts/scan.py --scene "image-to-word" --path "/local/path/to/contract.png"
python3 scripts/scan.py --scene "image-to-pdf" --base64 "<base64-encoded image data>"
```

Supported input methods: URL, local file path, Base64 encoding.

## Output Format

On success, the script outputs a JSON object to stdout containing download links or Base64 data for the converted file.

When the API response includes a `FileBase64` field, the underlying script automatically decodes it and saves it as a local file, then appends a `path` field (e.g., `"/tmp/xx.docx"`) to the returned JSON `data` for direct downstream access.

## Constraints & Limitations

- Maximum image size: **5 MB**
- Supported formats: `jpg / jpeg / png / gif / bmp / webp / tiff / wbmp`
- Single conversion intent per call — cannot output multiple formats simultaneously
- Image data is sent to `scan-business.quark.cn` for processing and is not permanently stored
- Converted files are saved to `/tmp` and persist until manually cleaned up

## Repository Structure

```
yescan-office-qoder/
├── SKILL.md                          # Skill definition (read by QoderWork Agent)
├── scripts/
│   ├── scan.py                       # Main execution script (Python 3.9+)
│   ├── file_saver.py                 # Auto-save module for Base64 files
│   └── common/                       # Shared utility modules
├── evals/                            # Evaluation test cases
├── references/                       # Reference documentation
└── LICENSE                           # MIT License
```

## Links

- [Quark Scan King Open Platform](https://scan.quark.cn/business) — API key & documentation
- [ClawHub Skill Page](https://clawhub.ai/mozhihuidage/yescan-transoffice-universal) — Install, downloads & ratings
- [QoderWork](https://qoder.com) — Agent runtime environment
- [yescan-ai GitHub Org](https://github.com/yescan-ai) — More skills

## License

[MIT License](LICENSE)
