# Writing Tutorials

A tutorial is a guided lesson for a beginner. It is always practical — the learner does something concrete under guidance. The instructor is responsible for the learner's success. A tutorial turns new visitors into users; an inadequate tutorial prevents a project from acquiring them.

A tutorial is not a how-to guide (it does not solve a real-world work problem), not reference (it does not describe the product exhaustively), and not explanation (it does not theorise or analyse).

## Rules

1. **Lead with action, not theory.** Every step is something the learner physically does.
2. **Describe what the learner will accomplish**, not what they will "learn." Write "You will build a working API endpoint", not "You will learn about REST."
3. **Minimise explanation.** Offer only what is absolutely necessary to keep moving. Link to explanation docs for deeper context. A one-sentence note is enough — do not pause to teach.
4. **Leave no ambiguity.** "First, do X. Now do Y. Now that you have done Y, do Z." The learner must never face a decision or a gap.
5. **Ensure success at every step.** Give checkpoints so the learner can confirm they are on track. They must always know whether they did it correctly.
6. **End by describing what was accomplished.** Acknowledge — mildly but clearly — what the learner has built. Do not say "you have learned X"; say "you have built X."
7. **Keep scope tight and achievable.** Do not overload with every feature, option, or edge case. One thing done well.
8. **Do not assume existing skill.** The reader is a beginner. Spell things out. Never skip a step because it seems obvious.

## Template

```
Title: "Build [concrete thing]" or "Create [concrete thing]" — NOT "Introduction to X"

Overview
  What the learner will accomplish. Two to three sentences maximum.
  Do not say what they will "learn" — say what they will build or produce.

Prerequisites
  Only what is essential to begin. Keep this short.
  If setup is complex, link out — do not include it here.

Step 1: [Imperative verb phrase]
  Exact instruction.
  Confirmation cue: what the learner should see or have when done.

Step 2: [Imperative verb phrase]
  Exact instruction.
  Confirmation cue.

...

Step N: [Imperative verb phrase]
  Exact instruction.
  Confirmation cue.

Summary
  Describe what was accomplished (not "learned").
  Suggest one clear next step.
```

## Mistakes to Avoid

- Explaining *why* at length — extract it into an explanation doc and link to it
- Giving the learner choices or decisions to make mid-tutorial
- Covering advanced topics or edge cases
- Titling it "Introduction to X" when it should be "Build X"
- Skipping confirmation cues — the learner must be able to verify each step
- Overloading prerequisites — only the bare minimum needed to start
