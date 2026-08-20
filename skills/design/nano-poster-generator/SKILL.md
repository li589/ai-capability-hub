---
name: poster-generator
description: |
  Generate high-quality posters using AI. Use this skill when the user wants to: create a poster, design a poster, make an event poster, promotional poster, social media graphic, movie-style poster, educational poster, motivational poster, or any visual poster/banner. Also trigger when the user mentions 海报, 生成海报, 活动海报, 宣传海报, 社交媒体图, 电影海报, 励志海报, 教育海报, or 横幅设计. Handles the full workflow: requirement gathering, style selection, AI image generation via NANO-BANANA/Gemini, and post-processing for various output sizes.
emoji: 🎨
metadata:
  openclaw:
    requires:
      bins:
        - python3
    primaryEnv: NANO_BANANA_ACCESS_KEY
    install:
      - kind: uv
        package: requests
      - kind: uv
        package: Pillow
      - kind: uv
        package: PyYAML
install_source: official
install_method: download
skill_id: official_ljVX9Yko
enabled_at: 1787232125232
version: 1.0.0
name_zh: 海报生成器
---

# Poster Generator

Generate high-quality posters using AI (NANO-BANANA / Gemini 3 Pro Image Preview).


## Setup

Set all 4 environment variables before use (all required):

```bash
export NANO_BANANA_ACCESS_KEY="your-access-key"
export NANO_BANANA_SECRET_KEY="your-secret-key"
```

Also set the API URL (required):

```bash
export NANO_BANANA_API_URL="https://your-api-server/task/v1/submit"
export NANO_BANANA_STATUS_URL="https://your-api-server/task/v1/status/{task_id}"
```


## Overview

- **API**: NANO-BANANA (Gemini 3 Pro Image Preview) — async submit/poll/download
- **Poster Types**: event, promotional, social_media, movie, educational, motivational, generic
- **Styles**: minimalist, retro, cyberpunk, watercolor, corporate, bold_modern, japanese_anime, chinese_traditional
- **Output Sizes**: Print (A4, A3, movie poster), Social (Instagram, Facebook, Twitter, 小红书), General (widescreen, square, portrait)
- **Languages**: English, Chinese, Bilingual
- **Variants**: Generate 1-4 design variations per poster
- **Smart Defaults**: Auto-fill missing fields based on poster type

## Prerequisites

```bash
pip3 install -r requirements.txt
```

## Style Presets & AVOID Constraints

每种风格都内置 AVOID 负面约束，确保生成质量：

| Preset | Description | Best For | AVOID |
|--------|-------------|----------|-------|
| `minimalist` | 干净留白，瑞士/包豪斯 | 教育、企业、现代品牌 | 杂乱、渐变、过多装饰、复杂纹理 |
| `retro` | 70-80 年代怀旧暖色 | 音乐活动、复古主题 | 冷色调、极简、科技感、霓虹 |
| `cyberpunk` | 暗底霓虹光效、未来感 | 科幻电影、科技活动 | 柔和色、水彩、自然元素、暖调 |
| `watercolor` | 柔和水彩、有机手感 | 励志、艺术、婚礼 | 尖锐几何、霓虹、金属质感、像素 |
| `corporate` | 专业网格、权威信赖 | 商务会议、公司宣传 | 手绘、涂鸦、霓虹、卡通 |
| `bold_modern` | 超大字体、强色块 | 社交媒体、促销 | 留白过多、细线条、柔和色 |
| `japanese_anime` | 动漫插画、高能构图 | 动漫活动、年轻受众 | 写实摄影、水墨、商务风 |
| `chinese_traditional` | 国风水墨、书法印章 | 中国传统节日、文化活动 | 赛博朋克、霓虹、西式排版 |

## Output Sizes

