#!/bin/bash
set -euo pipefail

# inject-content.sh — 往公众号推文模板里塞「标题 + 时间 + 正文 HTML」
#
# 设计原则：
#   模板 DATA 块里的 account / author / location / is_original 等都是写死的默认值，
#   脚本不碰它们。脚本只负责注入这三样：
#     ① title      推文标题
#     ② date       发布时间（默认今天当前时间）
#     ③ body_html  正文 HTML 片段（公众号正文本质就是 HTML）
#
# Usage:
#   bash inject-content.sh <post-dir> --title "标题" --body-file body.html [--date "..."]
#
#   --title TITLE       推文标题（必填）
#   --body-file FILE    正文 HTML 文件（必填，直接原样注入）
#   --date TEXT         发布时间，默认今日当前时间 YYYY年M月D日 HH:MM

usage() {
  cat <<'EOF'
Usage: bash inject-content.sh <post-dir> --title "标题" --body-file body.html [--date "..."]

  --title TITLE       推文标题（必填）
  --body-file FILE    正文 HTML 文件（必填，原样注入，不做任何转换）
  --date TEXT         发布时间，默认今日当前时间

说明：公众号名 / 作者 / 地点 / 原创徽章等都是模板写死的默认值，脚本不修改。
EOF
  exit 1
}

if [ $# -lt 2 ]; then usage; fi

POST_DIR="$1"
shift

TITLE=""
BODY_FILE=""
DATE_TEXT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --title)     TITLE="$2"; shift 2 ;;
    --body-file) BODY_FILE="$2"; shift 2 ;;
    --date)      DATE_TEXT="$2"; shift 2 ;;
    *) echo "[ERROR] 未知参数: $1"; usage ;;
  esac
done

HTML_FILE="${POST_DIR}/index.html"

if [ ! -f "$HTML_FILE" ]; then
  echo "[ERROR] 目标文件不存在: $HTML_FILE"
  echo "请先运行 new-article.sh 创建目录结构"
  exit 1
fi
if [ -z "$TITLE" ]; then
  echo "[ERROR] --title 必填"; exit 1
fi
if [ -z "$BODY_FILE" ]; then
  echo "[ERROR] --body-file 必填（正文 HTML 文件）"; exit 1
fi
if [ ! -f "$BODY_FILE" ]; then
  echo "[ERROR] 正文文件不存在: $BODY_FILE"; exit 1
fi

# 默认时间：今天当前时间，如 "2026年7月28日 14:26"
if [ -z "$DATE_TEXT" ]; then
  DATE_TEXT="$(date '+%Y年%-m月%-d日 %H:%M')"
fi

export WMP_TITLE="$TITLE"
export WMP_BODY_FILE="$BODY_FILE"
export WMP_DATE="$DATE_TEXT"
export WMP_HTML_FILE="$HTML_FILE"

python3 - <<'PYEOF'
import json, os, re, sys

html_file = os.environ["WMP_HTML_FILE"]
title     = os.environ["WMP_TITLE"]
date_text = os.environ["WMP_DATE"]
with open(os.environ["WMP_BODY_FILE"], "r", encoding="utf-8") as f:
    body_html = f.read()

with open(html_file, "r", encoding="utf-8") as f:
    html_src = f.read()

# 定位模板里的 DATA 块，解析出现有 JSON（保留 account/location 等写死默认值）
m = re.search(
    r'<script id="post-data" type="application/json">\s*(\{.*?\})\s*</script>',
    html_src, re.S
)
if not m:
    print("[ERROR] 未在模板中找到 post-data JSON 块")
    sys.exit(1)

data = json.loads(m.group(1))

# 只更新这三样，其余字段原样保留
data["title"]     = title
data["date"]      = date_text
data["body_html"] = body_html

new_json = json.dumps(data, ensure_ascii=False, indent=2)
new_script = (
    '<script id="post-data" type="application/json">\n'
    + new_json + '\n</script>'
)

html_out = (
    html_src[:m.start()] + new_script + html_src[m.end():]
)
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_out)

print("✓ 已注入：标题 / 时间 / 正文 HTML")
print(f"  标题     : {title}")
print(f"  时间     : {date_text}")
print(f"  正文长度 : {len(body_html)} 字符 (HTML)")
print(f"  公众号   : {data.get('account')} (模板默认，未改)")
print(f"  地点     : {data.get('location')} (模板默认，未改)")
PYEOF

echo ""
echo "═══════════════════════════════════════"
echo "  ✓ 公众号推文预览已生成"
echo "  文件: ${HTML_FILE}"
echo "═══════════════════════════════════════"
