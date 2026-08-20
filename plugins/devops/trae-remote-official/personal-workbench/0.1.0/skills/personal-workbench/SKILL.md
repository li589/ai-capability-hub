---
name: personal-workbench
description: "Skill for a personal daily workbench — a self-contained HTML app that unifies 每日计划/待办, 习惯打卡, 记账, 长期目标 and 内容记录/灵感 in one place. Triggers on 个人工作台 / personal workbench / 我的工作台, 每日计划, 打卡 / check-in / habit tracker, 记账 / ledger, 长期计划 / goals, 灵感/备忘/内容记录. Ships two files — a desktop version (sidebar shell) and a mobile version (drawer + bottom tab bar) — both driven by the same CONFIG, data in localStorage, no build, no backend."
---

# Personal Workbench

Ship a personal daily workbench the user opens in any browser. No build step, no backend — data lives in `localStorage`. Every module follows the same shape (记录 → 执行 → 统计 → 反馈); only the fields differ.

Two template files, one shared `CONFIG` shape:
- [scripts/workbench-desktop.html](scripts/workbench-desktop.html) — left sidebar navigation, wide multi-column layout.
- [scripts/workbench-mobile.html](scripts/workbench-mobile.html) — hamburger drawer + bottom tab bar + floating add button, single-column phone layout, safe-area aware.

Which file(s) to ship is decided by **§0 形态路由** — not always both. When `full` mode is active, both read/write the same `storageKey`, so on one device+browser they show the same data.

> [!IMPORTANT]
> **Always state the storage limitation when delivering — in plain language.** No jargon like `localStorage`/"后端"/"同步". Say it like you'd tell a friend:
> - "东西都存在你自己这台设备的这个浏览器里。换台电脑、换个浏览器、或者清了浏览记录，之前填的就没了。"
> - "手机版和电脑版的数据不会互相同步，各记各的。"
>
> If the user needs multi-device sync or sharing with others, tell them plainly this version can't do that.

## 0. 形态路由

Before any other workflow, decide which **form** (产物形态) the user wants. This determines which template file(s) to create and which file(s) every subsequent workflow (delivery, re-skin, add-module, add-layout, add-icon) operates on.

### 0.1 三种形态

| 形态 | 产物文件 | 模板 | 布局特征 |
|---|---|---|---|
| `desktop` | `workbench-desktop.html` | desktop | 侧栏导航 + 多列网格，`min-width:1000px`，居中对话框 |
| `app` | `workbench-mobile.html` | mobile | 抽屉 + 底栏Tab + 浮动+按钮，`max-width:480px`，底部弹窗，safe-area |
| `full` | 两个文件都出 | both | 两个模板，CONFIG 与 `:root` 必须同步 |

### 0.2 信号识别

判定维度只有一个：**用户在什么设备上用**。

| 形态 | 强信号（任一命中即判定） |
|---|---|
| `app` | 手机能看 / 手机上用 / 手机版 / app / 应用 / 移动端 / 随身 |
| `desktop` | 电脑上用 / 桌面 / 桌面版 / 浏览器里打开 / 网页 / web |
| `full` | 都要 / 两端 / 电脑和手机 / 全平台 |

### 0.3 仲裁规则

```
full 信号 → full
app 信号（手机能看 / 手机上用 / 移动端） → app
desktop 信号（电脑 / 桌面 / 浏览器） → desktop
都没有 → desktop（默认）
```

优先级：`full` > `app` > `desktop` > 默认 `desktop`。

**关键规则**：只要用户提到"手机上用 / 手机能看"，无论后面跟的是"网页"还是"app"，都判 `app`。用户的约束是使用场景（在手机上看），不是技术形态。

### 0.4 下游穿透

形态判定结果穿透所有工作流，决定操作哪个文件：