| Category | Preset | Dimensions | Use Case |
|----------|--------|------------|----------|
| Print | `a4_portrait` | 2480x3508 | 打印海报 |
| Print | `a3_portrait` | 3508x4961 | 大幅打印 |
| Print | `movie_poster` | 2700x4000 | 电影海报 |
| Social | `instagram_square` | 1080x1080 | IG 方图 |
| Social | `instagram_story` | 1080x1920 | IG Story/Reels |
| Social | `instagram_portrait` | 1080x1350 | IG 竖图 |
| Social | `facebook_post` | 1200x630 | Facebook |
| Social | `twitter_post` | 1600x900 | Twitter/X |
| Social | `xiaohongshu` | 1080x1440 | 小红书 |
| General | `widescreen` | 1920x1080 | 横屏展示 |
| General | `square` | 2000x2000 | 通用方图 |
| General | `portrait_2x3` | 2000x3000 | 通用竖图 (default) |
| General | `portrait_3x4` | 2000x2667 | 通用竖图 |
| Custom | `WxH` | 自定义 | 如 `1080x1920` |

---

## Smart Defaults

根据 `poster_type` 自动推荐缺失字段：

| poster_type | 推荐风格 | 默认尺寸 | 布局 | 标题位置 |
|-------------|---------|---------|------|---------|
| event | retro | a3_portrait | 三段式 | upper third |
| promotional | bold_modern | portrait_2x3 | 对角不对称 | upper third |
| social_media | bold_modern | instagram_square | 居中 | center |
| movie | cyberpunk | movie_poster | 居中纵向 | lower third |
| educational | minimalist | a3_portrait | 网格分区 | top |
| motivational | watercolor | portrait_2x3 | 居中纵向 | center |
| generic | minimalist | portrait_2x3 | 居中纵向 | upper third |

**用户只需提供 `title` + `poster_type`，以下字段全部自动填充：**
- `style_preset` — 风格预设
- `output_size` — 输出尺寸
- `layout_strategy` — 布局策略
- `title_position` — 标题位置
- `visual_elements` — 视觉元素描述
- `color_palette` — 配色方案（primary ~50-60%, secondary ~25-30%, accent ~10-15%）

---

## Workflow

### Phase 0 — 理解需求

根据用户输入完整度分三层处理：

**Tier 1 — 最简输入**（如 "做一张海报"）

使用 AskUserQuestion 批量提问（最多 3 个问题）：

1. **海报主题**（开放式）：这张海报是关于什么的？
2. **使用场景**：

| 选项 | 说明 | 对应 poster_type |
|------|------|-----------------|
| 线下活动/演出 | 音乐会、展览、派对 | event |
| 商业推广 | 产品、服务、促销 | promotional |
| 社交媒体发布 | IG/朋友圈/小红书 | social_media |
| 影视/娱乐 | 电影、游戏 | movie |
| 教育/知识传播 | 课堂、培训 | educational |
| 励志/装饰 | 名言、格言 | motivational |

3. **视觉风格偏好**：让我推荐 / 极简 / 复古 / 赛博朋克 / 水彩 / 大胆现代 / 日系动漫 / 国风传统 / 商务专业

**Tier 2 — 部分输入**（如 "爵士音乐节海报"）

用户已提供主题/类型 → 自动推断 poster_type → 用 Smart Defaults 填充 → **跳过 Phase 0，直接进入 Phase 1 确认**。

**Tier 3 — 完整输入**（用户提供详细 JSON 或所有字段）

直接进入 Phase 1 确认。

**核心原则：首次生成前最多问 3 个问题。能推断的不要问。**

---

### Phase 1 — 确认配置

展示完整的生成配置摘要，让用户确认或修改：

```
海报: Summer Jazz Festival 2026
类型: event → 推荐风格: retro
尺寸: A3 Portrait (3508x4961)
语言: English
变体数: 2

标题: "SUMMER JAZZ FESTIVAL 2026"
副标题: "A Night of Smooth Rhythms"
视觉: saxophone player silhouette, jazz club ambiance, warm stage lights
配色: #D84315 (主) + #FFF8E1 (辅) + #4E342E (强调)
CTA: "Buy Tickets at jazzfest.com"
```

使用 AskUserQuestion："确认以上配置？或选择要修改的部分。"

---

### Phase 2 — 生成海报

#### Step 2a: 写入 poster spec JSON

