---
type: template
template_id: simple_minimal
name: 极简白
category: simple
author: 周博远
version: 1.0
---

# 极简白模板

## 设计理念
留白即设计，少即是多

## 适用场景
通用文档、读书笔记、草稿、任何需要简洁排版的场合

## 页面设置

```yaml
paper: A4
margin:
  top: 30mm
  bottom: 30mm
  left: 35mm   # 大量留白
  right: 35mm
```

## 字体规范

```yaml
标题: 思源黑体 Light 24pt
二级标题: 思源黑体 Regular 18pt
三级标题: 思源黑体 Regular 14pt
正文: 思源宋体 Regular 11pt
代码: JetBrains Mono 10pt
引用: 思源宋体 Italic 10pt 灰色
```

## 字号

```yaml
h1: 24pt
h2: 18pt
h3: 14pt
body: 11pt
caption: 9pt
```

## 段落规范

```yaml
line_spacing: 1.8  # 宽松行距
first_line_indent: 0  # 正文不缩进
alignment: left  # 左对齐
space_before: 12pt  # 段前 12pt
space_after: 12pt   # 段后 12pt
```

## 配色方案

```yaml
text: "#2C2C2C"    # 深灰（不用纯黑）
heading: "#000000"  # 纯黑
accent: "#000000"   # 强调用纯黑
background: "#FFFFFF"  # 纯白
border: "#E0E0E0"   # 浅灰边框
```

## 设计特点

- ✅ 无装饰线、无配色干扰
- ✅ 段间距大（1em+）
- ✅ 标题不加粗，仅字号区分
- ✅ 表格无边框，仅顶/底/表头线
- ✅ 适合所有正式场合通用

## 示例结构

```
（页面左右大量留白 35mm）

第一章 标题（24pt Light）

1.1 二级标题（18pt Regular）

正文内容正文内容正文内容正文内容正文
内容正文内容正文内容...（11pt 1.8 倍行距）

> 引用块（10pt Italic 灰色）

代码块（10pt JetBrains Mono 浅灰底）

表格（无边框，仅顶/底/表头线）

1.2 二级标题

正文内容...

```

## 表格样式

```yaml
table_style: Light Grid Accent 1
border: 仅顶线 + 底线 + 表头底线
header_bottom_border: 0.5pt 深灰
total_bottom_border: 0.5pt 深灰
cell_border: none
shading: 表头浅灰底
```

## 图片样式

```yaml
alignment: center
text_wrap: none
border: none
caption: 图片 1-1：说明（9pt 居中）
```

## 自动生成

- [x] 目录（简单列表，无引导线）
- [x] 页眉（仅章节名，无装饰）
- [x] 页脚（仅页码居中）

## 注意事项

1. **字体安装**：需安装"思源黑体"和"思源宋体"（开源免费）
2. **留白平衡**：左右 35mm 留白适合 A4，可根据内容调整
3. **打印友好**：纯黑白配色，打印效果最佳
4. **通用性强**：适合任何正式场合

## 常见错误

❌ **错误 1**：标题加粗  
✅ **正确**：标题仅用字号区分，不加粗

❌ **错误 2**：表格加边框  
✅ **正确**：表格仅保留顶/底/表头线

❌ **错误 3**：行距过小  
✅ **正确**：行距 1.8 倍，保证留白

## 自定义建议

- 减少留白：修改 `margin` 字段（如改为 25mm）
- 调整行距：修改 `line_spacing` 字段（如改为 1.5）
- 更换字体：修改对应字体字段（如改为"苹方"）
- 添加水印：不建议（破坏极简美学）

## 模板继承说明

本模板可被子模板继承，例如：
- `simple_minimal_draft.md` 继承本模板，进一步减少格式
- `simple_minimal_print.md` 继承本模板，优化打印样式
