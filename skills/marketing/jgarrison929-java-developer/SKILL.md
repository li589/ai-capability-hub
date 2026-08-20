---
name: java-developer
description: Use when building modern Java 17/21+ applications with Spring Boot, JPA/Hibernate, streams, records, virtual threads, or enterprise patterns. Invoke for JVM optimization, testing with JUnit 5, or reactive programming.
triggers:
  - Java
  - Spring Boot
  - Spring
  - JPA
  - Hibernate
  - Maven
  - Gradle
  - JUnit
  - Stream API
  - records
  - virtual threads
  - CompletableFuture
  - Kotlin
role: specialist
scope: implementation
output-format: code
install_source: official
install_method: download
skill_id: official_wKwdsVLa
enabled_at: 1787231588276
version: 1.0.0
name_zh: 开发指南
---

# Java Developer

Senior Java specialist with deep expertise in modern Java (17/21+), Spring Boot, and production-grade enterprise application development.

## Role Definition

You are a senior Java engineer who leverages modern language features — records, sealed classes, pattern matching, virtual threads — to write clean, performant enterprise applications. You build with Spring Boot 3.x, test with JUnit 5, and optimize for the JVM.

## Core Principles

1. **Modern Java first** — use records, sealed classes, pattern matching, virtual threads
2. **Immutability by default** — records for data, unmodifiable collections
3. **Spring Boot conventions** — auto-configuration, profiles, actuator
4. **Streams for data processing** — functional pipelines over imperative loops
5. **Test everything** — JUnit 5 with parameterized tests, Testcontainers for integration
6. **Type safety** — strong types, avoid stringly-typed code

---

## Project Structure (Spring Boot)

```
myservice/
├── src/
│   ├── main/
│   │   ├── java/com/example/myservice/
│   │   │   ├── MyServiceApplication.java
│   │   │   ├── config/
│   │   │   │   ├── SecurityConfig.java
│   │   │   │   └── JpaConfig.java
│   │   │   ├── user/                    # Feature-based packaging
│   │   │   │   ├── User.java           # Entity
│   │   │   │   ├── UserDto.java        # DTO (record)
│   │   │   │   ├── UserRepository.java
│   │   │   │   ├── UserService.java
│   │   │   │   └── UserController.java
│   │   │   └── common/
│   │   │       ├── exception/
│   │   │       │   ├── AppException.java
│   │   │       │   └── GlobalExceptionHandler.java
│   │   │       └── validation/
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       └── db/migration/           # Flyway
│   │           └── V1__init.sql
│   └── test/
│       └── java/com/example/myservice/
│           ├── user/
│           │   ├── UserServiceTest.java
│           │   └── UserControllerIT.java
│           └── TestcontainersConfig.java
├── pom.xml (or build.gradle.kts)
└── README.md
```

---

## Records and Sealed Classes (Java 17+)

```java
// Records for immutable data carriers (DTOs, value objects)
public record CreateUserRequest(
    @NotBlank String name,
    @Email String email,
    @Min(0) @Max(150) int age
) {}

public record UserResponse(
    String id,
    String name,
    String email,
    Instant createdAt
) {
    // Compact constructor for validation
    public UserResponse {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(name, "name must not be null");
    }

    // Static factory from entity
    public static UserResponse from(User entity) {
        return new UserResponse(
            entity.getId(),
            entity.getName(),
            entity.getEmail(),
            entity.getCreatedAt()
        );
    }
}

// Sealed classes for exhaustive type hierarchies
public sealed interface PaymentResult {
    record Success(String transactionId, BigDecimal amount) implements PaymentResult {}
    record Declined(String reason) implements PaymentResult {}
    record Error(Exception cause) implements PaymentResult {}
}

// Pattern matching with sealed types (Java 21+)
public String formatResult(PaymentResult result) {
    return switch (result) {
        case PaymentResult.Success s -> "Paid %s: %s".formatted(s.amount(), s.transactionId());
        case PaymentResult.Declined d -> "Declined: %s".formatted(d.reason());
        case PaymentResult.Error e -> "Error: %s".formatted(e.cause().getMessage());
    };
}
```

---

## Streams and Functional Patterns

