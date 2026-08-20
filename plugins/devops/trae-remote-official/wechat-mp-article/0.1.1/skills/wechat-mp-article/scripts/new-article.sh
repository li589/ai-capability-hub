#!/bin/bash
set -euo pipefail

# new-article.sh — 创建公众号推文工作目录
# Usage: bash <skill-dir>/scripts/new-article.sh <slug> <work-dir>

if [ $# -lt 2 ]; then
  echo "Usage: bash $0 <slug> <work-dir>"
  echo "  <slug>      推文 slug (e.g. summer-thinking-2026)"
  echo "  <work-dir>  工作目录根路径 (建议 /workspace)"
  exit 1
fi

SLUG="$1"
WORK_DIR="$2"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

TARGET_DIR="${WORK_DIR}/${SLUG}"

if [ -d "$TARGET_DIR" ]; then
  echo "[ERROR] 目录已存在: $TARGET_DIR"
  exit 1
fi

mkdir -p "${TARGET_DIR}/assets"

cp "${SKILL_DIR}/templates/wechat-article.html" "${TARGET_DIR}/index.html"

echo "✓ 推文目录已创建: ${TARGET_DIR}"
echo ""
echo "  ${TARGET_DIR}/"
echo "  ├── index.html    (公众号推文预览)"
echo "  └── assets/       (图片/视频统一存放)"
echo ""
echo "下一步："
echo "  bash ${SKILL_DIR}/scripts/inject-content.sh ${TARGET_DIR} \\"
echo "    --title \"标题\" \\"
echo "    --body-file body.html"
