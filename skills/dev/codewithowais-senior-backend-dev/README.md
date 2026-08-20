# 🏗️ Senior Backend Developer — Claude Skill

A Claude Agent Skill that acts as a **Senior Backend Developer** with 12+ years of experience building distributed systems. It covers system architecture, API design, database engineering, and code review across all major backend stacks.

---

## What This Skill Does

When loaded, Claude will:

| Capability | What Claude Produces |
|------------|---------------------|
| **System Architecture** | Mermaid diagrams, ADRs, service boundary definitions |
| **API Design (REST, GraphQL, gRPC)** | Production-ready endpoints, OpenAPI specs, middleware, tests |
| **Database Engineering** | Migration files (up+down), ER diagrams, index strategies, query optimization |
| **Code Review** | Severity-tagged findings (🔴🟡🟢), concrete fixes, prioritized action items |

## Supported Stacks

| Stack | Frameworks | DB Tools |
|-------|-----------|----------|
| **Node.js / TypeScript** | Express, NestJS, Fastify | Prisma, TypeORM |
| **Python** | Django, FastAPI, Flask | SQLAlchemy, Alembic |
| **Java** | Spring Boot | JPA, Flyway, Liquibase |
| **Go** | stdlib, chi, gin | sqlx, pgx, goose |
| **Rust** | Axum, Actix-web | sqlx |

---

## Installation

### Claude.ai

1. Download this repository as a ZIP
2. Go to **Settings → Capabilities → Skills**
3. Click **Upload** and select the ZIP
4. Toggle the skill **ON**

### Claude Code

```bash
# From GitHub plugin marketplace
/plugin marketplace add YOUR_USERNAME/senior-backend-dev
/plugin install senior-backend-dev@YOUR_USERNAME/senior-backend-dev

# Or manual install
git clone https://github.com/YOUR_USERNAME/senior-backend-dev.git
cp -r senior-backend-dev ~/.claude/skills/senior-backend-dev
```

### Claude API

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "custom", "skill_id": "your_skill_id", "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Design a REST API for a multi-tenant SaaS platform"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

---

## File Structure

```
senior-backend-dev/
├── SKILL.md                          # Core skill instructions (required)
├── LICENSE                           # MIT License
├── README.md                         # This file
├── CONTRIBUTING.md                   # Contributor guide
├── references/
│   ├── diagram-patterns.md           # Mermaid diagram templates
│   └── stacks/
│       ├── nodejs.md                 # Node/TS patterns & conventions
│       ├── python.md                 # Python patterns & conventions
│       ├── java.md                   # Java/Spring Boot conventions
│       └── go-rust.md                # Go & Rust conventions
├── templates/
│   └── adr.md                        # Architecture Decision Record template
└── evals/
    └── evals.json                    # 5 test cases for skill evaluation
```

---

## Example Prompts

Try these after installing:

> "Design a microservice architecture for a ride-sharing app handling 50K concurrent users"

> "Review this Express.js controller and tell me what's wrong" *(paste your code)*

> "Build a FastAPI CRUD service for a blog with PostgreSQL, including migrations and tests"

> "Our PostgreSQL query on a 10M row table takes 8 seconds. Here's the query and schema — help me optimize it"

> "Create a Go URL shortener microservice with rate limiting and click analytics"

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick summary:**
- Fork → branch → make changes → PR
- If adding a stack, add a reference file AND an eval
- If changing SKILL.md behavior, run evals first
- Keep code examples idiomatic and production-ready

---

## License

[MIT](LICENSE) — use it, fork it, improve it.

---

## Acknowledgments

Built for the [Anthropic Agent Skills](https://github.com/anthropics/skills) ecosystem. Compatible with [Claude.ai](https://claude.ai), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), and the [Claude API](https://platform.claude.com/docs).
