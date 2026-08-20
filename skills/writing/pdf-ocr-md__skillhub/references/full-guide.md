---
name: pdf-ocr-md
version: 3.3.0
description: 当用户需要从 PDF、图片、扫描件中提取文字内容时使用。适合处理合同、发票、报告等文档，尤其是中文扫描件、手机拍照的弯曲页面、歪斜的文档。支持 PP-OCRv6 三档模型 (Tiny/Small/Medium)。
related_skills:
  - ocr-and-documents
---

# pdf-ocr-md — PDF → OCR → 结构化 Markdown

> **环境**：
> - `lit` — LiteParse 快速文本层解析（`~/.venvs/liteparse/`，Rust 核心）
> - `pdf2md` — PaddleOCR 中文扫描件（`~/.venvs/paddleocr/`）
> - `ocr6` — **PP-OCRv6** 三档模型（`~/.venvs/ppocrv6/`，ONNX Runtime），见 F 节
> - `prep` — 文档预处理（含倾斜/方向/展平），见 D 节
>
> **快速选择**：不确定类型 → `lit parse file.pdf --no-ocr`，空结果再退到 `prep` + `ocr6`
>
> **曾用名**：`pdf2md`（因 SkillHub/ClawHub 已被占用，v1.1.0 起更名）
>
> **一体化 skill**：合并了原 `opendataloader-pdf`、`paddleocr-chinese` 和 `pdf-ocr-md`。
> 详见 `references/opendataloader.md` 和 `references/paddleocr.md`。

---

## 用法

### 快速选择（推荐）

```bash
# ① 先试试 LiteParse（文本层PDF秒出）
lit parse input.pdf --no-ocr -o output.txt

# ② 如果输出为空，说明是扫描件
#     按需选模型档位（速度从快到慢：tiny > small > medium）
python scripts/pdf_ocr_v6.py input.pdf --tier tiny -o ./output
```

### 直接指定

```bash
# 文本层PDF（电子合同/报表）
lit parse input.pdf --no-ocr -o output.txt

# 中文扫描件（合同/发票）— 先预处理
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all
pdf2md ./preprocessed/input_p001.jpg -o ./output_dir

# 或快速跳过预处理（平整的扫描件）
pdf2md input.pdf -o ./output_dir
```

输出：
- LiteParse: `output.txt` — 纯文本（版面保持）
- pdf2md: `output_dir/input.md` — Markdown + `input.json` + `input_images/`
- 预处理: `preprocessed/` — 经过校正/展平的图片

## 工作流总览

```
输入文档
  ├── 有文本层 → LiteParse 提取 (~0.9ms/页)
  │
  └── 无文本层（扫描件）
       ├── ① 选择模型档位
       │    ├── Tiny  (1.5 MB)  极速
       │    ├── Small (7.7 MB)  均衡
       │    └── Medium(34.5 MB) 高精度
       │
       ├── ② 预处理（根据文档状况）
       │    ├── --deskew    倾斜校正
       │    ├── --orient    方向校正
       │    ├── --unwarp    文档展平
       │    └── --all       全部
       │
       └── ③ PP-OCRv6 OCR → 文本 / JSON
```
> **LiteParse 比 OpenDataLoader 快约 300 倍**（0.9ms vs 300ms），且不用装 Java 11。

## 性能参考（CPU）

| 类型 | 引擎 | 单页耗时 | 17页合同 |
|------|------|---------|----------|
| 文本层 PDF | LiteParse --no-ocr | **~0.9ms** | **~15ms** |
| 文本层 PDF | OpenDataLoader（旧） | ~15ms | ~300ms |
| **PP-OCRv6 Tiny** | ONNX Runtime (CPU) | **~3-8s** | **~1-2min** |
| **PP-OCRv6 Small** | ONNX Runtime (CPU) | **~8-15s** | **~2-4min** |
| **PP-OCRv6 Medium** | ONNX Runtime (CPU) | **~15-30s** | **~4-8min** |
| **预处理-倾斜校正** | OpenCV Hough | **~300ms** | **~5s** |
| **预处理-文档展平** | OpenCV 透视变换 | **~500ms** | **~8s** |
| 扫描件（中文） | PaddleOCR PP-OCRv4（旧） | ~15s | ~4.5min |
| 扫描件（中文） | Tesseract chi_sim | ~170ms | ~3s |
| 扫描件（英文） | LiteParse 默认 | ~170ms | ~3s |

