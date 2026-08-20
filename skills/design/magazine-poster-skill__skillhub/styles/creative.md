# CREATIVE 极简黑白 · 画廊展览风

**适用**：设计作品、艺术创作、摄影分享、视觉灵感、审美表达

---

## CSS 变量

```
--bg:        #fafafa
--surface:   #ffffff
--ink:       #09090b
--ink-dim:   #3f3f46
--ink-mute:  #a1a1aa
--border:    #e4e4e7
--accent:    #09090b
--pop:       #2563eb
```

body 外部背景：`#d4d4d8`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;700;900&family=Syne:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/装饰：`Syne` weight 700-800，letter-spacing -0.03em
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.9，font-size 13px
- 编号/标注：`Syne` weight 500，font-size 10px，letter-spacing 0.2em

## 版式模块

### 1. Gallery Header 画廊顶栏

- padding: 20px 40px，display: flex，justify-content: space-between，align-items: baseline，border-bottom: 2px solid var(--ink)
- 展览名（Syne 800，16px，uppercase，color: var(--ink)）
- 日期（Syne 500，10px，color: var(--ink-mute)，letter-spacing 0.2em）

### 2. Hero 主视觉区

- padding: 72px 40px 56px
- 主标题（Noto Sans SC 900，clamp(42px, 10vw, 80px)，line-height 0.9，letter-spacing -0.04em，color: var(--ink)）
- 副标题（Syne 500，13px，color: var(--ink-mute)，letter-spacing 0.15em，uppercase，margin-top 24px）
- 装饰线（width 40px，height 2px，background: var(--ink)，margin-top 40px）

### 3. Statement 宣言区

- padding: 48px 40px，border-top/bottom: 1px solid var(--border)
- 引文（Noto Sans SC 300，clamp(16px, 3vw, 22px)，color: var(--ink)，line-height 1.8，max-width 560px；关键词 color: var(--pop)）

### 4. Grid Works 作品网格

- padding: 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 2px（极窄间距）
- 作品块（background: var(--surface)，padding: 32px 28px）
- 编号（Syne 500，10px，color: var(--ink-mute)，letter-spacing 0.2em，margin-bottom 16px）
- 标题（Noto Sans SC 700，16px，color: var(--ink)）
- 说明（Noto Sans SC 300，12px，color: var(--ink-dim)，line-height 1.9，margin-top 10px）

### 5. Solo Text 独白文字区

- padding: 56px 40px，max-width 480px
- 正文（Noto Sans SC 300，13px，line-height 2.0；段间距 margin-top 1.6em）

### 6. Colophon 版权页式结尾

- padding: 40px，border-top: 2px solid var(--ink)
- display: grid，grid-template-columns: 1fr auto
- 左结语（Noto Sans SC 900，clamp(18px, 4vw, 28px)，color: var(--ink)）
- 右元数据（Syne 500，10px，color: var(--ink-mute)，letter-spacing 0.15em，line-height 2.0，text-align right）
