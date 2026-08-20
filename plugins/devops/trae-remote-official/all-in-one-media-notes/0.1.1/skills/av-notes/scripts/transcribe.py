#!/usr/bin/env python3
"""
Audio/Video -> text via SenseVoice on sherpa-onnx. No PyTorch, CPU-only, China-friendly.

Why sherpa-onnx (not funasr+torch, not llama.cpp):
- `pip install sherpa-onnx` ships a prebuilt onnxruntime wheel — NO torch, NO CUDA needed.
- The int8 SenseVoice model (~229MB) has a ModelScope mirror, so download works in China.
- Runs fully offline on CPU once the model is local.

Video input: when the file is a video, the script ALSO grabs 10 key frames + video info
(ffprobe) IN PARALLEL with transcription — same run, no extra pass. Video info and frame
paths are printed on stderr AS SOON AS they are ready (before transcription finishes), so a
caller can start reading frames while transcription is still running.

Usage:
    python transcribe.py <audio_or_video> [--out transcript.txt] [--lang auto|zh|en|yue|ja|ko]
                          [--model-dir DIR] [--vad silero_vad.onnx] [--num-threads 4]
                          [--frames 3] [--frames-dir DIR] [--no-frames]

Deps:
    pip install sherpa-onnx -i https://pypi.tuna.tsinghua.edu.cn/simple
    # model download (either one):
    #   pip install modelscope   (script auto-downloads), OR
    #   git clone https://www.modelscope.cn/poloniumrock/SenseVoiceSmallOnnx.git
    # ffmpeg decodes audio & grabs frames; ffprobe (ships with ffmpeg) reads video info.
"""
import argparse
import json
import os
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np

# Default model repo on ModelScope (int8, ~229MB): contains model.int8.onnx + tokens.txt
MS_MODEL_REPO = "poloniumrock/SenseVoiceSmallOnnx"
DEFAULT_MODEL_DIR = os.path.expanduser("~/.cache/sherpa-onnx-sense-voice")
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".ts", ".m4v", ".wmv", ".mpg", ".mpeg"}


def resolve_model_dir(model_dir):
    """Return a dir containing model.int8.onnx + tokens.txt, downloading from ModelScope if needed."""
    if model_dir and _has_model(model_dir):
        return model_dir
    target = model_dir or DEFAULT_MODEL_DIR
    if _has_model(target):
        return target
    # try auto-download via modelscope (domestic, no torch needed for snapshot_download)
    try:
        from modelscope import snapshot_download
        print(f"[info] downloading {MS_MODEL_REPO} from ModelScope …", file=sys.stderr)
        return snapshot_download(MS_MODEL_REPO)
    except ImportError:
        sys.exit(
            "[error] model not found and modelscope not installed. Do one of:\n"
            "  pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple\n"
            "or clone the model manually (China mirror):\n"
            f"  git clone https://www.modelscope.cn/{MS_MODEL_REPO}.git\n"
            "then pass its path via --model-dir."
        )


def _has_model(d):
    return os.path.isfile(os.path.join(d, "model.int8.onnx")) and \
           os.path.isfile(os.path.join(d, "tokens.txt"))


def _has_ffmpeg():
    from shutil import which
    return which("ffmpeg") is not None


def is_video(path):
    return os.path.splitext(path)[1].lower() in VIDEO_EXTS


def probe_video(path):
    """Return a dict of basic video info via ffprobe (duration, size, codecs, fps). {} on failure."""
    from shutil import which
    if which("ffprobe") is None:
        return {}
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", path]
    try:
        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout
        raw = json.loads(out)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}
    fmt = raw.get("format", {})
    vstream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), {})
    astream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "audio"), {})
    dur = float(fmt.get("duration", 0) or 0)
    fr = vstream.get("avg_frame_rate", "0/1")
    try:
        num, den = fr.split("/")
        fps = round(float(num) / float(den), 2) if float(den) else None
    except (ValueError, ZeroDivisionError):
        fps = None
    return {
        "duration_sec": round(dur, 1),
        "duration_hms": _hms(dur),
        "width": vstream.get("width"),
        "height": vstream.get("height"),
        "video_codec": vstream.get("codec_name"),
        "audio_codec": astream.get("codec_name"),
        "fps": fps,
        "size_bytes": int(fmt.get("size", 0) or 0),
    }