## 准确率

| 引擎 | 中文扫描件 |
|------|-----------|
| PP-OCRv6 Medium | **~0.425 ed** (OmniDocBench) |
| PP-OCRv6 Small | **~0.443 ed** |
| PP-OCRv6 Tiny | **~0.446 ed** |
| Apple Vision (macOS) | ~0.448 ed |
| PaddleOCR PP-OCRv4 | **~97%+** |
| + 预处理 | **~98%+** (歪斜/弯曲照片) |

## 注意事项

- 首次运行自动下载模型（版面分析 ~770 weights + OCR det/cls/rec ~17MB）
- 模型从 hf-mirror.com / modelscope.cn 下载，国内畅通
- 机器有 3.6GB 内存，PaddleOCR 冷启动 ~300MB 峰值可承受
- 中文 OCR 场景：**LiteParse(Tesseract) ~80% → 退到 PaddleOCR ~97%+**，准确率优先时用 `pdf2md`
- 英文 / Office 文档场景可优先试 LiteParse（见 C 节）
- **预处理能提升照片/弯曲文档的 OCR 准确率 1~5%**，对平整扫描件效果不明显
- **结构化解析**（doc-parsing）会额外增加版面分析时间, 但输出更结构化

---

## A：OpenDataLoader — 文本层 PDF 解析

适用于有文本层的 PDF（电子合同、报表、PDF/A 文件）。支持的 CLI 和 Python SDK，完整用法详见 `references/opendataloader.md`。

### 快速启动

```bash
# 安装
python3 -m venv ~/.venvs/opendataloader
~/.venvs/opendataloader/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opendataloader-pdf

# CLI
opendataloader-pdf input.pdf -f json,markdown -o ./output

# Python
from opendataloader_pdf import convert
convert("input.pdf", output_dir="./out", format="json,markdown")
```

### 关键特性
- **输出格式**：JSON（含 bounding box/font/size）、Markdown、HTML、Text、Tagged PDF
- **表格检测**：`--table-method cluster` 模式
- **脱敏**：`--sanitize` 替换邮箱/电话/银行卡号
- **页码范围**：`--pages "1,3,5-7"` 指定页
- **性能**：~0.015s/页（纯 Java 本地模式，无网络）

### 环境前提
- Java 11+ (`java -version`)
- PyPI 官方源可能超时 → 用清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`

---

## B：PaddleOCR — 中文扫描件 OCR

适用于无文本层的扫描件 PDF（合同、发票、报纸）。详见 `references/paddleocr.md`。

### 快速启动

```bash
# 环境
python3 -m venv ~/.venvs/paddleocr
~/.venvs/paddleocr/bin/pip install paddlepaddle==2.6.2 "numpy<2" paddleocr==2.7.3

# CLI —— 逐张 OCR 图片
~/.venvs/paddleocr/bin/python -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch')
result = ocr.ocr('page.png')
for line_info in result[0]:
    text = line_info[1][0]; conf = line_info[1][1]
    print(f'{conf:.2f} {text}')
