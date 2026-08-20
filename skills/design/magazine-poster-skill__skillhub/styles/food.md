# FOOD 暖土食欲 · 美食杂志风

**适用**：美食探店、餐厅推荐、食谱分享、烹饪技巧、饮品文化

---

## CSS 变量

```
--bg:           #fffbeb
--surface:      #fff8e1
--card:         #ffffff
--border:       #fde68a
--ink:          #1c1917
--ink-dim:      #78716c
--ink-mute:     #a8a29e
--accent:       #9a3412
--accent-lt:    #c2410c
--accent-warm:  #d97706
--cream:        #fef3c7
--green:        #15803d
--green-bg:     rgba(21,128,61,0.06)
```

body 外部背景：`#fde68a`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600;900&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/引言/装饰：`Cormorant Garamond` weight 600-700 或 italic
- 中文标题：`Noto Serif SC` weight 900
- 中文正文：`Noto Serif SC` weight 300，line-height 2.0，font-size 13.5px
- 标签/品名/评分：`Cormorant Garamond` weight 500，letter-spacing 0.15em

## 版式模块

### 1. Plate Header 餐盘顶栏

- padding: 16px 36px，display: flex，justify-content: space-between，border-bottom: 2px solid var(--ink)
- 品牌名（Cormorant Garamond 600，14px，letter-spacing 0.25em，uppercase）
- 分类（Cormorant Garamond 400 italic，11px，color: var(--ink-dim)）

### 2. Hero 主视觉区

- padding: 48px 40px 40px
- 标签行（Cormorant Garamond 500，10px，letter-spacing 0.3em，uppercase，color: var(--accent-warm)）
- 主标题（Noto Serif SC 900，clamp(36px, 8vw, 62px)，line-height 1.0，color: var(--ink)；食材关键词 color: var(--accent)）
- 副标题（Cormorant Garamond italic 500，16px，color: var(--ink-dim)，margin-top 14px）
- 风味指标条（display: flex，gap 24px，margin-top 28px，padding-top 20px，border-top: 1px solid var(--border)）：数值（Cormorant Garamond 700，28px，color: var(--accent)）+ 标签（10px，uppercase，color: var(--ink-dim)）

### 3. Flavor Quote 风味引言

- background: var(--accent)，padding: 28px 40px
- 引文（Noto Serif SC 300，clamp(14px, 2.5vw, 17px)，color: var(--cream)，text-align center；关键词 weight 600 color: #fff）

### 4. Recipe Grid 食谱/探店双栏

- padding: 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 36px

### 5. Ingredient Card 食材/亮点卡

- background: var(--surface)，border: 1px solid var(--border)，border-radius 8px，padding 24px，margin: 0 36px 16px
- 食材名（Cormorant Garamond 700，18px）
- 说明（Noto Serif SC 300，12.5px，color: var(--ink-dim)，line-height 1.9，margin-top 8px）
- 风味标签（Cormorant Garamond 500，10px，padding: 3px 10px，border: 1px solid var(--border)，border-radius 100px，color: var(--accent-warm)）

### 6. Chef's Note 厨师手记

- padding: 32px 40px，background: var(--cream)，border-top/bottom: 1px solid var(--border)
- display: grid，grid-template-columns: 4px 1fr，gap 20px
- 左竖线：background: var(--accent)
- 正文（Noto Serif SC 300，13px，color: var(--ink)，line-height 2.0，font-style italic）

### 7. Footer 底栏

- padding: 20px 40px，border-top: 2px solid var(--ink)，display: flex，justify-content: space-between
- 左（Cormorant Garamond italic 400，11px，color: var(--ink-mute)）
- 右（Cormorant Garamond 600，12px，letter-spacing 0.2em，uppercase，color: var(--ink-dim)）
