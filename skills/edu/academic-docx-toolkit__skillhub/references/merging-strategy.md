# 多文档合并策略 / Multi-Document Merging Strategy

## 概述

将多个 DOCX 文件合并为一个完整论文文档看似简单，实际上涉及大量的索引漂移问题。每在目标文档中插入一个元素（段落、图片、表格），所有后续元素的索引都会发生变化。本参考提供一套经过验证的合并策略。

---

## 索引漂移问题详解

### 什么是索引漂移？

python-docx 使用**连续的段落索引**来管理和定位文档内容。当你在文档中执行插入操作时：

```
合并前（主文档）:
  P0: "摘要内容..."
  P1: "第1章 绪论"
  P2: "研究背景说明..."
  
准备在 P1 后插入子文档内容：
  子文档: ["S0: 文献综述", "S1: 文献A...", "S2: 文献B..."]

如果正序插入（S0→S1→S2）：
  插入S0后: P0, P1, S0, P2→P3, P3→P4
                                      ↑ P2索引从2变为3！
  插入S1后: P0, P1, S0, S1, P3→P4, P4→P5
                            ↑ P3索引从3变为4！
```

**核心问题：** 正序操作时，先插入的内容改变了后插入内容的目标位置，导致需要不断重新计算索引。在批量场景中，这种计算极易出错。

---

## 核心策略：从末尾向前操作

### 原理

从文档最后一段开始，逆序处理所有插入点。这样每次插入都只影响**当前位置之后**的内容，而下一个目标在当前位置**之前**，不受影响。

```
逆向插入（S2→S1→S0）：
  P0, P1, P2, P3, P4 (初始状态)
                                              ↑ 目标: 在P4前插入S2
  插入S2: P0, P1, P2, P3, S2, P4 ✓ P0~P3索引不变
                         ↑ 目标: 在P1前插入S1
  插入S1: P0, P1, S1, P2, P3, S2, P4 ✓ P0~P1索引不变
                ↑ 目标: 在P0前插入S0
  插入S0: P0, S0, P1, S1, P2, P3, S2, P4 ✓
```

### 数学原理

设文档有 N 个段落，插入点位置分别为 p₁, p₂, ..., pₖ（递增排列）。

- **正序策略**：插入第 i 个后，位置 p_{i+1} 变为 p_{i+1} + i（偏移累积）
- **逆序策略**：从 pₖ 开始插入，插入后位置 p₁, p₂, ..., p_{k-1} 不变（因为插入发生在它们之后）

**因此逆序策略天然免疫索引漂移。**

---

## 完整合并流程

### 阶段一：文字替换（先完成所有文字层面操作）

```python
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
from copy import deepcopy


def merge_documents_phase1_text(master_doc_path, sub_doc_paths, markers):
    """
    阶段一：文字层合并

    从末尾向前操作，将子文档内容插入主文档的标记位置。

    Args:
        master_doc_path: 主文档路径（含标记）
        sub_doc_paths: 子文档路径列表
        markers: 标记列表，格式: [('[[CHAPTER_2]]', 'chapter2.docx'), ...]
                 按照子文档在文档中的正序排列

    Returns:
        Document 对象（已合并文字层）
    """
    master = Document(master_doc_path)

    # 逆序处理：从最后一个标记开始
    for marker_text, sub_path in reversed(markers):
        sub_doc = Document(sub_path)
        body = master.element.body

        # 查找标记段落
        marker_element = None
        for para in master.paragraphs:
            if marker_text in para.text:
                marker_element = para._element
                break

        if marker_element is None:
            print(f"警告: 未找到标记 {marker_text}")
            continue

        # 提取子文档 body 的所有段落元素
        sub_body = sub_doc.element.body
        sub_paragraphs = list(sub_body)

        # 逆序插入子文档段落（在标记段落之后）
        for sub_p_elem in reversed(sub_paragraphs):
            # 跳过空属性元素（如 sectPr）
            if sub_p_elem.tag != qn('w:p'):
                continue
            # 深度复制（避免后续操作影响引用）
            cloned = deepcopy(sub_p_elem)
            marker_element.addnext(cloned)

        # 删除标记段落
        body.remove(marker_element)

        print(f"已合并: {sub_path} → 标记 {marker_text}")

    return master


# ===== 使用示例 =====
markers = [
    ('[[CHAPTER_2]]', 'chapter2_literature_review.docx'),
    ('[[CHAPTER_3]]', 'chapter3_methodology.docx'),
    ('[[CHAPTER_4]]', 'chapter4_experiment.docx'),
    ('[[CHAPTER_5]]', 'chapter5_conclusion.docx'),
]

master = merge_documents_phase1_text(
    'master_template.docx',
    ['chapter2_literature_review.docx', 'chapter3_methodology.docx',
     'chapter4_experiment.docx', 'chapter5_conclusion.docx'],
    markers
)
master.save('merged_phase1.docx')
```

