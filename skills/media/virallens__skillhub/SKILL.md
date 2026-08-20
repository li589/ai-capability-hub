---
name: virallens-analyzer
description: 爆款短视频深度拆解分析 — 场景检测+语音转文字+AI视觉分析+病毒传播评分+可复用脚本模板
version: 1.0.0
author: 熵海领航
pricing:
  analysis: ¥1.99/次
---

# ViralLens 爆款视频深度分析（付费版）

AI驱动的短视频拆解工具，支持 TikTok/YouTube/B站/抖音/小红书/Instagram 等平台视频，提供完整的病毒传播分析和可执行优化建议。

## 功能说明

| 分析维度 | 内容 |
|---------|------|
| 🎬 场景检测 | PySceneDetect 自动切分 + 关键帧提取 |
| 🎤 语音转文字 | DashScope Paraformer v2，中英双语 |
| 👁️ 视觉分析 | Qwen-VL 多模态分析：风格/色彩/构图/文字覆盖 |
| 📊 病毒评分 | 0-100分，含 Hook 类型/内容结构/情绪曲线 |
| 🎯 受众画像 | 人口统计/痛点/购买信号 |
| 💡 优化建议 | 10+条可执行建议，按优先级排序 |
| 📝 脚本模板 | 可复用的爆款脚本框架 |

## 定价

¥1.99/次 — 完整分析报告（含所有维度）

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- 已安装：可继续提供付费服务
- 未安装：向用户提示"当前 Agent 暂不支持微信支付付费能力，请安装 weixinpay 插件后再使用"，终止流程

## 工作流程

### 第一步：发起分析请求

```
POST https://meihua.astrakairos.com/virallens/api/resource
Content-Type: application/json

{
  "query": "https://www.tiktok.com/@username/video/1234567890",
  "video_url": "https://www.tiktok.com/@username/video/1234567890"
}
```

参数说明：
- `query` (必填): 视频URL或描述文字
- `video_url` (推荐): 视频直接URL
- `proxy` (可选): 下载代理URL
- `threshold` (可选): 场景检测灵敏度，默认15.0

### 第二步：处理 402 支付响应

服务返回 HTTP 402 + `WeixinPay-Required` header：

```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "支付¥1.99获取视频深度分析",
  "out_trade_no": "VL20260730...",
  "amount": "1.99",
  "preview": {
    "platform": "TikTok",
    "features": ["🎬 场景切换检测", "🎤 语音转文字", "👁️ AI视觉分析", "📊 病毒传播评分"],
    "preview_text": "即将为您深度分析TikTok视频..."
  }
}
```

Agent 应调用 `weixinpay_pay(paymentCode=<WeixinPay-Required的值>)` 完成支付。

### 第三步：重试请求（必须带订单号）

支付完成后，用 **相同的请求体** + `X-Out-Trade-No` header 重新请求：

```
POST https://meihua.astrakairos.com/virallens/api/resource
Content-Type: application/json
X-Out-Trade-No: VL20260730...

{
  "query": "https://www.tiktok.com/@username/video/1234567890",
  "video_url": "https://www.tiktok.com/@username/video/1234567890"
}
```

服务验证支付后返回 200，同时启动后台分析任务：

```json
{
  "code": "SUCCESS",
  "message": "支付成功！视频分析已开始，通常需要2-5分钟完成",
  "task_id": "VL20260730...",
  "task_status": "processing",
  "poll_url": "https://meihua.astrakairos.com/virallens/api/task/VL20260730...",
  "estimated_time": "2-5分钟"
}
```

### 第四步：轮询任务状态

分析需要 2-5 分钟，Agent 应轮询任务状态：

```
GET https://meihua.astrakairos.com/virallens/api/task/{task_id}
```

响应示例（分析中）：
```json
{
  "task_id": "VL20260730...",
  "status": "processing",
  "message": "分析中... 当前状态: downloading"
}
```

响应示例（已完成）：
```json
{
  "task_id": "VL20260730...",
  "status": "completed",
  "result": {
    "metadata": {"resolution": "1080x1920", "duration": 45.2, "fps": 30},
    "scenes": [{"index": 0, "start": 0, "end": 3.2, "duration": 3.2}, ...],
    "transcript": {"full_text": "...", "audio_type": "voiceover"},
    "visual_analysis": {"visual_style": "product demo", "color_palette": [...]},
    "insights": {
      "viral_score": 82,
      "viral_factors": ["strong hook in first 2s", ...],
      "hook_analysis": {"type": "problem_solution", "strength": 85},
      "content_structure": {"pattern": "PAS", "breakdown": [...]},
      "actionable_tips": [{"category": "hook", "tip": "...", "priority": "high"}],
      "script_template": "..."
    }
  }
}
```

### 退款处理

分析失败时系统自动退款，可能收到以下响应：

- `REFUNDED`: 服务异常，已自动退款
- `NOT_PAID`: 支付尚未完成，请稍后重试
- `FULFILL_AND_REFUND_FAILED`: 服务异常且退款失败，请联系客服

## 如何向用户展示结果

收到完整分析结果后，按以下结构呈现给用户：

1. **📊 视频概况**: 分辨率、时长、帧率、场景数量
2. **🎯 病毒评分**: 分数 + 主要传播因素
3. **🎬 Hook分析**: 类型、强度、出现时机
4. **📝 内容结构**: 使用的文案框架 (AIDA/PAS/BAB等)
5. **💡 Top 3 优化建议**: 按优先级列出最有价值的建议
6. **📋 脚本模板**: 可直接套用的脚本框架
7. **🎵 数据洞察**: 最佳时长、发布时间、标签策略

## 支持的视频平台

TikTok, YouTube, B站 (bilibili), 抖音, 小红书, Instagram, 以及任何 yt-dlp 支持的平台。