| 工作流 | `desktop` | `app` | `full` |
|---|---|---|---|
| 交付 (§1) | 只出 desktop | 只出 mobile | 两个都出 |
| 换肤 (§4.2) | 只改 desktop `:root` | 只改 mobile `:root` | 两端都改 |
| 加模块 (§3) | 只改 desktop CONFIG | 只改 mobile CONFIG + tabbar | 两端CONFIG都改 |
| 加 layout (§3.1) | 只改 desktop `<style>` | 只改 mobile `<style>` | 两端都加 |
| 加图标 (§3.2) | 只改 desktop ICONS | 只改 mobile ICONS | 两端都改 |
| 生成 hero 图 (§1.1) | 存 desktop 的 assets | 存 mobile 的 assets | 共用一份 |

### 0.5 状态持久化（后续请求怎么知道当前形态）

靠目录文件存在性判断，**不在 CONFIG 里加 `form` 字段**：

```
目录里只有 workbench-desktop.html  → 当前形态 = desktop
目录里只有 workbench-mobile.html   → 当前形态 = app
两个文件都在                        → 当前形态 = full
```

- 用户说"换个莫兰迪配色"时，Agent 扫一眼目录就知道改哪个文件，不需要用户重复说形态。
- 用户想从 `desktop` 升级到 `full`（"给我也加个手机版"）→ 补出 mobile 文件，形态自动变为 `full`。
- 用户想从 `full` 降为 `app`（"删掉桌面版"）→ 删 desktop 文件，形态降为 `app`。

---

## 1. Usage

1. **Determine form** — run §0 形态路由. Only copy the file(s) for the decided form to the target location.
2. **Generate the hero image** — call the image generation tool (`GenerateImage`) to create a hero banner that matches the user's requested style. This is **mandatory for every delivery** — the首页"晚上好"区域 must have a real image, not the default placeholder. See §1.1 for the prompt template.
3. Save the generated image to `assets/greet-banner.jpg` (or update `--greet-image` in `:root` to point to the new file).
4. Edit the `CONFIG` object at the top of the `<script>` block. In `full` mode, **keep `CONFIG` identical in both files** so desktop and mobile stay in sync. In `desktop` or `app` mode, only edit the single file.
5. Open the file(s) on the matching device.

### 1.1 Hero 图片生成规范（每次必做）

Every time this skill is used to deliver a workbench, the Agent MUST generate a hero image via `GenerateImage`. Do not skip this step or reuse a previous image — the hero is the first thing the user sees and sets the entire visual tone.

