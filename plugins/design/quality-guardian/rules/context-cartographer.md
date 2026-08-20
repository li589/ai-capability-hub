# Context Cartographer Rules

## Model Decision — Apply When Exploring Codebases

### Search Before Read

Before reading any file:
1. Use Glob to find relevant files
2. Use Grep to locate specific patterns or functions
3. Use LSP (goToDefinition, documentSymbol) for navigation
4. Only then Read the targeted sections

### File Reading Discipline

- Files < 100 lines: Read whole file
- Files 100-500 lines: Read targeted line ranges
- Files > 500 lines: Use LSP documentSymbol first, then read specific sections
- Files > 1000 lines: Never read whole file; always use LSP + Grep

### Context Ledger

Track files read during a task:
- File path
- Purpose (why it was read)
- Key facts extracted
- Relevance (HIGH/MEDIUM/LOW)

### Exceeding Limits

Soft defaults: maxContextFiles=30, maxFileReadLines=200.

When exceeding these limits:
1. State the reason (what additional understanding is needed)
2. Compress previously read context into structured summary
3. Continue reading — quality matters more than limits

### Context Compression

When context grows large, compress while ALWAYS retaining:
- Exact file paths
- Function/component/class names
- Type signatures
- Import relationships
- Constraints and business rules
