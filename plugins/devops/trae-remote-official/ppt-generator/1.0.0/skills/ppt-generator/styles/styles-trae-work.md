# Styles · TRAE-work

This file defines the **complete visual system** for the TRAE-work style—including precise CSS code blocks.
Use it together with `../layouts.md` (the pure structural framework).

> To switch styles, simply replace this file with another styles file; the framework structure in layouts stays unchanged.

---

## 1. CSS Variables

```css
:root {
  --bg: #ffffff;
  --bg-off: #e8e8ec;
  --bg-2: #f7f7f8;
  --surface: #f0f0f2;
  --line: #e8e8ec;
  --line-strong: #c0c0c0;
  --text: #1a1a1a;
  --text-2: #5c5c5c;
  --text-3: #8b8b8b;
  --accent: #4B3FE3;
  --accent-2: #3a2fb8;
  --accent-soft: rgba(75, 63, 227, .10);
  --accent-bright: #7B71FF;
  --sans: "Inter", "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", sans-serif;
  --mono: "JetBrains Mono", "SF Mono", "Cascadia Code", monospace;
  --pad-x: 77px;
  --pad-y: 69px;
}
```

---

## 2. Base Reset and Canvas

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; background: var(--bg-off); color: var(--text); font-family: var(--sans); -webkit-font-smoothing: antialiased; font-feature-settings: "ss01", "cv11"; }
body { overflow: hidden; }

/* ASCII backdrop layer — lives INSIDE the deck so it scales together with the
   1280×720 canvas. Fixed px, absolutely positioned, sits behind the slides. */
canvas.ascii-bg {
  position: absolute; inset: 0;
  width: 1280px; height: 720px;
  z-index: 0; pointer-events: none;
  opacity: .6;
}

.deck { position: fixed; width: 1280px; height: 720px; top: 50%; left: 50%; transform: translate(-50%,-50%); z-index: 1; flex-shrink: 0; overflow: hidden; background: var(--bg); box-shadow: 0 10px 60px rgba(0,0,0,.16), 0 2px 8px rgba(0,0,0,.08); }
.slide {
  position: absolute; inset: 0;
  z-index: 1;
  display: grid;
  padding: var(--pad-y) var(--pad-x);
  opacity: 0; visibility: hidden; pointer-events: none;
  transition: opacity .5s cubic-bezier(.2,.7,.2,1), visibility .5s;
}
.slide.active { opacity: 1; visibility: visible; pointer-events: auto; }
```

---

## 3. Chrome Components

```css
.chrome-top, .chrome-bottom {
  position: absolute; left: var(--pad-x); right: var(--pad-x);
  z-index: 20;
  display: flex; align-items: center; justify-content: space-between;
  font-family: var(--mono); font-size: 12px; letter-spacing: .18em;
  text-transform: uppercase; color: var(--text-3);
}
.chrome-top { top: 28px; }
.chrome-bottom { bottom: 28px; }
.mark { display: inline-flex; align-items: center; gap: 10px; color: var(--text-2); }
.mark .dot { width: 8px; height: 8px; background: var(--accent); border-radius: 999px; box-shadow: 0 0 0 4px var(--accent-soft); }

.page { display: inline-flex; align-items: center; gap: 14px; font-variant-numeric: tabular-nums; }
.page .num { color: var(--text); font-weight: 500; }
.page .sep { width: 24px; height: 1px; background: var(--line-strong); display: inline-block; }

/* The T08 close slide is a full-bleed split that carries its OWN top identifiers
   (.chrome-min) and bottom sign-off (.sig / .foot) in each column. When it is
   active, suppress the deck-level chrome bars so the top brand row and the bottom
   page-number row are not doubled. The nav dots stay (they are the pager). */
.deck:has(.s-close.active) .chrome-top,
.deck:has(.s-close.active) .chrome-bottom { opacity: 0; visibility: hidden; }
```

**The Chrome top/bottom bars carry no border or divider**—they are pure text overlays on a transparent background; do not add border-top / border-bottom / box-shadow.

---

```css
.nav {
  position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 6px; z-index: 30;
  padding: 8px 14px;
  background: rgba(255,255,255,.82); backdrop-filter: blur(12px);
  border: 1px solid var(--line); border-radius: 20px;
}
.nav i {
  width: 22px; height: 3px; background: var(--line-strong);
  border-radius: 2px; transition: all .35s ease; cursor: pointer;
}
.nav i.active { background: var(--accent); width: 44px; }
```

**Note**: the global rule keeps only the bottom dots navigation; left/right navigation arrows are forbidden. When generating, **do not output** any arrow HTML, and do not define any `.arrow`-related styles.

---

## 5. Typography Helper Classes

```css
.kicker {
  display: inline-flex; align-items: center; gap: 12px;
  font-family: var(--mono); font-size: 12px; letter-spacing: .22em;
  text-transform: uppercase; color: var(--accent);
}
.kicker::before { content: ""; width: 28px; height: 2px; background: var(--accent); }