**Prompt template** (adapt to user's requested style):

```
[PURPOSE]: Mobile app hero banner background, displayed as a right-aligned cover image behind a greeting card on a personal workbench app.
[CONTENT]: {根据用户风格描述生成对应场景的插画/摄影/纹理}
[STYLE]: {匹配用户描述的视觉风格 — 如"复古杂志风"则用暖色调纸张质感+"水彩食物插画"}
[COMPOSITION]: Right-weighted composition, left side should be sparse/blurry/dark enough for a text overlay gradient; no text in the image.
[SIZE]: landscape, wide aspect ratio, suitable for mobile hero banner (approximately 1200×600).
```

**Rules**:
- The image must visually match the `:root` color palette — same hue family, same warmth/coolness.
- The left ~40% must be visually quiet (dark or sparse) so the greeting text remains readable over the gradient overlay.
- Save to `assets/greet-banner.jpg`. If the tool returns a different format, convert or update `--greet-image` accordingly.
- If the user's style is minimalist or the user explicitly says "no image", generate a subtle texture/pattern instead of a figurative illustration — still call `GenerateImage`, just with a texture prompt.
- Other images (module covers, record thumbnails, page texture) are **optional** — only generate when the user's request or style explicitly calls for them.

## 2. What to customize (the `CONFIG` block)

- **`profile`** — `name` / `avatar` (emoji) / `subtitle` shown in the sidebar/drawer.
- **`storageKey`** — the localStorage bucket. Bump it to force a clean reset.
- **`modules`** — the ordered list of modules; each has `id`, `type`, `icon` (emoji), `name`, `desc`, plus type-specific fields and `seed` starter data.
- **`tabbar`** (mobile only) — up to ~5 module `id`s to surface in the bottom tab bar.

## 3. Module types

Every module is one `type`; pick per need and add as many as you want:

- **`dashboard`** — the 首页: greeting, today's progress rings (auto-computed from the other modules), module grid, quick-record shortcuts. Keep exactly one.
- **`todo`** — 每日计划: checkable tasks with priority; seed items are `{ text, level: high|mid|low, done }`.
- **`checkin`** — 习惯打卡: tap-to-complete cards with 连续天数 streak; auto-clears each new day (streak kept). Seed items `{ name, emoji, done, streak }`.
- **`ledger`** — 记账本: income/expense entries with `categories`, monthly totals and a 支出构成 bar chart. Seed items `{ kind: income|expense, cat, amount, note, date }`.
- **`goal`** — 长期计划: progress bars with a +1 button. Seed items `{ name, emoji, current, target, unit, note }`.
- **`notes`** — 内容记录: free-text cards with optional `tags`. Seed items `{ title, body, tag, date }`.

To **add a module**: append an entry to `modules` with a supported `type` and its `seed`. To repurpose one (e.g. 护肤打卡, 阅读进度, 情绪日记), reuse the closest type and rename `name`/`icon`/fields — 补品/护肤/运动 → `checkin`, 阅读/学习 → `goal`, 记账 → `ledger`, 日记/摘录/灵感 → `notes`. Operate only on the file(s) determined by §0 形态路由 — `desktop` edits desktop only, `app` edits mobile only, `full` edits both.

### 3.0.1 自定义字段（`fields` 数组）

每个模块除了内置字段（title/done/priority/log/current/amount/content 等），还可以通过 `fields` 数组声明**自定义字段**。这些字段会被编辑器自动渲染为表单控件、在记录卡片底部以 `.meta-tag` 形式显示、在 `newItem()` 时自动初始化。**Agent 只需在 CONFIG 里声明，不需要改 JS 渲染逻辑。**

```js
{
  key: "recipe", type: "notes", icon: "book", name: "菜谱收藏", color: "var(--module-3)",
  fields: [
    { key: "cookTime", label: "烹饪时间", type: "text", placeholder: "30分钟" },
    { key: "difficulty", label: "难度", type: "select", options: ["简单","中等","复杂"] },
    { key: "ingredients", label: "食材", type: "textarea", placeholder: "列出食材..." },
    { key: "calories", label: "热量", type: "number", placeholder: "350" }
  ],
  seed: [...]
}
```

支持的字段类型：

| `type` | 表单控件 | 卡片显示 | 说明 |
|---|---|---|---|
| `text` | `<input>` 单行 | `.meta-tag` 文字 | 通用短文本（时间、标签、数值描述） |
| `textarea` | `<textarea>` 多行 | `.meta-tag` 文字 | 长文本（食材、步骤、备注） |
| `number` | `<input type="number">` | `.meta-tag` 数字 | 数值（热量、份数、评分） |
| `select` | `.seg` 分段选择器 | `.meta-tag` 选中值 | 枚举（难度、口味、场景） |

规则：
- `key` 必须唯一，小写驼峰，不与内置字段冲突（避免 title/done/note/log/current/target/amount/category/date/mood/content/priority/image/pinned/id）。
- `select` 类型必须提供 `options` 数组。
- 字段值自动持久化到 localStorage，无需额外处理。
- 空值不显示在卡片上（`filter(f=>x[f.key])` 过滤）。

### 3.0.2 图片槽位与背景图 token

模板支持以下图片位置：

| 槽位 | 位置 | 机制 | CONFIG 或 token |
|---|---|---|---|
| 首页 hero | 首页"晚上好"容器 `.greet` | CSS 背景图 | `--greet-image: url(...)` |
| 页面纹理 | 整页 `body::before` 叠加层 | CSS 背景图，50% 透明 | `--page-texture: url(...)` 或 `none` |
| 模块封面 | 模块页 hero `.hero.has-cover` | JS CONFIG `m.cover` | `cover: "https://..."` |
| 记录缩略图 | 记录卡片左侧 `.thumb` | JS 记录字段 `x.image` | 编辑器"图片 URL"字段 |
| 用户头像 | 抽屉头部 `.brand` | JS CONFIG `profile.avatar` | `avatar: "emoji"` 或 URL |

**换肤时**：`--greet-image` 和 `--page-texture` 是 CSS token，改 `:root` 即换；模块封面和缩略图是 CONFIG/数据字段，由用户填写或 AI 生成 URL 后填入。

`--page-texture` 用法示例：
```css
--page-texture: url("assets/paper-texture.jpg");  /* 叠加纸张纹理 */
--page-texture: none;                              /* 关闭纹理 */
```

## 3.1 图标系统与扩展

### 3.1.0 卡片布局变体（layout 字段）

每条记录有一个 `layout` 字段，控制卡片的视觉样式。模板预置 3 个变体，Agent 可通过加 CSS 规则无限扩展，**不需要改 JS**。

| layout 值 | 效果 | 适用场景 |
|---|---|---|
| `default` | 标准左文右操作（原有样式） | 待办、打卡、记账、进度 |
| `feature` | 大图在上 + 标题 + 正文在下 | 菜谱、餐厅、旅行记录（需要有 `image` 字段） |
| `quote` | 大字居中 + 留白多 | 灵感、金句、日记摘要 |

**使用方式**：
- 用户在编辑器里选"标准/大图/引文"
- 或 Agent 在 CONFIG seed 里直接写 `layout: "feature"`

**扩展新变体（Agent 操作规范）**：

当用户需要的布局不在预置 3 个里时，Agent 可以创建新变体：

1. 在 `<style>` 里加 CSS 规则，命名必须为 `.rec.rec-layout-xxx { ... }`
2. 在 CONFIG seed 或编辑器选项里引用 `layout: "xxx"`

**硬约束（必须遵守）**：
- 所有颜色必须用 `var()` 引用现有 token（如 `var(--surface-card)`、`var(--text)`），**禁止硬编码 hex**
- 所有圆角必须用 `--radius-*` token（`--radius-control` / `--radius-tile` / `--radius-card` / `--radius-sheet`）
- 字号只能用现有量级：12px / 13px / 14px / 15px / 16px / 18px，不能自创新字号
- 只能用 `display:flex` / `display:grid` / `position` 调布局，不能改全局样式或影响其他卡片
- 新变体只影响 `.rec.rec-layout-xxx` 内部的元素，不会泄漏到其他组件

示例——加一个"横向卡片"变体：
```css
.rec.rec-layout-horizontal { flex-direction:row-reverse; }
.rec.rec-layout-horizontal .thumb { width:80px; height:80px; }
.rec.rec-layout-horizontal .body { flex:1; }
```
然后在编辑器的 `layoutOpts` 数组里加 `{v:'horizontal', l:'横卡'}` 即可。

## 3.2 图标系统与扩展

All icons are inline SVG paths stored in a `ICONS` dictionary inside `<script>`. No runtime library, no network dependency — the `icon(name)` function looks up the path and wraps it in a standard `<svg>` shell:

```
viewBox="0 0 24 24" · fill="none" · stroke="currentColor" · stroke-width=1.7 · linecap/linejoin=round
```

This spec is identical to [Lucide](https://lucide.dev) — same 24×24 grid, same stroke rules. The 20 built-in icons (`home grid chart user plus menu calendar list leaf book activity wallet pen camera flame target star bolt quote chevron check trash close sun moon`) are hand-picked Lucide paths.

**Fallback**: if `icon(name)` receives a key not in `ICONS`, it falls back to `grid` (a 2×2 square grid) instead of rendering empty — no visual holes.

**When the user wants a module whose concept isn't covered by built-in icons** (e.g. 喝水/droplet, 冥想/brain, 睡眠/moon-star, 植物/sprout), the Agent should:

1. Search the icon name on [lucide.dev/icons](https://lucide.dev/icons).
2. Copy that icon's inner SVG content (the `<path>`/`<circle>`/`<rect>` elements, **not** the wrapping `<svg>` tag).
3. Add an entry to `ICONS`: `droplet: '<path d="..."/><circle .../>'`.
4. Reference it in CONFIG: `icon: "droplet"`.

Rules for adding icons:
- Source must be Lucide official (same 24×24 stroke spec). Do not hand-draw paths or use other icon sets — stroke width, cap, and join must match.
- Keep the key lowercase, one word, semantic (e.g. `droplet` not `water-icon`).
- One icon can be reused across modules (e.g. `check` for both todo checkboxes and quick-record shortcuts).
- Icon color is inherited via `currentColor` — it follows the module's `color` token automatically, no per-icon coloring needed.

## 4. Theme — 一键换肤

All visual style lives in CSS variables under `:root` at the top of `<style>`. **Zero hardcoded colors in component CSS** — every color, radius, shadow, and background image references a token, so editing `:root` alone re-skins the entire app without touching component code.

### 4.1 Token 体系（语义化命名）

Token names describe **role, not color** — a model reading `:root` can immediately pick the right token for a new component without guessing.

| 维度 | Token | 角色 |
|---|---|---|
| 页面与表面 | `--page-bg` `--surface-card` `--surface-nested` | 页面底色、卡片/面板/输入框背景、嵌套区域（图标瓦底、ghost 按钮、hero 底） |
| 边框 | `--border` `--border-input` | 常规边框（卡片、分隔线）、强边框（输入框、按钮、chip、勾选框） |
| 文本层级 | `--text` `--text-secondary` `--text-tertiary` | 主文本（标题、正文）、次文本（标签、副标题）、弱文本（图标色、占位、导航字） |
| 主色 | `--accent` `--accent-muted` `--on-accent` | 按钮/选中/强调、主色浅底（focus 光晕）、主色上的前景字 |
| 模块色 | `--module-1` `--module-2` `--module-3` `--module-4` `--module-5` | 5 色轮转，新模块按序取下一个未用的。注释标明了每色的常用场景 |
| 危险色 | `--danger` `--danger-muted` | 删除/危险操作、危险浅底（hover、标签） |
| 抽屉 | `--drawer-bg` `--drawer-bg-top` `--drawer-text` `--drawer-text-mute` `--drawer-hover` `--drawer-active` | 深色抽屉专用色板 |
| 圆角 | `--radius-control` `--radius-tile` `--radius-card` `--radius-sheet` | 勾选框/步进按钮/日历格 → 图标瓦/输入框/按钮/chip → 卡片/面板/hero → 底部弹窗 |
| 阴影 | `--shadow-card` `--shadow-overlay` | 卡片/面板、弹窗/toast/悬浮按钮 |
| 字体与布局 | `--font` `--nav-h` | 字体栈、底栏高度 |
| 背景图 | `--greet-image` `--page-texture` | 首页 hero 背景图 URL、页面纹理叠加（none 或 url(...)） |

**生成新组件时选 token 的规则**：
- 需要卡片背景 → `--surface-card`；卡片内的嵌套区域 → `--surface-nested`
- 需要主文本 → `--text`；标签/副标题 → `--text-secondary`；图标色/占位 → `--text-tertiary`
- 需要按钮/选中 → `--accent` + `--on-accent`（文字）；focus 光晕 → `--accent-muted`
- 新模块的颜色 → 取 `--module-1` 到 `--module-5` 中下一个未被使用的
- 需要边框 → `--border`（轻）；输入框/按钮边框 → `--border-input`（强）
- 需要阴影 → 卡片用 `--shadow-card`；弹窗/toast 用 `--shadow-overlay`
- 需要圆角 → 控件用 `--radius-control`；图标瓦/输入框用 `--radius-tile`；卡片用 `--radius-card`；弹窗用 `--radius-sheet`
- 需要图片 → 首页 hero 用 `--greet-image`；页面纹理用 `--page-texture`；模块封面用 CONFIG `cover` 字段；记录缩略图用记录 `image` 字段

### 4.2 换肤工作流（Agent 执行）

When the user describes a style in natural language (e.g. "换成莫兰迪粉系" / "make it dark mode" / "换成冷色科技感"), execute this pipeline:

1. **解析意图** — 从用户描述提取 3 个维度：色温（暖/冷/中性）、明度（浅/深）、饱和度（低/中/高）。若用户提到具体颜色名，以此为准。
2. **生成 token** — 按下表映射规则，生成一整套 `:root` 变量值。所有颜色必须满足 WCAG AA 对比度（文本≥4.5:1，大字≥3:1）。`--on-accent` 必须与 `--accent` 对比度≥4.5:1。抽屉色板必须与主色板协调。
3. **应用到 HTML** — 只替换 `:root` 块内的值，**不碰组件 CSS、不碰 JS、不碰 CONFIG**。组件层全部用 `var()` 引用，无需改动。
4. **校验** — 改完后用浏览器打开，检查：主色上的文字可读、抽屉文字可读、日历已打卡格颜色与模块色一致、图表数据色不撞色、暗色背景下的文本对比度达标。
5. **同步两端** — 按 §0 形态路由决定的作用范围操作：`desktop` 只改 desktop，`app` 只改 mobile，`full` 两端都改且保持一致。

### 4.3 预设色板（可复用）

<details>
<summary>墨色中性（默认）</summary>

```css
--page-bg:#f4f3f0; --surface-card:#fcfbf8; --surface-nested:#f7f6f1;
--text:#232220; --text-secondary:#6b665d; --text-tertiary:#8c877c;
--accent:#2f2e2b; --accent-muted:#efeee8; --on-accent:#f4f3f0;
--drawer-bg:#232220; --drawer-bg-top:#2d2c29; --drawer-text:#f4f3f0;
```

</details>

<details>
<summary>莫兰迪暖粉</summary>

```css
--page-bg:#f5f1f0; --surface-card:#fcf9f8; --surface-nested:#f8f3f2;
--text:#3a3434; --text-secondary:#7a6e6e; --text-tertiary:#9c9090;
--accent:#a06b6b; --accent-muted:#f0e6e6; --on-accent:#fcf9f8;
--drawer-bg:#3a3030; --drawer-bg-top:#463a3a; --drawer-text:#f5f1f0;
--module-1:#8aa394; --module-2:#7a8da3; --module-3:#c4a572; --module-4:#b8837a; --module-5:#a09ab5;
```

</details>

<details>
<summary>冷色科技</summary>

```css
--page-bg:#f0f2f5; --surface-card:#f8fafc; --surface-nested:#f2f4f8;
--text:#1a1f2e; --text-secondary:#5a6378; --text-tertiary:#8590a8;
--accent:#2c4a7c; --accent-muted:#e8edf5; --on-accent:#f8fafc;
--drawer-bg:#1a1f2e; --drawer-bg-top:#242b3d; --drawer-text:#e8edf5;
--module-1:#6a9a7a; --module-2:#4a6a9c; --module-3:#a08850; --module-4:#9a6a5a; --module-5:#7a7aa0;
```

</details>

### 4.4 生成新色板时的约束

- `--page-bg` 与 `--surface-card` 明度差≥3%，否则卡片浮不出来。
- `--surface-card` 与 `--surface-nested` 明度差≥2%，否则分层消失。
- `--text` 与 `--page-bg` 对比度≥7:1（AAA），保证正文可读。
- `--text-secondary` 对比度≥4.5:1（AA），`--text-tertiary`≥3:1。
- `--module-1` 到 `--module-5` 之间色相差≥25°，避免相邻段难辨。
- `--drawer-*` 色板必须与主色板同色温——暖色主题用暖色抽屉，冷色主题用冷色抽屉。
- 阴影 `--shadow-card` / `--shadow-overlay` 的 rgba 透明度可根据明度调整：深色背景降低透明度，浅色背景提高。

## 5. Desktop vs mobile

- **Desktop** — persistent sidebar; each module fills a wide area (grids up to 3–4 columns); modals are centered dialogs.
- **Mobile** — drawer opens from the ☰ button; a bottom tab bar switches the main modules; a floating + button creates records; modals are bottom sheets. Layout is single-column and respects the phone's safe areas.
