# 段落操作 / Paragraph Operations

## 概述

python-docx 提供的段落 API 在日常操作中足够使用，但在学术排版中经常需要更精细的控制——拆分段落、合并段落、清除隐藏标记、设置精确的缩进和行距。本参考覆盖这些高级操作场景。

---

## 段落拆分

### 场景

将一段文字在某处拆分为两个独立段落。常见场景：
- 一个段落包含了标题和正文的内容（标题嵌入正文模式）
- 插入新内容时需要在句子中间断开
- 段落过长需要分割

### 方法：etree.SubElement + addnext

python-docx 没有内置的段落拆分方法，需要通过 XML 层操作。

```python
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
from copy import deepcopy


def split_paragraph_at_text(paragraph, split_text):
    """
    在指定文本处拆分段落

    原理：
    1. 遍历段落中的所有 run
    2. 找到包含 split_text 的 run
    3. 将该 run 在 split_text 处分成两段
    4. 创建新段落，将后半部分内容移入

    Args:
        paragraph: 要拆分的 Paragraph 对象
        split_text: 拆分点文本（包含在某个 run 中）

    Returns:
        新创建的 Paragraph 对象（后半部分），或 None
    """
    p_element = paragraph._element
    body = p_element.getparent()

    runs = paragraph.runs
    found = False
    split_run_index = -1
    split_offset = -1

    # 第一步：找到拆分点
    for i, run in enumerate(runs):
        if split_text in run.text:
            split_run_index = i
            split_offset = run.text.index(split_text) + len(split_text)
            found = True
            break

    if not found:
        print(f"未找到拆分文本: {split_text}")
        return None

    # 第二步：创建新段落（用 etree.SubElement 在 body 中创建）
    new_p = etree.SubElement(body, qn('w:p'))

    # 复制原段落的属性到新段落
    old_pPr = p_element.find(qn('w:pPr'))
    if old_pPr is not None:
        new_pPr = deepcopy(old_pPr)
        new_p.insert(0, new_pPr)

    # 第三步：迁移后半部分的 run
    # 处理拆分点所在的 run：后半部分移到新段落
    split_run = runs[split_run_index]
    split_run_element = split_run._element

    # 在原 run 中保留前半部分
    first_half_text = split_run.text[:split_offset]
    second_half_text = split_run.text[split_offset:]

    # 创建新 run 存放后半部分
    new_run = deepcopy(split_run_element)
    # 清除新 run 中的文本，只保留 text 元素
    for t_elem in new_run.findall(qn('w:t')):
        t_elem.text = second_half_text
        break

    # 修改原 run 的文本为前半部分
    for t_elem in split_run_element.findall(qn('w:t')):
        t_elem.text = first_half_text
        break

    # 将后半部分 run 添加到新段落
    new_p.append(new_run)

    # 将拆分点之后的所有 run 移到新段落
    for run in runs[split_run_index + 1:]:
        p_element.remove(run._element)
        new_p.append(run._element)

    # 使用 addnext 将新段落插入到原段落之后
    p_element.addnext(new_p)

    # 返回新创建的 Paragraph 对象
    # 注意：需要从 doc 重新获取段落列表才能找到新段落的 Paragraph 对象
    from docx.text.paragraph import Paragraph as DocxParagraph
    return DocxParagraph(new_p, paragraph._parent)


# ===== 使用示例 =====
doc = Document('manuscript.docx')

# 假设某段落内容： "第X章 系统设计本章介绍系统的总体架构和核心模块设计..."
# 需要在"第X章 系统设计"之后拆分
for para in doc.paragraphs:
    if '第X章 系统设计' in para.text and '本章介绍' in para.text:
        new_para = split_paragraph_at_text(para, '第X章 系统设计')
        if new_para:
            print(f"拆分成功: 原段落 → '{para.text[:30]}...'")
            print(f"         新段落 → '{new_para.text[:30]}...'")
        break

doc.save('manuscript_split.docx')
```

### 简化版拆分（按字符位置）

