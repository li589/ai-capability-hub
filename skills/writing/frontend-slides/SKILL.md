---
name: frontend-slides
description: Create stunning, animation-rich slide presentations. Supports both React+Tailwind and zero-dependency HTML paths. AI auto-selects the best theme based on content. 触发词：幻灯片, 演示文稿, 演示, slide, slides, presentation, PPT, PPTX, pitch deck, 网页幻灯片, 做PPT, 制作PPT, 转换PPT, 导入PPT, web slide, 全屏展示, 主题演讲
available-agents:
  - DesignLite
install_source: official
install_method: download
skill_id: official_vjfY86uO
enabled_at: 1787232878933
version: 1.0.0
name_zh: 前端幻灯片
---

{% raw %}
# Frontend Slides

Create beautiful, animation-rich slide presentations. AI automatically selects the best theme based on content; users can override anytime.

**Supports two tech paths:**
- **React Path** — React + Tailwind CSS 4 + Framer Motion, multi-file components
- **HTML Path** — Zero-dependency single HTML file, inline CSS/JS

---

## ⚠️ REQUIRED: Two-Step Style Reference

**Before generating any presentation, follow these two steps in order:**

**Step 1 — Read the shared presets (always):**
```
shared/STYLE_PRESETS.md
```
Contains: 12 curated presets, viewport fitting requirements, theme selection guide, font quick reference, animation feelings mapping, design aesthetics.

**Step 2 — Read tech-specific references (based on chosen path):**

| Path | Read |
|------|------|
| React | `react/themes/{theme-name}.md` + `react/animation-presets.md` |
| HTML | `html/html-template.md` + `html/viewport-base.css` + `html/animation-patterns.md` |

**⛔ Hard block:** Do NOT generate any code without completing both steps.

---

## Core Philosophy

1. **Distinctive Design** — Avoid generic "AI slop" aesthetics. Every presentation should feel custom-crafted.
2. **AI-Driven Selection** — Automatically select the best theme based on content. Users can override anytime.
3. **Viewport Fitting (NON-NEGOTIABLE)** — Every slide MUST fit exactly within 100dvh. No scrolling within slides, ever.
4. **Production Quality** — Well-commented, accessible, and performant code.
5. **Zero-Ask Workflow** — Infer from what the user provides, never block on missing information.

---

## Tech Stack Routing

Determine the implementation path at the start. **Do NOT ask the user — detect automatically.**

| Signal | → Path |
|--------|--------|
| OpenClaw context / DesignLite agent | **HTML** |
| README specifies HTML / zero dependencies | **HTML** |
| User says "single HTML file" / "no npm" / "零依赖" | **HTML** |
| Vite + React project / README specifies React | **React** |
| PPT conversion (Mode B) | **React** |
| No clear signal | **React** (default) |

### React Path Tech Stack

| Technology | Usage |
|------------|-------|
| Tailwind CSS 4 | Styling with CSS variables |
| Framer Motion | Animations |
| Lucide React | Icons |
| Shiki | Code syntax highlighting |

### HTML Path Tech Stack

| Constraint | Detail |
|------------|--------|
| Zero dependencies | No npm, no build tools |
| Single file | All CSS/JS inline in one .html |
| Fonts | Fontshare or Google Fonts only (never system fonts) |
| Animations | Pure CSS + vanilla JS |

---

## Viewport Fitting (CRITICAL)

Each slide = exactly one viewport height (`100dvh`). Content overflows → split into multiple slides. **Never scroll within a slide.**

Shared rules for BOTH paths:
- All font sizes and spacing MUST use `clamp(min, preferred, max)` — never fixed px/rem
- Content containers need `max-height` constraints
- Images: `max-height: min(50vh, 400px)`
- Include `prefers-reduced-motion` support

Content density limits — see `shared/STYLE_PRESETS.md`.

### React-specific viewport rules
```tsx
<section className="w-screen h-dvh overflow-hidden snap-start flex flex-col relative p-[clamp(1rem,4vw,4rem)]">
```