.h-display { font-family: var(--sans); font-weight: 200; font-size: 108px; line-height: .96; letter-spacing: -.03em; }
.h-1 { font-family: var(--sans); font-weight: 300; font-size: 72px; line-height: 1.02; letter-spacing: -.02em; }
.h-2 { font-family: var(--sans); font-weight: 400; font-size: 38px; line-height: 1.15; }
.lead { font-family: var(--sans); font-size: 18px; line-height: 1.7; color: var(--text-2); max-width: 62ch; }
.body { font-size: 15px; line-height: 1.7; color: var(--text-2); }
.en { font-family: var(--mono); font-weight: 400; letter-spacing: .08em; text-transform: uppercase; }
.en-num { font-family: var(--sans); font-variant-numeric: tabular-nums; }
.rule { height: 1px; background: var(--line); width: 100%; }
```

---

## 6. T01 Cover Styles

```css
.s-cover { grid-template-columns: 1fr; grid-template-rows: 1fr auto; align-items: stretch; }
.cover-main { align-self: center; }
.cover-meta { display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; padding-top: 32px; border-top: 1px solid var(--line); }
.cover-meta > div { color: var(--text-3); font-family: var(--mono); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; }
.cover-meta strong { display: block; margin-top: 8px; color: var(--text); font-family: var(--sans); font-weight: 600; font-size: 18px; letter-spacing: -.01em; text-transform: none; }
.cover-chinese { font-family: var(--sans); font-weight: 200; line-height: .95; font-size: 120px; letter-spacing: -.025em; display: flex; flex-direction: column; }
.cover-chinese span:last-child { color: var(--accent); }
.cover-sub { margin-top: 22px; max-width: 68ch; }
.cover-sub em { font-style: normal; color: var(--text); font-weight: 500; }
```

---

## 7. T01-B Cover Split Styles

```css
.s-cover-split { grid-template-columns: 1fr 1fr; padding: 0; }
.cover-split-text { padding: 40px 51px; display: flex; flex-direction: column; justify-content: center; gap: 0; }
.cover-split-text .kicker { font-family: var(--mono); font-size: 11px; letter-spacing: .22em; text-transform: uppercase; color: var(--text-3); }
.cover-split-text .h-display { font-family: var(--sans); font-size: 77px; line-height: .96; font-weight: 200; letter-spacing: -.03em; margin-top: 20px; }
.cover-split-text .lead { margin-top: 24px; max-width: 38ch; }
/* Tags sit directly under the lead. The text column is a centered flex column
   (justify-content:center), so `margin-top:auto` here would absorb all remaining
   vertical space and shove the tags to the very bottom of the column — leaving a
   huge gap between the title block and the tags. Use a fixed margin so the tags
   stay grouped with the title/lead. */