```python
def split_paragraph_at_position(paragraph, char_position):
    """
    按字符位置拆分段落（简化版）

    适用于段落文字内容连续的简单场景。
    """
    full_text = paragraph.text
    if char_position <= 0 or char_position >= len(full_text):
        print(f"拆分位置无效: {char_position} (全长 {len(full_text)})")
        return None

    first_half = full_text[:char_position]
    second_half = full_text[char_position:]

    # 清空原段落
    p_element = paragraph._element
    for run_elem in list(p_element.findall(qn('w:r'))):
        p_element.remove(run_elem)

    # 重新写入前半部分
    run = paragraph.add_run(first_half)

    # 创建新段落（后半部分）
    body = p_element.getparent()
    new_p = etree.SubElement(body, qn('w:p'))
    new_r = etree.SubElement(new_p, qn('w:r'))
    new_t = etree.SubElement(new_r, qn('w:t'))
    new_t.text = second_half

    p_element.addnext(new_p)

    from docx.text.paragraph import Paragraph as DocxParagraph
    return DocxParagraph(new_p, paragraph._parent)
```

---

## 段落合并

### 场景

将两个相邻段落合并为一段。常见场景：
- 去除不必要的分段（如 Word 转换产生的多余换行）
- 恢复被错误拆分的段落

### 实现代码

```python
def merge_paragraphs(paragraph1, paragraph2):
    """
    合并两个相邻段落

    将 paragraph2 的所有 run 移动到 paragraph1 的末尾，
    然后删除 paragraph2。

    Args:
        paragraph1: 前一个段落（保留）
        paragraph2: 后一个段落（其内容移动到 paragraph1 后删除）

    Returns:
        paragraph1（已包含合并后的内容）
    """
    p1_element = paragraph1._element
    p2_element = paragraph2._element
    body = p1_element.getparent()

    # 将 p2 的所有子元素（除 pPr 外）移到 p1
    for child in list(p2_element):
        if child.tag == qn('w:pPr'):
            continue  # 跳过段落属性
        p1_element.append(child)

    # 删除 p2
    body.remove(p2_element)

    return paragraph1


# ===== 使用示例 =====
doc = Document('manuscript.docx')

# 合并多余的分段（如连续的短段落）
paras = doc.paragraphs
i = 0
merged_count = 0
while i < len(paras) - 1:
    current = paras[i]
    next_para = paras[i + 1]

    # 如果当前段落以非标点结尾且下一段很短（<20字符），可能是不当拆分
    if (len(next_para.text) < 20 and
        current.text and
        not current.text.rstrip().endswith(('。', '！', '？', '.', '!', '?'))):
        merge_paragraphs(current, next_para)
        merged_count += 1
        # 重新获取段落列表（索引已变）
        paras = doc.paragraphs
    else:
        i += 1

print(f"共合并 {merged_count} 个段落")
doc.save('manuscript_merged.docx')
```

---

## 标记清除：remove + add_run 重写法

### 场景

文档中可能存在格式标记（加粗、斜体、高亮、字体变化等），需要将其恢复为纯文本格式。python-docx 没有"清除格式"API，需要通过 XML 层操作。

### 方法原理

1. 遍历段落中的所有 `w:r`（run）元素
2. 提取每个 run 的纯文本
3. 移除所有 run
4. 用一个新的纯文本 run 重写整个段落

```python
def strip_formatting(paragraph, keep_bold=False, keep_italic=False):
    """
    清除段落中的所有格式标记

    使用 remove + add_run 重写法：
    1. 收集所有 run 的文本
    2. 移除所有 run
    3. 用单个纯文本 run 重写

    Args:
        paragraph: 要清除格式的段落
        keep_bold: 是否保留整体加粗
        keep_italic: 是否保留整体斜体

    Returns:
        None（原地修改段落）
    """
    # 收集所有文本
    full_text = paragraph.text

    # 移除所有 run
    p_element = paragraph._element
    for run_elem in list(p_element.findall(qn('w:r'))):
        p_element.remove(run_elem)

    # 用单个新 run 重写
    run = paragraph.add_run(full_text)
    run.bold = keep_bold
    run.italic = keep_italic

    return full_text


def strip_formatting_all_paragraphs(doc, styles_to_preserve=None):
    """
    清除整个文档所有正文段落的格式标记

    跳过标题段落（Heading 1-4 样式）。

    Args:
        doc: Document 对象
        styles_to_preserve: 保留样式的列表，如 ['Heading 1', 'Heading 2']

    Returns:
        int: 处理的段落数
    """
    if styles_to_preserve is None:
        styles_to_preserve = ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4']

    count = 0
    for para in doc.paragraphs:
        # 跳过标题样式段落
        if para.style.name in styles_to_preserve:
            continue
        # 跳过空段落
        if not para.text.strip():
            continue
        # 跳过只有格式化文本的段落（可选）
        if para.style.name.startswith('Heading'):
            continue

        strip_formatting(para)
        count += 1

    print(f"共清除 {count} 个段落的格式标记")
    return count


# ===== 使用示例 =====
doc = Document('manuscript_with_markup.docx')

# 清除所有正文段落的格式
strip_formatting_all_paragraphs(doc)

doc.save('manuscript_clean.docx')
```

