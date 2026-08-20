# Quarkus Java Backend Playbook

A Claude Code skill that enforces backend Java/Quarkus project standards across microservices.

## What it does

This skill provides comprehensive guidelines for building Java backend microservices with **Quarkus 3.x** and **Java 21**. When activated, Claude Code will follow these standards when writing, modifying, or reviewing your Java backend code.

### Standards enforced

- **Architecture**: Layered architecture (Resource > Service > Repository) with proper package structure
- **Design Patterns**: SOLID, Service Layer, Repository Pattern, DTO Pattern, Builder, Strategy
- **Code Reuse**: Always reuse existing utilities and Panache built-in methods before writing new logic
- **Java 21 Features**: Records, pattern matching, switch expressions, sealed classes, virtual threads, text blocks
- **Dependency Injection**: Constructor injection via Lombok `@AllArgsConstructor` (never `@Inject`)
- **Validation**: Hibernate Validator constraints on DTOs with `@Valid` in Resources
- **Exception Handling**: `BusinessException` + `Problem` response model + `ExceptionMapper` providers
- **DTO Pattern**: Static `fromEntity()`, `toEntity()`, `toDtoList()`, `toEntityList()` conversion methods
- **Lombok**: `@Data`, `@Builder`, `@AllArgsConstructor`, `@NoArgsConstructor` to eliminate boilerplate
- **Testing (TDD)**: `@QuarkusTest`, GIVEN/WHEN/THEN pattern, `@InjectMock`, mock factories
- **File Formatting**: Single trailing newline, 4-space indentation, organized imports
- **Constants**: `private static final` at the top of each class

### Technology stack

Java 21 | Quarkus 3.27.x | Hibernate ORM + Panache | Flyway | SQL Server | Keycloak/OIDC | Lombok | MapStruct | JUnit 5 + Mockito | TestContainers | REST Assured | JaCoCo

## Installation

```bash
npx skills add flaviodotcom/quarkus-java-backend-playbook -g -y
```

Or install manually by copying `SKILL.md` to:

```
~/.claude/skills/quarkus-java-backend-playbook/SKILL.md
```

## When it activates

This skill is automatically used when Claude Code detects you are working with:

- Java backend code with Quarkus
- Panache repositories or Hibernate ORM
- Jakarta EE / JAX-RS resources
- Microservices architecture patterns

## License

MIT License - see [LICENSE](LICENSE) for details.
