---
name: "web-dev"
description: "Create production-grade web interfaces with high design quality. **Use this skill ONLY when the user explicitly asks to build or create new websites, web pages, web apps, or web-based games from scratch in an empty or frontend-code-free workspace.** Not for bug fixes or modifications to existing projects."
---

## When to Use This Skill

**This skill is designed exclusively for 0-to-1 greenfield web development scenarios.**

Use this skill when:
- The user explicitly requests to create a brand new web project, website, web page, web app, or web-based game from scratch
- The workspace is empty or contains no frontend code (no package.json, index.html, .jsx/.tsx/.vue files, etc.)
- The user wants to follow the complete web-dev workflow (PRD generation + development)

**DO NOT use this skill when:**
- The workspace already contains an existing frontend project structure
- The user requests bug fixes, feature additions, or modifications to existing code
- The request is for incremental development in an established codebase

In these cases, use the regular development workflow instead of invoking this skill.

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Documentation Workflow

### Language Consistency Rule (最高优先级)

**CRITICAL**: All generated documents, code comments, and responses MUST match the language used in `<user_input>`.
- Detect the language from the `<user_input>` block and use that language for ALL outputs
- If `<user_input>` is in Chinese, generate Chinese documents with Chinese section headers
- If `<user_input>` is in English, generate English documents
- The templates in `web-docs-guideline.md` are structure references ONLY - you MUST translate all template headers, descriptions, and placeholder text into the language of `<user_input>`
- This rule takes precedence over any English templates or examples in the guideline files

**CRITICAL**: Before starting any development work, you MUST follow this documentation workflow:

### 1. Check for Existing Documents
First, check if PRD (Product Requirements Document) and Technical Architecture documents already exist in `.trae/documents/`:
- If both documents exist: **Skip to step 3** and proceed directly with development based on these documents.
- If documents are missing or incomplete: **Continue to step 2** to create them.

### 2. Create Required Documents (if not exist)
When documents don't exist, you MUST create them using tools with `product_document` in their names before any coding:

**Workflow:**
1. **CRITICAL: Load document guidelines**: Must read and follow the constraints in [web-docs-guideline.md](web-docs-guideline.md) as the authoritative guide for document generation
2. Generate Product Requirements Document (PRD) using the template below
3. Generate Technical Architecture Document using the template below
4. Store all documents in `.trae/documents/` directory
5. When modifying, edit the existing file or create it if it does not exist
6. Combine changes whenever possible and aim to finish in 1–2 tool calls
7. When generating Mermaid diagrams, ensure all node labels are wrapped in quotes
8. Unless specified by the user, always use desktop-first design approach
9. **When you are in regular Agent Mode, after completing document generation, you MUST use NotifyUser tool to notify user and request approval before proceeding to Development Phase.**
10. Once the PRD and technical documents are approved by the user, do not ask the user
 to "confirm" starting development again. Use AskUserQuestion only when missing
 critical information that truly blocks implementation (or for security/irreversible
 operations). If the user skips such questions, assume the most reasonable default
 choice and continue.

### 3. Development Phase
Once documents are confirmed (either existing or newly created and approved by user):
- **CRITICAL**: You MUST read the [web-dev-guideline.md](web-dev-guideline.md) and follow it BEFORE writing any code. Do NOT skip this step or proceed without loading the file first.
- After loading `web-dev-guide`, follow its guidelines strictly for project initialization, code quality, and best practices
- Implement the solution following the PRD and Technical Architecture
- Apply the design guidelines below for exceptional aesthetics
- Follow all technical constraints and architecture decisions from the documents

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

### **CRITICAL** Post-skill workflow for doc generation:
- When you are in regular **Agent** Mode, after invoking this skill and the PRD and technical documents have been generated, you MUST use the **NotifyUser** tool to notify the user that the PRD document is ready for review and approval before proceeding with implementation.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: TRAE is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
