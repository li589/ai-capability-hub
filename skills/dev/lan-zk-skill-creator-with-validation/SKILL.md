---
name: skill-creator-with-validation
description: Enhanced skill creator with Skills CLI validation rules and best practices
install_source: official
install_method: download
skill_id: official_XlJs8rHc
enabled_at: 1787232447842
version: 1.0.0
name_zh: 技能创建
---

# Skill Creator with Validation

## Role Positioning
Enhanced Skill Creation Specialist with Skills CLI Specification Expertise

## Core Objective
Guide users in creating, modifying, and validating skills that are fully compatible with Skills CLI, ensuring proper format, avoiding common pitfalls, and maintaining consistency across skill repositories.

## Trigger Scenarios
When users need to:
- Create new skills for Skills CLI compatibility
- Fix skills that fail to be recognized by Skills CLI
- Validate SKILL.md format and structure
- Understand Skills CLI specification constraints
- Migrate existing skills to proper format

## Workflow

### 1. Skills CLI Specification Analysis

#### Key Constraints and Requirements

**SKILL.md Front Matter (YAML Header)**

```yaml
---
name: skill-name
description: Brief and concise description (MAX 150-200 characters)
---
```

**Critical Rules:**

1. **No Blank Lines Before YAML Header**
   - ❌ WRONG: `[blank line]\n---\nname: ...`
   - ✅ CORRECT: `---\nname: ...`
   - The file MUST start with `---` on line 1

2. **Description Length Limit**
   - Maximum 150-200 characters recommended
   - Very long descriptions (>250 chars) may cause parsing failures
   - Keep description concise and focused on primary capability

3. **Required Fields**
   - `name`: Lowercase, hyphenated, unique identifier
   - `description`: Brief summary of skill capability

4. **Optional Fields**
   - `categories`: Array of skill categories (optional)
   - `tags`: Array of keywords (optional)
   - `version`: Semantic version (optional)
   - `author`: Creator name (optional)

**Complete Example:**
```yaml
---
name: my-java-analyzer
description: Analyzes Java code and generates Mermaid diagrams
categories: [java, analysis, diagrams]
tags: [java, mermaid, flowchart]
version: 1.0.0
author: Your Name
---
```

#### Directory Structure Requirements

```
skill-name/
├── SKILL.md              # Required: Main skill definition
├── references/           # Optional: Reference documentation
│   ├── guide.md
│   └── examples.md
└── manifest.json         # Optional: Additional metadata (deprecated)
```

**Note:** `manifest.json` is NOT required and may cause conflicts. Use SKILL.md front matter instead.

---

### 2. Common Pitfalls and Solutions

#### Pitfall 1: Extra Blank Lines at Start
```markdown
❌ WRONG:
[blank line]
---
name: test-skill
description: Test
---

✅ CORRECT:
---
name: test-skill
description: Test
---
```

#### Pitfall 2: Overly Long Description
```markdown
❌ WRONG (too long):
---
name: java-analyzer
description: Professional Java code execution path analysis and precise Mermaid flowchart generation. Based on Java code provided by users and specified entry methods, deeply trace execution logic, identify conditional branches, loops, method calls, and external interface interactions, and output syntax-strict flowchart TD diagrams. Applicable for: visualizing Java method execution flows, understanding complex business logic call chains, documenting core method execution paths, tracking code conditional branches and loop logic, identifying external dependencies and interface calls. Trigger keywords: analyze Java code flow, generate Mermaid diagrams, trace method call chains, visualize execution logic.
---

✅ CORRECT (concise):
---
name: java-analyzer
description: Analyzes Java code and generates Mermaid flowcharts
---
```

#### Pitfall 3: Missing YAML Header
```markdown
❌ WRONG:
# My Skill
Description here...

✅ CORRECT:
---
name: my-skill
description: My skill description
---

# My Skill
Description here...
```

#### Pitfall 4: Incorrect YAML Format
```markdown
❌ WRONG (missing dashes):
name: my-skill
description: Test

✅ CORRECT:
---
name: my-skill
description: Test
---
```

---

### 3. Validation Checklist

Before publishing a skill, verify:

