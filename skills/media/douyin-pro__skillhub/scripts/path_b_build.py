#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path B 全链路串联脚本 · 抖音短视频生产专家团
============================================================
把"优化好的脚本文字"变成带 AI 配音 + 字幕的竖屏 MP4，全程零云费:

    脚本文本 ──▶ ① 分段            (按空行 / JSON 场景)
              ──▶ ② edge-tts 配音   (免费, 微软接口) → 每段 .mp3 + .vtt
              ──▶ ③ 生成合成 HTML    (HyperFrames 格式, 时序对齐配音时长)
              ──▶ ④ HyperFrames 渲染 → 静帧视频 silent.mp4 (画面)
              ──▶ ⑤ ffmpeg 合成      → 拼音频 + 烧字幕 → 最终 final.mp4

依赖 (先跑 install_path_b_deps.py 装好):
    - Python >= 3.10
    - edge-tts          (pip install edge-tts)
    - Node.js >= 22     (https://nodejs.org)
    - hyperframes       (npm install -g hyperframes)
    - ffmpeg + ffprobe  (https://ffmpeg.org)
    - Chrome            (npx hyperframes browser ensure)

用法:
    python path_b_build.py --input script.txt --output final.mp4
    python path_b_build.py --input scenes.json --voice zh-CN-YunxiNeural
    python path_b_build.py --doctor            # 只做环境自检
    python path_b_build.py --input script.txt --skip-render   # 只出音频+HTML, 不渲染

输入格式:
    A) 纯文本/Markdown: 用空行分段, 每段 = 一个分镜。段首短行(<=18字且非标点句)
       自动当标题, 其余当正文。
    B) JSON: [{"title": "...", "body": "...", "voice": "..."}, ...]
       或    [{"text": "整段旁白"}, ...]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import timedelta


# ------------------------- 工具函数 -------------------------
def log(msg: str):
    print(f"[path_b] {msg}", flush=True)


def run(cmd, **kw):
    """运行命令, 返回 CompletedProcess; 出错时按 check 决定抛不抛。

    ⚠️ 跨平台关键：Windows 下 npx/npm/hyperframes/ffmpeg 有的是 .cmd 包装
    (npx/npm/hyperframes) 有的是 .exe (ffmpeg/ffprobe)。统一用 list 传入时，
    原生 Windows 的 CreateProcess 无法直接启动 .cmd，会抛 FileNotFoundError/
    WinError 193。所以 Windows 下必须 shell=True + list2cmdline 走 cmd.exe。
    （Git Bash 里能直接跑 npx 是 bash 自己解析了；用户用 python 在
    cmd/PowerShell 跑脚本时若不处理就会崩溃。）
    """
    if isinstance(cmd, str):
        cmd_list = cmd.split()
        display = cmd
    else:
        cmd_list = [str(c) for c in cmd]
        display = " ".join(cmd_list)
    log("▶ " + display)
    if sys.platform == "win32":
        s = subprocess.list2cmdline(cmd_list)
        return subprocess.run(s, shell=True, **kw)
    return subprocess.run(cmd_list, **kw)


def which(tool: str) -> str | None:
    return shutil.which(tool) or shutil.which(tool + ".exe")


