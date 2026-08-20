# LITERARY 暖色纸质 · 人文杂志风

**适用**：文学散文、游记、个人叙事、诗意长文、文学评论、读书笔记

---

## CSS 变量

```
--paper:       #f4f0e8
--paper-warm:  #ede8dc
--ink:         #0f0d0b
--cream:       #e8e2d4
--grey-mid:    #6b6560
--grey-light:  #9a9490
--bone:        #d4ccc0
--accent-rust: #8b4a3a
--accent-ice:  #7a8fa0
--col-blue:    #2a3d4f
```

body 外部背景：`#1a1814`
page-wrapper 背景：`var(--paper)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600;900&family=EB+Garamond:ital,wght@0,400;0,500;1,400;1,500&display=swap" rel="stylesheet">
```

## 字体使用规则

- 中文标题：`Noto Serif SC` weight 900
- 中文正文：`Noto Serif SC` weight 300，line-height 2.0，font-size 13.5px
- 英文引言/标注/期号：`EB Garamond` italic
- 首字下沉：`EB Garamond` weight 500，color: var(--accent-rust)，font-size 3.6em，float left

## 版式模块

### 1. Masthead 顶栏

- 三栏 flex 布局：左标签 | 中刊名 | 右期号/日期
- border-bottom: 2px solid var(--ink)，padding: 18px 40px
- 字体：EB Garamond 10px，letter-spacing 0.35em，text-transform uppercase，color: var(--grey-mid)
- 中间刊名：Noto Serif SC 900，13px，letter-spacing 0.2em，color: var(--ink)

### 2. Hero 主视觉区

- display: grid，grid-template-columns: 1fr 1fr，border-bottom: 1.5px solid var(--bone)
- 左栏（padding: 52px 0 44px，border-right: 1.5px solid var(--bone)，padding-right: 36px）：
  - 眉题（EB Garamond 10.5px，letter-spacing 0.3em，uppercase，color: var(--grey-light)）
  - 主标题（Noto Serif SC 900，font-size: clamp(48px, 9vw, 74px)，line-height 0.92，letter-spacing -0.02em）
  - 副标题（EB Garamond italic 15px，color: var(--grey-mid)，line-height 1.6）
- 右栏（padding-left: 36px）：
  - 装饰大数字（EB Garamond 120px，color: var(--cream)，text-align right，user-select none）
  - 作者名（Noto Serif SC 600，16px，letter-spacing 0.15em）+ 英文注（EB Garamond 11px，uppercase，letter-spacing 0.25em，color: var(--grey-light)）

### 3. Pull Quote Bar 引言条

- background: var(--ink)，padding: 28px 40px，display: flex，align-items: center，gap: 24px
- 左侧大引号（EB Garamond 72px，color: var(--accent-ice)，line-height 0.7，opacity 0.6）
- 引文（Noto Serif SC 300，font-size: clamp(14px, 2.5vw, 17px)，color: var(--paper)，line-height 1.7，letter-spacing 0.04em）
- 关键词：font-weight 600，color: var(--accent-ice)

### 4. Body Columns 正文双栏

- padding: 44px 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 0 40px，border-bottom: 1.5px solid var(--bone)
- 正文：Noto Serif SC 300，13.5px，line-height 2.0，color: var(--ink)
- 段落间距：margin-top 1.2em
- 首字下沉（仅第一列第一段 p:first-child::first-letter）：EB Garamond 3.6em，weight 500，float left，line-height 0.75，margin-right 6px，color: var(--accent-rust)

### 5. Mid Quote 旁注引用

有高价值引用时使用。

- padding: 40px，background: var(--paper-warm)，border-bottom: 1.5px solid var(--bone)
- display: grid，grid-template-columns: 4px 1fr，gap: 0 24px
- 左竖线：width 4px，background: var(--accent-rust)
- 中文说明（Noto Serif SC 300，13px，color: var(--grey-mid)，line-height 1.9）
- 英文引文（EB Garamond italic 15px，color: var(--ink)，line-height 1.6）
- 来源（EB Garamond 11px，letter-spacing 0.25em，uppercase，color: var(--grey-light)，margin-top 10px）

### 6. Section Head 章节标题

内容分段时插入。

- padding: 0 40px，display: flex，align-items: stretch，border-bottom: 1.5px solid var(--bone)
- 左竖排编号（§ I / § II / § III）：writing-mode vertical-rl，EB Garamond 11px，letter-spacing 0.3em，color: var(--grey-light)，border-right: 1px solid var(--bone)，padding 20px
- 右标题区（padding: 24px 0）：
  - 主标题：Noto Serif SC 900，font-size: clamp(24px, 5vw, 38px)，line-height 1.1
  - 英文副标题：EB Garamond italic 13px，color: var(--grey-mid)，margin-top 8px

### 7. Wide Single Column 单栏段落

叙述性段落使用。

- padding: 40px，border-bottom: 1.5px solid var(--bone)
- 段落 max-width: 540px
- 正文同 Body Columns 规格

### 8. Contrast Band 对比深色区

情感高潮段落使用。

- background: var(--col-blue)，padding: 44px 40px，border-bottom: 1.5px solid var(--bone)
- display: grid，grid-template-columns: 1fr 1fr，gap: 40px，align-items: end
- 左栏：小标签（EB Garamond 10px，uppercase，letter-spacing 0.4em，color: var(--accent-ice)，opacity 0.7）+ 大引文（Noto Serif SC 300，font-size: clamp(15px, 3vw, 20px)，color: var(--paper)，line-height 1.8）
- 右栏：补充说明（EB Garamond italic 13px，color: var(--accent-ice)，opacity 0.8，border-left: 2px solid var(--accent-ice)，padding-left 16px）

### 9. Coda 结尾

- background: var(--ink)，padding: 44px 40px
- display: grid，grid-template-columns: 1fr auto，gap: 40px，align-items: end
- 左祝语/结句：Noto Serif SC 900，font-size: clamp(22px, 5vw, 36px)，color: var(--paper)，line-height 1.3；金句/年份另起一行 color: var(--accent-ice)
- 右元信息：text-align right；日期（EB Garamond 11px，uppercase，letter-spacing 0.3em，color: var(--grey-light)）+ 场景描述（Noto Serif SC 300，12px，color: var(--grey-mid)）
- 底部分隔线（grid-column: 1/-1，border-top: 1px solid #2a2820，padding-top 20px）：两端 EB Garamond 11px，color: #3a3830
