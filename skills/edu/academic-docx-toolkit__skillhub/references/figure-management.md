# 图片管理与编号 / Figure Management & Numbering

## 概述

在学术论文中管理图片（插入、替换、删除、编号）需要特别小心，因为 python-docx 使用段落索引来定位元素，而插入/删除图片会导致索引漂移。本参考提供一套完整的解决方案。

---

## 学术图片规范

在开始操作之前，先明确学术论文图片的基本规范：

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 图片宽度 | 11 cm（单栏）或 16 cm（双栏） | 基于A4纸可打印区域 |
| 分辨率 | ≥300 dpi | 打印质量保证 |
| 格式 | PNG（推荐）或 TIFF | PNG无压缩损失，兼容性好 |
| 对齐 | 居中 | 学术惯例 |
| 图片位置 | 紧接图题之后 | 图题在上或在下取决于期刊要求 |

---

## 基本图片插入

### 标准插入代码

```python
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def insert_figure(doc, image_path, caption_text, figure_num, width_cm=11.0):
    """
    插入学术图片及图题

    Args:
        doc: Document 对象
        image_path: 图片文件路径（建议PNG，300dpi）
        caption_text: 图题文字（不含编号）
        figure_num: 图片编号（整数）
        width_cm: 图片宽度（厘米），默认11cm

    Returns:
        包含图片的 Paragraph 对象
    """
    # --- 图片段落：居中 ---
    img_paragraph = doc.add_paragraph()
    img_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = img_paragraph.add_run()
    run.add_picture(image_path, width=Cm(width_cm))

    # --- 图题段落：居中、加粗 ---
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_before = Pt(3)
    caption_paragraph.paragraph_format.space_after = Pt(6)

    run = caption_paragraph.add_run(f'图{figure_num}：{caption_text}')
    run.bold = True
    run.font.size = Pt(9)
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return img_paragraph
```

### 含图片描述的三段体结构

部分期刊要求图题之后附带图片说明（如数据来源、缩写释义等），形成三段体：

```
图题（Figure 1. ...）
图片
图注（Note: ... / Source: ...）
```

```python
def insert_figure_with_note(doc, image_path, caption_text, note_text, figure_num, width_cm=11.0):
    """
    插入图片 + 图题 + 图注（三段体）

    Args:
        doc: Document 对象
        image_path: 图片路径
        caption_text: 图题文字
        note_text: 图注文字（如 "注：数据来源于..."）
        figure_num: 图片编号
        width_cm: 图片宽度
    """
    # 图题
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = caption_paragraph.add_run(f'图{figure_num}：{caption_text}')
    run.bold = True
    run.font.size = Pt(9)
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 图片
    img_paragraph = doc.add_paragraph()
    img_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = img_paragraph.add_run()
    run.add_picture(image_path, width=Cm(width_cm))

    # 图注
    note_paragraph = doc.add_paragraph()
    note_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = note_paragraph.add_run(note_text)
    run.font.size = Pt(8)
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    return img_paragraph
```

---

## 逆向插入防索引漂移

### 问题描述

在已有文档中按正序插入图片（图1 → 图2 → ... → 图N）时，每次插入都会改变后续段落的索引。如果需要在特定位置插入多张图片，后插入的图片位置会因先插入的图片而偏移。

**核心原理：** python-docx 的段落索引是动态的——每次 `add_paragraph()` 或 `add_picture()` 都会改变所有后续段落的索引。

### 解决方案：从末尾向前操作

**逆向插入**策略：先插入编号最大的图片（如先图8，再图7，...，最后图1），这样每次操作都不会影响已完成操作的段落。

```
插入顺序：图8 → 图7 → 图6 → 图5 → 图4 → 图3 → 图2 → 图1
                          ↑
                    从后往前插入，不影响已完成的位置
```

### 代码实现

