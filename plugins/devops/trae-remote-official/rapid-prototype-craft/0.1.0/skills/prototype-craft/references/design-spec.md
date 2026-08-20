# design-spec · Design Spec & the "Design Contract"

Goal: turn "high fidelity, texture, style consistency" into executable constraints and keep AI-slop out. This file is both **the field list for writing the contract** and **the visual quality floor.**

## 1. Design Contract file (freeze before fan-out / writing code)

Write it to a temp working directory (e.g. `<tmp>/design-contract.md`) as the single source of truth for all pages. Template:

```md
# Design Contract
## Style Tier & Aesthetic Direction
style: tech-dark | minimal-light | pixel | business-international | brand-themed
aesthetic: <commit to one clear direction, e.g. editorial/magazine, extreme minimal,
           retro-futuristic, industrial-utilitarian, luxury-refined, geometric-decorative…
           — see "Section 4. Elevating Design Quality">
tone keywords: <e.g. calm / restrained / high information density>

## Design Tokens
color.primary:   #____      color.primary-hover: #____
color.bg:        #____      color.surface:       #____
color.border:    #____      color.text:          #____   color.text-sub: #____
color.success/warning/danger: #____ / #____ / #____
font.display: <a characterful font for headings/display>   font.body: <a refined body font stack>
font.mono: <monospace>
font.scale:  12 / 14 / 16 / 20 / 24 / 32 (px)
radius:      sm6 / md10 / lg16      shadow: sm / md / lg (give concrete values)
spacing.unit: 4px base (4/8/12/16/24/32/48)
layout: max-width / grid columns / sidebar width
icon.lib:  lucide (single icon library, no emoji as icons)
icon.size: 16 / 20 / 24 (px)   icon.stroke: 1.5~2   icon.color: follows currentColor
motion: page-load choreography (staggered reveal) + key hover/transition (duration/easing)
bg-texture: background atmosphere (one of gradient mesh / noise / texture / layered transparency / dramatic shadow; avoid flat solid fill)

## Component Spec
button / input / card / table / modal / nav-sidebar / tag / empty-state
(for each: default state + hover + active + disabled + sizes)

## App Shell + Canonical Nav (mandatory for multi-page — prevents nav drift)
shell skeleton: <the exact outer HTML: wrapper + nav/sidebar/top-bar block + single main-content slot>
nav items:      <ordered list: label | lucide icon | href | data-nav key>  (frozen; pages must not add/remove/reorder)
nav positioning: <e.g. sidebar fixed, width var(--sidebar-w); content margin-left var(--sidebar-w) — identical on every page>
active rule:    <the ONE mechanism, e.g. .active on <a data-nav> matching body[data-page]>
mount:          <inline shell per page (default) | JS-injected via components.js (must mount early + idempotent on every page)>
(see multipage-system.md §1.5 — every page pastes this shell verbatim, only the main-content slot varies)

## Page List
- page name | responsibility | key components | navigates to which pages

## Mock Schema
(see interaction-mock.md, entity fields + sample data)
```

Once frozen, sub-agents may only reference these values and must not invent colors/type sizes/radii.

## 2. Quick Style-Tier Selection

| Tier | Trigger words | Key approach |
|---|---|---|
| tech-dark | tech / black premium / geeky / AI product | Dark base + a single high-saturation accent + localized monospace + glow/gradient edges |
| minimal-light | simple / clean / premium / understated | Lots of whitespace + neutral grays + one restrained accent + thin borders + soft shadows |
| business-international | admin / international tone / grand / SaaS | Steady primary + clear hierarchy + high data density + tidy grid |
| pixel/retro | pixel style / retro / game | Pixel font + hard edges + limited palette + no radius/no gradient |
| brand-themed | given a palette/image/brand color | Extract 3-5 colors into tokens; don't copy verbatim, systematize it |

## 3. Elevating Design Quality (borrowed from frontend-design, so the prototype "looks designed")

Anti-slop is the floor; this section is the ceiling — give the prototype a clear aesthetic personality that is memorable. When writing the contract, fill `aesthetic` / `font.display` / `motion` / `bg-texture` accordingly.