```java
// Stream pipelines for data processing
public List<UserResponse> getActiveAdults(List<User> users) {
    return users.stream()
        .filter(User::isActive)
        .filter(u -> u.getAge() >= 18)
        .sorted(Comparator.comparing(User::getName))
        .map(UserResponse::from)
        .toList();  // Unmodifiable list (Java 16+)
}

// Collectors for aggregation
public Map<String, Long> countByDepartment(List<Employee> employees) {
    return employees.stream()
        .collect(Collectors.groupingBy(
            Employee::getDepartment,
            Collectors.counting()
        ));
}

// Reduce for accumulation
public BigDecimal totalRevenue(List<Order> orders) {
    return orders.stream()
        .filter(o -> o.getStatus() == OrderStatus.COMPLETED)
        .map(Order::getTotal)
        .reduce(BigDecimal.ZERO, BigDecimal::add);
}

// Optional — no more null checks
public Optional<User> findByEmail(String email) {
    return userRepository.findByEmail(email);
}

// Chaining optionals
public String getUserDisplayName(String userId) {
    return userRepository.findById(userId)
        .map(User::getDisplayName)
        .orElse("Unknown User");
}

// flatMap for nested optionals
public Optional<Address> getUserAddress(String userId) {
    return userRepository.findById(userId)
        .flatMap(User::getPrimaryAddress);
}

// ❌ BAD: Optional anti-patterns
Optional.of(value).isPresent();  // Just check value != null
optional.get();                   // Might throw NoSuchElementException
Optional<List<T>>                 // Use empty list instead
```

---

## Spring Boot Patterns

```java
// Controller with validation
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable String id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse createUser(@Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }

    @GetMapping
    public Page<UserResponse> listUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        return userService.findAll(PageRequest.of(page, size));
    }
}

// Service layer
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public Optional<UserResponse> findById(String id) {
        return userRepository.findById(id)
            .map(UserResponse::from);
    }

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new ConflictException("Email already registered");
        }

        var user = User.builder()
            .name(request.name())
            .email(request.email())
            .build();

        return UserResponse.from(userRepository.save(user));
    }
}

// Global exception handler
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(NotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ProblemDetail handleNotFound(NotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(
            HttpStatus.NOT_FOUND, ex.getMessage()
        );
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        var detail = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        var errors = ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                FieldError::getDefaultMessage
            ));
        detail.setProperty("errors", errors);
        return detail;
    }
}
```

---

## JPA / Hibernate

```java
// Entity with proper equals/hashCode
@Entity
@Table(name = "users")
@Getter @Setter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    @Enumerated(EnumType.STRING)
    private UserStatus status = UserStatus.ACTIVE;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;

    // N+1 prevention: use LAZY + entity graph
    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(name = "user_roles")
    private Set<Role> roles = new HashSet<>();

    // Business-key equals (not id-based)
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User other)) return false;
        return email != null && email.equals(other.email);
    }

    @Override
    public int hashCode() {
        return Objects.hash(email);
    }
}

// Repository with custom queries
public interface UserRepository extends JpaRepository<User, String> {

    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u JOIN FETCH u.roles WHERE u.status = :status")
    List<User> findActiveWithRoles(@Param("status") UserStatus status);

    // Projections for read-only queries
    @Query("SELECT new com.example.UserSummary(u.id, u.name, u.email) FROM User u")
    Page<UserSummary> findAllSummaries(Pageable pageable);
}
```

---

## Virtual Threads (Java 21+)

```java
// Virtual threads for I/O-bound work
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<String>> futures = urls.stream()
        .map(url -> executor.submit(() -> fetchUrl(url)))
        .toList();

    List<String> results = futures.stream()
        .map(f -> {
            try { return f.get(); }
            catch (Exception e) { throw new RuntimeException(e); }
        })
        .toList();
}

// Spring Boot with virtual threads (application.yml)
// spring.threads.virtual.enabled: true

// Structured concurrency (preview in Java 21+)
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var userTask = scope.fork(() -> userService.getUser(userId));
    var ordersTask = scope.fork(() -> orderService.getOrders(userId));

    scope.join();
    scope.throwIfFailed();

    var user = userTask.get();
    var orders = ordersTask.get();
    return new UserProfile(user, orders);
}

// CompletableFuture for async composition
public CompletableFuture<UserProfile> getUserProfile(String userId) {
    var userFuture = CompletableFuture.supplyAsync(() -> userService.getUser(userId));
    var ordersFuture = CompletableFuture.supplyAsync(() -> orderService.getOrders(userId));

    return userFuture.thenCombine(ordersFuture, UserProfile::new)
        .exceptionally(ex -> {
            log.error("Failed to load profile for {}", userId, ex);
            return UserProfile.empty(userId);
        });
}
```

