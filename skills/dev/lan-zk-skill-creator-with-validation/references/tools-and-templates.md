# Skills CLI Validation Tools and Templates

## Quick Validation Scripts

### Bash/Shell Scripts

#### 1. Validate Single SKILL.md
```bash
#!/bin/bash
# validate-skill.sh <path-to-SKILL.md>

SKILL_MD="${1:-SKILL.md}"

echo "Validating: $SKILL_MD"
echo "==="

# Check file exists
if [ ! -f "$SKILL_MD" ]; then
    echo "✗ File not found: $SKILL_MD"
    exit 1
fi

# Check first line is ---
FIRST_LINE=$(head -1 "$SKILL_MD")
if [ "$FIRST_LINE" != "---" ]; then
    echo "✗ FAILED: First line must be '---' (no blank lines before)"
    echo "   Got: '$FIRST_LINE'"
    exit 1
fi
echo "✓ First line is ---"

# Check YAML header is closed
LINE_COUNT=$(grep -n "^---" "$SKILL_MD" | wc -l)
if [ "$LINE_COUNT" -lt 2 ]; then
    echo "✗ FAILED: YAML header not closed (missing second ---)"
    exit 1
fi
echo "✓ YAML header properly closed"

# Extract and check description length
DESCRIPTION=$(grep "^description:" "$SKILL_MD" | cut -d':' -f2- | xargs)
DESC_LENGTH=${#DESCRIPTION}

if [ $DESC_LENGTH -eq 0 ]; then
    echo "✗ FAILED: No description found"
    exit 1
fi

if [ $DESC_LENGTH -gt 200 ]; then
    echo "✗ WARNING: Description too long ($DESC_LENGTH chars, max 200)"
    echo "   Description: $DESCRIPTION"
elif [ $DESC_LENGTH -gt 150 ]; then
    echo "⚠ WARNING: Description long ($DESC_LENGTH chars, recommended <150)"
    echo "   Description: $DESCRIPTION"
else
    echo "✓ Description length: $DESC_LENGTH chars"
fi

# Check name field exists
NAME=$(grep "^name:" "$SKILL_MD" | cut -d':' -f2 | xargs)
if [ -z "$NAME" ]; then
    echo "✗ FAILED: No name field found"
    exit 1
fi
echo "✓ Name: $NAME"

# Check directory name matches
DIR_NAME=$(basename "$(dirname "$SKILL_MD")")
if [ "$DIR_NAME" != "$NAME" ]; then
    echo "⚠ WARNING: Directory name '$DIR_NAME' doesn't match skill name '$NAME'"
else
    echo "✓ Directory name matches skill name"
fi

echo "==="

# Try to parse with YAML linter if available
if command -v yaml-lint &> /dev/null; then
    echo "Running YAML linter..."
    yaml-lint "$SKILL_MD" 2>&1 | grep -q "valid" && \
        echo "✓ YAML syntax valid" || \
        echo "⚠ YAML validation warnings/errors"
fi

echo ""
echo "✓ Validation complete!"
```

#### 2. Validate All Skills in Repository
```bash
#!/bin/bash
# validate-all-skills.sh

echo "Validating all skills in repository..."
echo ""

for skill_dir in */; do
    SKILL_MD="${skill_dir}/SKILL.md"

    if [ -f "$SKILL_MD" ]; then
        echo "Checking $skill_dir..."
        ./validate-skill.sh "$SKILL_MD"
        echo ""
    fi
done

echo "=== Validation complete ==="
```

#### 3. Fix Blank Lines Script
```bash
#!/bin/bash
# fix-blank-lines.sh <SKILL.md>

SKILL_MD="${1:-SKILL.md}"

echo "Fixing blank lines in: $SKILL_MD"

# Remove blank lines at start of file
sed -i '1{/^$/d;}' "$SKILL_MD"

echo "✓ Fixed blank lines"
```

### Python Validation Script

