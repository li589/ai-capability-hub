# Spring Data Redis — Boot 4

**Spring Boot**: 4.0.x | **Spring Data Redis**: aligned with Boot BOM | **Jakarta EE**: 11

---

## Table of Contents

1. [Dependencies](#1-dependencies)
2. [application.yaml](#2-applicationyaml)
3. [RedisTemplate and StringRedisTemplate](#3-redistemplate-and-stringredistemplate)
4. [Redis as cache backend](#4-redis-as-cache-backend)
5. [Pub/Sub (optional)](#5-pubsub-optional)
6. [Session store (optional)](#6-session-store-optional)

---

## 1. Dependencies

Spring Boot 4 BOM manages Spring Data Redis. Add the starter:

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-data-redis")
    // Optional: use Redis as distributed cache backend (see section 4)
    // implementation("org.springframework.boot:spring-boot-starter-cache")
}
```

For connection pooling (Lettuce is the default client):

```kotlin
// Lettuce is included transitively; no extra dependency for basic use
```

---

## 2. application.yaml

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      password:                    # set in production
      timeout: 2000ms
      lettuce:
        pool:
          max-active: 16
          max-idle: 8
          min-idle: 4
```

For a single Redis URL:

```yaml
spring:
  data:
    redis:
      url: redis://user:password@localhost:6379/0
```

---

## 3. RedisTemplate and StringRedisTemplate

Use `StringRedisTemplate` for string keys/values; use `RedisTemplate<String, Object>` (with a configured serializer) for objects. Prefer strings when possible for simplicity and interoperability.

```java
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class TokenStore {

    private final StringRedisTemplate redis;

    public TokenStore(StringRedisTemplate redis) {
        this.redis = redis;
    }

    public void save(String key, String value, java.time.Duration ttl) {
        var ops = redis.opsForValue();
        ops.set(key, value, ttl);
    }

    public String get(String key) {
        return redis.opsForValue().get(key);
    }
}
```

Hashes and lists:

```java
redis.opsForHash().put("user:1", "name", "Alice");
redis.opsForHash().put("user:1", "email", "alice@example.com");
redis.opsForList().rightPush("queue:tasks", taskId);
```

Use Records or simple DTOs when storing JSON; serialize with Jackson and store as string, or use `RedisTemplate<String, YourRecord>` with `GenericJackson2JsonRedisSerializer` (ensure Jakarta and Boot 4 Jackson versions align).

---

## 4. Redis as cache backend

For distributed caching, use Redis instead of Caffeine. Enable caching and set the cache type to Redis:

```yaml
spring:
  cache:
    type: redis
    cache-names: products,users
  data:
    redis:
      host: localhost
      port: 6379
```

```java
@SpringBootApplication
@EnableCaching
public class Application { ... }
```

Use `@Cacheable`, `@CacheEvict`, `@CachePut` as with any Spring Cache backend. TTL can be configured per cache via `spring.cache.redis.time-to-live` or custom `RedisCacheConfiguration` if needed.

Dependencies: `spring-boot-starter-cache` and `spring-boot-starter-data-redis`. No extra starter for Redis cache; Boot auto-configures it when `type: redis` is set.

---

## 5. Pub/Sub (optional)

Publish messages with `RedisTemplate`:

```java
redis.convertAndSend("notifications", "User signed up: " + userId);
```

Subscribe with a listener:

```java
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.RedisMessageListenerContainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RedisPubSubConfig {

    @Bean
    RedisMessageListenerContainer redisMessageListenerContainer(
            org.springframework.data.redis.connection.RedisConnectionFactory factory,
            NotificationSubscriber subscriber) {
        var container = new RedisMessageListenerContainer();
        container.setConnectionFactory(factory);
        container.addMessageListener(subscriber, new ChannelTopic("notifications"));
        return container;
    }
}
```

Implement `MessageListener` and handle `message.getBody()` in `onMessage`.

---

## 6. Session store (optional)

To store HTTP sessions in Redis, add Spring Session:

```kotlin
implementation("org.springframework.session:spring-session-data-redis")
```

Configure session timeout and optionally namespace in `application.yaml`. Sessions are then stored in Redis instead of in-memory; suitable for multi-instance deployments. Security and session configuration remain in Spring Security 7; see `references/spring-security-7.md` for auth.

---

**Summary:** Use `spring-boot-starter-data-redis` with Boot 4 BOM, configure host/port/pool in `application.yaml`, and use `StringRedisTemplate` or `RedisTemplate` for keys/values, hashes, and lists. Use `spring.cache.type=redis` for distributed cache; optionally use pub/sub or Spring Session Data Redis for sessions.
