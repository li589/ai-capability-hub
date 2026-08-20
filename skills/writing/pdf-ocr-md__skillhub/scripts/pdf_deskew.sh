#!/bin/bash
# 倾斜校正 — 检测文本角度并自动旋转
# 用法: pdf_deskew input.jpg -o output.jpg
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python "$SCRIPT_DIR/pdf_preprocess.py" "$@" --deskew
