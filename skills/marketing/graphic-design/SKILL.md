---
name: graphic-design
description: "Graphic design skill: logo design (55 styles, 30 color palettes, 25 industry guides), corporate identity programs (50+ deliverables), icon design (15 styles, SVG), banner design (22 art direction styles, social/ads/web/print), HTML presentations (Chart.js, copywriting formulas), social photos (multi-platform). Trigger on: logo, logo design, corporate identity, CIP, banner, social media banner, presentation, slides, icon design, social photos, graphic design, visual assets."
user-invocable: true
disable-model-invocation: false
install_source: official
install_method: download
skill_id: official_SvN0U66B
enabled_at: 1787232953509
version: 1.0.0
name_zh: 图形设计
---

# Graphic Design

Unified graphic design skill covering logo design, corporate identity programs (CIP), icon design, banner design, slide presentations, and social photos. This skill provides design knowledge, workflows, rules, size specifications, and art direction guidance.

## When to Use

- Logo creation and brand mark design
- Corporate identity program (CIP) deliverables
- Icon design (SVG, multi-style)
- Banner design for social media, ads, web, print
- Presentations and pitch decks
- Social photos for Instagram, Facebook, LinkedIn, Twitter, Pinterest, TikTok

## Section Routing

| Task | Section | Key Reference |
|------|---------|---------------|
| Logo creation, brand marks | Logo Design | `references/logo-design.md` |
| CIP mockups, deliverables | Corporate Identity (CIP) | `references/cip-design.md` |
| SVG icons, icon sets | Icon Design | `references/icon-design.md` |
| Banners, covers, headers | Banner Design | `references/banner-sizes-and-styles.md` |
| Presentations, pitch decks | Slides/Presentations | `references/slides.md` |
| Social media images/photos | Social Photos | `references/social-photos-design.md` |

---

## Logo Design

55+ styles, 30 color palettes, 25 industry guides.

### Logo: Design Process

1. **Gather requirements** — brand name, industry, target audience, style preference, color direction
2. **Research** — study competitor logos, industry conventions, differentiation opportunities
3. **Select style** — choose from 55+ styles (see `references/logo-style-guide.md`)
4. **Select colors** — apply color psychology principles (see `references/logo-color-psychology.md`)
5. **Design** — create logo as SVG/HTML with chosen style and colors
6. **Generate output** with white background (ALWAYS white background for logos)
7. **Present options** — show multiple variants, iterate on feedback

### Logo: Style Categories

| Category | Examples |
|----------|----------|
| Wordmark | Custom typography-based logos |
| Lettermark | Monogram/initial-based |
| Pictorial | Icon or symbol-based |
| Abstract | Geometric abstract marks |
| Emblem | Badge/seal/crest style |
| Combination | Icon + wordmark together |
| Mascot | Character-based logos |

### Logo: Design Rules

- Always generate logos with **white background**
- Ensure logos work at small sizes (favicon) and large sizes (billboard)
- Test in both color and monochrome
- Provide variants: full color, single color, reversed (white on dark)
- Minimum clear space around logo mark

### Logo: References

| Topic | File |
|-------|------|
| Logo Design Guide | `references/logo-design.md` |
| Logo Styles (55+) | `references/logo-style-guide.md` |
| Color Psychology | `references/logo-color-psychology.md` |
| Prompt Engineering | `references/logo-prompt-engineering.md` |

---

## Corporate Identity (CIP)

50+ deliverables, 20 styles, 20 industries. A complete corporate identity program extends the logo into all brand touchpoints.

### CIP: Design Process

1. **Start with logo** — use Logo Design section above if no logo exists
2. **Define brand guidelines** — colors, typography, tone of voice
3. **Select deliverables** — choose from 50+ deliverable types (see `references/cip-deliverable-guide.md`)
4. **Select style** — match to brand personality (see `references/cip-style-guide.md`)
5. **Design deliverables** — create HTML/CSS mockups for each item
6. **Present** — compile into a presentation showing all deliverables

### CIP: Deliverable Categories

| Category | Examples |
|----------|----------|
| Stationery | Business card, letterhead, envelope |
| Marketing | Brochure, flyer, poster |
| Digital | Email signature, social media templates |
| Signage | Office signs, vehicle wrap, storefront |
| Packaging | Product packaging, labels, bags |
| Uniforms | Staff uniform, name badge |
| Environmental | Office interior, reception, wall graphics |

### CIP: Design Rules

