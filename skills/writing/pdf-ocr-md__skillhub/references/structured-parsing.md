# Structured Parsing

> 来源: pdf-ocr-md v3.3.0 SKILL.md | 从主文件拆分，保持原内容不变

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