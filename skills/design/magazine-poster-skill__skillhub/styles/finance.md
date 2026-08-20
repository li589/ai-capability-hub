# FINANCE 信任深蓝 · 金融简报风

**适用**：理财知识、投资分析、商业洞察、经济趋势、创业复盘

---

## CSS 变量

```
--bg:          #f8fafc
--surface:     #ffffff
--card:        #ffffff
--border:      #e2e8f0
--ink:         #020617
--ink-dim:     #64748b
--ink-mute:    #94a3b8
--accent:      #0f172a
--accent-blue: #1e40af
--blue:        #2563eb
--blue-bg:     rgba(37,99,235,0.05)
--green:       #059669
--red:         #dc2626
--gold:        #a16207
```

body 外部背景：`#e2e8f0`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文标题/数据/标签：`Inter` weight 700-800
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.85，font-size 13.5px
- 数据展示：`Inter` weight 700，font-variant-numeric: tabular-nums

## 版式模块

### 1. Briefing Header 简报头

- background: var(--accent)，padding: 14px 36px，display: flex，justify-content: space-between
- 简报名（Inter 700，13px，color: #fff，letter-spacing 0.1em，uppercase）
- 日期（Inter 500，11px，color: #94a3b8）

### 2. Hero 主视觉区

- padding: 44px 36px 36px，background: var(--surface)，border-bottom: 1px solid var(--border)
- 标签行（Inter 600，10px，color: var(--blue)，uppercase；前置蓝色圆点 6px）
- 主标题（Noto Sans SC 900，clamp(28px, 6vw, 46px)，line-height 1.1，color: var(--ink)，margin-top 12px）
- 摘要（Noto Sans SC 300，14px，color: var(--ink-dim)，border-left: 3px solid var(--blue)，padding-left 16px，margin-top 14px，max-width 520px）

### 3. Metrics Dashboard 数据看板

- display: grid，grid-template-columns: repeat(4, 1fr)，border-bottom: 1px solid var(--border)
- 每格（padding: 24px 16px，text-align center，border-right: 1px solid var(--border)）：
  - 标签（Inter 500，9px，color: var(--ink-mute)，uppercase）
  - 数值（Inter 800，clamp(22px, 4vw, 32px)，color: var(--ink)）
  - 变化（Inter 600，11px）：正 color: var(--green) ↑ / 负 color: var(--red) ↓

### 4. Analysis Columns 分析双栏

- display: grid，grid-template-columns: 1fr 1fr，border-bottom: 1px solid var(--border)
- 左栏 border-right: 1px solid var(--border)，padding: 32px 28px

### 5. Insight Block 洞察块

- padding: 28px，border-bottom: 1px solid var(--border)
- 标签（Inter 600，10px，color: var(--blue)，uppercase）
- 标题（Noto Sans SC 700，15px，color: var(--ink)）
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.85）

### 6. Risk/Opportunity 机会与风险条

- display: grid，grid-template-columns: 1fr 1fr，border-bottom: 1px solid var(--border)
- 机会栏（标签 color: var(--green)）/ 风险栏（标签 color: var(--red)）

### 7. Key Takeaway 要点条

- background: var(--blue-bg)，padding: 28px 36px
- 标签（Inter 700，10px，color: var(--blue)，uppercase）
- 要点（Noto Sans SC 500，14px，color: var(--ink)，line-height 1.7）

### 8. Footer 底栏

- background: var(--accent)，padding: 20px 36px，display: flex，justify-content: space-between
- 左（Inter 400，10px，color: #64748b）
- 右（Inter 600，11px，color: #94a3b8）