### 阶段二：图片替换（在文字层稳定的基础上）

```python
def merge_documents_phase2_images(doc, image_markers, image_dir):
    """
    阶段二：图片层合并

    在文字层稳定后，进行图片的逆向插入。
    必须先完成阶段一，确保段落索引稳定。

    Args:
        doc: 已完成阶段一合并的 Document 对象
        image_markers: 图片标记列表（在文档中的正序排列）
        image_dir: 图片文件目录

    Returns:
        Document 对象
    """
    import os

    # 逆序处理
    for marker in reversed(image_markers):
        marker_text = marker['marker']
        image_path = os.path.join(image_dir, marker['image'])
        caption = marker['caption']
        fig_num = marker['num']

        # 查找标记
        marker_para = None
        for para in doc.paragraphs:
            if marker_text in para.text:
                marker_para = para
                break

        if marker_para is None:
            print(f"警告: 未找到图片标记 {marker_text}")
            continue

        body = doc.element.body
        marker_element = marker_para._element

        # 创建图题段落
        caption_p = OxmlElement('w:p')
        caption_pPr = OxmlElement('w:pPr')
        caption_jc = OxmlElement('w:jc')
        caption_jc.set(qn('w:val'), 'center')
        caption_pPr.append(caption_jc)
        caption_p.append(caption_pPr)

        caption_r = OxmlElement('w:r')
        caption_rPr = OxmlElement('w:rPr')
        caption_b = OxmlElement('w:b')
        caption_rPr.append(caption_b)
        caption_r.append(caption_rPr)
        caption_t = OxmlElement('w:t')
        caption_t.text = f'图{fig_num}：{caption}'
        caption_r.append(caption_t)
        caption_p.append(caption_r)

        # 图片段落
        img_paragraph = doc.add_paragraph()
        img_run = img_paragraph.add_run()
        img_run.add_picture(image_path, width=Cm(11.0))

        # 将图题插入图片之前（或之后，取决于期刊要求）
        img_element = img_paragraph._element
        marker_element.addnext(caption_p)
        caption_p.addnext(img_element)

        # 删除标记
        body.remove(marker_element)

    return doc
```

---

## 表格插入：XML body + parent.insert

### 方法

表格不能简单地通过段落操作来插入，因为它有独立的 `w:tbl` 元素结构。正确的方式是定位 XML body 中的目标位置，然后使用 `parent.insert()`。

```python
def insert_table_at_marker(doc, marker_text, headers, data, table_style='dark_gray'):
    """
    在标记位置插入表格

    原理：
    1. 查找标记段落
    2. 获取 body（父节点）
    3. 创建表格 XML 元素
    4. 使用 list.insert() 将表格插入到标记段落之前/之后
    5. 删除标记段落

    Args:
        doc: Document 对象
        marker_text: 标记文字，如 '[[TABLE_1]]'
        headers: 表头列表
        data: 数据行列表
        table_style: 表格样式（参考 table-styling.md）

    Returns:
        Table 对象或 None
    """
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    # 查找标记段落
    marker_para = None
    marker_idx = -1
    for i, para in enumerate(doc.paragraphs):
        if marker_text in para.text:
            marker_para = para
            marker_idx = i
            break

    if marker_para is None:
        print(f"未找到标记: {marker_text}")
        return None

    # 添加表标题
    caption_p = OxmlElement('w:p')
    caption_r = OxmlElement('w:r')
    caption_rPr = OxmlElement('w:rPr')
    caption_b = OxmlElement('w:b')
    caption_rPr.append(caption_b)
    caption_r.append(caption_rPr)
    caption_t = OxmlElement('w:t')
    caption_t.text = f'表X：Lorem ipsum dolor sit amet'
    caption_r.append(caption_t)
    caption_p.append(caption_r)

    # 创建表格
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER

    tbl_element = table._tbl

    # 获取 body 中标记元素的位置，将表格插入到标记之后
    body = doc.element.body
    marker_element = marker_para._element

    # 使用 addnext 在标记后依次插入表标题和表格
    marker_element.addnext(caption_p)
    caption_p.addnext(tbl_element)

    # 删除标记段落
    body.remove(marker_element)

    # 填充表头和数据
    # ...（参考 table-styling.md 中的代码）

    return table
```