---

## Testing with JUnit 5

```java
// Unit test with Mockito
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock UserRepository userRepository;
    @InjectMocks UserService userService;

    @Test
    void shouldReturnUser_whenExists() {
        var user = new User("Alice", "alice@test.com");
        when(userRepository.findById("1")).thenReturn(Optional.of(user));

        var result = userService.findById("1");

        assertThat(result).isPresent();
        assertThat(result.get().name()).isEqualTo("Alice");
    }

    @Test
    void shouldThrow_whenEmailExists() {
        when(userRepository.existsByEmail("taken@test.com")).thenReturn(true);
        var request = new CreateUserRequest("Bob", "taken@test.com", 25);

        assertThatThrownBy(() -> userService.create(request))
            .isInstanceOf(ConflictException.class)
            .hasMessageContaining("already registered");
    }

    @ParameterizedTest
    @CsvSource({
        "alice, alice@test.com, true",
        "'', bob@test.com, false",
        "charlie, invalid-email, false"
    })
    void shouldValidateInput(String name, String email, boolean valid) {
        var request = new CreateUserRequest(name, email, 25);
        var violations = validator.validate(request);
        assertThat(violations.isEmpty()).isEqualTo(valid);
    }
}

// Integration test with Testcontainers
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Testcontainers
class UserControllerIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("testdb");

    @DynamicPropertySource
    static void configureDb(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired TestRestTemplate restTemplate;

    @Test
    void shouldCreateAndRetrieveUser() {
        var request = new CreateUserRequest("Alice", "alice@test.com", 30);

        var createResponse = restTemplate.postForEntity("/api/v1/users", request, UserResponse.class);
        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);

        var userId = createResponse.getBody().id();
        var getResponse = restTemplate.getForEntity("/api/v1/users/" + userId, UserResponse.class);
        assertThat(getResponse.getBody().name()).isEqualTo("Alice");
    }
}
```

---

## application.yml Best Practices

```yaml
spring:
  application:
    name: myservice
  threads:
    virtual:
      enabled: true    # Java 21+ virtual threads
  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
  jpa:
    open-in-view: false    # Always disable OSIV in production
    hibernate:
      ddl-auto: validate   # Never auto-create in production
    properties:
      hibernate:
        default_batch_fetch_size: 16
        jdbc.batch_size: 25
        order_inserts: true
  flyway:
    enabled: true

management:
  endpoints:
    web:
      exposure:
        include: health,metrics,info
  endpoint:
    health:
      show-details: when-authorized

server:
  shutdown: graceful
  servlet:
    context-path: /api

logging:
  level:
    com.example: INFO
    org.hibernate.SQL: DEBUG    # Only in dev profile
```

---

## Common Anti-Patterns

```java
// ❌ BAD: Returning null
public User findUser(String id) { return null; }

// ✅ GOOD: Return Optional
public Optional<User> findUser(String id) { ... }

// ❌ BAD: Catching Exception
try { ... } catch (Exception e) { log.error("error", e); }

// ✅ GOOD: Catch specific exceptions
try { ... }
catch (UserNotFoundException e) { return ResponseEntity.notFound().build(); }
catch (ValidationException e) { return ResponseEntity.badRequest().body(e.getMessage()); }

// ❌ BAD: Mutable DTOs with getters/setters
public class UserDto { private String name; /* getters, setters, equals, hashCode... */ }

// ✅ GOOD: Records
public record UserDto(String name, String email) {}

// ❌ BAD: Field injection
@Autowired private UserRepository repo;

// ✅ GOOD: Constructor injection
private final UserRepository repo;
public UserService(UserRepository repo) { this.repo = repo; }

// ❌ BAD: open-in-view = true (lazy loading in controller layer)
// ✅ GOOD: Fetch everything needed in service layer with JOIN FETCH
```

---

*Adapted from buildwithclaude by Dave Poon (MIT)*
