---
name: verification-runner
description: >
  Enforces post-change verification by running lint, typecheck, tests, and builds after code
  modifications. For web/UI tasks, performs browser checks for blank pages, console errors, text
  overlap, and interactivity. Only reports verification that actually ran. Use after any code
  modification, file creation, or refactoring.
description_zh: >
  在代码修改后强制执行验证：运行 lint、类型检查、测试和构建。对于 Web/UI 任务，
  执行浏览器检查（空白页、控制台错误、文字重叠、交互可用性）。只报告实际运行过的
  验证。在任何代码修改、文件创建或重构后使用。
version: 1.0.0
user-invocable: false
---

# Verification Runner

## Core Principle

**Only report what you actually ran.** Never claim tests passed if you didn't execute them. Never fake build success.

**If you can't verify, say so.** Explicitly state what wasn't verified and why.

## Configuration

```yaml
enableBrowserVerification: true      # Use browser for UI checks when possible
requiredVerificationCommands: []     # Override: commands that MUST run after changes
skipIfNoConfig: false                # Don't skip verification even without project config
```

## Verification Workflow

### Step 1: Detect Available Verification

Before running anything, detect what the project supports:

```
DETECTION CHECKLIST:
- package.json scripts:
  - "lint" → ESLint/Biome available
  - "typecheck" or "tsc" → TypeScript checking available
  - "test" → Test runner available (check which: jest, vitest, mocha)
  - "build" → Build command available
  - "check" → Combined check command
- Cargo.toml → cargo check, cargo test, cargo clippy
- pyproject.toml / setup.py → pytest, mypy, ruff
- go.mod → go build, go test, go vet
- Makefile → make targets
```

### Step 2: Run Verification (in order)

Execute in this priority order. Stop at first failure and fix before continuing:

```
1. Lint        → Fast feedback, catches obvious issues
2. TypeCheck   → Catches type errors without running code
3. Test        → Catches logic errors (run relevant tests first, then full suite)
4. Build       → Catches import errors, missing dependencies
5. Browser     → Catches visual issues (for web/UI changes only)
```

### Step 3: Report Results

```markdown
## Verification Report

### Executed
| Check | Command | Result | Details |
|---|---|---|---|
| Lint | `npm run lint` | PASS | No errors |
| TypeCheck | `npx tsc --noEmit` | PASS | No type errors |
| Test | `npm test -- --testPathPattern=settings` | PASS | 3/3 tests passed |
| Build | `npm run build` | FAIL | Import error in settings/page.tsx |

### Failed (with fix)
- Build: Missing import `Select` from @/components/ui/select
  - Fix: Added import statement
  - Re-run: `npm run build` → PASS

### Not Executed (with reason)
- Browser: Dev server not available in current environment
- E2E tests: No Playwright/Cypress configured

### Summary
- Total checks: 4 executed, 2 skipped
- All executed: PASS
- Fixes applied: 1 (missing import)
```

## Verification Commands by Stack

### Node.js / TypeScript

```bash
# Detection
cat package.json | grep -E '"lint"|"test"|"build"|"typecheck"'

# Standard commands
npm run lint                    # ESLint
npx tsc --noEmit               # TypeScript type check
npm test                       # Jest/Vitest
npm run build                  # Next.js/Vite/Webpack build

# Targeted test (preferred for speed)
npm test -- --testPathPattern=<changed-file>   # Jest
npm test -- <changed-file>                      # Vitest
```

### Python

```bash
# Detection
ls pyproject.toml setup.py requirements.txt 2>/dev/null

# Standard commands
python -m pytest               # pytest
python -m mypy .               # Type checking
ruff check .                   # Linting
python -m build                # Build check
```

### Rust

```bash
cargo check                    # Compilation check
cargo clippy                   # Linting
cargo test                     # Tests
cargo build                    # Full build
```

### Go

```bash
go vet ./...                   # Static analysis
go build ./...                 # Compilation
go test ./...                  # Tests
```

## Browser Verification (Web/UI Tasks)

When a dev server is available and the change involves UI:

### Checklist

```
BROWSER VERIFICATION:
1. Page loads without blank screen
2. No console errors (severity: error)
3. No console warnings from our code
4. Text is readable (not overlapping, not truncated)
5. Layout renders correctly at 1280px
6. Layout renders correctly at 375px (mobile)
7. Interactive elements respond (buttons click, inputs type)
8. Navigation works (links go where expected)
9. Loading states display during data fetch
10. Empty states display when no data
```

### How to Browser-Verify

1. Start dev server if not running: `npm run dev` (or equivalent)
2. Navigate to the changed page
3. Take a screenshot
4. Check console for errors
5. Interact with key elements
6. Check responsive behavior (resize viewport)
7. Report findings

### When Browser Verification Is Not Possible

If browser is unavailable, explicitly state:

```markdown
> **Browser verification skipped**: Dev server not available / No browser MCP configured.
> Manual verification recommended:
> 1. Run `npm run dev`
> 2. Navigate to /settings
> 3. Verify settings form renders and saves correctly
```

## Failure Handling

When verification fails:

1. **Read the error carefully** — Don't guess what went wrong
2. **Fix the root cause** — Don't suppress warnings or skip tests
3. **Re-run the specific check** — Don't re-run everything unless needed
4. **Report the fix** — Include what failed and how it was fixed

### Common Fix Patterns

```
Lint error (unused import)     → Remove the import
Lint error (missing type)      → Add proper type annotation
Type error (wrong prop type)   → Fix the type, don't use 'any'
Test failure (assertion)       → Fix the logic, don't change the test
Build error (missing export)   → Add the export
Build error (missing dep)      → Install or import the dependency
```

## What NOT to Do

1. **Don't fake results** — If you didn't run it, don't say it passed
2. **Don't skip silently** — If you can't run something, say why
3. **Don't suppress errors** — Don't add `// @ts-ignore` or disable lint rules
4. **Don't change tests to pass** — Fix the code, not the test (unless test is wrong)
5. **Don't ignore warnings** — Report them even if non-blocking

## Integration

- **Evidence Guard**: Verification results become evidence entries (`test-result`, `command-output`)
- **Context Cartographer**: Failed verification may require reading additional files
- **UI Taste Guard**: Browser verification checks for anti-patterns visually

## Additional Resources

- For verification report templates, see [verification-templates.md](references/verification-templates.md)
