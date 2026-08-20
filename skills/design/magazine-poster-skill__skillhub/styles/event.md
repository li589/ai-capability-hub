# EVENT 霓虹电竞 · 活动通告风

**适用**：会议议程、活动预告、峰会回顾、沙龙通知、线下聚会

---

## CSS 变量

```
--bg:          #0f0f23
--surface:     #1a1a2e
--card:        #16213e
--border:      #2a2a4a
--ink:         #e2e8f0
--ink-dim:     #94a3b8
--ink-mute:    #4a4a6a
--accent:      #f43f5e
--accent-lt:   #fb7185
--accent-glow: rgba(244,63,94,0.3)
--purple:      #a78bfa
--purple-glow: rgba(167,139,250,0.2)
--cyan:        #22d3ee
--cyan-glow:   rgba(34,211,238,0.2)
```

body 外部背景：`#050510`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Bebas+Neue&family=Barlow+Condensed:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## 字体使用规则

- 大标题/数字/倒计时：`Bebas Neue`，letter-spacing 0.05em
- 英文标签/时间：`Barlow Condensed` weight 600，letter-spacing 0.12em，uppercase
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.85，font-size 13px

## 版式模块

### 1. Neon Header 霓虹顶栏

- background: var(--surface)，padding: 12px 36px，display: flex，justify-content: space-between，border-bottom: 1px solid var(--border)
- 活动系列名（Barlow Condensed 600，11px，color: var(--accent)，uppercase）
- 状态标签（如有"即将开始"：padding: 3px 10px，background: var(--accent-glow)，color: var(--accent)，border-radius 3px）

### 2. Hero 主视觉区

- padding: 56px 36px 48px，position relative，overflow hidden
- 背景大字（position absolute，Bebas Neue 180px，color: rgba(255,255,255,0.02)，right -20px，top 0，user-select none）
- 标签行（Barlow Condensed 600，10px，color: var(--cyan)，uppercase，text-shadow: 0 0 10px var(--cyan-glow)）
- 主标题（Noto Sans SC 900，clamp(36px, 8vw, 64px)，line-height 1.0，color: var(--ink)；关键词 color: var(--accent)，text-shadow: 0 0 20px var(--accent-glow)）
- 时间地点条（display: flex，gap 20px，margin-top 24px）：Unicode 图标 ◷ ◎ color: var(--purple) + 文字（Barlow Condensed 500，12px，color: var(--ink-dim)）

### 3. Countdown / Stat Bar 数据条

- display: grid，grid-template-columns: repeat(3, 1fr)，border-top/bottom: 1px solid var(--border)
- 数字（Bebas Neue 48px，color: var(--ink)，text-shadow: 0 0 15px var(--purple-glow)）
- 标签（Barlow Condensed 500，10px，color: var(--ink-dim)，uppercase，margin-top 6px）

### 4. Schedule Grid 议程网格

- 每项（display: grid，grid-template-columns: 100px 1fr，border-bottom: 1px solid var(--border)）：
  - 时间栏（padding: 20px 16px，background: var(--surface)，border-right: 1px solid var(--border)；Barlow Condensed 600，13px，color: var(--purple)）
  - 内容栏（padding: 20px 24px）：标题（Noto Sans SC 700，14px）+ 说明（Noto Sans SC 300，12px，color: var(--ink-dim)）

### 5. Speaker / Highlight Cards 亮点卡片

- padding: 24px 36px，display: grid，grid-template-columns: 1fr 1fr，gap: 16px
- 卡片（background: var(--card)，border: 1px solid var(--border)，border-radius 8px，padding 24px，position relative，overflow hidden）
- 顶部色条（height 3px，background: linear-gradient(90deg, var(--accent), var(--purple))，position absolute，top 0，left/right 0）
- 姓名/标题（Noto Sans SC 700，14px）+ 身份/说明（Noto Sans SC 300，12px，color: var(--ink-dim)）

### 6. CTA Band 行动号召条

- background: linear-gradient(135deg, var(--accent), var(--purple))，padding: 32px 36px，text-align: center
- 标题（Noto Sans SC 900，clamp(18px, 4vw, 28px)，color: #fff）
- 按钮（display: inline-block，padding: 12px 32px，border: 2px solid #fff，border-radius 4px；Barlow Condensed 700，13px，color: #fff，uppercase，margin-top 20px）

### 7. Footer 底栏

- background: var(--surface)，padding: 16px 36px，display: flex，justify-content: space-between，border-top: 1px solid var(--border)
- 左（Barlow Condensed 400，10px，color: var(--ink-mute)）
- 右（Bebas Neue 18px，color: var(--border)，letter-spacing 0.2em）
