# Spring Boot 4.0.x — Feature Reference

**Version**: 4.0.3 (Stable) | **Framework**: Spring 7.0.x | **Java baseline**: 17 (25 recommended)

---

## Table of Contents
1. [Platform Requirements](#1-platform-requirements)
2. [Auto-Configuration Changes](#2-auto-configuration-changes)
3. [Testing — @SpringBootTest & Slices](#3-testing--springboottest--slices)
4. [Actuator & Observability](#4-actuator--observability)
5. [GraalVM Native Image](#5-graalvm-native-image)
6. [Virtual Threads (Project Loom)](#6-virtual-threads-project-loom)
7. [Structured Concurrency (Java 25)](#7-structured-concurrency-java-25)
8. [Scoped Values (Java 25)](#8-scoped-values-java-25)
9. [Docker Compose Support](#9-docker-compose-support)
10. [Spring Security 7 Basics](#10-spring-security-7-basics)
11. [Reactive Stack (R2DBC + WebFlux)](#11-reactive-stack-r2dbc--webflux)
12. [Rate Limiting](#12-rate-limiting)
13. [Resources & Performance](#13-resources--performance)
14. [API Documentation (OpenAPI / springdoc)](#14-api-documentation-openapi--springdoc)
15. [Scheduling](#15-scheduling)

---

## 1. Platform Requirements

| Component | Version |
|---|---|
| Java (minimum) | 17 |
| Java (recommended) | 25 |
| GraalVM | 24+ |
| Spring Framework | 7.0.x |
| Jakarta EE | 11 |
| Servlet | 6.1 |
| JPA (Hibernate ORM) | 3.2 / 7.0 |
| Bean Validation | 3.1 |
| Jackson | 3.x |
| Kotlin | 2.2 |

---

## 2. Auto-Configuration Changes

### Functional Bean Registration (Native-Friendly)

Avoid `@ComponentScan` when targeting GraalVM. Use functional registration in `ApplicationContext` initialization:

```java
@SpringBootApplication(proxyBeanMethods = false)
public class Application {

    public static void main(String[] args) {
        new SpringApplicationBuilder(Application.class)
            .initializers(ctx -> {
                ctx.registerBean(UserService.class, UserServiceImpl::new);
                ctx.registerBean(UserRepository.class, UserRepositoryImpl::new);
            })
            .run(args);
    }
}
```

### Condition-Based Auto-Configuration

```java
@AutoConfiguration
@ConditionalOnClass(DataSource.class)
@ConditionalOnMissingBean(JdbcClient.class)
public class JdbcClientAutoConfiguration {

    @Bean
    JdbcClient jdbcClient(DataSource dataSource) {
        return JdbcClient.create(dataSource);
    }
}
```

---

## 3. Testing — @SpringBootTest & Slices

### Full Context Test

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class ApplicationIntegrationTest {

    @Autowired RestTestClient client;

    @Test
    void healthEndpointIsUp() {
        client.get().uri("/actuator/health")
              .exchange().expectStatus().isOk();
    }
}
```

### Web Layer Slice

```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {

    @Autowired MockMvc mvc;
    @MockitoBean ProductService productService;

    @Test
    void shouldReturn200() throws Exception {
        given(productService.findAll()).willReturn(List.of(new Product(1L, "Widget")));
        mvc.perform(get("/api/products"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$[0].name").value("Widget"));
    }
}
```

### Data Layer Slice

```java
@DataJpaTest
class UserRepositoryTest {

    @Autowired UserRepository repository;

    @Test
    void shouldPersistUser() {
        User saved = repository.save(new User("Alice", "alice@example.com"));
        assertThat(saved.id()).isNotNull();
    }
}
```

### Testcontainers (integration tests)

For full integration tests against a real database, use **Testcontainers**. Prefer this when testing repository logic, transactions, or schema; use `@MockBean` for unit/slice tests where the focus is the controller or service in isolation.

```kotlin
// build.gradle.kts
testImplementation("org.springframework.boot:spring-boot-testcontainers")
testImplementation("org.testcontainers:postgresql")
testImplementation("org.testcontainers:junit-jupiter")
```

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Testcontainers
class OrderRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17")
        .withDatabaseName("testdb").withUsername("test").withPassword("test");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired OrderRepository repository;

    @Test
    void shouldFindOrdersByUserId() {
        // real DB; no mocks
        List<Order> orders = repository.findByUserId("user-1");
        assertThat(orders).isNotEmpty();
    }
}
```

**When to use @MockBean vs Testcontainers:** Use `@MockBean` in `@WebMvcTest` or `@DataJpaTest` when you want fast, isolated tests. Use Testcontainers when you need real DB/network behavior (transactions, constraints, SQL).

---

## 4. Actuator & Observability

Spring Boot 4 ships first-class **Micrometer Tracing + OpenTelemetry** support.

### Endpoint exposure (secure by default)

Expose only what you need. In production, prefer `health` and `info` for public checks; restrict `metrics`, `prometheus`, and `traces` to an internal network or secure endpoint (e.g. via Spring Security).

```yaml
# application.yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,traces   # restrict in prod
      base-path: /actuator
  endpoint:
    health:
      show-details: when-authorized   # or "never" in prod
  tracing:
    sampling:
      probability: 1.0
  otlp:
    metrics:
      export:
        url: http://otel-collector:4318/v1/metrics
    tracing:
      endpoint: http://otel-collector:4318/v1/traces
```

Protect actuator in Security 7: allow `health`/`info` for load balancers, require authentication for `metrics`/`prometheus`/`traces`. See `references/spring-security-7.md`.

### Health groups (readiness / liveness)

Customize health groups for Kubernetes or load balancers. Example: a custom "readiness" group that includes DB and a custom indicator:

```yaml
management:
  endpoint:
    health:
      show-details: when-authorized
  health:
    livenessstate:
      enabled: true
    readinessstate:
      enabled: true
    db:
      enabled: true
    group:
      readiness:
        include: readinessState,db
      liveness:
        include: livenessState
```

Expose only the group endpoints (e.g. `/actuator/health/readiness`, `/actuator/health/liveness`) in Security 7 for k8s probes.

### Dependencies (Micrometer + OTEL)

```kotlin
// build.gradle.kts
implementation("io.micrometer:micrometer-tracing-bridge-otel")
implementation("io.opentelemetry:opentelemetry-exporter-otlp")
```

### Custom span (Tracer)

```java
@Service
public class OrderService {

    private final Tracer tracer;

    @Observed(name = "order.process", contextualName = "Processing order")
    public Order process(OrderRequest request) {
        Span span = tracer.nextSpan().name("validate").start();
        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            validate(request);
        } finally {
            span.end();
        }
        return persist(request);
    }
}
```

---

## 5. GraalVM Native Image

```kotlin
// build.gradle.kts
plugins {
    id("org.graalvm.buildtools.native") version "0.10.4"
}

graalvmNative {
    binaries {
        named("main") {
            imageName.set("app")
            buildArgs.add("--enable-preview")
        }
    }
}
```

Build native image:

```bash
./gradlew nativeCompile
./build/native/nativeCompile/app
```

**AOT hints** when reflection is unavoidable:

```java
@RegisterReflectionForBinding(MyDto.class)
@Configuration(proxyBeanMethods = false)
public class NativeHintsConfig {}
```

---

## 6. Virtual Threads (Project Loom)

Enable via single property — no code changes needed for existing Spring MVC apps:

```yaml
# application.yaml
spring:
  threads:
    virtual:
      enabled: true
```

Programmatic usage:

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> callExternalService());
}
```

---

## 7. Structured Concurrency (Java 25)

Use `StructuredTaskScope` for fan-out patterns with lifecycle guarantees.

```java
import java.util.concurrent.StructuredTaskScope;

@Service
public class DashboardService {

    public Dashboard loadDashboard(String userId) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {

            var orders   = scope.fork(() -> orderService.findByUser(userId));
            var profile  = scope.fork(() -> profileService.find(userId));
            var payments = scope.fork(() -> paymentService.findByUser(userId));

            scope.join().throwIfFailed();

            return new Dashboard(profile.get(), orders.get(), payments.get());
        }
    }
}
```

---

## 8. Scoped Values (Java 25)

`ScopedValue` replaces `ThreadLocal` for context propagation in virtual threads.

```java
public final class RequestContext {
    public static final ScopedValue<String> TENANT_ID = ScopedValue.newInstance();
    public static final ScopedValue<User>   CURRENT_USER = ScopedValue.newInstance();
}

// Set in a filter
ScopedValue.where(RequestContext.TENANT_ID, tenantId)
           .where(RequestContext.CURRENT_USER, user)
           .run(() -> filterChain.doFilter(request, response));

// Read anywhere in the call stack
String tenant = RequestContext.TENANT_ID.get();
```

---

## 9. Docker Compose Support

Spring Boot 4 auto-detects `compose.yaml` and starts services before the application.

```yaml
# compose.yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
    ports: ["5432:5432"]
  redis:
    image: redis:8
    ports: ["6379:6379"]
```

```yaml
# application.yaml
spring:
  docker:
    compose:
      enabled: true
      lifecycle-management: start-and-stop
```

No manual connection properties needed — Boot auto-configures `DataSource` and `RedisTemplate`.

---

## 10. Spring Security 7 Basics

Spring Security 7 uses **lambda DSL** only for `SecurityFilterChain` and related config. Minimal example:

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> jwt.decoder(jwtDecoder())))
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .build();
    }

    @Bean
    JwtDecoder jwtDecoder() {
        return NimbusJwtDecoder.withJwkSetUri("https://auth.example.com/.well-known/jwks.json").build();
    }
}
```

For **OAuth2 Resource Server (JWT)**, **method security (`@PreAuthorize`)**, and **CORS**, load `references/spring-security-7.md`.

---

## 11. Reactive Stack (R2DBC + WebFlux)

Choose the reactive stack when you need non-blocking I/O end-to-end (high concurrency, streaming, or integration with reactive drivers). For typical CRUD APIs with blocking JDBC/JPA, prefer **Spring MVC + virtual threads** (section 6).

### Dependencies

```kotlin
// build.gradle.kts — replace or add to starters
implementation("org.springframework.boot:spring-boot-starter-webflux")
implementation("org.springframework.boot:spring-boot-starter-data-r2dbc")
runtimeOnly("org.postgresql:r2dbc-postgresql")
```

### Main application

Use `Netty` as the default server (Boot chooses it when `spring-boot-starter-webflux` is on the classpath and `spring-boot-starter-web` is not).

### R2DBC repositories and WebFlux controllers

Define reactive repositories (`ReactiveCrudRepository`) and inject them into `@RestController` or handler functions. Use `ServerWebExchange`, `Mono`, and `Flux` for reactive types. For **RestClient** in a reactive app, use the reactive variant and streaming; see `references/spring-framework-7.md` (Streaming Support) for alignment with Spring 7 APIs.

---

## 12. Rate Limiting

**Concurrency vs time-based:** For **limiting concurrent calls per method**, use Spring 7’s built-in `@ConcurrencyLimit(maxConcurrentCalls = N)` — see `references/spring-framework-7.md` (Resilience Annotations). For **rate limiting by time window** (e.g. 100 requests per minute per IP or per user), use an in-app filter/interceptor with a token-bucket implementation or a gateway.

### Time-based rate limit (in application)

Use **Bucket4j** (token bucket) with a key per client (e.g. IP or authenticated user). Apply it in a `Filter` or `HandlerInterceptor` and return `429 Too Many Requests` when the bucket is exhausted.

**Dependency:**

```kotlin
// build.gradle.kts
implementation("com.bucket4j:bucket4j-core:8.10.1")
```

**Example: filter keyed by IP**

```java
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
@Order(1)
public class RateLimitFilter extends OncePerRequestFilter {

    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();
    private static final int CAPACITY = 100;
    private static final Duration REFILL_DURATION = Duration.ofMinutes(1);

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String key = clientKey(request); // e.g. request.getRemoteAddr() or principal name
        Bucket bucket = buckets.computeIfAbsent(key, k -> newBucket());
        if (bucket.tryConsume(1)) {
            filterChain.doFilter(request, response);
        } else {
            response.setStatus(HttpServletResponse.SC_TOO_MANY_REQUESTS);
            response.getWriter().write("Rate limit exceeded");
        }
    }

    private static String clientKey(HttpServletRequest request) {
        return request.getRemoteAddr();
    }

    private static Bucket newBucket() {
        Bandwidth limit = Bandwidth.classic(CAPACITY, Refill.greedy(CAPACITY, REFILL_DURATION));
        return Bucket.builder().addLimit(limit).build();
    }
}
```

For **per-user** limits, use a key derived from `SecurityContextHolder.getContext().getAuthentication()` (e.g. principal name) and exempt unauthenticated or health endpoints from the filter if needed.

**When to use which:** Use `@ConcurrencyLimit` to cap concurrent executions of a specific method. Use a filter with Bucket4j (or similar) for API-level limits per time window (per IP or per user). If traffic is fronted by **Spring Cloud Gateway**, rate limiting can also be implemented at the edge; that is outside the scope of this reference.

---

## 13. Resources & Performance

### Connection pools (HikariCP, R2DBC)

**HikariCP (blocking JDBC)** — Spring Boot configures it by default. Tune in `application.yaml`:

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
```

See [Spring Boot Data Access](https://docs.spring.io/spring-boot/docs/current/reference/html/data.html#data.sql.datasource.hikari) for all options.

**R2DBC** — For reactive apps, configure the connection pool similarly (e.g. `spring.r2dbc.pool.*`). DB health is included in health groups (section 4); use readiness to avoid sending traffic to instances that cannot get a connection.

### Metrics for resources

Actuator exposes **HikariCP** metrics (e.g. `hikaricp.connections.active`, `hikaricp.connections.idle`, `hikaricp.connections.pending`). Use these in Prometheus/Grafana to size pools and alert on exhaustion. R2DBC pool metrics follow a similar pattern when the reactive stack is used.

### Caching

Use **Spring Cache** with **Caffeine** for in-process caching. Reduces repeated work and database load.

**Dependencies:**

```kotlin
// build.gradle.kts
implementation("org.springframework.boot:spring-boot-starter-cache")
implementation("com.github.ben-manes.caffeine:caffeine")
```

**Enable and configure:**

```java
@SpringBootApplication
@EnableCaching
public class Application { ... }
```

```yaml
# application.yaml
spring:
  cache:
    cache-names: products,users
    caffeine:
      spec: maximumSize=1000,expireAfterWrite=300s
```

**Usage:**

```java
@Service
public class ProductService {

    @Cacheable(cacheNames = "products", key = "#id")
    public Product findById(Long id) {
        return productRepository.findById(id).orElseThrow();
    }
}
```

Use short TTLs or size limits to avoid stale or unbounded caches.

### Performance tuning (summary)

- **Virtual threads** (section 6): Enable for high concurrency with blocking I/O; no need to size a large thread pool.
- **Pool sizing:** Set HikariCP (or R2DBC pool) size based on observed metrics (connections in use, pending); avoid over-provisioning.
- **N+1:** Avoid N+1 queries in JPA (e.g. `@EntityGraph`, fetch joins, or DTO projections) so a single request does not open many statements.
- **Observability:** Use Actuator/Prometheus and traces (section 4) to find bottlenecks (slow endpoints, DB, or external calls) and tune accordingly. No JVM-level tuning (heap, GC) is covered here.

---

## 14. API Documentation (OpenAPI / springdoc)

Use **springdoc-openapi** to expose OpenAPI 3 spec and Swagger UI from your REST controllers. The JSON/YAML spec is consumed by clients and code generators; the UI is useful in development.

**Dependency:**

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.6.0")  // align with Boot 4
}
```

**application.yaml:**

```yaml
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
```

Document controllers with `@Operation` and `@Parameter`:

```java
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;

@RestController
@RequestMapping("/api/products")
@Tag(name = "Products", description = "Product API")
public class ProductController {

    @GetMapping("/{id}")
    @Operation(summary = "Get product by ID")
    public Product get(@Parameter(description = "Product ID") @PathVariable String id) {
        return productService.findById(id);
    }
}
```

The OpenAPI spec is available at `springdoc.api-docs.path` (default `/v3/api-docs`); Swagger UI at `springdoc.swagger-ui.path`. Protect these endpoints in production via Spring Security 7 (e.g. allow only for authenticated users or internal network). See [springdoc documentation](https://springdoc.org/) for grouping, security schemes, and more.

---

## 15. Scheduling

Use `@EnableScheduling` and `@Scheduled` for periodic tasks (cron, fixed rate, or fixed delay).

**Enable scheduling:**

```java
@SpringBootApplication
@EnableScheduling
public class Application { ... }
```

**Scheduled component:**

```java
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class SyncJob {

    @Scheduled(fixedRate = 60000)  // every 60 seconds
    public void sync() {
        // run task
    }

    @Scheduled(cron = "0 0 * * * *")  // every hour at minute 0
    public void hourlyReport() {
        // run task
    }
}
```

With **virtual threads** enabled (section 6), scheduled tasks run on virtual threads when the default task scheduler is used; blocking work in the task does not block platform threads. For a custom `TaskScheduler` (e.g. thread pool size), define a `TaskScheduler` bean and configure as needed. Spring Batch is not covered here; for batch jobs (chunk-based reading/writing), see Spring Batch documentation.
