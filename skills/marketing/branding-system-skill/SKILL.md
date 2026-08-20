---
name: branding-system-skill
description: Use when designing or generating any brand identity, website, poster, UI, motion piece, or visual asset for any project. Always activated before any visual output is produced. Reads the brief, moodboard, and brand preferences to develop a coherent visual system first — covering line language, shape grammar, pattern logic, typography, color, spatial rules, and motion. Prevents generic AI aesthetics and enforces studio-level quality.
install_source: official
install_method: download
skill_id: official_OSzTLhbw
enabled_at: 1787232959946
version: 1.0.0
name_zh: 品牌系统
---


# Branding System Skill 

## Core Philosophy

You are not making something that looks good.
You are constructing a visual language — a system so coherent that someone 
could recognize the brand without seeing the logo. Every output is an 
expression of that system. Surfaces are just proofs.

The standard is: hex.inc, Pentagram, Sagmeister & Walsh.
Not inspiration — the actual bar.

---

## Step 0 — Read Before You Build

Before anything, extract the following from the brief, moodboard, or 
preferences provided:

- What does this brand do, and who is it for?
- What is the emotional register? (austere, playful, technical, human, raw, refined)
- What are the visual references? Study them — what system logic underlies them?
- What surfaces will this live on? (web, print, motion, environmental, all of the above)
- Is there an existing system to extend, or are we starting from zero?
- What should this brand never feel like?

If the brief is incomplete or ambiguous on any of these, ask one focused 
question before proceeding. Never assume. Never fill gaps with generic defaults.

---

## Step 1 — Derive the System from the Brief

The system is not chosen — it is derived. Every decision below must trace 
back to something in the brief. If you cannot justify a choice with the 
brief, it is the wrong choice.

### Line Language
Determined by brand personality and visual references.

Ask: Is this brand precise and constructed, or gestural and alive? Is there 
tension between those two qualities?

- Geometric / architectural: rigid, technical, grid-anchored, blueprint energy
- Organic / gestural: flowing, hand-drawn tension, loose but intentional
- Hybrid: structured skeleton with organic surface — define where each lives

Define:
- Primary stroke weight and whether it varies across hierarchy
- Corner treatment: sharp, rounded, chamfered — and when each applies
- Line behavior: do they connect, interrupt, trail, loop, react?
- What lines are NOT allowed in this system

### Shape Grammar
Build from 2–3 atomic shapes derived from the brand concept.

- What is the origin of the shape? (logotype geometry, industry reference, 
  abstract concept made visual)
- What transformations are allowed? Define rotation, scale, mirror, fragment rules
- How do shapes combine — union, subtraction, overlap with transparency?
- Does the shape system have a modular grid? Define the snap logic.
- Stress test: can this shape work at 16px and at full bleed?

### Pattern Logic
All patterns are generated from the atomic shapes. No stock textures.

- Define the repeat unit and its construction from atomic shapes
- Define spacing rhythm and density range (sparse ↔ dense)
- Two states minimum: resting and activated (scroll, hover, time-based)
- Micro application: texture, background noise, surface grain
- Macro application: hero sections, print backgrounds, environmental graphics
- Define what makes the pattern feel alive vs static

### Typography System
Type is structure, not decoration. Define it like architecture.

Primary typeface — role: display, brand mark, major headlines
Secondary typeface — role: body, UI, supporting text
Tertiary (if needed) — role: code, data, captions

Type ramp — minimum 6 named sizes:
  display / h1 / h2 / h3 / body-lg / body / caption / label

For each size define:
- font-size, line-height, letter-spacing, font-weight
- When to use uppercase, when not to
- Maximum line length (characters)

Rules:
- Hierarchy must hold in single color — size, weight, and spacing carry it
- No default browser sizing
- Type must work at mobile breakpoints without redesigning

### Color System
Color carries meaning. Define the meaning before defining the colors.

Primary palette — 1 to 2 colors. What does each communicate?
Neutral scale — minimum 6 stops: near-black → mid → near-white
Accent — 1 color, interaction and emphasis only, used sparingly
Semantic — success, warning, error if the project needs them

For every color define:
- OKLCH values (primary format) — HEX as fallback for tooling that doesn't support it yet
- What surfaces it appears on
- What sits on top of it (text, icons, overlays)
- Dark mode equivalent — both modes are required, not optional

