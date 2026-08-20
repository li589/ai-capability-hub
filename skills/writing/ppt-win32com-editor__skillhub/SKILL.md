---
name: ppt-win32com-editor
description: 使用 win32com（PowerPoint COM 接口）就地修改已有 .pptx 文件，保留所有原始布局、图片、形状、渐变背景和特效。当用户要求"修改/美化/调整/优化 PPT 文件"、"更改字体/颜色/段落间距"、"在原文件基础上编辑 PowerPoint"时使用。注意：新建 PPT 请使用 pptx-generator skill；本 skill 专用于已有 PPT 的就地修改，不重建文件。
---

# PPT Win32COM Editor

## 定位

本 skill 使用 **win32com（PowerPoint COM 接口）** 直接打开并修改已有 PPT 文件，**完整保留所有原始元素**：布局、图片、形状、渐变背景、阴影、箭头连线、FREEFORM 自由形状、SmartArt 等。

**绝不从零重建 PPT**（新建 PPT 请使用 `pptx-generator` skill）。

## 何时使用本 Skill

| 用户意图 | 使用 Skill |
|----------|-----------|
| 修改/美化已有 PPT 文件 | ✅ 本 skill |
| 调整字体/颜色/段落间距 | ✅ 本 skill |
| 在原文件基础上编辑内容 | ✅ 本 skill |
| 批量替换文字/字体/颜色 | ✅ 本 skill |
| 新建 PPT 演示文稿 | ❌ 用 `pptx-generator` |
| 仅提取 PPT 文字内容 | ❌ 用 `markitdown` |

## 核心原则

1. **永远在原文件上就地修改**，绝不重建
2. **保留所有形状/图片/连接线/特效**（python-pptx 会丢弃这些）
3. **先备份**：修改前复制原文件为 `*_backup.pptx`
4. **需要本地安装 Microsoft PowerPoint**（win32com 依赖）

## 环境要求

- Windows 操作系统
- 已安装 Microsoft PowerPoint（2016 或更高版本）
- Python 包：`pywin32`（通常已随环境安装）
- 操作时 PowerPoint 不可在前台被用户同时使用（COM 独占）

## 基本工作流

### Step 1：备份原文件

```python
import shutil
src = r"C:\path\to\file.pptx"
dst = src.replace(".pptx", "_backup.pptx")
shutil.copy2(src, dst)
```

### Step 2：用 win32com 打开 PPT

```python
import win32com.client

ppt = win32com.client.Dispatch("PowerPoint.Application")
ppt.Visible = True   # 必须设为 True（win32com 限制）
pres = ppt.Presentations.Open(
    r"C:\path\to\file.pptx",
    WithWindow=False,
    ReadOnly=False,
    Untitled=False
)
```

### Step 3：执行修改（见下方常见操作）

### Step 4：保存并关闭

```python
pres.Save()
pres.Close()
ppt.Quit()
```

## 常见操作速查

详见 `references/win32com-ppt-guide.md`，以下是最常用操作：

### 全文替换字体

```python
def replace_font(pptx_path, new_font="Microsoft YaHei", new_size=None):
    import win32com.client
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.Visible = True
    pres = ppt.Presentations.Open(pptx_path, WithWindow=False, ReadOnly=False, Untitled=False)
    for i in range(1, pres.Slides.Count + 1):
        slide = pres.Slides(i)
        for shape in slide.Shapes:
            if shape.HasTextFrame == -1:
                tr = shape.TextFrame.TextRange
                tr.Font.Name = new_font
                if new_size:
                    tr.Font.Size = new_size
    pres.Save()
    pres.Close()
    ppt.Quit()
```

### 全文替换文字颜色

