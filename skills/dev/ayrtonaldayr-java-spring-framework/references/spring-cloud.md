# Spring Cloud — Gateway, Config, Discovery (Boot 4)

**Spring Boot**: 4.0.x | **Spring Cloud**: 2025.1.x (Oakwood) | **Jakarta EE**: 11

This reference covers Spring Cloud Gateway (routing and filters), Spring Cloud Config (server and client), and service discovery (Eureka) with concrete examples. Backend services are Spring Boot 4 applications; for security (OAuth2 Resource Server, JWT) see `references/spring-security-7.md`. For microservices design context see `references/microservices-architecture.md`.

---

## Table of Contents

1. [BOM and Dependencies](#1-bom-and-dependencies)
2. [Spring Cloud Gateway — Routing and Filters](#2-spring-cloud-gateway--routing-and-filters)
3. [Gateway Examples](#3-gateway-examples)
4. [Spring Cloud Config — Server and Client](#4-spring-cloud-config--server-and-client)
5. [Config Examples](#5-config-examples)
6. [Service Discovery (Eureka)](#6-service-discovery-eureka)
7. [Discovery Examples](#7-discovery-examples)
8. [Spring Cloud Stream (Optional)](#8-spring-cloud-stream-optional)

---

## 1. BOM and Dependencies

Use the Spring Cloud release train compatible with Spring Boot 4.0.x: **2025.1.x (Oakwood)**. The BOM manages Gateway, Config, and Eureka versions.

**Gradle (Kotlin DSL):**

```kotlin
// build.gradle.kts
plugins {
    java
    id("org.springframework.boot") version "4.0.3"
    id("io.spring.dependency-management") version "1.1.7"
}

dependencyManagement {
    imports {
        mavenBom("org.springframework.cloud:spring-cloud-dependencies:2025.1.1")
    }
}

dependencies {
    // Gateway only (do not add spring-boot-starter-web; Gateway uses Netty)
    implementation("org.springframework.cloud:spring-cloud-starter-gateway")

    // Config server (separate app)
    // implementation("org.springframework.cloud:spring-cloud-config-server")

    // Config client (in each backend service that needs central config)
    // implementation("org.springframework.cloud:spring-cloud-starter-config")

    // Eureka server (separate app)
    // implementation("org.springframework.cloud:spring-cloud-starter-netflix-eureka-server")

    // Eureka client (in each backend service and in Gateway for discovery)
    // implementation("org.springframework.cloud:spring-cloud-starter-netflix-eureka-client")

    // Optional: Redis for Gateway rate limiting
    // implementation("org.springframework.boot:spring-boot-starter-data-redis-reactive")
}
```

**Maven:** Use the same BOM in `pom.xml` under `dependencyManagement` and add the corresponding `spring-cloud-starter-*` artifacts. See the [Spring Cloud release documentation](https://docs.spring.io/spring-cloud/reference/) for the latest BOM version.

---

## 2. Spring Cloud Gateway — Routing and Filters

The **API Gateway** sits in front of your backend services and handles routing by path or host, and filters (add headers, strip prefix, rate limit, JWT validation). Each backend remains a Spring Boot 4 app; see `references/spring-security-7.md` for OAuth2 Resource Server and JWT validation in backends.

- **Dependency:** `spring-cloud-starter-gateway`. Do **not** add `spring-boot-starter-web` in the same application; Gateway uses Netty.
- **Routes** are defined in `application.yaml` (or Java) with predicates (Path, Host, etc.) and filters (StripPrefix, AddRequestHeader, RequestRateLimiter, custom).
- **Discovery:** When using Eureka, use `uri: lb://service-name` so the Gateway resolves the service via discovery.

---

## 3. Gateway Examples

### Example 1: Path route

Route `/api/orders/**` to the order service:

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: http://localhost:8081
          predicates:
            - Path=/api/orders/**
```

Requests to `http://gateway:8080/api/orders/123` are forwarded to `http://localhost:8081/api/orders/123`.

---

### Example 2: Strip prefix

Forward to the backend but remove the first path segment so the backend receives `/orders/...` instead of `/api/orders/...`:

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: http://localhost:8081
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1
```

With `StripPrefix=1`, the path `/api/orders/123` becomes `/orders/123` at the backend. Use `StripPrefix=2` to remove `/api/orders` and send only `/123`.

---

### Example 3: Add request header

Add a header to every request sent to the backend (e.g. for correlation or feature flags):

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: http://localhost:8081
          predicates:
            - Path=/api/orders/**
          filters:
            - AddRequestHeader=X-Gateway, true
            - AddRequestHeader=X-Request-Time, ${requestTime}
```

Backend can read `X-Gateway` and `X-Request-Time` from the request.

---

### Example 4: Route by host

Route by the `Host` header (e.g. for multi-tenant or subdomains):

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders-by-host
          uri: http://order-service:8080
          predicates:
            - Host=orders.example.com
```

Requests with `Host: orders.example.com` go to the order service.

---

### Example 5: Rate limit (RequestRateLimiter)

Limit requests per key (e.g. per IP or per user). The in-memory implementation is suitable for a single Gateway instance; use Redis for a cluster.

**application.yaml:**

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: http://localhost:8081
          predicates:
            - Path=/api/orders/**
          filters:
            - name: RequestRateLimiter
              args:
                key-resolver: "#{@ipKeyResolver}"
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
  data:
    redis:
      host: localhost
      port: 6379
```

For **in-memory** rate limiting (no Redis), you can use a custom `KeyResolver` and a simple in-memory rate limiter; the built-in `RequestRateLimiter` typically expects a Redis connection unless you provide a custom `RateLimiter` implementation. Here we show the Redis-based config; for single-instance Gateways, see the [Spring Cloud Gateway docs](https://docs.spring.io/spring-cloud-gateway/reference/) for alternatives.

**KeyResolver bean (e.g. by IP):**

```java
import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import reactor.core.publisher.Mono;

@Configuration
public class GatewayConfig {

    @Bean
    public KeyResolver ipKeyResolver() {
        return exchange -> Mono.just(
            exchange.getRequest().getRemoteAddress() != null
                ? exchange.getRequest().getRemoteAddress().getAddress().getHostAddress()
                : "unknown"
        );
    }
}
```

---

### Example 6: JWT at edge

Validate JWT in the Gateway and only forward valid requests. You can use Spring Security in the Gateway app (`spring-boot-starter-security` + `spring-boot-starter-oauth2-resource-server`) so the Gateway acts as an OAuth2 Resource Server; see `references/spring-security-7.md` for JWT configuration. Alternatively, a custom `GatewayFilter` can validate the `Authorization: Bearer <token>` header and return 401 if invalid:

```java
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class JwtValidationFilter implements GlobalFilter, Ordered {

    private final org.springframework.security.oauth2.jwt.JwtDecoder jwtDecoder;

    public JwtValidationFilter(org.springframework.security.oauth2.jwt.JwtDecoder jwtDecoder) {
        this.jwtDecoder = jwtDecoder;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String auth = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (auth == null || !auth.startsWith("Bearer ")) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        String token = auth.substring(7);
        try {
            jwtDecoder.decode(token);
            return chain.filter(exchange);
        } catch (Exception e) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
    }

    @Override
    public int getOrder() {
        return -1;
    }
}
```

Configure `JwtDecoder` (issuer-uri or jwk-set-uri) as in `references/spring-security-7.md`. For production, also validate audience and expiration; the Resource Server support in Spring Security handles this when the Gateway uses OAuth2 Resource Server.

---

## 4. Spring Cloud Config — Server and Client

- **Config Server:** A separate Spring Boot application that serves configuration from a Git repository (or filesystem). Add `spring-cloud-config-server` and enable it with `@EnableConfigServer`.
- **Config Client:** Backend services that fetch config at bootstrap using `spring.config.import=optional:configserver:http://config-server:8888`. The client uses `spring.application.name` (and optional profile) to request e.g. `order-service.yml` from the server.

See the [Spring Cloud Config reference](https://docs.spring.io/spring-cloud-config/reference/) for full options.

---

## 5. Config Examples

### Example 1: Config server with Git backend

**Dependencies:** `spring-cloud-config-server`.

**application.yaml (Config Server):**

```yaml
server:
  port: 8888

spring:
  application:
    name: config-server
  cloud:
    config:
      server:
        git:
          uri: https://github.com/your-org/config-repo.git
          default-label: main
```

**Main class:**

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.config.server.EnableConfigServer;

@EnableConfigServer
@SpringBootApplication
public class ConfigServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

The server serves files like `order-service.yml` or `order-service-prod.yml` from the Git repo based on `spring.application.name` and `spring.profiles.active` of the client.

---

### Example 2: Config client bootstrap

**Dependencies:** `spring-cloud-starter-config`.

**application.yaml (e.g. order-service):**

```yaml
spring:
  application:
    name: order-service
  config:
    import: optional:configserver:http://localhost:8888
```

If the Config Server is unavailable, `optional:` allows the app to start with local config only. The client requests configuration for `order-service` and, if profile `prod` is active, the server can return `order-service-prod.yml` from Git.

**Profile-specific:** In the Git repo, add `order-service.yml` (default) and `order-service-prod.yml` (for profile `prod`). The server merges them by name and profile.

---

## 6. Service Discovery (Eureka)

When services need to find each other by **name** (e.g. `order-service`) instead of fixed URLs, use a discovery mechanism. **Eureka** is a common choice in the Spring ecosystem; alternatives include Consul and Kubernetes services. For when to use discovery vs static URLs or gateway routing, see `references/microservices-architecture.md` (section 6).

- **Eureka Server:** One application that holds the registry; other apps register and fetch the registry.
- **Eureka Client:** Each Boot 4 service (and the Gateway) registers itself and can resolve `lb://service-name` to actual instances.

---

## 7. Discovery Examples

### Example 1: Eureka server

**Dependencies:** `spring-cloud-starter-netflix-eureka-server`. Do not add `spring-boot-starter-web` if you want the default Eureka server setup; the Eureka starter brings the right dependencies.

**application.yaml:**

```yaml
server:
  port: 8761

eureka:
  instance:
    hostname: localhost
  client:
    register-with-eureka: false
    fetch-registry: false
```

**Main class:**

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@EnableEurekaServer
@SpringBootApplication
public class EurekaServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

---

### Example 2: Eureka client (order-service)

**Dependencies:** `spring-cloud-starter-netflix-eureka-client`.

**application.yaml:**

```yaml
spring:
  application:
    name: order-service

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
```

The service registers as `order-service`; other clients (or the Gateway) can resolve it by name.

---

### Example 3: Gateway with discovery (lb://)

Use **load-balanced** URIs so the Gateway resolves the backend via Eureka:

**application.yaml (Gateway):**

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1
```

With Eureka client on the Gateway and `lb://order-service`, the Gateway discovers instances of `order-service` and load-balances across them. Ensure the Gateway has `spring-cloud-starter-netflix-eureka-client` and `eureka.client.service-url.defaultZone` configured.

---

## 8. Spring Cloud Stream (Optional)

For **bindings-based** Kafka (or other bindings) where consumers and producers are configured via `spring.cloud.stream.bindings.*`, use [spring-messaging.md](spring-messaging.md) for the underlying Kafka setup and the [Spring Cloud Stream reference](https://docs.spring.io/spring-cloud-stream/reference/). The same Kafka dependencies can be used; add the Stream starters for the binding abstraction. This reference does not cover Stream bindings in detail.

---

**Summary:** Use the Spring Cloud 2025.1.x BOM with Boot 4. For **Gateway**, define routes and filters (path, strip prefix, headers, rate limit, JWT) in YAML or Java. For **Config**, run a Config Server with a Git backend and use `spring.config.import=optional:configserver:...` in clients. For **Discovery**, run an Eureka server and register clients; use `lb://service-name` in the Gateway for load-balanced routing. For OAuth2/JWT in backends, see `references/spring-security-7.md`.
