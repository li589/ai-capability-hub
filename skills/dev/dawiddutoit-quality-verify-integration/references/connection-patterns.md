# Connection Patterns Reference

Integration patterns for different artifact types.

## LangGraph Nodes

**Files involved:**
- Node definition: `coordination/graph/*_nodes.py`
- Builder: `coordination/graph/builder.py`

**Required connections:**
```python
# In builder.py
from .architecture_nodes import create_architecture_review_node

# Create node
node = await create_architecture_review_node(agent)

# Add to graph
graph.add_node("node_name", node)

# Wire edges
graph.add_conditional_edges("source", routing_fn, {"path": "node_name"})
```

**Verification:**
```bash
grep -n "from.*nodes import" src/temet_run/coordination/graph/builder.py
grep -n "add_node" src/temet_run/coordination/graph/builder.py
```

## Dependency Injection Services

**Files involved:**
- Service: `services/*.py` or `domain/*.py`
- Container: `container.py`

**Required connections:**
```python
# In container.py
from .services.notification import NotificationService

class Container(containers.DeclarativeContainer):
    notification = providers.Singleton(NotificationService)
```

**Verification:**
```bash
grep -n "providers.Singleton\|providers.Factory" src/temet_run/container.py
```

## CLI Commands

**Files involved:**
- Command: `cli/commands/*.py`
- App: `cli/app.py`

**Required connections:**
```python
# In cli/app.py
from .commands.memory import memory_group

app.add_command(memory_group)
```

**Verification:**
```bash
uv run temet-run --help  # Should show command
grep -n "add_command" src/temet_run/cli/app.py
```

## API Endpoints

**Files involved:**
- Route: `api/routes/*.py`
- App: `api/app.py`

**Required connections:**
```python
# In api/app.py
from .routes.health import health_router

app.include_router(health_router)
```

**Verification:**
```bash
grep -n "include_router" src/temet_run/api/app.py
```

## Configuration Fields

**Files involved:**
- Settings: `config/settings.py`
- Consumer: Any file using the config

**Required connections:**
```python
# In settings.py
class Settings(BaseSettings):
    max_retries: int = 3

# In consumer.py
for i in range(settings.max_retries):
    ...
```

**Verification:**
```bash
grep -r "settings\." src/ --include="*.py" | grep -v test
```

## Factory Functions

**Files involved:**
- Factory: `factories/*.py` or inline
- Consumer: Code that calls factory

**Required connections:**
```python
# Factory defined
def create_agent(config: AgentConfig) -> Agent:
    ...

# Factory called somewhere
agent = create_agent(config)
```

**Verification:**
```bash
grep -r "create_agent" src/ --include="*.py" | grep -v "^def "
```

## Event Handlers

**Files involved:**
- Handler: `handlers/*.py`
- Event bus: `events.py` or similar

**Required connections:**
```python
# Handler subscribed
event_bus.subscribe("user_created", on_user_created)
```

**Verification:**
```bash
grep -r "subscribe\|on_event" src/ --include="*.py"
```

## Quick Reference Table

| Artifact | Connection File | Key Pattern |
|----------|----------------|-------------|
| LangGraph Node | builder.py | `add_node()` |
| DI Service | container.py | `providers.Singleton()` |
| CLI Command | cli/app.py | `add_command()` |
| API Endpoint | api/app.py | `include_router()` |
| Config Field | consumer file | `settings.field` |
| Factory | caller file | `create_x()` call |
| Event Handler | event setup | `subscribe()` |
