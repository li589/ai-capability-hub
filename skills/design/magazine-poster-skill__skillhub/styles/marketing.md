# MARKETING 活力渐变 · 营销海报风

**适用**：营销推广、活动宣传、促销信息、品牌发布、新品上市

---

## CSS 变量

```
--bg:          #ffffff
--surface:     #f8fafc
--card:        #ffffff
--border:      #e2e8f0
--ink:         #0f172a
--ink-dim:     #64748b
--ink-mute:    #94a3b8
--accent:      #2563eb
--accent-hot:  #ea580c
--accent-glow: #3b82f6
--gradient-1:  #2563eb
--gradient-2:  #7c3aed
--gradient-3:  #ec4899
--cta-bg:      #ea580c
--cta-text:    #ffffff
--tag-bg:      rgba(37,99,235,0.08)
--tag-text:    #2563eb
```

body 外部背景：`#f1f5f9`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

## 字体使用规则

- 英文大标题/数字：`Plus Jakarta Sans` weight 800，letter-spacing -0.03em
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.8，font-size 13.5px
- 标签/CTA：`Plus Jakarta Sans` weight 600，font-size 11px，letter-spacing 0.1em，uppercase

## 版式模块

### 1. Top Bar 品牌条

- background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2))，padding: 14px 36px
- display: flex，justify-content: space-between
- 品牌名（Plus Jakarta Sans 700，14px，color: #fff，letter-spacing 0.15em）
- 右侧分类（Plus Jakarta Sans 500，11px，color: rgba(255,255,255,0.7)）

### 2. Hero 主视觉区

- padding: 60px 40px 48px，background: var(--bg)
- 标签丸（background: var(--tag-bg)，color: var(--tag-text)，Plus Jakarta Sans 600，10px，padding: 6px 14px，border-radius: 100px，uppercase）
- 主标题（Noto Sans SC 900，font-size: clamp(38px, 8vw, 68px)，line-height 1.0，color: var(--ink)）
- 关键词渐变：background: linear-gradient(135deg, var(--gradient-1), var(--gradient-3)) + -webkit-background-clip: text + color: transparent
- 副标题（Noto Sans SC 300，15px，color: var(--ink-dim)，line-height 1.7，max-width 480px，margin-top 20px）
- CTA 按钮（background: var(--cta-bg)，color: var(--cta-text)，Plus Jakarta Sans 700，13px，padding: 14px 32px，border-radius 8px，box-shadow: 0 4px 14px rgba(234,88,12,0.3)，margin-top 28px）

### 3. Stats Row 数据指标行

- display: grid，grid-template-columns: repeat(3, 1fr)，border-top/bottom: 1px solid var(--border)
- 每格 padding: 28px 24px，text-align: center
- 数字（Plus Jakarta Sans 800，clamp(28px, 5vw, 44px)，渐变文字同 Hero 关键词）
- 标签（Noto Sans SC 400，12px，color: var(--ink-dim)，margin-top 6px）

### 4. Feature Cards 特性卡片

- padding: 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 20px，background: var(--surface)
- 卡片（background: var(--card)，border: 1px solid var(--border)，border-radius: 12px，padding: 28px）
- 图标区（48px，border-radius 10px，background: var(--tag-bg)）—— 用 Unicode 符号（◆ ▲ ● ★）
- 标题（Noto Sans SC 700，15px，color: var(--ink)）
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.8）

### 5. Highlight Band 高亮引言条

- background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2))，padding: 36px 40px
- 引文（Noto Sans SC 700，clamp(15px, 3vw, 20px)，color: #fff，text-align center）
- 来源（Plus Jakarta Sans 500，11px，color: rgba(255,255,255,0.6)，margin-top 12px，text-align center）

### 6. Benefits List 利益点列表

- padding: 40px，display: grid，grid-template-columns: 1fr 1fr，gap: 24px
- 每项：圆标（28px，border-radius 50%，background: var(--tag-bg)，内含 ✓ 符号 color: var(--accent)）+ 标题（Noto Sans SC 500，13px）+ 说明（Noto Sans SC 300，12px，color: var(--ink-dim)）

### 7. CTA Section 行动号召区

- background: var(--ink)，padding: 48px 40px，text-align: center
- 标题（Noto Sans SC 900，clamp(22px, 5vw, 34px)，color: #fff）
- 副文（Noto Sans SC 300，14px，color: #94a3b8，margin-top 12px）
- CTA 按钮同 Hero

### 8. Footer 底栏

- padding: 20px 40px，border-top: 1px solid var(--border)，display: flex，justify-content: space-between
- 左（Noto Sans SC 300，11px，color: var(--ink-mute)）
- 右（Plus Jakarta Sans 500，11px，color: var(--ink-mute)）
