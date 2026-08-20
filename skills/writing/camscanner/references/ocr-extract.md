# OCR 识别与内容提取工作流

> **前置阅读**：`references/image-processing.md`（ocr/convert/merge-text 参数）、`references/pdf-processing.md`（pdf convert 参数）

## 场景

用户需要从图片或 PDF 中提取文字内容。

## 决策树

| 用户需求 | 最佳方案 | 说明 |
|----------|----------|------|
| 只要纯文本 | `image ocr` | 输出到 stdout，不支持 `-s` |
| 保留格式（标题、列表） | `image convert --format md -s` | Markdown 格式 |
| 多页文档提取为一份 | `image merge-text --format md` | 最多 100 张 |
| PDF 提取为 Markdown | `pdf convert --format md -s` | |
| 需要可编辑 Word | `image convert --format word -s` | 保留排版 |

## 方案选择逻辑

1. **输入是 PDF？** → `pdf convert --format xx`
2. **输入是多张图片？** → `image merge-text`（纯文本）或 `image merge-word`（保留排版）
3. **输入是单张图片？** → 按输出格式需求选择 `image ocr` / `image convert`

## 多页文档衔接

多张图片需要合并为一份文档时：
- 纯文本：`image merge-text` → stdout 或 `-o` 输出
- 带格式文档：`image merge-word -s` 直接保存为云文档
