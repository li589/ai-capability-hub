# Contributing to Senior Backend Developer Skill

Thank you for your interest in contributing! This guide will help you get started.

---

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/senior-backend-dev.git
cd senior-backend-dev
```

### 2. Create a Branch

```bash
git checkout -b feat/add-graphql-patterns
```

### 3. Make Your Changes

See the sections below for guidance on different types of contributions.

### 4. Test Your Changes

Upload the skill folder as a ZIP to Claude.ai (Settings → Capabilities → Skills)
and test with relevant prompts. If you have access to the `skill-creator` tool,
run the evals:

```
Use the skill-creator to run evals for senior-backend-dev
```

### 5. Submit a Pull Request

```bash
git add .
git commit -m "feat: add GraphQL schema-first patterns"
git push origin feat/add-graphql-patterns
```

Open a PR with:
- **What** you changed
- **Why** it improves the skill
- **How** you tested it (paste a sample prompt + output if possible)

---

## Types of Contributions

### Adding a New Tech Stack

1. Create `references/stacks/{stack-name}.md`
2. Include these sections (follow existing files as a template):
   - Project structure diagram
   - Handler/controller pattern with code
   - Error handling pattern with code
   - Repository/data access pattern with code
   - Testing patterns with code
   - Migration example
3. Add the stack to the table in `SKILL.md` under **Tech Stack Guidelines**
4. Add at least one eval in `evals/evals.json`

### Improving Existing Stack Patterns

1. Identify the gap (outdated library, missing pattern, bad practice)
2. Update the relevant file in `references/stacks/`
3. If it changes core behavior, update `SKILL.md` too
4. Test with a prompt that exercises the changed pattern

### Adding New Capability Areas

If you want to add something beyond architecture/API/DB/review (e.g.,
observability, CI/CD, containerization):

1. Add a new section under **Capability Areas** in `SKILL.md`
2. Create a reference file in `references/` if needed
3. Define output standards in the **Output Standards** section
4. Add at least one eval

### Adding Evals

Evals live in `evals/evals.json`. Each eval has:

```json
{
  "id": "eval-XX-descriptive-name",
  "prompt": "The user's request to Claude",
  "expectations": [
    "Specific, objectively gradable expectation"
  ],
  "files": []
}
```

**Good evals are:**
- **Specific** — test one capability area primarily
- **Realistic** — mirror what real engineers actually ask
- **Measurable** — expectations can be objectively graded pass/fail
- **Non-trivial** — a basic prompt that any LLM handles doesn't test the skill

### Fixing Bugs or Typos

Just open a PR — no eval required for typos, formatting fixes, or broken links.

---

## Code Style for Examples

All code examples in reference files must:

- **Compile / pass linting** — don't submit pseudocode
- **Be idiomatic** — follow the language's conventions (gofmt, rustfmt, PEP 8, etc.)
- **Include error handling** — no happy-path-only snippets
- **Use real types** — no `any`, no `Object`, no untyped params
- **Be self-contained** — a reader should understand the pattern without external context

---

## Suggested Contributions

Here are areas we'd love help with:

- [ ] GraphQL-specific patterns (schema design, DataLoader, subscriptions)
- [ ] gRPC `.proto` design patterns and service definitions
- [ ] Event-driven architecture (Kafka, RabbitMQ, NATS patterns)
- [ ] Containerization templates (Dockerfile, docker-compose, K8s manifests)
- [ ] CI/CD pipeline examples (GitHub Actions, GitLab CI)
- [ ] Observability patterns (OpenTelemetry, structured logging, metrics)
- [ ] Caching deep-dive (Redis patterns, cache invalidation strategies)
- [ ] API versioning strategy guide
- [ ] Authentication deep-dive (OAuth2 flows, JWT best practices, RBAC)
- [ ] WebSocket / real-time patterns
- [ ] Message queue patterns (dead letter queues, retry strategies, idempotency)
- [ ] Database replication and sharding patterns
- [ ] Load testing guidance (k6, Locust patterns)

---

## Code of Conduct

Be respectful, constructive, and helpful. We're all here to build better tools.

---

## Questions?

Open an issue with the `question` label and we'll get back to you.