.cover-split-tags { margin-top: 28px; display: flex; gap: 16px; flex-wrap: wrap; }
.cover-split-tags span { font-family: var(--mono); font-size: 11px; letter-spacing: .16em; text-transform: uppercase; padding: 6px 14px; border: 1px solid var(--line); border-radius: 999px; color: var(--text-2); }
.cover-split-img { overflow: hidden; position: relative; }
.cover-split-img img { width: 100%; height: 100%; object-fit: cover; display: block; }
```

---

## 8. T01-C Cover Minimal Styles

```css
.s-cover-min { grid-template-rows: auto 1fr auto; gap: 0; }
.cover-min-top { display: flex; justify-content: space-between; align-items: center; font-family: var(--mono); font-size: 12px; letter-spacing: .16em; text-transform: uppercase; color: var(--text-3); padding-bottom: 24px; border-bottom: 1px solid var(--line); }
.cover-min-center { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0; }
.cover-min-center .h-display { font-family: var(--sans); font-size: 128px; line-height: .92; font-weight: 200; letter-spacing: -.04em; }
.cover-min-center .lead { margin-top: 28px; max-width: 52ch; font-size: 15px; text-align: center; }
.cover-min-bottom { display: flex; justify-content: space-between; align-items: center; font-family: var(--mono); font-size: 12px; letter-spacing: .16em; text-transform: uppercase; color: var(--text-3); padding-top: 24px; border-top: 1px solid var(--line); }
```

---

## 9. T01-D Cover Hero Styles

```css
.s-cover-hero { grid-template-rows: 1fr auto; padding: 0; overflow: hidden; }
.cover-hero-bg { position: absolute; inset: 0; z-index: 0; }
.cover-hero-bg img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cover-hero-bg::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,.72) 0%, rgba(0,0,0,.18) 50%, transparent 100%); }
.cover-hero-content { position: relative; z-index: 1; padding: 0 51px 29px; align-self: end; max-width: 70%; }
.cover-hero-content .kicker { font-family: var(--mono); font-size: 11px; letter-spacing: .22em; text-transform: uppercase; color: rgba(255,255,255,.7); }
.cover-hero-content .h-display { font-family: var(--sans); font-size: 95px; line-height: .94; font-weight: 200; letter-spacing: -.03em; color: #fff; margin-top: 16px; }
.cover-hero-content .lead { margin-top: 20px; max-width: 48ch; font-size: 14px; color: rgba(255,255,255,.82); }
.cover-hero-meta { position: relative; z-index: 1; padding: 17px 51px; display: flex; justify-content: flex-end; gap: 32px; font-family: var(--mono); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: rgba(255,255,255,.6); }
```

---

## 10. T02 Agenda Styles

```css
.s-agenda { grid-template-columns: minmax(280px, 26%) 1fr; gap: 77px; align-items: center; }
.agenda-side { align-self: center; padding-bottom: 8px; }
.agenda-side .lead { margin-top: 24px; }
.agenda-list { display: flex; flex-direction: column; min-height: 0; overflow: hidden; align-self: center; }
.agenda-item { display: grid; grid-template-columns: 90px 1fr auto; align-items: baseline; padding: 18px 0; border-top: 1px solid var(--line); gap: 24px; }
.agenda-item:last-child { border-bottom: 1px solid var(--line); }
.agenda-item .idx { font-family: var(--sans); font-weight: 200; font-size: 22px; color: var(--accent); font-variant-numeric: tabular-nums; }
.agenda-item .name { font-family: var(--sans); font-weight: 500; font-size: 26px; letter-spacing: -.015em; }
.agenda-item .en { color: var(--text-3); font-size: 13px; letter-spacing: .14em; text-transform: uppercase; font-family: var(--mono); }
```

---

## 11. T03 Brand Styles

```css
.s-brand { grid-template-columns: 1fr 1fr; gap: 69px; align-items: center; }
.brand-left h1 { margin-top: 20px; }
.brand-left .lead { margin-top: 22px; }
.brand-stats { margin-top: 40px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding-top: 24px; border-top: 1px solid var(--line); }
.brand-stats > div { display: grid; grid-template-rows: 1fr auto; align-items: end; }
.brand-stats .k { font-family: var(--sans); font-weight: 200; font-size: 46px; color: var(--text); letter-spacing: -.02em; line-height: 1; display: flex; align-items: flex-end; }
.brand-stats .k b { color: var(--accent); font-weight: 500; }
.brand-stats .lbl { margin-top: 8px; color: var(--text-3); font-size: 12px; letter-spacing: .16em; text-transform: uppercase; font-family: var(--mono); }
/* Right column is centered (align-items:center); if the stacked cards exceed the
   582px content area (720 − 2×69 pad) they overflow symmetrically into the bottom
   page-number chrome. Two layers of defense: (1) card padding/desc are tuned so
   4 cards with ≤2-line desc stay under 582px (~129px/card ×4 + 14px gap ×3 ≈ 558px);
   (2) max-height:582 + overflow:hidden is a HARD cap so that even over-long copy or
   a 5th card is clipped instead of spilling into the chrome. Keep ≤4 cards and
   desc ≤2 lines; do NOT patch a single generated slide. */
.brand-cards { display: grid; grid-template-columns: 1fr; gap: 14px; max-height: 582px; overflow: hidden; align-content: center; }
.brand-card { padding: 20px 24px; background: var(--bg-2); border: 1px solid var(--line); border-radius: 12px; display: grid; grid-template-columns: 46px 1fr auto; align-items: center; gap: 22px; transition: transform .3s ease, border-color .3s ease; }
.brand-card:hover { transform: translateY(-2px); border-color: var(--accent); }
.brand-card .tag { font-family: var(--mono); font-size: 11px; color: var(--text-3); letter-spacing: .18em; text-transform: uppercase; font-variant-numeric: tabular-nums; }
.brand-card .title { font-family: var(--sans); font-weight: 600; font-size: 19px; margin-top: 4px; }
.brand-card .desc { color: var(--text-2); font-size: 13px; margin-top: 6px; line-height: 1.5; }
.brand-card .badge { padding: 6px 12px; border: 1px solid var(--accent); border-radius: 999px; font-family: var(--mono); font-size: 11px; letter-spacing: .16em; text-transform: uppercase; color: var(--accent); }
```

---

## 12. T04 Grid Lines Styles

```css
.s-lines { grid-template-rows: auto auto; gap: 48px; align-content: center; }
.lines-head { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 32px; }
.lines-head .h-1 { font-size: 64px; }
.lines-head .lead { max-width: 56ch; margin-top: 16px; font-size: 14px; }
.lines-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: var(--line); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.line-cell { background: var(--bg); padding: 30px 26px 22px; display: grid; grid-template-rows: auto auto 1fr auto; gap: 14px; min-height: 240px; position: relative; transition: background .35s ease; overflow: hidden; }
.line-cell::after { content: ""; position: absolute; top: 0; left: 0; width: 0; height: 2px; background: var(--accent); transition: width .5s cubic-bezier(.2,.7,.15,1); }
.line-cell:hover { background: var(--bg-2); }
.line-cell:hover::after { width: 100%; }
.line-cell .num { position: absolute; top: 22px; right: 24px; font-family: var(--sans); font-weight: 200; font-size: 34px; line-height: 1; color: var(--line-strong); font-variant-numeric: tabular-nums; letter-spacing: -.02em; transition: color .35s; }
.line-cell:hover .num { color: var(--accent); }
.line-cell .head { display: flex; flex-direction: column; gap: 10px; padding-right: 44px; }
.line-cell .name { font-family: var(--sans); font-weight: 600; font-size: 24px; line-height: 1; letter-spacing: -.01em; }
.line-cell .micro-rule { width: 24px; height: 2px; background: var(--accent); }
.line-cell .en { font-family: var(--mono); font-size: 10.5px; color: var(--text-3); letter-spacing: .22em; text-transform: uppercase; font-weight: 500; }
.line-cell .desc { font-size: 14px; line-height: 1.7; color: var(--text-2); padding-right: 8px; align-self: end; }
.line-cell .desc em { font-style: normal; color: var(--text); font-weight: 500; }
.line-cell .foot { display: flex; align-items: center; gap: 12px; padding-top: 14px; border-top: 1px solid var(--line); }
.line-cell .foot .glyph { width: 6px; height: 6px; background: var(--accent); display: inline-block; transform: rotate(45deg); margin: 0; }
.line-cell .accent { font-family: var(--mono); font-size: 10.5px; color: var(--accent); letter-spacing: .24em; text-transform: uppercase; font-weight: 500; }
.line-cell.consensus { background: radial-gradient(120% 100% at 100% 0%, rgba(75, 63, 227, .06), transparent 60%), var(--bg); }
.line-cell.consensus .num { color: var(--accent); }
.line-cell.consensus .name { color: var(--accent); }
.line-cell.consensus .desc em { color: var(--accent); }
```

---

## 13. T05 Team Cards Styles

```css
.s-team { grid-template-columns: 40% 1fr; gap: 77px; align-items: center; }
/* Right column is centered (align-items:center); if the 2×2 cards are taller than
   the 582px content area (720 − 2×69 pad) they overflow symmetrically into the
   bottom page-number chrome. min-height is a floor (keeps short cards even), and
   max-height + overflow caps the worst case. Tuned so 4 cards with ≤3-line desc
   stay under 582px (~176px/card ×2 rows + 20px gap ≈ 372px). Keep desc ≤3 lines;
   do NOT patch a single generated slide. */
.team-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-height: 582px; overflow: hidden; align-content: center; }
.team-card { padding: 24px 24px; background: var(--bg-2); border: 1px solid var(--line); border-radius: 12px; display: flex; flex-direction: column; gap: 12px; min-height: 168px; position: relative; overflow: hidden; transition: border-color .3s ease, background .3s ease; }
.team-card:hover { border-color: var(--accent); background: var(--surface); }
.team-card .idx { font-family: var(--mono); font-weight: 500; color: var(--accent); font-size: 12px; letter-spacing: .2em; }
.team-card .title { font-family: var(--sans); font-weight: 600; font-size: 19px; line-height: 1.25; }
.team-card .desc { color: var(--text-2); font-size: 13px; line-height: 1.55; margin-top: auto; }
.team-card .en-sub { font-family: var(--mono); font-size: 11px; color: var(--text-3); letter-spacing: .18em; text-transform: uppercase; margin-top: 4px; }
```

---

## 14. T06 Refine List Styles

```css
.s-refine { grid-template-columns: 34% 1fr; gap: 77px; align-items: center; }
/* Right list fits the 582px content area (720 − 2×69 pad) for 3–6 items.
   Defaults are tuned so 5 items with 1–2 line descriptions never reach the
   bottom chrome, and max-height:582 + overflow:hidden is a HARD cap so an extra
   item or over-long copy is clipped rather than spilling into the page-number
   chrome. Do NOT patch a single slide with an ad-hoc compact class —
   these defaults already keep every T06 in-bounds. */
