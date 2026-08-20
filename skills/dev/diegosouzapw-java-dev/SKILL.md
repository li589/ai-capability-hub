---
name: java-dev
description: Java 开发规范，包含命名约定、异常处理、Spring Boot 最佳实践等
version: 1.0.0
paths:
  - "**/*.java"
  - "**/pom.xml"
  - "**/build.gradle"
  - "**/build.gradle.kts"
install_source: official
install_method: download
skill_id: official_QNHn1uzy
enabled_at: 1787231580803
name_zh: Java开发规范
---

# Java 开发规范

> 参考来源: Google Java Style Guide、阿里巴巴 Java 开发手册

---

## 工具链

```bash
# Maven
mvn clean compile                    # 编译
mvn test                             # 运行测试
mvn verify                           # 运行所有检查

# Gradle
./gradlew build                      # 构建
./gradlew test                       # 运行测试
```

---

## 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 包名 | 全小写，域名反转 | `com.example.project` |
| 类名 | 大驼峰，名词/名词短语 | `UserService`, `HttpClient` |
| 方法名 | 小驼峰，动词开头 | `findById`, `isValid` |
| 常量 | 全大写下划线分隔 | `MAX_RETRY_COUNT` |
| 布尔返回值 | is/has/can 前缀 | `isActive()`, `hasPermission()` |

---

## 类成员顺序

```java
public class Example {
    // 1. 静态常量
    public static final String CONSTANT = "value";

    // 2. 静态变量
    private static Logger logger = LoggerFactory.getLogger(Example.class);

    // 3. 实例变量
    private Long id;

    // 4. 构造函数
    public Example() { }

    // 5. 静态方法
    public static Example create() { return new Example(); }

    // 6. 实例方法（公共 → 私有）
    public void doSomething() { }
    private void helperMethod() { }

    // 7. getter/setter（或使用 Lombok）
}
```

---

## 异常处理

```java
// ✅ 好：捕获具体异常，添加上下文
try {
    user = userRepository.findById(id);
} catch (DataAccessException e) {
    throw new ServiceException("Failed to find user: " + id, e);
}

// ✅ 好：资源自动关闭
try (InputStream is = new FileInputStream(file)) {
    // 使用资源
}

// ❌ 差：捕获过宽
catch (Exception e) { e.printStackTrace(); }
```

---

## 空值处理

```java
// ✅ 使用 Optional
public Optional<User> findById(Long id) {
    return userRepository.findById(id);
}

// ✅ 参数校验
public void updateUser(User user) {
    Objects.requireNonNull(user, "user must not be null");
}

// ✅ 安全的空值处理
String name = Optional.ofNullable(user)
    .map(User::getName)
    .orElse("Unknown");
```

---

## 并发编程

```java
// ✅ 使用 ExecutorService
ExecutorService executor = Executors.newFixedThreadPool(10);
Future<Result> future = executor.submit(() -> doWork());

// ✅ 使用 CompletableFuture
CompletableFuture<User> future = CompletableFuture
    .supplyAsync(() -> findUser(id))
    .thenApply(user -> enrichUser(user));

// ❌ 差：直接创建线程
new Thread(() -> doWork()).start();
```

---

## 测试规范 (JUnit 5)

```java
class UserServiceTest {
    @Test
    @DisplayName("根据 ID 查找用户 - 用户存在时返回用户")
    void findById_whenUserExists_returnsUser() {
        // given
        when(userRepository.findById(1L)).thenReturn(Optional.of(expected));

        // when
        Optional<User> result = userService.findById(1L);

        // then
        assertThat(result).isPresent();
        assertThat(result.get().getName()).isEqualTo("test");
    }
}
```

---

## Spring Boot 规范

```java
// ✅ 构造函数注入
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}

// ✅ REST Controller
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public ResponseEntity<UserDto> findById(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```

---

## 性能优化

| 陷阱 | 解决方案 |
|------|---------|
| N+1 查询 | 使用 JOIN FETCH 或批量查询 |
| 循环拼接字符串 | 使用 `StringBuilder` |
| 频繁装箱拆箱 | 使用原始类型流 |
| 未指定集合初始容量 | `new ArrayList<>(size)` |

---

## 日志规范

```java
// ✅ 参数化日志
log.debug("Finding user by id: {}", userId);
log.info("User {} logged in successfully", username);
log.error("Failed to process order {}", orderId, exception);

// ❌ 差：字符串拼接
log.debug("Finding user by id: " + userId);
```

---

## 详细参考

| 文件 | 内容 |
|------|------|
| `references/java-style.md` | 命名约定、异常处理、Spring Boot、测试规范 |
| `references/collections.md` | 不可变集合（Guava）、字符串分割 |
| `references/concurrency.md` | 线程池配置、CompletableFuture 超时 |
| `references/code-patterns.md` | 卫语句、枚举优化、策略工厂模式 |

---

> 📋 本回复遵循：`java-dev` - [具体章节]
