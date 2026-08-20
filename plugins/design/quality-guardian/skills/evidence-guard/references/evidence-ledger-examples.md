# Evidence Ledger Examples

## Example 1: Adding a New API Endpoint

### During Investigation

```
EVIDENCE LEDGER — Task: Add user settings API
─────────────────────────────────────────────────
[1] Project uses Express.js v4.18.2
    → local-code: package.json line 12
    → confidence: verified

[2] Existing route pattern: /api/v1/[resource]
    → local-code: src/routes/index.ts lines 5-20
    → confidence: verified

[3] Project uses JWT authentication middleware
    → local-code: src/middleware/auth.ts
    → confidence: verified

[4] Database is PostgreSQL with Prisma ORM
    → local-code: prisma/schema.prisma
    → confidence: verified

[5] Settings table already exists
    → local-code: prisma/schema.prisma model Settings
    → confidence: verified

[6] Express rate limiter supports per-user limits
    → ASSUMPTION: Based on common express-rate-limit usage
    → Risk: API may have changed in installed version
    → How to verify: Check node_modules/express-rate-limit/README.md
```

### Final Report

```markdown
## Verification Status

### Verified
- [x] Express v4.18.2 in use — source: package.json
- [x] Route pattern /api/v1/[resource] — source: src/routes/index.ts
- [x] JWT middleware exists — source: src/middleware/auth.ts
- [x] Prisma + PostgreSQL — source: prisma/schema.prisma
- [x] Settings model exists — source: prisma/schema.prisma
- [x] New endpoint returns 200 — source: curl test output
- [x] Lint passes — source: npm run lint output

### Unverified (assumptions)
- [ ] Rate limiter supports per-user limits — need to check installed version

### Remaining Risks
- Rate limiting behavior untested under load; verify with manual test
```

## Example 2: Using a Third-Party Library

### Before Using `zod` for Validation

```
CHECKLIST:
1. Is zod in dependencies?
   → Read package.json → YES, zod@3.22.4

2. Does .z.object() exist in zod 3.22?
   → WebFetch: https://zod.dev → YES, documented

3. Does the project already use zod elsewhere?
   → Grep "from 'zod'" → Found in src/validators/user.ts
   → Pattern: z.object({ name: z.string(), email: z.string().email() })

4. Safe to use same pattern → verified
```

### When Library Is NOT in Dependencies

```
[CLAIM] We should use date-fns for date formatting
→ Source: NONE — not in package.json
→ Status: RECOMMENDATION, not implementation
→ Action: Tell user "date-fns is not installed. 
   Options: (a) install it, (b) use Intl.DateTimeFormat (native), 
   (c) use existing dayjs already in project"
```

## Example 3: Architecture Decision

```
EVIDENCE LEDGER — Task: Choose state management approach
─────────────────────────────────────────────────────────
[1] Project uses React 18.2
    → local-code: package.json
    → verified

[2] Project already has Redux Toolkit installed
    → local-code: package.json + src/store/index.ts
    → verified

[3] Existing pattern: feature-based slices
    → local-code: src/store/slices/*.ts
    → verified

[4] DECISION: Use Redux Toolkit slice for new feature
    → Basis: evidence [1][2][3] — consistent with existing architecture
    → confidence: verified

[5] ALTERNATIVE CONSIDERED: Zustand
    → Rejected because: Would add new dependency when Redux already handles state
    → This is reasoning, not a fact claim
```
