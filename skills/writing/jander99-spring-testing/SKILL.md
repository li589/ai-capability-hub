---
name: spring-testing
description: Write, create, and generate Spring Boot tests with JUnit 5, MockMvc, Mockito, and Testcontainers. Implement unit tests (pure Mockito), slice tests (@WebMvcTest, @DataJpaTest, @JsonTest), and integration tests (@SpringBootTest). Use when testing controllers, repositories, services, REST APIs, or setting up test fixtures. Covers test organization, mocking strategies, test data builders, and debugging test failures.
license: MIT
metadata:
  version: 1.0.0
  audience: developers
  workflow: testing
install_source: official
install_method: download
skill_id: official_SzFfw57O
enabled_at: 1787232615333
version: 1.0.0
name_zh: 容器Spring开发
---

# Spring Boot Testing

Test pyramid approach: fast unit tests at the base, slice tests in the middle, integration tests at the top.

## What I Do

- Choose the right test type (unit vs slice vs integration) for speed and confidence
- Set up `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest` with minimal context
- Integrate Testcontainers with `@ServiceConnection` or `@DynamicPropertySource`
- Debug common failures (missing beans, slow suites, container lifecycle)
- Test Spring Security endpoints with `@WithMockUser` and JWT mocking

## When to Use Me

- Write tests for Spring Boot controllers, services, or repositories
- Set up @WebMvcTest, @DataJpaTest, or @SpringBootTest
- Configure Testcontainers for integration tests
- Mock dependencies with Mockito or @MockitoBean
- Debug failing tests or slow test suites
- Test Spring Security endpoints

## Test Pyramid Quick Reference

| Layer | Annotation | Speed | Use For |
|-------|-----------|-------|---------|
| Unit | None (pure Mockito) | ~1ms | Business logic |
| Slice | @WebMvcTest | ~500ms | Controller endpoints |
| Slice | @DataJpaTest | ~500ms | Repository queries |
| Integration | @SpringBootTest | ~5s | Full application flows |

## @WebMvcTest - Controller Testing

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderService orderService;

    @Test
    void shouldReturnOrder_whenOrderExists() throws Exception {
        when(orderService.findById(1L)).thenReturn(Optional.of(order));

        mockMvc.perform(get("/api/orders/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1));
    }
}
```

## @DataJpaTest - Repository Testing

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
@Testcontainers
class OrderRepositoryTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = 
        new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private TestEntityManager entityManager;  // Use TestEntityManager for @DataJpaTest

    @Test
    void shouldFindOrdersByStatus() {
        entityManager.persistAndFlush(new Order("SKU-1", OrderStatus.PENDING));
        var orders = orderRepository.findByStatus(OrderStatus.PENDING);
        assertThat(orders).hasSize(1);
    }
}
```

## @SpringBootTest with Testcontainers

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Testcontainers
class OrderIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = 
        new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private TestRestTemplate restTemplate;

    @BeforeEach
    void setUp() {
        orderRepository.deleteAll();
    }

    @Test
    void shouldCreateAndRetrieveOrder() {
        var response = restTemplate.postForEntity("/api/orders", request, OrderDto.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    }
}
```

## Singleton Container Pattern

Share containers across test classes for speed:

```java
public abstract class AbstractIntegrationTest {
    static final PostgreSQLContainer<?> postgres;

    static {
        postgres = new PostgreSQLContainer<>("postgres:16-alpine");
        postgres.start();
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

## Pure Unit Tests (No Spring)

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock private OrderRepository orderRepository;
    @InjectMocks private OrderService orderService;

    @Test
    void shouldCreateOrder_whenValidRequest() {
        when(orderRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        var order = orderService.createOrder(request);
        assertThat(order.getSku()).isEqualTo("SKU-123");
    }
}
```

## Test Naming Convention

**Pattern:** `should{ExpectedBehavior}_when{Condition}`

```java
void shouldReturnOrder_whenOrderExists()
void shouldThrowException_whenOrderNotFound()
void shouldApplyDiscount_whenCustomerIsPremium()
```

## Spring Security Testing

```java
@WebMvcTest(AdminController.class)
@Import(SecurityConfig.class)
class AdminControllerTest {

    @Test
    void shouldRejectUnauthenticated() throws Exception {
        mockMvc.perform(get("/api/admin")).andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void shouldAllowAdmin() throws Exception {
        mockMvc.perform(get("/api/admin")).andExpect(status().isOk());
    }
}
```

## Context7 Integration

Fetch up-to-date docs when writing tests:

```bash
context7 query "@WebMvcTest MockMvc" --library spring-boot
context7 query "PostgreSQLContainer" --library testcontainers
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `NoSuchBeanDefinitionException` | Missing mock | Add `@MockitoBean` |
| `DataSource` required | No database | Add Testcontainers |
| Slow test suite | Container per class | Singleton pattern |
| `@MockBean` deprecated | Spring Boot 3.4+ | Use `@MockitoBean` (same behavior, new package) |

## Reference

| Topic | Reference |
|-------|-----------|
| Test patterns | `references/research.md` |
| Anti-patterns | `references/research.md#common-anti-patterns` |
| Testcontainers | `references/research.md#testcontainers-patterns` |

## Related Skills

- **spring-boot-core** - Application configuration
- **spring-data** - Repository patterns
- **spring-security** - Security testing

## Resources

- [Spring Boot Testing](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.testing)
- [Testcontainers](https://java.testcontainers.org/)
- [JUnit 5](https://junit.org/junit5/docs/current/user-guide/)
