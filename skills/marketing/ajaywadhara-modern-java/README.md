# modern-java

> Your `build.gradle` says Java 21. Your code still says 2011.
> One skill. Your entire codebase, caught up automatically.

**modern-java** scans your Java project, detects outdated patterns, and transforms them to modern idioms — version-aware, framework-smart, zero configuration. It reads your build file, loads only what's relevant for your Java version, and shows you exactly what changed and why.

```bash
npx skills@1.4.1 add ajaywadhara/modern-java
```

---

## What It Does

| Legacy Pattern | Modern Alternative | Java Since |
|---|---|---|
| `for` loop with filter/map | Stream API | 8 |
| Anonymous inner classes | Lambdas | 8 |
| `null` check chains | `Optional` | 8 |
| 50-line POJO / DTO | `record` | 16 |
| `if (x instanceof Foo) { Foo f = (Foo) x; }` | Pattern matching `instanceof` | 16 |
| `switch` with `break` | Switch expression with `->` | 14 |
| `Executors.newFixedThreadPool(N)` | Virtual threads | 21 |
| `ThreadLocal<T>` | `ScopedValue<T>` | 25 |
| `HttpURLConnection` | `HttpClient` | 11 |
| Multi-line string concatenation | Text blocks | 15 |

---

## Live Examples

### DTO / POJO → Record (Java 16+)

You wrote this once. You've written it a thousand times since.

**Before** — 45 lines, all boilerplate:

```java
// UserResponse.java
public class UserResponse {
    private final Long id;
    private final String email;
    private final String role;
    private final LocalDateTime createdAt;

    public UserResponse(Long id, String email, String role, LocalDateTime createdAt) {
        this.id = id;
        this.email = email;
        this.role = role;
        this.createdAt = createdAt;
    }

    public Long getId() { return id; }
    public String getEmail() { return email; }
    public String getRole() { return role; }
    public LocalDateTime getCreatedAt() { return createdAt; }

    @Override public boolean equals(Object o) { /* 10 lines */ }
    @Override public int hashCode() { /* 5 lines */ }
    @Override public String toString() { /* 5 lines */ }
}
```

**After** — 1 line, all the same guarantees:

```java
// UserResponse.java
public record UserResponse(Long id, String email, String role, LocalDateTime createdAt) {}
```

- Immutable by default
- `equals`, `hashCode`, `toString` generated
- Works with Spring's `@ConstructorBinding`, Jackson, and Quarkus Panache (for DTOs, not entities)

---

### Platform Threads → Virtual Threads (Java 21+)

The old way caps you at the size of your thread pool. The new way scales to millions.

**Before** — 100 threads, 100 concurrent orders max:

```java
// OrderProcessingService.java
public class OrderProcessingService {

    // Max 100 concurrent orders — OS threads are expensive
    private final ExecutorService executor =
        Executors.newFixedThreadPool(100);

    public void processOrders(List<Order> orders) {
        for (Order order : orders) {
            executor.submit(() -> {
                fetchInventory(order);    // I/O: ~50ms blocks a thread
                chargePayment(order);     // I/O: ~80ms blocks a thread
                sendConfirmation(order);  // I/O: ~30ms blocks a thread
            });
        }
    }
}
```

**After** — one virtual thread per task, millions of concurrent orders:

```java
// OrderProcessingService.java
public class OrderProcessingService {

    public void processOrders(List<Order> orders) {
        // Virtual threads park on I/O instead of blocking an OS thread
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            orders.forEach(order ->
                executor.submit(() -> {
                    fetchInventory(order);    // parks, releases carrier thread
                    chargePayment(order);     // parks, releases carrier thread
                    sendConfirmation(order);  // parks, releases carrier thread
                })
            );
        } // structured: waits for all tasks, auto-closes
    }
}
```

> **Result:** Same code shape, same exception handling, same blocking-style readability —
> but now your service handles 10,000+ concurrent orders with a fraction of the memory.

---

## How It Works

1. **Detects your Java version** from `pom.xml`, `build.gradle`, or `gradle/libs.versions.toml`
2. **Loads only relevant features** — Java 8 project? No virtual thread suggestions
3. **Detects framework** (Spring Boot, Quarkus, Micronaut) for framework-specific advice
4. **Scans `.java` files** for legacy patterns using version-appropriate detection rules
5. **Shows BEFORE/AFTER** for every transformation with the minimum Java version required
6. **Generates a modernization report** — files changed, lines saved, patterns found

```
## Modernization Report

Project Version: Java 21
Files Scanned:   47
Patterns Found:  23
Lines Saved:     ~320 (14%)

| File                    | Pattern              | Lines Saved |
|-------------------------|----------------------|-------------|
| UserResponse.java       | DTO → Record         | −44         |
| OrderService.java       | for-loop → Stream    | −12         |
| ApiClient.java          | HttpURLConnection    | −28         |
| TaskExecutor.java       | Platform → Virtual   | −8          |
```

---

## Supported Versions & Frameworks

| Java | Features Loaded |
|------|----------------|
| 8–11 | Lambdas, Streams, Optional, CompletableFuture, `var`, HttpClient |
| 12–17 | Switch expressions, Text blocks, Records, Pattern matching, Sealed classes |
| 18–21 | Virtual threads, Pattern matching switch, Record patterns, Sequenced collections |
| 22–25 | Unnamed variables, Stream Gatherers, ScopedValue, Flexible constructors, Compact source files |

**Framework-aware transformations:**
- **Spring Boot** — `RestClient` over `RestTemplate`, `@ConstructorBinding` with records, virtual thread auto-config
- **Quarkus** — Panache-aware (records for DTOs, not entities), RESTEasy virtual thread support
- **Micronaut** — Records for value objects, reactive runtime integration

---

## Install

```bash
npx skills@1.4.1 add ajaywadhara/modern-java
```

Or place `SKILL.md` in your project root and load it with your AI agent.

**Works with:** Claude Code, Cursor, Cline, and any agent that supports the [Agent Skills](https://skills.sh) standard.

> The `skills` CLI is published by [vercel-labs/skills](https://github.com/vercel-labs/skills).
> Pinning to `@1.4.1` ensures you run a verified version.

---

## Security

This skill contains **only markdown and Java code examples** — no executable scripts, no network calls, no dependencies, and no data collection.

- **Read scope:** Scans `.java` files and build descriptors (`pom.xml`, `build.gradle`, `*.toml`) in the current project
- **Write scope:** Suggests transformations; applies them only when you approve
- **No outbound calls:** The skill itself makes no network requests
- **No secrets accessed:** Does not read environment variables, credentials, or system files

Audited by [Agent Trust Hub](https://skills.sh/audits) · [Socket](https://socket.dev) · [Snyk](https://snyk.io)

---

## Compatibility Notes

- Records require **Java 16+** (preview in 14-15)
- Virtual threads require **Java 21+** (preview in 19-20)
- Sealed classes require **Java 17+** (preview in 15-16)
- Pattern matching switch requires **Java 21+** (preview in 17-20)
- `String templates` (`STR."..."`) — **withdrawn in Java 23**, not recommended

---

*Built on the [Agent Skills](https://skills.sh) open standard. Version-aware from Java 8 to 25.*
