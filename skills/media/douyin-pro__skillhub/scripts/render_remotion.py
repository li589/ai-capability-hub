#!/usr/bin/env python3
"""
Remotion 渲染编排脚本（douyin-video-skill 下游通道）。
把 image_map + audio + shot_plan 喂给 templates/remotion，输出成片 MP4。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTION_DIR = ROOT / "templates" / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"


def run(cmd, cwd=None, check=True):
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def copy_assets(image_map: dict, audio_path: str):
    """把图片和音频复制到 Remotion public/ 目录，返回相对文件名列表。"""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    # 音频
    audio_ext = Path(audio_path).suffix or ".wav"
    dest_audio = PUBLIC_DIR / f"audio{audio_ext}"
    shutil.copy2(audio_path, dest_audio)

    # 图片
    image_files = {}
    for beat, src in image_map.items():
        src_p = Path(src)
        if not src_p.exists():
            print(f"[WARN] 图片不存在，跳过: {src}", file=sys.stderr)
            continue
        dest_name = f"beat_{beat}{src_p.suffix}"
        shutil.copy2(src_p, PUBLIC_DIR / dest_name)
        image_files[str(beat)] = dest_name
    return "audio" + audio_ext, image_files


def build_props(shot_plan: list, audio_file: str, image_files: dict,
                total_duration: float, aspect_ratio: str, ai_label_config: dict, title: str = None):
    shots = []
    for beat in shot_plan:
        b = beat["beat"]
        shots.append({
            "beat": b,
            "visual_prompt": beat.get("visual_prompt", ""),
            "source": beat.get("source", "ai_gen"),
            "duration_sec": beat.get("duration_sec", 5.0),
            "image": image_files.get(str(b)),
            "caption": beat.get("caption", ""),
        })
    return {
        "shots": shots,
        "audioFile": audio_file,
        "totalDurationSec": total_duration,
        "aspectRatio": aspect_ratio,
        "aiLabelConfig": ai_label_config or {"mode": "overlay", "duration_sec": 3, "text": "本视频含 AI 生成内容"},
        "title": title or "",
    }


def ensure_deps():
    node_modules = REMOTION_DIR / "node_modules"
    if not node_modules.exists():
        print("[INFO] Remotion 依赖缺失，执行 npm install...")
        run(["npm", "install"], cwd=REMOTION_DIR)


def main():
    parser = argparse.ArgumentParser(description="Remotion 渲染编排")
    parser.add_argument("--shot-plan", required=True, help="shot_plan JSON 文件路径")
    parser.add_argument("--image-map", required=True, help="image_map JSON 文件路径（beat_index -> image_path）")
    parser.add_argument("--audio", required=True, help="48k wav 音频路径")
    parser.add_argument("--output", default="out.mp4", help="输出 MP4 路径")
    parser.add_argument("--aspect-ratio", default="9:16", choices=["9:16", "1:1", "16:9"])
    parser.add_argument("--ai-label-duration", type=int, default=3, help="AI 标识显示秒数")
    parser.add_argument("--ai-label-text", default="本视频含 AI 生成内容")
    parser.add_argument("--title", default=None, help="片头标题")
    args = parser.parse_args()

    shot_plan = json.loads(Path(args.shot_plan).read_text(encoding="utf-8"))
    image_map = json.loads(Path(args.image_map).read_text(encoding="utf-8"))

    # 计算总时长
    total_duration = sum(b.get("duration_sec", 5.0) for b in shot_plan)

    # 复制素材
    audio_file, image_files = copy_assets(image_map, args.audio)

    # 生成 props.json
    props = build_props(
        shot_plan, audio_file, image_files,
        total_duration, args.aspect_ratio,
        {"mode": "overlay", "duration_sec": args.ai_label_duration, "text": args.ai_label_text},
        args.title,
    )
    props_path = REMOTION_DIR / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

    # 安装依赖并渲染
    ensure_deps()
    out_path = (Path(args.output).resolve() if args.output else REMOTION_DIR / "out.mp4")
    run([
        "npx", "remotion", "render", "src/index.tsx", "DouyinVideo", str(out_path),
        f"--props=props.json",
    ], cwd=REMOTION_DIR)

    print(f"[OK] 成片已输出: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
