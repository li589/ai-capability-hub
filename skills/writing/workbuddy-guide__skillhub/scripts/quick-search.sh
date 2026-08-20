#!/bin/bash
# 在知识库所有参考文件中搜索关键词
# 用法: quick-search.sh <关键词>
KEYWORD="${1:-}"
if [ -z "$KEYWORD" ]; then
    echo "用法: quick-search.sh <关键词>"
    exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REFERENCES_DIR="$SCRIPT_DIR/../references"
echo "=== 在知识库中搜索: $KEYWORD ==="
grep -n -C 2 "$KEYWORD" "$REFERENCES_DIR"/*.md 2>/dev/null || echo "未找到匹配结果"
