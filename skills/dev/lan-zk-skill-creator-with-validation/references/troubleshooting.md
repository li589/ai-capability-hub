# Troubleshooting Common Skills CLI Issues

## Problem 1: "No matching skills found for: skill-name"

### Symptom
```
npx skills add https://github.com/user/repo --skill my-skill

x  No matching skills found for: my-skill

•  Available skills:
   - other-skill
```

### Causes and Solutions

#### Cause 1: Description Too Long
**Symptoms**: Only some skills are detected, others with long descriptions are missing

**Diagnosis**:
```bash
# Check description length
grep -A 1 "^description:" SKILL.md
```

**Fix**:
```markdown
# Before (too long)
description: Very long description that describes the skill in excessive detail and goes on for many sentences, which can cause parsing failures

# After (concise)
description: Analyzes code and generates diagrams
```

**Rule**: Keep under 200 characters

---

#### Cause 2: Blank Lines Before YAML Header
**Symptoms**: Skill completely missing from detection

**Diagnosis**:
```bash
# Check first few bytes
head -5 SKILL.md | cat -A
```

Look for `^M$` or blank lines before `---`

**Fix**:
```markdown
# WRONG:
[blank line here]
---
name: my-skill

# CORRECT:
---
name: my-skill
```

Remove any blank lines before the `---` marker.

---

#### Cause 3: Invalid YAML Syntax
**Symptoms**: Parse error or skill not detected

**Diagnosis**:
```bash
# Validate YAML
npx yaml-lint SKILL.md
```

**Fix**:
```markdown
# WRONG (missing closing dashes):
---
name: my-skill
description: Test

# CORRECT:
---
name: my-skill
description: Test
---
```

---

#### Cause 4: Missing YAML Header Entirely
**Symptoms**: "No valid skills found"

**Diagnosis**:
```bash
head -1 SKILL.md
```

Should show `---`

**Fix**: Add YAML header:
```markdown
---
name: my-skill
description: My skill description
---
```

---

## Problem 2: "Found 0 skills"

### Symptoms
```
npx skills add https://github.com/user/repo

x  No valid skills found. Skills require a SKILL.md with name and description.
```

### Causes and Solutions

#### Cause 1: SKILL.md File Missing
**Diagnosis**:
```bash
ls -la skill-name/
```

**Fix**: Create SKILL.md file with proper format.

---

#### Cause 2: All SKILL.md Files Have Errors
**Diagnosis**:
```bash
# Test each skill individually
cd skill-name
npx skills add . --skill skill-name
```

**Fix**: Use validation checklist to fix each skill.

---

#### Cause 3: Incorrect Directory Structure
**Symptoms**: Skills CLI can't find skill directories

**Correct Structure**:
```
repo/
├── skill-one/
│   └── SKILL.md  # Must be here
├── skill-two/
│   └── SKILL.md  # Must be here
```

**Wrong Structure**:
```
repo/
├── SKILL.md      # WRONG - not in subdirectory
└── skills/
    ├── skill-one/SKILL.md  # MAYBE - depends on config
```

---

## Problem 3: "Found X skills" but Wrong Count

### Symptoms
You have 5 skills but only 3 are detected.

### Cause: Some Skills Have Format Errors

**Diagnosis**: Skills CLI may stop parsing after encountering an error.

**Solution**:
1. Test each skill directory individually:
   ```bash
   cd skill-one && npx skills add . --skill skill-one
   cd ../skill-two && npx skills add . --skill skill-two
   ```

2. Fix any skills that fail

---

## Problem 4: Only One Skill Detected

### Symptoms
Multiple skill directories exist but only one is found.

### Possible Causes

#### Cause 1: Other Skills Have Critical Errors
Skills CLI may stop after first error.

**Fix**: Validate each SKILL.md file individually.

#### Cause 2: Directory Names Don't Match
**Diagnosis**:
```bash
# Check directory name
basename $(pwd)

# Check skill name
grep "^name:" SKILL.md
```

**Fix**: Rename directory to match `name` field.

---

## Problem 5: Skill Installs But Doesn't Work

### Symptoms
Installation succeeds but skill doesn't trigger.

### Causes

#### Cause 1: Incorrect Trigger Words
**Fix**: Ensure skill description and content match actual usage patterns.

