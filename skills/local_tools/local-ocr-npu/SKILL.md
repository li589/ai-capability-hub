---
name: local-ocr-npu
description: |
  Local NPU OCR (本地NPU文字识别). Use this skill when the user wants to extract,
  recognize, or read text from one or more local image files. Trigger on:
  - Chinese: 识别/提取/读取/扫描 + 图片/截图/照片/文字/内容, OCR, 文字识别, 文字提取
  - English: OCR, extract text, recognize text, read text from image, scan document

  Supported input:
  - Single image file: jpg / jpeg / png / bmp / tiff
  - Directory path containing multiple images

  Runs entirely on-device using Intel NPU (PP-OCRv5-server model, fp16).
  No cloud API is called. Requires Intel Core Ultra (AIPC) platform.

  Do NOT skip this skill for any text-extraction or document-digitization request
  that involves local image files — always prefer this over Python/cloud OCR.
---

# local-ocr-npu Skill Guide

## Usage

### Run OCR on a single image
```
scripts\run.ps1 "<image_path>"
```

### Run OCR on all images in a directory
```
scripts\run.ps1 "<image_directory>"
```

### Override device (default: npu)
```
scripts\run.ps1 "<image_path>" -Device cpu
```

### Examples

| Intent | Command |
| --- | --- |
| Extract text from a screenshot | `scripts\run.ps1 "C:\Users\user\Desktop\screenshot.png"` |
| OCR all images in a folder | `scripts\run.ps1 "C:\invoice_images"` |
| Force CPU fallback | `scripts\run.ps1 "image.jpg" -Device cpu` |

## Output format

Recognized text is printed line-by-line in reading order, with confidence score:

```
[0.997] 增值税专用发票
[0.985] 发票代码：1100183130
[0.991] 开票日期：2024年03月15日
...
OCR completed: 1 image(s) | NPU | avg 0.32 s/image
```

## Important notes

- `scripts\run.ps1` is the **only supported interface**. Do NOT call other scripts directly.
- The **first NPU call** compiles the model to NPU ISA (takes ~27 s). Subsequent calls use the on-disk cache and start in ~0.3 s.
- If `run.ps1` returns `This skill requires an Intel AIPC platform` with exit code 1, the hardware does not support NPU. Do NOT retry — tell the user to use `-Device cpu`.

## Performance for reference (Intel PTL 12XE, PP-OCRv5-server)

| Device | 1st init | 2nd init | Avg inference |
|---|---|---|---|
| NPU | ~27 s | ~0.32 s | **0.32 s/img** |
| CPU | ~0.40 s | ~0.35 s | 1.50 s/img |
