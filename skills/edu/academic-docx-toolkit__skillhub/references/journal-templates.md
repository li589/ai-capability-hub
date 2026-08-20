# 期刊与学位论文模板参数 / Journal & Thesis Template Parameters

## 概述

本参考提供主流学术出版格式的页面参数，可直接用于 python-docx 的 Section API 配置。每种模板包含页面尺寸、页边距、字体组合、行距和标题格式的完整参数。

---

## GB/T 标准页面设置

### 参数一览

| 参数 | 值 | 说明 |
|------|-----|------|
| 纸张大小 | A4 (210×297mm) | GB/T 148-1997 |
| 上边距 | 2.54 cm | 标准 1 英寸 |
| 下边距 | 2.54 cm | 标准 1 英寸 |
| 左边距 | 3.17 cm | 标准 1.25 英寸（留装订空间） |
| 右边距 | 3.17 cm | 标准 1.25 英寸 |
| 页眉距边界 | 1.5 cm | — |
| 页脚距边界 | 1.75 cm | — |

### python-docx 代码

```python
from docx import Document
from docx.shared import Cm, Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def setup_gbt_page(doc):
    """
    配置 GB/T 标准页面设置

    适用于中文学术论文、技术报告等。
    """
    for section in doc.sections:
        # 页面尺寸
        section.page_width = Cm(21.0)   # A4 宽度
        section.page_height = Cm(29.7)  # A4 高度

        # 页边距
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.17)
        section.right_margin = Cm(3.17)

        # 页眉页脚距离
        section.header_distance = Cm(1.5)
        section.footer_distance = Cm(1.75)


# ===== 使用示例 =====
doc = Document()
setup_gbt_page(doc)
doc.save('gbt_format.docx')
```

---

## 中文学位论文常见格式

### 参数一览

| 参数 | 值 | 说明 |
|------|-----|------|
| 纸张大小 | A4 (210×297mm) | — |
| 上边距 | 2.54 cm | 各高校略有差异 |
| 下边距 | 2.54 cm | — |
| 左边距 | 3.0 cm | 含装订线 |
| 右边距 | 2.5 cm | — |
| 装订线 | 0 cm（已含在左边距） | — |
| 正文行距 | 1.5 倍行距 / 固定值 20 磅 | 以学校要求为准 |
| 标题行距 | 1.25 倍行距 | — |

### 字体组合

| 元素 | 中文字体 | 英文字体 | 字号 | 字形 |
|------|----------|----------|------|------|
| 论文题目 | 黑体 | Times New Roman | 二号 (22pt) | 加粗 |
| 章标题 | 黑体 | Times New Roman | 三号 (16pt) | 加粗 |
| 节标题 | 黑体 | Times New Roman | 小三 (15pt) | 加粗 |
| 小节标题 | 黑体 | Times New Roman | 四号 (14pt) | 加粗 |
| 正文 | 宋体 | Times New Roman | 小四 (12pt) | 常规 |
| 图表标题 | 宋体 | Times New Roman | 五号 (10.5pt) | 加粗（标题） |
| 表格内容 | 宋体 | Times New Roman | 小五 (9pt) | 常规 |
| 页眉 | 宋体 | Times New Roman | 小五 (9pt) | 常规 |
| 脚注 | 宋体 | Times New Roman | 小五 (9pt) | 常规 |

### python-docx 代码

```python
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def setup_thesis_page(doc):
    """配置中文学位论文页面"""
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.5)


def setup_thesis_style_normal(doc):
    """配置正文字体选项"""
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'        # 西文字体
    font.size = Pt(12)                    # 小四号
    font.color.rgb = RGBColor(0, 0, 0)
    # 中文字体通过 eastAsia 设置
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 段落格式
    pf = style.paragraph_format
    pf.line_spacing = 1.5                 # 1.5倍行距
    pf.first_line_indent = Pt(24)         # 首行缩进2字符（12pt×2）
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)


def setup_thesis_headings(doc):
    """配置学位论文标题样式"""
    styles = doc.styles

    # 章标题 Heading 1: 黑体 三号 加粗 居中
    h1 = styles['Heading 1']
    h1.font.name = 'Times New Roman'
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0, 0, 0)
    h1.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.line_spacing = 1.25
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)

    # 节标题 Heading 2: 黑体 小三 加粗 左对齐
    h2 = styles['Heading 2']
    h2.font.name = 'Times New Roman'
    h2.font.size = Pt(15)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0, 0, 0)
    h2.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h2.paragraph_format.line_spacing = 1.25
    h2.paragraph_format.space_before = Pt(6)
    h2.paragraph_format.space_after = Pt(3)

    # 小节标题 Heading 3: 黑体 四号 加粗
    h3 = styles['Heading 3']
    h3.font.name = 'Times New Roman'
    h3.font.size = Pt(14)
    h3.font.bold = True
    h3.font.color.rgb = RGBColor(0, 0, 0)
    h3.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h3.paragraph_format.line_spacing = 1.25
    h3.paragraph_format.space_before = Pt(3)
    h3.paragraph_format.space_after = Pt(3)


# ===== 使用示例 =====
doc = Document()
setup_thesis_page(doc)
setup_thesis_style_normal(doc)
setup_thesis_headings(doc)

# 写入内容
doc.add_paragraph('Lorem ipsum dolor sit amet, consectetur adipiscing elit.')

doc.save('thesis_format.docx')
```

