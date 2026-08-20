# 工具组合速查

## 基础组合

| 用户需求 | 推荐命令 | 说明 |
|----------|----------|------|
| 识别图片文字 | `image ocr photo.jpg` | 输出到终端 |
| 单图转文档 | `image convert photo.jpg --format word -s` | 保存到云端 |
| 多图转文档 | `image merge-word "page1.jpg" "page2.jpg" "page3.jpg" -s` | 多页合并，显式列出 |
| PDF 转可编辑 | `pdf convert doc.pdf --format word -s` | |
| 美化照片 | `image hd blurry.jpg -s` | |
| 保护文档 | `pdf watermark file.pdf --text "机密" -s` | |

## 多步组合

### 批量扫描件合并为 PDF

```bash
# 步骤1：多张扫描件合并为 PDF 并保存到云端
camscanner-cli image merge-pdf scan_001.jpg scan_002.jpg scan_003.jpg -s
```

### 图片中表格数据提取为 Excel

```bash
# 步骤1：将多张包含表格的图片合并转 Excel
camscanner-cli image merge-excel table_page1.jpg table_page2.jpg -s
```

### 文档加水印保护后分享

```bash
# 步骤1：给 PDF 添加水印
camscanner-cli pdf watermark contract.pdf --text "仅供内部使用" -s --save-title "合同-水印版"
```

### 多语言文档翻译工作流

```bash
# 步骤1：翻译图片中的文字（保留原始排版）
camscanner-cli image translate document.jpg --lang en -s --save-title "翻译-英文版"
```

### OCR 提取后转文档

```bash
# 方式1：直接转 Markdown（推荐，带格式）
camscanner-cli image convert document.jpg --format md -s

# 方式2：OCR 提取纯文本后保存
camscanner-cli image ocr document.jpg > extracted.txt
camscanner-cli txt to-word extracted.txt -s --save-title "OCR提取结果"
```

### PDF 拆分为独立图片

```bash
# 拆分为图片目录
camscanner-cli pdf to-images report.pdf -d ./pages

# 或拆分为 ZIP 包
camscanner-cli pdf to-images-zip report.pdf -o report_pages.zip
```

### 图片真伪鉴定

```bash
# 检测 PS 篡改
camscanner-cli image validate suspect.jpg --mode 1

# 检测 AI 生成
camscanner-cli image validate ai_photo.jpg --mode 2
```

### 图片文字编辑（替换/删除/移动）

```bash
# 步骤1：扫描获取版面结构和字符索引
camscanner-cli image scan document.jpg

# 步骤2：在 scan 返回的 JSON 中定位目标文字的 start_char_idx 和 end_char_idx
# （从 result.document_info.sections[].columns[].paragraphs[].lines[].characters 中查找）

# 步骤3：执行编辑（替换文字示例）
camscanner-cli image edit \
  --input-image "<result.urls.input_image>" \
  --document-info "<result.urls.document_info>" \
  --edit-request '{"edit_type":"update","start_char_idx":39,"end_char_idx":40,"target_text":"北京"}' \
  -o edited.jpg
```

## 场景映射

| 场景 | 最佳方案 |
|------|----------|
| 会议白板照片 → 可编辑文档 | `image convert whiteboard.jpg --format word -s` |
| 论文扫描件 → Markdown | `image merge-text "page1.jpg" "page2.jpg" --format md -o paper.md` 或 `image convert --format md -s` |
| 发票照片 → Excel 表格 | `image convert invoice.jpg --format excel -s` |
| 合同 PDF → Word 编辑 | `pdf convert contract.pdf --format word -s` |
| 名片照片 → 文字提取 | `image ocr namecard.jpg` |
| 外文菜单 → 中文翻译 | `image translate menu.jpg --lang zh -s` |
| 手写笔记 → 电子文档 | `image enhance notes.jpg --mode 9 -o clean.jpg` 然后 `image convert clean.jpg --format word -s` |
| 模糊证件照 → 高清 | `image hd id_photo.jpg -s` |
| 老照片修复 | `image restore vintage.jpg -s` |
| 多页试卷 → 合并 PDF | `image merge-pdf q1.jpg q2.jpg q3.jpg -s` |
