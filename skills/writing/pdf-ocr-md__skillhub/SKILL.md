---
name: pdf-ocr-md
version: 3.4.0
description: 当用户需要从 PDF、图片、扫描件中提取文字内容时使用。适合处理合同、发票、报告等文档，尤其是中文扫描件、手机拍照的弯曲页面、歪斜的文档。支持 PP-OCRv6 三档模型 (Tiny/Small/Medium)。
related_skills:
  - ocr-and-documents
---

# pdf-ocr-md — PDF → OCR → 结构化 Markdown [v3.4.0]

> v3.4.0：SKILL.md 精简至 ~120 行（原 578 行），详细教程移至 references/，按需加载。对标 OpenAI 上下文压缩策略。

## 环境

| 工具 | 用途 | 虚拟环境 |
|------|------|---------|
| `lit` | 文本层 PDF 快速解析（Rust，~0.9ms/页） | `~/.venvs/liteparse/` |
| `ocr6` | PP-OCRv6 三档 OCR | `~/.venvs/ppocrv6/` |
| `pdf2md` | PaddleOCR 中文扫描件（旧版 v4） | `~/.venvs/paddleocr/` |
| `prep` | 文档预处理（倾斜/方向/展平） | (同 ocr6) |

## 快速选择（必读）

```bash
# ① 先试 LiteParse（文本层 PDF 秒出）
lit parse input.pdf --no-ocr -o output.txt

# ② 空结果 = 扫描件，按需选模型档位
#    tiny(1.5MB 极速) | small(7.7MB 均衡) | medium(34.5MB 高精度)
python scripts/pdf_ocr_v6.py input.pdf --tier small -o ./output

# ③ 低质量文档先预处理（deskew倾斜/orient方向/unwarp展平/--all全部）
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all
python scripts/pdf_ocr_v6.py ./preprocessed/input_p001.jpg --tier medium -o ./output
```

## 工作流

```
输入文档
  ├── 有文本层 → lit parse --no-ocr（0.9ms/页）
  └── 扫描件 → 先预处理(倾斜/方向/展平) → ocr6(tiny|small|medium)
```

## 性能速查

| 类型 | 引擎 | 单页 | 17 页合同 |
|------|------|------|----------|
| 文本层 PDF | LiteParse | ~0.9ms | ~15ms |
| 扫描件(极速) | PP-OCRv6 Tiny | ~3-8s | ~1-2min |
| 扫描件(均衡) | PP-OCRv6 Small | ~8-15s | ~2-4min |
| 扫描件(高精度) | PP-OCRv6 Medium | ~15-30s | ~4-8min |
| 中文旧版 | PaddleOCR v4 | ~15s | ~4.5min |

> 准确率：PP-OCRv6 ~97%+，预处理后 ~98%+。公章/签名场景必须用 PaddleOCR（Tesseract 会乱码）。

## 按需加载的参考文档

所有详细教程已移至 references/，需要时读取：

| 场景 | 参考文件 |
|------|---------|
| LiteParse 完整用法（Rust CLI/截图/批量） | `references/liteparse-usage.md` |
| PaddleOCR 旧版（v4，Python 3.13 兼容修复） | `references/paddleocr.md` + `references/paddleocr-py313-compat.md` |
| 文档预处理详解（倾斜/方向/展平/效果预测） | `references/pdf-preprocessing.md` |
| 结构化解析（版面分析+表格提取+JSON） | `references/structured-parsing.md` |
| PP-OCRv6 完整指南（模型选择/GPU加速/迁移） | `references/ppocrv6-guide.md` |
| 完整原版 SKILL.md（v3.3.0 全部内容） | `references/full-guide.md` |
| OpenDataLoader（纯 Java，已不推荐） | `references/opendataloader.md` |

## 注意事项

- 首次运行自动下载模型（~17MB，从 hf-mirror/modelscope 国内镜像）
- 机器 3.6GB 内存，PaddleOCR 冷启动 ~300MB 峰值可承受
- 预处理对平整扫描件效果不明显，对手机拍照/弯曲文档提升 1~5%
