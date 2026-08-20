# 学术表格配色与样式 / Academic Table Styling

## 概述

学术论文中的表格需要兼顾**可读性**、**专业性**和**打印安全性**。本参考提供三套经过验证的学术表格配色方案，均包含完整的 python-docx 代码，可直接复制使用。

---

## 方案一：深蓝方案 (Dark Blue)

### 配色参数

- **表头背景：** `#2C5AA0`（深蓝）
- **表头文字：** 白色（`#FFFFFF`），加粗
- **偶数行背景：** `#D6E4F4`（浅蓝）
- **奇数行背景：** 白色
- **边框：** 深灰色 `#404040`，0.5pt

### 效果说明

深蓝表头搭配浅蓝斑马纹，视觉层次分明，适合彩色打印或电子阅读场景（如PDF分发）。不建议用于纯黑白打印，因为浅蓝背景在灰阶下可能不够清晰。

### 适用场景

- 电子版论文/报告
- 彩色打印的学位论文
- PPT 中嵌入的表格
- 在线期刊

### 完整代码

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_cell_shading(cell, hex_color):
    """设置单元格背景色"""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), hex_color)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_border(cell, **kwargs):
    """设置单元格边框
    kwargs: top, bottom, left, right, insideH, insideV
    每个值为 dict: {'sz': '4', 'val': 'single', 'color': '404040'}
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge, attrs in kwargs.items():
        element = OxmlElement(f'w:{edge}')
        for key, val in attrs.items():
            element.set(qn(f'w:{key}'), str(val))
        tcBorders.append(element)
    tcPr.append(tcBorders)


def create_dark_blue_table(doc, headers, data):
    """
    创建深蓝方案学术表格

    Args:
        doc: Document 对象
        headers: 表头列表，如 ['编号', '参数名称', '取值', '单位']
        data: 数据行列表，每行为 list

    Returns:
        Table 对象
    """
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- 设置列宽（示例：均分页面宽度）---
    col_width = Cm(14.66 / len(headers))  # A4可用宽度约14.66cm
    for col in table.columns:
        col.width = col_width

    # --- 表头样式 ---
    HEADER_BG = '2C5AA0'
    HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)

    for j, header_text in enumerate(headers):
        cell = table.rows[0].cells[j]
        # 背景色
        set_cell_shading(cell, HEADER_BG)
        # 文字
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(9)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        run.font.color.rgb = HEADER_FG

    # --- 数据行样式 ---
    EVEN_BG = 'D6E4F4'

    for i, row_data in enumerate(data):
        row = table.rows[i + 1]
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            # 偶数行背景
            if i % 2 == 1:
                set_cell_shading(cell, EVEN_BG)
            # 文字
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(cell_text))
            run.font.size = Pt(9)
            run.font.name = '宋体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return table


# ===== 使用示例 =====
doc = Document()

# 添加表标题
caption = doc.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = caption.add_run('表1：某对比实验数据统计')
run.bold = True
run.font.size = Pt(10)
run.font.name = '宋体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

# 创建表格
headers = ['组别', '样本量', '均值', '标准差', 'P值']
data = [
    ['对照组', '30', '2.47', '0.38', '0.042'],
    ['实验组A', '30', '2.89', '0.41', '—'],
    ['实验组B', '30', '3.12', '0.35', '—'],
    ['实验组C', '30', '3.45', '0.44', '—'],
]
create_dark_blue_table(doc, headers, data)

doc.save('output_dark_blue.docx')
```

---

## 方案二：深灰方案 (Dark Gray)

### 配色参数

- **表头背景：** `#333333`（深灰）
- **表头文字：** 白色，加粗
- **偶数行背景：** `#F5F5F5`（浅灰）
- **奇数行背景：** 白色
- **边框：** 黑色 `#000000`，0.5pt

### 效果说明

灰阶配色在任何打印模式下（彩色/黑白/灰度）都能保持良好可读性。表头与数据行对比度充足，浅灰斑马纹在黑白打印中退化为极淡底纹，不影响阅读。

### 适用场景

- 需要黑白打印的学位论文（首选方案）
- 图书馆存档论文
- 审稿阶段盲审稿
- 不确定最终输出模式的场景

### 完整代码

```python
def create_dark_gray_table(doc, headers, data):
    """
    创建深灰方案学术表格（灰阶打印安全）

    Args:
        doc: Document 对象
        headers: 表头列表
        data: 数据行列表

    Returns:
        Table 对象
    """
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- 设置列宽 ---
    col_width = Cm(14.66 / len(headers))
    for col in table.columns:
        col.width = col_width

    # --- 表头样式 ---
    HEADER_BG = '333333'
    HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)

    for j, header_text in enumerate(headers):
        cell = table.rows[0].cells[j]
        set_cell_shading(cell, HEADER_BG)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(9)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        run.font.color.rgb = HEADER_FG

    # --- 数据行样式 ---
    EVEN_BG = 'F5F5F5'

    for i, row_data in enumerate(data):
        row = table.rows[i + 1]
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            if i % 2 == 1:
                set_cell_shading(cell, EVEN_BG)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(cell_text))
            run.font.size = Pt(9)
            run.font.name = '宋体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return table


# ===== 使用示例 =====
doc = Document()

caption = doc.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = caption.add_run('表2：某性能指标对比')
run.bold = True
run.font.size = Pt(10)
run.font.name = '宋体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

headers = ['指标', '方法A', '方法B', '方法C', '方法D']
data = [
    ['准确率(%)', '92.3', '94.1', '89.7', '96.2'],
    ['召回率(%)', '88.5', '91.2', '85.4', '93.8'],
    ['F1值', '0.903', '0.926', '0.875', '0.949'],
    ['耗时(ms)', '45.2', '38.7', '52.1', '41.3'],
]
create_dark_gray_table(doc, headers, data)

doc.save('output_dark_gray.docx')
```

---

## 方案三：简约方案 (Minimalist)

### 配色参数

- **表头背景：** `#000000`（纯黑）
- **表头文字：** 白色，加粗
- **所有数据行背景：** 白色（无斑马纹）
- **边框：** 仅使用细线（0.5pt）分割

### 效果说明

极简风格，仅通过表头与数据的强烈对比区分层级，无斑马纹。边框细且统一，视觉干扰最小化。

### 适用场景

- 顶级期刊投稿（Nature/Science 风格）
- 表格数据密度高、行数多的场景
- 希望读者专注数据本身的场景

### 完整代码

```python
def create_minimal_table(doc, headers, data):
    """
    创建简约方案学术表格（纯黑表头 + 全白行 + 细线边框）

    Args:
        doc: Document 对象
        headers: 表头列表
        data: 数据行列表

    Returns:
        Table 对象
    """
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- 设置列宽 ---
    col_width = Cm(14.66 / len(headers))
    for col in table.columns:
        col.width = col_width

    # --- 表头样式 ---
    HEADER_BG = '000000'
    HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)

    for j, header_text in enumerate(headers):
        cell = table.rows[0].cells[j]
        set_cell_shading(cell, HEADER_BG)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(9)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        run.font.color.rgb = HEADER_FG

    # --- 数据行：全白，仅调整字体 ---
    for row_data in data:
        row = table.add_row()
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(cell_text))
            run.font.size = Pt(9)
            run.font.name = '宋体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return table


# ===== 使用示例 =====
doc = Document()

caption = doc.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = caption.add_run('表3：某实验条件参数')
run.bold = True
run.font.size = Pt(10)
run.font.name = '宋体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

headers = ['参数', '条件1', '条件2', '条件3']
data = [
    ['温度(°C)', '25', '37', '45'],
    ['pH值', '7.0', '7.4', '6.8'],
    ['浓度(mM)', '10', '20', '50'],
]
create_minimal_table(doc, headers, data)

doc.save('output_minimal.docx')
```

---

## 通用表格设置

### 字体大小惯例

学术论文表格惯例使用 **9pt 宋体**（中文）或 **9pt Times New Roman**（数字/英文），比正文（通常 12pt 或 10.5pt）略小，以便容纳更多信息。

### 单元格边距设置

```python
def set_cell_margins(cell, top=36, bottom=36, left=72, right=72):
    """
    设置单元格内边距（单位：1/20 pt，即 twips）

    默认值：上下 36 twips (≈1.27mm)，左右 72 twips (≈2.54mm)

    Args:
        cell: 单元格对象
        top, bottom, left, right: 边距值（twips）
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')

    for side, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{side}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)

    tcPr.append(tcMar)
