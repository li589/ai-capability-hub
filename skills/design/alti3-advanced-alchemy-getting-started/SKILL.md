---
name: advanced-alchemy-getting-started
description: Set up Advanced Alchemy in a new or existing Python service, including package installation, sync or async SQLAlchemy config selection, first model and repository wiring, and framework selection for Litestar, FastAPI, Flask, or standalone SQLAlchemy. Use when bootstrapping Advanced Alchemy, validating prerequisites, or choosing the initial integration shape. Do not use for detailed framework-specific implementation that belongs in the dedicated integration skills.
install_source: official
install_method: download
skill_id: official_6OSNd9V1
enabled_at: 1787231606722
version: 1.0.0
name_zh: Started开发
---

# Getting Started

## Execution Workflow

1. Confirm prerequisites: Python 3.9+, SQLAlchemy 2.x, and whether the project needs sync or async database access.
2. Install `advanced-alchemy`, or `advanced-alchemy[cli]` if database migration commands are required.
3. Choose the correct config pair: `SQLAlchemyAsyncConfig` plus `AsyncSessionConfig` or `SQLAlchemySyncConfig` plus `SyncSessionConfig`.
4. Start with one model, one repository, and one service before wiring framework-specific plugins or middleware.
5. Decide early whether the app will use Litestar, FastAPI, Flask, or standalone SQLAlchemy patterns.

## Implementation Rules

- Prefer the smallest viable setup before adding service layers, framework helpers, or multiple binds.
- Keep session configuration explicit, especially `expire_on_commit=False` in request-driven applications.
- Choose sync versus async once per integration boundary and avoid mixing styles casually.
- Keep the first CRUD path runnable end-to-end before introducing migrations, seeding, or custom types.

## Example Pattern

```python
from advanced_alchemy.config import AsyncSessionConfig, SQLAlchemyAsyncConfig

alchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///app.db",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    create_all=True,
)
```

## Validation Checklist

- Confirm the selected config class matches the driver and execution style.
- Confirm metadata creation or migrations can see the same models as runtime code.
- Confirm a repository or service can open a session and perform one basic read or write.
- Confirm framework integration is deferred until the underlying SQLAlchemy setup works.

## Cross-Skill Handoffs

- Use `advanced-alchemy-modeling` for base classes, mixins, and relationships.
- Use `advanced-alchemy-repositories` and `advanced-alchemy-services` once CRUD is working.
- Use `advanced-alchemy-litestar`, `advanced-alchemy-fastapi`, or `advanced-alchemy-flask` for framework wiring.
- Use `advanced-alchemy-cli` and `advanced-alchemy-database-seeding` after the base setup is stable.

## Advanced Alchemy References

- https://github.com/litestar-org/advanced-alchemy/blob/main/README.md
- https://advanced-alchemy.litestar.dev/latest/getting-started.html
- https://advanced-alchemy.litestar.dev/latest/usage/index.html