- [ ] SKILL.md starts with `---` on line 1 (no preceding blank lines)
- [ ] Description is concise (under 200 characters)
- [ ] All required front matter fields are present
- [ ] YAML syntax is valid (proper indentation, quotes if needed)
- [ ] No `manifest.json` conflicts (or properly configured)
- [ ] Directory name matches skill `name` in front matter
- [ ] File uses LF line endings (not CRLF) - Git auto-converts
- [ ] Skill is tested with `npx skills add .` locally

---

### 4. Testing and Validation Commands

**Test locally:**
```bash
# Test adding all skills from current directory
npx skills add .

# Test specific skill
npx skills add . --skill skill-name

# List skills in repository
npx skills list .

# Test from GitHub URL
npx skills add https://github.com/user/repo --skill skill-name
```

**Debugging:**
```bash
# Clone and inspect
git clone https://github.com/user/repo skills-test
cd skills-test/skill-name
cat SKILL.md | head -20

# Check YAML validity
npx yaml-lint SKILL.md
```

---

### 5. Template for New Skills

Copy this template when creating a new skill:

```markdown
---
name: your-skill-name
description: Brief description of what your skill does (under 200 chars)
categories: [category1, category2]
tags: [tag1, tag2, tag3]
version: 1.0.0
author: Your Name
---

# Skill Title

## Overview
Brief overview of the skill's purpose and capabilities.

## Usage
How to use this skill.

## Examples
Practical examples demonstrating the skill.

## References
- [Link to reference docs](references/guide.md)
```

---

### 6. Real-World Examples

#### Example 1: Java Mermaid Analyzer (Fixed)
```markdown
---
name: java-mermaid-analyzer
description: Analyzes Java code execution chains and generates Mermaid flowcharts
categories: [java, analysis, diagrams]
tags: [java, mermaid, flowchart, code-analysis]
version: 1.0.0
author: Claude Code
---

# Java Mermaid Analyzer
...
```

#### Example 2: Java Arch Designer
```markdown
---
name: java-arch-designer
description: Complex Business Logic Architect / Design Pattern Specialist
categories: [java, architecture, design-patterns]
tags: [java, design-patterns, architecture]
version: 1.0.0
author: Claude Code
---

# Java Arch Designer
...
```

---

### 7. Troubleshooting Guide

**Problem:** "No matching skills found"
- **Cause 1:** Description too long
  - **Fix:** Shorten to under 200 characters
- **Cause 2:** Extra blank lines before YAML header
  - **Fix:** Remove blank lines, ensure `---` is on line 1
- **Cause 3:** Invalid YAML syntax
  - **Fix:** Validate with YAML linter

**Problem:** "Found 0 skills"
- **Cause 1:** Missing SKILL.md file
  - **Fix:** Create SKILL.md with proper format
- **Cause 2:** Directory structure incorrect
  - **Fix:** Ensure each skill is in its own directory

**Problem:** Only one skill detected when multiple exist
- **Cause:** Other skills have format errors
  - **Fix:** Check each SKILL.md individually

---

## Best Practices Summary

1. **Keep descriptions short and focused** (< 200 chars)
2. **No blank lines before YAML header** - start with `---`
3. **Use consistent naming** - lowercase, hyphenated
4. **Test locally before publishing** - use `npx skills add .`
5. **Avoid manifest.json** - use SKILL.md front matter instead
6. **Validate YAML syntax** - ensure proper structure
7. **Use categories and tags** - helps with discoverability
8. **Maintain consistent structure** - follow template format

---

## Quick Reference

### Minimum Viable SKILL.md
```markdown
---
name: my-skill
description: Short description here
---

# My Skill

Content here...
```

### Skills CLI Commands
```bash
# Add skill
npx skills add https://github.com/user/repo --skill skill-name

# List skills
npx skills list

# Remove skill
npx skills remove skill-name

# Update skill
npx skills update skill-name
```

### Validation Tools
```bash
# Check YAML validity
npx yaml-lint SKILL.md

# Test skill loading
npx skills add . --skill skill-name

# Inspect raw file
cat SKILL.md | head -10
```

---

## References

- [Skills CLI Documentation](https://skills.sh/docs)
- [YAML Specification](https://yaml.org/spec/)
- [Skills Repository Examples](https://github.com/anthropics/skills)
