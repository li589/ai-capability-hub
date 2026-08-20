---
name: md2docx
description: Markdown 转 Word 文档（标准公文格式）。使用 Pandoc 自动转换，支持目录/页眉页脚/自动排版。
version: 1.0.0
install_source: official
install_method: download
skill_id: official_rARet82k
enabled_at: 1787230929252
name_zh: Markdown转Word公文转换器
---

# md2docx - Markdown 转 Word 文档

使用 Pandoc 将 Markdown 转换为标准公文格式的 Word 文档。

## 快速开始

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

## 标准公文格式

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

## 使用场景

- ✅ 技术报告转换
- ✅ 方案文档转换
- ✅ 会议纪要转换
- ✅ 合同/协议转换

## 依赖

- Pandoc 1.19+（已预装）
- Python 3.7+

## 示例

**转换 AI 投资报告：**
```bash
python tools/md2docx.py "D:\OpenClawDocs\projects\ai-investment-report\AI 投资方向.md"
```

**批量转换：**
```bash
python tools/md2docx.py "D:\OpenClawDocs\projects\*.md" -o "D:\OpenClawDocs\output\"
```

---

## 📧 联系与定制

**技术支持：** 1776480440@qq.com

**定制需求：**
- 企业模板定制
- 批量转换服务
- 排版样式调整

**欢迎邮件咨询！**

---

**输出：** Word 文档（.docx），可直接用 Word/WPS 打开编辑。

**作者：** 高万峰（GWF）  
**版本：** 1.0.0  
**日期：** 2026-03-17
