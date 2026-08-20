# Writing How-to Guides

A how-to guide provides directions for solving a specific, real-world problem. It is written for a user who already has baseline competence. It is defined by the user's goal, not by the product's features. Like a recipe: a professional chef may follow a recipe to ensure correctness — it serves work, not study.

A how-to guide is not a tutorial (it does not teach from scratch), not reference (it does not exhaustively describe machinery), and not explanation (it does not discuss or theorise).

## Rules

1. **Title with a verb phrase that names the task exactly.** "How to configure TLS certificates" — not "TLS certificates", not "Configuring certificates." The title should tell the user immediately whether this guide solves their problem.
2. **Write from the user's perspective, not the product's.** The guide answers a human need. It is not a tour of features. Every how-to guide should correspond to something a real person needs to get done.
3. **Assume competence.** Do not explain basics. The reader is already working in this domain. Do not explain what a file system is, what an environment variable does, or other fundamentals.
4. **Allow for non-linearity.** Real tasks sometimes branch. Steps may have conditions: "If using X, do Y instead." A how-to guide is not always a linear list.
5. **Stay focused.** Do not include every possible option. Refer readers to reference docs for full details. A how-to guide is about achieving the goal, not surveying the landscape.
6. **Use conditional imperatives.** "If you want X, do Y. To achieve W, do Z."
7. **Do not teach while guiding.** Strip explanatory passages. If something needs explaining, move it to an explanation doc and link to it with one sentence.

## Template

```
Title: "How to [accomplish specific goal]"

Overview
  One to two sentences describing the problem or task this guide solves.
  What will the user be able to do when done?

Prerequisites
  What the user needs before starting: tools, access, prior configuration.
  Do not explain these things — just list them. Link to setup guides if needed.

Steps

  1. [Imperative instruction]
  2. [Imperative instruction]
  [Condition: If X applies, do Y instead of step 3]
  3. [Imperative instruction]
  N. [Final step]

Result
  What a successful outcome looks like. How does the user know it worked?

Related
  Links to relevant reference documentation.
  Links to related how-to guides.
```

## Mistakes to Avoid

- Teaching from scratch — that is a tutorial's job
- Explaining every option instead of the one needed for the task
- Titling by product feature rather than user goal ("Database Settings" vs "How to configure a read replica")
- Treating it as a linear procedure when the task requires conditional logic
- Padding with background knowledge the competent user already has
- Including inline explanation — extract it, link to it
