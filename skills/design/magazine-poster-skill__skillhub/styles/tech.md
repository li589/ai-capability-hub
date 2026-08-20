# TECH 终端暗色 · 极客代码风

**适用**：技术分享、编程教程、开发者内容、架构说明、技术博客

---

## CSS 变量

```
--bg:         #0d1117
--surface:    #161b22
--card:       #1c2128
--border:     #30363d
--ink:        #e6edf3
--ink-dim:    #8b949e
--ink-mute:   #484f58
--accent:     #00ff41
--accent-dim: #238636
--blue:       #58a6ff
--orange:     #d29922
--red:        #f85149
--purple:     #bc8cff
```

body 外部背景：`#010409`
page-wrapper 背景：`var(--bg)`

## 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Noto+Sans+SC:wght@300;400;700;900&display=swap" rel="stylesheet">
```

## 字体使用规则

- 所有英文/代码/标签/编号：`JetBrains Mono`
- 中文标题：`Noto Sans SC` weight 900
- 中文正文：`Noto Sans SC` weight 300，line-height 1.9，font-size 13px
- 终端提示符：`JetBrains Mono` weight 700，color: var(--accent)，前缀 `$ ` 或 `> `

## 版式模块

### 1. Terminal Bar 终端顶栏

- background: var(--surface)，padding: 10px 36px，display: flex，align-items: center，gap: 8px
- border-bottom: 1px solid var(--border)
- 三个圆点（12px，border-radius 50%）：#ff5f57，#febc2e，#28c840
- 路径（JetBrains Mono 11px，color: var(--ink-dim)，margin-left 12px）格式：`~/topics/主题`

### 2. Hero 主视觉区

- padding: 48px 36px，border-bottom: 1px solid var(--border)
- 标签行（JetBrains Mono 10px，color: var(--accent)，letter-spacing 0.15em；前缀 `// `）
- 主标题（Noto Sans SC 900，clamp(34px, 7vw, 58px)，line-height 1.05，color: var(--ink)）
- 关键词高亮：color: var(--accent)，text-shadow: 0 0 20px rgba(0,255,65,0.3)
- 副标题（Noto Sans SC 300，13px，color: var(--ink-dim)，max-width 420px，margin-top 16px）
- 状态栏（margin-top 32px，display: flex，gap 24px）：色点（8px，border-radius 50%）+ 文字（JetBrains Mono 10px，color: var(--ink-dim)）

### 3. Code Block Section 代码块区

有代码/命令/伪代码时使用。

- background: var(--card)，border: 1px solid var(--border)，margin: 24px 36px，border-radius 6px
- 顶栏（padding: 10px 16px，border-bottom: 1px solid var(--border)）：文件名 + 语言标签
- 代码区（padding 20px，JetBrains Mono 12px，line-height 1.7；注释 var(--ink-mute)；关键字 var(--purple)；字符串 var(--accent)；数字 var(--orange)）

### 4. Two Column 内容双栏

- display: grid，grid-template-columns: 1fr 1fr，border-bottom: 1px solid var(--border)
- 左栏 border-right: 1px solid var(--border)

### 5. Concept Card 概念卡

- padding: 28px，border-bottom: 1px solid var(--border)
- 编号（JetBrains Mono 10px，color: var(--accent-dim)）格式：`[01]`
- 标题（Noto Sans SC 700，15px，color: var(--ink)，margin: 8px 0 12px）
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.9）
- 内联代码词（JetBrains Mono 11px，background: var(--surface)，padding: 2px 6px，border-radius 3px，color: var(--blue)）

### 6. Diagram Block 流程图区

有流程/架构关系时使用。

- padding: 36px，background: var(--surface)
- 用 flex + border + 箭头符号（→ ↓ ⟶）构建简易流程图
- 节点（background: var(--card)，border: 1px solid var(--border)，padding: 12px 18px，border-radius 4px，JetBrains Mono 11px）
- 箭头（color: var(--accent)，JetBrains Mono 16px）

### 7. Warning Block 警告区

有注意事项/常见错误时使用。

- margin: 0 36px 24px，padding: 20px 24px，border-left: 3px solid var(--red)，background: rgba(248,81,73,0.06)，border-radius: 0 6px 6px 0
- 标题（JetBrains Mono 11px，color: var(--red)，uppercase）前缀 `⚠ `
- 正文（Noto Sans SC 300，12.5px，color: var(--ink-dim)，line-height 1.8）

### 8. Key Takeaway 要点总结

- padding: 36px，background: var(--surface)
- 标签（JetBrains Mono 10px，color: var(--accent)，letter-spacing 0.2em）前缀 `$ `
- 每项（前缀 `>` JetBrains Mono 14px color: var(--accent)）+ 文字（Noto Sans SC 400，13px，color: var(--ink)）

### 9. Footer 底栏

- background: var(--surface)，padding: 16px 36px，display: flex，justify-content: space-between，border-top: 1px solid var(--border)
- 左（JetBrains Mono 10px，color: var(--ink-mute)）格式：`$ echo "主题" | published YYYY-MM-DD`
- 右（JetBrains Mono 10px，color: var(--ink-mute)）：`EOF`
