---
name: research-to-website
description: Build informative websites from research reports. Transforms research output (markdown or typst/pdf) into polished, domain-appropriate websites with professional design, data visualization, and scroll-based animations. Triggers on research-to-website tasks, report visualization, or when converting research into web presentations.
install_source: official
install_method: download
skill_id: official_2gCse01d
enabled_at: 1787232799036
version: 1.0.0
name_zh: 研究报告转网站
---

# Research to Website Builder

You are building a website from research output. This skill guides domain classification, design decisions, and implementation.

## Workflow

1. **Analyze Research** → Identify domains, key insights, data points
2. **Load Domain Guidelines** → Read relevant files from `domains/`
3. **Load Component Specs** → Read from `components/` (animations, typography, etc.)
4. **Create design-spec.md** → Merge guidelines into unified spec
5. **Build Website** → Implement based on design-spec.md
6. **Deploy** → Publish and provide live URL

## Domain Classification

Classify the research into 1-3 domains based on **content nature and presentation needs**, not keywords.

### Available Domains

| Domain | Use When Content Is... | Design Character |
|--------|------------------------|------------------|
| `business-financial` | Corporate reports, investor materials, market analysis, professional audiences | Professional, trustworthy, conservative |
| `academic-technical` | Scientific papers, technical docs, formal research with citations, methodology-focused | Clean, structured, evidence-based |
| `art-creative-storytelling` | Storytelling, art, culture, nature, emotion-driven, visual narratives, humanities | Immersive, animated, image-rich |
| `data-analytics` | Metrics-heavy, dashboards, quantitative analysis, charts as primary content | Interactive, chart-focused, insight-driven |
| `government-policy` | Public sector, regulations, citizen-facing, accessibility-critical | Formal, accessible, authoritative |

### How to Decide

Ask these questions about the content:

1. **What is the core purpose?**
   - Inform investors/professionals → `business-financial`
   - Present scientific findings → `academic-technical`
   - Tell a story, evoke emotion, explore culture → `art-creative-storytelling`
   - Show data trends and metrics → `data-analytics`
   - Communicate policy to citizens → `government-policy`

2. **How should the audience experience it?**
   - Read carefully, reference later → `academic-technical`
   - Scroll through a narrative journey → `art-creative-storytelling`
   - Explore data interactively → `data-analytics`
   - Scan for key decisions → `business-financial`

3. **What visual treatment does it need?**
   - Minimal, focused on text → `academic-technical`
   - Image-rich, atmospheric, animated → `art-creative-storytelling`
   - Chart-heavy, metrics prominent → `data-analytics`
   - Conservative, branded → `business-financial`

### Classification Output

Example:
```yaml
domains:
  primary: art-creative-storytelling   # Drives overall experience
  secondary: data-analytics     # Adds specific capabilities
  tertiary: null                # Optional
rationale: |
  Content explores Earth's landscapes and cultural myths - fundamentally
  storytelling about human connection to nature. Needs immersive visuals
  and narrative flow, not academic structure.
```

## Domain Composition Rules

When multiple domains apply, resolve conflicts:

| Aspect | Rule |
|--------|------|
| **Layout** | Most structured wins: Gov > Academic > Business > Data > Creative |
| **Color** | Primary domain base; secondary provides accents |
| **Typography** | Primary domain fonts; creative domains override display headings |
| **Animation** | Additive - layer from most dynamic: Creative > Marketing > Data > others |
| **Data Viz** | data-analytics rules always apply when data exists |

## Required Reference Files

Before creating design-spec.md, READ these files based on classified domains:

```
domains/{primary-domain}.md      # REQUIRED
domains/{secondary-domain}.md    # If secondary exists
components/animations.md         # If domain uses animations
components/typography.md         # REQUIRED for all
components/color-systems.md      # REQUIRED for all
components/visual-patterns.md    # REQUIRED for image-heavy domains
```

## Design Spec Template

Generate `design-spec.md` with this structure:

```markdown
# Design Specification

## Domain Classification
- Primary: {domain}
- Secondary: {domain or none}
- Rationale: {why these domains}

## Design Direction
- Style: {e.g., "Data-driven storytelling with investor-grade polish"}
- Mood: {e.g., "Confident, transparent, forward-looking"}

## Color System
- Background: {hex}
- Primary: {hex}
- Secondary: {hex}
- Accent: {hex}
- Data Palette: [{hex array for charts}]

## Typography
- Display: {font} - {usage}
- Heading: {font} - {usage}
- Body: {font} - {usage}
- Mono: {font} - {usage for data}

## Layout Structure
{Section-by-section breakdown}

## Animation Plan
{Scroll behaviors, transitions, micro-interactions}

## Visual Patterns
{Selected patterns from visual-patterns.md based on domain availability}
- Pattern 1: {name} - {where/how it will be used}
- Pattern 2: {name} - {where/how it will be used}

## Data Visualization Plan
{Charts, metrics, interactive elements}

## Image Requirements
{Hero images, diagrams, icons, plus specific images needed for visual patterns}
```

## Content Integrity Rules

The website must be a **complete, accurate presentation** of the research:

