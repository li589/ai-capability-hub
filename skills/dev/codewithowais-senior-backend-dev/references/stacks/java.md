# Java / Spring Boot Stack Reference

## Key Conventions

- Use constructor injection (not field injection). Makes dependencies explicit
  and testable.
- Layer architecture: Controller → Service → Repository. Services contain
  business logic.
- Use `@Transactional` deliberately — understand propagation levels.
- DTOs at API boundary. Never expose JPA entities directly.
- Use Spring Data JPA specifications for complex queries. Native queries only
  when absolutely necessary.
- Exception handling via `@ControllerAdvice` with consistent error responses.
- Use Flyway or Liquibase for migrations.
- Configure connection pools (HikariCP) with appropriate sizing.

---

## Project Structure

```
src/
├── main/
│   ├── java/com/example/app/
│   │   ├── Application.java
│   │   ├── config/
│   │   │   ├── SecurityConfig.java
│   │   │   ├── WebConfig.java
│   │   │   └── OpenApiConfig.java
│   │   ├── common/
│   │   │   ├── exception/
│   │   │   │   ├── AppException.java
│   │   │   │   ├── NotFoundException.java
│   │   │   │   └── GlobalExceptionHandler.java
│   │   │   ├── dto/
│   │   │   │   └── ErrorResponse.java
│   │   │   └── model/
│   │   │       └── BaseEntity.java
│   │   └── modules/
│   │       └── user/
│   │           ├── UserController.java
│   │           ├── UserService.java
│   │           ├── UserRepository.java
│   │           ├── User.java
│   │           └── dto/
│   │               ├── CreateUserRequest.java
│   │               └── UserResponse.java
│   └── resources/
│       ├── application.yml
│       ├── application-dev.yml
│       └── db/migration/
│           └── V1__create_users.sql
└── test/
    └── java/com/example/app/
        └── modules/user/
            ├── UserControllerTest.java
            └── UserServiceTest.java
```

---

## Controller Pattern

```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "Users")
public class UserController {

    private final UserService userService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse create(
            @Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }

    @GetMapping("/{id}")
    public UserResponse findById(@PathVariable UUID id) {
        return userService.findById(id);
    }

    @GetMapping
    public Page<UserResponse> findAll(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return userService.findAll(
            PageRequest.of(page, size, Sort.by("createdAt").descending())
        );
    }
}
```

---

## Service Pattern

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new ConflictException("Email already registered");
        }

        User user = User.builder()
            .email(request.email())
            .name(request.name())
            .passwordHash(passwordEncoder.encode(request.password()))
            .role(Role.USER)
            .build();

        User saved = userRepository.save(user);
        return UserResponse.from(saved);
    }

    public UserResponse findById(UUID id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("User", id));
        return UserResponse.from(user);
    }

    public Page<UserResponse> findAll(Pageable pageable) {
        return userRepository.findAll(pageable)
            .map(UserResponse::from);
    }
}
```

---

## Exception Handling

```java
// Base exception
@Getter
public class AppException extends RuntimeException {
    private final HttpStatus status;
    private final String code;
    private final Map<String, Object> details;

    public AppException(String message, HttpStatus status, String code) {
        this(message, status, code, null);
    }

    public AppException(String message, HttpStatus status,
                        String code, Map<String, Object> details) {
        super(message);
        this.status = status;
        this.code = code;
        this.details = details;
    }
}

public class NotFoundException extends AppException {
    public NotFoundException(String resource, Object id) {
        super(
            "%s with id %s not found".formatted(resource, id),
            HttpStatus.NOT_FOUND,
            "NOT_FOUND"
        );
    }
}

// Global handler
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(AppException.class)
    public ResponseEntity<ErrorResponse> handleApp(AppException ex) {
        return ResponseEntity.status(ex.getStatus())
            .body(new ErrorResponse(
                ex.getCode(), ex.getMessage(), ex.getDetails()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(
            MethodArgumentNotValidException ex) {
        Map<String, Object> details = ex.getBindingResult()
            .getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                fe -> fe.getDefaultMessage() != null
                    ? fe.getDefaultMessage() : "invalid"
            ));
        return ResponseEntity.badRequest()
            .body(new ErrorResponse(
                "VALIDATION_ERROR", "Validation failed", details));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception ex) {
        log.error("Unhandled exception", ex);
        return ResponseEntity.internalServerError()
            .body(new ErrorResponse(
                "INTERNAL_ERROR", "An unexpected error occurred", null));
    }
}

// Response record
public record ErrorResponse(
    String code,
    String message,
    @JsonInclude(JsonInclude.Include.NON_NULL)
    Map<String, Object> details
) {}
```

---

## DTO Records

```java
// Request — use Jakarta validation
public record CreateUserRequest(
    @NotBlank @Email String email,
    @NotBlank @Size(min = 1, max = 100) String name,
    @NotBlank @Size(min = 8) String password
) {}

// Response — static factory from entity
public record UserResponse(
    UUID id,
    String email,
    String name,
    Role role,
    Instant createdAt
) {
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getId(),
            user.getEmail(),
            user.getName(),
            user.getRole(),
            user.getCreatedAt()
        );
    }
}
```

---

## Flyway Migration

```sql
-- V1__create_users.sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(20)  NOT NULL DEFAULT 'USER',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_email ON users (email);
```

---

## Testing

```java
@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean UserService userService;

    @Test
    void createUser_returns201() throws Exception {
        var request = new CreateUserRequest(
            "a@b.com", "Test", "password123");
        var response = new UserResponse(
            UUID.randomUUID(), "a@b.com", "Test",
            Role.USER, Instant.now()
        );
        given(userService.create(any())).willReturn(response);

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email":"a@b.com","name":"Test",\
                    "password":"password123"}
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.email").value("a@b.com"));
    }

    @Test
    void findById_returns404_whenNotFound() throws Exception {
        var id = UUID.randomUUID();
        given(userService.findById(id))
            .willThrow(new NotFoundException("User", id));

        mockMvc.perform(get("/api/v1/users/" + id))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.code").value("NOT_FOUND"));
    }
}
```
