#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号爆款短视频拆解（体验版）【零一数科·出品】【零一数科·出品】 v0.3.0 —— 本地素材提取脚本

纯标准库实现。不调用任何远端 API、不需要任何 Key。
对本地视频文件提取：元数据 / 封面 / 定时自适应关键帧 / 音频 + 本地 Whisper 转写。
最终在 stdout 输出一个 JSON manifest，供 agent 读取帧图片与转写文本后撰写报告。

用法:
    python3 analyze_local_video.py <video_path> [--out PATH] [--max-frames 20]
                                      [--interval AUTO|<秒>] [--lang <zh|en|auto>]
                                      [--install-ffmpeg] [--install-whisper] [--no-transcribe]
                                      [--max-size-mb 500] [--max-duration-sec 900]

退出码:
    0   成功（含 Whisper 不可用时的降级）
    2   输入错误 / 文件不存在
    8   ffmpeg/ffprobe 缺失（或 --install-ffmpeg 安装后仍缺失）
    9   抽帧失败（致命，无法继续视觉分析）
    10  内部异常
    11  超出大小/时长限制
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ---------- stdout / stderr 约定 ----------
MANIFEST_START = "=== WX_VIDEO_LOCAL_MANIFEST_START ==="
MANIFEST_END = "=== WX_VIDEO_LOCAL_MANIFEST_END ==="

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi", ".flv", ".ts", ".wmv"}


def log(msg: str) -> None:
    print(f"[analyze_local_video] {msg}", file=sys.stderr, flush=True)


def die(code: int, msg: str) -> "None":
    log(f"ERROR({code}): {msg}")
    sys.exit(code)


# ---------- 依赖探测 ----------
def which(name: str) -> "str | None":
    return shutil.which(name)


def require_ffmpeg(install: bool = False) -> tuple[str, str]:
    ff = which("ffmpeg")
    fp = which("ffprobe")
    if ff and fp:
        return ff, fp
    if install:
        install_ffmpeg()
        ff, fp = which("ffmpeg"), which("ffprobe")
        if ff and fp:
            return ff, fp
        log("自动安装后仍未检测到 ffmpeg/ffprobe（可能安装仍在进行或 PATH 未刷新）。"
            "请手动安装后重试。")
    die(8, "缺少 ffmpeg/ffprobe。请先安装（一次性、约几分钟、下载几百 MB）：macOS `brew install ffmpeg`；"
          "Ubuntu/Debian `sudo apt install ffmpeg`；"
          "Windows `winget install Gyan.FFmpeg` 或从 https://ffmpeg.org/download.html 下载并加入 PATH。"
          "安装后重试。")