def ffprobe_duration(path: str) -> float | None:
    """用 ffprobe 取音频时长(秒); 取不到返回 None。"""
    ff = which("ffprobe")
    if not ff:
        return None
    try:
        out = subprocess.check_output(
            [ff, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return float(out)
    except Exception:
        return None


def estimate_duration(text: str) -> float:
    """没有 ffprobe 时的兜底估算: 中文约 4.5 字/秒, 英文约 2.5 词/秒。"""
    cn = len(re.findall(r"[一-鿿]", text))
    en = len(re.findall(r"[A-Za-z]+", text))
    secs = cn / 4.5 + en / 2.5
    return max(1.5, secs + 0.6)  # 至少 1.5s, 留余量


def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def ffmpeg_sub_path(p: str) -> str:
    """把任意路径转成 ffmpeg subtitles 过滤器里安全的写法。

    ffmpeg 的 filtergraph 里 ':' 是选项分隔符、'\\' 是转义符、空格等需转义；
    Windows 用户的临时目录常带空格(如 'C:\\Users\\John Doe\\...')，直接塞进去
    渲染会报找不到字幕文件。这里统一: 反斜杠→正斜杠, 特殊字符转义, 整段单引号包住。
    """
    p = p.replace("\\", "/")
    p = p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return "'" + p + "'"


def vtt_time(secs: float) -> str:
    td = timedelta(seconds=secs)
    h, rem = divmod(td.seconds + td.days * 86400, 3600)
    m, s = divmod(rem, 60)
    ms = int(td.microseconds / 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def shift_vtt(path: str, offset: float) -> str:
    """读取一个 .vtt, 把所有时间点整体后移 offset 秒, 返回合并后的文本块。"""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    blocks, cur = [], []
    for line in raw.splitlines():
        if line.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)
    out = []
    for b in blocks:
        # 找到含 '-->' 的时间轴行
        new_b = []
        for line in b:
            m = re.match(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})", line)
            if m:
                t1 = timedelta(hours=int(m.group(1)[:2]), minutes=int(m.group(1)[3:5]),
                               seconds=int(m.group(1)[6:8]), microseconds=int(m.group(1)[9:]) * 1000)
                t2 = timedelta(hours=int(m.group(2)[:2]), minutes=int(m.group(2)[3:5]),
                               seconds=int(m.group(2)[6:8]), microseconds=int(m.group(2)[9:]) * 1000)
                line = f"{vtt_time(t1.total_seconds() + offset)} --> {vtt_time(t2.total_seconds() + offset)}"
            new_b.append(line)
        if new_b:
            out.append("\n".join(new_b))
    return "\n\n".join(out)


# ------------------------- 场景解析 -------------------------
def parse_input(text: str):
    """返回场景列表: [{"title": str|None, "body": str, "voice": str|None}]"""
    text = text.strip()
    if not text:
        return []
    # 尝试 JSON
    if text.lstrip().startswith("["):
        try:
            data = json.loads(text)
            scenes = []
            for item in data:
                if "text" in item:
                    scenes.append({"title": item.get("title"), "body": item["text"],
                                   "voice": item.get("voice")})
                else:
                    scenes.append({"title": item.get("title"), "body": item.get("body", ""),
                                   "voice": item.get("voice")})
            return scenes
        except json.JSONDecodeError:
            pass  # 不是合法 JSON, 当纯文本处理

    scenes = []
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        lines = [l.rstrip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        # 段首短行当标题
        title = None
        if len(lines) > 1 and len(lines[0]) <= 18 and not lines[0].endswith(("。", "，", "、", "：")):
            title = lines[0]
            body = "\n".join(lines[1:])
        else:
            body = "\n".join(lines)
        scenes.append({"title": title, "body": body, "voice": None})
    return scenes


# ------------------------- 合成 HTML 生成 -------------------------
HTML_HEAD = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      /* 中文系统字体: 用 src: local() 声明, 渲染器即可识别(无需字体文件) */
      @font-face {{ font-family: "PingFang SC"; src: local("PingFang SC"); }}
      @font-face {{ font-family: "Microsoft YaHei"; src: local("Microsoft YaHei"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{
        margin: 0; width: {w}px; height: {h}px; overflow: hidden;
        background: radial-gradient(circle at 30% 20%, #1b2a4a 0%, #0b1020 60%, #05070f 100%);
      }}
      body {{ font-family: "PingFang SC", "Microsoft YaHei", "Inter", sans-serif; color: #f5f7ff; }}
      #root {{ width: {w}px; height: {h}px; position: relative; }}
      .clip {{
        position: absolute; inset: 0; display: flex; flex-direction: column;
        justify-content: center; padding: {pad}px; gap: 40px;
      }}
      .kicker {{ font-size: 38px; letter-spacing: 5px; color: #6ea8ff; font-weight: 700; }}
      h1 {{ font-size: {h1}px; line-height: 1.2; font-weight: 800; }}
      p  {{ font-size: {p}px; line-height: 1.5; color: #c7d2e8; white-space: pre-line; }}
      .accent {{ color: #ffd166; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0"
         data-duration="{total:.1f}" data-width="{w}" data-height="{h}">
"""

CLIP_TPL = """      <div id="{cid}" class="clip"
           data-start="{start:.1f}" data-duration="{dur:.1f}" data-track-index="1">
        {inner}
      </div>
"""

HTML_TAIL = """    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{tweens}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def build_html(scenes, durations, w=1080, h=1920):
    pad = int(w * 0.11)
    h1 = int(h * 0.05)
    p = int(h * 0.027)
    total = sum(durations)
    clips, tweens, start = [], [], 0.0
    for i, (sc, dur) in enumerate(zip(scenes, durations), 1):
        cid = f"scene-{i}"
        inner = ""
        if sc["title"]:
            inner += f'        <div class="kicker">Path B</div>\n        <h1>{html_escape(sc["title"])}</h1>\n'
        body = sc["body"].strip()
        # 标题已单独显示时, 正文缩进
        if sc["title"]:
            inner += f'        <p>{html_escape(body)}</p>'
        else:
            inner += f'        <h1>{html_escape(body)}</h1>'
        clips.append(CLIP_TPL.format(cid=cid, start=start, dur=dur, inner=inner))
        tweens.append(f'      tl.from("#{cid}", {{ opacity: 0, y: 80, duration: 0.6 }}, {start:.1f});')
        start += dur
    html = (HTML_HEAD.format(w=w, h=h, pad=pad, h1=h1, p=p, total=total)
            + "\n".join(clips) + "\n" + HTML_TAIL.format(tweens="\n".join(tweens)))
    return html


# ------------------------- 环境自检 -------------------------
def doctor():
    ok = True
    log("=== 环境自检 (doctor) ===")

    node = which("node")
    if node:
        ver = subprocess.check_output([node, "--version"]).decode().strip()
        maj = int(ver.lstrip("v").split(".")[0])
        if maj >= 22:
            log(f"✅ Node.js {ver} (>=22 满足)")
        else:
            log(f"❌ Node.js {ver} 过低, 需要 >=22"); ok = False
    else:
        log("❌ 未找到 node, 请安装 https://nodejs.org (>=22)"); ok = False

    hf = which("hyperframes") or (which("npx") is not None)
    if hf:
        log("✅ hyperframes 可经 npx 调用 (npm install -g hyperframes 后更佳)")
    else:
        log("❌ 未找到 npx/hyperframes, 请安装 Node.js + npm"); ok = False

    ff = which("ffmpeg")
    if ff:
        log("✅ ffmpeg 已安装")
    else:
        log("❌ 未找到 ffmpeg, 请安装 https://ffmpeg.org"); ok = False

    try:
        import edge_tts  # noqa
        log("✅ edge-tts 已安装")
    except ImportError:
        log("❌ 未安装 edge-tts, 请运行: pip install edge-tts"); ok = False

    if which("npx"):
        log("→ 运行 'npx hyperframes doctor' 检查 Chrome 是否就绪:")
        run(["npx", "-y", "hyperframes", "doctor"])
    log("=== 自检结束: " + ("全部就绪 ✅" if ok else "有缺失项, 见上方 ❌") + " ===")
    return ok


# ------------------------- 主流程 -------------------------
def main():
    ap = argparse.ArgumentParser(description="Path B 免费端到端成片脚本")
    ap.add_argument("--input", help="脚本文件 (.txt/.md 或 .json 场景列表)")
    ap.add_argument("--output", default="output.mp4", help="最终 MP4 路径 (默认 output.mp4)")
    ap.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="edge-tts 音色")
    ap.add_argument("--resolution", default="1080x1920", help="分辨率, 如 1080x1920(竖) 或 1920x1080(横)")
    ap.add_argument("--doctor", action="store_true", help="只做环境自检")
    ap.add_argument("--skip-render", action="store_true", help="只生成音频+HTML, 不渲染(调试用)")
    ap.add_argument("--keep", action="store_true", help="保留中间文件")
    args = ap.parse_args()

    if args.doctor:
        sys.exit(0 if doctor() else 1)

    if not args.input:
        ap.error("必须提供 --input 脚本文件 (或用 --doctor 自检)")

    if not os.path.isfile(args.input):
        log(f"❌ 找不到输入文件: {args.input}"); sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        scenes = parse_input(f.read())
    if not scenes:
        log("❌ 输入未解析出任何分镜"); sys.exit(1)
    log(f"解析到 {len(scenes)} 个分镜")

    # 解析分辨率
    try:
        w, h = (int(x) for x in args.resolution.lower().split("x"))
    except ValueError:
        log(f"❌ 分辨率格式错误: {args.resolution} (应为 宽x高, 如 1080x1920)"); sys.exit(1)

    work = tempfile.mkdtemp(prefix="pathb_")
    audio_files, sub_files, durations = [], [], []
    edge_tts_bin = which("edge-tts")
    if not edge_tts_bin:
        log("❌ 找不到 edge-tts 命令。请先: pip install edge-tts (并确认其 Scripts 目录在 PATH)")
        sys.exit(1)

    try:
        # ② edge-tts 逐段配音
        for i, sc in enumerate(scenes, 1):
            voice = sc.get("voice") or args.voice
            mp3 = os.path.join(work, f"scene_{i}.mp3")
            vtt = os.path.join(work, f"scene_{i}.vtt")
            log(f"→ 配音 分镜{i} (voice={voice})")
            cmd = [edge_tts_bin, "--voice", voice, "--text", sc["body"],
                   "--write-media", mp3, "--write-subtitles", vtt]
            r = run(cmd)
            if r.returncode != 0 or not os.path.exists(mp3):
                log(f"❌ 分镜{i} 配音失败 (检查网络是否能连微软语音服务 / edge-tts 是否安装)")
                sys.exit(1)
            dur = ffprobe_duration(mp3)
            if dur is None:
                dur = estimate_duration(sc["body"])
                log(f"  (ffprobe 不可用, 估算时长 {dur:.1f}s)")
            else:
                log(f"  时长 {dur:.1f}s")
            audio_files.append(mp3)
            sub_files.append(vtt)
            durations.append(dur)

        # ③ 生成合成 HTML
        html = build_html(scenes, durations, w, h)
        comp = os.path.join(work, "composition.html")
        with open(comp, "w", encoding="utf-8") as f:
            f.write(html)
        log(f"→ 合成 HTML 已生成: {comp}")

        if args.skip_render:
            log("⏭  --skip-render 已设, 跳过渲染与合成。中间文件在: " + work)
            if args.keep:
                import shutil as _s
                dest = os.path.join(os.getcwd(), "pathb_debug")
                _s.copytree(work, dest, dirs_exist_ok=True)
                log(f"已复制到 {dest}")
            sys.exit(0)

        # ④ HyperFrames 渲染静帧视频
        silent = os.path.join(work, "silent.mp4")
        log("→ HyperFrames 渲染画面 (首次会下载 Chrome, 请耐心等待)")
        r = run(["npx", "-y", "hyperframes", "render", "-c", comp, "-o", silent])
        if r.returncode != 0 or not os.path.exists(silent):
            log("❌ HyperFrames 渲染失败。常见原因: 未装 Chrome(运行 npx hyperframes browser ensure) / 未装 ffmpeg / 网络受限")
            sys.exit(1)

        # ⑤ ffmpeg 合成: 拼音频 + 烧字幕
        narr = os.path.join(work, "narration.mp3")
        with open(os.path.join(work, "list.txt"), "w", encoding="utf-8") as f:
            for a in audio_files:
                f.write(f"file '{a.replace(chr(92), '/')}'\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", os.path.join(work, "list.txt"), "-c", "copy", narr],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 合并字幕(按分镜起始时间偏移后拼接为一条完整字幕轨)
        merged = ["WEBVTT", ""]
        start = 0.0
        for idx, vtt in enumerate(sub_files):
            shifted = shift_vtt(vtt, start)
            if shifted.strip():
                merged.append(shifted)
                merged.append("")
            start += durations[idx]
        subs = os.path.join(work, "subs.vtt")
        with open(subs, "w", encoding="utf-8") as f:
            f.write("\n".join(merged))

        final = args.output
        log(f"→ ffmpeg 合成最终视频: {final}")
        vf = f"subtitles={ffmpeg_sub_path(subs)}:force_style='FontSize=36,PrimaryColour=&HFFFFFF&'"
        r = run(["ffmpeg", "-y", "-i", silent, "-i", narr,
                 "-vf", vf,
                 "-c:a", "aac", "-shortest", "-movflags", "+faststart", final],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0 or not os.path.exists(final):
            log("❌ ffmpeg 合成失败。检查 ffmpeg 是否安装、字幕路径是否正确")
            sys.exit(1)

        log(f"✅ 完成! 最终视频: {os.path.abspath(final)}")
    finally:
        if not args.keep:
            import shutil as _s
            _s.rmtree(work, ignore_errors=True)
        else:
            log(f"中间文件保留在: {work}")


if __name__ == "__main__":
    main()
