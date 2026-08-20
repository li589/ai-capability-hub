---
name: free-video-cutter-online
version: 1.0.0
displayName: Free Video Cutter Online — Cut and Export Video Clips
description: |
  Get 1080p MP4 files from your video clips using this free-video-cutter-online tool. It runs video trimming and cutting on cloud GPUs, so your machine does zero heavy lifting. content creators and casual users can removing unwanted sections from video recordings in roughly 20-40 seconds — supports MP4, MOV, AVI, WebM.
metadata:
  openclaw:
    emoji: ✂️
    requires:
      env:
        - NEMO_TOKEN
      configPaths:
        - ~/.config/nemovideo/
    primaryEnv: NEMO_TOKEN
    variant: short_prompts
install_source: official
install_method: download
skill_id: official_Yi8iQYfs
enabled_at: 1787232749101
name_zh: 免费在线视频剪辑器
---

## Getting Started

> Got a video clips for me? Send it over and I'll handle the video trimming and cutting. Or just describe what you need.

**Try saying:**
- "trim my video clips"
- "export 1080p MP4"
- "cut out the first 2 minutes"

### First-Time Connection

When a user first opens this skill, connect to the processing backend automatically. Briefly let them know (e.g. "Setting up...").

**Authentication**: Check if `NEMO_TOKEN` is set in the environment. If it is, skip to step 2.

1. **Obtain a free token**: Generate a random UUID as client identifier. POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with header `X-Client-Id` set to that UUID. The response `data.token` is your NEMO_TOKEN — 100 free credits, valid 7 days.
2. **Create a session**: POST to `https://mega-api-prod.nemovideo.ai/api/tasks/me/with-session/nemo_agent` with `Authorization: Bearer <token>`, `Content-Type: application/json`, and body `{"task_name":"project","language":"<detected>"}`. Store the returned `session_id` for all subsequent requests.

Keep setup communication brief. Don't display raw API responses or token values to the user.

# Free Video Cutter Online — What You Get

This does video trimming and cutting for video clips. Everything runs server-side.

A quick walkthrough: upload a 10-minute interview recording → ask for cut out the first 2 minutes and trim the ending after the 7-minute mark → wait roughly 20-40 seconds → download your MP4 at 1080p. The backend handles rendering, encoding, all of it.

Fair warning — shorter clips process faster — split long videos before uploading if possible.

## Routing Cut and Export Requests

When you paste a video URL or upload a file and set in/out timestamps, the request routes to the trim action handler, which queues a clip export job with your specified start time, end time, and output format (MP4, WebM, or GIF).

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## Cloud Render Pipeline Details

Each trim job runs on a cloud GPU instance that decodes only the keyframe range you selected, re-encodes the output using H.264 at your chosen bitrate, and stores the result in a temporary S3 bucket for 24 hours. Files over 2GB fall back to CPU-based FFmpeg processing, which increases render time by roughly 3–5x.

All calls go to `https://mega-api-prod.nemovideo.ai`. The main endpoints:

1. **Session** — `POST /api/tasks/me/with-session/nemo_agent` with `{"task_name":"project","language":"<lang>"}`. Gives you a `session_id`.
2. **Chat (SSE)** — `POST /run_sse` with `session_id` and your message in `new_message.parts[0].text`. Set `Accept: text/event-stream`. Up to 15 min.
3. **Upload** — `POST /api/upload-video/nemo_agent/me/<sid>` — multipart file or JSON with URLs.
4. **Credits** — `GET /api/credits/balance/simple` — returns `available`, `frozen`, `total`.
5. **State** — `GET /api/state/nemo_agent/me/<sid>/latest` — current draft and media info.
6. **Export** — `POST /api/render/proxy/lambda` with render ID and draft JSON. Poll `GET /api/render/proxy/lambda/<id>` every 30s for `completed` status and download URL.

Formats: mp4, mov, avi, webm, mkv, jpg, png, gif, webp, mp3, wav, m4a, aac.

Headers are derived from this file's YAML frontmatter. `X-Skill-Source` is `free-video-cutter-online`, `X-Skill-Version` comes from the `version` field, and `X-Skill-Platform` is detected from the install path (`~/.clawhub/` = `clawhub`, `~/.cursor/skills/` = `cursor`, otherwise `unknown`).

Include `Authorization: Bearer <NEMO_TOKEN>` and all attribution headers on every request — omitting them triggers a 402 on export.

**Draft field mapping**: `t`=tracks, `tt`=track type (0=video, 1=audio, 7=text), `sg`=segments, `d`=duration(ms), `m`=metadata.

```
Timeline (3 tracks): 1. Video: city timelapse (0-10s) 2. BGM: Lo-fi (0-10s, 35%) 3. Title: "Urban Dreams" (0-3s)
```

### Translating GUI Instructions

The backend responds as if there's a visual interface. Map its instructions to API calls:

- "click" or "点击" → execute the action via the relevant endpoint
- "open" or "打开" → query session state to get the data
- "drag/drop" or "拖拽" → send the edit command through SSE
- "preview in timeline" → show a text summary of current tracks
- "Export" or "导出" → run the export workflow

### SSE Event Handling

| Event | Action |
|-------|--------|
| Text response | Apply GUI translation (§4), present to user |
| Tool call/result | Process internally, don't forward |
| `heartbeat` / empty `data:` | Keep waiting. Every 2 min: "⏳ Still working..." |
| Stream closes | Process final response |

~30% of editing operations return no text in the SSE stream. When this happens: poll session state to verify the edit was applied, then summarize changes to the user.

### Error Codes

- `0` — success, continue normally
- `1001` — token expired or invalid; re-acquire via `/api/auth/anonymous-token`
- `1002` — session not found; create a new one
- `2001` — out of credits; anonymous users get a registration link with `?bind=<id>`, registered users top up
- `4001` — unsupported file type; show accepted formats
- `4002` — file too large; suggest compressing or trimming
- `400` — missing `X-Client-Id`; generate one and retry
- `402` — free plan export blocked; not a credit issue, subscription tier
- `429` — rate limited; wait 30s and retry once

## FAQ

**What resolution can I grab?** Up to 1080p. Input quality matters though — garbage in, garbage out.

**Can I use this on my phone footage?** Yes. Vertical (9:16), horizontal (16:9), square — all work. Just upload and specify what you want.

**Credits?** 100 free to start. Most operations cost 1-5 credits depending on video length.

## Best Practices

Use source footage in MP4, MOV, AVI, WebM format for best compatibility. 1080p input gives the cleanest results but 720p works fine too.

Be specific with your requests — "add upbeat background music at 30% volume" beats "add some music". The AI works better with concrete details.

Export as MP4 for widest compatibility across devices and platforms.

## Quick Start Guide

First time? Just upload a video clips and describe what you need. I'll run it through NemoVideo's backend and hand you back a 1080p MP4.

Processing takes about 20-40 seconds depending on video length. You start with 100 free credits — most edits cost 1-3.
