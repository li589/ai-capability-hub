#!/usr/bin/env bash
# 爆款视频 designkitwebapi（全球化）执行入口
# 用法:
#   bash run_viral_video.sh init_cfg --input-json '{"market":"US"}'
#   bash run_viral_video.sh preview  --input-json '{"mode":"generate","market":"US","script_types":[{"type":"ugc","count":2}]}'
#   bash run_viral_video.sh submit   --input-json '{"mode":"generate","market":"US","product_info":"...","product_images":["..."],"script_types":[{"type":"ugc","count":2}],"aspect_ratio":"9:16"}'
#   bash run_viral_video.sh submit   --input-json '{"mode":"replica","market":"US","product_images":["..."],"reference_video":"https://...","total_count":2}'
#   bash run_viral_video.sh query    --input-json '{"batch_id":"...","max_wait_sec":120}'
#   bash run_viral_video.sh download --input-json '{"batch_id":"..."}'
#   bash run_viral_video.sh cancel   --input-json '{"batch_id":"..."}'
#   bash run_viral_video.sh redo     --input-json '{"task_ids":["..."]}'
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/viral_video.py" "$@"
