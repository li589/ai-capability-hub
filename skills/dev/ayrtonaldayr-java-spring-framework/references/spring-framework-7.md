# Spring Framework 7.0.x — Feature Reference

**Version**: 7.0.5 (Stable) | **Java baseline**: 17 (25 recommended) | **Jakarta EE**: 11

For **reactive applications (WebFlux + R2DBC)**, combine this reference with the **Reactive stack** section in `references/spring-boot-4.md`.

---

## Table of Contents
1. [API Versioning](#1-api-versioning)
2. [Null Safety — JSpecify](#2-null-safety--jspecify)
3. [Resilience Annotations](#3-resilience-annotations)
4. [Programmatic Bean Registration](#4-programmatic-bean-registration)
5. [RestClient (Synchronous)](#5-restclient-synchronous)
6. [HTTP Service Proxy (Declarative)](#6-http-service-proxy-declarative)
7. [JdbcClient](#7-jdbcclient)
8. [JmsClient](#8-jmsclient)
9. [Streaming Support](#9-streaming-support)
10. [SpEL — Optional Support](#10-spel--optional-support)
11. [Enhanced PathPattern](#11-enhanced-pathpattern)
12. [RestTestClient (Testing)](#12-resttestclient-testing)
13. [Removed APIs Migration](#13-removed-apis-migration)
14. [Bean Validation 3.1](#14-bean-validation-31)

---

## 1. API Versioning

Spring 7 introduces **native HTTP API versioning** via `@RequestMapping(version = "...")`.
Routing uses the `Version` HTTP request header by default.

```java
@RestController
@RequestMapping("/api/products")
public class ProductController {

    @GetMapping(value = "/search", version = "1")
    public List<ProductV1> searchV1(@RequestParam String query) { ... }

    @GetMapping(value = "/search", version = "2")
    public ProductPageV2 searchV2(@RequestParam String query,
                                  @RequestParam(defaultValue = "10") int limit) { ... }
}
```

**No library required** — built into Spring MVC and WebFlux.

---

## 2. Null Safety — JSpecify

Spring 7 adopts **JSpecify** (`org.jspecify`) for null safety annotations.

```java
import org.jspecify.annotations.NonNull;
import org.jspecify.annotations.Nullable;
import org.jspecify.annotations.NullMarked;

@NullMarked          // entire package is non-null by default
@Service
public class UserService {

    public @NonNull User findRequired(@NonNull String userId) { ... }

    public @Nullable User findOptional(@Nullable String userId) { ... }
}
```

**Gradle dependency**:
```kotlin
implementation("org.jspecify:jspecify:1.0.0")
```

---

## 3. Resilience Annotations

Spring 7 ships **built-in resilience** — no Resilience4j required for basic cases.

```java
@Service
@EnableResilientMethods
public class PaymentService {

    @Retryable(maxAttempts = 3, delay = 500)
    public Receipt processPayment(PaymentRequest req) { ... }

    @ConcurrencyLimit(maxConcurrentCalls = 10)
    public Balance fetchBalance(String accountId) { ... }

    @CircuitBreaker(failureRateThreshold = 0.5)
    public ExchangeRate getExchangeRate(String currency) { ... }
}
```

For **time-window rate limiting** (e.g. requests per minute per IP or user), see `references/spring-boot-4.md` (Rate limiting).

---

## 4. Programmatic Bean Registration

Prefer `BeanRegistrar` over `@Bean`-heavy classes. Avoids proxy overhead and is GraalVM-friendly.

```java
@Configuration(proxyBeanMethods = false)
public class InfrastructureConfig implements BeanRegistrar {

    @Override
    public void registerBeans(BeanRegistry registry) {
        registry.registerBean("userRepository",
            UserRepository.class,
            spec -> spec.supplier(UserRepositoryImpl::new)
                        .scope(BeanDefinition.SCOPE_SINGLETON));
    }
}
```

---

## 5. RestClient (Synchronous)

`RestClient` replaces `RestTemplate`. Fluent, immutable, interceptor-aware.

```java
@Configuration(proxyBeanMethods = false)
public class HttpConfig {

    @Bean
    RestClient restClient(RestClient.Builder builder) {
        return builder
            .baseUrl("https://api.example.com")
            .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}

// Usage
record Product(Long id, String name) {}

List<Product> products = restClient.get()
    .uri("/products")
    .retrieve()
    .body(new ParameterizedTypeReference<List<Product>>() {});
```

---

## 6. HTTP Service Proxy (Declarative)

Use `@HttpExchange` interfaces with `HttpServiceProxyFactory` for zero-boilerplate clients.

```java
// Declare the interface
@HttpExchange("/products")
public interface ProductClient {

    @GetExchange("/{id}")
    Product findById(@PathVariable Long id);

    @PostExchange
    Product create(@RequestBody Product product);
}

// Register as a bean
@Configuration(proxyBeanMethods = false)
@ImportHttpServices(group = "product", types = {ProductClient.class})
public class ClientConfig {}
```

Auto-configuration wires the `RestClient` adapter. For custom setup:

```java
@Bean
ProductClient productClient(RestClient restClient) {
    return HttpServiceProxyFactory
        .builderFor(RestClientAdapter.create(restClient))
        .build()
        .createClient(ProductClient.class);
}
```

---

## 7. JdbcClient

Fluent JDBC wrapper — replaces direct `JdbcTemplate` usage.

```java
@Repository
public class UserRepository {

    private final JdbcClient jdbc;

    public UserRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    public List<User> findAll() {
        return jdbc.sql("SELECT id, name, email FROM users")
                   .query(User.class)       // uses RowMapper by convention
                   .list();
    }

    public Optional<User> findById(Long id) {
        return jdbc.sql("SELECT id, name, email FROM users WHERE id = :id")
                   .param("id", id)
                   .query(User.class)
                   .optional();
    }

    public int save(User user) {
        return jdbc.sql("INSERT INTO users (name, email) VALUES (:name, :email)")
                   .param("name", user.name())
                   .param("email", user.email())
                   .update();
    }
}
```

---

## 8. JmsClient

Fluent JMS API replacing `JmsTemplate`.

```java
@Service
public class OrderEventPublisher {

    private final JmsClient jms;

    public OrderEventPublisher(JmsClient jms) {
        this.jms = jms;
    }

    public void publishOrder(OrderCreatedEvent event) {
        jms.send("orders.created", event);
    }

    public OrderCreatedEvent consumeNext() {
        return jms.receive("orders.created", OrderCreatedEvent.class);
    }
}
```

---

## 9. Streaming Support

Spring MVC now accepts `InputStream` directly in controller parameters for large uploads.

```java
@PostMapping("/upload")
public ResponseEntity<Void> upload(InputStream body) throws IOException {
    storageService.store(body);
    return ResponseEntity.accepted().build();
}
```

---

## 10. SpEL — Optional Support

Spring Expression Language now understands `Optional` chaining natively.

```java
@Value("#{userService.findUser(#userId)?.orElse('Guest')}")
private String currentUser;
```

---

## 11. Enhanced PathPattern

Double-wildcard `**` now works in the middle of patterns (previously end-only).

```java
@GetMapping("/**/docs/{name}")
public String getDoc(@PathVariable String name) { ... }
```

---

## 12. RestTestClient (Testing)

`RestTestClient` replaces `TestRestTemplate` and `WebTestClient` for servlet-layer tests.

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class ProductControllerTest {

    @Autowired
    private RestTestClient client;

    @Test
    void shouldReturnProducts() {
        client.get().uri("/api/products")
              .exchange()
              .expectStatus().isOk()
              .expectBodyList(Product.class).hasSize(3);
    }
}
```

---

## 13. Removed APIs Migration

| Removed | Replacement |
|---|---|
| `RestTemplate` | `RestClient` |
| `JdbcTemplate` (direct) | `JdbcClient` |
| `javax.*` namespaces | `jakarta.*` |
| `spring-jcl` | Apache Commons Logging |
| JUnit 4 | JUnit 5 |
| Jackson 2.x | Jackson 3.x |
| XML Spring MVC config | `WebMvcConfigurer` (Java) |
| `suffixPatternMatch` | Explicit media types |
| `trailingSlashMatch` | Explicit URI templates |

---

## 14. Bean Validation 3.1

Spring MVC and WebFlux support **Jakarta Bean Validation 3.1** (Boot 4 brings the dependency). Use `@Valid` (or `@Validated`) on `@RequestBody`, and optionally on `@RequestParam` / path variables with group validation or custom validators.

**DTO with constraints:**

```java
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateUserRequest(
    @NotBlank(message = "Name is required")
    @Size(min = 1, max = 100)
    String name,

    @NotBlank
    @Email(message = "Must be a valid email")
    String email
) {}
```

**Controller:**

```java
@PostMapping("/api/users")
public ResponseEntity<User> create(@Valid @RequestBody CreateUserRequest request) {
    User user = userService.create(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(user);
}
```

Validation failures trigger `MethodArgumentNotValidException`; handle them in an `@ExceptionHandler` to return 400 with error details. Standard annotations include `@NotNull`, `@NotBlank`, `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern`. For validation groups or custom validators, use `@Validated` with a group class or implement `ConstraintValidator`; see the Bean Validation spec for details.