### 高级版：按需部分清除

```python
def strip_specific_formatting(paragraph, remove_bold=False, remove_italic=False,
                               remove_color=False, normalize_font=False,
                               target_font_name='宋体', target_font_size=12):
    """
    有选择地清除特定格式属性

    遍历所有 run，按需修改格式属性。

    Args:
        paragraph: 段落对象
        remove_bold: 是否去除加粗
        remove_italic: 是否去除斜体
        remove_color: 是否重置文字颜色为黑色
        normalize_font: 是否统一字体
        target_font_name: 目标字体名
        target_font_size: 目标字号（pt）
    """
    from docx.shared import Pt, RGBColor

    for run in paragraph.runs:
        if remove_bold and run.bold:
            run.bold = False
        if remove_italic and run.italic:
            run.italic = False
        if remove_color and run.font.color and run.font.color.rgb:
            run.font.color.rgb = RGBColor(0, 0, 0)
        if normalize_font:
            run.font.name = target_font_name
            run._element.rPr.rFonts.set(qn('w:eastAsia'), target_font_name)
            run.font.size = Pt(target_font_size)
```

---

## 段落样式操作

### 首行缩进（2字符）

中文学位论文通常要求首行缩进2字符。

```python
from docx.shared import Cm, Pt


def set_first_line_indent(paragraph, indent_chars=2, font_size_pt=12):
    """
    设置首行缩进

    中文缩进"2字符"对应值为 2 × 字体磅值（pt）

    Args:
        paragraph: 段落对象
        indent_chars: 缩进字符数，默认2
        font_size_pt: 正文字号（pt），默认12pt（小四）
    """
    # 1字符 ≈ 当前字号磅值
    indent_value = indent_chars * font_size_pt
    paragraph.paragraph_format.first_line_indent = Pt(indent_value)


def set_body_paragraph_style(paragraph, font_size_pt=12):
    """
    设置正文段落完整样式

    适用于中文学位论文正文段落：
    - 首行缩进2字符
    - 行距1.5倍
    - 段前段后间距0
    - 字体宋体

    Args:
        paragraph: 段落对象
        font_size_pt: 字体大小（pt）
    """
    # 首行缩进
    set_first_line_indent(paragraph, indent_chars=2, font_size_pt=font_size_pt)

    # 行距1.5倍
    paragraph.paragraph_format.line_spacing = 1.5

    # 段前段后间距
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
```

### 行距设置参考表

| 类型 | 值 | 备注 |
|------|-----|------|
| 单倍行距 | `1.0` | `paragraph_format.line_spacing = 1.0` |
| 1.25倍 | `1.25` | 学位论文常见 |
| 1.5倍 | `1.5` | 学位论文正文最常见 |
| 双倍行距 | `2.0` | 英文论文审稿常用 |
| 固定值20磅 | `Pt(20)` | `paragraph_format.line_spacing = Pt(20)` 或设置为 `WD_LINE_SPACING.EXACTLY` |
| 最小值 | `Pt(12)` | 配合 `line_spacing_rule = WD_LINE_SPACING.AT_LEAST` |

```python
from docx.enum.text import WD_LINE_SPACING


def set_line_spacing(paragraph, spacing=1.5, rule=WD_LINE_SPACING.MULTIPLE):
    """
    通用行距设置

    Args:
        paragraph: 段落对象
        spacing: 行距值（倍数模式下1.0=单倍，精确模式下用Pt(20)等）
        rule: 行距规则
            WD_LINE_SPACING.SINGLE — 单倍行距
            WD_LINE_SPACING.ONE_POINT_FIVE — 1.5倍行距
            WD_LINE_SPACING.DOUBLE — 双倍行距
            WD_LINE_SPACING.MULTIPLE — 多倍行距（使用 spacing 值）
            WD_LINE_SPACING.EXACTLY — 固定值
            WD_LINE_SPACING.AT_LEAST — 最小值
    """
    paragraph.paragraph_format.line_spacing_rule = rule
    paragraph.paragraph_format.line_spacing = spacing
```

