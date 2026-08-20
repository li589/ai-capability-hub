#!/usr/bin/env python3
"""
ViralLens Video Analyzer - Library Module
Downloads video, detects scenes, extracts audio, analyzes with LLM.
"""

import os
import sys
import json
import base64
import subprocess
import time
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────
def _get_dashscope_config():
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    base_url = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    return api_key, base_url


def write_progress(output_dir, step, message, progress=0):
    """Write progress to JSON file for frontend polling"""
    progress_file = output_dir / "progress.json"
    data = {"step": step, "message": message, "progress": progress}
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def log(msg):
    print(msg, flush=True)
    logger.info(msg)


# ── Step 1: Download ────────────────────────────────────────────
def normalize_douyin_url(url: str) -> str:
    """Convert Douyin jingxuan URL to standard video URL"""
    import re
    # https://www.douyin.com/jingxuan?modal_id=7667851693773589811
    # -> https://www.douyin.com/video/7667851693773589811
    match = re.search(r'douyin\.com/jingxuan\?modal_id=(\d+)', url)
    if match:
        video_id = match.group(1)
        return f'https://www.douyin.com/video/{video_id}'
    return url


def download_video(url: str, output_dir: Path, proxy: str = "", cookies: str = "") -> Path:
    video_path = output_dir / "source_video.mp4"
    if video_path.exists() and video_path.stat().st_size > 10000:
        log(f"[SKIP] Video already exists ({video_path.stat().st_size / 1024 / 1024:.1f}MB)")
        return video_path

    # Normalize URL
    url = normalize_douyin_url(url)
    log(f"[DOWNLOAD] {url}")
    
    cmd = ["yt-dlp", "--impersonate", "chrome",
           "-f", "best[height<=1920]/best",
           "-o", str(video_path)]
    
    # Add cookies if provided
    if cookies:
        cmd.extend(["--cookies", cookies])
    
    cmd.extend([
        "--no-playlist", "--merge-output-format", "mp4",
        "--quiet", "--no-warnings",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        url
    ])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        # Retry without quality limit
        cmd2 = ["yt-dlp", "--impersonate", "chrome", "-o", str(video_path),
                "--no-playlist", "--merge-output-format", "mp4",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"]
        if cookies:
            cmd2.extend(["--cookies", cookies])
        if proxy:
            cmd2.extend(["--proxy", proxy])
        cmd2.append(url)
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
        if result2.returncode != 0:
            raise RuntimeError(f"Download failed: {result2.stderr[:500]}")

    if not video_path.exists():
        candidates = list(output_dir.glob("source_video.*"))
        if candidates: video_path = candidates[0]
        else: raise RuntimeError("No video file found after download")

    log(f"[OK] Downloaded: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f}MB)")
    return video_path


# ── Step 2: Scene Detection ─────────────────────────────────────
def detect_scenes(video_path: Path, output_dir: Path, threshold: float = 15.0) -> list:
    log(f"[SCENES] Detecting (threshold={threshold})...")
    from scenedetect import open_video, SceneManager
    from scenedetect.detectors import ContentDetector

    video = open_video(str(video_path))
    sm = SceneManager()
    sm.add_detector(ContentDetector(threshold=threshold))
    sm.detect_scenes(video)
    scenes = sm.get_scene_list()
    log(f"[OK] {len(scenes)} scenes detected")

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    scene_data = []
    for i, (start, end) in enumerate(scenes):
        start_s = start.get_seconds()
        end_s = end.get_seconds()
        mid_s = start_s + (end_s - start_s) / 2
        frame_path = frames_dir / f"scene_{i:03d}.jpg"
        cmd = ["ffmpeg", "-ss", str(mid_s), "-i", str(video_path),
               "-vframes", "1", "-q:v", "2", str(frame_path), "-y"]
        subprocess.run(cmd, capture_output=True, timeout=30)

        scene_data.append({
            "index": i,
            "start": round(start.get_seconds(), 2),
            "end": round(end.get_seconds(), 2),
            "duration": round((end - start).get_seconds(), 2),
            "frame": str(frame_path) if frame_path.exists() else "",
        })

    with open(output_dir / "scenes.json", "w") as f:
        json.dump(scene_data, f, ensure_ascii=False, indent=2)
    return scene_data


# ── Step 3: Audio Extraction + ASR ──────────────────────────────
def extract_and_transcribe(video_path: Path, output_dir: Path) -> dict:
    log("[AUDIO] Extracting audio...")
    audio_path = output_dir / "audio.wav"
    cmd = ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
           "-ar", "16000", "-ac", "1", str(audio_path), "-y"]
    subprocess.run(cmd, capture_output=True, timeout=60)

    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        log("[WARN] No audio track found")
        return {"full_text": "", "segments": [], "language": "unknown", "audio_type": "silent"}

    log("[ASR] Transcribing with DashScope...")
    api_key, _ = _get_dashscope_config()

    try:
        import dashscope
        from dashscope.audio.asr import Transcription

        dashscope.api_key = api_key

        with open(str(audio_path), "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()

        task = Transcription.async_call(
            model='paraformer-v2',
            file_urls=[f'data:audio/wav;base64,{audio_b64}'],
            language_hints=['zh', 'en'],
            headers={'x-dashscope-data-inspection': 'disable'}
        )

        result = Transcription.wait(task.output.task_id)

        if result.output.task_status == 'SUCCEEDED':
            import requests
            url = result.output.results[0]['transcription_url']
            data = requests.get(url).json()
            full_text = data['transcripts'][0]['text']
            log(f"[OK] Transcript: {len(full_text)} chars")
            return {
                "full_text": full_text,
                "segments": [],
                "language": "auto",
                "audio_type": "voiceover" if len(full_text) > 20 else "music_only",
            }
        else:
            error_code = result.output.get('code', '')
            error_msg = result.output.get('message', '')
            log(f"[WARN] ASR failed: {error_code} - {error_msg}")
            return {"full_text": "", "segments": [], "language": "unknown", "audio_type": "asr_failed"}

    except Exception as e:
        log(f"[WARN] ASR failed: {e}")
        return {"full_text": "", "segments": [], "language": "unknown", "audio_type": "asr_failed"}


# ── Step 4: Visual Analysis ───────────────────────────────────
def analyze_frames(frames_dir: Path, max_frames: int = 12) -> dict:
    log(f"[VISION] Analyzing keyframes...")
    api_key, base_url = _get_dashscope_config()

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)

    frames = sorted(frames_dir.glob("*.jpg"))[:max_frames]
    if not frames:
        return {"visual_style": "unknown", "analysis": "No frames"}

    frames = frames[:3]
    log(f"[VISION] Using {len(frames)} frames")

    image_contents = []
    for f in frames:
        b64 = base64.b64encode(f.read_bytes()).decode()
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    prompt = """You are a viral video analysis expert. Analyze these keyframes from a short-form video.
Return JSON with these fields:
- visual_style: overall visual style
- color_palette: array of dominant colors as hex codes (max 5)
- composition: camera angles and framing patterns
- text_overlays: describe any text/captions visible
- product_visibility: how the product is shown (0-100 score)
- energy_level: visual energy/pacing (low/medium/high)
- aesthetic_quality: production quality (amateur/semi-pro/professional)
- key_visual_hooks: what visual elements grab attention in the first frames

Return ONLY valid JSON, no other text.
"""

    try:
        resp = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[{"role": "user", "content": image_contents + [{"type": "text", "text": prompt}]}],
            temperature=0.7,
            max_tokens=1500,
        )
        text = resp.choices[0].message.content
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        return {"raw": text, "visual_style": "parsed_manually"}
    except Exception as e:
        log(f"[WARN] Vision analysis failed: {e}")
        return {"error": str(e), "visual_style": "analysis_failed"}