.refine-list { display: grid; gap: 0; align-content: center; max-height: 582px; overflow: hidden; }
.refine-item { display: grid; grid-template-columns: 90px 1fr; gap: 32px; padding: 18px 0; border-top: 1px solid var(--line); align-items: start; }
.refine-item:last-child { border-bottom: 1px solid var(--line); }
.refine-item .idx { font-family: var(--mono); font-size: 13px; color: var(--text-3); letter-spacing: .16em; padding-top: 5px; font-variant-numeric: tabular-nums; }
.refine-item .idx b { color: var(--accent); font-weight: 500; }
.refine-item .h { font-family: var(--sans); font-weight: 600; font-size: 22px; letter-spacing: -.01em; }
.refine-item .d { color: var(--text-2); font-size: 13.5px; line-height: 1.55; margin-top: 6px; max-width: 68ch; }
/* When a deck genuinely needs 6 items, add .refine-dense on .refine-list to
   shave spacing further; never exceed 6 items on one T06 slide. */
.refine-list.refine-dense .refine-item { padding: 12px 0; }
.refine-list.refine-dense .refine-item .h { font-size: 20px; }
.refine-list.refine-dense .refine-item .d { font-size: 13px; line-height: 1.5; margin-top: 4px; }
```

---

## 15. T07 Think Styles

```css
.s-think { display: grid; grid-template-columns: 1fr; align-items: center; }
/* Content is vertically centered in the 582px area (720 − 2×69 pad). Because a
   centered grid overflows symmetrically, any excess spills into the bottom
   page-number chrome. Two layers of defense: (1) defaults are tuned to keep the
   worst realistic case (3-line question + 2-line sub + two notes) under 582px;
   (2) .think-wrap carries max-height:582 + overflow:hidden as a HARD cap so even
   over-long copy is clipped instead of drifting into the chrome. Keep the
   question to ≤3 lines and ≤2 notes; do NOT rescue an overflow by patching one
   slide. */
.think-wrap { max-width: 1100px; max-height: 582px; overflow: hidden; }
.think-kicker { color: var(--accent); font-family: var(--mono); font-size: 13px; letter-spacing: .3em; text-transform: uppercase; }
.think-q { margin-top: 22px; font-family: var(--sans); font-weight: 200; font-size: 76px; line-height: 1.04; letter-spacing: -.025em; }
.think-q em { font-style: normal; color: var(--accent); }
.think-sub { margin-top: 26px; max-width: 72ch; color: var(--text-2); font-size: 15px; line-height: 1.65; }
/* Notes are block-level so multiple notes stack reliably (inline-flex made
   margin-top unreliable). Each note is only as wide as its content. */
