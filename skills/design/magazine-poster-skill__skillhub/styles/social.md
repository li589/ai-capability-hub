# SOCIAL 柔粉浪漫 · 社交分享风

**适用**：个人感悟、朋友圈分享、情感表达、日常记录、心情随笔

---

## CSS 变量

```
--bg:          #fdf2f8
--surface:     #ffffff
--card:        #ffffff
--border:      #fbcfe8
--ink:         #1e1b4b
--ink-dim:     #64748b
--ink-mute:    #a8a29e
--accent:      #ec4899
--accent-lt:   #f9a8d4
--accent-bg:   rgba(236,72,153,0.06)
--violet:      #8b5cf6
--violet-bg:   rgba(139,92,246,0.06)
```

body 外部背景：`#fce7f3`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Quicksand:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/标签：`Quicksand` weight 600-700
- 中文标题：`Noto Sans SC` weight 700（不用 900，更柔和）
- 中文正文：`Noto Sans SC` weight 300，line-height 2.0，font-size 13.5px
- 装饰文字：`Quicksand` weight 400

## 版式模块

### 1. Soft Header 柔和顶栏

- padding: 16px 36px，display: flex，justify-content: center
- 品牌名（Quicksand 600，12px，letter-spacing 0.25em，color: var(--accent)，uppercase）

### 2. Hero 主视觉区

- padding: 48px 40px 40px，background: var(--surface)，text-align center，border-radius: 0 0 24px 24px
- 装饰 emoji（font-size 36px，opacity 0.7）—— 根据内容选 ✨ 🌸 💭 🌙
- 主标题（Noto Sans SC 700，clamp(26px, 6vw, 42px)，line-height 1.2，color: var(--ink)）
- 副标题（Noto Sans SC 300，14px，color: var(--ink-dim)，max-width 400px，margin: 12px auto 0）
- 日期/场景（Quicksand 500，11px，color: var(--ink-mute)，margin-top 20px）

### 3. Mood Card 心情卡片

- margin: 16px 24px，background: var(--accent-bg)，border-radius 20px，padding: 28px 32px
- 引文（Noto Sans SC 400，clamp(14px, 2.5vw, 16px)，color: var(--ink)，text-align center；关键词 color: var(--accent) weight 500）

### 4. Story Flow 故事单栏

- padding: 32px 40px
- 正文（max-width 500px，margin: 0 auto；段间距 margin-top 1.4em；首行不缩进）

### 5. Photo Moment 照片时刻

用纯 CSS 模拟照片卡效果。

- margin: 16px 24px，background: var(--surface)，border-radius 16px，overflow hidden，box-shadow: 0 2px 12px rgba(0,0,0,0.04)
- 色块（height 120px，background: linear-gradient(135deg, var(--accent-bg), var(--violet-bg))）
- 文字区（padding: 20px 24px）：标题（Noto Sans SC 500，14px）+ 说明（Noto Sans SC 300，12px，color: var(--ink-dim)）

### 6. Tag Cloud 标签云

- padding: 20px 40px，display: flex，flex-wrap: wrap，gap 8px，justify-content: center
- 标签（Quicksand 500，11px，padding: 6px 14px，border-radius 100px，border: 1px solid）
- 颜色交替：粉色 var(--accent-lt)/var(--accent) 和紫色 rgba(139,92,246,0.3)/var(--violet)

### 7. Closing 柔和结尾

- padding: 40px，text-align: center
- 结语（Noto Sans SC 700，clamp(18px, 4vw, 28px)，color: var(--ink)）
- 签名（Quicksand 500，11px，color: var(--ink-mute)，margin-top 16px）
- 装饰（margin-top 20px，color: var(--accent-lt)，font-size 20px）—— ♡ ✦