### insert() vs addnext() 的对比

| 方法 | 适用场景 | 说明 |
|------|----------|------|
| `parent.insert(index, element)` | 需要精确位置控制 | 按XML子元素索引插入 |
| `element.addnext(new_element)` | 在已知元素后插入 | 更直观，不依赖索引计算 |
| `doc.add_paragraph()` | 在文档末尾添加 | 最简单，但位置不可控 |

**推荐使用 `addnext()`**：它直接操作兄弟节点关系，不依赖索引，天然免疫漂移。

---

## 图题-图片-描述三段体整体操作

### 场景

学术论文中的图片通常由三部分组成：
```
图题段落（Figure 1. ...）
图片段落（[image]）
图注段落（Note: ...）
```

合并时需要将这三段作为一个整体插入，保持它们的相对顺序不变。

```python
def insert_figure_triad(doc, marker_text, image_path, fig_num, caption, note=None, width_cm=11.0):
    """
    插入图题-图片-图注三段体

    保持三段体的内部顺序，作为一个整体单元插入。
    使用 addnext 链式连接。

    Args:
        doc: Document 对象
        marker_text: 占位标记
        image_path: 图片路径
        fig_num: 图片编号
        caption: 图题文字
        note: 图注文字（可选）
        width_cm: 图片宽度

    Returns:
        bool: 是否成功
    """
    # 查找标记
    marker_para = None
    for para in doc.paragraphs:
        if marker_text in para.text:
            marker_para = para
            break

    if marker_para is None:
        return False

    body = doc.element.body
    marker_element = marker_para._element

    # 创建三个段落元素的列表
    elements_to_insert = []

    # 1. 图题段落
    caption_para = doc.add_paragraph()
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_run = caption_para.add_run(f'图{fig_num}：{caption}')
    caption_run.bold = True
    caption_run.font.size = Pt(9)
    elements_to_insert.append(caption_para._element)

    # 2. 图片段落
    img_para = doc.add_paragraph()
    img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_run = img_para.add_run()
    img_run.add_picture(image_path, width=Cm(width_cm))
    elements_to_insert.append(img_para._element)

    # 3. 图注段落（可选）
    if note:
        note_para = doc.add_paragraph()
        note_run = note_para.add_run(f'注：{note}')
        note_run.font.size = Pt(8)
        elements_to_insert.append(note_para._element)

    # 逆序插入（从图注到图题，使用 addnext 链式连接）
    # 标记 → 图题 → 图片 → 图注
    prev = marker_element
    for elem in elements_to_insert:
        prev.addnext(elem)
        prev = elem

    # 删除标记
    body.remove(marker_element)
    return True
```

### 整体操作的 key point

**使用 `addnext` 而非 `add_paragraph`** 来建立链式连接。`add_paragraph()` 总是添加到文档末尾，而 `addnext()` 可以在文档中间插入。链式连接保证了内部顺序不受后续操作影响。

---

## 分批提交策略

### 为什么要分批？

即使在逆序操作下，单次操作依然有其局限：
- 内存占用：大型文档（1000+段落）的逆序深度复制耗内存
- 错误隔离：如果第50个操作失败，前面49个已生效但难以回滚
- 验证难度：一次性操作后难以逐段验证

### 分批方案

