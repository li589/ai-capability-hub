# Spring Boot Testing Research

> Best practices, patterns, and anti-patterns for testing Spring Boot applications

---

## Test Pyramid Overview

```
        /\
       /  \      E2E Tests (Few)
      /----\     - Full application with real browser
     /      \    - Selenium, Cypress
    /--------\   Integration Tests (Some)
   /          \  - @SpringBootTest with Testcontainers
  /------------\ - @WebMvcTest, @DataJpaTest
 /              \
/________________\ Unit Tests (Many)
                   - Pure Mockito, no Spring context
                   - Fast, isolated, focused
```

### When to Use Each Level

| Test Type | Speed | Confidence | Use When |
|-----------|-------|------------|----------|
| Unit | ~1ms | Low-Medium | Testing business logic in isolation |
| Slice | ~500ms | Medium | Testing web layer, data layer |
| Integration | ~5s | High | Testing component interactions |
| E2E | ~30s+ | Very High | Critical user journeys |

---

## Test Organization

### Directory Structure

```
src/test/java/com/example/
├── unit/                    # Pure unit tests (no Spring)
│   ├── service/
│   │   └── OrderServiceTest.java
│   └── util/
│       └── PriceCalculatorTest.java
├── integration/             # @SpringBootTest tests
│   ├── OrderIntegrationTest.java
│   └── PaymentIntegrationTest.java
├── contract/                # Contract tests (Pact, Spring Cloud Contract)
│   └── OrderApiContractTest.java
└── slice/                   # Slice tests (@WebMvcTest, @DataJpaTest)
    ├── web/
    │   └── OrderControllerTest.java
    └── repository/
        └── OrderRepositoryTest.java
```

### Test Naming Convention

**Pattern:** `should{ExpectedBehavior}_when{StateUnderTest}`

```java
// Good examples
void shouldReturnOrder_whenOrderExists()
void shouldThrowException_whenOrderNotFound()
void shouldCalculateDiscount_whenCustomerIsPremium()
void shouldRejectPayment_whenInsufficientFunds()

// Bad examples (too vague)
void testOrder()
void orderTest()
void test1()
```

---

## Pure Unit Tests (No Spring Context)

### When to Use

- Testing business logic, calculations, transformations
- Testing utility classes
- Testing domain objects and value objects
- When you need fast feedback (<10ms per test)

### Pattern: Constructor Injection with Mocks

```java
class OrderServiceTest {

    private OrderRepository orderRepository;
    private PaymentGateway paymentGateway;
    private OrderService orderService;

    @BeforeEach
    void setUp() {
        orderRepository = Mockito.mock(OrderRepository.class);
        paymentGateway = Mockito.mock(PaymentGateway.class);
        orderService = new OrderService(orderRepository, paymentGateway);
    }

    @Test
    void shouldCreateOrder_whenValidRequest() {
        // Arrange
        var request = new CreateOrderRequest("SKU-123", 2);
        when(orderRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        // Act
        var order = orderService.createOrder(request);

        // Assert
        assertThat(order.getSku()).isEqualTo("SKU-123");
        assertThat(order.getQuantity()).isEqualTo(2);
        verify(orderRepository).save(any(Order.class));
    }

    @Test
    void shouldThrowException_whenSkuNotFound() {
        // Arrange
        var request = new CreateOrderRequest("INVALID-SKU", 1);
        when(orderRepository.findBySku("INVALID-SKU")).thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(SkuNotFoundException.class, 
            () -> orderService.createOrder(request));
    }
}
```

### JUnit 5 Extension for Mockito

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private PaymentGateway paymentGateway;

    @InjectMocks
    private OrderService orderService;

    @Test
    void shouldProcessOrder() {
        // Test implementation
    }
}
```

---

## Slice Tests

### @WebMvcTest - Controller Layer

**When to Use:**
- Testing request mapping, validation, serialization
- Testing error handling and response formatting
- Testing security at controller level

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderService orderService;

    @Test
    void shouldReturnOrder_whenOrderExists() throws Exception {
        // Arrange
        var order = new OrderDto(1L, "SKU-123", 2, BigDecimal.TEN);
        when(orderService.findById(1L)).thenReturn(Optional.of(order));

        // Act & Assert
        mockMvc.perform(get("/api/orders/1")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.sku").value("SKU-123"))
            .andExpect(jsonPath("$.quantity").value(2));
    }

    @Test
    void shouldReturn404_whenOrderNotFound() throws Exception {
        when(orderService.findById(999L)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/orders/999"))
            .andExpect(status().isNotFound());
    }

    @Test
    void shouldValidateRequest_whenCreatingOrder() throws Exception {
        var invalidRequest = """
            {
                "sku": "",
                "quantity": -1
            }
            """;

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidRequest))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.errors").isNotEmpty());
    }
}
```