---

## IEEE 双栏模板参数

### 参数一览

| 参数 | 值 | 说明 |
|------|-----|------|
| 纸张大小 | US Letter (8.5×11 inch) | IEEE 标准纸张 |
| 上边距 | 0.75 inch (1.905 cm) | — |
| 下边距 | 1.0 inch (2.54 cm) | — |
| 左边距 | 0.63 inch (1.6 cm) | — |
| 右边距 | 0.63 inch (1.6 cm) | — |
| 栏数 | 2 | — |
| 栏间距 | 0.25 inch (0.635 cm) | — |
| 正文字体 | Times New Roman 10pt | — |
| 标题字体 | Times New Roman 24pt 加粗 | 论文标题 |
| 作者行 | Times New Roman 11pt | — |
| 摘要字体 | Times New Roman 9pt 加粗 | — |
| 节标题 | Times New Roman 10pt 小型大写 | — |
| 行距 | 单倍行距 | — |

### python-docx 代码

```python
from docx import Document
from docx.shared import Inches, Cm, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def setup_ieee_page(doc):
    """
    配置 IEEE 双栏页面

    ⚠ 注意：python-docx 对双栏的支持有限。
    对于复杂的双栏排版，建议使用 LaTeX。
    以下代码设置了基本的分栏结构。
    """
    for section in doc.sections:
        # US Letter 纸张
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

        # 页边距
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(0.63)
        section.right_margin = Inches(0.63)

    # 设置双栏（需要操作 XML 层）
    sectPr = doc.sections[0]._sectPr
    cols = OxmlElement('w:cols')
    cols.set(qn('w:num'), '2')                      # 双栏
    cols.set(qn('w:space'), '360')                   # 栏间距（twips），360≈0.25inch
    cols.set(qn('w:equalWidth'), '1')                # 等宽栏
    sectPr.append(cols)


def setup_ieee_styles(doc):
    """配置 IEEE 样式"""
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(10)
    style.paragraph_format.line_spacing = 1.0
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after = Pt(0)
    # 首段悬挂缩进
    style.paragraph_format.first_line_indent = Inches(0.25)


# ===== 使用示例 =====
doc = Document()
setup_ieee_page(doc)
setup_ieee_styles(doc)

doc.save('ieee_format.docx')
```

### IEEE 样式速查

```
论文标题: 24pt Bold, 居中
作者信息: 11pt, 居中
摘要标题: 9pt Bold, 居中
摘要正文: 9pt Regular
关键词: 9pt Regular
一级标题: 10pt 小型大写字母, 居中, 罗马编号 (I. II. III.)
二级标题: 10pt 斜体, 大写字母编号 (A. B. C.)
正文: 10pt, 首行缩进, 双栏
参考文献: 8pt
表格标题: 8pt 大写, 表格上方居中
图片标题: 8pt, 图片下方居中
```

---

## Elsevier 期刊模板参数

### 参数一览

| 参数 | 值 | 说明 |
|------|-----|------|
| 纸张大小 | A4 (210×297mm) | 或 US Letter |
| 上边距 | 2.0 cm | — |
| 下边距 | 2.0 cm | — |
| 左边距 | 2.0 cm | — |
| 右边距 | 2.0 cm | — |
| 栏数 | 单栏（部分期刊双栏） | 以具体期刊指南为准 |
| 正文字体 | Times New Roman 12pt（或 Georgia 12pt） | — |
| 行距 | 双倍行距（投稿阶段） | 出版后单倍 |
| 标题 | Times New Roman 18pt 加粗 | — |
| 节标题 | Times New Roman 14pt 加粗 | 编号格式: "1. Introduction" |
| 小节标题 | Times New Roman 12pt 加粗 | "1.1. Background" |

