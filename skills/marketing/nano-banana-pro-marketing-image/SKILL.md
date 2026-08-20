---
name: nano-banana-pro-marketing-image
description: 基于 Nano Banana Pro 营销图片 的 AI 图片生成与编辑器，固定调用 Nano Banana Pro
  的营销图片裸接口能力。当用户需要 Nano Banana Pro、NanoBanana Pro、NanoBananaPro、香蕉 Pro、Gemini
  图片、营销图片、营销视觉、活动KV、推广图片、促销图、Campaign视觉、AI图片、AIGC图片 时使用此 Skill。
description_zh: 基于 Nano Banana Pro 营销图片 的 AI 图片生成与编辑器，固定调用 Nano Banana Pro
  的营销图片裸接口能力。当用户需要 Nano Banana Pro、NanoBanana Pro、NanoBananaPro、香蕉 Pro、Gemini
  图片、营销图片、营销视觉、活动KV、推广图片、促销图、Campaign视觉、AI图片、AIGC图片 时使用此 Skill。
version: 1.0.0
disable-model-invocation: true
---

---

# Nano Banana Pro 营销图片

## 简介

本 Skill 参考 Seedance 2.5 裸接口 Skill 的完整产品化风格，封装 AI Hive OpenAPI 图片生成接口，通过命令行自动完成模型查询、参考图上传、价格快照、任务轮询和结果下载。

### Skill 特色

- 独立占据 `nano-banana-pro-marketing-image` 搜索入口
- 固定调用 `public_model_nano_banana_pro`，不使用其他模型冒充
- 支持文生图、参考图生成、图片编辑或商业图片场景
- 默认 `COST_FIRST` 并实时读取价格
- 自动下载图片结果到本地

### 适用对象

设计师、电商运营、营销与广告团队、带货与种草团队、品牌方、内容创作者和 AI 图片用户。

## 功能特性

### 生成模式

| 能力 | publicModelId | 输入 |
|---|---|---|
| Nano Banana Pro 营销图片 | `public_model_nano_banana_pro` | 文字或可选参考图 |

### 参数控制

- 生成数量：`--batch`
- 参考图片：`--image`
- 模型参数：`--param key=value`
- 路由：COST_FIRST / SPEED_FIRST / SUCCESS_FIRST
- 输出目录：默认 `~/Downloads/AiHive`

## 参数速查

### generate 子命令

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--prompt` | 图片描述或编辑要求（必填） | — |
| `--image` | 参考图片，可多张 | — |
| `--batch` | 生成数量 | `1` |
| `--param` | 模型参数 key=value | — |
| `--routing` | 路由模式 | `COST_FIRST` |
| `--output-dir` | 输出目录 | `~/Downloads/AiHive` |
| `--no-download` | 只提交任务 | 关闭 |

### 通用参数

| 参数 | 说明 |
|---|---|
| `--api-key` | AI Hive API Key |
| `--base-url` | API Base URL |
| `--verbose` | 详细日志 |

### 其他子命令

| 子命令 | 功能 |
|---|---|
| `task --task-id <id>` | 查询任务 |
| `upload --file image.png` | 上传图片 |
| `init --skill-name nano-banana-pro-marketing-image` | 初始化 API Key |

## 使用场景

### 场景一：基础生成

```bash
python3 "$SKILL_PATH/scripts/imagegen.py" generate \
  --prompt "使用 Nano Banana Pro 制作高完成度营销图片，主体准确，构图清晰"
