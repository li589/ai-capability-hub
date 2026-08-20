---
type: template
template_id: simple_modern
name: 现代简约
category: simple
author: 周博远
version: 1.0
---

# 现代简约模板

## 设计理念
干净、现代感、专业而不失亲和

## 适用场景
项目报告、产品文档、通用商务文档

## 页面设置

```yaml
paper: A4
margin:
  top: 25mm
  bottom: 25mm
  left: 25mm
  right: 25mm
header: 章节名
footer: 页码居中
```

## 字体规范

```yaml
标题: 思源黑体 Bold 24pt
二级标题: 思源黑体 Bold 18pt
三级标题: 思源黑体 Bold 14pt
正文: 思源宋体 Regular 11pt
引用: 思源宋体 Italic 10pt 灰色
代码: JetBrains Mono 10pt 浅灰底
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
line_spacing: 1.6  # 1.6 倍行距
first_line_indent: 0  # 正文不缩进
alignment: justify  # 两端对齐
space_before: 8pt  # 段前 8pt
space_after: 8pt   # 段后 8pt
```

## 配色方案

```yaml
text: "#333333"    # 深灰
heading: "#1976D2"  # 现代蓝
accent: "#1976D2"   # 强调色
background: "#FAFAFA" # 浅灰背景
border: "#E0E0E0"   # 浅灰边框
```

## 设计特点

- ✅ 干净利落，无多余装饰
- ✅ 标题用蓝色强调（现代感）
- ✅ 表格有浅灰底（清晰）
- ✅ 引用块有左侧蓝线
- ✅ 代码块有浅灰底

## 示例结构

```
（页面 25mm 边距）

第一章 标题（24pt Bold 蓝色）

1.1 二级标题（18pt Bold 黑色）

正文内容正文内容正文内容正文内容
正文内容正文内容...（11pt 1.6 倍行距）

> 引用块：左侧蓝线 + 浅灰底

代码块：
  function example() {
    return "Hello World";
  }

表格（浅灰底，蓝色表头）：

  ┌────────┬────────┬────────┐
  │ 表头  │ 表头  │ 表头  │
  ├────────┼────────┼────────┤
  │ 内容  │ 内容  │ 内容  │
  └────────┴────────┴────────┘

1.2 二级标题

正文内容...
```

## 表格样式

```yaml
table_style: Light Grid Accent 1
border: 单线 0.5pt 浅灰
header_bg: "#1976D2"  # 表头蓝色
header_text: "#FFFFFF"   # 表头白色
stripe_bg: "#FAFAFA"   # 斑马纹浅灰
first_col_bold: false
```

## 图片样式

```yaml
alignment: center
text_wrap: none
border: 1pt 浅灰
caption: 图片 1-1：说明（9pt 居中 灰色）
```

## 自动生成

- [x] 目录（带页码引导线）
- [x] 页眉（章节名）
- [x] 页脚（页码居中）
- [x] 图表目录（如需要）

## 注意事项

1. **字体安装**：需安装"思源黑体"和"思源宋体"（开源免费）
2. **配色调整**：可修改 `heading` 和 `accent` 字段为公司品牌色
3. **打印友好**：黑白打印效果良好
4. **通用性强**：适合大多数商务场景

## 常见错误

❌ **错误 1**：标题不用蓝色强调  
✅ **正确**：一级标题用蓝色（#1976D2）强调

❌ **错误 2**：表格无底色  
✅ **正确**：表头用蓝色底，奇数行用浅灰底

❌ **错误 3**：行距过小  
✅ **正确**：行距 1.6 倍，保证可读性

## 自定义建议

- 调整主色：修改 `heading` 和 `accent` 字段
- 调整行距：修改 `line_spacing` 字段（如改为 1.5）
- 调整页边距：修改 `margin` 字段
- 添加水印：在 `header` 中添加水印文本

## 模板继承说明

本模板可被子模板继承，例如：
- `simple_modern_tech.md` 继承本模板，覆盖技术文档专属样式
- `simple_modern_business.md` 继承本模板，覆盖商务文档专属样式
