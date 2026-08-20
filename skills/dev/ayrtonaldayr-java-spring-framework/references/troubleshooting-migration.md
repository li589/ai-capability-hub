# Troubleshooting & Migration — Spring Boot 4 / Framework 7

Quick fixes for common errors and a short checklist for migrating from Boot 3 to Boot 4.

---

## Table of Contents

1. [Common errors](#1-common-errors)
2. [Boot 3 → 4 migration checklist](#2-boot-3--4-migration-checklist)

---

## 1. Common errors

### javax vs jakarta

**Symptom:** Compilation errors like `package javax.servlet does not exist`, `javax.persistence` not found, or similar for `javax.*`.

**Cause:** Spring Boot 4 and Spring Framework 7 use **Jakarta EE 11**. All `javax.*` namespaces were replaced by `jakarta.*`.

**Fix:**

- Replace imports: `javax.servlet.*` → `jakarta.servlet.*`, `javax.persistence.*` → `jakarta.persistence.*`, `javax.validation.*` → `jakarta.validation.*`, etc.
- Ensure dependencies use Jakarta. Spring Boot 4 BOM already brings Jakarta-based starters. Third-party libs must be Jakarta-compatible (e.g. Hibernate 7.x, Bean Validation 3.x, Servlet API 6.x).
- Search the project for `javax.` and replace with `jakarta.` where applicable.

---

### RestTemplate not found or deprecated

**Symptom:** `RestTemplate` cannot be resolved, or IDE/compiler warns it is deprecated.

**Cause:** In Spring Framework 6+, `RestTemplate` is in maintenance mode. Spring 7 promotes `RestClient` for synchronous HTTP.

**Fix:**

- Add dependency (usually already present with `spring-boot-starter-web`): `RestClient` is in `spring-web`.
- Replace usage:

```java
// Before
RestTemplate rest = new RestTemplate();
MyDto dto = rest.getForObject(url, MyDto.class);

// After (Spring 7)
RestClient rest = RestClient.create();
MyDto dto = rest.get().uri(url).retrieve().body(MyDto.class);
```

For declarative clients, use `HttpServiceProxyFactory` + interface. See `references/spring-framework-7.md`.

---

### Null-safety: JSR-305 vs JSpecify

**Symptom:** Warnings or errors about `@Nullable` / `@NonNull` (e.g. wrong package or conflicting annotations).

**Cause:** Spring 7 aligns with **JSpecify** (`org.jspecify.annotations`). Legacy JSR-305 (`javax.annotation` or `org.checkerframework`) is not the standard for Spring 7.

**Fix:**

- Remove JSR-305 / Checker Framework null annotations from dependencies if possible.
- Add JSpecify and use it consistently:

```kotlin
implementation("org.jspecify:jspecify:1.0.0")
```

```java
import org.jspecify.annotations.Nullable;
import org.jspecify.annotations.NonNull;
import org.jspecify.annotations.NullMarked;
```

- Annotate packages or types with `@NullMarked` where you want strict null checking. Replace `javax.annotation.Nullable` with `org.jspecify.annotations.Nullable`, etc.

---

### Native image: reflection or classpath errors

**Symptom:** GraalVM native build fails with "Class not found", "Reflection without registration", or similar.

**Cause:** Native images need explicit metadata for reflection, resources, and dynamic proxies. Spring Boot AOT helps but not all code paths are covered.

**Fix:**

- Prefer **functional bean registration** instead of classpath scanning where possible. Use `ApplicationContextInitializer` or `BeanDefinitionRegistryPostProcessor` to register beans programmatically.
- For DTOs or types used in JSON/serialization, register reflection:

```java
@RegisterReflectionForBinding({MyDto.class, OtherDto.class})
@Configuration(proxyBeanMethods = false)
public class NativeHintsConfig {}
```

- Add GraalVM reachability metadata for third-party libraries if needed (e.g. `native-image.properties` or library-specific hints). Check [GraalVM Native Image documentation](https://www.graalvm.org/latest/reference-manual/native-image/) and Spring Boot’s native support.
- Ensure you are not loading classes only by name (e.g. `Class.forName`) without registering them for reflection.

---

## 2. Boot 3 → 4 migration checklist

Use this as a short guide. For authoritative steps, refer to the official [Spring Boot 4 release notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes) and upgrade guides.

| Step | Action |
|------|--------|
| **Java** | Use Java 17 minimum; **Java 21 or 25** recommended. |
| **BOM** | Update parent or BOM to Spring Boot **4.0.x** (e.g. `4.0.3`). |
| **javax → jakarta** | Replace all `javax.*` imports and dependencies with `jakarta.*` (servlet, persistence, validation, etc.). |
| **Dependencies** | Align with Boot 4: Jackson **3.x**, JPA/Hibernate **3.2 / 7.x**, Bean Validation **3.1**, Spring Framework **7.0.x**. Remove or upgrade any lib that still depends on `javax.*` or old versions. |
| **RestTemplate** | Migrate to **RestClient** (or WebClient for reactive). See `references/spring-framework-7.md`. |
| **Null annotations** | Migrate to **JSpecify** (`org.jspecify`) if you use null-safety annotations. |
| **Security** | Spring Security 7 uses **lambda DSL** only. Update `SecurityFilterChain` and related config to lambda style. See `references/spring-security-7.md`. |
| **Optional: Virtual threads** | Enable with `spring.threads.virtual.enabled: true` in `application.yaml` for eligible workloads. |
| **Optional: Java 25 features** | For Structured Concurrency or Scoped Values, enable `--enable-preview` in compile and run; use Boot 4 + Java 25. See `references/spring-boot-4.md`. |
| **Tests** | Run full test suite; fix any failures due to API changes (e.g. `RestTestClient` instead of `TestRestTemplate` where applicable). Use **Testcontainers** for integration tests if needed. See `references/spring-boot-4.md` Testing section. |

After migration, verify actuator endpoints, security rules, and database access. For deeper issues, load the appropriate reference file (e.g. `spring-security-7.md`, `spring-framework-7.md`, `spring-boot-4.md`) as indicated in the skill’s Reference Files table.
