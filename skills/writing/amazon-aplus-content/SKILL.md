---
name: amazon-aplus-content
description: "Amazon A+ content (Enhanced Brand Content) builder. Design module layouts, write conversion-optimized copy, create brand story sections, and plan comparison charts. Works for Standard A+ and Premium A+. Triggers: a+ content, amazon a+, enhanced brand content, ebc, amazon brand story, a+ modules, premium a+, a+ content builder, amazon brand content, a+ copy, brand story, a+ design, amazon ebc, product detail page, a+ comparison chart"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-aplus-content
install_source: official
install_method: download
skill_id: official_BUJCC6MY
enabled_at: 1787231048807
version: 1.0.0
name_zh: 亚马逊 A+ 内容构建器
---

# Amazon A+ Content Builder

Design high-converting A+ content modules, write compelling copy, and plan your brand story. Turn your product detail page into a sales machine.

## Commands

```
a+ plan [product]               # plan A+ module layout strategy
a+ copy [module type]           # write copy for specific module
a+ brand story                  # write brand story section
a+ compare [products]           # build comparison chart
a+ audit [paste existing]       # score and improve existing A+
a+ premium                      # Premium A+ module planning
a+ mobile                       # mobile-optimized A+ checklist
a+ save [product]               # save A+ content plan
```

## What Data to Provide

- **Product & brand** — what you sell, your brand positioning
- **Target customer** — who buys, their pain points and desires
- **Key differentiators** — what makes you better than competitors
- **Brand assets** — colors, fonts, visual style (describe or paste)
- **Competitor A+** — describe competitor pages to differentiate

## A+ Module Types Reference

### Standard A+ (Available to Brand Registry sellers)

| Module | Best Used For | Copy Length |
|--------|--------------|-------------|
| **Header Image with Text** | Hero brand statement | Headline 150 chars, body 300 chars |
| **Image & Text** | Feature highlights | 300 chars per block |
| **Image Sidebar** | Specifications + visual | 200 chars |
| **Technical Specs Table** | Product details | 20 rows max |
| **Four Image with Text** | Use cases / benefits | 200 chars each |
| **Logo + Description** | Brand intro | 600 chars |
| **Comparison Chart** | Product line showcase | Up to 6 ASINs |
| **Single Image** | Lifestyle/usage shot | No text required |

### Premium A+ (For qualifying brands with Brand Story)

Additional modules:
- **Interactive Image Hotspot** — clickable image zones
- **Q&A Module** — FAQ format with expandable answers
- **Video Module** — embed product/brand video
- **Carousel** — swipeable multi-image module

## A+ Content Strategy by Goal

### Goal: Reduce Returns
Focus on: Technical specs table, size/fit guide, what's-in-the-box module
Copy angle: Set accurate expectations, answer "will this fit/work for me?"

### Goal: Increase Conversion Rate
Focus on: Hero image with power headline, 3–4 key benefits with lifestyle photos
Copy angle: Emotional benefit + proof point in every module

### Goal: Build Brand Loyalty
Focus on: Brand story, founder narrative, sustainability/mission
Copy angle: Why we exist, what we stand for, our promise

### Goal: Upsell Product Line
Focus on: Comparison chart (position this product as mid-tier, show premium)
Copy angle: "Good / Better / Best" positioning

## Copy Framework by Module

### Hero Header Formula
```
[Transformation Statement] — [How You Achieve It]
Example: "Sleep Through the Night — Engineered for Side Sleepers"
```

### Feature Module Formula
```
[Benefit Headline — NOT feature]
[1-sentence explanation of how it works]
[Proof point or spec if available]

❌ Weak: "Memory Foam Material"
✅ Strong: "Wakes Up With You — Responds to body heat in 3 seconds for perfect pressure relief"
```

### Brand Story Framework (600 chars)
```
1. Origin (2 sentences): Why we started, what problem we saw
2. Mission (1 sentence): What we're trying to do for customers
3. Promise (1 sentence): What you can always expect from us
4. CTA: Invite them into the community/brand
```

## A+ Content Rules (Amazon Policy)

**Prohibited:**
- Pricing or promotional information ("$49.99", "Buy 2 get 1 free")
- References to customer reviews ("As seen in 5-star reviews")
- Time-sensitive claims ("Limited time offer")
- Competitor brand names
- Shipping information
- "Best seller" or "#1" claims without substantiation
- Blurry, low-resolution images (<72 DPI)

**Recommended image specs:**
- Minimum: 970px wide
- Ideal: 1500px wide (auto-scales for mobile)
- Aspect ratios vary by module — check Seller Central for exact specs

## Conversion Rate Benchmarks

| A+ Quality Level | Typical CVR Lift |
|-----------------|-----------------|
| No A+ content | Baseline |
| Basic A+ (text-heavy) | +3–5% |
| Good A+ (balanced images + copy) | +8–12% |
| Premium A+ (interactive, video) | +15–20% |

## Mobile Optimization Checklist

- [ ] Text readable without zooming (min 16px equivalent)
- [ ] No critical info hidden in image (mobile crops differently)
- [ ] Headline visible above fold on mobile
- [ ] Comparison chart columns ≤4 (wider tables scroll poorly)
- [ ] Videos have captions (60% watch without sound)

## Output Format

1. **Module Layout Plan** — recommended sequence of 5–7 modules
2. **Copy for Each Module** — headline + body text, ready to paste
3. **Image Brief** — what each image should show (for designer/photographer)
4. **Brand Story Draft** — complete 600-char brand story
5. **Conversion Score** — 100-point audit with specific improvements

## Rules

1. Lead every module with a benefit, not a feature
2. Mobile-first: if it doesn't work on a 375px screen, redesign it
3. No module should repeat information from another
4. Every image needs a clear subject — no busy backgrounds
5. Brand story must feel human, not corporate