#### Cause 2: Wrong File Format
**Fix**: Verify SKILL.md is valid Markdown with proper YAML header.

---

## Problem 6: Special Character Issues

### Symptoms
Description contains special characters that cause parsing issues.

### Common Problem Characters
- Unescaped quotes: `"My "quoted" description"`
- Unescaped colons in values
- Non-ASCII characters (may work but can cause issues)

### Fix
```markdown
# WRONG:
description: My "special" skill with: colons

# BETTER:
description: My special skill with colons
```

Or use YAML block scalar:
```markdown
description: |
  My "special" skill
  with multiple lines
```

---

## Problem 7: Line Ending Issues (Windows)

### Symptoms
Works on one machine but not another, especially Windows vs Unix.

### Diagnosis
```bash
# Check line endings
file SKILL.md
# Should show: ASCII text

# On Windows, check with:
cat -A SKILL.md | head -1
# Should show: ---^M$
```

### Fix
Configure Git to handle line endings:
```bash
# Global setting
git config --global core.autocrlf input

# Or per-repository
echo "* text=auto" > .gitattributes
```

---

## Problem 8: manifest.json Conflicts

### Symptoms
Skill recognized but metadata is wrong or incomplete.

### Cause
Both `manifest.json` and SKILL.md front matter exist with conflicting data.

### Fix
**Option 1**: Remove manifest.json (recommended)
```bash
rm manifest.json
```

**Option 2**: Ensure both files have identical data (not recommended)

---

## Debugging Workflow

### Step 1: Basic Validation
```bash
# Check file exists
ls -la SKILL.md

# Check first few lines
head -10 SKILL.md

# Check YAML validity
npx yaml-lint SKILL.md 2>&1 | head -20
```

### Step 2: Local Testing
```bash
# Clone your repo
git clone https://github.com/user/repo test-skills
cd test-skills

# Test all skills
npx skills add .

# Test specific skill
npx skills add . --skill skill-name
```

### Step 3: Character Count Check
```bash
# Check description length
grep "^description:" SKILL.md | wc -c
```

Should be < 250 characters.

### Step 4: Blank Line Check
```bash
# Check for blank lines before ---
head -3 SKILL.md | cat -A
```

First line should be `---^M$` (no preceding blank).

### Step 5: Compare with Working Skill
```bash
# Compare with a known working skill
diff -u working-skill/SKILL.md broken-skill/SKILL.md
```

---

## Quick Fix Scripts

### Fix Blank Lines at Start
```bash
# Remove blank lines before ---
sed -i '1{/^$/d;}' SKILL.md
```

### Shorten Description
```bash
# Interactive editor to shorten
nano SKILL.md
# Focus on line with "description:"
```

### Validate All Skills in Repo
```bash
#!/bin/bash
for skill_dir in */; do
    if [ -f "${skill_dir}/SKILL.md" ]; then
        echo "Checking ${skill_dir}..."
        cd "$skill_dir"
        npx yaml-lint SKILL.md 2>&1 | grep -q "valid" && echo "  ✓ Valid" || echo "  ✗ Invalid"
        cd ..
    fi
done
```

---

## Prevention Checklist

Before committing/publishing:

- [ ] No blank lines before YAML header
- [ ] Description under 200 characters
- [ ] YAML header properly closed with `---`
- [ ] Directory name matches `name` field
- [ ] Tested with `npx skills add .`
- [ ] No conflicting manifest.json
- [ ] YAML syntax is valid
- [ ] Line endings are consistent (LF preferred)
- [ ] All required fields present

---

## Resources

- [Skills CLI Docs](https://skills.sh/docs)
- [YAML Linter](https://github.com/ibiwan/yamllint)
- [YAML Spec](https://yaml.org/spec/)

---

## Common Error Messages Explained

| Error Message | Meaning | Fix |
|--------------|---------|-----|
| "No matching skills found" | Skill name not recognized | Check spelling, fix SKILL.md format |
| "No valid skills found" | No SKILL.md files or all invalid | Create/fix SKILL.md files |
| "Found 0 skills" | Repository has no detectable skills | Add skills or fix format |
| "Skills require a SKILL.md" | Missing required file | Create SKILL.md with proper format |