```python
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from lxml import etree


def insert_figures_reverse(doc, figure_markers, image_dir):
    """
    逆向插入多张图片，防止索引漂移

    原理：从最后一个标记位置开始，逆序插入图片。
    每次插入只影响插入位置之后的段落索引，
    之前的段落不受影响——而我们的下一个目标
    "正好在"已完成区域之前。

    Args:
        doc: Document 对象
        figure_markers: 图片标记列表，按正序排列
            每项为 dict: {
                'marker': '[[FIG:1]]',      # 文档中的占位标记
                'image': 'fig1_results.png', # 图片文件名
                'caption': '实验一结果对比',  # 图题
                'num': 1                     # 图号
            }
        image_dir: 图片文件目录
    """
    import os

    # 逆序处理：从最后一幅图开始
    for fig_info in reversed(figure_markers):
        marker = fig_info['marker']
        image_path = os.path.join(image_dir, fig_info['image'])
        caption = fig_info['caption']
        num = fig_info['num']

        # 查找标记段落
        marker_paragraph = None
        marker_index = None
        for i, para in enumerate(doc.paragraphs):
            if marker in para.text:
                marker_paragraph = para
                marker_index = i
                break

        if marker_paragraph is None:
            print(f"未找到标记: {marker}")
            continue

        # 获取标记段落的 XML body 父节点
        body = doc.element.body
        marker_element = marker_paragraph._element

        # 创建图片段落XML
        img_p = etree.SubElement(body, qn('w:p'))
        img_pPr = etree.SubElement(img_p, qn('w:pPr'))
        img_jc = etree.SubElement(img_pPr, qn('w:jc'))
        img_jc.set(qn('w:val'), 'center')

        img_r = etree.SubElement(img_p, qn('w:r'))
        img_drawing = etree.SubElement(img_r, qn('w:drawing'))
        # 此处需要完整的 drawing XML，推荐使用 python-docx 标准方式
        # 简化示例：在实际使用中请用 doc.add_paragraph().add_run().add_picture()

        # 插入到标记段落之后
        marker_element.addnext(img_p)

        # 创建图题段落
        caption_p = etree.SubElement(body, qn('w:p'))
        caption_pPr = etree.SubElement(caption_p, qn('w:pPr'))
        caption_jc = etree.SubElement(caption_pPr, qn('w:jc'))
        caption_jc.set(qn('w:val'), 'center')

        caption_r = etree.SubElement(caption_p, qn('w:r'))
        caption_rPr = etree.SubElement(caption_r, qn('w:rPr'))
        caption_b = etree.SubElement(caption_rPr, qn('w:b'))
        caption_sz = etree.SubElement(caption_rPr, qn('w:sz'))
        caption_sz.set(qn('w:val'), '18')  # 9pt = 18 half-points
        caption_t = etree.SubElement(caption_r, qn('w:t'))
        caption_t.text = f'图{num}：{caption}'

        img_p.addnext(caption_p)

        # 删除原始标记段落
        body.remove(marker_element)

    print(f"完成：从后往前共插入 {len(figure_markers)} 幅图片")


# ===== 使用示例 =====
doc = Document('manuscript_with_markers.docx')

figure_markers = [
    {'marker': '[[FIG:1]]', 'image': 'architecture.png', 'caption': '系统总体架构示意图', 'num': 1},
    {'marker': '[[FIG:2]]', 'image': 'workflow.png', 'caption': '业务流程处理时序图', 'num': 2},
    {'marker': '[[FIG:3]]', 'image': 'experiment_setup.png', 'caption': '实验环境部署拓扑', 'num': 3},
    {'marker': '[[FIG:4]]', 'image': 'results_comparison.png', 'caption': '性能对比实验结果', 'num': 4},
    {'marker': '[[FIG:5]]', 'image': 'analysis_chart.png', 'caption': '数据分析统计图表', 'num': 5},
    # ... 更多图片
]

insert_figures_reverse(doc, figure_markers, 'figures/')
doc.save('manuscript_with_figures.docx')
```

### 原理图解

```
文档初始状态:
    P0  P1  P2  [P3:FIG1]  P4  P5  [P6:FIG2]  P7  [P8:FIG8]  P9

步骤1: 先处理 FIG8（最末尾）
    在 P8 位置插入图片 → 不影响 P0~P8 的索引
    文档变为: ... P5  [P6:FIG2]  P7  图8+题  P9

步骤2: 处理 FIG2
    在 P6 位置插入 → 不影响 P0~P6（因为之后修改在末尾）
    文档变为: ... P4  P5  图2+题  P7  图8+题  P9

步骤3: 处理 FIG1
    在 P3 位置插入 → 不影响 P4 之后（P4/P5 索引仍未变）
    文档变为: P0  P1  P2  图1+题  P4  P5  图2+题  P7  图8+题  P9

✓ 所有图片按正确编号插入，无索引漂移
```