```python
#!/usr/bin/env python3
# validate_skill.py

import sys
import re
import yaml

def validate_skill(skill_md_path):
    """Validate SKILL.md file format"""

    with open(skill_md_path, 'r') as f:
        content = f.read()

    print(f"Validating: {skill_md_path}")
    print("=" * 50)

    # Check 1: No blank lines before YAML header
    lines = content.split('\n')
    if lines[0] != '---':
        print("✗ FAILED: First line must be '---' (no blank lines before)")
        print(f"   Got: '{lines[0]}'")
        return False
    print("✓ First line is ---")

    # Check 2: YAML header exists and is valid
    try:
        # Find YAML header (between first and second ---)
        yaml_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL | re.MULTILINE)

        if not yaml_match:
            print("✗ FAILED: YAML header not found or not properly closed")
            return False

        yaml_content = yaml_match.group(1)
        front_matter = yaml.safe_load(yaml_content)

        print("✓ YAML header valid")

    except yaml.YAMLError as e:
        print(f"✗ FAILED: Invalid YAML syntax: {e}")
        return False

    # Check 3: Required fields
    if 'name' not in front_matter:
        print("✗ FAILED: Missing 'name' field in YAML header")
        return False
    print(f"✓ Name: {front_matter['name']}")

    if 'description' not in front_matter:
        print("✗ FAILED: Missing 'description' field in YAML header")
        return False

    desc = front_matter['description']
    desc_len = len(desc)

    if desc_len > 250:
        print(f"✗ FAILED: Description too long ({desc_len} chars, max 250)")
        print(f"   {desc}")
        return False
    elif desc_len > 200:
        print(f"⚠ WARNING: Description long ({desc_len} chars, recommended <200)")
    else:
        print(f"✓ Description length: {desc_len} chars")
    print(f"   {desc}")

    # Check 4: Directory name matches
    import os
    dir_name = os.path.basename(os.path.dirname(skill_md_path))
    if dir_name != front_matter['name']:
        print(f"⚠ WARNING: Directory name '{dir_name}' doesn't match skill name '{front_matter['name']}'")
    else:
        print("✓ Directory name matches skill name")

    print("=" * 50)
    print("✓ Validation complete!")
    return True

if __name__ == "__main__":
    skill_md = sys.argv[1] if len(sys.argv) > 1 else "SKILL.md"
    success = validate_skill(skill_md)
    sys.exit(0 if success else 1)
```

### Batch Validation for Windows

```batch
@echo off
REM validate-skill.bat <path-to-SKILL.md>

set SKILL_MD=%1
if "%SKILL_MD%"=="" set SKILL_MD=SKILL.md

echo Validating: %SKILL_MD%
echo ===

REM Check first line is ---
for /f "delims=" %%a in ('more +0 "%SKILL_MD%" ^| findstr /n "^" ^| findstr "^1:"') do (
    set "FIRST_LINE=%%a"
    goto :check_line
)

:check_line
if not "%FIRST_LINE:~2%"=="---" (
    echo ✗ FAILED: First line must be '---' (no blank lines before)
    echo    Got: '%FIRST_LINE:~2%'
    exit /b 1
)

echo ✓ First line is ---

REM Check name field
findstr /r "^name:" "%SKILL_MD%" >nul
if errorlevel 1 (
    echo ✗ FAILED: No name field found
    exit /b 1
)

echo ✓ Name field exists

REM Check description field
findstr /r "^description:" "%SKILL_MD%" >nul
if errorlevel 1 (
    echo ✗ FAILED: No description field found
    exit /b 1
)

echo ✓ Description field exists
echo ===
echo ✓ Validation complete!
```

---

## Pre-commit Hook

Add this to `.git/hooks/pre-commit` to validate skills before committing:

```bash
#!/bin/bash
# Pre-commit hook to validate SKILL.md files

echo "Validating SKILL.md files..."

# Find all SKILL.md files that are staged
SKILL_FILES=$(git diff --cached --name-only | grep SKILL.md)

if [ -z "$SKILL_FILES" ]; then
    echo "No SKILL.md files to validate"
    exit 0
fi

FAILURES=0

for skill_md in $SKILL_FILES; do
    echo "Validating $skill_md..."

    # Check first line
    if [ "$(head -1 "$skill_md")" != "---" ]; then
        echo "✗ FAILED: $skill_md - First line must be '---'"
        FAILURES=$((FAILURES + 1))
    fi

    # Check description length
    DESC=$(grep "^description:" "$skill_md" | cut -d':' -f2- | xargs)
    if [ ${#DESC} -gt 250 ]; then
        echo "✗ FAILED: $skill_md - Description too long (${#DESC} chars)"
        FAILURES=$((FAILURES + 1))
    fi
done

if [ $FAILURES -gt 0 ]; then
    echo ""
    echo "Validation failed! Please fix the issues above."
    echo "Use: ./validate-skill.sh <file> to debug"
    exit 1
fi

echo "✓ All SKILL.md files validated"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## VS Code Snippets

Add to `.vscode/snippets/skills.json`:

```json
{
  "Skills CLI Skill Template": {
    "prefix": "skill-template",
    "body": [
      "---",
      "name: ${1:skill-name}",
      "description: ${2:Short description of skill}",
      "categories: [${3:category1}, ${4:category2}]",
      "tags: [${5:tag1}, ${6:tag2}]",
      "version: ${7:1.0.0}",
      "author: ${8:Your Name}",
      "---",
      "",
      "# ${1:skill-name}",
      "",
      "## Overview",
      "${9:Overview here}",
      "",
      "## Usage",
      "",
      "## Examples"
    ],
    "description": "Skills CLI SKILL.md template"
  }
}
```

---

## GitHub Action for Validation

Add to `.github/workflows/validate-skills.yml`:

```yaml
name: Validate Skills

on:
  push:
    paths:
      - '**/SKILL.md'
  pull_request:
    paths:
      - '**/SKILL.md'

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Validate all SKILL.md files
        run: |
          find . -name "SKILL.md" -type f | while read skill; do
            echo "Validating: $skill"
            python3 << 'VALIDATOR'
import sys
import re
import yaml

skill_md = sys.argv[1]
with open(skill_md, 'r') as f:
    content = f.read()

# Check first line
lines = content.split('\n')
if lines[0] != '---':
    print(f"✗ FAILED: First line must be '---'")
    sys.exit(1)

# Parse YAML
yaml_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL | re.MULTILINE)
if not yaml_match:
    print("✗ FAILED: YAML header not properly closed")
    sys.exit(1)

try:
    front_matter = yaml.safe_load(yaml_match.group(1))
except yaml.YAMLError as e:
    print(f"✗ FAILED: Invalid YAML: {e}")
    sys.exit(1)

# Check required fields
if 'name' not in front_matter or 'description' not in front_matter:
    print("✗ FAILED: Missing required fields (name, description)")
    sys.exit(1)

desc_len = len(front_matter['description'])
if desc_len > 250:
    print(f"✗ FAILED: Description too long ({desc_len} chars)")
    sys.exit(1)

print(f"✓ Valid: {skill_md}")
            VALIDATOR
            "$skill" || exit 1
          done
        shell: bash
```

---

## Browser Bookmarklet for Quick Validation

Create a bookmark with this JavaScript to validate SKILL.md on GitHub:

```javascript
javascript:(function(){
    const content = document.querySelector('.blob-code-inner')?.textContent;
    if (!content) {
        alert('Could not find SKILL.md content');
        return;
    }

    const lines = content.split('\n');
    let issues = [];

    if (lines[0] !== '---') {
        issues.push('First line must be "---" (no blank lines before)');
    }

    const descMatch = content.match(/^description:\s*(.*)$/m);
    if (descMatch) {
        const desc = descMatch[1].trim();
        if (desc.length > 250) {
            issues.push(`Description too long (${desc.length} chars, max 250)`);
        }
    }

    const nameMatch = content.match(/^name:\s*(.*)$/m);
    if (!nameMatch) {
        issues.push('Missing "name" field');
    }

    if (issues.length === 0) {
        alert('✓ SKILL.md appears valid!');
    } else {
        alert('Issues found:\n\n' + issues.join('\n'));
    }
})();
```

---

## Interactive Prompt for Creating Skills

```bash
#!/bin/bash
# create-skill.sh

