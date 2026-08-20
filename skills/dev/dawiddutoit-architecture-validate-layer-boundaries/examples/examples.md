# Clean Architecture Layer Boundary Validation Examples

Complete examples showing validation scenarios and expected outcomes.

## Example 1: Successful Validation

**Scenario:** All files respect layer boundaries

**Output:**
```
✅ Clean Architecture Validation: PASSED

Files checked: 15
Violations: 0

All layer boundaries respected.
```

## Example 2: Domain Layer Violation

**Scenario:** Domain model importing from infrastructure

**Violation:**
```python
# src/project_watch_mcp/domain/models/entity.py:12
from infrastructure.neo4j import Neo4jDriver

class File:
    def save_to_db(self):
        driver = Neo4jDriver()
        driver.save(self)
```

**Output:**
```
❌ Clean Architecture Validation: FAILED

Violations found:

1. Domain Layer Violation
   File: src/project_watch_mcp/domain/models/entity.py:12
   Issue: Importing from infrastructure layer
   Code: from infrastructure.neo4j import Neo4jDriver
   Fix: Remove direct infrastructure dependency. Use repository interface instead.

Total Violations: 1
Exit Code: 1
```

**Correct Implementation:**
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

## Example 3: Application Layer Violation

**Scenario:** Application importing from interfaces

**Violation:**
```python
# src/project_watch_mcp/application/services/search.py:8
from interfaces.mcp.tools import search_code

class SearchService:
    async def search(self, query: str):
        return search_code(query)
```

**Output:**
```
❌ Clean Architecture Validation: FAILED

Violations found:

1. Application Layer Violation
   File: src/project_watch_mcp/application/services/search.py:8
   Issue: Importing from interfaces layer
   Code: from interfaces.mcp.tools import search_code
   Fix: Application should not know about interfaces. Use application-level handler instead.

Total Violations: 1
Exit Code: 1
```

**Correct Implementation:**
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

## Example 4: Multiple Violations

**Scenario:** Multiple files with violations across layers

**Output:**
```
❌ Clean Architecture Validation: FAILED

Violations found:

1. Domain Layer Violation
   File: src/project_watch_mcp/domain/models/entity.py:12
   Issue: Importing from infrastructure layer
   Code: from infrastructure.neo4j import Neo4jDriver
   Fix: Remove direct infrastructure dependency. Use repository interface instead.

2. Application Layer Violation
   File: src/project_watch_mcp/application/services/search.py:8
   Issue: Importing from interfaces layer
   Code: from interfaces.mcp.tools import search_code
   Fix: Application should not know about interfaces. Use application-level handler instead.

3. Interface Layer Violation
   File: src/project_watch_mcp/interfaces/mcp/tools.py:5
   Issue: Importing from domain.models directly
   Code: from domain.models import Entity
   Fix: Use application layer queries instead of direct domain access.

Total Violations: 3
Exit Code: 1
```

## Example 5: Using the Validation Script

**Command:**
```bash
./scripts/validate.sh
```

**Output (Success):**
```
Validating Clean Architecture boundaries in: .
✅ Clean Architecture validation: PASSED
```

**Output (Failure):**
```
Validating Clean Architecture boundaries in: .
❌ Domain layer violation in src/project_watch_mcp/domain/models/entity.py
12:from infrastructure.neo4j import Neo4jDriver
❌ Application layer violation in src/project_watch_mcp/application/services/search.py
8:from interfaces.mcp.tools import search_code
❌ Clean Architecture validation: FAILED (2 violations)

For fix patterns, see: .claude/skills/validate-layer-boundaries/references/violation-fixes.md
For examples, see: .claude/skills/validate-layer-boundaries/examples/examples.md
```

## Example 6: Validating Single File

**Command:**
```bash
./scripts/validate.sh src/project_watch_mcp/domain/models/entity.py
```

**Output:**
```
Validating Clean Architecture boundaries in: src/project_watch_mcp/domain/models/entity.py
✅ Clean Architecture validation: PASSED
```

## Example 7: Integration with Pre-Commit Hook

**Hook Configuration:**
```python
# .claude/scripts/pre_flight_validation.py
def validate_architecture():
    result = subprocess.run(
        ["bash", ".claude/skills/validate-layer-boundaries/scripts/validate.sh"],
        capture_output=True
    )
    if result.returncode != 0:
        print("❌ Architecture validation failed")
        print(result.stdout.decode())
        return False
    return True
```

---

**Related:** [../SKILL.md](../SKILL.md), [../references/layer-rules.md](../references/layer-rules.md), [../references/violation-fixes.md](../references/violation-fixes.md)