---

## 图片替换（XML层操作）

### 定位与替换机制

图片在 DOCX 中通过 `w:drawing` 元素存储。替换图片的最可靠方式是直接操作 XML 层。

```python
from lxml import etree
from docx.oxml.ns import qn


def find_all_drawings(doc):
    """
    查找文档中所有 w:drawing 元素

    Returns:
        list of (paragraph_index, drawing_element)
    """
    results = []
    for i, para in enumerate(doc.paragraphs):
        drawings = para._element.findall('.//' + qn('w:drawing'))
        for drawing in drawings:
            results.append((i, drawing))
    return results


def replace_image_in_drawing(drawing_element, new_image_path, doc):
    """
    替换 w:drawing 中的图片

    实现原理：
    1. 遍历 w:drawing 下的 inline/anchor 元素
    2. 找到 blipFill → blip → embed 属性（图片关系ID）
    3. 更新关系对应的图片数据

    注意：完整替换需要同时更新 blip 的 r:embed 关系和
    媒体文件的实际内容。以下为简化示意，生产环境建议使用
    python-docx 的官方 API 或直接操作 ZIP 包内的文件。

    Args:
        drawing_element: w:drawing XML 元素
        new_image_path: 新图片路径
        doc: Document 对象
    """
    # 查找 blip 元素（图片引用）
    nsmap = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    }

    blip = drawing_element.find('.//a:blip', nsmap)
    if blip is None:
        print("未找到 blip 元素，无法替换")
        return False

    # 获取原始关系ID
    old_rId = blip.get(qn('r:embed'))
    if old_rId is None:
        print("blip 无 r:embed 属性")
        return False

    # 通过关系ID获取原始图片part
    try:
        old_part = doc.part.related_parts[old_rId]

        # 读取新图片
        with open(new_image_path, 'rb') as f:
            new_image_data = f.read()

        # 替换图片数据（使用相同的 part）
        # 注意：python-docx 的 ImagePart 不支持直接替换 blob
        # 此处需要更新内部 _blob 属性
        old_part._blob = new_image_data

        print(f"成功替换图片: {new_image_path}")
        return True

    except KeyError:
        print(f"未找到关系ID对应的图片part: {old_rId}")
        return False


def replace_figure_by_index(doc, paragraph_index, new_image_path):
    """
    根据段落索引替换图片

    Args:
        doc: Document 对象
        paragraph_index: 包含图片的段落索引
        new_image_path: 新图片路径

    Returns:
        bool: 是否成功替换
    """
    para = doc.paragraphs[paragraph_index]
    drawings = para._element.findall('.//' + qn('w:drawing'))

    if not drawings:
        print(f"段落 {paragraph_index} 中未找到图片")
        return False

    for drawing in drawings:
        replace_image_in_drawing(drawing, new_image_path, doc)

    return True
```

---

## 图片删除

### 递归查找父节点清除法

图片通过 `w:drawing` 元素嵌入段落。删除图片需要向上递归查找，找到合适的父节点后移除整个 `w:drawing` 子树。

```python
from lxml import etree
from docx.oxml.ns import qn


def delete_all_drawings_in_paragraph(paragraph):
    """
    删除段落中的所有图片（w:drawing元素）

    原理：
    1. 查找段落中所有 w:drawing 元素
    2. 从后往前移除，避免前向索引问题
    3. 若图片在 w:r 中，移除整个 run；
       若图片是段落直接子元素，直接移除 drawing

    Args:
        paragraph: Paragraph 对象

    Returns:
        int: 删除的图片数量
    """
    nsmap = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    }

    p_element = paragraph._element

    # 查找所有 w:drawing（可能在 w:r 内或直接在 w:p 下）
    drawings = p_element.findall('.//w:drawing', nsmap)
    count = len(drawings)

    # 从后往前移除
    for drawing in reversed(drawings):
        # 获取父元素
        parent = drawing.getparent()

        if parent is not None:
            # 如果父元素是 w:r（run），移除整个 run
            if parent.tag == qn('w:r'):
                grandparent = parent.getparent()
                if grandparent is not None:
                    grandparent.remove(parent)
            else:
                # 否则直接移除 drawing 元素
                parent.remove(drawing)

    return count


def delete_all_images_in_doc(doc):
    """
    删除文档中的所有图片

    Args:
        doc: Document 对象

    Returns:
        int: 删除的图片总数
    """
    total = 0
    for para in doc.paragraphs:
        total += delete_all_drawings_in_paragraph(para)
    print(f"共删除 {total} 张图片")
    return total
```

