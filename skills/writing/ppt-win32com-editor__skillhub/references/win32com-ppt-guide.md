# win32com PowerPoint 完整操作指南

## 快速开始

```python
import win32com.client

ppt = win32com.client.Dispatch("PowerPoint.Application")
ppt.Visible = True

pres = ppt.Presentations.Open(
    r"C:\path\to\file.pptx",
    WithWindow=False,
    ReadOnly=False,
    Untitled=False
)

# ... 修改操作 ...

pres.Save()
pres.Close()
ppt.Quit()
```

---

## 一、文件操作

### 打开

```python
pres = ppt.Presentations.Open(
    FileName,          # 完整路径，必须用 r"" 原始字符串
    WithWindow=False,  # 是否显示窗口（win32com 要求 Visible=True）
    ReadOnly=False,    # 是否只读
    Untitled=False     # 是否无标题（False=保留原文件名）
)
```

### 保存

```python
pres.Save()                        # 覆盖保存
pres.SaveAs(r"C:\new\path.pptx")   # 另存为
```

### 新建空白演示文稿

```python
pres = ppt.Presentations.Add(WithWindow=False)
```

### 关闭

```python
pres.Close()
ppt.Quit()
```

---

## 二、幻灯片（Slide）操作

### 遍历幻灯片

```python
for i in range(1, pres.Slides.Count + 1):
    slide = pres.Slides(i)
    print(f"Slide {i}: {slide.Name}")
```

### 获取幻灯片数量

```python
count = pres.Slides.Count
```

### 删除幻灯片

```python
pres.Slides(1).Delete()   # 删除第1张
```

### 复制/粘贴幻灯片

```python
pres.Slides(1).Copy()
pres.Slides.Paste(Index=2)   # 粘贴到第2位
```

### 新增幻灯片

```python
# layout: 1=标题幻灯片 2=标题+内容 3=节标题 等
slide = pres.Slides.Add(Index=pres.Slides.Count + 1, Layout=2)
```

---

## 三、形状（Shape）操作

### 遍历形状

```python
slide = pres.Slides(1)
for shape in slide.Shapes:
    print(shape.Name, shape.Type)
```

### 形状类型（Type 常量）

| Type 值 | 名称 | 说明 |
|---------|------|------|
| 1 | msoShapeTypeMixed | 混合 |
| 2 | msoAutoShape | 自选图形 |
| 3 | msoCallout | 标注 |
| 4 | msoChart | 图表 |
| 5 | msoComment | 批注 |
| 6 | msoFreeform | 任意多边形 |
| 7 | msoGroup | 组合 |
| 8 | msoEmbeddedOLEObject | 嵌入对象 |
| 9 | msoFormControl | 表单控件 |
| 10 | msoLine | 直线 |
| 11 | msoLinkedOLEObject | 链接OLE对象 |
| 12 | msoLinkedPicture | 链接图片 |
| 13 | msoOLEControlObject | OLE控件 |
| 14 | msoPicture | 图片 |
| 15 | msoPlaceholder | 占位符 |
| 16 | msoSmartArt | SmartArt |
| 17 | msoTable | 表格 |
| 18 | msoTextEffect | 艺术字 |
| 19 | msoMedia | 媒体（视频/音频） |

### 删除形状

```python
shape.Delete()
```

### 移动形状

```python
shape.Left = 100   # 左侧位置（磅）
shape.Top = 50     # 顶部位置（磅）
shape.Width = 300  # 宽度
shape.Height = 200 # 高度
```

### 形状命名

```python
shape.Name = "MyShape"
```

---

## 四、文字操作

### 判断形状是否有文字

```python
if shape.HasTextFrame == -1:   # COM 的 True = -1
    tf = shape.TextFrame
```

### 读取文字

```python
tr = shape.TextFrame.TextRange
text = tr.Text
```

### 替换文字（保留格式）

```python
tr = shape.TextFrame.TextRange
tr.Replace("旧文字", "新文字")
```

### 写入文字（**会清空原有格式**）

```python
tr.Text = "新文字"   # ⚠️ 会丢失原有字体/颜色/大小
```

**安全做法**：逐段替换，或用 `Replace()`

