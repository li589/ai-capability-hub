# Skills CLI Specification Reference

## 1. SKILL.md File Format

### Required Structure

Every skill MUST have a `SKILL.md` file with the following structure:

```markdown
---
name: skill-name
description: Skill description (concise, <200 chars)
---
[Content]
```

### Front Matter (YAML Header) Requirements

#### Required Fields
- `name`: Unique identifier for the skill
  - Format: lowercase, hyphenated (e.g., `java-analyzer`)
  - Must match directory name
- `description`: Brief summary of skill's purpose
  - Recommended: 50-200 characters
  - Maximum: Avoid >250 characters (may cause parsing issues)

#### Optional Fields
- `categories`: Array of skill categories
  ```yaml
  categories: [java, analysis, diagrams]
  ```
- `tags`: Array of keywords for discoverability
  ```yaml
  tags: [java, mermaid, flowchart, analysis]
  ```
- `version`: Semantic version number
  ```yaml
  version: 1.0.0
  ```
- `author`: Creator's name
  ```yaml
  author: Jane Doe
  ```
- `license`: License identifier (SPDX format)
  ```yaml
  license: MIT
  ```

### Formatting Rules

1. **No Blank Lines Before YAML Header**
   ```markdown
   ❌ WRONG:
   [blank line]
   ---
   name: test

   ✅ CORRECT:
   ---
   name: test
   ```

2. **YAML Header Must Be Enclosed in Triple Dashes**
   ```markdown
   ❌ WRONG:
   name: test
   description: test

   ✅ CORRECT:
   ---
   name: test
   description: test
   ---
   ```

3. **Description Length**
   ```markdown
   ❌ TOO LONG:
   description: Very long description that goes on and on describing the skill in excessive detail, which might cause parsing failures in Skills CLI because it's way too verbose and unnecessary for a simple description field

   ✅ APPROPRIATE:
   description: Analyzes Java code and generates Mermaid diagrams
   ```

4. **Line Endings**
   - Use LF (Unix-style) line endings
   - Git will auto-convert CRLF to LF on commit if configured properly

## 2. Directory Structure

```
skill-name/
├── SKILL.md              # REQUIRED: Main skill definition
├── references/           # OPTIONAL: Reference docs
│   ├── examples.md
│   └── guide.md
└── manifest.json         # DEPRECATED: Avoid using
```

### Directory Naming
- Must match the `name` field in SKILL.md front matter
- Use lowercase and hyphens
- Example: `java-analyzer/` with `name: java-analyzer`

## 3. Content Guidelines

### Main Content Section
After the YAML header, include:
- Skill overview and purpose
- Usage instructions
- Examples and use cases
- Reference links (to files in `references/` directory)
- Troubleshooting tips

### Example Structure
```markdown
---
name: example-skill
description: Example skill for demonstration
---

# Skill Title

## Overview
Brief description of what the skill does.

## Usage
How to use this skill.

## Examples
```code
example code
```

## References
- [Detailed Guide](references/guide.md)
- [Examples](references/examples.md)
```

## 4. Validation Checklist

Before publishing, ensure:

- [ ] SKILL.md exists in skill directory
- [ ] YAML header is present and valid
- [ ] No blank lines before `---`
- [ ] Description is concise (<200 chars)
- [ ] Directory name matches `name` field
- [ ] Required fields (`name`, `description`) are present
- [ ] YAML syntax is valid (use YAML linter)
- [ ] Tested with `npx skills add .`
- [ ] Line endings are LF (not CRLF)

## 5. Common Errors and Fixes

### Error: "No matching skills found"
**Causes:**
- Description too long (>250 chars)
- Extra blank lines before YAML header
- Missing YAML header entirely
- Invalid YAML syntax

**Solutions:**
```markdown
# If description too long:
description: Short, focused description

# If blank lines present:
# Remove them - file must start with ---

# If YAML invalid:
# Use online YAML validator or:
npx yaml-lint SKILL.md
```

### Error: "Found 0 skills"
**Causes:**
- SKILL.md file missing
- Incorrect directory structure
- All SKILL.md files have format errors

