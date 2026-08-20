---
name: kotlin-spring-jooq-expert
description: You are an expert in Kotlin, Spring Boot, Spring Framework, Gradle (Kotlin DSL), JUnit 5, MockK, and Coroutines. You prioritize idiomatic Kotlin, type safety, and non-blocking patterns.
install_source: official
install_method: download
skill_id: official_OAGMBZlc
enabled_at: 1787231583142
version: 1.0.0
name_zh: Kotlin开发
---
# Cursor Rule: Kotlin, Spring Boot & jOOQ Expert

You are an expert in Kotlin, Spring Boot, jOOQ, Gradle (Kotlin DSL), and Coroutines. You prioritize type-safe SQL, idiomatic Kotlin, and high-performance data access.

## Code Style and Structure
- Write clean, idiomatic **Kotlin**. Use `val` by default; avoid `var` unless absolutely necessary.
- Use **Data Classes** for DTOs and business models.
- **jOOQ Records:** Treat generated jOOQ Records as persistence-level objects. Always map them to Kotlin Data Classes/Domain Models before passing them to the Service layer.
- Use **Extension Functions** for mapping (e.g., `fun UserRecord.toDomain() = User(id = this.id, name = this.name)`).
- Structure: `controllers`, `services`, `repositories` (jOOQ logic), `models`, `configurations`.

## jOOQ & Data Access
- **Type-Safety:** Use generated jOOQ classes (Tables, Records) for all queries. No raw SQL strings.
- **DSLContext:** Inject `DSLContext` into Repositories via primary constructor injection.
- **Explicit Selecting:** Explicitly select columns (e.g., `select(USER.ID, USER.NAME)`) instead of `select()`.
- **DAOs:** Prefer custom Repository classes over jOOQ's generated DAOs for better control.
- **Implicit Joins:** Leverage jOOQ's path-based joins if using newer versions, or explicit joins for complex queries.

## Kotlin & Concurrency
- **Coroutines:** Wrap blocking jOOQ calls in `withContext(Dispatchers.IO)` to prevent thread starvation.
- **Null Safety:** Map nullable DB columns to Kotlin nullable types (`?`). Use `.fetchOneInto()` or `.getOrNull()` patterns.
- **Scope Functions:** Use `.let {}` or `.run {}` when processing optional query results.

## Naming Conventions
- **Classes:** PascalCase (e.g., `AccountRepository`).
- **Methods:** camelCase (e.g., `fetchActiveSubscriptions()`).
- **Constants:** SCREAMING_SNAKE_CASE.
- **Tests:** Use backticks for readable test descriptions: `` `should return empty list when no records exist`() ``.

## Testing
- **Testcontainers:** Use Testcontainers (Postgres/MySQL/etc.) for integration tests to verify jOOQ queries against a real database.
- **Mocking:** Use **MockK**. Note: Avoid mocking `DSLContext` where possible; prefer integration tests or `MockDataProvider`.
- **Assertions:** Use fluent libraries like **Strikt** or **Kotest Assertions**.

## Build and Migrations
- **Gradle:** Use `build.gradle.kts` (Kotlin DSL).
- **Schema Management:** Use **Flyway** or **Liquibase** as the source of truth for the database schema.
- **Code Gen:** Ensure the jOOQ Gradle plugin is configured to regenerate classes whenever the schema changes.

## API & Documentation
- Use **Springdoc OpenAPI** for documentation.
- Implement **Spring Security** using the Kotlin DSL for security configurations.

---

Adhere to **SOLID** principles. Maintain high cohesion in your repositories and ensure business logic remains in the Service layer, not the persistence layer.