1. **Full Coverage**: Extract and present ALL key findings, conclusions, and data points. The website is not a teaser.
2. **Data Accuracy**: Numbers, statistics, and quotes must be preserved exactly. Never paraphrase data.
3. **Structure Mapping**: Every major heading in the report should have a corresponding section on the site.
4. **Insight Hierarchy**: Identify 3-5 most critical insights for prominent treatment (hero sections, pull quotes). Supporting details use scannable formats (cards, lists).

## Image Strategy (ALL DOMAINS)

**High-quality images are essential for premium websites in ALL domains**, not just creative. Use image proactively.

### Image Requirements by Purpose

| Purpose | When to Use | Examples |
|---------|-------------|----------|
| **Hero/Atmospheric** | Section openers, mood setting | Landscape for nature topic, office for business, lab for technical |
| **Explanatory** | Clarify concepts, visualize abstract ideas | infographics, process illustrations |
| **Supporting** | Break up text, add visual interest | Relevant photos between content sections |

### How to Source Images

Always prioritize finding real images through search. Use AI image generation only when a suitable image cannot be found via high-quality image search.

1. **Image Search Tool** (Primary Choice)

Use image search first for accuracy, realism, and credibility.
- Use image search first for accuracy, realism, and credibility.
- Source high-quality photography for real people, places, products, and events
- Find diagrams, charts, or infographics that explain concrete concepts
- Use official brand, company, or product images when applicable
- Prefer authentic, well-lit, high-resolution visuals
- Default rule: If a relevant, high-quality image exists, do not generate one.

2. **Image Generation Tool** (Fallback Only)

Use AI image generation only when image search does not yield a suitable result. Appropriate use cases include:
- Abstract or conceptual ideas that lack real-world imagery
- Custom atmospheric backgrounds tailored to a specific theme or mood
- Unique hero visuals when no existing image matches the required tone or composition
- Generation is a last resort, not a replacement for image search.

3. **Download Remote Images** (IMPORTANT)

Always download remote images to local storage before using them in the website:
- Remote URLs may become unavailable, break, or change over time
- Downloaded images ensure the website remains functional after deployment
- Store images in a local `/public/images/` or `/assets/` directory
- Use relative paths in the code (e.g., `/images/hero.jpg`) instead of remote URLs
- This applies to both searched images and any external image sources

### Image Placement Guidelines

- **Every major section** should have at least one visual element (image, chart, or diagram)
- **Text-heavy sections** need visual breaks every 2-3 paragraphs
- **Hero sections** require strong, full-bleed imagery
- **Transitions** between sections can use images to shift mood

## Asset Rules

1. **Icons**: Use professional React icon libraries (Lucide, Heroicons). **Never use emojis.** Avoid icon abuse—use icons sparingly for clarity, not decoration. Not every label needs an icon.
2. **Charts**: Use professional libraries (Recharts, Chart.js). Never use raw chart images.
3. **Images**: Actively source high-quality images. A website without images looks incomplete.
4. **Fallbacks**: Only if appropriate image truly cannot be found, use abstract shapes, gradients, or typographic treatments.

## Brand Color Rules

If the research is **about or related to** a specific organization/company (e.g., company analysis, stock report, product review, case study):

1. **Identify the subject**: Is a company/organization the main focus or key subject of the report?
2. **Research brand colors**: Search for their official brand guidelines, logo colors, or visual identity.
3. **Apply brand palette**: Use their primary brand color as your primary color. Derive secondary/accent colors that complement it.
4. **Maintain consistency**: The website should feel like it could belong to or represent that organization.

Examples:
- Stock analysis of Tesla → Use Tesla's red/black brand colors
- Case study on Spotify → Use Spotify's green brand color
- Government policy about NHS → Use NHS blue

## Anti-Patterns (AVOID)

- Generic AI aesthetics (purple gradients, dark mode defaults)
- Overused fonts (Inter, Roboto, system fonts)
- Cookie-cutter layouts (hero + cards + footer)
- Decorative-only images
- Animations without purpose
- Charts without context or insight callouts
- **Emojis anywhere in the UI**
- **Icon abuse** (icons on every label, decorative icons)
- Paraphrasing or approximating data/statistics
- Ignoring brand colors when research is about a specific company/organization

### Ugly Card/Box Patterns (NEVER USE)

- **Colored rounded icon containers**: Icons inside colored rounded squares (e.g., green box with chart icon)
- **Icon on every list item**: ✓ checkmarks or ✗ icons on every bullet point
- **Semantic color overload**: Green = good, red = bad applied to everything (cards, text, icons, backgrounds)
- **Pastel tinted card backgrounds**: Light green, light red, light blue card backgrounds
- **Generic comparison cards**: Two side-by-side cards with "pros vs cons" or "good vs bad" layout
- **Colored text labels**: Bright colored uppercase labels like "SUCCESS", "WARNING", "BUY", "SELL"

Instead:
- Use subtle borders or shadows for card definition
- Use whitespace and typography for hierarchy, not color
- Reserve semantic colors (green/red) for actual data changes only
- Keep backgrounds neutral (white, off-white, light gray)
- Use icons purposefully, not on every element

## Tech Stack

- **Framework**: Next.js (TypeScript)
- **Styling**: TailwindCSS + shadcn/ui
- **Animation**: GSAP, Framer Motion, Lenis (smooth scroll)
- **Charts**: Recharts, Chart.js, D3.js
- **Icons**: Lucide, Heroicons