- **Commit to an aesthetic direction before coding**: from the query context commit to a bold flavor (editorial/magazine, extreme minimal, retro-futuristic, industrial-utilitarian, luxury-refined, geometric-decorative, soft pastel, raw brutalist…) and carry it throughout. **The key is "intentionality" not "intensity"** — minimal and maximal both work; what fails is the opinion-less generic default.
- **Characterful, paired fonts**: **avoid Inter/Roboto/Arial/system defaults** and other "AI-flavored" choices; pair a distinctive **display font** with a refined **body font**. For Chinese, pick characterful weights and size contrast within available fonts; don't run everything at one size. Don't converge on the same font every project.
- **Color with hierarchy, not evenly spread**: a dominant color + a few sharp accents beats a timid, evenly-distributed palette. **Especially avoid "purple gradient on white," the most typical AI cliché.** Unify via CSS variables.
- **Motion focused on high-impact moments**: one well-choreographed **page-load staggered reveal** (offset via `animation-delay`) delights more than scattered micro-interactions; add restrained hover / transition / scroll triggers. Prefer CSS-only motion for HTML.
- **Spatial composition dares to break convention**: asymmetry, overlap, diagonal flow, grid-breaking accent elements; use generous whitespace **or** controlled density — both with intent.
- **Backgrounds and details create atmosphere**: don't default to flat solid fills; per the aesthetic direction add gradient mesh, noise texture, geometric patterns, layered transparency, dramatic shadows, decorative borders, grain overlays, etc., for depth and texture.
- **Match complexity to the vision**: maximalist directions warrant rich motion and effect code; minimal/refined directions win via restraint and precise spacing/typography. Elegance comes from executing the vision well.
- **Diversity requirement**: vary light/dark themes, fonts, and aesthetics across generations — **don't converge on the same "safe" set every time.**
- **Fonts**: plain HTML+CSS covers most effects; for **static** offline delivery, **default to system-available fonts or self-hosted woff2** (dropped into `assets/` and referenced via relative `@font-face`) so the artifact stays offline-openable. **CDN fonts are only permitted when the user has explicitly given up the offline requirement** — never default to them when offline is still required. For **build-type** projects, install fonts via npm (e.g. `@fontsource/*`) or self-host in `assets/` and let the bundler process them.

## 4. Anti-AI-Slop Checklist (mandatory)

- **Forbidden**: uniform default font + pure-black #000 text + all-equal sizes; use paired display+body fonts, neutral dark-gray body text (e.g. #1f2933), and clear size hierarchy.
- **No "purple gradient on white"** or similar AI cliché palettes; dominant color + sharp accents, not evenly spread.
- **Forbidden**: identical heavy shadows on every card; keep shadows restrained and layered.
- **≤ 3 primary color families**, use scales rather than adding random colors; gradients restrained and directional.
- **Systematic spacing** (multiples of the 4px base), no ad-hoc 13px/17px.
- **States present**: hover / active / focus / disabled / empty / loading, at least covering interactive elements and list empty states.
- **Icons unified via Lucide** (see "Icon Spec" below); **strictly no emoji as icons**, and no mixing icon styles/languages.
- **Alignment and grid**: elements align to the grid, avoid pixel-level misalignment.
- **Realistic copy and data**: mock uses business-appropriate text, no "lorem ipsum" / "sample text 1".

## 5. Icon Spec (unified Lucide, no emoji)

- **Single icon library: Lucide** (https://lucide.dev). All icons across the project use this one library only; do not mix in other icon libraries or style-inconsistent hand-drawn icons.
- **Strictly no emoji as icons**: no emoji (e.g. ✅🔔📁🚀) at any UI icon slot — navigation, buttons, status, tags, empty states; emoji may appear only when clearly "content/expression" semantics and the user asks for it.
- **Integration approach** (pick one by scenario):
  - Static prototypes **must use inline SVG by default**: copy the corresponding Lucide icon SVG and embed it directly — zero external dependency, opens offline. This is the mandatory default because the delivery hard-requirement for pure-static is "zero external dependency, openable offline" (see `acceptance.md` §2).
  - **CDN is only permitted when the user has explicitly given up the offline requirement** (e.g. "will only run online / will host it anyway"). Only then may a many-icon static project use `<script src="https://unpkg.com/lucide@latest"></script>` + `<i data-lucide="name"></i>` + `lucide.createIcons()`. Never silently choose CDN by default — if offline is still required, inline SVG (or self-hosted assets) is the only option.
  - **Build-type projects** use the icon **npm package** for the chosen stack (e.g. `lucide-react` / `lucide-vue-next`), imported as components and tree-shaken by the bundler — this is the build-type equivalent, no inline-SVG/CDN needed.
- **Unified styling**: size from `icon.size` (16/20/24), `stroke-width` 1.5~2, color `currentColor` following text color, auto-adapting to theme.
- **Semantic accuracy**: choose names by meaning (search=search, settings=settings, delete=trash-2, success=check-circle, warning=alert-triangle…); don't pick for looks.
- **Register in the contract**: list the prototype's frequent icon Lucide names in the design contract so all pages/sub-agents draw from the same set, avoiding different icons for the same meaning across pages.

## 6. Imagery & Assets

- For **bitmap assets** like illustrations/photos/textures, use the base image-generation capability, save to the delivery directory's `assets/`, and reference via relative paths.
- Simple graphics (geometry, gradients, decorative blocks) are written directly in CSS/SVG, not generated as images; **icons always follow the Lucide spec above.**
- For Chinese charts/visualizations needing fonts, explicitly specify `Noto Sans CJK SC`, `WenQuanYi Micro Hei`.

## 7. Responsiveness & Adaptation

- Mobile-first scenarios: viewport meta + `env(safe-area-inset-*)` to adapt to notched screens.
- Desktop/admin: given max-width and grid, layout doesn't collapse on window resize.
- Cover at least mobile (≤480) / tablet (768) / desktop (≥1024) breakpoints.
