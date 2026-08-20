#!/bin/bash
set -euo pipefail

# new-post.sh — 创建小红书图文笔记目录结构
# Usage: bash <skill-dir>/scripts/new-post.sh <report-name> <work-dir>

if [ $# -lt 2 ]; then
  echo "Usage: bash $0 <report-name> <work-dir>"
  echo "  <report-name>  笔记 slug (e.g. summer-art-2024)"
  echo "  <work-dir>     工作目录根路径"
  exit 1
fi

REPORT_NAME="$1"
WORK_DIR="$2"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

TARGET_DIR="${WORK_DIR}/${REPORT_NAME}"

if [ -d "$TARGET_DIR" ]; then
  echo "[ERROR] 目录已存在: $TARGET_DIR"
  exit 1
fi

# 创建目录结构
mkdir -p "${TARGET_DIR}/post"
mkdir -p "${TARGET_DIR}/images"

# 复制模板
cp "${SKILL_DIR}/templates/phone-preview.html" "${TARGET_DIR}/index.html"
cp "${SKILL_DIR}/templates/post/rednote-post.html" "${TARGET_DIR}/post/rednote-post.html"

echo "✓ 笔记目录已创建: ${TARGET_DIR}。目录下所有内容无需阅读，与任务无关" 
echo ""
echo "  ${TARGET_DIR}/"
echo "  ├── index.html              (主预览页 )"
echo "  ├── post/"
echo "  │   └── rednote-post.html   (内容页)"
echo "  └── images/"
echo "      └── (将图片放在此目录)"
echo ""
echo "下一步: 使用 inject-content.sh 注入内容"
echo "  bash ${SKILL_DIR}/scripts/inject-content.sh ${TARGET_DIR} \\"
echo "    --title \"标题\" \\"
echo "    --body \"正文内容\" \\"
echo "    --tags \"标签1,标签2\" \\"
echo "    --images \"img1.jpg,img2.jpg\""
