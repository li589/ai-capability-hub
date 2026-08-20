# 公众号爆款封面工坊（GZH Cover Studio）

一个零配置、开箱即用的微信公众号爆款封面设计 Skill。

## 核心能力

- **开箱即用**：仅使用平台内置的图像生成与理解能力，无需额外配置即可运行。
- **视觉底图 + 标题精排分离**：AI 负责生成无字高质感底图，本地排版引擎负责清晰中文标题，避免 AI 乱字。
- **30+ 视觉风格家族 × 17 大内容赛道**：从极简大字报到国潮水墨、黑金奢华、街头涂鸦，覆盖职场、美食、育儿、科技等场景。
- **多尺寸一体**：主封面 900×383（2.35:1）、方形缩略 1080×1080（1:1）、朋友圈 1080×1350（4:5）。
- **A/B 变体 + 交互精修**：一次出 2–4 套方案对比，支持聚焦修改。
- **自包含 HTML 方案册**：所有图片、样式、脚本内嵌，离线可查看。

## 安装使用

1. 将整个 `my-gzh-cover` 文件夹复制到 WorkBuddy 的 skills 目录或项目 `.workbuddy/skills/`。
2. 在对话中输入：
   - "帮我做一个职场时间管理的公众号封面"
   - "生成 3 套美食爆款封面方案"
   - "根据这张参考图做封面，标题入图"
3. Skill 自动进入意图解析 → 风格匹配 → 生成底图 → 标题精排 → 输出 HTML 方案册 → 交付成片。

## 目录说明

```
my-gzh-cover/
├── SKILL.md                          # 主流程与调用约定
├── README.md                         # 本文件
├── references/
│   ├── styles.md                     # 30+ 视觉风格库
│   ├── design_principles.md          # 配色/字体/构图/点击率心理学
│   ├── prompt_recipes.md             # 结构化提示词配方
│   └── cover_preview_template.html   # 方案册 HTML 模板
└── scripts/
    └── studio.py                     # preview / compose / check 工具
```

## 工具脚本用法

### 生成 HTML 方案册

```bash
python3 scripts/studio.py preview \
  --input 方案数据.json \
  --output 封面方案.html
```

### 标题精排（合成到视觉底图）

```bash
python3 scripts/studio.py compose \
  --base 底图.png \
  --title "别让忙等于盲" \
  --subtitle "职场新人的时间管理" \
  --tag "干货" \
  --out 成片.png
```

需要 Pillow：

```bash
pip install pillow
```

### 尺寸自检

```bash
python3 scripts/studio.py check --images 成片.png --target 900x383
```

## 设计原则速览

- 标题字数：主标题 ≤ 14 字，缩略后仍可读。
- 标题安全区：底部 1/3 或顶部高亮区，主体沉在中上部。
- 配色：≤ 3 主色，标题与背景对比 ≥ 4.5:1。
- 中文标题：绝不让 AI 直接生成文字，使用 `compose` 合成。

## 依赖

- 图像能力使用平台内置工具，无需额外配置即可运行。
- `compose/check` 需要本地 Pillow（可一键安装）。
- 字体自动探测系统 CJK 字体；也可通过环境变量 `GZH_COVER_FONT` 指定。

---

按你自己的主题试试吧。
