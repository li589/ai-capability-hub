---
name: project-knowledge
description: Load project architecture and structure knowledge. Use when you need to understand how this project is organized.
allowed-tools: Read
install_source: official
install_method: download
skill_id: official_9rVNWESO
enabled_at: 1787232415036
version: 1.0.0
name_zh: 项目开发
---

# Project Knowledge Skill

Understanding project architecture and structure.

## When to Load This Skill

- Starting work on this project
- Making architectural decisions
- Understanding how components connect

## Knowledge Files

Load these as needed:

### Architecture
@memory/knowledge/codebase/architecture.json

### Conventions
@memory/knowledge/codebase/conventions.json

### Patterns
@memory/knowledge/codebase/patterns.json

### Gotchas
@memory/knowledge/codebase/gotchas.json

## How to Use

1. Read the relevant knowledge file for your task
2. Follow patterns and conventions described
3. Update knowledge if you discover new information

## Updating Knowledge

When you discover something new:
```json
{"knowledge_updates":[{"category":"codebase","content":"Discovery description","confidence":"certain|likely|uncertain"}]}
```

These updates are merged after task completion.
