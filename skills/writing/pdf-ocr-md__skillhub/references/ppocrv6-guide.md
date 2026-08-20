# PP-OCRv6 完整指南

> 来源: pdf-ocr-md v3.3.0 SKILL.md F 节 | 更新: 2026-07-30（补充官方版 v3.7.0 + 社区项目新功能）

## 概述

PaddleOCR 最新 v6 模型家族（官方 v3.7.0, 2026-06-11），使用 ONNX Runtime + DirectML/CoreML 本地推理。
三档可选：**Tiny (1.5MB) / Small (7.7MB) / Medium (34.5MB)**。

**新特性（vs v3.3.0 知识库）**：
- 🔥 **统一 50 语言模型**：中文/英文/日文 + 46 种拉丁语言，无需切换模型
- 🔥 **Apple Silicon CoreML 加速**：M 系列芯片自动启用（安装 `onnxruntime-silicon`）
- 🔥 **浏览器端运行**：Tiny 模型通过 ONNX Runtime Web 零依赖运行
- 🔥 **Web 工作台**：FastAPI + 单页 UI，拖拽上传、批量处理、结果导出(CSV/Markdown/Excel)

## 模型来源

| 来源 | 链接 | 用途 |
|------|------|------|
| PaddleOCR 官方 | https://github.com/PaddlePaddle/PaddleOCR | 模型研发、论文、v3.7.0 API |
| HuggingFace | https://huggingface.co/collections/PaddlePaddle/pp-ocrv6 | 模型下载 |
| ModelScope | https://www.modelscope.cn/collections/PaddlePaddle/PP-OCRv6 | 模型下载（国内镜像） |
| ppocrv6-studio | https://github.com/andyhuo520/ppocrv6-studio | 本地工作台、Web UI、CoreML 加速 |

## 安装

```bash
# 创建虚拟环境并安装
python3 -m venv ~/.venvs/ppocrv6
~/.venvs/ppocrv6/bin/pip install onnxruntime opencv-python-headless numpy Pillow pdf2image

# macOS Apple Silicon 用户：替换为标准 onnxruntime
~/.venvs/ppocrv6/bin/pip install onnxruntime-silicon

# 下载模型（从 ppocrv6-studio GitHub Releases）
bash scripts/download_models.sh all
# 或只下载指定档位: tiny / small / medium
```

## CLI 命令

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

## 输出

```
output/
├── input.txt      ← 纯文本（每页分段）
└── input.json     ← 完整结果（含置信度、文本框坐标）
```

## 模型档位对比

| 档位 | 参数量 | 模型大小 | 适用场景 |
|------|--------|---------|---------|
| Tiny | 极轻量 | **1.5 MB** | 快速预览、浏览器端运行、批量处理 |
| Small | 轻量 | **7.7 MB** | 日常使用，性能均衡 |
| Medium | 标准 | **34.5 MB** | 高精度场景（合同/发票/复杂文档） |

## 性能参考

| 平台 | Tiny | Small | Medium |
|------|------|-------|--------|
| Apple M4 (CoreML) | ~3s | ~8s | ~15s |
| Intel CPU (OpenVINO, 5.2x) | ~6s | ~15s | ~30s |
| Intel CPU (标准) | ~8s | ~15s | ~30s |
| 浏览器 (WASM) | ~12s | — | — |

> 官方数据：medium 模型在 A100 GPU 上仅需 0.13 秒。

## 文档类型建议

| 文档类型 | 推荐档位 | 理由 |
|---------|---------|------|
| 平整扫描件 | Tiny 或 Small | 速度优先 |
| 手机拍照件 | Small | 平衡速度与准确率 |
| 复杂文档/小字 | **Medium** | 精度优先 |
| 点阵字体/轮胎压印 | **Medium** | 边缘场景需最高精度 |
| 多语言文档 | Medium | 统一 50 语言模型需要 medium 档位 |
| 批量处理 | Tiny | 优先速度 |

## Web 工作台（新增）

ppocrv6-studio 提供 FastAPI Web 工作台，适合交互式 OCR：

```bash
# 启动 Web 工作台（端口 8765）
python webapp/server.py
```

功能：拖拽上传、批量处理、剪贴板粘贴、历史记录网格、结果导出(CSV/Markdown/Excel)、模型档位切换、CoreML 开关。

## 浏览器 Demo（新增）

Tiny 模型可完全在浏览器内运行，无需服务器：
- `ppocrv6_browser.html` — 通过 ONNX Runtime Web 加载，零依赖

## 迁移说明

> PP-OCRv6 是比 PP-OCRv4 更轻量、效果更好的新一代模型。
> 默认 GPU 加速（DirectML / CoreML），CPU 5-6x 提速。无 GPU 时自动回退 CPU。
> 官方 v3.7.0 (2026-06-11) 发布，旧版 PaddleOCR（PP-OCRv4）管线保留为备选。
> 准确率参考：OmniDocBench 文本块编辑距离 Medium 0.425 / Small 0.443 / Tiny 0.446（越低越好）。
