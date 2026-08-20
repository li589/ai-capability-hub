# Verification Report Templates

## Template 1: Full Verification (All Pass)

```markdown
## Verification Report

### Executed
| Check | Command | Result | Duration | Details |
|---|---|---|---|---|
| Lint | `npm run lint` | PASS | 2.1s | 0 errors, 0 warnings |
| TypeCheck | `npx tsc --noEmit` | PASS | 4.3s | No type errors |
| Test (targeted) | `npm test -- --testPathPattern=settings` | PASS | 1.8s | 5/5 tests passed |
| Build | `npm run build` | PASS | 12.4s | Compiled successfully |
| Browser | Manual check at localhost:3000/settings | PASS | — | Page renders, form works |

### Not Executed
- Full test suite: Only targeted tests run for speed. Run `npm test` for full suite.

### Summary
- 5/5 checks passed
- 0 fixes needed
- Recommendation: Run full test suite before merging
```

## Template 2: Partial Failure with Fixes

```markdown
## Verification Report

### Executed
| Check | Command | Result | Details |
|---|---|---|---|
| Lint | `npm run lint` | FAIL | 2 errors |
| TypeCheck | `npx tsc --noEmit` | FAIL | 1 error |
| Test | (skipped) | SKIP | Blocked by lint/type errors |
| Build | (skipped) | SKIP | Blocked by type errors |

### Failures & Fixes

**Lint Error 1**: `'Select' is defined but never used` at settings/page.tsx:3
- Fix: Removed unused import
- Re-run: PASS

**Lint Error 2**: `Missing return type on function` at settings/api.ts:15
- Fix: Added explicit return type `Promise<Settings>`
- Re-run: PASS

**Type Error**: `Property 'theme' does not exist on type 'UserPreferences'`
- Fix: Added `theme` field to UserPreferences interface in types/settings.ts
- Re-run: PASS

### Re-verification After Fixes
| Check | Command | Result |
|---|---|---|
| Lint | `npm run lint` | PASS |
| TypeCheck | `npx tsc --noEmit` | PASS |
| Test | `npm test -- --testPathPattern=settings` | PASS (5/5) |
| Build | `npm run build` | PASS |

### Summary
- Initial: 2 failures
- After fixes: All pass
- Fixes applied: 3 (2 lint, 1 type)
```

## Template 3: Limited Environment

```markdown
## Verification Report

### Executed
| Check | Command | Result | Details |
|---|---|---|---|
| Lint | `npm run lint` | PASS | 0 errors |
| TypeCheck | `npx tsc --noEmit` | PASS | No type errors |

### Not Executed (with reasons)
| Check | Reason | Manual Alternative |
|---|---|---|
| Test | Test runner requires database connection | `npm test` with DB running |
| Build | Build takes >5min, skipped for iteration speed | `npm run build` before deploy |
| Browser | No dev server available | `npm run dev` + visit /settings |

### Summary
- 2/5 checks executed, both passed
- 3 checks require manual verification
- Risk: Medium — build and runtime not verified
```

## Template 4: Non-JavaScript Project

```markdown
## Verification Report (Python)

### Executed
| Check | Command | Result | Details |
|---|---|---|---|
| Lint | `ruff check .` | PASS | 0 errors |
| TypeCheck | `mypy src/` | FAIL | 2 errors |
| Test | `pytest tests/test_settings.py` | PASS | 8/8 passed |

### Failures & Fixes
**mypy**: `Incompatible return type` in src/api/settings.py:42
- Fix: Changed return type annotation
- Re-run: PASS

### Summary
- All checks pass after fix
```

## Template 5: Task Completion Report (Combined)

Use this at the end of a complete task:

```markdown
## Task Completion Report

### Changes Made
1. Created `src/app/(dashboard)/settings/page.tsx` — Settings page with tabs
2. Created `src/components/forms/SettingsForm.tsx` — Reusable settings form
3. Modified `src/components/layout/Sidebar.tsx` — Added settings nav link
4. Created `src/types/settings.ts` — Settings type definitions

### Evidence Summary
- Verified: 12 claims from local code, docs, and commands
- Assumed: 0 claims
- Key evidence: shadcn/ui components confirmed in components.json

### Verification Report
| Check | Result |
|---|---|
| Lint | PASS |
| TypeCheck | PASS |
| Test | PASS (5/5 targeted) |
| Build | PASS |
| Browser | PASS (page renders, form works) |

### UI Review
- [x] Uses shadcn/ui components (not custom recreations)
- [x] Colors from project palette
- [x] All states handled (loading, empty, error)
- [x] Responsive at 375px and 1280px
- [x] No AI-pattern anti-patterns detected

### Remaining Risks
- Full test suite not run (only targeted tests)
- No E2E test added for settings flow
```