OKLCH is the default color format for this system.
- Defines colors in perceptual lightness, chroma, and hue
- Gradients interpolated in OKLCH avoid the muddy mid-point problem
- Color scales (neutrals, tints) are built by stepping lightness and chroma 
  along the same hue — not by mixing with black or white
- Use @supports (color: oklch(0 0 0)) with HEX fallback where needed

Gradient rules:
- Only use if the gradient is derived from system logic
- Define angle, stops, opacity behavior
- Never use gradients to compensate for weak color decisions

### Spatial Grammar
One base unit governs everything. Usually 4px or 8px.

Define:
- Base unit value
- Spacing scale with named tokens: 2xs / xs / sm / md / lg / xl / 2xl / 3xl
- Grid: columns, gutter, margin at mobile / tablet / desktop
- Container max-widths and content sitting rules
- Breathing room principle: more space = higher hierarchy signal
- When to break the grid — and what that communicates

### Motion Grammar

Motion is determined by the brand's physical personality.
Ask: if this brand were a physical object, how would it move?
Heavy machinery moves differently from water. Define that quality first.

Personality axis — pick a position on each:
- Weight: heavy ←→ light
- Speed: slow ←→ fast
- Character: mechanical ←→ organic
- Entry behavior: emerge ←→ snap ←→ drift
- Exit behavior: dissolve ←→ cut ←→ retract

Technical decisions based on context:

CSS transitions / animations
→ Use for: UI state changes, micro-interactions, simple entrance animations
→ When: performance-critical, broad browser support required

Canvas API / SVG + JS
→ Use for: procedural patterns, reactive graphics, data-driven visuals, 
   particle systems, line drawing animations
→ When: 2D generative work, interactive brand expressions, poster-level motion

WebGL / Shaders
→ Use for: immersive hero experiences, atmospheric depth, physics simulations,
   real-time generative texture
→ When: the brand warrants it, performance envelope allows it, web-first output
→ Ask before defaulting here — confirm the technical context

For each motion in the system define:
- Purpose: what does this motion communicate?
- Duration: micro (80–120ms) / standard (200–300ms) / expressive (400–600ms)
- Easing: define cubic-bezier values, not named presets
- Trigger: what initiates it? (load, scroll, hover, interaction, data change, time)
- Reduced motion fallback: required every time, no exceptions

Procedural motion — always consider:
- What in this brand could be alive? (reactive to cursor, scroll, data, sound)
- What patterns could breathe or evolve over time?
- What brand element has natural physics? (tension, gravity, magnetism, fluid)
- Define the rules of the generative behavior, not just the aesthetic

---

## Step 2 — Pressure Test Before Output

Before producing any final asset, test the system at these scales:

- Favicon / 16px icon — does the system survive compression?
- Business card / print format — does it hold at physical scale?
- Full-bleed poster — does it feel like a world, not a layout?
- Web hero section — full viewport, does it have atmosphere?
- Social card (1200×630) — system under constraint
- Motion expression — one animated proof the system is alive

If any surface breaks the system: fix the system, not the surface.
A system that only works on one surface is not a system.

---

## Step 3 — Output

**Web / UI**
- CSS custom properties for every token: color, spacing, type, radius, motion
- Motion via CSS transitions or Web Animations API for UI
- Procedural elements via Canvas or WebGL based on context
- All interactive states defined: default, hover, focus, active, disabled
- Mobile-first, always

**Posters / Print**
- Define bleed and safe zone before composing
- Typography must hold hierarchy without color
- At least one element demonstrates pattern or line language at scale
- Composition follows the spatial grammar — not intuition

**Brand Identity**
- Wordmark, symbol/mark, lockup rules
- Color usage guide
- Type specimen
- Pattern tile (resting and active states)
- Motion expression (minimum one)
- System in use across 3+ surfaces — not isolated components
- Brief extension note: how does this system behave on the next surface?

---

## Non-Negotiables

These are never acceptable regardless of brief:

- Generic sans-serif + gradient hero + card grid
- Neon on black with no system logic
- Decorative motion with no communicative purpose
- Color palette chosen before the meaning is defined
- Patterns or icons not derived from the system
- A single polished surface with no system behind it
- A system so complex it collapses in daily use
- Beautiful case study work that fails in the real world
- Filling brief gaps with defaults instead of asking

---

## When the Brief Is Incomplete

If the brief does not give you enough to make a real decision on any layer, 
ask one focused question. Make it specific — not "what's the vibe?" but 
"the references lean technical but the brand name feels warm — which 
quality leads?"

Never guess on the foundations. Guess on the details, refine from there.