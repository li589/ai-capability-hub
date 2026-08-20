# PRODUCT 磨砂玻璃 · 产品展示风

**适用**：产品介绍、功能说明、产品评测、开箱体验、硬件展示

---

## CSS 变量

```
--bg:            #0f172a
--surface:       #1e293b
--card:          rgba(255,255,255,0.05)
--card-border:   rgba(255,255,255,0.1)
--border:        rgba(255,255,255,0.08)
--ink:           #f8fafc
--ink-dim:       #94a3b8
--ink-mute:      #475569
--accent:        #3b82f6
--accent-lt:     #60a5fa
--gradient-1:    #3b82f6
--gradient-2:    #8b5cf6
--green:         #22c55e
--amber:         #f59e0b
```

body 外部背景：`#020617`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/标签/数字：`Space Grotesk` weight 600-700
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.85，font-size 13px
- 规格标签：`Space Grotesk` weight 500，font-size 10px，letter-spacing 0.12em

## 版式模块

### 1. Glass Header 玻璃顶栏

- background: rgba(255,255,255,0.03)，backdrop-filter: blur(10px)，-webkit-backdrop-filter: blur(10px)
- padding: 14px 36px，display: flex，justify-content: space-between，border-bottom: 1px solid var(--border)
- 品牌名（Space Grotesk 700，14px，color: var(--ink)）
- 产品线（Space Grotesk 500，10px，color: var(--ink-dim)，uppercase）

### 2. Hero 主视觉区

- padding: 56px 36px 44px，position: relative
- 背景光晕（position absolute，300px，radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)，top -50px，right -50px，pointer-events none）
- 标签行（Space Grotesk 500，10px，color: var(--accent-lt)，uppercase）
- 主标题（Noto Sans SC 900，clamp(32px, 7vw, 56px)，line-height 1.05，color: var(--ink)；关键词渐变 gradient-1→gradient-2 + background-clip text）
- 副标题（Noto Sans SC 300，14px，color: var(--ink-dim)，max-width 460px，margin-top 14px）

### 3. Spec Cards 规格卡片行

- display: grid，grid-template-columns: repeat(3, 1fr)，gap: 12px，padding: 24px 36px
- 卡片（background: var(--card)，border: 1px solid var(--card-border)，border-radius 12px，padding 20px，backdrop-filter: blur(8px)）
- 数值（Space Grotesk 700，clamp(24px, 4vw, 36px)，color: var(--ink)）
- 标签（Space Grotesk 500，10px，color: var(--ink-dim)，uppercase，margin-top 6px）

### 4. Feature Highlight 功能亮点双栏

- display: grid，grid-template-columns: 1fr 1fr，border-top/bottom: 1px solid var(--border)
- 左栏 border-right: 1px solid var(--border)
- 每项（padding 28px）：功能名（Noto Sans SC 700，15px）+ 说明（12.5px，color: var(--ink-dim)）+ 标签（Space Grotesk 500，10px，padding: 3px 10px，border-radius 4px；绿色/蓝色方案）

### 5. Glass Quote 玻璃引言

- margin: 24px 36px，background: var(--card)，border: 1px solid var(--card-border)，border-radius 16px，padding: 28px 32px，backdrop-filter: blur(8px)
- 引文（Noto Sans SC 500，clamp(14px, 2.5vw, 17px)，color: var(--ink)）
- 来源（Space Grotesk 500，10px，color: var(--ink-dim)，margin-top 12px）

### 6. Verdict 评分/结论区

- padding: 36px，background: var(--surface)，border-top: 1px solid var(--border)
- 标题（Noto Sans SC 900，clamp(20px, 4vw, 30px)，color: var(--ink)）
- 评分（Space Grotesk 700，48px，渐变文字同 Hero）
- 说明（Noto Sans SC 300，13px，color: var(--ink-dim)，margin-top 12px）

### 7. Footer 底栏

- padding: 16px 36px，border-top: 1px solid var(--border)，display: flex，justify-content: space-between
- 左/右（Space Grotesk 400-500，10px，color: var(--ink-mute)）
