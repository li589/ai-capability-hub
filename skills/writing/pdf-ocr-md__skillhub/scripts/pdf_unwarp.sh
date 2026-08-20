#!/bin/bash
# 文档展平 — 透视变换校正弯曲/变形的文档照片
# 用法: pdf_unwarp input.jpg -o output.jpg
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python "$SCRIPT_DIR/pdf_preprocess.py" "$@" --unwarp