def _hms(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def extract_key_frames(path, out_dir, n=10, duration_sec=None):
    """Grab n frames evenly across the video (skipping head/tail). Returns list of saved paths."""
    if not _has_ffmpeg():
        return []
    os.makedirs(out_dir, exist_ok=True)
    if not duration_sec or duration_sec <= 0:
        info = probe_video(path)
        duration_sec = info.get("duration_sec") or 0
    stem = os.path.splitext(os.path.basename(path))[0]
    saved = []
    if duration_sec and duration_sec > 0:
        # sample at 1/(n+1), 2/(n+1), … of the timeline to avoid black intro/outro frames
        timestamps = [duration_sec * (i + 1) / (n + 1) for i in range(n)]
    else:
        timestamps = [None] * n  # unknown duration: fall back to first-frame grabs
    for idx, ts in enumerate(timestamps, 1):
        dst = os.path.join(out_dir, f"{stem}_frame{idx}.jpg")
        cmd = ["ffmpeg", "-nostdin", "-y"]
        if ts is not None:
            cmd += ["-ss", f"{ts:.2f}"]
        cmd += ["-i", path, "-frames:v", "1", "-q:v", "3", dst]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.isfile(dst):
            saved.append(dst)
    return saved


def load_audio(path):
    """Decode any audio to 16k mono float32. Uses ffmpeg when available, else stdlib wave for .wav."""
    if _has_ffmpeg():
        cmd = ["ffmpeg", "-nostdin", "-i", path, "-ac", "1", "-ar", "16000",
               "-f", "s16le", "-acodec", "pcm_s16le", "-"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if proc.returncode != 0 or not proc.stdout:
            sys.exit(f"[error] ffmpeg failed to decode: {path}")
        return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if path.lower().endswith(".wav"):
        with wave.open(path, "rb") as w:
            if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
                sys.exit("[error] no ffmpeg: .wav must be 16kHz mono 16-bit. Install ffmpeg for other formats.")
            raw = w.readframes(w.getnframes())
        return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    sys.exit("[error] ffmpeg not found; install it to decode non-wav audio (brew install ffmpeg).")


def transcribe_whole(recognizer, samples):
    stream = recognizer.create_stream()
    stream.accept_waveform(16000, samples)
    recognizer.decode_stream(stream)
    return stream.result.text.strip()


def transcribe_with_vad(recognizer, samples, vad_model):
    """Segment long audio with silero VAD, transcribe each speech chunk. Better for long meetings."""
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = vad_model
    cfg.silero_vad.min_silence_duration = 0.25
    cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=100)

    texts, window, i = [], 512, 0

    def drain():
        while not vad.empty():
            seg = vad.front.samples
            st = recognizer.create_stream()
            st.accept_waveform(16000, seg)
            recognizer.decode_stream(st)
            t = st.result.text.strip()
            if t:
                texts.append(t)
            vad.pop()

    while i < len(samples):
        vad.accept_waveform(samples[i:i + window])
        i += window
        drain()
    vad.flush()
    drain()
    return "\n".join(texts)


def main():
    ap = argparse.ArgumentParser(description="Transcribe audio/video with SenseVoice on sherpa-onnx (no torch).")
    ap.add_argument("audio", help="Path to audio OR video file (any format via ffmpeg).")
    ap.add_argument("--out", help="Write transcript to this file (default: stdout).")
    ap.add_argument("--lang", default="auto", help="auto (default) | zh | en | yue | ja | ko")
    ap.add_argument("--model-dir", help="Dir with model.int8.onnx + tokens.txt (auto-downloaded if omitted).")
    ap.add_argument("--vad", help="Path to silero_vad.onnx; enables segmentation for long audio.")
    ap.add_argument("--num-threads", type=int, default=4, help="CPU threads (default 4).")
    ap.add_argument("--frames", type=int, default=10, help="For video: number of key frames to grab (default 10).")
    ap.add_argument("--frames-dir", help="Where to save frames (default: alongside --out, or ./<name>_frames).")
    ap.add_argument("--no-frames", action="store_true", help="Video: skip key-frame extraction / info.")
    args = ap.parse_args()

    if not os.path.isfile(args.audio):
        sys.exit(f"[error] audio file not found: {args.audio}")

    try:
        import sherpa_onnx
    except ImportError:
        sys.exit("[error] sherpa-onnx not installed. Run:\n"
                 "    pip install sherpa-onnx -i https://pypi.tuna.tsinghua.edu.cn/simple")

    # For video input, kick off key-frame extraction + ffprobe IN A BACKGROUND THREAD so it
    # overlaps the (much slower) transcription. The worker emits frame paths on stderr AS SOON
    # AS they are ready — so a caller can start reading frames while transcription is still running.
    video = is_video(args.audio) and not args.no_frames
    frame_future = None
    executor = None
    if video:
        info = probe_video(args.audio)
        # print video info immediately — available before transcription finishes
        print("[video-info] " + json.dumps(info, ensure_ascii=False), file=sys.stderr, flush=True)
        if args.frames_dir:
            frames_dir = args.frames_dir
        elif args.out:
            frames_dir = os.path.join(os.path.dirname(os.path.abspath(args.out)) or ".",
                                      os.path.splitext(os.path.basename(args.audio))[0] + "_frames")
        else:
            frames_dir = os.path.splitext(os.path.basename(args.audio))[0] + "_frames"

        def grab_and_report():
            frames = extract_key_frames(args.audio, frames_dir, args.frames, info.get("duration_sec"))
            # emit the moment extraction is done, i.e. usually WHILE transcription is still running
            if frames:
                print("[video-frames] " + json.dumps(frames, ensure_ascii=False), file=sys.stderr, flush=True)
                print(f"[video-frames-ready] {len(frames)} frames in {frames_dir} — safe to read now "
                      f"while transcription continues.", file=sys.stderr, flush=True)
            else:
                print("[warn] no key frames extracted (need ffmpeg).", file=sys.stderr, flush=True)
            return frames

        executor = ThreadPoolExecutor(max_workers=1)
        frame_future = executor.submit(grab_and_report)
        print(f"[info] video detected — grabbing {args.frames} key frames in parallel …", file=sys.stderr, flush=True)

    model_dir = resolve_model_dir(args.model_dir)
    print(f"[info] loading SenseVoice int8 from {model_dir} …", file=sys.stderr)
    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=os.path.join(model_dir, "model.int8.onnx"),
        tokens=os.path.join(model_dir, "tokens.txt"),
        num_threads=args.num_threads,
        use_itn=True,                       # punctuation + inverse text normalization
        language="" if args.lang == "auto" else args.lang,
        debug=False,
    )

    print(f"[info] decoding audio: {args.audio} …", file=sys.stderr)
    samples = load_audio(args.audio)

    if args.vad:
        text = transcribe_with_vad(recognizer, samples, args.vad)
    else:
        text = transcribe_whole(recognizer, samples)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[done] transcript written to {args.out}", file=sys.stderr)
    else:
        print(text)

    # Make sure the parallel frame work is finished before exiting (it already printed its results).
    if video:
        frame_future.result()
        executor.shutdown()


if __name__ == "__main__":
    main()
