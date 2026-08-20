# WELLNESS 柔和有机 · 身心疗愈风

**适用**：健康养生、冥想正念、心理疗愈、瑜伽运动、生活方式

---

## CSS 变量

```
--bg:          #faf5ff
--surface:     #ffffff
--card:        #ffffff
--border:      #ede9fe
--ink:         #1e1b4b
--ink-dim:     #64748b
--ink-mute:    #a8a29e
--accent:      #8b5cf6
--accent-lt:   #c4b5fd
--accent-bg:   rgba(139,92,246,0.06)
--green:       #059669
--green-lt:    #10b981
--green-bg:    rgba(5,150,105,0.06)
--warm:        #f5f0eb
```

body 外部背景：`#f3e8ff`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600;900&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/引言：`Lora` italic 或 weight 600-700
- 中文标题：`Noto Serif SC` weight 900
- 中文正文：`Noto Serif SC` weight 300，line-height 2.1，font-size 13.5px
- 标签：`Lora` weight 500，font-size 10px，letter-spacing 0.15em

## 版式模块

### 1. Soft Header 柔和顶栏

- padding: 18px 36px，display: flex，justify-content: space-between，border-bottom: 1px solid var(--border)
- 品牌名（Lora 500，13px，letter-spacing 0.2em，color: var(--accent)）
- 分类（Lora 400 italic，11px，color: var(--ink-mute)）

### 2. Hero 主视觉区

- padding: 56px 40px 44px，background: var(--surface)，text-align: center
- 装饰符号（Lora italic 48px，color: var(--accent-lt)，opacity 0.5）—— ✦ ❋ ○
- 主标题（Noto Serif SC 900，clamp(30px, 7vw, 50px)，line-height 1.15，color: var(--ink)）
- 副标题（Lora italic 400，15px，color: var(--ink-dim)，max-width 440px，margin: 16px auto 0）
- 装饰线（width 60px，height 2px，background: var(--accent-lt)，margin: 28px auto 0）

### 3. Breath Quote 呼吸引言

- padding: 36px 40px，background: var(--warm)，text-align: center
- 引文（Noto Serif SC 300，clamp(14px, 2.5vw, 17px)，color: var(--ink)，line-height 1.9，font-style italic；关键词 color: var(--accent) weight 600）
- 来源（Lora 400，11px，color: var(--ink-mute)，margin-top 14px，letter-spacing 0.2em）

### 4. Gentle Columns 柔和双栏

- padding: 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 36px
- 段落首行不缩进，段间距 margin-top 1.4em

### 5. Insight Card 洞察卡

- margin: 0 36px，background: var(--accent-bg)，border-radius 16px，padding: 28px 32px
- 标签（Lora 500，10px，color: var(--accent)，uppercase，margin-bottom 12px）
- 洞察（Noto Serif SC 600，16px，color: var(--ink)）
- 说明（Noto Serif SC 300，12.5px，color: var(--ink-dim)，line-height 1.9，margin-top 10px）

### 6. Practice Steps 练习步骤

有具体练习/操作时使用。

- padding: 36px 40px
- 每步（margin-bottom 24px，padding-left 24px，border-left: 2px solid var(--accent-lt)）：
  - 编号（Lora 500，10px，color: var(--accent)）
  - 标题（Noto Serif SC 600，14px，margin: 6px 0 8px）
  - 正文（Noto Serif SC 300，12.5px，color: var(--ink-dim)，line-height 1.9）

### 7. Nature Band 自然色带

- background: var(--green-bg)，padding: 32px 40px，border-radius 16px，margin: 0 20px
- 文字（Noto Serif SC 300，14px，color: var(--green)，text-align center）

### 8. Closing 柔和结尾

- padding: 48px 40px，text-align: center
- 装饰符号（color: var(--accent-lt)，opacity 0.3）
- 结语（Noto Serif SC 900，clamp(20px, 4vw, 30px)，color: var(--ink)）
- 日期（Lora italic 400，11px，color: var(--ink-mute)，margin-top 16px）
