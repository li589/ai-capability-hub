# ViralLens 爆款视频分析 Pay Skill

AI驱动的短视频拆解工具，支持 TikTok/YouTube/B站/抖音/小红书/Instagram 等平台视频深度分析。

## 功能

- 🎬 **场景检测**: PySceneDetect 自动切分 + 关键帧提取
- 🎤 **语音转文字**: DashScope Paraformer v2，中英双语
- 👁️ **AI视觉分析**: Qwen-VL 多模态分析：风格/色彩/构图/文字覆盖
- 📊 **病毒传播评分**: 0-100分 + Hook分析 + 内容结构拆解
- 💡 **优化建议**: 10+条可执行建议
- 📝 **脚本模板**: 可复用的爆款脚本框架

## 技术栈

- FastAPI + BackgroundTasks (异步任务)
- yt-dlp (视频下载)
- PySceneDetect (场景检测)
- ffmpeg/ffprobe (音视频处理)
- DashScope (ASR + Vision + LLM)
- 微信支付 V3 + SkillHub X402 协议

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 系统依赖 (需要预装)
# - ffmpeg
# - yt-dlp

# Mock 模式 (无需微信支付配置)
SKILLPAY_MODE=mock uvicorn app.main:app --port 8090

# Live 模式
cp .env.example .env
# 编辑 .env 填入真实配置
SKILLPAY_MODE=live uvicorn app.main:app --port 8090
```

## API 接口

### POST /api/resource
发起视频分析（首次请求返回 402，支付后重试返回 200 + 启动后台任务）

### GET /api/task/{task_id}
轮询分析任务状态（processing → completed / failed）

### GET /api/health
健康检查

## 系统依赖

服务器需要预装：
- `ffmpeg` / `ffprobe` (音视频处理)
- `yt-dlp` (视频下载)