.think-note { margin-top: 20px; padding: 16px 20px; background: var(--accent-soft); border-radius: 12px; display: flex; width: fit-content; align-items: center; gap: 16px; font-family: var(--sans); font-size: 15px; color: var(--text); }
.think-note b { color: var(--accent); font-family: var(--mono); font-weight: 500; letter-spacing: .14em; font-size: 11px; text-transform: uppercase; }
```

---

## 16. T08 Closing Styles

```css
.s-close { display: grid; grid-template-columns: 1fr 1fr; padding: 0; }
.close-left { background: var(--accent); color: #fff; padding: 28px 46px 28px 77px; display: flex; flex-direction: column; justify-content: space-between; position: relative; overflow: hidden; }
.close-left canvas.ascii-bg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; opacity: .85; mix-blend-mode: screen; }
.close-left > * { position: relative; z-index: 1; }
.close-left .chrome-min { font-family: var(--mono); font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: rgba(255,255,255,.62); display: flex; justify-content: space-between; }
.close-left .manifesto { display: flex; flex-direction: column; gap: 14px; }
.close-left .manifesto .meta { font-family: var(--mono); font-size: 13px; letter-spacing: .22em; text-transform: uppercase; color: rgba(255,255,255,.78); margin-bottom: 12px; }
.close-left .manifesto h2 { font-family: var(--sans); font-size: 86px; line-height: .96; letter-spacing: -.025em; font-weight: 200; color: #fff; }
.close-left .manifesto h2 em { font-style: italic; font-weight: 300; }
.close-left .manifesto .sub { font-family: var(--sans); font-size: 14px; line-height: 1.6; color: rgba(255,255,255,.82); font-weight: 400; max-width: 36ch; margin-top: 10px; }
.close-left .sig { display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid rgba(255,255,255,.22); padding-top: 14px; font-family: var(--mono); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: rgba(255,255,255,.62); }
.close-right { background: var(--bg); color: var(--text); padding: 28px 77px 28px 46px; display: flex; flex-direction: column; justify-content: space-between; }
.close-right .chrome-min { font-family: var(--mono); font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: var(--text-3); display: flex; justify-content: space-between; }
.close-right .takeaways { display: flex; flex-direction: column; gap: 0; }
.close-right .take-item { display: grid; grid-template-columns: auto 1fr; gap: 26px; align-items: start; padding: 19px 0; border-top: 1px solid var(--line); }
.close-right .take-item:last-child { border-bottom: 2px solid var(--accent); }
.close-right .take-item .num { font-family: var(--sans); font-weight: 200; font-size: 56px; line-height: .9; color: var(--text); font-variant-numeric: tabular-nums; min-width: 2.2ch; }
.close-right .take-item:last-child .num { color: var(--accent); }
.close-right .take-item h3 { font-family: var(--sans); font-weight: 400; font-size: 23px; line-height: 1.2; letter-spacing: -.015em; margin-bottom: 7px; }
.close-right .take-item:last-child h3 { color: var(--accent); }
.close-right .take-item p { font-size: 16px; line-height: 1.6; color: var(--text-2); }
.close-right .foot { font-family: var(--mono); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--text-3); text-align: right; }
```

---

## 17. T09 Gallery Grid Styles

```css
.s-gallery { grid-template-rows: auto 1fr; gap: 16px; align-content: start; padding-top: 80px; padding-bottom: 84px; }
.gallery-head { display: grid; grid-template-columns: auto 1fr; align-items: end; gap: 32px; }
.gallery-head .h-1 { font-size: 44px; line-height: 1.1; }
.gallery-head .lead { max-width: 48ch; font-size: 13px; align-self: end; }
.gallery-grid { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 12px; overflow: hidden; min-height: 0; }
.gallery-card { display: flex; flex-direction: column; gap: 6px; transition: transform .3s ease; min-height: 0; overflow: hidden; }
.gallery-card:hover { transform: translateY(-2px); }
.gallery-img { flex: 1; min-height: 0; overflow: hidden; border-radius: 12px; border: 1px solid var(--line); background: var(--bg-2); }
.gallery-img img { width: 100%; height: 100%; object-fit: cover; object-position: top; transition: transform .5s ease; }
.gallery-card:hover .gallery-img img { transform: scale(1.02); }
.gallery-cap { display: flex; align-items: center; gap: 14px; padding: 0 4px; flex-shrink: 0; }
.gallery-cap .label { font-family: var(--mono); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); font-weight: 500; white-space: nowrap; }
.gallery-cap .title { font-family: var(--sans); font-size: 15px; font-weight: 500; color: var(--text); }
```

---

## 18. T10 Feature Split Styles

```css
.s-feature { grid-template-columns: 55% 1fr; gap: 64px; align-items: center; }
.s-feature.reverse { grid-template-columns: 1fr 55%; }
.s-feature.reverse .feature-img { order: 2; }
.s-feature.reverse .feature-text { order: 1; }
.feature-img { border-radius: 12px; overflow: hidden; border: 1px solid var(--line); background: var(--bg-2); }
.feature-img img { width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }
.feature-text .h-1 { font-size: 42px; line-height: 1.1; }
.feature-text .lead { margin-top: 18px; }
/* The text column is centered (align-items:center); if kicker+title+lead+points
   exceed the 582px content area (720 − 2×69 pad) it overflows symmetrically into
   the bottom chrome. Two layers of defense: (1) padding/type are tuned so the
   worst realistic case — 2-line 42px title + 2-line lead + 3 points with 2-line
   desc (~475px) — stays under 582px; (2) max-height:582 + overflow:hidden is a
   HARD cap so that even over-long copy is clipped instead of spilling into the
   page-number chrome. Keep ≤3 points and desc ≤2 lines; do NOT patch a single
   generated slide. */