echo "Skills CLI Skill Creator"
echo "========================="
echo ""

# Get skill name
read -p "Skill name (lowercase, hyphens): " NAME
while [[ ! "$NAME" =~ ^[a-z0-9\-]+$ ]]; do
    echo "Invalid name. Use lowercase letters, numbers, and hyphens only."
    read -p "Skill name: " NAME
done

# Create directory
mkdir -p "$NAME/references"

# Get description
read -p "Description (<200 chars): " DESCRIPTION
while [ ${#DESCRIPTION} -gt 200 ]; do
    echo "Description too long (${#DESCRIPTION} chars). Keep under 200."
    read -p "Description: " DESCRIPTION
done

# Get categories
read -p "Categories (comma-separated, e.g., java,analysis): " CATEGORIES
CATEGORIES=${CATEGORIES//,/\", \"}

# Create SKILL.md
cat > "$NAME/SKILL.md" <<EOF
---
name: $NAME
description: $DESCRIPTION
categories: ["$CATEGORIES"]
version: 1.0.0
---

# ${NAME}

## Overview

## Usage

## Examples
EOF

echo ""
echo "✓ Created skill: $NAME"
echo "  - $NAME/SKILL.md"
echo "  - $NAME/references/"
echo ""
echo "Next steps:"
echo "1. Edit $NAME/SKILL.md to add content"
echo "2. Add reference docs to $NAME/references/"
echo "3. Test with: cd $NAME && npx skills add ."
```

---

## Template Files

### Minimal SKILL.md Template
```markdown
---
name: skill-name
description: Short description
---

# Skill Name

## Overview

## Usage

## Examples
```

### Complete SKILL.md Template
```markdown
---
name: skill-name
description: Brief description under 200 characters
categories: [category1, category2]
tags: [tag1, tag2, tag3]
version: 1.0.0
author: Your Name
license: MIT
---

# Skill Name

## Overview
Brief description of what the skill does and its primary use cases.

## Features
- Feature 1
- Feature 2
- Feature 3

## Usage
How to use this skill.

### Basic Usage
```example
code example
```

### Advanced Usage
```example
advanced example
```

## Examples

### Example 1: Basic
Description of example.

### Example 2: Advanced
Description of example.

## Configuration
Any configuration options.

## References
- [Detailed Guide](references/guide.md)
- [Examples](references/examples.md)
- [API Reference](references/api.md)

## Troubleshooting
Common issues and solutions.

## Contributing
How to contribute to this skill.
```

---

## Quick Reference Card

### DOs
✅ Start file with `---` (no blank lines)
✅ Keep description <200 chars
✅ Include required fields (name, description)
✅ Use valid YAML syntax
✅ Match directory name to skill name
✅ Test with `npx skills add .`

### DON'Ts
❌ Don't add blank lines before YAML header
❌ Don't use descriptions >250 chars
❌ Don't forget to close YAML header with `---`
❌ Don't use invalid YAML
❌ Don't mix manifest.json and SKILL.md metadata
❌ Don't skip local testing

### Validation Commands
```bash
# Quick check
head -1 SKILL.md  # Should be ---

# Check description
grep "^description:" SKILL.md

# Validate YAML
npx yaml-lint SKILL.md

# Test loading
npx skills add . --skill skill-name
```

---

## Online Validators

### YAML Validator
- https://www.yamllint.com/
- https://codebeautify.org/yaml-validator

### Character Counter
- https://charactercounttool.com/

---

These tools should help you create and validate skills efficiently!
