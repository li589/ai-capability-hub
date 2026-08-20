---
description: Add structured logging to any TypeScript file using @alcyone-labs/simple-logger
---

## Workflow

### Step 1: Check for --update-skill flag

If `$ARGUMENTS` contains `--update-skill`:
1. Run `skills/install.sh --local` (or `--global` based on context)
2. Stop execution

### Step 2: Load skill

```javascript
skill({ name: 'simple-logger-usage' })
```

### Step 3: Parse task from arguments

Analyze `$ARGUMENTS` to determine task type:
- **"add logging to file X"** → Apply file-scoped logger pattern
- **"add logging to component X"** → Apply frontend component pattern
- **"configure transports"** → Show transport setup options
- **"Chrome MV3"** or **"service worker"** → Apply MV3 IIFE pattern
- **"best practices"** → Reference decision tree and patterns
- **General question** → Provide overview and relevant references

### Step 4: Read relevant references

| Task | Files to Read |
|------|---------------|
| Backend/service logging | `references/usage/api.md` + `patterns.md` |
| Frontend component | `references/usage/patterns.md` (Pattern 3) |
| Chrome MV3/SW | `references/usage/configuration.md` (MV3 section) + `gotchas.md` (MV3 limitations) |
| Transport setup | `references/usage/configuration.md` |
| API details | `references/usage/api.md` |
| Troubleshooting | `references/usage/gotchas.md` |

### Step 5: Execute

- Generate file-scoped logger with appropriate metadata
- Create child loggers for request/function context
- Show transport configuration if needed
- Include Chrome MV3 specific guidance when applicable
- Reference patterns and gotchas as needed

### Step 6: Output

Return complete implementation with:
- Import statement
- Logger initialization with contextual metadata
- Example log statements at appropriate levels
- Comments explaining the pattern