.feature-text { max-height: 582px; overflow: hidden; align-self: center; }
.feature-points { margin-top: 28px; display: grid; gap: 0; }
.feature-point { display: grid; grid-template-columns: 60px 1fr; gap: 20px; padding: 14px 0; border-top: 1px solid var(--line); align-items: start; }
.feature-point:last-child { border-bottom: 1px solid var(--line); }
.feature-point .idx { font-family: var(--mono); font-size: 13px; color: var(--accent); letter-spacing: .16em; padding-top: 4px; font-weight: 500; }
.feature-point .h { font-family: var(--sans); font-weight: 600; font-size: 18px; letter-spacing: -.01em; }
.feature-point .d { color: var(--text-2); font-size: 13.5px; line-height: 1.55; margin-top: 5px; }
```

---

## 19. T11 Duo Images Styles

```css
.s-duo { grid-template-rows: auto 1fr; gap: 20px; align-content: start; padding-top: 80px; padding-bottom: 84px; }
.duo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; min-height: 0; overflow: hidden; }
.duo-card { display: flex; flex-direction: column; gap: 12px; min-height: 0; overflow: hidden; }
.duo-card .duo-img { flex: 1; min-height: 0; overflow: hidden; border-radius: 12px; border: 1px solid var(--line); background: var(--bg-2); }
.duo-card .duo-img img { width: 100%; height: 100%; object-fit: cover; object-position: center; display: block; }
.duo-card .duo-cap { flex-shrink: 0; }
.duo-cap .label { font-family: var(--mono); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); font-weight: 500; }
.duo-cap .title { font-family: var(--sans); font-size: 18px; font-weight: 600; margin-top: 6px; }
.duo-cap .desc { font-size: 14px; color: var(--text-2); line-height: 1.6; margin-top: 6px; max-width: 52ch; }
```

---

## 20. T12 Trio Images Styles

```css
.s-trio { grid-template-rows: auto 1fr; gap: 16px; align-content: start; padding-top: 80px; padding-bottom: 84px; }
.trio-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 0; overflow: hidden; }
.trio-main { display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow: hidden; }
.trio-main .trio-img { flex: 1; min-height: 0; overflow: hidden; border-radius: 12px; border: 1px solid var(--line); background: var(--bg-2); }
.trio-main .trio-img img { width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }
.trio-side { display: grid; grid-template-rows: 1fr 1fr; gap: 16px; min-height: 0; }
.trio-side .trio-card { display: flex; flex-direction: column; gap: 8px; min-height: 0; overflow: hidden; }
.trio-side .trio-img { flex: 1; min-height: 0; overflow: hidden; border-radius: 12px; border: 1px solid var(--line); background: var(--bg-2); }
.trio-side .trio-img img { width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }
.trio-cap { flex-shrink: 0; display: flex; align-items: center; gap: 12px; }
.trio-cap .label { font-family: var(--mono); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); font-weight: 500; white-space: nowrap; }
.trio-cap .title { font-family: var(--sans); font-size: 14px; font-weight: 500; color: var(--text); }
```

---

## 21. T13 Hero Image Styles

```css
.s-hero { grid-template-rows: 1fr auto; gap: 0; padding: 56px var(--pad-x) 56px; }
.hero-img { position: relative; overflow: hidden; min-height: 0; max-height: 456px; border-radius: 12px; border: 1px solid var(--line); }
.hero-img img { width: 100%; height: 100%; object-fit: cover; object-position: center; display: block; }
.hero-bottom { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 32px; padding: 22px 4px 0; }
.hero-bottom .kicker { margin-bottom: 6px; }
.hero-bottom .h-1 { font-size: 41px; line-height: 1.1; }
.hero-bottom .lead { margin-top: 8px; font-size: 13px; }
.hero-meta { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.hero-meta span { font-family: var(--mono); font-size: 11px; letter-spacing: .16em; text-transform: uppercase; color: var(--text-3); }
.hero-meta strong { color: var(--text); font-weight: 500; margin-left: 8px; font-family: var(--sans); text-transform: none; letter-spacing: 0; }
.hero-meta .tagline { color: var(--accent); }
```

---

## 22. T14 Penta Styles

```css
.s-penta { grid-template-rows: auto 1fr; gap: 16px; align-content: start; padding-top: 80px; padding-bottom: 84px; }
.penta-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 12px; min-height: 0; overflow: hidden; }
.penta-grid .penta-card:nth-child(1) { grid-column: 1 / 2; grid-row: 1 / 3; }
.penta-grid .penta-card:nth-child(2) { grid-column: 2 / 3; grid-row: 1 / 2; }
.penta-grid .penta-card:nth-child(3) { grid-column: 3 / 4; grid-row: 1 / 2; }
.penta-grid .penta-card:nth-child(4) { grid-column: 2 / 3; grid-row: 2 / 3; }
.penta-grid .penta-card:nth-child(5) { grid-column: 3 / 4; grid-row: 2 / 3; }
.penta-card { position: relative; overflow: hidden; border-radius: 12px; border: 1px solid var(--line); background: var(--bg-2); min-height: 0; transition: transform .3s ease; }
.penta-card:hover { transform: translateY(-2px); }
.penta-card img { width: 100%; height: 100%; object-fit: cover; object-position: center; display: block; transition: transform .5s ease; }
.penta-card:hover img { transform: scale(1.02); }
.penta-card .cap { position: absolute; bottom: 0; left: 0; right: 0; padding: 14px 16px; background: linear-gradient(to top, rgba(0,0,0,.55), transparent); }
.penta-card .cap .title { font-size: 13px; font-weight: 500; color: #fff; }
.penta-card .cap .sub { font-size: 11px; color: rgba(255,255,255,.7); margin-top: 2px; }
```

---

## 23. T15 Hexa Styles

```css
.s-hexa { grid-template-rows: auto 1fr; gap: 16px; align-content: start; padding-top: 80px; padding-bottom: 84px; }
.hexa-grid { display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr 1fr; gap: 12px; min-height: 0; overflow: hidden; }
.hexa-card { position: relative; overflow: hidden; border-radius: 12px; border: 1px solid var(--line); background: var(--bg-2); min-height: 0; transition: transform .3s ease; }
.hexa-card:hover { transform: translateY(-2px); }
.hexa-card img { width: 100%; height: 100%; object-fit: cover; object-position: center; display: block; transition: transform .5s ease; }
.hexa-card:hover img { transform: scale(1.02); }
.hexa-card .cap { position: absolute; bottom: 0; left: 0; right: 0; padding: 12px 14px; background: linear-gradient(to top, rgba(0,0,0,.55), transparent); }
.hexa-card .cap .title { font-size: 12px; font-weight: 500; color: #fff; }
.hexa-card .cap .sub { font-size: 10px; color: rgba(255,255,255,.7); margin-top: 2px; }
```

---

## 24. T16 Mosaic Styles

```css
.s-mosaic { grid-template-rows: auto 1fr; gap: 16px; align-content: start; padding-top: 80px; padding-bottom: 84px; }
.mosaic-grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: 1fr 1fr; gap: 10px; min-height: 0; overflow: hidden; }
.mosaic-grid .mosaic-card:nth-child(1) { grid-column: 1 / 3; grid-row: 1 / 2; }
.mosaic-grid .mosaic-card:nth-child(2) { grid-column: 3 / 4; grid-row: 1 / 2; }
.mosaic-grid .mosaic-card:nth-child(3) { grid-column: 4 / 5; grid-row: 1 / 3; }
.mosaic-grid .mosaic-card:nth-child(4) { grid-column: 1 / 2; grid-row: 2 / 3; }
.mosaic-grid .mosaic-card:nth-child(5) { grid-column: 2 / 3; grid-row: 2 / 3; }
.mosaic-grid .mosaic-card:nth-child(6) { grid-column: 3 / 4; grid-row: 2 / 3; }
.mosaic-card { position: relative; overflow: hidden; border-radius: 10px; border: 1px solid var(--line); background: var(--bg-2); min-height: 0; transition: transform .3s ease; }
.mosaic-card:hover { transform: translateY(-2px); }
.mosaic-card img { width: 100%; height: 100%; object-fit: cover; object-position: center; display: block; transition: transform .5s ease; }
.mosaic-card:hover img { transform: scale(1.02); }
.mosaic-card .cap { position: absolute; bottom: 0; left: 0; right: 0; padding: 10px 12px; background: linear-gradient(to top, rgba(0,0,0,.5), transparent); }
.mosaic-card .cap .title { font-size: 11px; font-weight: 500; color: #fff; }
```

---

## 25. T17 Chart Styles

```css
.s-chart { grid-template-rows: auto 1fr; gap: 18px; padding-top: 80px; padding-bottom: 84px; }
.chart-head { display: grid; grid-template-columns: auto 1fr; align-items: end; gap: 32px; }
.chart-head .h-1 { font-size: 38px; line-height: 1.1; margin-top: 12px; }
.chart-head .lead { max-width: 48ch; font-size: 13px; align-self: end; }

.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--line); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; min-height: 0; }
.chart-grid.cols-1 { grid-template-columns: 1fr; }
.chart-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
.chart-grid.cols-2x2 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
.chart-grid.cols-3x2 { grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr 1fr; }

