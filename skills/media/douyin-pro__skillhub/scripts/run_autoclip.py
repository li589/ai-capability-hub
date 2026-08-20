#!/usr/bin/env python3
"""
autoclip 包装脚本：把 autoclip 的输出归一化为 douyin-video-skill 标准的 clip_segments.json。

用法：
    python scripts/run_autoclip.py --input raw.mp4 --output clip_segments.json --top-k 5

前提：已按 skills/混剪/SKILL.md 装好 autoclip（默认在 ~/.workbuddy/skills/douyin-video-skill/autoclip）。
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_AUTOCLIP_DIR = Path(__file__).resolve().parent.parent / "autoclip"


def run(cmd, cwd=None, check=True):
    print(f"[RUN] {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def get_video_duration(video_path: str) -> float:
    """用 ffprobe 取视频总时长。"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())
    except Exception as e:
        print(f"[WARN] 无法获取视频时长: {e}", file=sys.stderr)
        return 0.0


def normalize(raw_path: Path, total_duration: float, top_k: int = None):
    """把 autoclip 原始输出转成标准 clip_segments.json。"""
    data = json.loads(raw_path.read_text(encoding="utf-8"))

    clips = []
    # autoclip 可能输出多种格式，这里兼容常见两种
    if isinstance(data, list):
        for i, item in enumerate(data):
            clips.append({
                "clip_id": i,
                "start": float(item.get("start", 0)),
                "end": float(item.get("end", 0)),
                "duration_sec": float(item.get("end", 0)) - float(item.get("start", 0)),
                "score": float(item.get("score", 0.8)),
                "description": item.get("description", ""),
            })
    elif isinstance(data, dict):
        raw_clips = data.get("clips", data.get("segments", data.get("highlights", [])))
        for i, item in enumerate(raw_clips):
            clips.append({
                "clip_id": i,
                "start": float(item.get("start", item.get("begin", 0))),
                "end": float(item.get("end", item.get("finish", 0))),
                "duration_sec": float(item.get("end", item.get("finish", 0))) -
                                float(item.get("start", item.get("begin", 0))),
                "score": float(item.get("score", item.get("importance", 0.8))),
                "description": item.get("description", item.get("text", "")),
            })
    else:
        raise ValueError(f"不支持的 autoclip 输出格式: {type(data)}")

    clips.sort(key=lambda x: x["score"], reverse=True)
    if top_k:
        clips = clips[:top_k]
    clips.sort(key=lambda x: x["start"])

    return {
        "source_video": str(raw_path.with_suffix("").name),
        "total_duration_sec": total_duration,
        "method": "autoclip",
        "clips": clips,
    }


def main():
    parser = argparse.ArgumentParser(description="autoclip 包装脚本")
    parser.add_argument("--input", required=True, help="原始视频路径")
    parser.add_argument("--output", default="clip_segments.json", help="标准输出 JSON 路径")
    parser.add_argument("--autoclip-dir", default=str(DEFAULT_AUTOCLIP_DIR), help="autoclip 仓库路径")
    parser.add_argument("--top-k", type=int, default=None, help="只保留 Top K 片段")
    args = parser.parse_args()

    autoclip_dir = Path(args.autoclip_dir)
    if not autoclip_dir.exists():
        print(
            f"[ERROR] 未找到 autoclip 目录: {autoclip_dir}\n"
            "请先安装：git clone https://github.com/zhouxiaoka/autoclip.git "
            f"{autoclip_dir}",
            file=sys.stderr,
        )
        return 1

    input_p = Path(args.input)
    if not input_p.exists():
        print(f"[ERROR] 输入视频不存在: {input_p}", file=sys.stderr)
        return 1

    # 调用 autoclip（尝试常见入口）
    raw_output = autoclip_dir / "autoclip_raw_output.json"
    candidates = [
        ["python", "main.py", "--input", str(input_p), "--output", str(raw_output)],
        ["python", "run.py", "--input", str(input_p), "--output", str(raw_output)],
        ["python", "autoclip.py", "--input", str(input_p), "--output", str(raw_output)],
    ]
    ok = False
    for cmd in candidates:
        try:
            run(cmd, cwd=autoclip_dir, check=True)
            if raw_output.exists():
                ok = True
                break
        except subprocess.CalledProcessError as e:
            print(f"[WARN] 命令失败: {' '.join(cmd)}\n{e.stderr}", file=sys.stderr)

    if not ok:
        print(
            "[ERROR] 无法调用 autoclip。请检查 autoclip 是否安装正确，\n"
            "或手动运行其 CLI 后，把输出 JSON 传给本脚本用 --from-raw 归一化。",
            file=sys.stderr,
        )
        return 1

    total_duration = get_video_duration(str(input_p))
    result = normalize(raw_output, total_duration, args.top_k)

    out_p = Path(args.output)
    out_p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 已生成标准 clip_segments: {out_p}（共 {len(result['clips'])} 段）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