```bash
cat > /tmp/poster_spec.json << 'POSTER_JSON'
{
    "title": "...",
    "subtitle": "...",
    "poster_type": "...",
    "text_elements": [...],
    "visual_elements": "...",
    "style_preset": "...",
    "color_palette": ["#...", "#...", "#..."],
    "output_size": "...",
    "language": "...",
    "reference_image_url": "",
    "variants": 2
}
POSTER_JSON
```

#### Step 2b: Dry run（推荐）

```bash
python3 scripts/generate_poster.py --from-json /tmp/poster_spec.json --dry-run
```

**Dry-run 检查清单：**
- [ ] 颜色指令包含 hex 值和覆盖率百分比
- [ ] AVOID 约束存在且与风格一致
- [ ] 文字渲染规则已注入（大写、留白、错误时跳过）
- [ ] 类型专属变体指令已生成（不同构图/色调/焦点）
- [ ] 无未替换的变量（如 `{title}` 残留）

**如果 dry-run 输出存在上述任何问题，修改 poster_spec.json 后重新 dry-run，不要将质量不达标的 prompt 发给 API。**

#### Step 2c: 生成

```bash
python3 scripts/generate_poster.py --from-json /tmp/poster_spec.json -v
```

---

### Phase 3 — 审查与迭代

1. **读取生成的图片**：使用 Read 工具查看 `output/posters/<slug>/`
2. **检查文字渲染**：重点检查标题拼写
3. **提供迭代选项**：

使用 AskUserQuestion 询问用户：

| 选项 | 说明 |
|------|------|
| 满意，全部保留 | 完成任务 |
| 重新生成（文字有误） | 减少文字量后重试 |
| 换一个风格 | 改用其他风格预设 |
| 调整内容后重新生成 | 修改标题/视觉/颜色 |
| 生成更多变体 | 追加不同构图变体 |
| 换一个尺寸 | 适配不同平台 |

Output: `output/posters/<slug>/`

---

## Variant Strategies

变体使用类型专属策略（非通用随机）：

| poster_type | 变体差异维度 |
|-------------|------------|
| event | 构图变化（三段式 / 对角 / 居中）+ 配色移位 |
| promotional | 焦点切换（产品为主 / 文字为主 / 场景为主） |
| social_media | 文字比例变化（大标题 / 图片为主 / 均衡） |
| movie | 光影方向（顶光 / 侧光 / 背光）+ 角色焦点 |
| educational | 布局网格变化（2栏 / 3栏 / 自由流） |
| motivational | 背景氛围变化（自然 / 抽象 / 纯色） |

---

## 文字渲染最佳实践

### 英文
- 标题控制在 **1-4 个单词**
- 优先 **全大写** (UPPERCASE)
- 图中只保留 **标题 + CTA**，其他后期叠加
- 使用 `wide letter-spacing` 增加可读性

### 中文
- 限制 **4-6 个字**
- 用 **黑体/粗体**（笔画粗，渲染成功率最高）
- 避免繁体字和生僻字
- 双语海报建议分别生成中英版本

### 通用
- 文字错误时宁可留白（prompt 已含此指令）
- 多生成变体（`--variants 3`）增加成功率
- 长文字（日期、地址）建议后期用设计工具添加

---

## Error Handling

| 问题 | 解决方案 |
|------|---------|
| API 提交失败 | 检查 `config/api.yaml` |
| Task FAILED | 简化 Prompt，减少文字，移除冲突指令 |
| Task TIMEOUT | 自动重试（已内置） |
| 文字拼写错误 | 减少文字量，全大写，重新生成 |
| 中文乱码 | 减少字数，用黑体，避免繁体 |
| 风格不匹配 | 检查 AVOID 约束，换风格 |
| 后处理出错 | 使用 `--skip-postprocess` 保留原始图 |

## Notes

- 智能默认值：只需 `title` + `poster_type` 即可生成
- 颜色指令含覆盖率指导（primary ~50-60%, secondary ~25-30%, accent ~10-15%）
- 文字渲染缓解规则自动注入每个 prompt
- 自定义尺寸自动 GCD 简化宽高比
- 社交媒体用 JPEG/cover 裁切，打印用 PNG/fit 填充
