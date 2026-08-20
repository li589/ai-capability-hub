# douyin-remotion-template

抖音短视频 Remotion 渲染模板（douyin-video-skill 下游渲染通道之一）。

## 能力

- 9:16 / 1:1 / 16:9 多尺寸
- 按 `shot_plan` 自动切镜
- 底部字幕条 + 片头标题 + AI 标识埋点
- 接收 `image_map` 产出的图片作为分镜画面

## 快速开始

```bash
cd templates/remotion
npm install

# 预览
npm run studio

# 渲染（默认 12s 占位）
npm run render

# 带真实数据渲染
npm run render:props
```

## 数据格式

运行前把 `props.json` 放在项目根目录，格式：

```json
{
  "shots": [
    {
      "beat": 0,
      "visual_prompt": "主播特写、手指向前勾引动作",
      "source": "ai_gen",
      "duration_sec": 3.0,
      "image": "beat_0.png",
      "caption": "今天教你三招"
    }
  ],
  "audioFile": "audio.wav",
  "totalDurationSec": 12,
  "aspectRatio": "9:16",
  "aiLabelConfig": {
    "mode": "overlay",
    "duration_sec": 3,
    "text": "本视频含 AI 生成内容"
  },
  "title": "三招提升完播率"
}
```

图片/音频文件放在 `public/` 下，`image` / `audioFile` 只写文件名。

## 与 video-render-engine 的接口

```python
render(
    audio_path="out.wav",
    channel="remotion",
    shots=shot_plan,
    aspect_ratio="9:16",
    ai_label_config={"mode": "overlay", "duration_sec": 3}
)
```
