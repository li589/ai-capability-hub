# Tags Taxonomy

Hierarchical tag system using `/`-separated format. All tags are in English, lowercase.

## Required Tags

Every distilled document MUST include:

- `distilled` — Base tag. Always present. Enables filtering all distilled knowledge in Obsidian.

## Tag Dimensions

### `scene/*` — Scene Classification

One per document, matching the detected scene:

| Tag | When |
|-----|------|
| `scene/project-wrapup` | Project completion, feature delivery |
| `scene/bug-retrospective` | Bug fix, debugging session |
| `scene/refactoring` | Code restructuring, optimization |
| `scene/tech-learning` | New technology exploration |
| `scene/universal` | General or mixed content |

### `tech/*` — Technology Stack

One or more per document. Use the canonical name:

**Languages**: `tech/python`, `tech/javascript`, `tech/typescript`, `tech/java`, `tech/go`, `tech/rust`, `tech/cpp`, `tech/csharp`, `tech/ruby`, `tech/php`, `tech/swift`, `tech/kotlin`, `tech/shell`

**Frameworks/Libraries**: `tech/react`, `tech/vue`, `tech/angular`, `tech/nextjs`, `tech/django`, `tech/flask`, `tech/fastapi`, `tech/express`, `tech/spring`, `tech/pytorch`, `tech/tensorflow`

**Tools/Platforms**: `tech/docker`, `tech/kubernetes`, `tech/git`, `tech/nginx`, `tech/redis`, `tech/postgresql`, `tech/mongodb`, `tech/aws`, `tech/gcp`, `tech/azure`

This list is open — add new `tech/*` tags as needed. Use the technology's common lowercase name.

### `topic/*` — Problem Domain

One or more per document:

| Tag | Covers |
|-----|--------|
| `topic/architecture` | System design, module structure, design patterns |
| `topic/performance` | Optimization, profiling, caching, latency |
| `topic/concurrency` | Async, threading, race conditions, locks |
| `topic/security` | Auth, encryption, vulnerabilities, input validation |
| `topic/testing` | Unit tests, integration tests, TDD, coverage |
| `topic/deployment` | CI/CD, containers, cloud, infrastructure |
| `topic/api-design` | REST, GraphQL, RPC, versioning, contracts |
| `topic/data-processing` | ETL, pipelines, serialization, databases |
| `topic/error-handling` | Exceptions, retries, graceful degradation |
| `topic/tooling` | IDE, CLI, dev tools, automation |
| `topic/documentation` | Code docs, API docs, knowledge management |

This list is open — add new `topic/*` tags as needed.

### `difficulty/*` — Difficulty Level

Exactly one per document:

| Tag | Criteria |
|-----|----------|
| `difficulty/beginner` | Common patterns, basic concepts, first encounter |
| `difficulty/intermediate` | Requires domain context, non-obvious solutions |
| `difficulty/advanced` | Deep expertise, edge cases, system-level understanding |

## Recommended Tags by Scene

| Scene | Typical `topic/*` Tags |
|-------|----------------------|
| Project Wrap-up | `topic/architecture`, `topic/deployment`, `topic/tooling` |
| Bug Retrospective | `topic/error-handling`, `topic/concurrency`, `topic/testing` |
| Refactoring | `topic/architecture`, `topic/performance`, `topic/testing` |
| Tech Learning | `topic/api-design`, `topic/tooling`, `topic/documentation` |

## Tag Selection Rules

1. Always include `distilled` + exactly one `scene/*` + at least one `tech/*` + at least one `topic/*` + exactly one `difficulty/*`
2. Prefer existing tags over creating new ones
3. When creating a new tag, follow the `dimension/lowercase-name` format
4. Maximum 10 tags per document to avoid noise
