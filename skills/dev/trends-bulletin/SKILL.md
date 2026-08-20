---
name: trends-bulletin
description: 多平台热词速报，采集 HuggingFace、GitHub、Hacker News、Product Hunt、Reddit、YouTube 6 个平台的热门趋势并推送到 Telegram。当用户提到热词速报、趋势推送、多平台趋势、trends bulletin 时使用此 skill。
metadata:
  author: iamzhihuix
  version: 1.0.0
install_source: official
install_method: download
skill_id: official_I3Ro7yjD
enabled_at: 1787232951233
version: 1.0.0
name_zh: 趋势公告
---

# 多平台热词速报

一键采集 6 个平台热门趋势，格式化后推送到 Telegram。

## 依赖

使用 Bun 运行时内置 fetch，无需安装额外依赖。

## 环境变量

必须配置以下环境变量（或在 `.env` 文件中设置）：

| 变量 | 必须 | 说明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | 是 | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 是 | Telegram 目标 Chat ID |
| `GROK_API_KEY` | 否 | xAI Grok API Key（为空则跳过 AI 趋势分析） |
| `PRODUCT_HUNT_TOKEN` | 否 | Product Hunt API Token（为空则跳过 PH） |
| `YOUTUBE_API_KEY` | 否 | YouTube Data API Key（为空则跳过 YouTube） |

## 执行

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `{baseDir}`
2. Script path = `{baseDir}/scripts/main.ts`
3. Replace all `{baseDir}` in this document with the actual path
4. Resolve `${BUN_X}` runtime: if `bun` installed → `bun`; if `npx` available → `npx -y bun`; else suggest installing bun

```bash
${BUN_X} run {baseDir}/scripts/main.ts
```

指定 `.env` 文件路径：

```bash
${BUN_X} --env-file=/path/to/.env run {baseDir}/scripts/main.ts
```

Dry-run 模式（只打印不发送）：

```bash
${BUN_X} run {baseDir}/scripts/main.ts --dry-run
```

## 输出格式

按平台分组推送到 Telegram，顶部附带 AI 分析的三大关键趋势（需配置 GROK_API_KEY）：

```
🔥 热词速报

━━━ 🎯 三大关键趋势 ━━━

1️⃣ AI代理兴起
💡 核心观点：AI代理技术正推动自动化任务执行
📊 关键数据：GitHub BitNet 今日+2149⭐
❗ 为什么重要：降低部署成本，促进广泛应用
🔗 https://github.com/microsoft/BitNet

━━━ HuggingFace Spaces ━━━
1. microsoft/TRELLIS.2 (🔥315)
2. Qwen/Qwen-Image-Layered (🔥264)

━━━ 每日论文 ━━━
1. SWE-EVO: Benchmarking... (👍3)

━━━ Hacker News ━━━
1. Python 3.15's interpreter... (🔥102 | 💬23)

━━━ Product Hunt ━━━
1. DiffSense (🔺211)

━━━ Reddit 热帖 ━━━
1. [r/singularity] GPT-5.2 Pro... (🔺346 | 💬83)

━━━ GitHub Trending ━━━
1. rendercv/rendercv ⭐+1,797 Python
```

## 自定义

脚本支持通过环境变量自定义：

- `REDDIT_SUBS` - Reddit 子版列表，逗号分隔（默认：`MachineLearning,LocalLLaMA,artificial,ChatGPT,singularity`）
- `ITEMS_PER_PLATFORM` - 每个平台展示条数（默认：`5`）

## 示例

用户请求：
```
帮我发一下热词速报
```

执行流程：
1. 检查环境变量是否配置（TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID）
2. 执行 `${BUN_X} run {baseDir}/scripts/main.ts`
3. 确认 Telegram 发送结果
