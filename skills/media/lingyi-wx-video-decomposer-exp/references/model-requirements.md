# 模型视觉能力要求

> 何时读本文件：SKILL.md 工作流第 5 步视觉预检被拦截，或需要确认当前模型是否支持视觉时。

## 为什么必须支持视觉

本 skill 的核心是「看图」：agent 须逐张读取封面图与抽出的若干帧截图，依据画面判断脚本类型、段落结构、Hook 方式、产品展示、情绪走向、CTA 设计等。纯文本模型无法读图——遇到图片会被系统拦截（报错类似 `the current model does not support images. Content filtered.`），只能提取元数据（时长/分辨率/编码），画面分析完全无法进行，拆解报告失去意义。

## 预检守则（见 SKILL.md 工作流第 5 步）

先用 Read 工具读取第一张帧：

- **返回了画面描述** → 当前模型支持视觉，继续逐张看帧、进入写报告。
- **返回 `does not support images` / `Content filtered` 或无任何画面描述** → 当前为纯文本模型，**立即停止、不要写报告**，向用户输出：
  > 当前模型为纯文本模型，无法查看视频画面，无法完成脚本类型/段落结构/Hook/产品展示/情绪/CTA 等画面分析。本 skill 的核心是「看图拆解」，请切换到支持视觉的模型后重新运行。元数据（时长/分辨率/编码）虽能提取，但缺画面分析的拆解报告没有意义，故不予输出。

## 支持视觉的模型（示例，以各平台当前上架型号为准）

**国内常见：**

- Kimi 视觉版（如 kimi 2.6 / kimi 2.7 等 Moonshot 视觉型号）
- 通义千问 Qwen-VL / Qwen2.5-VL / Qwen3-VL（阿里）
- 智谱 GLM-4V / GLM-4.6V / GLM-4.5V
- 字节豆包 Doubao 视觉版
- 腾讯混元 vision

**国际常用：** Claude 4.x（Sonnet/Opus 等）、OpenAI GPT-4o、Google Gemini 2.x。

## 不可用的纯文本模型（举例）

DeepSeek-V3 / DeepSeek-R1、GLM 纯文本版、Qwen 纯文本版、Kimi 纯文本版等——这些无法读取图片，跑本 skill 会卡在画面分析环节。