"
```

### 关键特性
- PP-OCRv4 模型，简体中文 ~98%，繁体 ~95%
- 支持竖排文字、手写体
- 公章/签名基本可识别（Tesseract 在此场景乱码）
- 可配合 `pdf2image` 拆分扫描件 PDF

### 精度对比

| 引擎 | 简体中文 | 繁体中文 | 公章/签名 | 竖排 |
|------|---------|---------|-----------|------|
| Tesseract chi_sim | ~80% | ~60% | ❌ 乱码 | ❌ |
| **PaddleOCR PP-OCRv4** | **~98%** | **~95%** | ✅ 基本正确 | ✅ |

### 常见问题
- **错字多**：提高 DPI 到 400-600，降低过滤阈值到 0.3
- **表格差**：对密集表格用 docling（pdf2md 集成管线）
- **GPU 加速**：`pip install paddlepaddle-gpu==2.6.2` + `use_gpu=True`

### Python 3.13 兼容性注意事项

> ⚠️ **重要**：PaddleOCR 在 Python 3.13 环境下存在多个兼容性问题，需手动修复。

#### 问题1：imghdr 模块缺失

**现象：**
```
ModuleNotFoundError: No module named 'imghdr'
```

**原因：** Python 3.13 移除了 `imghdr` 模块（原用于检测图像类型）

**解决方案：** 创建兼容 shim 模块

```python
# 保存到 site-packages/imghdr.py
"""imghdr module shim for Python 3.13+ compatibility"""
def whatfile(f):
    return None

def what(buf, h=None):
    return None
```

#### 问题2：np.sctypes 移除

**现象：**
```
AttributeError: module 'numpy' has no attribute 'sctypes'
```

**原因：** NumPy 2.0 移除了 `np.sctypees` 属性（`imgaug` 包使用了该属性）

**解决方案：** 修改 `site-packages/imgaug/imgaug.py` 第44-46行

```python
# 原代码（不可用）：
# NP_FLOAT_TYPES = set(np.sctypes["float"])
# NP_INT_TYPES = set(np.sctypes["int"])
# NP_UINT_TYPES = set(np.sctypes["uint"])

# 修复后：
NP_FLOAT_TYPES = {np.float16, np.float32, np.float64}
NP_INT_TYPES = {np.int8, np.int16, np.int32, np.int64}
NP_UINT_TYPES = {np.uint8, np.uint16, np.uint32, np.uint64}
```

#### 问题3：OpenCV 与 NumPy 2.x 不兼容

**现象：**
```
ImportError: numpy.core.multiarray failed to import
```

**原因：** `opencv-python` 4.6 是针对 NumPy 1.x 编译的，与 NumPy 2.x ABI 不兼容

**解决方案：** 改用 `opencv-python-headless` 4.13.0.92+

```bash
~/.venvs/paddleocr/bin/pip uninstall opencv-python -y
~/.venvs/paddleocr/bin/pip install opencv-python-headless --no-cache-dir
```

#### 问题4：scikit-image DLL 加载失败（Windows）

**现象：**
```
ImportError: DLL load failed while importing _cython_blas
```

**原因：** Windows 安全策略阻止未签名的 C 扩展 DLL

**解决方案：**
- 方案A：使用预编译的 wheel（推荐）
- 方案B：临时关闭 Windows Defender 实时保护
- 方案C：使用 WSL2 或 Linux 环境

#### 推荐的 Python 3.13 安装命令

```bash
# 环境
python3 -m venv ~/.venvs/paddleocr
source ~/.venvs/paddleocr/bin/activate

# 安装（使用 PaddlePaddle 3.0.0，支持 NumPy 2.x）
pip install paddlepaddle==3.0.0
pip install "numpy>=2" paddleocr==2.7.3
pip uninstall opencv-python -y
pip install opencv-python-headless --no-cache-dir

# 创建 imghdr shim
cat > ~/.venvs/paddleocr/lib/python3.13/site-packages/imghdr.py << 'EOF'
def whatfile(f):
    return None
def what(buf, h=None):
    return None
EOF

