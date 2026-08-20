# Knowledge Document Format

Each knowledge document is a SKILL.md file with YAML frontmatter. It serves dual purpose: providing structured context about a codebase module, and being discoverable through the skill triggering mechanism (progressive disclosure).

## Frontmatter

```yaml
---
name: knowledge-<domain-path>
description: >
  Covers <what this knowledge provides — the module, its responsibility>.
  Navigate when: <specific task scenarios that should trigger loading>.
  Excludes: <what is NOT covered, with pointers to sibling nodes>.
  Keywords: <comma-separated: module names, class names, function names, technology, common queries>.
---
```

The `description` field is the **sole trigger mechanism** — it determines when the agent
loads this knowledge. Write it as **routing information**, not a summary. The four-part
structure helps the agent make fast recall decisions:

- **Covers**: What context this document provides
- **Navigate when**: Specific task scenarios (e.g., "modifying the auth flow", "adding a
  new payment provider", "debugging token expiry")
- **Excludes**: What's NOT here, with pointers (e.g., "permissions — see rbac/")
- **Keywords**: Module names, class/function names, technology names, error messages

## Document Body Structure

### 1. Module Structure (required)

Opens every knowledge document. Gives the agent spatial orientation.

```markdown
## Module Structure

Brief description of what this module/layer does and its role in the system.

### Directory Layout
- `src/auth/` — Authentication handlers
  - `middleware.py` — JWT validation middleware (L12-L45: core validation logic)
  - `providers/` — OAuth provider implementations
    - `google.py` — Google OAuth2 flow
    - `github.py` — GitHub OAuth flow
- `src/auth/config.py` — Auth configuration and feature flags

### Key Entry Points
- `create_auth_router()` in `src/auth/__init__.py` — Main router factory
- `AuthMiddleware` class in `src/auth/middleware.py` — Per-request authentication
```

### 2. Knowledge Entries (required)

Entries are **one line each**, grouped under their category as a subheading. Source references
go at the end of the line in parentheses. This keeps the document scannable and compact.

```markdown
## Gotchas
- JWT refresh tokens are validated against a blocklist in Redis, not just expiry — missing this causes "valid" tokens to work after logout (`src/auth/jwt.py`)
- The `user.save()` method silently swallows UniqueConstraintError in batch mode; always use `user.save(strict=True)` outside migrations (`src/models/user.py`, `git:a1b2c3d`)
- Config values from `.env` are cached at import time; changes require full restart, not just reload (`src/config/loader.py`)

## Architecture
- Auth module uses strategy pattern — each OAuth provider is a pluggable `AuthProvider` subclass registered in `PROVIDER_REGISTRY` (`src/auth/providers/__init__.py`)
- Request lifecycle: nginx → rate limiter → auth middleware → route handler → serializer; failures at any stage short-circuit to error middleware (`src/middleware/chain.py`)

## Decisions
- Chose Celery over asyncio for background tasks because the team needed visibility into task queues via Flower, and most tasks are I/O-bound DB writes that benefit from prefork workers (`src/tasks/__init__.py`, `git:e4f5g6h`)

## Patterns
- All database queries go through `QueryBuilder` rather than raw ORM calls, enforcing tenant isolation automatically (`src/db/query_builder.py`)

## Conventions
- Test files mirror source structure: `src/auth/jwt.py` → `tests/auth/test_jwt.py`; fixtures live in `tests/conftest.py` per module (`tests/conftest.py`)

## Dependencies
- Redis 7.x required for ACL support used in token blocklist; 6.x silently ignores ACL commands (`requirements.txt`, `src/auth/jwt.py`)

## Security Considerations
- All OAuth tokens are encrypted at rest via `Fernet(settings.TOKEN_KEY)`; rotating the key invalidates every stored token — coordinate with ops (`src/auth/encryption.py`)
- Rate limiting on `/login` is per-IP, not per-account — distributed brute-force from multiple IPs bypasses it; tracked in issue #347 (`src/middleware/rate_limit.py`)

## Performance Characteristics
- Provider registry lookup is O(1) dict access but each provider's `authenticate()` makes 1-2 external HTTP calls; total auth latency is dominated by provider response time, not internal code (`src/auth/providers/base.py`)
```

Each line follows the pattern: `- <insight> (<source>)`

Rules:
- One insight per line — if an entry needs multiple sentences, keep it on one line
- Source in parentheses at the end of the SAME line, not as a separate field or sub-item
- No line numbers in source paths — use file path only (e.g., `src/auth/jwt.py` not `src/auth/jwt.py:12-45`)
- No bold title prefix — write the insight directly, not `**title**: insight`
- Group entries under their category heading as `## <Category>`
- Empty categories can be omitted

**Anti-patterns — do NOT generate these formats:**

```markdown
❌ WRONG: multi-line with "来源" sub-item
- **usePreloadData 的 loading 状态**: 只有当预加载数据不存在时才会触发 loading 状态
  - 来源: `packages/bridge/src/webview/hook.ts:9-24`

❌ WRONG: line numbers in source path
- usePreloadData only triggers loading when no cached data exists (`src/hook.ts:9-24`)

❌ WRONG: bold title prefix
- **Loading state**: usePreloadData only triggers loading when no cached data exists (`src/hook.ts`)

✅ CORRECT: single line, file path only, no prefix
- usePreloadData only triggers loading when preloaded data is absent; cached data returns immediately (`packages/bridge/src/webview/hook.ts`)
```

### 3. Child Nodes (non-leaf nodes only)

```markdown
## Child Knowledge Nodes
- `./auth/SKILL.md` — Authentication & authorization: JWT, OAuth, sessions
- `./database/SKILL.md` — Database layer: schema, migrations, query patterns
```

## Entry Categories

Categories fall into two kinds: **fixed categories** that every knowledge document should
consider, and **emergent categories** that the model discovers from the codebase itself.

### Fixed Categories

These are universal — they apply to virtually every codebase. Always consider them when
scanning a module, and include them when relevant entries exist.

| Category | What it captures | Signal level |
|----------|-----------------|--------------|
| **Gotchas** | Non-obvious behaviors, common mistakes, workarounds | Highest — things that trip people up |
| **Architecture** | Module boundaries, data flow, system design | High — structural understanding |
| **Decisions** | Architectural decisions with rationale (ADR-like) | High — the "why" behind the code |
| **Patterns** | Recurring idioms specific to this codebase | Medium — "how we do things here" |
| **Conventions** | Naming, file organization, code style rules | Medium — consistency guardrails |
| **Dependencies** | External deps, version constraints, integration points | Medium — what's wired to what |

### Emergent Categories

Beyond the fixed set, you should **create new category headings** that capture
domain-specific or module-specific knowledge that doesn't fit neatly into the fixed six.
These emergent categories are where the real value often hides — they reflect what makes
*this particular module* unique.

Examples of emergent categories (these are illustrative, not prescriptive — invent your own
based on what you actually find):

- `## Performance Characteristics` — for modules where latency, throughput, or memory
  footprint are critical (e.g., "Hot path processes 10K events/sec; avoid allocations
  inside the loop")
- `## Security Considerations` — for auth, payment, or data-handling modules
- `## Migration History` — for modules that underwent major refactors, with context on
  what changed and why legacy artifacts remain
- `## Error Handling & Recovery` — for modules with complex failure modes, retry logic,
  or circuit breakers
- `## Concurrency Model` — for modules using threads, async, actors, or locks
- `## Data Flow` — for pipeline or ETL modules where understanding the flow is key
- `## API Contract` — for modules exposing interfaces consumed by other services or clients
- `## State Machine` — for modules with lifecycle states and transitions
- `## Testing Strategy` — for modules with unusual or complex test setups
- `## Platform Differences` — for cross-platform code with OS/browser-specific branches

Guidelines for emergent categories:
- Create one when you find 2+ related insights that don't belong in the fixed categories
- Name it clearly — someone reading the heading should immediately know what's inside
- A single knowledge document might have 0–5 emergent categories; there's no fixed limit
- Emergent categories appear **after** the fixed categories in the document
- If an emergent category grows common across many nodes, it's a signal that it might
  deserve promotion to a project-wide convention (note this in the root SKILL.md)

## Specialized Node Types

Some modules deserve extra sections beyond the standard format. These are not separate
templates — they're **additional sections** added to the standard document when the module
matches certain criteria.

### Component-Like Modules

A module is component-like when it's a shared/base module consumed by 3+ business domains.
Signs: cross-domain imports, extension patterns (subclass, protocol, plugin), naming with
`Base`/`Kit`/`Foundation`/`Utils`/`Common`/`Shared`.

When identified, add these sections after Module Structure and before knowledge entries:

```markdown
## API Surface

### <Protocol / Class Name>
- `methodOrProperty` — one-line description
- `anotherMethod` — one-line description

## Usage Examples

### <Scenario: e.g., "Registering a handler">
` `` typescript
// Minimal correct usage pattern (≤ 10 lines)
// Derived from actual consumer code, not hypothetical
` ``
```

Also add a `## Consumer Analysis` emergent category in the entries section listing top
3-5 consumer modules and their usage patterns. This is mandatory for component-like nodes.

Consumer analysis process:
1. Search for imports of this module across Git-visible codebase files
2. Record top 3-5 consumer modules by import frequency
3. Sample 3-5 consumer call sites for Usage Examples
4. Detect misuse or inconsistency across consumers → record as Gotchas
5. List consumer relationships with most-used APIs

### Cross-Cutting Patterns

A module is cross-cutting when it represents a conditional branching pattern spanning 3+
domains: feature flags, environment switches, A/B tests, regional routing.

When identified, add these sections after Module Structure:

```markdown
## Branching Table

| Dimension | <Branch A> | <Branch B> |
|-----------|-----------|-----------|
| Config loading | <behavior> | <behavior> |
| Cache system | <behavior> | <behavior> |
```

Rules for the Branching Table:
- 4–10 rows, only dimensions where behavior DIFFERS
- Cell contents must be specific, not "different config"
- Fewer than 4 differing dimensions → may not warrant cross-cutting treatment

```markdown
## Affected Scope
- `relative/path/to/module/` — brief impact description (N call sites)
```

Rules for Affected Scope:
- 5–10 most significantly affected modules
- Include relative paths and brief impact descriptions
- Order by significance

Also add a `## Branching Behavior` emergent category in the entries section for
branch-specific rules that affect coding decisions.

## Source Reference Formats

Every entry MUST have a source. This is non-negotiable — unsourced knowledge can't be verified.

**All file paths must be relative to the project root.** Never use absolute paths.
An absolute path like `/Users/someone/project/src/auth/middleware.py` is useless to anyone
on a different machine. Always write `src/auth/middleware.py` instead.

| Format | Example | When to use |
|--------|---------|-------------|
| File path | `src/auth/middleware.py` | Code in a specific file |
| Git commit | `git:abc1234` | Decision captured in commit message |
| Multiple | `src/auth/jwt.py`, `src/auth/config.py` | Cross-file insight |
| External | `url:https://...` | External doc or spec |

**Never include line numbers** in source references (e.g., `src/auth/jwt.py:12-45` is wrong).
Line numbers change frequently and become stale quickly. Use file paths only.

## Updating Existing Knowledge

When updating (not creating fresh), follow these rules:

1. **Check for duplicates** — search existing entries before adding new ones
2. **Update in place** — if the insight exists but the source path changed, update the source reference to a Git-visible path
3. **Mark stale entries** — if a source file was deleted or heavily refactored, verify the knowledge still holds. Remove entries whose facts are no longer true.
4. **Preserve git provenance** — when updating an entry, keep the original source reference and append the new one: `src/old.py` → `src/old.py, src/new.py`
5. **Bump the description** — if new entries shift the knowledge node's scope, update the frontmatter description to improve future recall

## Quality Checklist

- [ ] Every entry ends with a source reference in parentheses pointing to an existing file
- [ ] Entries are grouped by category, with Gotchas listed first
- [ ] Each entry is a single line — concise but complete
- [ ] Fixed categories are considered (include those with relevant entries; omit empty ones)
- [ ] Emergent categories are created for domain-specific insights that don't fit the fixed six
- [ ] The frontmatter description is rich enough for keyword-based recall
- [ ] Module Structure section accurately reflects current directory layout
- [ ] No duplicate entries covering the same insight
- [ ] Child node pointers are present for non-leaf documents