- All deliverables must use the brand's color palette consistently
- Typography hierarchy: primary typeface for headlines, secondary for body
- Logo placement rules: minimum size, clear space, permitted backgrounds
- Maintain visual consistency across all touchpoints

### CIP: References

| Topic | File |
|-------|------|
| CIP Design Guide | `references/cip-design.md` |
| Deliverable Guide (50+) | `references/cip-deliverable-guide.md` |
| CIP Styles (20+) | `references/cip-style-guide.md` |
| CIP Prompt Engineering | `references/cip-prompt-engineering.md` |

---

## Icon Design

15 styles, 12 categories. SVG-based icon design.

### Icon: Design Process

1. **Define requirements** — purpose, platform, style, sizes needed
2. **Select style** — match to product and platform conventions
3. **Design** — create as clean SVG with proper viewBox and paths
4. **Export** — provide at multiple sizes if needed (16, 24, 32, 48px)

### Icon: Top Styles

| Style | Best For |
|-------|----------|
| outlined | UI interfaces, web apps |
| filled | Mobile apps, nav bars |
| duotone | Marketing, landing pages |
| rounded | Friendly apps, health |
| sharp | Tech, fintech, enterprise |
| flat | Material design, Google-style |
| gradient | Modern brands, SaaS |

### Icon: Design Rules

- Use consistent stroke width across an icon set
- Align to pixel grid for crisp rendering at small sizes
- Maintain optical balance (visual weight, not mathematical center)
- Use 24x24 as the base design grid, scale from there
- Keep SVG paths clean and optimized

### Icon: References

| Topic | File |
|-------|------|
| Icon Design Guide | `references/icon-design.md` |

---

## Banner Design

22 art direction styles across social media, advertising, web, and print formats.

### Banner: Design Process

1. **Gather requirements** — purpose, platform, content, brand, style, quantity
2. **Research** — browse references for design inspiration, select 2-3 art direction styles
3. **Design** — create HTML/CSS banner at exact platform dimensions
4. **Apply rules** — safe zones, typography limits, text ratio, CTA placement
5. **Export** — screenshot to PNG at exact dimensions
6. **Present** — show all options side-by-side, iterate on feedback

### Banner: Size Reference

| Platform | Type | Size (px) | Aspect Ratio |
|----------|------|-----------|--------------|
| Facebook | Cover | 820 x 312 | ~2.6:1 |
| Twitter/X | Header | 1500 x 500 | 3:1 |
| LinkedIn | Personal | 1584 x 396 | 4:1 |
| YouTube | Channel art | 2560 x 1440 | 16:9 |
| Instagram | Story | 1080 x 1920 | 9:16 |
| Instagram | Post | 1080 x 1080 | 1:1 |
| Google Ads | Med Rectangle | 300 x 250 | 6:5 |
| Google Ads | Leaderboard | 728 x 90 | 8:1 |
| Website | Hero | 1920 x 600-1080 | ~3:1 |

### Banner: Top Art Direction Styles

| Style | Best For | Key Elements |
|-------|----------|--------------|
| Minimalist | SaaS, tech | White space, 1-2 colors, clean type |
| Bold Typography | Announcements | Oversized type as hero element |
| Gradient | Modern brands | Mesh gradients, chromatic blends |
| Photo-Based | Lifestyle, e-com | Full-bleed photo + text overlay |
| Geometric | Tech, fintech | Shapes, grids, abstract patterns |
| Retro/Vintage | F&B, craft | Distressed textures, muted colors |
| Glassmorphism | SaaS, apps | Frosted glass, blur, glow borders |
| Neon/Cyberpunk | Gaming, events | Dark bg, glowing neon accents |
| Editorial | Media, luxury | Grid layouts, pull quotes |
| 3D/Sculptural | Product, tech | Rendered objects, depth, shadows |

Full 22 styles: `references/banner-sizes-and-styles.md`

### Banner: Design Rules

- **Safe zones**: critical content in central 70-80% of canvas
- **CTA**: one per banner, bottom-right, min 44px height, action verb
- **Typography**: max 2 fonts, min 16px body, >=32px headline
- **Text ratio**: under 20% for ads (Meta penalizes heavy text)
- **Print**: 300 DPI, CMYK, 3-5mm bleed
- **Contrast**: minimum 4.5:1 ratio for text readability

### Banner: Output Organization

