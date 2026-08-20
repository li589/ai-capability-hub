# io-and-convert · Input Parsing, Fidelity Conversion, Prototype ↔ Doc

Covers two kinds of needs: **(A) diverse inputs as the generation basis** (URL / screenshot / existing html / PRD·md), and **(B) fidelity and format conversion** (high ↔ low fidelity, device mockup, prototype ↔ PRD/dev doc).

## A. Input Parsing (reference intent)

First turn the input into "design language + content structure," write it into the design contract, then follow the normal generation flow. **Don't copy verbatim — distill it into a system.**

| Input | Handling |
|---|---|
| **Reference URL** | Use the base capability to fetch page content/structure; distill its information architecture, colors, layout language → write into the contract. Aim for "same vibe" rather than pixel-perfect copy (unless the user explicitly asks for 1:1 restoration). |
| **Screenshot / image** | Read the image, extract colors, layout, component style, brand tone → build tokens and component spec. |
| **Existing HTML prototype** | Read the source, reuse its tokens/components/interaction conventions; extend or modify on top, keeping consistency (see multipage-system iterate). |
| **PRD / md / word doc** | Parse features and information architecture → produce a page list and mock schema → then implement the prototype. |
| **Multiple files / folder** | First read all relevant files and their linked content, work out features and data model, then start. |

Key: read the real content in full before planning (for long docs / many files, don't act on just the opening); 1:1 restoration needs a screen-by-screen check of layout and main elements.

## B. Fidelity & Format Conversion (convert intent, single-step, not the multi-page pipeline)

| Conversion | Approach |
|---|---|
| **High → low fidelity** | Remove real copy/images/brand color, keep the layout skeleton and icon shapes; express structure with grayscale blocks, placeholders, wireframe style ("icons/shapes only, no text"). |
| **Low → high fidelity** | Per design-spec, add tokens, real copy, component states, interactions, and mock. |
| **Device mockup** | Composite a high-fidelity page screenshot/image onto a given device frame (phone/browser); use the base image capability, output to `assets/`. |
| **Prototype → PRD** | Reverse-engineer from the prototype: product positioning, feature list, page flows, field descriptions, interaction notes; output in the user's requested format (html/word/md), reusing html-report / docx for long docs. |
| **Prototype / mockup → dev doc** | Reverse-engineer: feature modules, front/back-end API contracts (based on the stub shapes), data model, page-to-API mapping; write the backend part in a "to-be-implemented" tone, noting the current prototype is mock. |

## C. Integration with Document Deliverables

- When a formal **long doc/report** is needed (PRD, dev doc, requirement analysis), content planning belongs to this skill, but **rendering/layout reuses `html-report` (HTML) or `docx` (when the user wants Word)** — don't rebuild document layout inside this skill.
- Composite needs like "first show a demo as HTML, and also give a doc": produce the interactive HTML prototype first (this skill's main line), then generate the doc from the prototype (switch to the doc capability in C).