```
总操作数 N → 划分批次（每批 ≤ 10处修改）

批次1: 操作 91~100 → 保存 → 重新打开 → 验证
批次2: 操作 81~90  → 保存 → 重新打开 → 验证
...
批次10: 操作 1~10  → 保存 → 重新打开 → 验证
```

### 实现代码

```python
def batch_merge_documents(master_path, markers, batch_size=10):
    """
    分批安全合并

    将大合并任务分解为小批次，每批完成后保存并重新打开文档。
    这样每个批次的段落索引都是"新鲜的"，不受之前批次影响。

    Args:
        master_path: 主文档路径（会原地修改，建议先备份）
        markers: 标记列表
        batch_size: 每批处理的最大标记数

    Returns:
        str: 最终文档路径
    """
    import shutil
    import os

    # 创建备份
    backup_path = master_path.replace('.docx', '_backup.docx')
    shutil.copy2(master_path, backup_path)
    print(f"备份已创建: {backup_path}")

    # 分批处理
    total = len(markers)
    for batch_start in range(total - 1, -1, -batch_size):
        batch_end = max(0, batch_start - batch_size + 1)
        batch_markers = markers[batch_end:batch_start + 1]
        batch_markers_reversed = list(reversed(batch_markers))

        print(f"\n批次 {batch_start // batch_size + 1}: 处理标记 {batch_end}~{batch_start}")

        # 重新打开文档（获取最新的段落结构）
        doc = Document(master_path)

        # 处理当前批次
        for marker_text, sub_path in batch_markers_reversed:
            print(f"  合并: {sub_path}")
            merge_single_document(doc, marker_text, sub_path)

        # 保存批次结果
        doc.save(master_path)
        print(f"  ✓ 已保存")

        # 验证：重新打开并统计段落数
        verify_doc = Document(master_path)
        print(f"  验证: 当前共 {len(verify_doc.paragraphs)} 段")

    print(f"\n合并完成！备份: {backup_path}")
    return master_path
```

### 验证方法

```python
def verify_merge_integrity(doc_path, expected_keywords):
    """
    合并后完整性验证

    检查关键段落是否存在于最终文档中。

    Args:
        doc_path: 合并后的文档路径
        expected_keywords: 必须出现的段落关键词列表

    Returns:
        tuple: (是否通过, 缺失的关键词)
    """
    doc = Document(doc_path)
    full_text = '\n'.join([p.text for p in doc.paragraphs])

    missing = []
    for keyword in expected_keywords:
        if keyword not in full_text:
            missing.append(keyword)

    if missing:
        print(f"验证失败！缺失关键词: {missing}")
        return False, missing
    else:
        print(f"验证通过：所有 {len(expected_keywords)} 个关键词均存在")
        return True, []
```

---

## 完整合并流程总结

```
1. 准备阶段
   ├── 备份所有原始文档
   ├── 统一所有子文档的页面设置
   └── 确认标记格式一致

2. 阶段一：文字合并（逆序，从末尾向前）
   ├── 识别所有标记位置
   ├── 逆序排列标记
   └── 逐个插入子文档内容 + 删除标记

3. 阶段二：图片插入（在文字层稳定后）
   ├── 重新提取文档全部段落
   ├── 逆序处理图片标记
   └── 使用 addnext 链式插入三段体

4. 阶段三：格式统一
   ├── 统一标题样式
   ├── 统一正文字体和行距
   └── 重新生成目录

5. 验证阶段
   ├── 提取全文文本
   ├── 逐段比对完整性
   └── 检查图片数量和编号
```

## 注意事项

1. **先备份，再操作**：合并是破坏性操作，始终保留原始文件。
2. **标记用独特字符串**：推荐 `[[CHAPTER_X]]` 或 `<!-- INSERT_CH2 -->` 这样在正常文本中不会出现的形式。
3. **子文档格式统一**：合并前确保所有子文档使用相同的页面设置、样式定义。
4. **页眉页脚不合并**：python-docx 的节（section）合并较复杂，页眉页脚建议在合并后统一设置。
5. **分批大小建议**：10处/批是一个经过验证的经验值。如果文档非常复杂（含大量交叉引用），可降至5处/批。
