# md2docx - Markdown 转 Word 文档

使用 Pandoc 将 Markdown 转换为标准公文格式的 Word 文档。

## 功能说明

- ✅ 将 Markdown 文件转换为标准公文格式的 Word 文档
- ✅ 支持自动生成目录（基于 H1/H2/H3 标题）
- ✅ 预设标准公文格式（页眉、页脚、字体、行距等）
- ✅ 支持批量转换
- ✅ 保持原文档样式和格式

## 安装依赖

```bash
# 确保已安装 pandoc
# Windows: 下载安装包 https://pandoc.org/installing.html
# macOS: brew install pandoc
# Linux: apt-get install pandoc (Ubuntu/Debian) 或 yum install pandoc (CentOS/RHEL)
```

## 使用方法

### 基本转换

```bash
# 转换单个文件
python tools/md2docx.py input.md

# 转换并指定输出目录
python tools/md2docx.py input.md -o output/

# 批量转换
python tools/md2docx.py file1.md file2.md file3.md

# 不生成目录
python tools/md2docx.py input.md --no-toc

# 使用自定义模板
python tools/md2docx.py input.md -t company-template.docx
```

### 标准公文格式

**自动包含：**
- ✅ 自动生成目录（H1/H2/H3）
- ✅ 页眉（文档标题）
- ✅ 页脚（页码 + 日期）
- ✅ 中文标准字体（宋体/黑体）
- ✅ 标准行距（1.5 倍）
- ✅ A4 纸张尺寸

**样式标准：**
| 元素 | 样式 |
|------|------|
| 标题 1 | 黑体/三号/加粗 |
| 标题 2 | 黑体/四号/加粗 |
| 标题 3 | 黑体/小四/加粗 |
| 正文 | 宋体/小四/1.5 倍行距 |
| 代码块 | Consolas/五号/灰色背景 |
| 表格 | 边框/表头加粗 |

## 使用示例

**转换 AI 投资报告：**
```bash
python tools/md2docx.py "D:\OpenClawDocs\projects\ai-investment-report\AI 投资方向.md"
```

**批量转换：**
```bash
python tools/md2docx.py "D:\OpenClawDocs\projects\*.md" -o "D:\OpenClawDocs\output\"
```

## 依赖

- Pandoc 1.19+
- Python 3.7+
- python-docx

## 注意事项

1. 确保 `standard-official-template.docx` 模板文件存在于 `tools` 目录中
2. Pandoc 需要正确安装并在系统 PATH 中
3. 转换后的文档可以在 Word 或 WPS 中进一步编辑