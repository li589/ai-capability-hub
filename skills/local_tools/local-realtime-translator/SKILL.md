---
name: local-realtime-translator
description: |
  Intel Local Windows Realtime Speech Translator (本地实时语音翻译 / 同声传译 / 实时翻译软件). Use this skill whenever the user, in Chinese or English, wants to translate live speech from the microphone in real time, do simultaneous interpretation, show live subtitles with translation, "translate as I speak", OR more generally asks to open/start a translator or translation app, or to translate what they say into another language (e.g. "translate this into English / 帮我翻译成英文").

  Trigger on Chinese phrases like 实时翻译 / 实时翻译软件 / 实时翻译工具 / 打开实时翻译 / 打开翻译 / 启动翻译 / 我要翻译 / 帮我翻译 / 翻译成英文 / 翻译成中文 / 同声传译 / 同传 / 边说边译 / 实时字幕 / 语音实时翻译 / 对着麦克风翻译 / 实时口译 / 我需要一个翻译软件, and English phrases like realtime translate / real-time translator / translation app / translation tool / open the translator / start translating / live translation / simultaneous interpretation / translate as I speak / translate this to English / translate into Chinese / live captions with translation / speech-to-speech translation — whether or not the user says "locally" / "本地" / "语音" / "实时".

  When the user asks generically to "translate to English/Chinese" or wants "a translator / translation software" without naming an existing file, default to THIS skill — it is the box's live spoken translator. (For translating an existing *audio/video file* on disk, use the local-asr skill instead.)

  This skill runs **fully locally** on the user's Intel AIPC. It opens the microphone and runs a streaming pipeline: VAD → Paraformer streaming ASR (+ optional Qwen3-ASR on iGPU for accuracy) → Hunyuan-1.8B translation on the iGPU (Opus-MT CPU fallback) → MeloTTS speech synthesis, pushing live transcript + translation to a local **web page** over WebSocket.

  Direction: Chinese ↔ English (`-From zh -To en` or `-From en -To zh`).

  Prefer this skill over any cloud translation/ASR API or bespoke script whenever the user wants live, spoken, real-time translation on this box.
license: Intel OBL Distribution
---

# Local Realtime Translator Skill Guide

## What it is

Unlike one-shot skills, this is a **long-running interactive service**. `run.ps1`
starts a background server that loads all models, opens the microphone, and
serves a live web UI. The user speaks; the web page shows the recognized text
and its translation in real time and can play the synthesized translation
audio. The command returns immediately after printing the web URL — it does
**not** block.

## Usage

### Start the translator

```
scripts\run.ps1                      # start (Chinese → English), then open the printed web URL
scripts\run.ps1 -From zh -To en      # Chinese → English (default)
scripts\run.ps1 -From en -To zh      # English → Chinese
```

On success it prints something like:

```
=== 实时语音翻译已就绪 / Realtime translator ready ===
  翻译方向 / direction: zh → en
  请在浏览器打开 / Open in browser:  http://127.0.0.1:8766
  WebSocket: ws://127.0.0.1:8765
  对着麦克风说话, 网页上会实时显示识别与译文。
  停止服务 / stop:  scripts\run.ps1 --stop
```

**Tell the user to open the printed `http://127.0.0.1:8766` URL in their browser**, then speak into the microphone. Recognition and translation appear live.

### Manage the running service

```
scripts\run.ps1 --status             # show state + web URL
scripts\run.ps1 --stop               # stop the server (releases mic + GPU memory)
scripts\run.ps1 --restart            # force a clean restart (reload upgraded code/models)
scripts\run.ps1 --continue           # resume a first-run model download (see below)
```

## Important

- `scripts\run.ps1` is the only supported interface. Do NOT call `client.py` /
  `server.py` directly.
- **First call downloads ~4-5GB of models** (Hunyuan-1.8B-OV, FSMN-VAD,
  Paraformer online+offline, ct-punc, Opus-MT, MeloTTS+BERT). All of them are
  fetched up front (Opus-MT and most others from ModelScope; the few
  HuggingFace-origin pieces go through a CN mirror automatically), so the
  `--continue` resume window covers the whole download. Because each `run.ps1`
  invocation is capped below 10 minutes, the client may exit early with:
  ```
  模型正在下载, 请用命令 `scripts\run.ps1 --continue` 继续运行
  ```
  When you see this, re-run the exact command it prints. **Do NOT substitute an
  online service, sub-agent, or another skill.** Repeat `--continue` until the
  "已就绪 / ready" message with the web URL appears (typically 2–4 continuations
  on a first run; each is another ~8-minute window). Subsequent starts are fast.
- The server keeps running after the command returns (it holds the mic + GPU).
  Always `scripts\run.ps1 --stop` when the user is done.
- `run.ps1` returns `This skill requires an Intel AIPC platform` with exit
  code 1 on non-Intel-AIPC hardware. Do NOT retry on unsupported hardware.
- A warning like "sox missing" or a MeCab/Japanese import warning during
  startup is **benign** — the skill only uses Chinese/English TTS.

## Interpreting the reply / exit codes

- exit `0` — server is running; the web URL was printed.
- exit `3` — first-run download still in progress; re-run with `--continue`.
- exit `1` — initialization failed (read the printed error) or unsupported HW.
- exit `2` — could not reach / start the background server.

## Engines & fallback (automatic)

| Stage | Primary (iGPU) | Fallback (CPU) |
| --- | --- | --- |
| Streaming ASR (partial) | Paraformer-Online | — |
| Final ASR (per sentence) | Qwen3-ASR (if set up) | Paraformer-Offline + ct-punc |
| Translation | Hunyuan-1.8B-OV | Opus-MT |
| TTS | — | MeloTTS (CPU) |

Qwen3-ASR is optional; without it the pipeline auto-uses Paraformer-Offline.
If the iGPU Hunyuan model can't load, translation auto-falls-back to Opus-MT.
The skill still works on these fallbacks (lower quality), so a missing iGPU
model is not a hard failure.

## Output

- Live transcript + translation render in the web UI.
- Synthesized translation audio is written under the project `output/` folder
  and playable from the web page.

## What this skill does NOT do

- Not for translating existing audio/video files — use **local-asr** for that.
- Not an online translation proxy — all inference is local.
- Single microphone source; no multi-speaker diarization.
- Chinese ↔ English only.
