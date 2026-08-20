# Spring Modulith 2.0.x — Reference

**Version**: 2.0.3 | **Spring Boot**: 4.0.x | **Purpose**: Domain-driven modular monolith

---

## Table of Contents
1. [Module Package Structure](#1-module-package-structure)
2. [Gradle Dependency](#2-gradle-dependency)
3. [Module Verification Test](#3-module-verification-test)
4. [@ApplicationModule Annotation](#4-applicationmodule-annotation)
5. [Event-Driven Inter-Module Communication](#5-event-driven-inter-module-communication)
6. [Transactional Event Listeners](#6-transactional-event-listeners)
7. [Module Integration Testing](#7-module-integration-testing)
8. [Generating Documentation](#8-generating-documentation)
9. [Common Pitfalls](#9-common-pitfalls)
10. [DDD & Modulith](#10-ddd--modulith)

---

## 1. Module Package Structure

Each direct sub-package of the application's root package is a **module**.
Internal types live in sub-packages; only the top-level package is public API.

```
com.example.shop/
├── ShopApplication.java          ← root
├── orders/                       ← "orders" module
│   ├── OrderService.java         ← public API
│   ├── OrderController.java      ← public API
│   └── internal/
│       ├── OrderRepository.java  ← internal
│       └── OrderMapper.java      ← internal
├── inventory/                    ← "inventory" module
│   ├── InventoryService.java     ← public API
│   └── internal/
│       └── StockRepository.java  ← internal
└── shared/                       ← shared utilities (no module boundary)
    └── Money.java
```

Modules **cannot** directly import each other's `internal` sub-packages.
Cross-module communication happens through **events** or **public service interfaces**.

---

## 2. Gradle Dependency

```kotlin
// build.gradle.kts
dependencyManagement {
    imports {
        mavenBom("org.springframework.modulith:spring-modulith-bom:2.0.3")
    }
}

dependencies {
    implementation("org.springframework.modulith:spring-modulith-starter-core")
    implementation("org.springframework.modulith:spring-modulith-starter-jpa")      // if using JPA
    testImplementation("org.springframework.modulith:spring-modulith-starter-test")
}
```

---

## 3. Module Verification Test

Run once per CI pipeline — validates that no module violates boundaries.

```java
@Test
void applicationModulesShouldBeCompliant() {
    ApplicationModules.of(ShopApplication.class).verify();
}
```

`verify()` throws if:
- A module imports another module's `internal` package.
- Circular module dependencies exist.

---

## 4. @ApplicationModule Annotation

Fine-tune module visibility and allowed dependencies:

```java
// orders/package-info.java
@ApplicationModule(
    displayName = "Orders",
    allowedDependencies = {"inventory", "shared"}   // only these modules may be imported
)
package com.example.shop.orders;

import org.springframework.modulith.ApplicationModule;
```

Named interfaces (explicit public API within a module):

```java
@NamedInterface("api")
package com.example.shop.orders.api;
```

---

## 5. Event-Driven Inter-Module Communication

Modules communicate via Spring's `ApplicationEventPublisher`. No direct service calls between modules.

**Publisher** (orders module):

```java
record OrderPlacedEvent(Long orderId, String productSku, int quantity) {}

@Service
public class OrderService {

    private final ApplicationEventPublisher events;
    private final JdbcClient jdbc;

    public Order placeOrder(OrderRequest req) {
        Order order = persistOrder(req);
        events.publishEvent(new OrderPlacedEvent(order.id(), req.sku(), req.quantity()));
        return order;
    }
}
```

**Listener** (inventory module):

```java
@Service
public class InventoryService {

    @ApplicationModuleListener   // replaces @EventListener for cross-module events
    public void on(OrderPlacedEvent event) {
        reserveStock(event.productSku(), event.quantity());
    }
}
```

`@ApplicationModuleListener` is async and transactional by default in Modulith.

---

## 6. Transactional Event Listeners

For guaranteed "at-least-once" delivery with persistent event logs:

```kotlin
// build.gradle.kts
implementation("org.springframework.modulith:spring-modulith-events-api")
implementation("org.springframework.modulith:spring-modulith-events-jpa")  // or jdbc, mongodb
```

```java
@Service
public class OrderService {

    @Transactional
    public Order placeOrder(OrderRequest req) {
        Order order = persistOrder(req);
        // Event is stored in the event publication log within the same transaction.
        // Published to listeners after commit — even survives a crash.
        events.publishEvent(new OrderPlacedEvent(order.id(), req.sku(), req.quantity()));
        return order;
    }
}
```

Incomplete publications are retried automatically on next application start.

---

## 7. Module Integration Testing

Test a single module in isolation with only its direct dependencies.

```java
@ApplicationModuleTest          // boots only the "orders" module + stubs
class OrderServiceTest {

    @Autowired OrderService orderService;
    @MockitoBean InventoryService inventoryService;  // stub cross-module dependency

    @Test
    void shouldPlaceOrderAndPublishEvent() {
        var result = orderService.placeOrder(new OrderRequest("SKU-001", 2));
        assertThat(result.id()).isNotNull();
    }
}
```

Bootstrap modes:
- `STANDALONE` — only the annotated module (default)
- `DIRECT_DEPENDENCIES` — module + direct dependencies
- `ALL_DEPENDENCIES` — full transitive graph

```java
@ApplicationModuleTest(mode = BootstrapMode.DIRECT_DEPENDENCIES)
class OrderServiceTest { ... }
```

---

## 8. Generating Documentation

Produces AsciiDoc / PlantUML diagrams of module dependencies:

```java
@Test
void generateModuleDocumentation() throws Exception {
    var modules = ApplicationModules.of(ShopApplication.class);
    new Documenter(modules)
        .writeDocumentation()
        .writeIndividualModulesAsPlantUml();
}
```

Output lands in `target/spring-modulith-docs/` (Maven) or `build/spring-modulith-docs/` (Gradle).

---

## 9. Common Pitfalls

| Pitfall | Remedy |
|--------|--------|
| **Circular module dependencies** | `ApplicationModules.of(...).verify()` fails. Break the cycle: introduce a shared module or move the coupling to events so no module depends on the other. |
| **Exposing internal types in the module API** | Public classes in the module root (e.g. `OrderService`) must not return or accept types from `internal/`. Use DTOs or domain types in the public package only. |
| **Forgetting the verification test in CI** | Add the module verification test (section 3) to your CI pipeline so boundary violations are caught on every commit. |
| **Direct service calls across modules** | One module must not inject another module's service and call it directly. Use `ApplicationEventPublisher` and `@ApplicationModuleListener` (or transactional events) for cross-module communication. |
| **Putting shared DTOs in one module's internal** | Types used in events or APIs consumed by several modules belong in a `shared/` (or similar) package, not in one module's `internal/`. |

---

## 10. DDD & Modulith

**Aggregate:** An aggregate is a cluster of entities and value objects with a **root entity** that enforces invariants. It is loaded and persisted as a unit. In Modulith, a module usually has one or more aggregates; the module’s public service (e.g. `OrderService`) orchestrates the aggregate: it loads the root via a repository, mutates it, and saves. Example: `Order` as aggregate root; `OrderService.placeOrder(...)` loads or creates an `Order`, applies domain logic, calls `OrderRepository.save(order)`, and publishes events. The repository interface lives in the module API; the implementation (JdbcClient or JPA) lives in `internal/`.

**Domain repository:** A **domain repository** is an interface that exposes only domain operations (e.g. `save(Order)`, `findById(OrderId)`), without infrastructure details. In Spring terms, that interface is the **port**; the implementation in `internal/` (using JdbcClient, JPA, etc.) is the **adapter**. The repository you already use for the module (e.g. `OrderRepository`) acts as the domain repository if it only exposes domain-centric methods and returns domain types or optionals.

**Domain events vs application events:** A **domain event** is something that happened in the domain (e.g. “OrderPlaced”). An **application event** is the mechanism: you publish with `ApplicationEventPublisher` and other modules listen with `@ApplicationModuleListener`. In practice with Modulith, the events you publish between modules are application events that typically **represent** domain events of the publishing module. The payload (e.g. `OrderPlacedEvent`) carries the domain data. Section 5 (Event-Driven Inter-Module Communication) and section 6 (Transactional Event Listeners) describe how to publish and consume these; here we only distinguish: domain event = meaning; application event = Spring’s delivery mechanism.
