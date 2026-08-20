# CLAUDE 温暖知性 · Claude 暖赭石风

**适用**：AI 工具心得、Claude 使用记录、知识整理、学习复盘、个人思考梳理、经验总结、对话精选

---

## CSS 变量

```
--bg:          #f5f4ed   /* 羊皮纸主背景 */
--paper-warm:  #ede9e0   /* 次级暖白 */
--card:        #faf9f5   /* 卡片背景 */
--ink:         #26251e   /* 深墨色主文字 */
--ink-dim:     #5c5a52   /* 次要文字 */
--ink-mute:    #9a978e   /* 辅助文字 */
--border:      #d8d4cb   /* 边框线 */
--accent:      #c96442   /* 赭石强调色 */
--accent-lt:   #e8a090   /* 浅赭石 */
--accent-deep: #b54e2d   /* 赭石深红（顶栏/结尾背景） */
```

body 外部背景：`#1a1814`
page-wrapper 背景：`var(--bg)`

---

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600;900&family=EB+Garamond:ital,wght@0,400;0,500;1,400;1,500&display=swap" rel="stylesheet">
```

## 字体使用规则

- 中文标题：`Noto Serif SC` weight 900，font-size: clamp(36px, 7vw, 64px)，line-height 1.05，letter-spacing -0.01em
- 中文正文：`Noto Serif SC` weight 300，font-size 13.5px，line-height 2.0，color: var(--ink)
- 英文引言/装饰：`EB Garamond` italic，font-size 15px，letter-spacing 0.02em
- 标签/期号/数据：`EB Garamond` 11px，letter-spacing 0.3em，text-transform uppercase，color: var(--ink-mute)

---

## 版式模块

### 1. Masthead 顶栏

固定使用，每张海报顶部。

- background: var(--accent-deep)，padding: 16px 36px
- 三栏 flex，align-items: center，justify-content: space-between
- 左：分类标签（EB Garamond 10px，uppercase，letter-spacing 0.4em，color: rgba(255,255,255,0.55)）
- 中：刊名「CLAUDE」（Noto Serif SC 900，13px，letter-spacing 0.25em，color: #ffffff）
- 右：期号/日期（EB Garamond 10.5px，letter-spacing 0.3em，color: rgba(255,255,255,0.45)）
- border-bottom: none（与 Hero 直接相连）

### 2. Hero 主视觉区

固定使用，紧接 Masthead。

- background: var(--bg)，padding: 48px 36px 40px
- border-bottom: 2px solid var(--ink)
- 眉题（EB Garamond 10.5px，uppercase，letter-spacing 0.35em，color: var(--accent)，margin-bottom 20px）
- 主标题（Noto Serif SC 900，font-size: clamp(36px, 7vw, 64px)，line-height 1.05，letter-spacing -0.01em，color: var(--ink)）
- 主标题下方装饰线：`::after { content:""; display:block; width:48px; height:3px; background:var(--accent); margin-top:20px; border-radius:2px }`
- 副标题（Noto Serif SC 300，font-size 14px，color: var(--ink-dim)，line-height 1.75，margin-top 20px，max-width 420px）

### 3. Pull Quote 引言带

有核心金句时使用。

- background: var(--ink)，padding: 32px 36px，border-bottom: 1.5px solid #2a2820
- display: flex，align-items: flex-start，gap: 20px
- 左大引号（EB Garamond 80px，color: var(--accent)，line-height 0.65，opacity 0.55，flex-shrink: 0）
- 引文（Noto Serif SC 300，font-size: clamp(14px, 2.5vw, 18px)，color: var(--bg)，line-height 1.8，letter-spacing 0.03em）
- 关键词用 `<strong>` 加粗，color: var(--accent-lt)

### 4. Body Columns 双栏正文

主要内容区，适合段落叙述。

- padding: 40px 36px，display: grid，grid-template-columns: 1fr 1fr，gap: 0 36px
- border-bottom: 1.5px solid var(--border)
- 正文：Noto Serif SC 300，13.5px，line-height 2.0，color: var(--ink)
- 段落间距：margin-top 1.1em
- 右栏可放补充引用：border-left: 1.5px solid var(--border)，padding-left 24px

### 5. Insight Card Grid 洞察卡片组

3~4 个核心观点时使用，每个卡片一个洞察。

- padding: 36px 36px 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 16px
- border-bottom: 1.5px solid var(--border)
- 卡片（background: var(--card)，border-left: 3px solid var(--accent)，border-radius: 4px，padding: 20px 20px 18px）：
  - 序号（EB Garamond 11px，uppercase，letter-spacing 0.3em，color: var(--accent)，margin-bottom 10px）
  - 标题（Noto Serif SC 600，14px，color: var(--ink)，line-height 1.4，margin-bottom 8px）
  - 正文（Noto Serif SC 300，12.5px，color: var(--ink-dim)，line-height 1.85）

### 6. Mid Section 中间深色带

结构性转折或关键结论时使用。

- background: var(--accent-deep)，padding: 36px 36px，border-bottom: 1.5px solid #9a3820
- display: grid，grid-template-columns: auto 1fr，gap: 0 28px，align-items: start
- 左侧竖线：width 3px，background: rgba(255,255,255,0.35)，flex-shrink: 0，border-radius 2px
- 结论文字（Noto Serif SC 300，font-size: clamp(14px, 2.5vw, 18px)，color: rgba(255,255,255,0.92)，line-height 1.85）
- 来源/说明（EB Garamond italic 12px，color: rgba(255,255,255,0.5)，margin-top 12px）

### 7. Key Points 要点列表

分条阐述要点、步骤或原则时使用。

- padding: 36px 36px 32px，border-bottom: 1.5px solid var(--border)
- 区块标题（Noto Serif SC 600，12px，uppercase，letter-spacing 0.2em，color: var(--accent)，margin-bottom 24px）
- 每个要点（display: flex，gap: 16px，margin-bottom 18px）：
  - 序号（EB Garamond 13px，letter-spacing 0.15em，color: var(--accent)，min-width 24px，padding-top 2px）
  - 要点文字（Noto Serif SC 300，13px，color: var(--ink)，line-height 1.85）
- 要点间分隔：border-bottom 1px solid var(--border)，padding-bottom 18px（末项除外）

### 8. Wide Quote 宽幅引言

结尾前强调一句话时使用。

- padding: 44px 36px，background: var(--paper-warm)，border-bottom: 1.5px solid var(--border)，text-align: center
- 大引号（EB Garamond 100px，color: var(--accent)，opacity 0.2，line-height 0.5，display: block，margin-bottom 16px）
- 引文（Noto Serif SC 300，font-size: clamp(16px, 3vw, 22px)，color: var(--ink)，line-height 1.75，max-width 480px，margin: 0 auto）
- 来源（EB Garamond 11px，uppercase，letter-spacing 0.25em，color: var(--ink-mute)，margin-top 20px）

### 9. Coda 结尾

固定使用，每张海报底部。

- background: var(--ink)，padding: 36px 36px 32px
- display: flex，justify-content: space-between，align-items: flex-end
- 左侧结句（Noto Serif SC 900，font-size: clamp(18px, 3.5vw, 28px)，color: var(--bg)，line-height 1.3）；若有副句另起一行，color: var(--accent-lt)，font-weight 300，font-size 13px
- 右侧元信息（text-align right）：日期（EB Garamond 10.5px，uppercase，letter-spacing 0.3em，color: #3a3830）+ 来源（Noto Serif SC 300，11px，color: #3a3830）
- 底部细线（border-top: 1px solid #2a2820，padding-top 16px，grid-column 1/-1）