def install_ffmpeg() -> None:
    """未检测到 ffmpeg/ffprobe 时，按平台用包管理器自动安装。

    按平台选型：macOS 用 brew；Linux 用 apt（需 sudo，非交互）；Windows 用 winget
    （Win10+ 自带），winget 不可用则提示手动安装。安装失败/不支持的平台不报错，
    由调用方降级为提示手动安装。安装为系统级操作、耗时长且体积大，故仅在显式带
    --install-ffmpeg 时执行。
    """
    pkg_mgr = None
    install_cmd = None
    if sys.platform == "darwin" and which("brew"):
        pkg_mgr = "brew"
        install_cmd = ["brew", "install", "ffmpeg"]
    elif sys.platform.startswith("linux") and which("apt-get"):
        pkg_mgr = "apt"
        # 非交互 sudo；若需要密码会被 -n 拒绝，交给调用方提示手动安装
        install_cmd = ["sudo", "-n", "apt-get", "install", "-y", "ffmpeg"]
    elif sys.platform == "win32" and which("winget"):
        pkg_mgr = "winget"
        install_cmd = ["winget", "install", "-e", "--id", "Gyan.FFmpeg",
                       "--accept-package-agreements", "--accept-source-agreements"]
    else:
        log("当前平台未找到可靠包管理器（macOS 需 brew、Linux 需 apt-get、Windows 需 winget），"
            "跳过自动安装。请手动安装：macOS `brew install ffmpeg`；"
            "Ubuntu/Debian `sudo apt install ffmpeg`；"
            "Windows 可用 `winget install Gyan.FFmpeg`，或从 https://ffmpeg.org/download.html "
            "下载解压后把 bin 目录加入 PATH。")
        return

    log(f"未检测到 ffmpeg/ffprobe，尝试用 {pkg_mgr} 自动安装（耗时较长、体积大，macOS/Linux 约 2–6 分钟、下载 200–500MB；Windows winget 类似，需联网）…")
    try:
        proc = subprocess.run(install_cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        log(f"包管理器 {pkg_mgr} 不可用，自动安装失败。请手动安装 ffmpeg。")
        return
    except subprocess.TimeoutExpired:
        log(f"{pkg_mgr} 安装 ffmpeg 超时（>10 分钟），已中止。请手动安装后重试。")
        return
    if proc.returncode != 0:
        log(f"{pkg_mgr} 安装 ffmpeg 失败（exit {proc.returncode}）。"
            f"stderr 摘要：{(proc.stderr or '').strip()[-500:]}")
        log("请手动安装：macOS `brew install ffmpeg`；Ubuntu/Debian `sudo apt install ffmpeg`；"
            "Windows `winget install Gyan.FFmpeg` 或从 https://ffmpeg.org/download.html 下载并加入 PATH。")
        return
    log(f"{pkg_mgr} 已安装 ffmpeg，重新探测…")


# ---------- 元数据 ----------
def probe_metadata(ffprobe: str, video: Path) -> dict:
    cmd = [
        ffprobe, "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        die(9, f"ffprobe 解析失败：{e.output.decode('utf-8', 'ignore')}")
    data = json.loads(out)
    fmt = data.get("format", {}) or {}
    streams = data.get("streams", []) or []

    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    def to_float(v, default=0.0):
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    duration = to_float(fmt.get("duration")) or to_float(v_stream.get("duration"))
    width = v_stream.get("width")
    height = v_stream.get("height")
    fps = _parse_fps(v_stream.get("avg_frame_rate") or v_stream.get("r_frame_rate"))
    tags = fmt.get("tags", {}) or {}

    return {
        "title": tags.get("title") or (v_stream.get("tags", {}) or {}).get("title"),
        "author": tags.get("artist") or tags.get("author") or tags.get("composer"),
        "duration_sec": round(duration, 2),
        "duration_hms": _sec_to_hms(duration),
        "width": width,
        "height": height,
        "fps": fps,
        "video_codec": v_stream.get("codec_name"),
        "audio_codec": a_stream.get("codec_name"),
        "bit_rate": fmt.get("bit_rate"),
        "format_name": fmt.get("format_name"),
        "size_bytes": fmt.get("size"),
    }


def _parse_fps(rate: "str | None") -> "float | None":
    if not rate or rate == "0/0":
        return None
    if "/" in rate:
        try:
            num, den = rate.split("/", 1)
            den_f = float(den)
            return round(float(num) / den_f, 3) if den_f else None
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return round(float(rate), 3)
    except ValueError:
        return None


def _sec_to_hms(sec: float) -> str:
    sec = float(sec or 0)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ---------- 抽帧 ----------
def decide_interval(duration: float, max_frames: int) -> float:
    """定时自适应：按时长决定抽帧间隔，并保证总帧数 <= max_frames。

    间隔偏密（v0.2.0 起），保证短视频有足够帧支撑画面拆解：
      < 2min 每 8s 一帧、2–10min 每 15s 一帧、>10min 每 30s 一帧；
      若估算帧数仍超过 max_frames 上限，则放大间隔封顶。
    """
    if duration <= 0:
        return 8.0
    if duration < 120:        # < 2min：每 8s 一帧
        base = 8.0
    elif duration < 600:      # 2–10min：每 15s 一帧
        base = 15.0
    else:                     # >10min：每 30s 一帧
        base = 30.0
    # 以 base 估算的帧数若超过上限，则放大间隔
    est = duration / base
    if est > max_frames:
        base = duration / max_frames
    return round(base, 3)


def _find_cover_stream_index(ffprobe: str, video: Path) -> "int | None":
    """用 ffprobe 探测是否存在内嵌封面流，返回其流 index；不存在返回 None。

    判定信号：容器内嵌封面/海报在 ffprobe 中以一个视频流出现，且 disposition
    的 attached_pic=1（mp4 covr / mkv attached_pic / mov poster 均如此）。
    仅当探测到这样的流才认定为真实内嵌封面，避免把主视频首帧误判为封面。
    """
    cmd = [ffprobe, "-v", "error", "-print_format", "json",
           "-show_entries",
           "stream=index,codec_type,codec_name:stream_disposition=attached_pic",
           str(video)]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    for s in data.get("streams", []) or []:
        if s.get("codec_type") != "video":
            continue
        disp = s.get("disposition") or {}
        # attached_pic 可能是 dict（新版 ffprobe）或不存在
        if (disp.get("attached_pic") == 1
                or disp.get("attached_pic") == "1"):
            return s.get("index")
    return None


def extract_embedded_cover(ffmpeg: str, ffprobe: str, video: Path, out: Path,
                           max_edge: int = 0) -> "str | None":
    """优先提取容器内嵌的封面流（创作者设置的真实封面/海报）。

    先用 ffprobe 探测是否存在 attached_pic 封面流；存在时按其流 index 精确提取，
    不存在则返回 None（由调用方回退中段帧）。这样可避免 `-map 0:v:1?` 在无封面时
    静默退回主视频首帧、误标为 embedded 的问题。
    """
    idx = _find_cover_stream_index(ffprobe, video)
    if idx is None:
        return None
    cover = out / "cover.jpg"
    scale = _scale_vf(max_edge)
    cmd = [ffmpeg, "-y", "-i", str(video),
           "-map", f"0:{idx}", "-frames:v", "1", "-q:v", "2", "-update", "1"]
    if scale:
        cmd += ["-vf", scale]
    cmd += [str(cover)]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None
    return str(cover) if cover.exists() and cover.stat().st_size > 0 else None


def extract_cover(ffmpeg: str, ffprobe: str, video: Path, out: Path, duration: float,
                  max_edge: int = 0) -> tuple["str | None", str]:
    """提取封面。优先内嵌封面流，失败回退到 duration/2 的中段帧。

    返回 (cover 绝对路径或 None, cover_source: "embedded" | "midframe")。
    """
    cover_path = out / "cover.jpg"
    if cover_path.exists():
        cover_path.unlink()

    embedded = extract_embedded_cover(ffmpeg, ffprobe, video, out, max_edge)
    if embedded:
        return embedded, "embedded"

    ss = duration / 2.0 if duration > 2 else 0.0
    midframe = out / "cover.jpg"
    scale = _scale_vf(max_edge)
    cmd = [ffmpeg, "-y", "-ss", f"{ss:.2f}", "-i", str(video)]
    if scale:
        cmd += ["-vf", scale]
    cmd += ["-frames:v", "1", "-q:v", "3", "-update", "1", str(midframe)]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if midframe.exists() and midframe.stat().st_size > 0:
            return str(midframe), "midframe"
    except subprocess.CalledProcessError:
        pass
    return None, "midframe"


def _scale_vf(max_edge: int) -> str:
    """ffmpeg scale 滤镜串：把图像长边 cap 到 max_edge、保持宽高比、不放大。

    max_edge<=0 返回 ""（不缩放，保留原分辨率）。用于压缩帧/封面以降低视觉
    token 数——吃速度的是分辨率（像素/token），不是 JPEG 画质，故仅缩分辨率、
    画质仍由 -q:v 控制。视频号常规叠加文字（产品名/CTA/价格/字幕条）在长边
    1280 下仍清晰；只在画面密集细小字时才需调高或置 0。
    """
    if max_edge <= 0:
        return ""
    return (f"scale=w='min({max_edge},iw)':h='min({max_edge},ih)':"
            "force_original_aspect_ratio=decrease")


def extract_frames(ffmpeg: str, video: Path, out: Path, interval: float,
                   max_frames: int, duration: float, max_edge: int = 0
                   ) -> tuple[list[str], list[float]]:
    """定时抽帧；返回 (帧路径列表, 每帧时间戳列表)。"""
    raw_dir = out / "_raw_frames"
    raw_dir.mkdir(exist_ok=True)
    pattern = str(raw_dir / "frame_%04d.jpg")
    fps_filter = f"fps=1/{interval}"
    scale = _scale_vf(max_edge)
    vf = f"{fps_filter},{scale}" if scale else fps_filter
    cmd = [ffmpeg, "-y", "-i", str(video), "-vf", vf,
           "-q:v", "3", pattern]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        die(9, f"抽帧失败：{e}")

    files = sorted(raw_dir.glob("frame_*.jpg"))
    if not files:
        die(9, "抽帧失败：未生成任何帧图片，无法进行视觉分析。")

    # 超上限则均匀二次采样
    if len(files) > max_frames:
        step = len(files) / max_frames
        idxs = [int(i * step) for i in range(max_frames)]
        files = [files[i] for i in idxs]

    # 重命名为连续编号 + 记录时间戳
    final_dir = out / "frames"
    final_dir.mkdir(exist_ok=True)
    paths, stamps = [], []
    for i, f in enumerate(files, 1):
        dst = final_dir / f"frame_{i:03d}.jpg"
        shutil.move(str(f), str(dst))
        t = round((i - 1) * interval, 2)
        stamps.append(t)
        paths.append(str(dst))

    # 清理空 raw 目录
    try:
        shutil.rmtree(raw_dir)
    except OSError:
        pass
    return paths, stamps


def extract_frames_scene(ffmpeg: str, video: Path, out: Path,
                         threshold: float, max_frames: int, max_edge: int = 0
                         ) -> "tuple[list[str], list[float]]":
    """场景感知抽帧：用 ffmpeg 场景变化检测抽关键镜头帧，去冗余、不降分辨率。

    现状定时抽帧对短视频偏密（2min 约 15 帧，多帧重复无用）。这里改用
    `select='gt(scene,threshold)'` 只在镜头切换时抽帧，重复静态镜头自然合并，
    把帧数压到「场景变化数」。**分辨率不变**（保小字识别），减的只是冗余帧。

    单次 ffmpeg 同时拿帧文件与时间戳：showinfo 把每个输出帧的 pts_time 打到
    stderr，按顺序与输出文件 scene_0001.. 一一对应。失败/无帧返回 ([], [])，
    由调用方回退到定时抽帧（见 build_frame_set）——保证任何情况下都不比定时差。
    """
    raw_dir = out / "_scene_frames"
    raw_dir.mkdir(exist_ok=True)
    pattern = str(raw_dir / "scene_%04d.jpg")
    base = f"select='gt(scene,{threshold})',showinfo"
    scale = _scale_vf(max_edge)
    vf = f"{base},{scale}" if scale else base
    cmd = [ffmpeg, "-y", "-i", str(video),
           "-vf", vf,
           "-vsync", "vfr", "-q:v", "3", pattern]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        return [], []
    files = sorted(raw_dir.glob("scene_*.jpg"))
    if not files:
        return [], []
    # showinfo 行格式含 pts_time:FLOAT；按出现顺序与输出帧文件对齐
    times = [float(t) for t in re.findall(r"pts_time:(\d+\.?\d*)", proc.stderr or "")]
    n = min(len(files), len(times))
    if n == 0:
        return [], []
    files, times = files[:n], times[:n]

    # 超上限则均匀二次采样
    if len(files) > max_frames:
        step = len(files) / max_frames
        idxs = [int(i * step) for i in range(max_frames)]
        files = [files[i] for i in idxs]
        times = [times[i] for i in idxs]

    final_dir = out / "frames"
    final_dir.mkdir(exist_ok=True)
    paths, stamps = [], []
    for i, (f, t) in enumerate(zip(files, times), 1):
        dst = final_dir / f"frame_{i:03d}.jpg"
        shutil.move(str(f), str(dst))
        paths.append(str(dst))
        stamps.append(round(t, 2))
    try:
        shutil.rmtree(raw_dir)
    except OSError:
        pass
    return paths, stamps


def _extract_single_frame(ffmpeg: str, video: Path, out: Path, t: float,
                         name: str, max_edge: int = 0) -> "str | None":
    """用 -ss 精确抽指定时刻的单帧，返回路径或 None。用于补首/末帧保证覆盖。"""
    dst = out / "frames" / f"{name}.jpg"
    (out / "frames").mkdir(exist_ok=True)
    scale = _scale_vf(max_edge)
    cmd = [ffmpeg, "-y", "-ss", f"{max(0.0, t):.2f}", "-i", str(video)]
    if scale:
        cmd += ["-vf", scale]
    cmd += ["-frames:v", "1", "-q:v", "3", "-update", "1", str(dst)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None
    return str(dst) if dst.exists() and dst.stat().st_size > 0 else None


def build_frame_set(ffmpeg: str, video: Path, out: Path, interval: float,
                    max_frames: int, duration: float,
                    scene_aware: bool, scene_threshold: float,
                    max_edge: int = 0
                    ) -> "tuple[list[str], list[float], list[str], str]":
    """编排抽帧：场景感知优先（去冗余），不足则回退定时兜底。

    返回 (frames, stamps, sources, mode)：
      - sources 每帧标注 'scene'（场景变化帧）或 'timed'（定时帧）；
      - mode = 'scene' | 'timed'，供 manifest 报告抽帧策略。

    稳定性保证：场景帧数不足（< 下限）即回退定时，绝不比纯定时更差；
    场景抽取彻底失败同样回退。下限取 max(5, max_frames//3)：足够覆盖结构，
    又让多数有镜头切换的视频能用上场景去冗余。
    """
    min_frames = max(5, max_frames // 3)
    if scene_aware:
        s_paths, s_stamps = extract_frames_scene(ffmpeg, video, out,
                                                 scene_threshold, max_frames, max_edge)
        if len(s_paths) >= min_frames:
            # 场景抽帧只在镜头切换点出帧，会漏掉开头 Hook 段与结尾 CTA 段。
            # 强制补首帧(t≈0)与末帧(t≈duration)，与已有场景帧按时间就近去重，
            # 保证时间线首尾覆盖、不丢结构。
            dedup_win = max(1.0, interval * 0.5)
            chosen = list(zip(s_paths, s_stamps))  # (path, ts)
            if not chosen or chosen[0][1] > dedup_win:
                first = _extract_single_frame(ffmpeg, video, out, 0.0, "frame_head", max_edge)
                if first:
                    chosen.insert(0, (first, 0.0))
            if duration > 2 and (not chosen or chosen[-1][1] < duration - dedup_win):
                tail_t = max(0.0, duration - 0.1)
                tail = _extract_single_frame(ffmpeg, video, out, tail_t, "frame_tail", max_edge)
                if tail:
                    chosen.append((tail, round(tail_t, 2)))
            # 按时间排序、超上限则均匀二次采样
            chosen.sort(key=lambda x: x[1])
            if len(chosen) > max_frames:
                step = len(chosen) / max_frames
                idxs = [int(i * step) for i in range(max_frames)]
                chosen = [chosen[i] for i in idxs]
            # 重命名连续编号 frame_001..；补的首/末帧 source 标 timed，其余 scene
            final_dir = out / "frames"
            paths, stamps, sources = [], [], []
            for i, (p, t) in enumerate(chosen, 1):
                src = "timed" if ("frame_head" in p or "frame_tail" in p) else "scene"
                dst = final_dir / f"frame_{i:03d}.jpg"
                if Path(p).resolve() != dst.resolve():
                    shutil.move(str(p), str(dst))
                paths.append(str(dst))
                stamps.append(round(t, 2))
                sources.append(src)
            log(f"场景感知抽帧：{len(paths)} 帧（阈值 {scene_threshold}），含首末帧覆盖。")
            return paths, stamps, sources, "scene"
        log(f"场景帧仅 {len(s_paths)} 帧（< 下限 {min_frames}），回退定时抽帧。")

    paths, stamps = extract_frames(ffmpeg, video, out, interval, max_frames, duration, max_edge)
    return paths, stamps, ["timed"] * len(paths), "timed"


# ---------- 音频 + 转写 ----------
def extract_audio(ffmpeg: str, video: Path, out: Path) -> "Path | None":
    wav = out / "audio.wav"
    cmd = [ffmpeg, "-y", "-i", str(video), "-vn", "-ac", "1",
           "-ar", "16000", "-f", "wav", str(wav)]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return wav if wav.exists() and wav.stat().st_size > 0 else None
    except subprocess.CalledProcessError:
        return None


def _find_whisper_cpp_model() -> "str | None":
    env = os.environ.get("WHISPER_CPP_MODEL")
    if env and Path(env).exists():
        return env
    # brew 默认路径
    for base in ("/opt/homebrew", "/usr/local"):
        share = Path(base) / "share" / "whisper-cpp"
        if share.exists():
            for f in share.glob("ggml-*.bin"):
                return str(f)
    # 常见模型名兜底
    for name in ("ggml-medium.bin", "ggml-small.bin", "ggml-base.en.bin", "ggml-base.bin"):
        p = shutil.which(name)
        if p:
            return p
    return None


def detect_whisper() -> "tuple[str, str | None]":
    """返回 (实现类型, 模型路径或None)。未命中返回 ('', None)。"""
    # 1) whisper-cpp / whisper.main
    for binname in ("whisper-cpp", "whisper.main", "whisper-cli", "main"):
        if which(binname):
            return ("whisper-cpp", _find_whisper_cpp_model())
    # 2) openai-whisper CLI
    if which("whisper"):
        return ("openai-whisper", None)
    # 3) mlx_whisper CLI
    if which("mlx_whisper"):
        return ("mlx-whisper", None)
    # 4) python 模块（兜底）
    try:
        import importlib
        if importlib.util.find_spec("whisper"):
            return ("python-whisper", None)
        if importlib.util.find_spec("mlx_whisper"):
            return ("mlx-whisper", None)
    except Exception:
        pass
    return ("", None)


def install_whisper() -> "tuple[str, str | None]":
    """未检测到 Whisper 时，按平台自动安装一个轻量实现，安装后重新探测。

    选型（跨平台、国内免翻墙优先）：
      - macOS（有 brew）→ brew install whisper-cpp（预编译、最轻、无 torch）
      - macOS Apple Silicon（无 brew）→ mlx-whisper（pip，国内镜像）
      - macOS Intel / Windows / Linux → openai-whisper（pip，国内镜像；依赖 torch）
    pip 统一走国内镜像（清华，失败回退阿里）确保免翻墙。
    安装失败不报错，返回 ('', None) 由调用方降级为无台词模式。
    """
    machine = platform.machine().lower()
    is_apple_silicon = (sys.platform == "darwin" and machine in ("arm64", "aarch64"))

    # 国内 pip 镜像（免翻墙），清华优先、阿里回退
    mirrors = [
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "https://mirrors.aliyun.com/pypi/simple",
    ]

    pkg = None
    # 1) macOS 有 brew → whisper-cpp（预编译，最轻）
    if sys.platform == "darwin" and which("brew"):
        log("未检测到 Whisper，尝试用 brew 安装 whisper-cpp（预编译、最轻，约几分钟、下载几百 MB，需联网）…")
        try:
            proc = subprocess.run(["brew", "install", "whisper-cpp"],
                                  capture_output=True, text=True, timeout=600)
        except FileNotFoundError:
            proc = None
            log("brew 不可用，转用 pip 安装。")
        except subprocess.TimeoutExpired:
            log("brew 安装 whisper-cpp 超时（>10 分钟），已中止。转用 pip 安装。")
            proc = None
        if proc is not None and proc.returncode == 0:
            log("whisper-cpp 已安装，重新探测…")
            impl, model = detect_whisper()
            if impl:
                log(f"自动安装成功，命中 Whisper 实现：{impl}")
                return impl, model
            log("whisper-cpp 已装但未探测到（可能 CLI 未进 PATH），转用 pip 安装。")
        elif proc is not None:
            log(f"brew 安装 whisper-cpp 失败（exit {proc.returncode}），转用 pip 安装。"
                f"stderr 摘要：{(proc.stderr or '').strip()[-300:]}")

    # 2) pip 路径：Apple Silicon → mlx-whisper，其它 → openai-whisper
    pkg = "mlx-whisper" if is_apple_silicon else "openai-whisper"
    log(f"未检测到 Whisper，尝试用 pip（国内镜像免翻墙）安装 {pkg}（耗时取决于包大小：mlx-whisper 约 1–3 分钟，openai-whisper 含 torch 约 5–15 分钟）…")
    installed = False
    last_err = ""
    for mirror in mirrors:
        cmd = [sys.executable, "-m", "pip", "install", "-U", "--user",
               "-i", mirror, "--timeout", "60", "--retries", "2", pkg]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=480)
        except FileNotFoundError:
            log("未找到 pip（python -m pip 不可用），自动安装失败。")
            break
        except subprocess.TimeoutExpired:
            last_err = f"镜像 {mirror} 超时（>8 分钟，可能在编译，如旧 Python 无预编译 wheel）"
            log(last_err + "，尝试下一个镜像。")
            continue
        if proc.returncode == 0:
            installed = True
            break
        last_err = f"镜像 {mirror} 失败（exit {proc.returncode}）：{(proc.stderr or '').strip()[-300:]}"
        log(last_err + "，尝试下一个镜像。")
    if not installed:
        log(f"pip 安装 {pkg} 失败（所有国内镜像均不可用）。{last_err}")
        log(f"请手动安装：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple {pkg}`"
            "（国内免翻墙），或 macOS 用 `brew install whisper-cpp`，"
            "或加 --no-transcribe 仅做画面分析（不影响出报告）。")
        return ("", None)
    log(f"已安装 {pkg}，重新探测…")
    impl, model = detect_whisper()
    if impl:
        log(f"自动安装成功，命中 Whisper 实现：{impl}")
    else:
        log(f"{pkg} 已安装但未被探测到（可能 CLI 未进 PATH，但模块可 import，转写时会自动回退进程内 API）。"
            "如仍不行请重新打开终端，或手动安装 whisper-cpp。")
    return impl, model


def transcribe(wav: Path, impl: str, model: "str | None", lang: str) -> "str | None":
    lang_arg = lang if lang and lang != "auto" else None
    try:
        if impl == "whisper-cpp":
            if not model:
                log("whisper-cpp 已安装但未找到模型（设置 WHISPER_CPP_MODEL 指向 ggml-*.bin）")
                return None
            outbase = wav.with_suffix("")
            cmd = [which("whisper-cpp") or "whisper-cpp", "-m", model, "-f", str(wav),
                   "-ojf", "-of", str(outbase)]
            if lang_arg:
                cmd += ["-l", lang_arg]
            subprocess.run(cmd, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            jf = Path(str(outbase) + ".json")
            if jf.exists():
                data = json.loads(jf.read_text("utf-8"))
                sgs = data.get("transcription") or data.get("segments") or []
                parts = []
                for s in sgs:
                    ts = s.get("timestamps", {})
                    frm = ts.get("from") if isinstance(ts, dict) else None
                    text = s.get("text", "").strip()
                    if text:
                        parts.append(f"[{_fmt_ts(frm)}] {text}" if frm else text)
                return "\n".join(parts) if parts else None
            return None

        if impl == "openai-whisper":
            # 优先用 CLI；--user 安装时 CLI 可能不在 PATH（Windows/Linux 常见），则回退进程内 API
            cli = which("whisper")
            if cli:
                cmd = [cli, str(wav), "--output_format", "json",
                       "--output_dir", str(wav.parent), "--verbose", "False"]
                if lang_arg:
                    cmd += ["--language", lang_arg]
                subprocess.run(cmd, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                jf = wav.with_suffix(".json")
                if jf.exists():
                    data = json.loads(jf.read_text("utf-8"))
                    sgs = data.get("segments", [])
                    parts = [f"[{_fmt_ts(s.get('start'))}] {s.get('text','').strip()}"
                             for s in sgs if s.get("text", "").strip()]
                    return "\n".join(parts) if parts else (data.get("text") or None)
                return None
            # 回退：进程内调用 openai-whisper Python API（首次会自动下载默认模型）
            import whisper  # noqa: PLC0415
            m = whisper.load_model("base")
            res = m.transcribe(str(wav), language=lang_arg) if lang_arg else m.transcribe(str(wav))
            sgs = res.get("segments", []) or []
            parts = [f"[{_fmt_ts(s.get('start'))}] {s.get('text','').strip()}"
                     for s in sgs if s.get("text", "").strip()]
            return "\n".join(parts) if parts else (res.get("text") or None)

        if impl == "mlx-whisper":
            # 优先用 CLI；--user 安装时 CLI 可能不在 PATH，则回退到 Python API（模块可直接 import）
            cli = which("mlx_whisper")
            if cli:
                cmd = [cli, str(wav), "--output-dir", str(wav.parent)]
                if lang_arg:
                    cmd += ["--language", lang_arg]
                subprocess.run(cmd, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                jf = next(wav.parent.glob(wav.stem + "*.json"), None)
                if jf:
                    data = json.loads(jf.read_text("utf-8"))
                    sgs = data.get("segments", [])
                    parts = [f"[{_fmt_ts(s.get('start'))}] {s.get('text','').strip()}"
                             for s in sgs if s.get("text", "").strip()]
                    return "\n".join(parts) if parts else (data.get("text") or None)
                return None
            # 回退：进程内调用 mlx_whisper Python API（首次会自动下载默认模型）
            import mlx_whisper  # noqa: PLC0415
            kwargs = {"language": lang_arg} if lang_arg else {}
            res = mlx_whisper.transcribe(str(wav), **kwargs)
            sgs = res.get("segments", []) or []
            parts = [f"[{_fmt_ts(s.get('start'))}] {s.get('text','').strip()}"
                     for s in sgs if s.get("text", "").strip()]
            return "\n".join(parts) if parts else (res.get("text") or None)

        if impl == "python-whisper":
            import whisper  # 本地 import
            m = whisper.load_model("base")
            res = m.transcribe(str(wav), language=lang_arg) if lang_arg else m.transcribe(str(wav))
            sgs = res.get("segments", [])
            parts = [f"[{_fmt_ts(s.get('start'))}] {s.get('text','').strip()}"
                     for s in sgs if s.get("text", "").strip()]
            return "\n".join(parts) if parts else (res.get("text") or None)
    except subprocess.CalledProcessError as e:
        log(f"转写失败（{impl}），降级为无台词模式：{e}")
        return None
    except Exception as e:  # noqa: BLE001
        log(f"转写异常（{impl}），降级为无台词模式：{e}")
        return None
    return None


def _fmt_ts(sec) -> str:
    try:
        sec = float(sec)
    except (TypeError, ValueError):
        return "00:00"
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


# ---------- 主流程 ----------
def main() -> int:
    ap = argparse.ArgumentParser(description="视频号爆款短视频拆解（体验版）【零一数科·出品】【零一数科·出品】v0.3.0——本地素材提取")
    ap.add_argument("video", help="本地视频文件路径")
    ap.add_argument("--out", help="输出目录（默认在系统临时目录下创建）")
    ap.add_argument("--max-frames", type=int, default=20, help="抽帧上限（默认 20）")
    ap.add_argument("--interval", default="AUTO",
                    help="抽帧间隔秒数，AUTO 为自适应（默认 AUTO）")
    ap.add_argument("--lang", default=os.environ.get("WHISPER_LANG", "auto"),
                    help="Whisper 语言，如 zh/en/auto（默认读取 WHISPER_LANG 或 auto）")
    ap.add_argument("--no-transcribe", action="store_true", help="跳过转写")
    ap.add_argument("--install-whisper", action="store_true",
                    help="选装：未检测到 Whisper 时自动安装（macOS 优先 brew 装 whisper-cpp，"
                         "其余 pip 国内镜像装 mlx-whisper/openai-whisper，首次需联网下模型），"
                         "安装后重新转写。Whisper 为可选依赖，不带此参数时未装也照常出报告")
    ap.add_argument("--install-ffmpeg", action="store_true",
                    help="未检测到 ffmpeg/ffprobe 时自动用包管理器安装"
                         "（macOS 装 brew、Linux 装 apt-get，需 sudo；Windows 等不自动装），"
                         "安装失败则提示手动安装命令")
    ap.add_argument("--max-size-mb", type=float, default=500,
                    help="文件大小上限（MB，默认 500；0 表示不限）")
    ap.add_argument("--max-duration-sec", type=int, default=900,
                    help="时长上限（秒，默认 900 即 15 分钟；0 表示不限）")
    ap.add_argument("--no-scene-aware", action="store_true",
                    help="关闭场景感知抽帧，强制用定时抽帧。场景感知默认开启："
                         "按镜头切换抽关键帧、合并重复静态镜头以减少冗余帧（分辨率不变），"
                         "场景帧不足时自动回退定时抽帧，不会比定时更差")
    ap.add_argument("--scene-threshold", type=float, default=0.3,
                    help="场景感知阈值（默认 0.3，0~1，越小越敏感、抽帧越多；"
                         "仅 --no-scene-aware 关闭时不生效）")
    ap.add_argument("--max-frame-edge", type=int, default=1280,
                    help="帧/封面图片长边像素上限（默认 1280；0 表示不缩放、保留原分辨率）。"
                         "压缩仅缩分辨率、不动 JPEG 画质——吃视觉速度/token 的是像素数。"
                         "1280 下视频号常规叠加文字仍清晰；画面文字极小时可调高（如 1600）或置 0")
    args = ap.parse_args()

    video = Path(args.video).expanduser()
    if not video.exists() or not video.is_file():
        die(2, f"视频文件不存在：{video}")
    if video.suffix.lower() not in VIDEO_EXTS:
        log(f"警告：扩展名 {video.suffix} 不在常见视频列表中，仍尝试处理。")

    # 大小闸门（ffprobe 之前即可做，开销极低）
    if args.max_size_mb > 0:
        size_mb = video.stat().st_size / 1024 / 1024
        if size_mb > args.max_size_mb:
            die(11, f"视频过大：{size_mb:.1f}MB > {args.max_size_mb}MB 上限。"
                  "请在本地压缩或裁剪后重新上传。")

    ffmpeg, ffprobe = require_ffmpeg(install=args.install_ffmpeg)

    # 输出目录
    if args.out:
        out_dir = Path(args.out).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = Path(tempfile.gettempdir()) / f"wx-video-local-{int(time.time())}"
        out_dir.mkdir(parents=True, exist_ok=True)

    log("正在提取元数据…")
    meta = probe_metadata(ffprobe, video)
    duration = meta.get("duration_sec") or 0.0
    log(f"时长 {meta.get('duration_hms')}，分辨率 {meta.get('width')}x{meta.get('height')}")

    # 时长闸门
    if args.max_duration_sec > 0 and duration > args.max_duration_sec:
        die(11, f"视频过长：{meta.get('duration_hms')} > {_sec_to_hms(args.max_duration_sec)} 上限。"
              "建议裁剪出关键片段后再拆解，长视频抽 16 帧分析粒度过粗。")

    log("正在提取封面…")
    cover, cover_source = extract_cover(ffmpeg, ffprobe, video, out_dir, duration,
                                        args.max_frame_edge)
    log(f"封面来源：{cover_source}" + ("（内嵌封面）" if cover_source == "embedded"
        else "（中段帧推断）"))

    # 间隔
    if args.interval and args.interval.upper() != "AUTO":
        try:
            interval = float(args.interval)
        except ValueError:
            die(2, f"--interval 取值非法：{args.interval}")
    else:
        interval = decide_interval(duration, args.max_frames)
    log(f"正在抽取关键帧（间隔 {interval}s，上限 {args.max_frames}，长边≤{args.max_frame_edge or '原始'}）…")
    frames, stamps, frame_sources, frames_mode = build_frame_set(
        ffmpeg, video, out_dir, interval, args.max_frames, duration,
        scene_aware=not args.no_scene_aware, scene_threshold=args.scene_threshold,
        max_edge=args.max_frame_edge)
    log(f"已抽取 {len(frames)} 帧到 {out_dir / 'frames'}（模式：{frames_mode}）")

    transcript = None
    whisper_impl = ""
    transcript_available = False
    if not args.no_transcribe:
        log("正在探测本地 Whisper…")
        impl, model = detect_whisper()
        if not impl and args.install_whisper:
            impl, model = install_whisper()
        if not impl:
            log("未检测到本地 Whisper，跳过转写（仅做画面分析）。"
                "Whisper 为选装依赖，未装不影响出报告；如需启用台词分析，"
                "可加 --install-whisper 或手动安装 whisper-cpp / openai-whisper / mlx-whisper。")
        else:
            log(f"命中 Whisper 实现：{impl}" +
                (f"（模型 {model}）" if model else ""))
            log("正在提取音频…")
            wav = extract_audio(ffmpeg, video, out_dir)
            if wav:
                log("正在转写音频…")
                transcript = transcribe(wav, impl, model, args.lang)
                if transcript:
                    transcript_available = True
                    log("转写完成。")
                else:
                    log("转写无结果，降级为无台词模式。")
            else:
                log("未提取到音频流，跳过转写。")
            whisper_impl = impl
    else:
        log("已按用户要求跳过转写。")

    # 帧索引表：供 agent 一次性拿到时间线地图，免逐帧往返建立结构
    frame_index = [
        {"idx": i + 1, "path": frames[i], "ts": stamps[i], "source": frame_sources[i]}
        for i in range(len(frames))
    ]

    manifest = {
        "video_path": str(video),
        "metadata": meta,
        "cover": cover,
        "cover_source": cover_source,
        "frames": frames,
        "frame_timestamps_sec": stamps,
        "frame_index": frame_index,
        "frame_sources": frame_sources,
        "frames_mode": frames_mode,
        "frames_interval_sec": interval,
        "frames_count": len(frames),
        "frames_max_edge": args.max_frame_edge,
        "transcript": transcript,
        "transcript_available": transcript_available,
        "whisper_impl": whisper_impl or None,
        "report_dir": str(out_dir),
    }

    report_file = out_dir / "report.md"
    report_file.touch()
    print(f"WX_VIDEO_REPORT_FILE={report_file}", flush=True)
    print(MANIFEST_START, flush=True)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)
    print(MANIFEST_END, flush=True)
    log(f"完成。素材目录：{out_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        die(10, f"内部异常：{e}")