# 修补 np.sctypes 问题
# 手动编辑 ~/.venvs/paddleocr/lib/python3.13/site-packages/imgaug/imgaug.py
```

---

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

## D：文档预处理 — 扫描件 OCR 增强

适用于质量不佳的扫描件（手机拍照、弯曲书页、倾斜/倒置的文档）。
预处理后 PaddleOCR 的中文准确率可从 ~97% 提升到 ~98%+。

### 安装

```bash
pip install opencv-python-headless numpy Pillow pdf2image
```

### CLI 命令

```bash
# 全部预处理（推荐）
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all

# 仅倾斜校正
python scripts/pdf_preprocess.py input.jpg -o ./output --deskew

# 仅方向校正
python scripts/pdf_preprocess.py input.jpg -o ./output --orient

# 仅文档展平（弯曲/透视照片）
python scripts/pdf_preprocess.py input.jpg -o ./output --unwarp

# PDF 全页 + 高DPI
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all --dpi 400

# 预览模式（显示对比图，不保存）
python scripts/pdf_preprocess.py input.jpg --preview --all
```

### 预处理项说明

| 预处理 | CLI 参数 | 适用场景 | 效果 |
|--------|---------|---------|------|
| **倾斜校正** (deskew) | `--deskew` | 扫描件轻微歪斜 (<15°) | 自动检测角度并旋转正位 |
| **方向校正** (orient) | `--orient` | 页面旋转/倒置 | 检测文本方向并自动旋转到正位 |
| **文档展平** (unwarp) | `--unwarp` | 手机拍的弯曲/透视变形的文档 | 自动检测边界, 透视变换展平 |

### 工作流集成

```bash
# 完整管线: 预处理 → pdf2md
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all
pdf2md ./preprocessed/input_p001.jpg -o ./output_dir

# 对于平整扫描件, 预处理效果不大, 可跳过
pdf2md input.pdf -o ./output_dir
```

### 预处理效果预测

| 文档类型 | 建议 | 预期提升 |
|---------|------|---------|
| 平整扫描件 (A4 扫描仪) | 跳过预处理 | OCR 已很好, 无明显提升 |
| 轻微歪斜 (< 15°) | `--deskew` | 准确率 +1~2% |
| 照片 (手机拍文档) | `--deskew --unwarp` | 准确率 +3~5% |
| 页面倒置/旋转 | `--orient` | 从乱码到正常识别 |
| 弯曲书页 | `--unwarp` | 准确率 +2~4% |

### 脚本参考

预处理脚本位于 `scripts/pdf_preprocess.py`，支持作为 Python 模块导入使用：

```python
from scripts.pdf_preprocess import preprocess_image, deskew_image, unwarp_image
import cv2

img = cv2.imread('scan.jpg')
processed = preprocess_image(img, deskew=True, orient=True, unwarp=True)
cv2.imwrite('corrected.jpg', processed)

---

## E：结构化文档解析 — 版面分析 + 表格提取

利用 docling 进行深度版面分析, 输出结构化 Markdown 和 JSON。
保留文档的标题层级、表格、列表、图片标注等逻辑结构。

### 安装

```bash
pip install docling
# docling 2.97+ 会自动安装版面分析模型
```

### CLI 命令

```bash
# 结构化解析为 Markdown + JSON
python scripts/pdf_parse_structured.py input.pdf -o ./output

# 禁用 OCR (文本层 PDF, 更快)
python scripts/pdf_parse_structured.py input.pdf -o ./output --no-ocr

# 仅输出 Markdown
python scripts/pdf_parse_structured.py input.pdf -o ./output --md-only

# 仅输出 JSON (含完整版面坐标)
python scripts/pdf_parse_structured.py input.pdf -o ./output --json-only

# 仅前3页
python scripts/pdf_parse_structured.py input.pdf -o ./output --pages "1-3"
```

### 输出说明

```
output/
├── input.md        ← 结构化 Markdown (标题层级/表格/列表)
└── input.json      ← 完整解析结果 (含版面坐标、表格网格、元数据)
```

### JSON 数据结构