# ── Step 5: Generate Viral Insights ─────────────────────────────
def generate_insights(scenes: list, transcript: dict, visual: dict, video_meta: dict) -> dict:
    log("[INSIGHTS] Generating viral analysis...")
    api_key, base_url = _get_dashscope_config()
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)

    scene_summary = f"{len(scenes)} scenes, avg {sum(s['duration'] for s in scenes)/max(len(scenes),1):.1f}s per scene"

    prompt = f"""You are an expert at analyzing viral short-form videos for cross-border e-commerce.
Analyze this video and provide data-driven insights.

VIDEO DATA:
- Scenes: {scene_summary}
- Duration: {video_meta.get('duration', 0):.1f}s
- Transcript: {transcript.get('full_text', 'N/A')[:2000]}
- Visual style: {visual.get('visual_style', 'N/A')}
- Color palette: {visual.get('color_palette', [])}
- Energy level: {visual.get('energy_level', 'N/A')}
- Product visibility score: {visual.get('product_visibility', 'N/A')}
- Key visual hooks: {visual.get('key_visual_hooks', 'N/A')}

Return JSON with:
{{
  "viral_score": 0-100 integer,
  "viral_factors": ["list of specific factors"],
  "hook_analysis": {{"type": "question|shocking_stat|before_after|problem_solution|story|demo", "strength": 0-100, "description": "why the hook works", "time_to_hook": "seconds"}},
  "content_structure": {{"pattern": "AIDA|PAS|BAB|4U|story_arc", "breakdown": [{{"phase": "hook|build|peak|cta", "time_range": "0-3s", "description": "..."}}]}},
  "emotional_journey": ["sequence of emotions"],
  "target_audience": {{"demographics": "age range, gender, interests", "pain_points": [], "buying_signals": []}},
  "product_strategy": {{"showcase_method": "demo|comparison|testimonial|tutorial|unboxing", "key_selling_points": [], "objection_handling": []}},
  "cta_analysis": {{"type": "link_in_bio|comment|dm|shop_now|follow", "placement": "when", "effectiveness": 0-100, "urgency_level": "none|low|medium|high"}},
  "actionable_tips": [{{"category": "hook|content|visual|audio|cta", "tip": "advice", "priority": "high|medium|low"}}],
  "script_template": "A reusable script template",
  "data_insights": {{"optimal_duration": "recommended", "best_posting_time": "windows", "hashtag_strategy": [], "music_suggestion": "style", "engagement_triggers": []}}
}}
"""

    try:
        resp = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000,
        )
        text = resp.choices[0].message.content
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        return {"raw": text}
    except Exception as e:
        log(f"[WARN] Insights generation failed: {e}")
        return {"error": str(e)}