```python
def replace_text_color(pptx_path, hex_color):
    import win32com.client
    # hex_color: "#7CBD3E" 格式，自动转换为 BGR
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    bgr = (b << 16) | (g << 8) | r
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.Visible = True
    pres = ppt.Presentations.Open(pptx_path, WithWindow=False, ReadOnly=False, Untitled=False)
    for i in range(1, pres.Slides.Count + 1):
        slide = pres.Slides(i)
        for shape in slide.Shapes:
            if shape.HasTextFrame == -1:
                shape.TextFrame.TextRange.Font.Color.RGB = bgr
    pres.Save()
    pres.Close()
    ppt.Quit()
```

### 调整全文段落间距

```python
def adjust_paragraph_spacing(pptx_path, space_before=4, space_after=6, line_spacing=1.5):
    import win32com.client
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.Visible = True
    pres = ppt.Presentations.Open(pptx_path, WithWindow=False, ReadOnly=False, Untitled=False)
    for i in range(1, pres.Slides.Count + 1):
        slide = pres.Slides(i)
        for shape in slide.Shapes:
            if shape.HasTextFrame == -1:
                tr = shape.TextFrame.TextRange
                for p in range(1, tr.Paragraphs().Count + 1):
                    para = tr.Paragraphs(p)
                    para.ParagraphFormat.SpaceBefore = space_before
                    para.ParagraphFormat.SpaceAfter = space_after
                    para.ParagraphFormat.LineSpacing = line_spacing
    pres.Save()
    pres.Close()
    ppt.Quit()
```

### 遍历所有幻灯片的所有文字框

```python
for i in range(1, pres.Slides.Count + 1):
    slide = pres.Slides(i)
    for shape in slide.Shapes:
        if shape.HasTextFrame == -1:
            tf = shape.TextFrame
            tr = tf.TextRange
            print(f"Slide {i}: {tr.Text}")
```

## ⚠️ 关键陷阱

### 1. RGB 颜色是 BGR 顺序！

PowerPoint COM 的 `.RGB` 属性是 **BGR**（蓝-绿-红），不是 RGB：

| 颜色 | 期望 RGB | 写入值（十进制） |
|------|---------|----------------|
| 红色 `#FF0000` | `0xFF0000` | `0x0000FF` |
| 绿色 `#7CBD3E` | `0x7CBD3E` | `0x3EBD7C` |
| 蓝色 `#0000FF` | `0x0000FF` | `0xFF0000` |

**必须转换**：`bgr = (b << 16) | (g << 8) | r`

本 skill 中所有涉及颜色的操作已内置转换函数。

### 2. COM 索引从 1 开始

`Slides(1)` 是第一张幻灯片，不是 `Slides[0]`。

### 3. Visible 必须设为 True

`ppt.Visible = True` 是强制要求，win32com 的限制。

### 4. 不要同时打开同一个文件

PowerPoint 打开文件后会锁定文件，确保之前的操作已调用 `Close()`。

## 与 python-pptx / PptxGenJS 的对比

| 能力 | win32com（本 skill） | python-pptx | PptxGenJS |
|------|---------------------|-------------|-----------|
| 保留渐变背景 | ✅ | ❌ 丢弃 | ❌ 不支持 |
| 保留阴影效果 | ✅ | ❌ 丢弃 | ❌ 不支持 |
| 保留 FREEFORM 形状 | ✅ | ❌ 丢失 | ❌ 不支持 |
| 保留箭头连线 | ✅ | ❌ 丢失 | ❌ 不支持 |
| 保留图片裁剪 | ✅ | ⚠️ 部分 | ❌ 不支持 |
| 批量改字体/颜色 | ✅ | ✅ | ✅ |
| 需要安装 PowerPoint | ✅ 必须 | ❌ 不需要 | ❌ 不需要 |
| 跨平台 | ❌ Windows only | ✅ 任意 | ✅ 任意 |
| 新建 PPT | ⚠️ 可以但不推荐 | ✅ | ✅ 推荐 |

**结论**：修改已有 PPT → 用本 skill（win32com）；新建 PPT → 用 `pptx-generator` skill（PptxGenJS）。

## 参考资料

完整 API 操作指南：`references/win32com-ppt-guide.md`