### @DataJpaTest - Repository Layer

**When to Use:**
- Testing custom queries
- Testing JPA entity mappings
- Testing repository behavior with real database

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private TestEntityManager entityManager;

    @Test
    void shouldFindOrdersByCustomerId() {
        // Arrange
        var customer = entityManager.persist(new Customer("john@example.com"));
        entityManager.persist(new Order(customer, "SKU-1", 2));
        entityManager.persist(new Order(customer, "SKU-2", 1));
        entityManager.flush();

        // Act
        var orders = orderRepository.findByCustomerId(customer.getId());

        // Assert
        assertThat(orders).hasSize(2);
        assertThat(orders).extracting(Order::getSku)
            .containsExactlyInAnyOrder("SKU-1", "SKU-2");
    }

    @Test
    void shouldFindOrdersByDateRange() {
        // Test date range queries
    }
}
```

### @DataJpaTest with H2 (Fast, In-Memory)

```java
@DataJpaTest  // Uses H2 by default
class OrderRepositoryH2Test {

    @Autowired
    private OrderRepository orderRepository;

    @Test
    void shouldSaveAndRetrieveOrder() {
        var order = new Order("SKU-123", 5);
        var saved = orderRepository.save(order);

        assertThat(saved.getId()).isNotNull();
        assertThat(orderRepository.findById(saved.getId())).isPresent();
    }
}
```

---

## Integration Tests with @SpringBootTest

### Full Application Context

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Testcontainers
class OrderIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", redis::getFirstMappedPort);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @LocalServerPort
    private int port;

    @Test
    void shouldCreateAndRetrieveOrder() {
        // Create order
        var createRequest = new CreateOrderRequest("SKU-123", 3);
        var createResponse = restTemplate.postForEntity(
            "/api/orders", createRequest, OrderDto.class);

        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(createResponse.getBody().getId()).isNotNull();

        // Retrieve order
        var orderId = createResponse.getBody().getId();
        var getResponse = restTemplate.getForEntity(
            "/api/orders/" + orderId, OrderDto.class);

        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().getSku()).isEqualTo("SKU-123");
    }
}
```

### Using @ServiceConnection (Spring Boot 3.1+)

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Testcontainers
class ModernIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Container
    @ServiceConnection
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.4.0"));

    // No @DynamicPropertySource needed - @ServiceConnection handles it!

    @Test
    void shouldProcessOrderViaKafka() {
        // Test Kafka integration
    }
}
```

---

## Testcontainers Patterns

### Singleton Container Pattern (Faster Tests)

```java
abstract class AbstractIntegrationTest {

    static final PostgreSQLContainer<?> postgres;
    static final KafkaContainer kafka;

    static {
        postgres = new PostgreSQLContainer<>("postgres:16-alpine");
        kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.4.0"));

        Startables.deepStart(postgres, kafka).join();
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }
}

// All test classes extend this - containers are shared
class OrderServiceIntegrationTest extends AbstractIntegrationTest {
    // Tests here
}

class PaymentServiceIntegrationTest extends AbstractIntegrationTest {
    // Tests here - same containers!
}
```

### Reusable Containers (Development Speed)

```java
// In test application.properties
testcontainers.reuse.enable=true

// In test code
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
    .withReuse(true);  // Container survives between test runs!
```

---

## Test Data Patterns

### Test Data Builder

```java
public class OrderTestDataBuilder {
    private Long id = null;
    private String sku = "DEFAULT-SKU";
    private int quantity = 1;
    private BigDecimal price = BigDecimal.TEN;
    private OrderStatus status = OrderStatus.PENDING;

    public static OrderTestDataBuilder anOrder() {
        return new OrderTestDataBuilder();
    }

    public OrderTestDataBuilder withSku(String sku) {
        this.sku = sku;
        return this;
    }

    public OrderTestDataBuilder withQuantity(int quantity) {
        this.quantity = quantity;
        return this;
    }

    public OrderTestDataBuilder withStatus(OrderStatus status) {
        this.status = status;
        return this;
    }

    public Order build() {
        return new Order(id, sku, quantity, price, status);
    }
}

// Usage in tests
@Test
void shouldCalculateTotal() {
    var order = anOrder()
        .withSku("PREMIUM-ITEM")
        .withQuantity(5)
        .build();
    
    assertThat(order.calculateTotal()).isEqualTo(new BigDecimal("50.00"));
}
```

### Object Mother Pattern

```java
public class TestFixtures {

    public static Customer aValidCustomer() {
        return new Customer("john@example.com", "John Doe", CustomerType.REGULAR);
    }

    public static Customer aPremiumCustomer() {
        return new Customer("premium@example.com", "Premium User", CustomerType.PREMIUM);
    }

    public static Order aPendingOrder() {
        return new Order("SKU-123", 1, OrderStatus.PENDING);
    }