### HTML-specific viewport rules
When generating HTML, read [html/viewport-base.css](html/viewport-base.css) and include its FULL contents in the `<style>` block.

---

## Phase 0: Detect Mode

| Mode | Trigger | Next Step |
|------|---------|-----------|
| **Mode A: New** | Create slides from scratch | Phase 1 below |
| **Mode B: PPT Conversion** | User has .ppt/.pptx to convert (React only) | ⬇️ Mode B Fast Path |
| **Mode C: Enhancement** | Improve existing presentation | Read file, then enhance |

| Mode | Interaction Strategy |
|------|----------|
| **Mode A** | No questions. Infer from input, make assumptions, proceed directly. |
| **Mode B** | Present extracted content for user confirmation before styling. |
| **Mode C** | Confirm intended changes only if scope is ambiguous. |

---

## ⚡ Mode B Fast Path: PPT Conversion (React Only)

Read `react/ppt-conversion.md` for the full extraction script and step-by-step workflow. After extraction and theme selection → go to Phase 4: Delivery.

---

## Phase 1: Content Analysis (Mode A / C only)

**Do not ask questions — infer from what the user provides.**

### Extract Information

| Information | How to Infer |
|-------------|--------------|
| **Purpose** | Keywords like "pitch", "teach", "present to team", "conference" |
| **Topic/Industry** | Subject matter: tech, finance, education, creative, etc. |
| **Audience** | Investors, developers, students, executives, general public |
| **Tone** | Formal vs casual, serious vs playful |
| **Content** | Bullet points, outlines, or raw text provided |

### Handle Missing Information

| User Provides | Action |
|---------------|--------|
| Full content | Proceed directly to theme selection |
| Topic only | Generate a reasonable slide outline (5-8 slides) |
| Vague request | Create a generic pitch deck structure, inform user they can refine |

---

## Phase 2: Theme Auto-Selection (AI-Driven)

**AI automatically selects the best theme. No user interaction required.**

### Selection Priority

1. **User Explicit Override** (highest) — e.g., "用 Neon Cyber 主题"
2. **Content Keywords** — see keyword matching table in `shared/STYLE_PRESETS.md`
3. **Audience Inference** — see audience mapping table in `shared/STYLE_PRESETS.md`
4. **Mood** — see mood mapping table in `shared/STYLE_PRESETS.md`
5. **Default Fallback** — Bold Signal

### Available Themes (12)

| Theme | Vibe | Best For |
|-------|------|----------|
| `bold-signal` | Confident, bold, high-impact | Pitch decks, keynotes |
| `electric-studio` | Bold, clean, professional | Corporate, agency pitches |
| `creative-voltage` | Energetic, retro-modern | Creative agencies, hackathons |
| `dark-botanical` | Elegant, warm luxury | Premium brands, lifestyle |
| `notebook-tabs` | Editorial, organized | Reports, documentation |
| `pastel-geometry` | Friendly, playful | Onboarding, consumer apps |
| `split-pastel` | Playful, creative | Community events, lifestyle |
| `vintage-editorial` | Witty, editorial | Book reviews, thought leadership |
| `neon-cyber` | Futuristic, techy | Tech startups, AI products |
| `terminal-green` | Hacker aesthetic | Dev tools, APIs, CLI |
| `swiss-modern` | Minimal, Bauhaus | Corporate, data-focused |
| `paper-ink` | Literary, timeless | Storytelling, thought leadership |

### Announce Selection

```
Based on your content about [topic], I'll use the **[Theme Name]** theme ([brief description]).
If you'd prefer a different style, let me know and I can regenerate.
```

---

## Phase 2.5: Navigation Style (React Only)

AI auto-selects navigation based on theme. See `react/navigation-styles.md` for all 6 styles and theme-navigation defaults. Users can override anytime.

---

## Phase 3: Generate Presentation

### React Path

Read `react/implementation-guide.md` for all code templates (components, hooks, theme CSS).

**Output Structure:**
```
client/src/pages/[PresentationName]/
├── slides/           # Slide01Title.tsx, Slide02Problem.tsx, ...
├── components/       # Slide.tsx, Reveal.tsx, Navigation.tsx
├── hooks/            # useSlideNavigation.ts, useKeyboardNav.ts
└── theme.css         # Theme CSS variables (from react/themes/{theme}.md)
```