### python-docx 代码

```python
def setup_elsevier_page(doc):
    """
    配置 Elsevier 期刊投稿页面

    注意：各 Elsevier 期刊的具体要求可能不同，
    请以目标期刊的 Guide for Authors 为准。
    """
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)


def setup_elsevier_styles(doc):
    """配置 Elsevier 样式"""
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.line_spacing = 2.0   # 投稿阶段双倍行距
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after = Pt(6)

    # 节标题
    h1 = doc.styles['Heading 1']
    h1.font.name = 'Times New Roman'
    h1.font.size = Pt(14)
    h1.font.bold = True
    h1.paragraph_format.line_spacing = 2.0
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)

    # 小节标题
    h2 = doc.styles['Heading 2']
    h2.font.name = 'Times New Roman'
    h2.font.size = Pt(12)
    h2.font.bold = True
    h2.paragraph_format.line_spacing = 2.0
    h2.paragraph_format.space_before = Pt(6)
    h2.paragraph_format.space_after = Pt(3)


# ===== 使用示例 =====
doc = Document()
setup_elsevier_page(doc)
setup_elsevier_styles(doc)
doc.save('elsevier_format.docx')
```

---

## 模板参数对比速查表

| 参数 | GB/T 标准 | 中文学位论文 | IEEE | Elsevier |
|------|-----------|-------------|------|----------|
| 纸张 | A4 | A4 | US Letter | A4 |
| 上边距 | 2.54cm | 2.54cm | 0.75in | 2.0cm |
| 下边距 | 2.54cm | 2.54cm | 1.0in | 2.0cm |
| 左边距 | 3.17cm | 3.0cm | 0.63in | 2.0cm |
| 右边距 | 3.17cm | 2.5cm | 0.63in | 2.0cm |
| 正文字号 | — | 小四(12pt) | 10pt | 12pt |
| 正文行距 | — | 1.5倍 | 单倍 | 双倍(投稿) |
| 标题字号 | — | 二号(22pt) | 24pt | 18pt |
| 节标题号 | — | 三号(16pt) | 10pt SC | 14pt |
| 西文字体 | — | Times New Roman | Times New Roman | Times New Roman |
| 中文字体 | — | 宋体 | — | — |
| 栏数 | 1 | 1 | 2 | 1(或2) |

---

## 通用字体设置函数

```python
def set_font_for_element(run_or_style, western='Times New Roman', eastern='宋体',
                          size_pt=12, bold=False, italic=False):
    """
    统一设置西文和中文字体

    python-docx 的 font.name 只设置西文字体。
    中文字体需要通过 XML 层的 eastAsia 属性设置。

    Args:
        run_or_style: Run 对象或 Style 对象
        western: 西文字体名
        eastern: 中文字体名
        size_pt: 字号（磅）
        bold: 是否加粗
        italic: 是否斜体
    """
    font = run_or_style.font
    font.name = western
    font.size = Pt(size_pt)
    font.bold = bold
    font.italic = italic

    # 设置中文字体
    # Style 对象的字体属性在 style.element.rPr.rFonts
    # Run 对象的字体属性在 run._element.rPr.rFonts
    try:
        rPr = run_or_style._element.rPr
    except AttributeError:
        rPr = run_or_style.element.rPr

    if rPr is not None:
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.insert(0, rFonts)
        rFonts.set(qn('w:eastAsia'), eastern)


# ===== 使用示例 =====
doc = Document()
run = doc.add_paragraph().add_run('Lorem ipsum 中英文混排测试')
set_font_for_element(run, western='Times New Roman', eastern='宋体', size_pt=12)
doc.save('font_test.docx')
```

---

## 注意事项

1. **以期刊最新指南为准**：出版社会定期更新投稿指南，本参考提供的是典型参数，投稿前请核对目标期刊的官方 Guide for Authors。
2. **字体回退机制**：如果系统未安装指定字体（如黑体），Word 会使用默认字体替代。建议在目标环境中确认字体可用性。
3. **双栏限制**：python-docx 对双栏排版的支持有限，复杂排版建议使用 LaTeX + pandoc 转换。
4. **页边距单位**：python-docx 支持 `Cm()`、`Inches()`、`Mm()` 等多种长度单位，选用与期刊一致的单位可减少换算误差。