**Solutions:**
- Verify SKILL.md exists in each skill directory
- Check directory structure matches specification
- Validate each SKILL.md individually

### Error: Only some skills detected
**Causes:**
- Some SKILL.md files have errors
- Skills CLI stops parsing after first error

**Solutions:**
- Test each skill directory individually
- Fix formatting errors in problem files
- Use the validation checklist for each skill

## 6. Testing Guide

### Local Testing
```bash
# Test adding all skills from current directory
npx skills add .

# Test specific skill
npx skills add . --skill skill-name

# Use force flag to overwrite
npx skills add . --skill skill-name --force

# Test without prompts
npx skills add . --skill skill-name --yes
```

### Remote Testing
```bash
# Test from GitHub repository
npx skills add https://github.com/user/repo

# Test specific skill from repository
npx skills add https://github.com/user/repo --skill skill-name
```

### Debugging
```bash
# Clone and inspect
git clone https://github.com/user/repo test-skills
cd test-skills/skill-name

# Check SKILL.md format
cat SKILL.md | head -10

# Validate YAML
npx yaml-lint SKILL.md

# Test loading
npx skills add . --skill skill-name
```

## 7. Advanced Configuration

### Using Categories
Categorize your skill for better organization:
```yaml
categories: [programming, java, analysis]
```
Common categories: `programming`, `documentation`, `testing`, `analysis`, `visualization`

### Using Tags
Add keywords for discoverability:
```yaml
tags: [java, mermaid, flowchart, diagrams, code-analysis]
```

### Versioning
Follow semantic versioning:
```yaml
version: 1.2.3  # major.minor.patch
```

### Author and License
```yaml
author: John Doe
license: MIT
```

## 8. File Naming Conventions

- **Directory**: `skill-name` (lowercase, hyphens)
- **Main file**: `SKILL.md` (uppercase, .md extension)
- **References**: Place in `references/` subdirectory
- **Additional docs**: Use descriptive names in `references/`

## 9. Examples of Valid SKILL.md

### Minimal Example
```markdown
---
name: hello-world
description: Simple hello world skill
---

# Hello World Skill

Says hello!
```

### Complete Example
```markdown
---
name: java-mermaid-analyzer
description: Analyzes Java code and generates Mermaid flowcharts
categories: [java, analysis, diagrams]
tags: [java, mermaid, flowchart, code-analysis]
version: 1.0.0
author: Claude Code
license: MIT
---

# Java Mermaid Analyzer

Analyzes Java code execution chains and generates precise Mermaid diagrams.

## Features
- Trace method execution paths
- Identify branches and loops
- Generate flowchart TD diagrams
- Handle external calls

## Usage

[Usage instructions here]

## References
- [Examples](references/examples.md)
- [Mermaid Syntax](references/mermaid-syntax.md)
```

## 10. Migration Guide

### From manifest.json to SKILL.md

If you have a `manifest.json`:

1. **Extract metadata to SKILL.md front matter:**
   ```json
   // manifest.json
   {
     "name": "my-skill",
     "description": "My skill",
     "version": "1.0.0"
   }
   ```

2. **Convert to YAML front matter:**
   ```markdown
   ---
   name: my-skill
   description: My skill
   version: 1.0.0
   ---
   ```

3. **Remove manifest.json** (optional but recommended to avoid conflicts)

## 11. Best Practices

1. **Keep it simple**: Short descriptions, clear purpose
2. **Be consistent**: Follow the same format across all skills
3. **Test early**: Validate with Skills CLI before publishing
4. **Document well**: Include examples and usage instructions
5. **Use categories/tags**: Helps with discoverability
6. **Version properly**: Follow semantic versioning
7. **Avoid duplication**: Don't use both manifest.json and front matter
8. **Maintain structure**: Keep references organized

## 12. Resources

- [Skills CLI Documentation](https://skills.sh/docs)
- [YAML Specification](https://yaml.org/spec/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Skills Repository](https://github.com/anthropics/skills)
