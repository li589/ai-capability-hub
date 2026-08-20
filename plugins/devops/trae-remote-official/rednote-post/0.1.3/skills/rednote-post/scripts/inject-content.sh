#!/bin/bash
set -euo pipefail

# inject-content.sh — 向小红书笔记注入内容并进行校验
# Usage: bash inject-content.sh <post-dir> --title "..." --body "..." --tags "t1,t2,..." --images "i1.jpg,i2.jpg,..."
#
# 校验规则:
#   - 标题: 最多 20 字符（每个字母/数字/汉字/符号均计 1 字符）
#   - 正文: 最多 2000 字符，超出将生成文本长图追加到图片列表末尾
#   - 标签: 最多 10 个，未带 # 前缀自动补上
#   - 图片: 路径相对于 <post-dir>/images/，所有图片必须存在于该目录

usage() {
  echo "Usage: bash $0 <post-dir> --title \"...\" --body \"...\" --tags \"t1,t2,...\" --images \"i1.jpg,i2.jpg,...\""
  exit 1
}

if [ $# -lt 2 ]; then usage; fi

POST_DIR="$1"
shift

TITLE=""
BODY=""
TAGS_RAW=""
IMAGES_RAW=""

while [ $# -gt 0 ]; do
  case "$1" in
    --title)  TITLE="$2"; shift 2 ;;
    --body)   BODY="$2"; shift 2 ;;
    --tags)   TAGS_RAW="$2"; shift 2 ;;
    --images) IMAGES_RAW="$2"; shift 2 ;;
    *) echo "[ERROR] 未知参数: $1"; usage ;;
  esac
done

HTML_FILE="${POST_DIR}/post/rednote-post.html"
IMAGES_DIR="${POST_DIR}/images"

if [ ! -f "$HTML_FILE" ]; then
  echo "[ERROR] 内容文件不存在: $HTML_FILE"
  echo "请先运行 new-post.sh 创建目录结构"
  exit 1
fi

# === 校验标题 ===
TITLE_LEN=$(printf '%s' "$TITLE" | wc -m | tr -d ' ')
if [ "$TITLE_LEN" -gt 20 ]; then
  echo "[ERROR] 标题超出限制: ${TITLE_LEN}/20 字符"
  echo "  标题内容: $TITLE"
  exit 1
fi
if [ "$TITLE_LEN" -eq 0 ]; then
  echo "[WARN] 标题为空"
fi

# === 校验并处理正文 ===
BODY_LEN=$(printf '%s' "$BODY" | wc -m | tr -d ' ')
OVERFLOW_IMAGE=""

if [ "$BODY_LEN" -gt 2000 ]; then
  echo "[INFO] 正文超出 2000 字符 (${BODY_LEN})，将生成长图..."

  OVERFLOW_IMAGE="overflow-text.png"
  OVERFLOW_PATH="${IMAGES_DIR}/${OVERFLOW_IMAGE}"

  if command -v convert &>/dev/null; then
    WRAPPED_BODY=$(printf '%s' "$BODY" | fold -w 30 -s)
    convert -size 1080x -background white -fill '#333333' \
      -font "PingFang-SC-Regular" -pointsize 36 \
      -gravity NorthWest -splice 60x60 \
      caption:"$WRAPPED_BODY" \
      "$OVERFLOW_PATH" 2>/dev/null || {
        convert -size 1080x2400 xc:white \
          -fill '#333333' -pointsize 32 \
          -annotate +60+60 "$BODY" \
          "$OVERFLOW_PATH" 2>/dev/null || {
            echo "[WARN] ImageMagick 渲染失败，将截断正文为 2000 字符"
            OVERFLOW_IMAGE=""
          }
      }
  else
    echo "[WARN] 未安装 ImageMagick (convert)，无法生成长图，正文将被截断为 2000 字符"
  fi

  BODY=$(printf '%s' "$BODY" | cut -c1-2000)
  BODY="${BODY}..."
fi

# === 校验并处理标签 ===
IFS=',' read -ra TAG_ARRAY <<< "$TAGS_RAW"
TAGS_JSON="["
TAG_COUNT=0