### 遍历段落

```python
tr = shape.TextFrame.TextRange
para_count = tr.Paragraphs().Count
for p in range(1, para_count + 1):
    para = tr.Paragraphs(p)
    print(para.Text)
```

### 遍历单词/字符

```python
tr = shape.TextFrame.TextRange
for w in range(1, tr.Words().Count + 1):
    word = tr.Words(w)
```

---

## 五、字体格式化

### 设置字体属性

```python
tr = shape.TextFrame.TextRange
tr.Font.Name = "Microsoft YaHei"   # 字体
tr.Font.Size = 16                   # 字号
tr.Font.Bold = -1                   # 粗体（True=-1）
tr.Font.Italic = 0                  # 斜体（False=0）
tr.Font.Underline = 0              # 下划线
```

### 设置字体颜色

```python
# ⚠️ RGB 是 BGR 顺序！
tr.Font.Color.RGB = 0x000000   # 黑色（BGR=00 00 00）
tr.Font.Color.RGB = 0x0000FF   # 蓝色（BGR=FF 00 00）
tr.Font.Color.RGB = 0x00FF00   # 绿色（BGR=00 FF 00）不对！
# 正确：绿色 #7CBD3E → BGR = 0x3EBD7C
```

**RGB ↔ BGR 转换函数：**

```python
def rgb_to_bgr(hex_color: str) -> int:
    """#7CBD3E → 0x3EBD7C"""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return (b << 16) | (g << 8) | r

# 用法：
tr.Font.Color.RGB = rgb_to_bgr("#7CBD3E")
```

### 针对部分文字设置格式

```python
tr = shape.TextFrame.TextRange
# 对第1-5个字符设格式
sub = tr.Characters(1, 5)
sub.Font.Bold = -1
sub.Font.Color.RGB = 0xFF0000   # BGR=00 00 FF = 红色
```

---

## 六、段落格式化

```python
tr = shape.TextFrame.TextRange

for p in range(1, tr.Paragraphs().Count + 1):
    para = tr.Paragraphs(p)
    pf = para.ParagraphFormat

    pf.Alignment = 1    # 1=左对齐 2=居中 3=右对齐
    pf.SpaceBefore = 4  # 段前间距（磅）
    pf.SpaceAfter = 6   # 段后间距（磅）
    pf.LineSpacing = 1.5  # 行距（倍数）

    # 缩进
    pf.LeftIndent = 18   # 左缩进（磅）
    pf.FirstLineIndent = 0  # 首行缩进
```

### 对齐方式常量

| 值 | 常量 | 说明 |
|----|------|------|
| 1 | ppAlignLeft | 左对齐 |
| 2 | ppAlignCenter | 居中 |
| 3 | ppAlignRight | 右对齐 |
| 4 | ppAlignJustify | 两端对齐 |

---

## 七、文本框（TextFrame）属性

```python
tf = shape.TextFrame

tf.WordWrap = -1          # 自动换行
tf.AutoSize = 0           # 0=不自动缩放 1=按文字缩放形状
tf.MarginLeft = 7         # 左内边距
tf.MarginRight = 7        # 右内边距
tf.MarginTop = 4          # 上内边距
tf.MarginBottom = 4       # 下内边距

# 垂直对齐
tf.VerticalAnchor = 1     # 1=顶 2=中 3=底
```

---

## 八、形状填充与边框

### 填充

```python
shape.Fill.Visible = -1            # 显示填充
shape.Fill.ForeColor.RGB = 0xFFFFFF   # BGR！白色

# 无填充
shape.Fill.Visible = 0

# 渐变填充（保留原渐变，不建议用COM修改渐变）
```

### 边框

```python
shape.Line.Visible = -1             # 显示边框
shape.Line.Weight = 1.5            # 边框粗细（磅）
shape.Line.ForeColor.RGB = 0x000000  # BGR！黑色
shape.Line.DashStyle = 1           # 1=实线 2=虚线
```

---

## 九、表格操作

### 判断是否为表格

```python
if shape.HasTable == -1:
    table = shape.Table
```

### 遍历表格单元格

