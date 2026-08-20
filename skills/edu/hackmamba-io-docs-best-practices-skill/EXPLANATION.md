# Writing Explanation Documentation

Explanation is discussion that clarifies and illuminates a topic. It is contextual, conceptual, and theoretical. It is free to explore history, design decisions, tradeoffs, alternatives, and implications. It is written for a user at study — one who wants to understand, not one who is trying to complete a task right now.

Explanation is not a tutorial (it does not guide doing), not a how-to guide (it does not solve a specific task), and not reference (it is not a factual inventory of the product surface).

## Rules

1. **Answer "why" questions.** What were the design decisions? What are the tradeoffs? Why does the system work this way and not some other way? Explanation exists to answer the questions that reference and how-to guides deliberately leave unanswered.
2. **Draw connections.** Connect this concept to related concepts, to the broader domain, to other systems. Weave a web of understanding. Explanation is allowed — encouraged — to range wider than the immediate topic.
3. **Bring in context freely.** Examples, analogies, comparisons, historical background, alternative perspectives — use whatever aids understanding. Explanation has the most latitude of all four types.
4. **Define a reasonable scope.** Unlike reference (bounded by the product surface) or how-to guides (bounded by the task), explanation has no natural edges. Use a real or imagined "why" question as your prompt, then draw a deliberate boundary and hold it.
5. **Do not instruct.** Explanation is not the place for step-by-step directions. If you find yourself writing steps, you are writing a how-to guide, not explanation.
6. **Write for the curious reader.** Not someone trying to complete a task right now. Someone who has a moment to think, who wants to move from working familiarity with something to genuine understanding of it.
7. **Link out.** Link to relevant reference entries when describing how things work. Link to related how-to guides when the reader may want to act on what they have understood.

## Template

```
Title: "[Topic] explained"
   or: "Understanding [concept]"
   or: "Why [X works the way it does]"
   or: "How [X] works"

Introduction
  Frame the question or questions this explanation answers.
  What will the reader understand by the end?
  One to three sentences.

[Section: Background or context]
  History, origins, or the problem this thing was designed to solve.
  Why does this exist at all?

[Section: How it works, conceptually]
  The core model or idea.
  Use analogies where helpful.
  Do not instruct — describe.

[Section: Design decisions and tradeoffs]
  Why it was built this way.
  What alternatives were considered and why they were not chosen.
  What the current approach optimises for, and what it sacrifices.

[Section: Implications and related concepts]
  What does understanding this unlock?
  How does it connect to other parts of the system or domain?
  What should the reader be aware of as a consequence?

Further reading
  Links to related explanation docs.
  Links to reference entries for the technical details.
  Links to how-to guides for acting on this understanding.
```

## Mistakes to Avoid

- Including step-by-step instructions — those belong in how-to or tutorial docs
- Writing exhaustive technical specs — that is reference
- Being so abstract or general that no concrete understanding is produced — anchor to examples
- Letting scope expand indefinitely — draw a boundary and hold it
- Burying explanation inside tutorials or how-to guides — extract it and link to it
- Repeating information available in reference — link to it instead
