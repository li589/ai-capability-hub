# EDUCATION 清新明亮 · 知识卡片风

**适用**：课程介绍、知识科普、教学大纲、学习笔记、学术分享

---

## CSS 变量

```
--bg:          #eef2ff
--surface:     #ffffff
--card:        #ffffff
--border:      #c7d2fe
--ink:         #1e1b4b
--ink-dim:     #64748b
--ink-mute:    #94a3b8
--accent:      #4f46e5
--accent-lt:   #818cf8
--accent-bg:   rgba(79,70,229,0.06)
--orange:      #ea580c
--orange-bg:   rgba(234,88,12,0.06)
--green:       #059669
--green-bg:    rgba(5,150,105,0.06)
```

body 外部背景：`#e0e7ff`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/数字/标签：`Outfit` weight 700-800
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.9，font-size 13.5px
- 标签丸/编号：`Outfit` weight 600，font-size 10px，letter-spacing 0.1em

## 版式模块

### 1. Top Bar 课程头

- background: var(--accent)，padding: 14px 36px，display: flex，justify-content: space-between
- 系列名（Outfit 600，12px，color: rgba(255,255,255,0.8)，uppercase）
- 课节编号（Outfit 700，12px，color: #fff）

### 2. Hero 主视觉区

- padding: 48px 36px 40px，background: var(--surface)，border-bottom: 1px solid var(--border)，border-radius: 0 0 20px 20px
- 标签丸（background: var(--accent-bg)，color: var(--accent)，Outfit 600，10px，padding: 6px 14px，border-radius 100px）
- 主标题（Noto Sans SC 900，clamp(32px, 7vw, 52px)，line-height 1.08，color: var(--ink)，margin-top 16px）
- 副标题（Noto Sans SC 300，14px，color: var(--ink-dim)，max-width 500px，margin-top 14px）
- 学习目标条（margin-top 24px，display: flex，flex-wrap: wrap，gap 8px）：目标丸（background: var(--orange-bg)，color: var(--orange)，Outfit 600，10px，padding: 5px 12px，border-radius 100px）

### 3. Outline Cards 知识点卡片

- padding: 28px 36px，display: grid，grid-template-columns: 1fr 1fr，gap: 16px
- 卡片（background: var(--card)，border: 1px solid var(--border)，border-radius 14px，padding 24px，position relative，overflow hidden）
- 卡片右上角序号（position absolute，top -8px，right 16px，Outfit 800，64px，color: var(--accent)，opacity 0.06）
- 标签（Outfit 600，10px，color: var(--accent)，uppercase）
- 标题（Noto Sans SC 700，15px，color: var(--ink)）
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.8，margin-top 10px）

### 4. Key Concept Band 核心概念条

- background: var(--accent)，padding: 28px 36px，border-radius 16px，margin: 0 20px
- 文字（Noto Sans SC 700，clamp(14px, 2.5vw, 18px)，color: #fff，text-align center）
- 关键词 em：color: rgba(255,255,255,0.7)，font-style normal

### 5. Steps Flow 步骤流程

- padding: 36px
- 每步（display: flex，gap 16px，margin-bottom 20px）：
  - 圆编号（32px，border-radius 50%，background: var(--accent)；Outfit 700 13px color: #fff）
  - 标题（Noto Sans SC 700，14px）+ 说明（Noto Sans SC 300，12.5px，color: var(--ink-dim)，margin-top 6px）
- 步骤间竖线（::after，width 2px，background: var(--border)）

### 6. Tips Card 小贴士卡

- margin: 0 36px，background: var(--green-bg)，border: 1px solid rgba(5,150,105,0.2)，border-radius 12px，padding: 20px 24px
- 标题（Outfit 700，12px，color: var(--green)）前缀 💡
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.8，margin-top 8px）

### 7. Summary 课程总结

- padding: 36px，background: var(--surface)，border-radius 16px，margin: 20px
- 标签（Outfit 700，11px，color: var(--accent)，uppercase，margin-bottom 16px）
- 每条（checkmark color: var(--green) + 文字 Noto Sans SC 400，13px）

### 8. Footer 底栏

- padding: 20px 36px，display: flex，justify-content: space-between
- 左（Noto Sans SC 300，11px，color: var(--ink-mute)）
- 右（Outfit 600，11px，color: var(--accent-lt)）
