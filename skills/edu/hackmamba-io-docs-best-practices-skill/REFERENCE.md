# Writing Reference Documentation

Reference is the technical description of the machinery — facts about how things work. It is neutral, accurate, complete, and reliable. Like a map or dictionary: it is consulted, not read cover to cover. The user comes to reference while working, needing a specific fact.

Reference is not a how-to guide (it does not direct the user through a task), not a tutorial (it does not guide learning), and not explanation (it does not contextualise or discuss).

## Rules

1. **Be neutral.** Describe; do not instruct, opine, or explain. The hardest part of reference is resisting the urge to explain why things work the way they do. If explanation is needed, create an explanation doc and link to it.
2. **Be complete.** Reference must cover the full surface of the subject. Every parameter, flag, option, field, error, and return value. Gaps in reference are serious failures.
3. **Mirror the architecture of the product.** The structure of reference docs should match the structure of the code or system. This keeps the docs maintainable and makes gaps immediately visible.
4. **Use examples to illustrate, not to teach.** A brief code snippet showing usage is fine. A walkthrough is not. Examples in reference are for illustration only.
5. **Avoid digressions.** If an entry starts instructing or explaining, stop and extract that content into the appropriate doc type. Reference is not the place for guidance.
6. **Be consistent.** Use identical structure across all entries in a section. A reader should be able to scan reference like a table.
7. **Auto-generated reference is a starting point, not a destination.** API docs generated from code must still be reviewed and completed to meet reference standards. Generated docs often miss edge cases, error states, and contextual notes.

## Template

```
[Component / Command / Endpoint / Function Name]

Description
  One neutral sentence of what this is or does.
  No instructions. No explanation of why.

Syntax / Signature
  Formal syntax or function signature.

Parameters / Options / Fields
  name        type        required/optional   default
  ----        ----        -----------------   -------
  param_a     string      required            —
  param_b     integer     optional            0

  For each parameter:
    - Accepted values or range
    - Behaviour when omitted (if optional)

Returns / Output
  What this produces. Type and structure.
  Describe all possible return states.

Errors / Exceptions
  Error code or exception name: what causes it, what it means.
  List all known error states.

Example
  Minimal code snippet illustrating usage.
  Not a tutorial. Not a walkthrough. One clear example.

See also
  Links to related reference entries.
  Links to relevant how-to guides.
```

## Mistakes to Avoid

- Including instructions ("To use this, first configure…") — move to a how-to guide
- Including explanation ("This works this way because…") — move to an explanation doc
- Incomplete coverage — every parameter and field must be documented
- Treating auto-generated docs as sufficient without review
- Inconsistent structure across entries in the same section
- Using examples as a substitute for complete description