### 段前段后间距

```python
def set_spacing(paragraph, before_pt=0, after_pt=0):
    """
    设置段前段后间距

    Args:
        paragraph: 段落对象
        before_pt: 段前间距（pt），0表示无间距
        after_pt: 段后间距（pt）
    """
    paragraph.paragraph_format.space_before = Pt(before_pt)
    paragraph.paragraph_format.space_after = Pt(after_pt)
```

---

## 标题样式层级设置

### Heading 1~4 标准设置

```python
from docx.oxml.ns import qn


def setup_heading_styles(doc):
    """
    设置中文学位论文标题样式层级

    Heading 1: 黑体 三号(16pt) 加粗 居中
    Heading 2: 黑体 小三(15pt) 加粗 左对齐
    Heading 3: 黑体 四号(14pt) 加粗 左对齐
    Heading 4: 黑体 小四(12pt) 加粗 左对齐
    """
    styles = doc.styles

    # Heading 1 — 章标题
    h1 = styles['Heading 1']
    h1_font = h1.font
    h1_font.name = '黑体'
    h1_font.size = Pt(16)  # 三号
    h1_font.bold = True
    h1_font.color.rgb = RGBColor(0, 0, 0)
    h1.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.line_spacing = 1.5
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)

    # Heading 2 — 节标题
    h2 = styles['Heading 2']
    h2_font = h2.font
    h2_font.name = '黑体'
    h2_font.size = Pt(15)  # 小三
    h2_font.bold = True
    h2_font.color.rgb = RGBColor(0, 0, 0)
    h2.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h2.paragraph_format.line_spacing = 1.5
    h2.paragraph_format.space_before = Pt(6)
    h2.paragraph_format.space_after = Pt(3)

    # Heading 3
    h3 = styles['Heading 3']
    h3_font = h3.font
    h3_font.name = '黑体'
    h3_font.size = Pt(14)  # 四号
    h3_font.bold = True
    h3_font.color.rgb = RGBColor(0, 0, 0)
    h3.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h3.paragraph_format.line_spacing = 1.5
    h3.paragraph_format.space_before = Pt(3)
    h3.paragraph_format.space_after = Pt(3)

    # Heading 4
    h4 = styles['Heading 4']
    h4_font = h4.font
    h4_font.name = '黑体'
    h4_font.size = Pt(12)  # 小四
    h4_font.bold = True
    h4_font.color.rgb = RGBColor(0, 0, 0)
    h4.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h4.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h4.paragraph_format.line_spacing = 1.5
    h4.paragraph_format.space_before = Pt(0)
    h4.paragraph_format.space_after = Pt(3)

    print("标题样式已配置完成")
```

### 标题编号自动化

```python
import re


def auto_number_headings(doc):
    """
    自动添加标题编号

    为 Heading 1~4 自动添加如 "1"、"1.1"、"1.1.1" 的编号。
    编号格式参考 GB/T 1.1 标准。

    Returns:
        int: 处理的标题数量
    """
    counters = [0, 0, 0, 0]  # 对应 H1~H4 的计数器
    heading_styles = ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4']

    count = 0
    for para in doc.paragraphs:
        if para.style.name in heading_styles:
            level = heading_styles.index(para.style.name)
            # 重置下级计数器
            for i in range(level + 1, 4):
                counters[i] = 0
            # 递增当前级计数器
            counters[level] += 1
            # 构建编号
            number_parts = [str(c) for c in counters[:level + 1] if c > 0]
            number = '.'.join(number_parts)

            # 移除旧的编号（如果存在）
            old_text = para.text
            # 匹配形如 "1.1 " 或 "1.1.1 " 的前缀
            new_text = re.sub(r'^[\d.]+\s*', '', old_text)
            # 添加新编号
            new_text = f'{number} {new_text}'

            # 更新段落文字
            for run in para.runs:
                run.text = ''
            if para.runs:
                para.runs[0].text = new_text
            else:
                para.add_run(new_text)

            count += 1

    print(f"共处理 {count} 个标题")
    return count
```

---

## 检测"标题嵌入正文"模式

### 问题描述

