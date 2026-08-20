# Liteparse Usage

> 来源: pdf-ocr-md v3.3.0 SKILL.md | 从主文件拆分，保持原内容不变

## C：LiteParse — 文本层 PDF 快速解析（Rust）

LlamaIndex 出品（8k⭐），Rust 核心，轻量零依赖。

### 安装

```bash
# 已安装: ~/.venvs/liteparse/ + ~/.local/bin/lit
pip install liteparse              # Python
npm i @llamaindex/liteparse        # Node.js
cargo install liteparse            # Rust CLI
```

### 核心命令

```bash
# 文本层PDF → 文本（推荐 --no-ocr，跳过不必要的OCR）
lit parse input.pdf --no-ocr -o output.txt

# 扫描件PDF → 文本（内置Tesseract，中文用 --ocr-language chi_sim）
lit parse input.pdf --ocr-language chi_sim -o output.txt

# 批量处理
lit batch-parse ./input-dir ./output-dir

# 生成截图（用于LLM视觉分析）
lit screenshot input.pdf -o ./screenshots --dpi 200
```

### 关键特性

| 特性 | 说明 |
|------|------|
| 文本层提取 | PDFium，**0.9ms/页**，比 OpenDataLoader 快 300x |
| 多格式输入 | PDF / 图片（PNG/JPG） |
| OCR 引擎 | 内置 Tesseract；可接 HTTP OCR server（PaddleOCR/自定义） |
| 输出格式 | 纯文本 / JSON（含 bounding box） |
| 截图输出 | `lit screenshot` 生成整页 PNG（支持 --target-pages） |
| 语言绑定 | Python / Node.js / Rust CLI / WASM |
| 平台 | Linux / macOS / Windows |
| License | Apache 2.0 |

### 局限

| 局限 | 说明 | 替代方案 |
|------|------|---------|
| 中文 OCR 准确率差 | Tesseract chi_sim ~80% vs PaddleOCR ~97% | 退到 `pdf2md`（见 B 节） |
| Office 文档 | DOCX/XLSX/PPTX 需 LibreOffice 转换 | 暂不支持，需时再装 |
| 表格识别 | 无版面分析，纯坐标提取 | 退到 `pdf2md`（docling 版面分析） |

### 机器资源

- 内存：LiteParse 进程 ~50MB（含 Tesseract 模型）
- 磁盘：`~/.venvs/liteparse/` ~35MB + tessdata ~15MB
- 安装：`pip install liteparse` 一行即可

---