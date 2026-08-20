# Marketing Image Contract

## Brand extraction

Extract logo, brand colors, fonts, product/packaging appearance, image style, prohibited uses, and existing slogans from supplied materials. Do not redraw or distort a logo. Do not invent packaging that could be mistaken for the real product.

## Temporary visual system

When brand assets are absent, propose one temporary system for user confirmation: primary, secondary, accent, background, Chinese font, image mood, and contrast rules. Keep it consistent across report and images. Default to a restrained consulting-style system rather than red-gold income hype.

## Report cover

- Canvas: A4 portrait at 2480×3508 PNG.
- Content: project name, strategic theme, company/brand, date, logo when supplied.
- No QR code and no earnings claim.

## Distributor recruitment poster

- Canvas: 1080×1440 PNG.
- Content: product value, suitable partner, direct-sales cooperation, training/support, process, disclaimer, QR image or labeled placeholder.
- Exclude internal cost, margin, total budget, guaranteed income, and recruitment/downline language.

## Social square

- Canvas: 1080×1080 PNG.
- Content: one verified hook, one product benefit, one restrained action, disclaimer, and optional QR.
- Keep text short enough for mobile reading.

## AI visual brief

Use the built-in image generation capability for a text-free visual only. Provide asset type, audience, approved product/brand references, scene, subject, style, composition, lighting, palette, negative constraints, and planned text-safe area. Explicitly request no words, numbers, logos, QR codes, watermarks, fabricated product packaging, or earnings imagery.

## Deterministic Chinese typography

Compose exact Chinese copy, logo, disclaimer, and QR area with `scripts/compose_marketing_poster.py`. Preserve text verbatim in the layout manifest. If no QR is supplied, draw a labeled placeholder; never fabricate a working QR code.

## Visual QA

Open every image at full resolution and verify exact Chinese text, no clipping, legible hierarchy, sufficient contrast, correct logo proportions, truthful product appearance, consistent brand system, safe external data, disclaimer presence, and absence of `躺赚`, `保证收益`, `拉人头`, `月入过万`, or similar claims.
