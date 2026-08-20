#!/usr/bin/env bash
# 将 42 篇知识库原文上传到腾讯云 COS（公开可读），供 Skill 按需拉取。
#
# 前置准备：
#   pip install coscmd
#   coscmd config -a <SecretId> -s <SecretKey> -b <bucket-name> -r <region>
#   （bucket-name 形如 my-kb-1250000000；region 如 ap-guangzhou）
#
# 用法：
#   bash scripts/upload_to_cos.sh
#
# 完成后，kb-index.md 中的 COS_BASE_URL 已替换为：
#   https://marketing-compliance-review-1300122096.cos.ap-guangzhou.myqcloud.com/kb/
set -e

SRC="/tmp/skill_cos_upload"          # 42 个 .md 所在目录（扁平）
BUCKET_DIR="kb"                      # COS 桶内目录名

if ! command -v coscmd >/dev/null 2>&1; then
  echo "请先安装 coscmd： pip install coscmd" >&2
  exit 1
fi

echo "上传 $SRC 下所有 .md 到 COS 桶内 $BUCKET_DIR/ ..."
coscmd upload -r "$SRC" "$BUCKET_DIR/"

echo
echo "上传完成。COS_BASE_URL 已写入："
echo "  https://marketing-compliance-review-1300122096.cos.ap-guangzhou.myqcloud.com/$BUCKET_DIR/"
echo "并确保该目录设为公有读（或配置免签下载），否则 WebFetch / fetch_kb.py 无法访问。"