    public static Order aCompletedOrder() {
        return new Order("SKU-456", 2, OrderStatus.COMPLETED);
    }
}
```

---

## What to Mock vs Real Implementations

### MOCK These
- External HTTP APIs (payment gateways, third-party services)
- Email/SMS services
- File systems (use in-memory alternatives)
- Clock/Time (use `Clock` injection)
- Random number generators
- External message queues (unless testing integration)

### Use REAL Implementations For
- Database (use Testcontainers)
- Message brokers in integration tests (Testcontainers)
- Redis/caching layers (Testcontainers)
- Your own services and repositories
- Validation logic
- Serialization/deserialization

---

## Common Anti-Patterns

### 1. Testing Implementation Details

```java
// BAD - Tests implementation, not behavior
@Test
void shouldCallRepositorySave() {
    orderService.createOrder(request);
    verify(orderRepository, times(1)).save(any(Order.class));
}

// GOOD - Tests behavior
@Test
void shouldPersistOrder_whenCreated() {
    var orderId = orderService.createOrder(request);
    assertThat(orderRepository.findById(orderId)).isPresent();
}
```

### 2. Over-Mocking

```java
// BAD - Mocking everything, test proves nothing
@Test
void testOrderCreation() {
    when(validator.validate(any())).thenReturn(true);
    when(repository.save(any())).thenReturn(new Order());
    when(eventPublisher.publish(any())).thenReturn(true);
    
    orderService.createOrder(request);
    
    verify(repository).save(any());  // Just verifying mocks...
}

// GOOD - Test real behavior with minimal mocking
@Test
void shouldCreateValidOrder() {
    var order = orderService.createOrder(validRequest);
    
    assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
    assertThat(order.getCreatedAt()).isCloseTo(Instant.now(), within(1, SECONDS));
}
```

### 3. Slow Test Suites

```java
// BAD - Each test starts new containers
@Testcontainers
class Test1 {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>();
    // ...
}

@Testcontainers
class Test2 {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>();
    // Different container, slow startup again!
}

// GOOD - Use singleton pattern (see above)
```

### 4. Flaky Tests with Timing

```java
// BAD - Flaky due to timing
@Test
void shouldExpireSession() {
    createSession();
    Thread.sleep(5000);  // DON'T DO THIS
    assertThat(sessionService.isExpired()).isTrue();
}

// GOOD - Use controllable time
@Test
void shouldExpireSession() {
    var clock = Clock.fixed(Instant.parse("2024-01-01T00:00:00Z"), ZoneId.UTC);
    var service = new SessionService(sessionRepository, clock);
    
    service.createSession();
    
    // Advance time
    clock = Clock.fixed(Instant.parse("2024-01-01T01:00:00Z"), ZoneId.UTC);
    service.setClock(clock);
    
    assertThat(service.isExpired()).isTrue();
}
```

### 5. Test Data Pollution

```java
// BAD - Tests depend on each other
@Test
@Order(1)
void shouldCreateOrder() {
    orderService.createOrder(request);  // Creates order with ID 1
}

@Test
@Order(2)
void shouldFindOrder() {
    var order = orderService.findById(1L);  // Depends on test 1!
    assertThat(order).isPresent();
}

// GOOD - Each test sets up its own data
@BeforeEach
void setUp() {
    orderRepository.deleteAll();  // Clean slate
}

@Test
void shouldFindOrder() {
    var created = orderRepository.save(new Order("SKU-1", 1));
    
    var found = orderService.findById(created.getId());
    
    assertThat(found).isPresent();
}
```

---

## Spring Security Testing

```java
@WebMvcTest(SecuredController.class)
@Import(SecurityConfig.class)
class SecuredControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void shouldRejectUnauthenticatedRequest() throws Exception {
        mockMvc.perform(get("/api/admin/users"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void shouldAllowAdminAccess() throws Exception {
        mockMvc.perform(get("/api/admin/users"))
            .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    void shouldDenyNonAdminAccess() throws Exception {
        mockMvc.perform(get("/api/admin/users"))
            .andExpect(status().isForbidden());
    }
}
```

---

## Context7 MCP Integration

When writing Spring Boot tests, use Context7 to fetch up-to-date documentation:

```
# Fetch latest Spring Boot Test docs
context7 query "Spring Boot @WebMvcTest MockMvc" --library spring-boot

# Fetch Testcontainers patterns
context7 query "PostgreSQLContainer Spring Boot" --library testcontainers

# Fetch JUnit 5 assertions
context7 query "assertThat nested properties" --library assertj
```

---

## Resources

- [Spring Boot Testing Documentation](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.testing)
- [Testcontainers for Java](https://java.testcontainers.org/)
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito Documentation](https://site.mockito.org/)
- [AssertJ Documentation](https://assertj.github.io/doc/)
