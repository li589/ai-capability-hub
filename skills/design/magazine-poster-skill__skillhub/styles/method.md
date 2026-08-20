# METHOD 暗色工业 · 策略手册风

**适用**：方法论、SOP、工作流、策略分析、操作指南、复盘框架

---

## CSS 变量

```
--bg:        #0d0d0f
--surface:   #131317
--card:      #1a1a1f
--border:    #2a2a32
--border-lt: #383844
--ink:       #e8e6e0
--ink-dim:   #8a8890
--ink-mute:  #4a4855
--accent:    #f0c060
--accent-lt: #f5d48a
--red:       #c85a42
--green:     #4a9068
--blue-lt:   #7aaccf
```

body 外部背景：`#080808`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Bebas+Neue&display=swap" rel="stylesheet">
```

## 字体使用规则

- 大标题/装饰数字/品牌名：`Bebas Neue`，letter-spacing 0.02~0.3em
- 中文正文/标题：`Noto Sans SC`，正文 weight 300，标题 weight 700/900
- 标签/编号/代码/数据标注：`DM Mono`，font-size 10px，letter-spacing 0.12em

## 版式模块

### 1. Masthead 顶栏

- display: flex，justify-content: space-between，padding: 14px 36px
- background: var(--surface)，border-bottom: 1px solid var(--border)
- 左：系列标识（DM Mono 10px，color: var(--ink-dim)，letter-spacing 0.12em）
- 中：品牌名（Bebas Neue 18px，letter-spacing 0.25em，color: var(--accent)）
- 右：内容分类（DM Mono 10px，color: var(--ink-dim)）

### 2. Hero 主视觉区

- padding: 52px 36px 0，border-bottom: 1px solid var(--border)，position: relative，overflow: hidden
- 背景装饰文字（position absolute，right -10px，top 10px，Bebas Neue 200px，color: var(--border)，user-select none，pointer-events none，z-index 0）
- 标签行（DM Mono 10px，letter-spacing 0.35em，uppercase，color: var(--accent)，display: flex，gap 10px；前置 24px 横线 background: var(--accent)）
- 主标题（Noto Sans SC 900，font-size: clamp(36px, 7vw, 62px)，line-height 1.05，color: var(--ink)；关键词 em 标签 color: var(--accent)）
- 副标题（Noto Sans SC 300，14px，color: var(--ink-dim)，line-height 1.7，max-width 420px，margin-bottom 36px）
- 底部指标栏（display: grid，grid-template-columns: repeat(3, 1fr)，border-top: 1px solid var(--border)）：
  - 数字：Bebas Neue 42px，color: var(--accent)
  - 标签：DM Mono 10px，color: var(--ink-dim)，letter-spacing 0.15em，uppercase

### 3. Logic Bar 核心逻辑条

- background: var(--accent)，padding: 18px 36px，display: flex，gap 16px
- 左标签（DM Mono 10px，uppercase，color: var(--bg)，opacity 0.6）
- 右逻辑文字（Noto Sans SC 700，13px，color: var(--bg)）—— A × B → C → D 公式形式

### 4. Two Column 主内容双栏

- display: grid，grid-template-columns: 1fr 1fr，border-bottom: 1px solid var(--border)
- 左栏 border-right: 1px solid var(--border)
- 左栏放步骤流程，右栏放模式矩阵/选项卡

### 5. Step Block 步骤块（左栏内）

- padding: 32px 28px，border-bottom: 1px solid var(--border)（最后无）
- 步骤编号行（Bebas Neue 13px，letter-spacing 0.25em，color: var(--accent)；::after 伪元素 flex:1 height:1px background: var(--border)）
- 步骤标题（Noto Sans SC 700，17px，color: var(--ink)，margin-bottom 14px）
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.95；重点 strong 标签 color: var(--ink) weight 500）
- 标签行（DM Mono 10px，padding: 4px 10px，border: 1px solid，border-radius 2px）：默认 var(--border-lt)/var(--ink-dim)；accent/red/green/blue-lt 各有对应色

### 6. Mode Block 模式卡（右栏内）

- padding: 28px，border-bottom: 1px solid var(--border)（最后无）
- 模式标题（Noto Sans SC 700，14px，color: var(--ink)）+ 徽章（DM Mono 10px，3色方案：green/blue-lt/accent）
- 描述（Noto Sans SC 300，12px，color: var(--ink-dim)，line-height 1.9）
- 关键数字（Bebas Neue 28px，颜色随徽章色）

### 7. Pull Quote 引言宽条

- padding: 40px 36px，background: var(--surface)，border-bottom: 1px solid var(--border)
- 左大引号（Bebas Neue 80px，color: var(--accent)，opacity 0.4）
- 引文（Noto Sans SC 700，font-size: clamp(14px, 2.5vw, 18px)，color: var(--ink)；关键词 em color: var(--accent)）

### 8. Case Study 案例区

- display: grid，grid-template-columns: 3fr 2fr
- 左栏（padding: 36px 28px）：案例标题 + 描述 + 步骤列表（带圆点编号 background: var(--accent)）
- 右栏（background: var(--surface)）：KPI 卡片（background: var(--card)，数值 Bebas Neue 32px color: var(--accent)）

### 9. Avoid Grid 避坑三栏

有避坑/注意事项时使用。

- display: grid，grid-template-columns: 1fr 1fr 1fr
- 背景大数字（Bebas Neue 48px，color: var(--red)，opacity 0.3）+ 错误标题（color: var(--red)）+ 说明正文

### 10. Secret Row 秘笈双栏

有隐藏技巧时使用。

- display: grid，grid-template-columns: 1fr 1fr
- 编号格式：// SECRET 0X（DM Mono 10px，color: var(--accent)）

### 11. Footer 底栏

- background: var(--surface)，padding: 24px 36px，display: flex，justify-content: space-between
- 左：元数据（DM Mono 10px，color: var(--ink-mute)）
- 右：品牌名（Bebas Neue 22px，color: var(--border-lt)）