.chart-panel { display: flex; flex-direction: column; gap: 10px; padding: 20px 22px; background: var(--bg); min-height: 0; }
.chart-panel .chart-cap { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.chart-panel .chart-title { font-family: var(--mono); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); font-weight: 500; white-space: nowrap; }
.chart-panel .chart-subtitle { font-size: 15px; font-weight: 500; color: var(--text); }
.chart-panel .chart-area { flex: 1; min-height: 0; position: relative; }
.chart-panel .chart-area svg { width: 100%; height: 100%; }
```

---

## 26. Motion and Decoration

```css
.glyph { display: inline-block; width: 10px; height: 10px; background: var(--accent); transform: rotate(45deg); vertical-align: middle; margin-right: 12px; }

.slide.active .stagger > * { animation: rise .7s cubic-bezier(.2,.7,.15,1) both; }
.slide.active .stagger > *:nth-child(1) { animation-delay: .05s; }
.slide.active .stagger > *:nth-child(2) { animation-delay: .12s; }
.slide.active .stagger > *:nth-child(3) { animation-delay: .19s; }
.slide.active .stagger > *:nth-child(4) { animation-delay: .26s; }
.slide.active .stagger > *:nth-child(5) { animation-delay: .33s; }
.slide.active .stagger > *:nth-child(6) { animation-delay: .40s; }
.slide.active .stagger > *:nth-child(7) { animation-delay: .47s; }
.slide.active .stagger > *:nth-child(8) { animation-delay: .54s; }
@keyframes rise {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: none; }
}
```

---

## 27. Responsive

The deck is a fixed 1280×720 canvas. Responsiveness is handled **only** by the
`fitDeck()` scale in the navigation script — the whole deck is scaled as one block
via `transform: translate(-50%,-50%) scale(s)`. Do **not** add media queries or
viewport units (`vw`/`vh`/`100vw`/`100vh`/viewport-based `min()`/`max()`) inside the
deck: they bypass the scale and double-scale against the viewport. All inner sizes
are fixed px.

**Everything is inside the deck.** The ASCII backdrop (`canvas.ascii-bg`), all
slides, both chrome bars (`.chrome-top`/`.chrome-bottom`), and the nav dots must be
children of `<div class="deck">` and use `position:absolute` with fixed px offsets —
never `position:fixed` against the viewport. Fixed-positioned chrome would stay
locked to the window edges and drift off the scaled canvas on large screens.

---

## 28. ASCII Breathing-field Script

```javascript
(function(){
  const canvas = document.getElementById('asciiBg');
  if(!canvas) return;
  const PALETTE = '   ...:::---+++***';
  const CELL = 16;
  const FONT_SIZE = 13;
  let ctx, w, h, dpr, cols, rows;
  let t0 = performance.now();

  function setup(){
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    // Fixed canvas dimensions — the ascii-bg lives inside the 1280×720 deck and
    // scales with it, so it must NOT read window.innerWidth/innerHeight.
    w = 1280; h = 720;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.font = '500 ' + FONT_SIZE + 'px JetBrains Mono, monospace';
    ctx.textBaseline = 'top';
    cols = Math.ceil(w / CELL); rows = Math.ceil(h / CELL);
  }

  function draw(t){
    if(!ctx) return;
    ctx.clearRect(0, 0, w, h);
    for(let r = 0; r < rows; r++){
      for(let c = 0; c < cols; c++){
        const n = (Math.sin(c * 0.18 + t) + Math.sin(r * 0.24 - t * 0.7) + Math.sin((c + r) * 0.12 + t * 0.45) + Math.sin(Math.hypot(c - cols * 0.5, r - rows * 0.5) * 0.16 - t * 0.55)) / 4;
        const v = (n + 1) / 2;
        if(v < 0.22) continue;
        const idx = Math.min(PALETTE.length - 1, Math.floor(v * PALETTE.length));
        const ch = PALETTE[idx];
        if(ch === ' ') continue;
        ctx.fillStyle = 'rgba(75, 63, 227, ' + (0.03 + (v - 0.22) * 0.12).toFixed(3) + ')';
        ctx.fillText(ch, c * CELL, r * CELL);
      }
    }
  }

  function tick(now){
    draw((now - t0) / 1000 * 0.55);
    requestAnimationFrame(tick);
  }

  window.addEventListener('resize', () => requestAnimationFrame(setup), {passive: true});
  setup();
  requestAnimationFrame(tick);
})();
```

**T08 left-side white ASCII (for the closing page only)**

```javascript
(function(){
  const canvas = document.querySelector('.close-left canvas.ascii-bg');
  if(!canvas) return;
  const PALETTE = '   ...:::---+++***';
  const CELL = 14;
  let ctx, w, h, dpr, cols, rows;
  let t0 = performance.now();

  function setup(){
    const rect = canvas.parentElement.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = rect.width; h = rect.height;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.font = '500 12px JetBrains Mono, monospace';
    ctx.textBaseline = 'top';
    cols = Math.ceil(w / CELL); rows = Math.ceil(h / CELL);
  }

  function draw(t){
    if(!ctx) return;
    ctx.clearRect(0, 0, w, h);
    for(let r = 0; r < rows; r++){
      for(let c = 0; c < cols; c++){
        const n = (Math.sin(c * 0.2 + t) + Math.sin(r * 0.26 - t * 0.7) + Math.sin((c + r) * 0.14 + t * 0.5) + Math.sin(Math.hypot(c - cols * 0.5, r - rows * 0.5) * 0.18 - t * 0.6)) / 4;
        const v = (n + 1) / 2;
        if(v < 0.2) continue;
        const idx = Math.min(PALETTE.length - 1, Math.floor(v * PALETTE.length));
        const ch = PALETTE[idx];
        if(ch === ' ') continue;
        ctx.fillStyle = 'rgba(255, 255, 255, ' + (0.08 + (v - 0.2) * 0.35).toFixed(3) + ')';
        ctx.fillText(ch, c * CELL, r * CELL);
      }
    }
  }

  function tick(now){
    draw((now - t0) / 1000 * 0.5);
    requestAnimationFrame(tick);
  }

  window.addEventListener('resize', () => requestAnimationFrame(setup), {passive: true});
  setup();
  requestAnimationFrame(tick);
})();
```

---

## 29. Navigation Script

```javascript
const deck = document.getElementById('deck');
const slides = Array.from(deck.querySelectorAll('.slide'));
const nav = document.getElementById('nav');
const pageNum = document.getElementById('pageNum');
let current = 0;

