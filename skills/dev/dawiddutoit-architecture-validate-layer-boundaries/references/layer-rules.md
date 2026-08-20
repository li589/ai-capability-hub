# Clean Architecture Layer Rules

## Complete Dependency Matrix

| Layer          | Can Import From      | Cannot Import From                                | Reason                                 |
|----------------|----------------------|---------------------------------------------------|----------------------------------------|
| Domain         | Domain only          | Application, Infrastructure, Interfaces, External | Pure business logic                    |
| Application    | Domain, Application  | Interfaces, External (except frameworks)          | Orchestrates domain                    |
| Infrastructure | Any layer + External | N/A                                               | Connects to external systems           |
| Interfaces     | Application          | Domain, Infrastructure directly                   | Entry points use application use cases |

## Detailed Rules by Layer

### Domain Layer

**Allowed:**
```python
# ✅ Domain imports
from your_project.domain.models import Entity
from your_project.domain.values import Identity
from your_project.domain.repositories import CodeRepository  # Interface only

# ✅ Standard library
from dataclasses import dataclass
from typing import Optional
```

**Forbidden:**
```python
# ❌ Application imports
from your_project.application.services import SearchService

# ❌ Infrastructure imports
from your_project.infrastructure.neo4j import Neo4jDriver

# ❌ Interface imports
from your_project.interfaces.mcp import search_code

# ❌ External dependencies
from neo4j import AsyncGraphDatabase
```

### Application Layer

**Allowed:**
```python
# ✅ Domain imports
from your_project.domain.models import File, Entity

# ✅ Application imports
from your_project.application.commands import IndexFileCommand

# ✅ Dependency interfaces (injected)
from your_project.domain.repositories import CodeRepository
```

**Forbidden:**
```python
# ❌ Interface imports
from your_project.interfaces.mcp.tools import search_code

# ❌ Direct infrastructure imports
from your_project.infrastructure.neo4j.repositories import Neo4jCodeRepository
```

### Infrastructure Layer

**Allowed:**
```python
# ✅ Everything (outermost layer)
from your_project.domain.repositories import CodeRepository  # Implementing
from neo4j import AsyncGraphDatabase  # External dependency
from your_project.application.services import SearchService  # If needed
```

### Interfaces Layer

**Allowed:**
```python
# ✅ Application use cases
from your_project.application.queries import SearchCodeQuery
from your_project.application.handlers import SearchHandler

# ✅ Dependency injection (container)
from your_project.infrastructure.container import get_container
```

**Forbidden:**
```python
# ❌ Direct domain imports
from your_project.domain.models import Entity  # Use application layer

# ❌ Direct infrastructure imports
from your_project.infrastructure.neo4j import Neo4jDriver  # Use DI
```

## Exception Cases

### Domain Repository Interfaces

Domain can define repository interfaces (abstractions):
```python
# ✅ ALLOWED in domain
from abc import ABC, abstractmethod
from your_project.domain.models import File

class CodeRepository(ABC):
    @abstractmethod
    async def save(self, file: File) -> ServiceResult[None]:
        pass
```

Infrastructure implements these:
```python
# ✅ ALLOWED in infrastructure
from your_project.domain.repositories import CodeRepository
from neo4j import AsyncGraphDatabase

class Neo4jCodeRepository(CodeRepository):
    async def save(self, file: File) -> ServiceResult[None]:
        # Implementation
        pass
```

### Dependency Injection

Application receives dependencies through constructor:
```python
# ✅ CORRECT: Dependency injection
class SearchService:
    def __init__(self, repository: CodeRepository):  # Interface type
        self.repository = repository  # Actual implementation injected by container
```

## Common Violations & Fixes

### Violation 1: Domain Importing Infrastructure

**BAD:**
```python
from infrastructure.neo4j import Neo4jDriver

class File:
    def save_to_db(self):
        driver = Neo4jDriver()
        driver.save(self)
```

**FIX:**
```python
# Domain model should be pure, no persistence logic
@dataclass
class File:
    path: str
    content: str

# Persistence handled by infrastructure:
class Neo4jFileRepository(FileRepository):
    async def save(self, file: File) -> ServiceResult[None]:
        # Infrastructure handles persistence
        pass
```

### Violation 2: Application Importing Interfaces

**BAD:**
```python
from interfaces.mcp.tools import search_code

class SearchService:
    async def search(self, query: str):
        return search_code(query)
```

**FIX:**
```python
# Application service focuses on use case logic
class SearchService:
    def __init__(self, repository: CodeRepository):
        self.repository = repository

    async def search(self, query: str) -> ServiceResult[list[SearchResult]]:
        results = await self.repository.search(query)
        return results

# Interface layer calls application:
@mcp.tool()
async def search_code(query: str):
    handler = get_search_handler()
    return await handler.handle(SearchCodeQuery(query=query))
```

### Violation 3: Interfaces Importing Domain Directly

**BAD:**
```python
from domain.models import Entity

@mcp.tool()
async def get_entity(entity_id: str) -> Entity:
    # Direct domain manipulation
    pass
```

**FIX:**
```python
from application.queries import GetEntityQuery

@mcp.tool()
async def get_entity(entity_id: str):
    handler = get_entity_handler()
    result = await handler.handle(GetEntityQuery(entity_id=entity_id))
    return result.unwrap()
```

---

**Related:** [../SKILL.md](../SKILL.md), [violation-fixes.md](violation-fixes.md)
