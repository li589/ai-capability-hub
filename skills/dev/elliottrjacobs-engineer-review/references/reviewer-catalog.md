# Reviewer Catalog

Quick reference for what each reviewer agent focuses on. Used by `/engineer-review` when spawning parallel agents.

## Core Reviewers (Always Launch)

### Security Reviewer
- OWASP Top 10 vulnerabilities
- Auth bypass, privilege escalation
- SQL injection, XSS, command injection, path traversal, SSRF
- Hardcoded secrets, exposed env vars
- Data exposure in API responses
- Missing input validation at system boundaries
- Insecure defaults, missing rate limiting

### Performance Reviewer
- N+1 query patterns
- Missing database indexes
- Unnecessary React re-renders, missing memoization
- Bundle size bloat, missing code splitting
- Request waterfalls (sequential fetches that could be parallel)
- Missing caching (React Query staleTime, server-side caching)
- Image optimization gaps
- Large payloads from over-fetching

### Architecture Reviewer
- Server vs client component boundaries
- Component responsibility (single responsibility)
- Module dependencies and boundaries
- State management choices (server state vs client state vs URL state)
- Data flow patterns (unidirectional)
- SOLID principles (applied pragmatically, not dogmatically)
- API layer isolation

### Patterns Reviewer
- Naming conventions (files, components, hooks, types)
- Import ordering and organization
- Error handling consistency
- Duplication that warrants extraction
- Anti-patterns (god components, prop drilling, useEffect for derived state)
- TypeScript patterns (discriminated unions, Zod schemas, avoiding any)

## Conditional Reviewers (Based on Tech Stack)

### TypeScript Reviewer
**Trigger:** `tsconfig.json` exists
- Type safety (no implicit any, proper null handling)
- Generic patterns and utility types
- Zod schema integration (z.infer for types)
- Avoiding `any` and `as` assertions
- Proper error typing

### Next.js Reviewer
**Trigger:** `next.config.*` exists
- Server/client component boundary correctness
- Data fetching patterns (server components, server actions, route handlers)
- Caching strategies (revalidate, tags)
- Middleware usage
- Metadata and SEO

### Expo/React Native Reviewer
**Trigger:** `app.json` or `expo` in package.json
- Expo Router file-based routing conventions
- NativeWind styling consistency
- Platform-specific handling (iOS vs Android)
- Native module usage and permissions
- Mobile performance (FlatList/FlashList, Reanimated, image caching)

### Supabase Reviewer
**Trigger:** `supabase/` directory
- RLS policy completeness (every table, every operation)
- Auth pattern correctness
- Client selection (browser client vs server client vs admin client)
- Storage bucket policies
- Realtime subscription security

### Spec Compliance Reviewer
**Trigger:** `docs/prds/` or `docs/tech-specs/` exist
- Requirements coverage (nothing missing from spec)
- Deviation detection (implementation differs from spec)
- Over-engineering (features built beyond spec scope)
- Compliance matrix (requirement → implementation mapping)

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| P1 — Critical | Security vulnerability, data loss risk, crash | Must fix before merge |
| P2 — Important | Bug, performance issue, architectural concern | Should fix before merge |
| P3 — Suggestion | Better pattern available, minor improvement | Consider fixing |
| P4 — Nitpick | Style preference, minor inconsistency | Optional |