```

### 表格标题格式

学术论文中表标题的规范格式为 **"表X：标题内容"**（居中、加粗、10pt），置于表格上方：

```python
def add_table_caption(doc, table_num, caption_text):
    """
    添加表标题

    Args:
        doc: Document 对象
        table_num: 表序号（整数）
        caption_text: 标题文字

    Returns:
        Paragraph 对象（标题段落）
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)

    run = p.add_run(f'表{table_num}：{caption_text}')
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return p
```

### 三线表样式（学术论文常用）

对于数据量不大的简单表格，三线表是最经典的选择：

```python
def create_three_line_table(doc, headers, data):
    """
    创建三线表（顶线、栏目线、底线）

    三线表是学术论文中最经典的简洁表格样式，
    仅保留三条横线，去除所有竖线。
    """
    table = doc.add_table(rows=1 + len(data), cols=len(headers))

    # 移除所有边框，然后手动添加三条线
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')

    # 设置表格边框
    tblBorders = OxmlElement('w:tblBorders')

    # 顶线：1.5pt 粗线
    top = OxmlElement('w:top')
    top.set(qn('w:val'), 'single')
    top.set(qn('w:sz'), '12')  # 1.5pt = 12 eighths
    top.set(qn('w:space'), '0')
    top.set(qn('w:color'), '000000')
    tblBorders.append(top)

    # 底线：1.5pt 粗线
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:space'), '0')
    bottom.set(qn('w:color'), '000000')
    tblBorders.append(bottom)

    # 水平内线（栏目线）：0.75pt
    insideH = OxmlElement('w:insideH')
    insideH.set(qn('w:val'), 'single')
    insideH.set(qn('w:sz'), '6')  # 0.75pt
    insideH.set(qn('w:space'), '0')
    insideH.set(qn('w:color'), '000000')
    tblBorders.append(insideH)

    # 移除左右边框和竖线
    for edge in ['left', 'right', 'insideV']:
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'none')
        el.set(qn('w:sz'), '0')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), 'auto')
        tblBorders.append(el)

    tblPr.append(tblBorders)

    # 填充表头
    for j, header_text in enumerate(headers):
        cell = table.rows[0].cells[j]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(9)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 填充数据
    for i, row_data in enumerate(data):
        row = table.rows[i + 1]
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(cell_text))
            run.font.size = Pt(9)
            run.font.name = '宋体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return table
```

---

## 方案对比速查表

| 方案 | 表头色 | 偶数行色 | 最佳场景 |
|------|--------|----------|----------|
| 深蓝方案 | `#2C5AA0` | `#D6E4F4` | 电子阅读、彩色打印 |
| 深灰方案 | `#333333` | `#F5F5F5` | 黑白打印、盲审稿 |
| 简约方案 | `#000000` | 白色 | 高密度数据、顶级期刊 |
| 三线表 | 无底色 | 无底色 | 简单数据、经典学术风格 |
