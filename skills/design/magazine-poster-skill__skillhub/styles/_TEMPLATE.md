# 风格扩展模板

> 复制本文件，重命名为 `你的风格ID小写.md`（如 `cyberpunk.md`），填写下方各节。
> 填写完成后，在 `SKILL.md` 的类型判断表中添加一行指向此文件。

---

## 元信息

- **风格 ID**：`YOUR_STYLE_ID`（全大写，用于类型判断表）
- **风格名称**：中文名 · 英文副标题（如：暗色工业 · 策略手册风）
- **适用内容**：描述什么类型的输入文本应该触发此风格（如：方法论、SOP、策略分析类内容）
- **视觉方向**：一句话描述色调氛围（如：深黑底 + 金色强调）

---

## CSS 变量

列出所有 CSS 自定义属性。至少包含以下语义 token：

```
--bg:          主背景色
--surface:     次背景/区块背景
--card:        卡片背景
--border:      主分隔线
--ink:         主文字色
--ink-dim:     辅助文字色
--ink-mute:    弱化文字色
--accent:      主强调色
--accent-lt:   浅强调色（可选）
```

根据风格需要可添加更多变量（如 `--red`、`--green`、`--gradient-1` 等）。

**body 外部背景色**：`#xxxxxx`（写在 body 的 background 上，page-wrapper 外部可见）

---

## 字体引入

提供完整的 Google Fonts `<link>` 标签：

```html
<link href="https://fonts.googleapis.com/css2?family=字体1&family=字体2&display=swap" rel="stylesheet">
```

---

## 字体使用规则

明确每种字体在何处使用：

- **中文标题**：字体名 + weight + 其他属性
- **中文正文**：字体名 + weight + line-height + font-size
- **英文标题/标签/装饰**：字体名 + weight + letter-spacing 等
- **编号/代码/数据**：字体名 + font-size + letter-spacing

---

## 版式模块

按从上到下的页面顺序定义模块。每个模块包含：

### N. 模块名（英文名）

- **用途**：什么时候使用此模块（如"页面顶部固定使用"或"有引用金句时使用"）
- **布局**：CSS 布局属性（display、grid-template-columns、padding 等）
- **背景**：background 值
- **子元素**：逐一列出内部元素的样式规则

模块数量建议 7~10 个，至少包含：
1. **Header/顶栏** — 品牌标识、分类、日期
2. **Hero/主视觉区** — 主标题、副标题、标签
3. **Quote/引言区** — 金句展示（至少一种形式）
4. **Content/正文区** — 双栏或单栏正文
5. **Card/卡片区** — 信息模块卡片展示
6. **Footer/底栏** — 元信息、品牌名

可选模块（根据风格特色添加）：
- 数据指标条、步骤流程、案例区、避坑网格、CTA 行动号召等

---

## 模块编写规范

每个子元素的样式描述应包含以下信息（缺一不可）：

1. **字体族**：具体字体名（如 `Noto Sans SC`，不要写"正文字体"）
2. **字重**：具体数值（如 `700`，不要写"粗体"）
3. **字号**：具体值或 clamp 表达式（如 `13.5px` 或 `clamp(14px, 2.5vw, 17px)`）
4. **颜色**：引用 CSS 变量（如 `var(--ink-dim)`）
5. **间距**：padding、margin、gap 的具体值
6. **行高**：line-height 具体值（如 `1.7`）
7. **letter-spacing**：如有（如 `0.15em`）

示例：
```
标题（Noto Sans SC 700，15px，color: var(--ink)，line-height: 1.4，margin-bottom: 8px）
```

---

## 检查清单

填写完成后，逐条确认：

- [ ] CSS 变量至少覆盖 9 个语义 token（bg/surface/card/border/ink/ink-dim/ink-mute/accent/accent-lt）
- [ ] body 外部背景色已指定
- [ ] Google Fonts link 标签完整可用
- [ ] 字体使用规则覆盖了中文标题、中文正文、英文装饰三类
- [ ] 版式模块 ≥ 7 个，含 Header + Hero + Quote + Content + Footer
- [ ] 每个子元素样式包含字体族、字重、字号、颜色、间距
- [ ] 所有颜色值使用 CSS 变量引用，不硬编码 hex 值（CSS 变量定义处除外）