```json
{
  "metadata": {
    "file": "合同.pdf",
    "pages": 17,
    "has_ocr": true
  },
  "items": [
    { "type": "heading", "text": "第一章 总则", "bbox": {...} },
    { "type": "paragraph", "text": "根据《中华人民共和国...", "bbox": {...} },
    { "type": "list", "text": "甲乙双方应遵守..." }
  ],
  "tables": [
    {
      "page": 3,
      "grid": [["项目", "金额"], ["服务费", "10000"]],
      "markdown": "| 项目 | 金额 |\n| --- | --- |\n| 服务费 | 10000 |"
    }
  ]
}
```

### 工作流集成

```bash
# 完整管线: 预处理 → 结构化解析
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all
python scripts/pdf_parse_structured.py ./preprocessed/input_p001.jpg -o ./output

# 也可直接解析
python scripts/pdf_parse_structured.py input.pdf -o ./output
```

### 关键特性

| 特性 | 说明 |
|------|------|
| 版面分析 | docling 深度学习版面分析, 识别标题/段落/表格/列表 |
| 表格提取 | 自动检测表格边界, 输出 Markdown 表格 + JSON 网格 |
| 标题层级 | 保留文档逻辑结构 |
| 元数据 | 页数、页码、元素统计 |
| 结构化 JSON | 含 bbox 坐标, 可用于后续处理 |
| 预处理兼容 | 可与 D 节预处理管线串联 |

---

## F：PP-OCRv6 — 三档模型 OCR（ONNX Runtime + GPU 加速）

PaddleOCR 最新 v6 模型家族，使用 ONNX Runtime + DirectML 本地推理。
默认 GPU 加速，Intel/AMD/NVIDIA GPU 均支持（需 ）。
三档可选：**Tiny (1.5MB) / Small (7.7MB) / Medium (34.5MB)**。

### 安装

```bash
# 创建虚拟环境并安装
python3 -m venv ~/.venvs/ppocrv6
~/.venvs/ppocrv6/bin/pip install onnxruntime opencv-python-headless numpy Pillow pdf2image

# 下载模型（从 GitHub Releases）
# 项目: https://github.com/andyhuo520/ppocrv6-studio
```

### CLI 命令

```bash
# Tiny 模型（极速，1.5MB，可浏览器运行）
python scripts/pdf_ocr_v6.py input.jpg --tier tiny -o output.txt

# Small 模型（均衡，7.7MB）
python scripts/pdf_ocr_v6.py input.jpg --tier small -o output.txt

# Medium 模型（高精度，34.5MB）
python scripts/pdf_ocr_v6.py input.pdf --tier medium -o ./output

# 指定最低置信度
python scripts/pdf_ocr_v6.py input.jpg --tier medium --min-conf 0.6 -o output.txt
```

### 输出

```
output/
├── input.txt      ← 纯文本（每页分段）
└── input.json     ← 完整结果（含置信度、文本框坐标）
```

### 模型档位对比

| 档位 | 参数量 | 模型大小 | 适用场景 |
|------|--------|---------|---------|
| Tiny | 极轻量 | **1.5 MB** | 快速预览、可浏览器端运行 |
| Small | 轻量 | **7.7 MB** | 日常使用，性能均衡 |
| Medium | 标准 | **34.5 MB** | 高精度场景（合同/发票/复杂文档） |

### 文档类型建议

| 文档类型 | 推荐档位 | 理由 |
|---------|---------|------|
| 平整扫描件 | Tiny 或 Small | 速度优先，Tiny 效果已足够 |
| 手机拍照件 | Small | 平衡速度与准确率 |
| 复杂文档/小字 | **Medium** | 精度优先 |
| 批量处理 | Tiny | 优先速度 |

### 迁移说明

> PP-OCRv6 是比 PP-OCRv4 更轻量、效果更好的新一代模型。
> 默认 GPU 加速（DirectML），CPU 6-9x 提速。无 GPU 时自动回退 CPU。
> 旧版 PaddleOCR（PP-OCRv4）管线保留为备选。
```