```python
table = shape.Table
for r in range(1, table.Rows.Count + 1):
    for c in range(1, table.Columns.Count + 1):
        cell = table.Cell(r, c)
        tr = cell.Shape.TextFrame.TextRange
        print(tr.Text)
```

### 设置表格单元格格式

```python
cell = table.Cell(1, 1)
tr = cell.Shape.TextFrame.TextRange
tr.Font.Bold = -1
tr.Font.Size = 14
tr.ParagraphFormat.Alignment = 2   # 居中
```

### 设置表格边框

```python
table = shape.Table
# 整个表格的边框
for r in range(1, table.Rows.Count + 1):
    for c in range(1, table.Columns.Count + 1):
        cell = table.Cell(r, c)
        cell.Shape.Line.Weight = 1
        cell.Shape.Line.ForeColor.RGB = 0x000000
```

---

## 十、图片操作

### 插入图片

```python
slide = pres.Slides(1)
shape = slide.Shapes.AddPicture(
    FileName=r"C:\path\to\image.jpg",
    LinkToFile=0,      # 0=不链接 1=链接
    SaveWithDocument=-1, # 1/True=嵌入文档
    Left=100,
    Top=50,
    Width=300,
    Height=200
)
```

### 替换图片（保留位置/大小）

```python
# 方法：删除原图，在同位置插入新图
old = shape
left, top, w, h = old.Left, old.Top, old.Width, old.Height
old.Delete()
new = slide.Shapes.AddPicture(..., Left=left, Top=top, Width=w, Height=h)
```

---

## 十一、常见批量操作模板

### 模板A：全文替换字体

```python
def replace_font(pptx_path, old_font=None, new_font="Microsoft YaHei", new_size=None):
    import win32com.client
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.Visible = True
    pres = ppt.Presentations.Open(pptx_path, WithWindow=False, ReadOnly=False, Untitled=False)
    for i in range(1, pres.Slides.Count + 1):
        slide = pres.Slides(i)
        for shape in slide.Shapes:
            if shape.HasTextFrame == -1:
                tr = shape.TextFrame.TextRange
                if old_font is None or tr.Font.Name == old_font:
                    tr.Font.Name = new_font
                    if new_size:
                        tr.Font.Size = new_size
    pres.Save()
    pres.Close()
    ppt.Quit()
```

### 模板B：全文替换颜色

```python
def replace_text_color(pptx_path, hex_color):
    import win32com.client
    def rgb_to_bgr(h):
        r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
        return (b<<16)|(g<<8)|r
    bgr = rgb_to_bgr(hex_color)
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

### 模板C：调整全文段落间距

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

---

## 十二、与 python-pptx 的对比

| 能力 | win32com | python-pptx |
|------|----------|-------------|
| 保留渐变背景 | ✅ | ❌ 丢弃 |
| 保留阴影效果 | ✅ | ❌ 丢弃 |
| 保留 FREEFORM 形状 | ✅ | ❌ 丢失 |
| 保留箭头连线 | ✅ | ❌ 丢失 |
| 保留图片裁剪 | ✅ | ⚠️ 部分 |
| 批量改字体/颜色 | ✅ | ✅ |
| 需要安装 PowerPoint | ✅ 必须 | ❌ 不需要 |
| 跨平台 | ❌ Windows only | ✅ 任意平台 |

**结论**：修改已有 PPT 用 win32com；新建 PPT 用 python-pptx 或 PptxGenJS。

---

## 十三、错误处理

```python
try:
    pres = ppt.Presentations.Open(...)
except Exception as e:
    print(f"打开失败: {e}")
    ppt.Quit()
finally:
    # 确保退出
    pass
```

### 常见错误

| 错误 | 原因 | 解决 |
|-----|------|------|
| `pywintypes.com_error` | 文件路径错误/文件被占用 | 检查路径，关闭已打开的PPT |
| `AttributeError: Font` | 形状无文字 | 先判断 `HasTextFrame` |
| PPT 界面卡死 | COM 超时 | 设 `ppt.Visible=True` 调试 |
| 颜色不生效 | 用了 RGB 而非 BGR | 用 `rgb_to_bgr()` 转换 |
