---
name: documentation
description: Write, review, classify, and improve technical documentation. Use when the user asks to write docs, create a tutorial, write a how-to guide, write a getting started guide, document a function or API, explain a concept, review or audit existing documentation, or improve unclear or mixed-content docs.
install_source: official
install_method: download
skill_id: official_RirsUON0
enabled_at: 1787230917654
version: 1.0.0
name_zh: 文档写作
---

# Documentation Skill

Technical documentation serves four distinct user needs. Each need requires a different kind of writing. Mixing types is the most common cause of poor documentation.

## The Four Types

| Type | User State | Content Kind | User Need |
|---|---|---|---|
| Tutorial | Learning | Action | "Help me learn by doing" |
| How-to Guide | Working | Action | "Help me accomplish this task" |
| Reference | Working | Knowledge | "Give me the facts I need" |
| Explanation | Learning | Knowledge | "Help me understand why" |

## Classify Before You Write

Ask these two questions:

1. Is the user **learning** or **working**?
2. Is the content **action-based** or **knowledge-based**?

Cross the answers:
- Learning + Action = **Tutorial**
- Learning + Knowledge = **Explanation**
- Working + Action = **How-to Guide**
- Working + Knowledge = **Reference**

If the content spans more than one quadrant, split it into separate documents and cross-link them.

## Quick Rules Per Type

**Tutorial** — beginner, learning by doing. Lead with action. No choices for the learner. Minimal explanation (link out). End by describing what was accomplished. See [TUTORIALS.md](TUTORIALS.md) for full rules and template.

**How-to Guide** — competent user, completing a real task. Title with "How to [task]". Write from the user's goal, not the product's features. Strip explanation — link to it. See [HOWTO.md](HOWTO.md) for full rules and template.

**Reference** — user consulting facts while working. Neutral description only. Mirror the product's architecture. No instructions, no explanation. See [REFERENCE.md](REFERENCE.md) for full rules and template.

**Explanation** — user wants to understand why. Answer design decisions, tradeoffs, history. Draw connections. No step-by-step instructions. See [EXPLANATION.md](EXPLANATION.md) for full rules and template.

## The Most Common Failures

- **Tutorial/how-to conflation**: A tutorial that assumes skill, or a guide that teaches from scratch. Fix: ask "is this user learning or working?"
- **Explanation inside a tutorial**: Pausing to discuss why things work. Fix: extract to an explanation doc, replace with one sentence and a link.
- **Instructional reference**: API docs that say "To use this, first configure…". Fix: move instructions to a how-to guide.
- **Feature-titled how-to guides**: "Database Settings" instead of "How to configure a read replica". Fix: rewrite titles as user tasks.
- **Incomplete reference**: Undocumented parameters or fields. Fix: audit reference against the product surface.

## Iterative Improvement Workflow

Do not restructure everything at once. Instead:

1. Choose any single piece of documentation.
2. Assess: what type should this be? Does it serve that purpose? Who is the reader?
3. Decide on one specific improvement.
4. Make that change and consider it complete.
5. Repeat.

Structure should emerge from improvement, not be imposed from above.

## Style at a Glance

| | Tutorial | How-to Guide | Reference | Explanation |
|---|---|---|---|---|
| Voice | Warm, guiding | Direct, efficient | Neutral, impersonal | Conversational |
| Person | Second ("you will…") | Second ("do X") | Third ("returns…") | Any |
| Instructions | Yes — they are the doc | Yes — they are the doc | No | No |
| Explanation | Minimal, link out | None | None | Yes — it's the point |
| Tone | Patient | Crisp | Authoritative | Curious |
