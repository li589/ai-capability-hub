# Violation Fixes

Quick reference for fixing Clean Architecture layer violations.

## Domain Layer Violations

### Problem: Domain importing from Infrastructure

```python
# ❌ WRONG
from infrastructure.neo4j import Neo4jDriver

class Entity:
    def save(self):
        driver = Neo4jDriver()
        driver.save(self)
```

### Solution: Use repository interface

```python
# ✅ CORRECT - Domain defines interface
from abc import ABC, abstractmethod

class EntityRepository(ABC):
    @abstractmethod
    async def save(self, entity: "Entity") -> ServiceResult[None]:
        pass

# ✅ CORRECT - Infrastructure implements
from domain.repositories import EntityRepository

class Neo4jEntityRepository(EntityRepository):
    async def save(self, entity: Entity) -> ServiceResult[None]:
        # Implementation
        pass
```

## Application Layer Violations

### Problem: Application importing from Interfaces

```python
# ❌ WRONG
from interfaces.mcp.tools import search_code

class SearchService:
    def search(self, query: str):
        return search_code(query)
```

### Solution: Interfaces call Application, not vice versa

```python
# ✅ CORRECT - Application provides service
class SearchService:
    def __init__(self, repository: CodeRepository):
        self.repository = repository

    def search(self, query: str) -> ServiceResult[list]:
        return self.repository.search(query)

# ✅ CORRECT - Interface calls Application
@mcp.tool()
def search_code(query: str):
    service = get_search_service()  # From DI
    return service.search(query)
```

## Interface Layer Violations

### Problem: Interfaces importing Domain directly

```python
# ❌ WRONG
from domain.models import Entity

@mcp.tool()
def get_entity(id: str) -> Entity:
    # Direct domain access
    pass
```

### Solution: Use Application layer

```python
# ✅ CORRECT - Through application
from application.queries import GetEntityQuery

@mcp.tool()
def get_entity(id: str):
    handler = get_entity_handler()  # From DI
    result = handler.handle(GetEntityQuery(id=id))
    return result.unwrap()
```

## Quick Reference

| Violation | Fix |
|-----------|-----|
| Domain → Infrastructure | Create interface in Domain, implement in Infrastructure |
| Application → Interfaces | Reverse direction: Interfaces call Application |
| Interfaces → Domain | Go through Application layer |
| Any → Implementation | Use Dependency Injection with interfaces |

---

**Related:** [layer-rules.md](layer-rules.md), [../SKILL.md](../SKILL.md)