---

## 图片编号自动重排

### 问题描述

在插入或删除图片后，需要重新编排图题编号（"图1"、"图2"...）。手动逐个修改容易出错，建议使用正则表达式自动重排。

### 实现代码

```python
import re


def renumber_figures(doc):
    """
    自动重排所有图片编号

    遍历所有段落，找到形如"图X："或"Figure X:"的图题，
    按出现顺序重新编号。

    Args:
        doc: Document 对象

    Returns:
        int: 重排的图题数量
    """
    # 中文图题模式："图1：", "图 2：", "图1-3："等
    pattern_cn = re.compile(r'图\s*(\d+(?:[-–]\d+)?)\s*[：:]')
    # 英文图题模式："Figure 1:", "Fig. 2:"等
    pattern_en = re.compile(r'(?:Figure|Fig\.)\s*(\d+(?:[-–]\d+)?)\s*[:.]')

    count = 0
    figure_index = 0

    for para in doc.paragraphs:
        text = para.text.strip()

        # 匹配中文图题
        match_cn = pattern_cn.match(text)
        if match_cn:
            figure_index += 1
            old_num = match_cn.group(1)
            new_text = pattern_cn.sub(f'图{figure_index}：', text, count=1)

            # 更新段落文字
            for run in para.runs:
                if old_num in run.text:
                    run.text = run.text.replace(old_num, str(figure_index), 1)
                    count += 1
                    break
            continue

        # 匹配英文图题
        match_en = pattern_en.match(text)
        if match_en:
            figure_index += 1
            old_num = match_en.group(1)
            new_text = pattern_en.sub(f'Figure {figure_index}:', text, count=1)

            for run in para.runs:
                if old_num in run.text:
                    run.text = run.text.replace(old_num, str(figure_index), 1)
                    count += 1
                    break

    print(f"共重排 {count} 个图题，最终编号到 {figure_index}")
    return count


def renumber_tables(doc):
    """
    自动重排所有表格编号（"表X："模式）

    Args:
        doc: Document 对象

    Returns:
        int: 重排的表题数量
    """
    pattern_cn = re.compile(r'表\s*(\d+(?:[-–]\d+)?)\s*[：:]')
    pattern_en = re.compile(r'Table\s*(\d+(?:[-–]\d+)?)\s*[:.]')

    count = 0
    table_index = 0

    for para in doc.paragraphs:
        text = para.text.strip()

        match_cn = pattern_cn.match(text)
        if match_cn:
            table_index += 1
            old_num = match_cn.group(1)
            for run in para.runs:
                if old_num in run.text:
                    run.text = run.text.replace(old_num, str(table_index), 1)
                    count += 1
                    break
            continue

        match_en = pattern_en.match(text)
        if match_en:
            table_index += 1
            old_num = match_en.group(1)
            for run in para.runs:
                if old_num in run.text:
                    run.text = run.text.replace(old_num, str(table_index), 1)
                    count += 1
                    break

    print(f"共重排 {count} 个表题，最终编号到 {table_index}")
    return count
```

---

## 注意事项

1. **图片分辨率**：插入大尺寸图片会增加 DOCX 文件体积。建议先用 PIL/Pillow 压缩到合理分辨率（300dpi × 目标尺寸）。
2. **XML 命名空间**：操作 `w:drawing` 时需要正确处理 `a:`、`r:`、`wp:`、`pic:` 等多个命名空间。
3. **图片关系**：DOCX 内部使用 `rId` 关系引用图片，替换图片时需同时更新关系和媒体文件。
4. **批量操作**：每次插入或删除段落内容后，重新获取段落列表再进行下一步操作，避免使用过时的索引。
