# Design Council

> A Claude Code skill that summons 3 design legends to wage total war over your UI — and from the wreckage, produce an actionable design PRD.

---

## What it does

**Design Council** convenes a panel of 3 legendary designers who analyze your project, fight each other viciously over the right approach, and produce a complete UI/UX Design PRD as a Markdown file in your project.

The council members are:

| Expert | Role | Obsession |
|---|---|---|
| 🧠 **Don Norman** | The Cognitive Scientist | Usability, mental models, affordances |
| 🎨 **Jony Ive** | The Minimalist Aesthete | Beauty, simplicity, emotional design |
| 💥 **Steve Jobs** | The Ruthless Visionary | Radical simplification, product intuition |

Their disagreements are the engine:
- **Norman vs Jobs** — Scientific rigor vs "I know it because I feel it"
- **Ive vs Norman** — Aesthetic purity vs cognitive comprehension
- **Jobs vs Ive** — Rare but explosive disagreements on vision vs execution

They interrupt each other, misquote each other on purpose, form alliances and break them, and have hidden agendas that surface during the debate. The best ideas emerge from the war.

---

## How it works

The skill runs in 4 phases:

1. **Analysis** — Each expert independently reviews your project (reads actual code, README, components)
2. **War** — Thematic rounds covering navigation, layout, interaction, and components. They fight until genuine consensus or maximum 5 rounds
3. **Verdict** — Each expert declares their conclusion and what they had to swallow to get there
4. **PRD** — A complete `DESIGN-COUNCIL-PRD.md` file is saved to your project root

---

## Installation

### Claude Code — project only
```bash
cp -r design-council/ .claude/skills/design-council/
```

### Claude Code — global (all projects)
```bash
cp -r design-council/ ~/.claude/skills/design-council/
```

### skills.sh
```bash
npx skills add ericrisco/design-council
```

---

## Usage

Once installed, trigger the skill with any design-related request:

```
Review the UI of my app and tell me how to improve it
```
```
I need a UI/UX plan for this project
```
```
Do a design review of my repository
```
```
Analyze the interface design and give me a complete design PRD
```

The skill will read your project files, run the full debate, and produce `DESIGN-COUNCIL-PRD.md` in your project root.

---

## Output

The generated `DESIGN-COUNCIL-PRD.md` includes:

- Executive summary
- Project analysis and target audience
- Design principles (specific to your project)
- Information architecture and navigation
- Visual design (palette, typography, grid)
- Key components and design system recommendations
- User flows (happy path, secondary, error states)
- Technical recommendations (framework, responsive, WCAG, performance)
- Council disagreements as A/B options
- Prioritized next steps

---

## Project structure

```
design-council/
├── SKILL.md                    # Main skill file (instructions for Claude)
├── references/
│   └── expert-profiles.md      # Full personality profiles for each expert
├── README.md
└── LICENSE
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