**React Generation Checklist:**
- [ ] Read `shared/STYLE_PRESETS.md` (viewport rules + theme selection)
- [ ] Read `react/themes/{theme-name}.md` (CSS variables + Tailwind classes，设计详情在 shared/STYLE_PRESETS.md)
- [ ] Read `react/animation-presets.md` (Framer Motion variants)
- [ ] Use `h-dvh overflow-hidden` on every slide
- [ ] Use `clamp()` for all font sizes and spacing
- [ ] Respect content density limits per slide
- [ ] Apply correct navigation style (see `react/navigation-styles.md`)

### HTML Path

Read the following supporting files before generating:
- [html/html-template.md](html/html-template.md) — HTML architecture and JS features
- [html/viewport-base.css](html/viewport-base.css) — Mandatory CSS (include in full)
- [html/animation-patterns.md](html/animation-patterns.md) — Animation reference for the chosen feeling

**Output:** Single self-contained HTML file, all CSS/JS inline.

**HTML Generation Checklist:**
- [ ] Read `shared/STYLE_PRESETS.md` (viewport rules + theme selection)
- [ ] Read `html/html-template.md` (HTML architecture)
- [ ] Include FULL contents of `html/viewport-base.css` in `<style>`
- [ ] Use fonts from Fontshare or Google Fonts — never system fonts
- [ ] Use `SlidePresentation` JS class architecture
- [ ] Every section has a clear `/* === SECTION NAME === */` comment
- [ ] **No Tailwind** — pure inline CSS only
- [ ] Each `.slide` has `height: 100dvh; overflow: hidden;`

#### Image Paths in OpenClaw

If user provided images via the OpenClaw `$STATIC$` system:
```html
<img src="$STATIC$/images/filename.png" alt="...">
```

---

## Phase 4: Delivery

### React Path
```
Your presentation is ready!

📁 Location: /client/src/pages/[PresentationName]/
🎨 Style: [Theme Name]
📊 Slides: [count]

Navigation:
- Arrow keys (← → ↑ ↓) or Space to navigate
- Scroll/swipe also works
- Click the navigation dots to jump to any slide

To customize:
- Colors: Edit theme.css variables
- Animations: Modify Reveal component delays
- Layout: Adjust Slide variant prop
```

### HTML Path
```
Your presentation is ready!

🎨 Style: [Theme Name]
📊 Slides: [count]

Navigation:
- Arrow keys (← → ↑ ↓) or Space to navigate
- Scroll/swipe also works
- Click the navigation dots to jump to any slide

To customize:
- Colors: Edit :root CSS variables
- Typography: Change the font link
- Animations: Modify .reveal class
```

---

## Troubleshooting

- **React issues**: See `react/troubleshooting.md`
- **HTML issues**: See troubleshooting table in `html/animation-patterns.md`

---

## Supporting Files

| File | Purpose | When to Read | Tech |
|------|---------|-------------|------|
| `shared/STYLE_PRESETS.md` | 12 presets, selection guide, design rules | Always (Step 1) | Both |
| `react/implementation-guide.md` | React components, hooks, templates | Phase 3 | React |
| `react/navigation-styles.md` | 6 nav styles, theme defaults | Phase 2.5 | React |
| `react/animation-presets.md` | Framer Motion variants, easing | Phase 3 | React |
| `react/ppt-conversion.md` | Python extraction, conversion flow | Mode B | React |
| `react/troubleshooting.md` | Common React issues | As needed | React |
| `react/themes/{name}.md` | React 实现：CSS vars + Tailwind classes（设计详情见 shared/） | Phase 3 | React |
| `html/html-template.md` | HTML architecture, JS features | Phase 3 | HTML |
| `html/viewport-base.css` | Mandatory responsive CSS | Phase 3 | HTML |
| `html/animation-patterns.md` | CSS/JS animation snippets | Phase 3 | HTML |

{% endraw %}
