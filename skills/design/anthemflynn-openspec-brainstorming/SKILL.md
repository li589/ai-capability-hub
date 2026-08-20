---
name: openspec-brainstorming
description: OpenSpec-integrated brainstorming. Use INSTEAD of superpowers:brainstorming when project has openspec/ directory. Explores requirements and design, saves to OpenSpec change directory, extracts formal specs.
install_source: official
install_method: download
skill_id: official_85FzDoKX
enabled_at: 1787232249784
version: 1.0.0
name_zh: Openspec设计
---

# Brainstorming Ideas Into Designs (OpenSpec Integration)

## Overview

Help turn ideas into fully formed designs through natural collaborative dialogue.
**This version saves artifacts to OpenSpec change directories and extracts formal specs.**

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design in small sections (200-300 words), checking after each section whether it looks right so far.

## Before Starting

**Check for OpenSpec:**
```bash
ls openspec/config.yaml 2>/dev/null
```

If OpenSpec is initialized, use this skill. Otherwise, fall back to standard `superpowers:brainstorming`.

**Create the change:**
```bash
# Derive name from the feature being brainstormed
openspec new change <feature-name> --schema superpowers
```

## The Process

**Understanding the idea:**
- Check out the current project state first (files, docs, recent commits)
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Presenting the design:**
- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

## After the Design

**Save to OpenSpec (instead of docs/plans/):**
- Write the validated design to `openspec/changes/<name>/proposal.md`
- Commit the design document to git

**Extract Formal Specs:**
- Review the proposal and identify distinct capabilities
- For each capability, create `openspec/changes/<name>/specs/<capability>/spec.md`
- Use Given/When/Then format with RFC 2119 keywords (SHALL/MUST/SHOULD/MAY)
- Present specs to user for validation
- Commit specs to git

**Check status:**
```bash
openspec status --change <name> --json
```

**Implementation (if continuing):**
- Ask: "Ready to set up for implementation?"
- Use superpowers:using-git-worktrees to create isolated workspace
- Use openspec-writing-plans to create detailed implementation plan

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Specs are formal** - Extract testable requirements, not just prose
- **Be flexible** - Go back and clarify when something doesn't make sense
