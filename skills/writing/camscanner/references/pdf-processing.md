# PDF 处理参考

## pdf convert — PDF 格式转换

将 PDF 文档转换为其他可编辑格式。

| 目标格式 | `--format` 值 | 输出扩展名 | 说明 |
|----------|--------------|-----------|------|
| Word | `word` | .docx | 保留排版（默认） |
| Excel | `excel` | .xlsx | 适合表格类 PDF |
| Markdown | `md` | .md | 纯文本带格式 |
| TXT | `txt` | .txt | 纯文本（不支持 `-s`） |

```bash
camscanner-cli pdf convert report.pdf --format word -s
camscanner-cli pdf convert invoice.pdf --format excel -s
camscanner-cli pdf convert paper.pdf --format md -s
camscanner-cli pdf convert doc.pdf --format txt -o plain.txt
```

## pdf to-images — PDF 逐页转图片

将 PDF 每一页渲染为 JPEG 图片。

```bash
# 散页输出到目录
camscanner-cli pdf to-images report.pdf -d ./pages
# 产物：pages/page_1.jpg, pages/page_2.jpg, ...

# 保存到云文档（多页图片文档）
camscanner-cli pdf to-images report.pdf -s
```

| 参数 | 说明 |
|------|------|
| `-d, --dir` | 输出目录（默认 `<文件名>_pages/`） |
| `-s` | 保存全部页到云文档 |

## pdf to-images-zip — PDF 转图片 ZIP

与 `to-images` 相同功能，但由服务端打包为单个 ZIP 文件。

```bash
camscanner-cli pdf to-images-zip report.pdf -o report_images.zip
```

> 注意：`to-images-zip` 不支持 `-s`（ZIP 不在云文档支持类型中）。

## pdf watermark — 添加水印

| 参数 | 说明 |
|------|------|
| `--text` | 水印文字（**必填**） |
| `--color` | 颜色，如 `#FF0000` |
| `--opacity` | 透明度 0-1 |
| `--size` | 字体大小 |

```bash
camscanner-cli pdf watermark contract.pdf --text "内部资料" -s
camscanner-cli pdf watermark doc.pdf --text "DRAFT" --color "#999999" --opacity 0.2 -s
```

## pdf remove-watermark — 去除水印

去除 PDF 中已有的水印。

```bash
camscanner-cli pdf remove-watermark document.pdf -s
camscanner-cli pdf remove-watermark doc.pdf -o clean.pdf
```

## 限制与注意事项

- **文件大小**：上传限制 40MB
- **页数限制**：水印操作最大 100 页
- **PDF 类型**：支持文字型和扫描型 PDF
- **加密 PDF**：不支持有密码保护的 PDF