for tag in "${TAG_ARRAY[@]}"; do
  tag=$(echo "$tag" | xargs)  # trim whitespace
  [ -z "$tag" ] && continue

  TAG_COUNT=$((TAG_COUNT + 1))
  if [ "$TAG_COUNT" -gt 10 ]; then
    echo "[WARN] 标签超出 10 个限制，已截断"
    break
  fi

  # 自动补 # 前缀
  if [[ "$tag" != \#* ]]; then
    tag="#${tag}"
  fi

  if [ "$TAG_COUNT" -gt 1 ]; then
    TAGS_JSON="${TAGS_JSON},"
  fi
  TAGS_JSON="${TAGS_JSON}\"${tag}\""
done

TAGS_JSON="${TAGS_JSON}]"

# === 校验并处理图片 ===
IFS=',' read -ra IMG_ARRAY <<< "$IMAGES_RAW"
IMAGES_JSON="["
IMG_COUNT=0

for img in "${IMG_ARRAY[@]}"; do
  img=$(echo "$img" | xargs)  # trim whitespace
  [ -z "$img" ] && continue

  IMG_COUNT=$((IMG_COUNT + 1))

  if [ ! -f "${IMAGES_DIR}/${img}" ]; then
    echo "[WARN] 图片不存在: ${IMAGES_DIR}/${img}"
  fi

  if [ "$IMG_COUNT" -gt 1 ]; then
    IMAGES_JSON="${IMAGES_JSON},"
  fi
  IMAGES_JSON="${IMAGES_JSON}\"../images/${img}\""
done

# 如果有溢出长图，追加到图片列表末尾
if [ -n "$OVERFLOW_IMAGE" ] && [ -f "${IMAGES_DIR}/${OVERFLOW_IMAGE}" ]; then
  if [ "$IMG_COUNT" -gt 0 ]; then
    IMAGES_JSON="${IMAGES_JSON},"
  fi
  IMAGES_JSON="${IMAGES_JSON}\"../images/${OVERFLOW_IMAGE}\""
  IMG_COUNT=$((IMG_COUNT + 1))
fi

IMAGES_JSON="${IMAGES_JSON}]"

# === 转义正文中的特殊字符用于 JSON (macOS 兼容) ===
BODY_ESCAPED=$(printf '%s' "$BODY" | perl -pe 's/\\/\\\\/g; s/"/\\"/g; s/\n/\\n/g')
TITLE_ESCAPED=$(printf '%s' "$TITLE" | perl -pe 's/\\/\\\\/g; s/"/\\"/g')

# === 生成 DATA 块写入临时文件 ===
DATA_TEMP=$(mktemp)
cat > "$DATA_TEMP" << DATAEOF
const DATA = {
  images: ${IMAGES_JSON},
  title: "${TITLE_ESCAPED}",
  body: "${BODY_ESCAPED}",
  tags: ${TAGS_JSON}
};
DATAEOF

# === 替换 HTML 中的 DATA 块 ===
TEMP_FILE=$(mktemp)
{
  in_data=0
  while IFS= read -r line; do
    if [[ "$line" == *"<!-- DATA SCHEMA BEGIN -->"* ]]; then
      echo "<!-- DATA SCHEMA BEGIN -->"
      echo "<script>"
      cat "$DATA_TEMP"
      echo "</script>"
      in_data=1
      continue
    fi
    if [[ "$line" == *"<!-- DATA SCHEMA END -->"* ]]; then
      echo "<!-- DATA SCHEMA END -->"
      in_data=0
      continue
    fi
    if [ "$in_data" -eq 0 ]; then
      echo "$line"
    fi
  done < "$HTML_FILE"
} > "$TEMP_FILE"

mv "$TEMP_FILE" "$HTML_FILE"
rm -f "$DATA_TEMP"

# === 输出摘要 ===
echo ""
echo "═══════════════════════════════════════"
echo "  ✓ 内容注入完成"
echo "═══════════════════════════════════════"
echo "  标题: ${TITLE} (${TITLE_LEN}/20)"
echo "  正文: ${BODY_LEN} 字符"
[ "$BODY_LEN" -gt 2000 ] && echo "        [已截断，长图已生成]"
echo "  标签: ${TAG_COUNT} 个"
echo "  图片: ${IMG_COUNT} 张"
echo ""
echo "═══════════════════════════════════════"