// Proportional canvas scaling: the 1280×720 deck is scaled as one block to fit the
// viewport. All inner sizes are fixed px; scaling is handled solely here, never by vw/vh.
function fitDeck() {
  const s = Math.min(window.innerWidth / 1280, window.innerHeight / 720);
  deck.style.transform = 'translate(-50%,-50%) scale(' + s + ')';
}
window.addEventListener('resize', fitDeck, { passive: true });
fitDeck();

slides.forEach((_, i) => {
  const b = document.createElement('i');
  if (i === 0) b.classList.add('active');
  b.addEventListener('click', () => goTo(i));
  nav.appendChild(b);
});

function goTo(idx) {
  idx = Math.max(0, Math.min(slides.length - 1, idx));
  if (idx === current) return;
  slides[current].classList.remove('active');
  slides[idx].classList.add('active');
  nav.children[current].classList.remove('active');
  nav.children[idx].classList.add('active');
  current = idx;
  pageNum.textContent = String(idx + 1).padStart(2, '0');
}
function go(delta) { goTo(current + delta); }

document.addEventListener('keydown', (e) => {
  if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(1); }
  if (['ArrowLeft', 'PageUp'].includes(e.key))         { e.preventDefault(); go(-1); }
  if (e.key === 'Home') goTo(0);
  if (e.key === 'End') goTo(slides.length - 1);
});

let wheelLock = false;
document.addEventListener('wheel', (e) => {
  if (wheelLock) return;
  if (Math.abs(e.deltaY) < 30) return;
  wheelLock = true;
  go(e.deltaY > 0 ? 1 : -1);
  setTimeout(() => wheelLock = false, 700);
}, { passive: true });

let touchY = 0;
document.addEventListener('touchstart', (e) => { touchY = e.touches[0].clientY; }, { passive: true });
document.addEventListener('touchend', (e) => {
  const dy = touchY - e.changedTouches[0].clientY;
  if (Math.abs(dy) > 40) go(dy > 0 ? 1 : -1);
}, { passive: true });
```

---

## 30. Google Fonts Reference

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600&family=Noto+Sans+SC:wght@200;300;400;500;700;900&display=swap" rel="stylesheet">
```

---

## 31. Chrome HTML Template

**Page structure** — the ASCII backdrop, all slides, both chrome bars, and the nav
**must all live inside `<div class="deck">`** so they scale together with the 1280×720
canvas. Nothing chrome-related sits outside the deck.

The `.chrome-top` / `.chrome-bottom` bars are **persistent across every slide**. The
one exception is the **T08 close slide**, which carries its own top/bottom text per
column; the CSS rule `.deck:has(.s-close.active) .chrome-top, …{ opacity:0 }` (see
section 3) auto-hides the deck bars while close is active so they are **not doubled**.
This is handled by CSS — do not add or remove chrome markup per slide.

```html
<body>
  <div class="deck" id="deck">
    <canvas class="ascii-bg" id="asciiBg" aria-hidden="true"></canvas>
    <!-- all <section class="slide"> go here -->
    <div class="chrome-top"> ... </div>
    <div class="chrome-bottom"> ... </div>
    <div class="nav" id="nav"></div>
  </div>
  <!-- inline <script> -->
</body>
```

**Top**
```html
<div class="chrome-top">
  <span class="mark"><span class="dot"></span>[Brand name] · <span class="en">[English subtitle]</span></span>
  <span>[Year] · [Quarter] · [Tag]</span>
</div>
```

**Bottom**
```html
<div class="chrome-bottom">
  <span>[Brand name] · <span class="en">[Organization]</span></span>
  <span class="page"><span class="num" id="pageNum">01</span><span class="sep"></span><span>[Total pages]</span></span>
</div>
```

**Navigation dots**
```html
<div class="nav" id="nav"></div>
```

---

## 32. Common Mistakes Checklist

1. **No square-corner cards** — all cards use `border-radius:12px`
2. **No dark/black backgrounds** — apart from the T08 left-side accent area, all pages have a white background
3. **Do not omit the ASCII canvas** — the background character field is the style's signature
4. **No off-brand colors** — the accent is purple only (#4B3FE3 / #3a2fb8 / #7B71FF)
5. **No round bullets** — use the diamond glyph
6. **The kicker must not be missing its left rule** — the `::before` 28px accent rule must be present
7. **The cover title must anchor the page** — the T01 cover is a single left-aligned title block (`.cover-chinese`); it has no left hero word. Let the large title carry the visual weight.
8. **No hover without feedback** — cards must have a hover state
9. **Bottom content must not cross the nav** — the nav sits at bottom:8px; keep content a safe distance away
10. **The cover Chinese text must not be too small** — `.cover-chinese` must use `font-size: 120px` (fixed px, never vw)