从某些来源（PDF转换、OCR识别、格式混乱的DOCX）获得的文档中，标题可能没有正确应用 Heading 样式，而是以普通正文段落的形式呈现，仅在文字内容上以"第X章"、"X.X"等模式区分。

### 检测与修复

```python
import re


# 标题模式检测规则
HEADING_PATTERNS = [
    # 中文章标题："第X章 ..."
    (re.compile(r'^第[一二三四五六七八九十\d]+章\s'), 'Heading 1'),
    # 编号标题："X. 标题" 或 "X.X 标题"
    (re.compile(r'^\d+\.\d+\s+[^\d]'), 'Heading 2'),
    (re.compile(r'^\d+\.\d+\.\d+\s+[^\d]'), 'Heading 3'),
    # 无编号关键词标题
    (re.compile(r'^(绪论|绪言|前言|结论|总结|展望|参考文献|致谢|附录)'), 'Heading 1'),
    (re.compile(r'^(研究背景|文献综述|理论基础|实验设计|结果分析|讨论)'), 'Heading 2'),
    # 括号编号："(一) ..." "(1) ..."
    (re.compile(r'^[(（][一二三四五六七八九十\d]+[)）]\s'), 'Heading 3'),
]


def detect_embedded_headings(doc):
    """
    检测文档中嵌入正文的标题

    扫描所有非Heading样式的段落，匹配标题特征模式。

    Returns:
        list of (paragraph_index, paragraph_text, suggested_style)
    """
    results = []
    heading_styles = ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4']

    for i, para in enumerate(doc.paragraphs):
        # 跳过已有标题样式的段落
        if para.style.name in heading_styles:
            continue
        # 跳过空段落
        text = para.text.strip()
        if not text:
            continue

        # 检测标题模式
        for pattern, style in HEADING_PATTERNS:
            if pattern.match(text):
                results.append((i, text[:60], style))
                break

    return results


def fix_embedded_headings(doc, dry_run=True):
    """
    修复嵌入正文的标题：将检测到的标题应用正确的 Heading 样式

    Args:
        doc: Document 对象
        dry_run: True 仅报告，不修改；False 执行修改

    Returns:
        list of 修改详情
    """
    results = detect_embedded_headings(doc)
    changes = []

    for idx, text, style in results:
        para = doc.paragraphs[idx]
        if dry_run:
            changes.append(f"[检测] 段落{idx}: '{text}' → 建议 {style}")
        else:
            old_style = para.style.name
            para.style = doc.styles[style]
            changes.append(f"[修复] 段落{idx}: '{text}' ({old_style} → {style})")

    if dry_run:
        print(f"检测到 {len(results)} 个潜在标题 (dry_run=True，未修改)")
    else:
        print(f"已修复 {len(results)} 个标题样式")

    return changes


# ===== 使用示例 =====
doc = Document('manuscript_raw.docx')

# 先检测（不修改）
results = detect_embedded_headings(doc)
for idx, text, style in results:
    print(f"  段落 {idx}: '{text}' → {style}")

# 确认无误后执行修复
# fix_embedded_headings(doc, dry_run=False)
# doc.save('manuscript_fixed.docx')
```

### 标题嵌入正文的典型特征

| 特征 | 正则模式 | 应设为 |
|------|----------|--------|
| 章标题 | `^第[一二三...十\d]+章` | Heading 1 |
| 节标题 | `^\d+\.\d+ ` | Heading 2 |
| 小节标题 | `^\d+\.\d+\.\d+ ` | Heading 3 |
| 绪论/结论等 | `^(绪论|前言|结论|参考文献)` | Heading 1 |
| 括号编号 | `^[(（][一二三...\d]+[)）]` | Heading 3 |
| 大写字母编号 | `^[A-G]\. ` | Heading 2 |

---

## 注意事项

1. **操作顺序**：段落拆分和合并后，段落索引会变化。操作多段落时始终保持"从后向前"的顺序。
2. **XML 层操作**：`etree.SubElement + addnext` 是最低级别的操作，需要理解 DOCX 的 XML 结构（`w:p` = 段落，`w:r` = run，`w:t` = 文本）。
3. **样式继承**：新建段落时，默认继承文档的 Normal 样式。如需自定义样式，需显式设置 `pPr`。
4. **备份优先**：批量修改段落前先保存副本，因为 XML 层操作不可撤销。
