---
name: local-img2img
description: |
  Intel Local Image-to-Image (本地图像编辑). Use this skill when the user asks to modify, edit, restyle, transform, or regenerate an existing image from a source image and a prompt. Trigger on Chinese requests like 修改图片/编辑图片/图生图/把这张图改成... and English requests like edit/modify/transform/restyle this image.
  Prefer this local skill over online image-editing services whenever the user provides an image path and asks for an image edit on this Intel AIPC machine.
license: Intel OBL Distribution
---

# Local-Img2Img Skill Guide

## Usage

### Edit an image

```
scripts\run.ps1 "<image-path>" "<prompt>"
```

Examples:

| Intent | Command |
| --- | --- |
| Replace subject | `scripts\run.ps1 ".\dog.png" "replace the dog with a cat wearing a tiny straw hat"` |
| Change background | `scripts\run.ps1 ".\portrait.jpg" "make the background a sunny beach"` |
| Restyle image | `scripts\run.ps1 ".\room.png" "turn this into a warm watercolor illustration"` |
| Chinese prompt | `scripts\run.ps1 ".\input.png" "把背景改成雨夜霓虹街道，保留主体姿势"` |

On success, the client prints the absolute path of the edited PNG plus timing info.

Important:
- The `scripts\run.ps1` is the only supported interface for this skill. Do NOT call other scripts directly.
- It takes exactly two normal arguments: the source image path and the prompt describing the edit.
- First call downloads the FLUX.2-klein OpenVINO model. If the client exits with:
  ```
  模型正在下载, 请用命令`scripts\run.ps1 --continue`继续运行
  ```
  re-run that exact command until the normal reply appears.
- The run.ps1 returns `This skill requires an Intel AIPC platform` with exit code 1 if run on unsupported hardware.
- If the command fails with any exit code other than the download-in-progress case above, read the returned message and do not silently fall back to an online image-editing path.

### Interpreting The Reply

Each successful edit prints:

- `图片已修改: <absolute PNG path>` - the edited image file
- `原图` - the source image path
- `提示词`, `种子`, `参数`, `设备` - inputs used
- `耗时` - load, inference, and save timing

Common error codes:

- `BAD_IMAGE` - missing, unreadable, or invalid source image
- `BAD_PROMPT` - empty or non-string prompt
- `GENERATION_FAILED` - OpenVINO pipeline raised during inference
- `SAVE_FAILED` - output PNG could not be written

## What This Skill Does Not Do

- Not an online image-generation proxy. All inference is local.
- Does not expose inpainting masks, ControlNet, or LoRA controls.