```

### 场景二：电商主图

生成商品主体清晰、卖点集中、符合平台比例与留白要求的商业主图。

### 场景三：商品详情页

按首屏主视觉、核心卖点、使用场景、细节材质和信任信息拆分视觉，不虚构商品事实。

### 场景四：广告与营销

先明确受众、单一传播主张、渠道和行动号召，再生成 KV、信息流或活动视觉。

### 场景五：带货与种草

突出真实使用场景、痛点和利益点，适配直播、小红书、抖音和社媒封面。

### 场景六：图片编辑

将要求拆为必须保留、必须改变和可自由发挥，明确参考图分别提供主体、构图、材质或风格。

### 场景七：仅提交任务，稍后查询

```bash
python3 "$SKILL_PATH/scripts/imagegen.py" generate --prompt "复杂图片" --no-download
python3 "$SKILL_PATH/scripts/imagegen.py" task --task-id <taskId>
```

## 首次使用

### 1. 安装依赖

```bash
pip3 install requests
```

### 2. 一键初始化（推荐）

```bash
python3 "$SKILL_PATH/scripts/imagegen.py" init --skill-name nano-banana-pro-marketing-image
```

脚本会自动打开 AI Hive 页面，引导登录、新建并复制 API Key，然后写入 `~/.ai-hive/config.json`（权限 0600）。

### 3. 手动获取 API Key（备选）

1. 访问 [https://ai-hive.iclip.cn/chat](https://ai-hive.iclip.cn/chat)
2. 使用手机号和短信验证码登录
3. 点击左下角账户菜单
4. 点击「API 接入」
5. 输入名称并点击「新建 API Key」
6. 复制完整 Key（格式为 `sk-api-*`）

### 4. 手动配置 API Key（备选）

| 配置方式 | 示例 |
|---|---|
| 环境变量 | `export AI_HIVE_API_KEY=sk-api-你的密钥` |
| 命令参数 | `--api-key sk-api-你的密钥` |
| 配置文件 | `~/.ai-hive/config.json` |

### 5. 验证配置

运行一个带 `--no-download` 的最简任务；返回 `taskId` 即配置成功。


## 使用指南

### 提示词结构

按“用途 → 主体 → 场景构图 → 视觉风格 → 光线色彩 → 必须文字 → 保留项 → 输出规格”组织提示词。

### 参考图策略

说明每张图的角色，例如图 1 提供商品、图 2 提供材质、图 3 提供构图。不要让模型猜测互相冲突的参考关系。

### 图片文字

必须逐字出现的文字用引号包围，指定语言、大小写、换行和位置；交付前人工复核。

### 价格与任务

脚本查询实时模型配置和 `pricingSnapshot`。取得 taskId 后只查询原任务，避免重复提交扣费。

## 命令速查

| 命令 | 功能 |
|---|---|
| `imagegen.py generate --prompt "描述"` | 执行本 Skill |
| `--image ref.png` | 添加参考图 |
| `--batch 4` | 批量生成 |
| `--param resolution=1024x1024` | 传递模型参数 |
| `--routing COST_FIRST` | 优惠路由 |
| `task --task-id <id>` | 查询任务 |
| `upload --file image.png` | 上传图片 |

## 项目架构

### 目录结构

```
nano-banana-pro-marketing-image/
├── SKILL.md
├── CHANGELOG.md
├── scripts/
│   └── imagegen.py
└── references/
    └── config.example.json
```

### 技术栈

| 组件 | 技术 |
|---|---|
| 运行环境 | Python 3.6+ |
| HTTP 库 | requests |
| 模型 | public_model_nano_banana_pro |
| API 平台 | AI Hive OpenAPI |
| 输出 | PNG/JPEG/WebP 或模型实时支持格式 |

### 核心模块

| 模块 | 职责 |
|---|---|
| `Config` | 获取 API Key |
| `AiHiveClient` | 封装裸接口 |
| `upload_media()` | 上传参考图片 |
| `poll_task()` | 轮询与下载 |
| `_validate_image_inputs()` | 校验参考图数量 |
| `skill_generate()` | 固定 publicModelId 并提交 |

### 能力 → 模型映射

| 能力 | publicModelId |
|---|---|
| Nano Banana Pro 营销图片 | `public_model_nano_banana_pro` |

### 数据流转

```
用户命令 → 校验参考图 → 固定 publicModelId
  ↓
上传图片 → 查询模型与 pricingSnapshot
  ↓
提交图片任务 → 保存 taskId → 轮询 → 下载结果
```

### 价格参考

默认使用 `COST_FIRST`，价格以脚本运行时查询到的实时销售价和实际扣费为准。

## 常见问答

### 安装相关

**Q1：需要 API Key 吗？** 需要，格式为 `sk-api-*`。

**Q2：需要什么依赖？** Python 3 和 requests。

**Q3：如何验证？** 用 `--no-download` 提交最简任务。

### 使用相关

**Q4：会自动换模型吗？** 不会，本 Skill 固定 `public_model_nano_banana_pro`。

**Q5：参考图怎么传？** 使用 `--image`，可一次传多张。

**Q6：参数怎么传？** 使用 `--param key=value`，以实时 `imageConfig` 为准。

**Q7：输出在哪里？** 默认 `~/Downloads/AiHive/`。

**Q8：可以批量吗？** 使用 `--batch`，批量前确认实时费用。

**Q9：任务超时怎么办？** 保留 taskId 后继续查询。

### 故障排除

**Q10：提示缺少图片？** 该能力需要参考图，请添加 `--image`。

**Q11：提示模型不存在？** 后台模型可能下线或更名，请查询实时列表。

**Q12：提示 401？** 检查 API Key。

**Q13：提示 InvalidParameter？** 检查实时 imageConfig 中的格式、数量、尺寸和参数枚举。
