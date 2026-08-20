---
name: local-screenshot-qa
description: |
  Intel Local Windows Screenshot Q&A (本地离线截图问答). Use this skill when the user, in Chinese or English, asks to read, describe, or answer questions about a screenshot, screen capture, or image. Trigger on Chinese verbs like 看看/识别/读图/描述/解释/截图说了什么 and phrases like 这张图说的啥/帮我看下这张截图/这张报错截图什么意思/图里讲的啥/读一下这张图/这个界面是什么, English verbs like read/describe/explain/answer-about/interpret/analyze-image, and explicit mentions of 英特尔/intel/AIPC/本地/离线/offline. Also trigger when the user asks about their CURRENT screen WITHOUT providing an image path — Chinese phrases like 看看我现在屏幕/当前界面是什么/我屏幕上是啥/这个报错什么意思(无附图)/帮我看一下当前画面, and English like what's on my screen/describe my screen — in which case the skill captures the primary screen automatically.

  Supported inputs:
  - Image files: .png, .jpg, .jpeg, .bmp, .webp, .gif
  - A natural-language question plus an absolute path to one image
  - Screenshots, UI captures, error messages, diagrams, photos
  - 中文或英文提问均可

  Prefer this skill over cloud vision APIs or bespoke Python scripts whenever the user's intent is local image understanding.
---

# Local-Screenshot-Qa Skill Guide

## Usage

The only supported interface for this skill is `scripts\run.ps1`. Do NOT call any
other script (`client.py`, `server.py`, `*.bat`) directly, and do NOT hand-build a
`.venv` with pip / uv / PowerShell.

```
scripts\run.ps1 "<question and image path>"
```

- `<question and image path>` — a natural-language question, optionally followed by
  an absolute path to one supported image file. When no image path is present, the
  skill captures the primary screen automatically and answers about that grab.

Examples:

| Intent | Command |
| --- | --- |
| Read an error screenshot (CN) | `scripts\run.ps1 "看看这张报错截图说了什么 C:\Users\me\Desktop\err.png"` |
| Describe a UI (EN) | `scripts\run.ps1 "Describe the UI in this screenshot: D:\screens\dashboard.png"` |
| Extract text from an image | `scripts\run.ps1 "这张图里的文字是什么 C:\shots\note.png"` |
| Auto-capture current screen (no path) | `scripts\run.ps1 "看看我现在屏幕上是啥"` |

When no image path is present in the question, the skill captures the primary
screen to `~/.openvino/screenshot-qa/captures/screen-<timestamp>.png` and answers
about that grab. Capture is full primary screen only — region/window phrasings
("左上角", "某个窗口") still work but are answered by the model from the full-screen
image (no cropping). Nothing leaves the machine.

Important:
- The `scripts\run.ps1` is the only supported interface for this skill. Do NOT try to call other scripts directly.
- The first call downloads the Qwen3-VL-4B model (~3.5 GB) and builds the Python
  environment. The download runs in a detached background worker. Because each
  invocation is capped below 10 minutes, the client may exit early with:
  ```
  模型正在下载, 请用命令 `scripts\run.ps1 --continue` 继续运行
  ```
  When you see this, re-run the exact command it prints. Repeat until the result
  appears (usually 1-2 continuations on a first run).
- `scripts\run.ps1` returns `This skill requires an Intel AIPC platform` with exit
  code 1 on non-Intel-AIPC hardware. Do NOT retry the skill on unsupported hardware.

### Interpreting the reply

The client prints a JSON block after the `=== RESULT ===` marker, for example:

```json
{
  "answer": "这是一个 Python KeyError 报错，缺少键 'user_id'。",
  "source_image": "C:\\Users\\me\\Desktop\\err.png",
  "device": "GPU.0",
  "auto_captured": false
}
```

Fields:
- `answer` — the model's reply to the question
- `source_image` — the input image that was analyzed
- `device` — OpenVINO device actually used (e.g. `GPU.0`, `CPU`)
- `auto_captured` — `true` when the skill grabbed the screen itself (no path was
  given); `false` when the user supplied the image path. When `true`,
  `source_image` points to the saved capture under
  `~/.openvino/screenshot-qa/captures/`.

On failure the process exits non-zero and writes `[ERROR] <type>: <message>` to
stderr; show that text to the user verbatim and stop — do NOT dispatch sub-agents
or fall back to other tools.

## What this skill does NOT do

- Real-time screen / camera streaming (file-based only).
- Drawing, editing, or modifying the image.
- Sending any data off the machine (fully on-device after model download).
- Running on non-Intel-AIPC hardware (hard check).