# ── Video Metadata ──────────────────────────────────────────────
def get_video_metadata(video_path: Path) -> dict:
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,duration,nb_frames,r_frame_rate,bit_rate",
               "-of", "json", str(video_path)]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        info = json.loads(out.stdout).get("streams", [{}])[0]

        fps = 30
        if info.get("r_frame_rate"):
            parts = info["r_frame_rate"].split("/")
            fps = float(parts[0]) / float(parts[1]) if len(parts) == 2 and float(parts[1]) > 0 else 30

        return {
            "width": info.get("width", 0),
            "height": info.get("height", 0),
            "duration": float(info.get("duration", 0)),
            "fps": fps,
            "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
        }
    except Exception:
        return {"width": 0, "height": 0, "duration": 0, "fps": 30, "resolution": ""}


# ── High-level Analysis Function ────────────────────────────────
def analyze_video(url: str, output_dir: Path, proxy: str = "", threshold: float = 15.0, cookies: str = "") -> dict:
    """Complete video analysis pipeline. Returns result dict or raises Exception."""
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    start_time = time.time()

    try:
        write_progress(output_dir, "downloading", "正在下载视频...", 10)
        video_path = download_video(url, output_dir, proxy, cookies)
        write_progress(output_dir, "downloaded", "下载完成", 20)

        write_progress(output_dir, "metadata", "正在读取视频信息...", 22)
        meta = get_video_metadata(video_path)
        log(f"[META] {meta['resolution']} {meta['duration']:.1f}s {meta['fps']:.0f}fps")

        write_progress(output_dir, "scenes", "正在检测场景切换...", 30)
        scenes = detect_scenes(video_path, output_dir, threshold)
        if not scenes:
            log("[RETRY] No scenes, trying threshold=10...")
            scenes = detect_scenes(video_path, output_dir, threshold=10.0)
        write_progress(output_dir, "scenes_done", f"场景检测完成，共 {len(scenes)} 个场景", 45)

        write_progress(output_dir, "audio", "正在提取音频...", 50)
        transcript = extract_and_transcribe(video_path, output_dir)
        t_chars = len(transcript.get('full_text', ''))
        write_progress(output_dir, "audio_done",
                      f"语音转文字完成（{t_chars} 字）" if t_chars > 0 else "语音转文字完成（无语音）", 65)

        write_progress(output_dir, "vision", "正在进行视觉分析...", 70)
        visual = analyze_frames(frames_dir)
        write_progress(output_dir, "vision_done", "视觉分析完成", 80)

        write_progress(output_dir, "insights", "正在生成病毒传播分析...", 85)
        video_meta = {**meta, "url": url}
        insights = generate_insights(scenes, transcript, visual, video_meta)
        write_progress(output_dir, "insights_done", "分析完成", 95)

        result = {
            "url": url,
            "metadata": meta,
            "scenes": scenes,
            "transcript": transcript,
            "visual_analysis": visual,
            "insights": insights,
            "processing_time": round(time.time() - start_time, 1),
        }

        with open(output_dir / "analysis_result.json", "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        log(f"[DONE] Analysis complete in {result['processing_time']}s")
        log(f"  Scenes: {len(scenes)}")
        log(f"  Transcript: {len(transcript.get('full_text', ''))} chars")
        log(f"  Viral score: {insights.get('viral_score', 'N/A')}")

        return result

    except Exception as e:
        log(f"[ERROR] {e}")
        with open(output_dir / "error.json", "w") as f:
            json.dump({"error": str(e), "url": url}, f)
        raise