```
assets/banners/{campaign}/
├── minimalist-1500x500.png
├── gradient-1500x500.png
├── bold-type-1500x500.png
├── minimalist-1080x1080.png
└── ...
```

- Use kebab-case for filenames: `{style}-{width}x{height}.{ext}`
- Date prefix for time-sensitive campaigns: `{YYMMDD}-{style}-{size}.png`
- Campaign folder groups all variants together

### Banner: References

| Topic | File |
|-------|------|
| Banner Sizes & Styles (22 styles) | `references/banner-sizes-and-styles.md` |

---

## Slides / Presentations

Strategic HTML presentations with Chart.js, design tokens, responsive layouts, and copywriting formulas.

### Slides: Design Process

Load `references/slides-create.md` for the full creation workflow.

1. **Define purpose** — pitch deck, keynote, training, report, proposal
2. **Select strategy** — match presentation type to slide strategies
3. **Structure content** — apply copywriting formulas for persuasive messaging
4. **Choose layout patterns** — pick from layout pattern library
5. **Build HTML slides** — use the HTML template system with Chart.js for data visualization
6. **Review** — check flow, pacing, visual consistency

### Slides: Key Principles

- One idea per slide
- Visual hierarchy: headline > supporting data > body text
- Data visualization with Chart.js for quantitative slides
- Copywriting formulas for persuasive messaging (AIDA, PAS, BAB, etc.)
- Consistent design tokens across all slides

### Slides: References

| Topic | File |
|-------|------|
| Slides Overview | `references/slides.md` |
| Creation Guide | `references/slides-create.md` |
| Layout Patterns | `references/slides-layout-patterns.md` |
| HTML Template | `references/slides-html-template.md` |
| Copywriting Formulas | `references/slides-copywriting-formulas.md` |
| Strategies | `references/slides-strategies.md` |

---

## Social Photos

Multi-platform social image design using HTML/CSS rendered to screenshots.

### Social Photos: Design Process

1. **Analyze** — parse requirements: subject, platforms, style, brand context, content elements
2. **Ideate** — develop 3-5 concepts
3. **Design** — create HTML/CSS per idea per platform size
4. **Export** — screenshot at exact pixel dimensions (2x deviceScaleFactor for retina)
5. **Verify** — visually inspect exported designs, fix layout/styling issues, re-export
6. **Report** — document design decisions

### Social Photos: Key Sizes

| Platform | Size (px) | Platform | Size (px) |
|----------|-----------|----------|-----------|
| IG Post | 1080x1080 | FB Post | 1200x630 |
| IG Story | 1080x1920 | X Post | 1200x675 |
| IG Carousel | 1080x1350 | LinkedIn | 1200x627 |
| YT Thumbnail | 1280x720 | Pinterest | 1000x1500 |

### Social Photos: References

| Topic | File |
|-------|------|
| Social Photos Guide | `references/social-photos-design.md` |

---

## Workflows

### Complete Brand Package

1. **Logo** — design logo variants using Logo Design section
2. **CIP** — create deliverable mockups using Corporate Identity section
3. **Presentation** — build pitch deck using Slides section
4. **Social** — create social media assets using Banner and Social Photos sections

### Campaign Asset Set

1. **Banners** — create platform-specific banners for the campaign
2. **Social Photos** — design content images for social platforms
3. **Presentation** — build campaign deck for stakeholders

---

## All References

| Topic | File |
|-------|------|
| Design Routing | `references/design-routing.md` |
| Logo Design Guide | `references/logo-design.md` |
| Logo Styles | `references/logo-style-guide.md` |
| Logo Colors | `references/logo-color-psychology.md` |
| Logo Prompts | `references/logo-prompt-engineering.md` |
| CIP Design Guide | `references/cip-design.md` |
| CIP Deliverables | `references/cip-deliverable-guide.md` |
| CIP Styles | `references/cip-style-guide.md` |
| CIP Prompts | `references/cip-prompt-engineering.md` |
| Slides Overview | `references/slides.md` |
| Slides Create | `references/slides-create.md` |
| Slides Layouts | `references/slides-layout-patterns.md` |
| Slides Template | `references/slides-html-template.md` |
| Slides Copy | `references/slides-copywriting-formulas.md` |
| Slides Strategy | `references/slides-strategies.md` |
| Banner Sizes & Styles | `references/banner-sizes-and-styles.md` |
| Social Photos Guide | `references/social-photos-design.md` |
| Icon Design Guide | `references/icon-design.md` |
