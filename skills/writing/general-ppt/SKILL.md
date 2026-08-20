---
name: general-pptx
description: "Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill."
license: Proprietary. LICENSE.txt has complete terms
install_source: official
install_method: download
skill_id: official55159671
enabled_at: 1787230696134
version: 1.0.0
name_zh: 通用 PPTX
---

# General PPTX Skill

## ⚠️ Completion Checklist (MANDATORY)

Before declaring any PPTX task complete, **all** of the following must be done:

- [ ] **Content QA**: `python3 -m markitdown output.pptx` — check text content, order, typos
- [ ] **Boundary check**: `python3 scripts/check_overlap.py output.pptx` — fix all `[OVERFLOW]`
- [ ] **Text overflow check**: `python3 scripts/check_text_overflow.py output.pptx` — fix all `[TEXT OVERFLOW]`
- [ ] **Visual QA via subagent**: convert to images, spawn a subagent to inspect (do NOT self-inspect)
- [ ] **Fix-and-verify cycle**: fix issues found → re-check → repeat until clean

Skipping visual QA because "markitdown looks fine" or "it's only a few slides" is **not acceptable**. See [QA (Required)](#qa-required) for details.

---

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python3 -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch | Read [crafting.md](crafting.md) |
| Acquire images for slides | See [Image Acquisition](#image-acquisition) below |

---

## Reading Content

```bash
# Text extraction
python3 -m markitdown presentation.pptx

# Visual overview
python3 scripts/thumbnail.py presentation.pptx

# Raw XML
python3 scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py` and `markitdown`
2. **Classify slides** — identify usable layouts vs. design reference pages (font specs, color swatches, icon libraries). Skip design reference slides.
3. **Measure text box constraints** — read the XML to get each text box's width, height, and font size. Calculate max content length before writing.
4. Unpack → manipulate slides → edit content (respecting size constraints) → clean → pack
5. **QA and visual inspection** — see [editing.md](editing.md) End-to-End Workflow steps 4-7

---

## Creating from Scratch

**Read [crafting.md](crafting.md) for full details.**

Use when no template or reference presentation is available.

---

## Style Discovery

Before designing slides, ask the user what visual style they want. The style choice drives color palette, layout density, and — critically — how much imagery to use.

| Style | Character | Image Strategy |
|-------|-----------|----------------|
| **Minimalist** | Clean, spacious, typography-driven. Whitespace is the hero. | Rarely use images. Rely on shapes, icons, and whitespace. Only add an image when it directly illustrates a key point (1-2 per deck max). |
| **Tech / Futuristic** | Dark backgrounds, geometric accents, modern. | Generated abstract or digital backgrounds for title/section slides. Content slides use shapes and icons, not stock photos. |
| **Business / Corporate** | Professional, structured, credible. | Stock photos on key slides (title, section dividers) — roughly 30-40% of slides. Most content slides use clean layouts with icons. |
| **Creative / Bold** | Eye-catching, expressive, strong imagery. | Heavy use of full-bleed photos and illustrations. Most slides (60-80%) benefit from visual elements. Mix search and generation. |
| **Academic / Technical** | Data-focused, structured, understated. | Charts and diagrams only. Decorative stock photos are distracting — skip them. |

If the user doesn't specify a style, infer from context (startup pitch → Business or Creative, research report → Academic, product launch → Tech or Creative). When genuinely unclear, ask — a one-sentence question is enough: "What visual style are you after — minimalist, corporate, techy, something bold, or more academic?"

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## Image Acquisition

Use images **deliberately** — not every slide needs one. Refer to the [Style Discovery](#style-discovery) table above for how aggressively to use images. When a slide does need an image, use **ImageGen** to generate it directly — do not use WebSearch to find images online (search results are unreliable and often low-quality).

### Workflow

1. **Decide which slides need images** based on the chosen style. List only those slides, noting for each:
   - A descriptive prompt (what the image should depict)
   - Purpose: background, hero image, supporting illustration, or icon
   - Desired aspect ratio (16:9 for full-bleed backgrounds, 4:3 for content areas, 1:1 for headshots)

2. **Generate images with ImageGen** — call ImageGen directly (no subagent needed). Generate each image one by one, saving them to `<output-dir>/images/`:

   - Write a detailed, specific prompt for each image describing the desired scene, style, color tones, and mood.
   - Choose the right size for the target aspect ratio:
     - `1792x1024` for 16:9 (full-slide backgrounds, wide layouts)
     - `1024x768` for 4:3 (content area illustrations)
     - `1024x1024` for 1:1 (headshots, profile images, square icons)
   - Save as `image-01.png`, `image-02.png`, etc.

3. **Use the file paths** in your slide code:
   ```javascript
   slide.addImage({ path: "<output-dir>/images/image-01.png", x: 0, y: 0, w: 10, h: 5.625 });
   ```

### Prompt Tips for ImageGen

- **Be specific about style**: "a modern flat illustration of…" or "a photorealistic aerial view of…"
- **Include color guidance**: "using warm tones of terracotta and sage green" to match the slide palette
- **Describe composition**: "left side shows X, right side shows Y, with negative space in the center for text overlay"
- **Specify mood**: "professional, clean, and minimal" vs "vibrant, energetic, and bold"
- **Avoid text in images**: Generated text is often garbled — use PptxGenJS text elements instead

### Guidelines

- **Specify dimensions.** Always choose the right ImageGen size for the target aspect ratio.
- **Save to a single directory.** All images under `<output-dir>/images/` so they can be referenced by path.
- **Match the deck's color palette.** Include the primary/accent colors in your ImageGen prompt so images feel cohesive with the slides.
- **Prefer illustration style for consistency.** AI-generated photos can look uncanny — illustrations, abstract art, and stylized graphics tend to produce better results.

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python3 -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python3 -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout|请填写|标题区域|内容区域|高亮词部分|请添加正文|请写描述|限制.*行|不超过.*行|设计完成后删除"
```

If grep returns results, fix them before declaring success. Common Chinese placeholder patterns include "请填写大标题", "标题区域", "内容区域", "高亮词部分" — these all indicate unfilled template text.

### Boundary Check (Hard Gate)

Run the boundary checker **before** visual QA. It catches elements that extend past the slide edges — something code can detect reliably.

```bash
python3 scripts/check_overlap.py output.pptx
```

If it reports `[OVERFLOW]` issues, fix them before proceeding. Adjust x/y/w/h so every element fits within the slide dimensions. Re-run after each fix.

Element **overlaps** (text-on-text, text-on-image) are not checked here — many overlaps are intentional design (text on cards, labels on backgrounds). Overlap issues are caught in Visual QA below.

### Text Overflow Check (Hard Gate)

Run the text overflow checker to detect text boxes where content doesn't fit. It temporarily enables auto-shrink on all text boxes, re-saves via LibreOffice, and reports any box where the font was scaled down.

```bash
python3 scripts/check_text_overflow.py output.pptx
```

If it reports `[TEXT OVERFLOW]` issues, **shorten the text content** to fit — do not resize text boxes or reduce font sizes, as this breaks the template's design proportions. Re-run after each fix.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- TEXT OVERFLOW: text visibly cut off at the bottom or right edge of its text box, or text crammed/compressed to fit
- Overlapping elements that look like bugs (text colliding with other text, lines cutting through words, elements stacked unintentionally). Ignore intentional layering like text on colored cards or labels on backgrounds.
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder/template text (e.g., "请填写", "标题区域", "高亮词部分", "lorem ipsum")
- Design reference content that wasn't removed (font specs, color swatches, icon grids)

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python3 scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

- `pip3 install "markitdown[pptx]"` - text extraction
- `pip3 install Pillow` - thumbnail grids
- `npm install -g pptxgenjs` - creating from scratch
- `npm install -g react-icons react react-dom sharp` - icon rendering
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images

### Missing Command Policy

**When a command fails with "command not found" or "No module named", always attempt to install it before trying alternatives.** Do not skip steps, substitute tools, or work around missing dependencies — install them.

| Missing command | Install with |
|-----------------|--------------|
| `markitdown` | `pip3 install "markitdown[pptx]"` |
| `python3 -m markitdown` (ModuleNotFoundError) | `pip3 install "markitdown[pptx]"` |
| `pptxgenjs` / `require("pptxgenjs")` | `npm install -g pptxgenjs` |
| `sharp` / `require("sharp")` | `npm install -g sharp` |
| `react-icons` / `require("react-icons/...")` | `npm install -g react-icons react react-dom` |
| `pdftoppm` | `brew install poppler` (macOS) / `apt-get install -y poppler-utils` (Linux) |
| `soffice` | `brew install --cask libreoffice` (macOS) / `apt-get install -y libreoffice` (Linux) |
| Pillow / `from PIL import ...` | `pip3 install Pillow` |

After installing, re-run the original command. Only ask the user for help if installation itself fails.
