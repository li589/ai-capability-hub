# Spring Security 7 — Reference (Boot 4)

**Spring Boot**: 4.0.x | **Spring Security**: 7.0.x | **Jakarta EE**: 11

---

## Table of Contents

1. [Dependencies](#1-dependencies)
2. [OAuth2 Resource Server (JWT)](#2-oauth2-resource-server-jwt)
3. [SecurityFilterChain (Lambda DSL)](#3-securityfilterchain-lambda-dsl)
4. [Method Security (@PreAuthorize)](#4-method-security-preauthorize)
5. [CORS](#5-cors)
6. [application.yaml](#6-applicationyaml)
7. [Integration with Keycloak](#7-integration-with-keycloak)

---

## 1. Dependencies

Spring Boot 4 BOM brings Spring Security 7. Add only what you need:

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-resource-server")  // JWT
    implementation("org.springframework.boot:spring-boot-starter-oauth2-client")             // optional: OAuth2 login
}
```

---

## 2. OAuth2 Resource Server (JWT)

Validate JWTs from an authorization server (e.g. OIDC issuer). Lambda DSL is the only supported style in Security 7.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.config.http.SessionCreationPolicy;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**", "/actuator/health").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.decoder(jwtDecoder())))
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .csrf(csrf -> csrf.disable())   // typical for stateless API
            .build();
    }

    @Bean
    JwtDecoder jwtDecoder() {
        return NimbusJwtDecoder.withJwkSetUri("https://auth.example.com/.well-known/jwks.json").build();
    }
}
```

With **issuer-uri** (Boot auto-configures `JwtDecoder`):

```yaml
# application.yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
```

Then omit the custom `JwtDecoder` bean; Boot provides it.

---

## 3. SecurityFilterChain (Lambda DSL)

All security configuration uses the lambda style. Example: form login + API protected by JWT.

```java
import org.springframework.security.config.Customizer;

@Bean
SecurityFilterChain webFilterChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .build();
}
```

---

## 4. Method Security (@PreAuthorize)

Enable method security and use SpEL in annotations (Jakarta namespace).

```java
@Configuration
@EnableMethodSecurity
public class MethodSecurityConfig {}
```

```java
import org.springframework.security.access.prepost.PreAuthorize;

@Service
public class OrderService {

    @PreAuthorize("hasRole('ADMIN') or #userId == authentication.name")
    public Order getOrder(String userId, String orderId) {
        return orderRepository.findById(orderId).orElseThrow();
    }

    @PreAuthorize("hasAuthority('SCOPE_orders:write')")
    public Order create(OrderRequest request) {
        return orderRepository.save(map(request));
    }
}
```

Use `@PreAuthorize` / `@PostAuthorize` for read; `@PreFilter` / `@PostFilter` for filtering collections. All use Jakarta annotations in Spring Security 7.

---

## 5. CORS

Configure CORS in the security pipeline or globally. Example: allow a frontend origin.

```java
import org.springframework.security.config.Customizer;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .cors(cors -> cors.configurationSource(corsConfigurationSource()))
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
        .build();
}

@Bean
CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://app.example.com"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    config.setAllowedHeaders(List.of("*"));
    config.setAllowCredentials(true);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", config);
    return source;
}
```

Or use `WebMvcConfigurer` for non-security CORS only; for APIs with credentials, the above is typical.

---

## 6. application.yaml

Minimal Security 7 + OAuth2 RS settings:

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
          jwk-set-uri: https://auth.example.com/.well-known/jwks.json  # if no issuer-uri

# Optional: restrict actuator by profile
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
```

For **development only**, you can disable security (e.g. with a `SecurityFilterChain` that permits all when a profile is active). Never disable in production.

---

## 7. Integration with Keycloak

**Keycloak** is an OAuth2/OIDC identity provider. Your Spring Boot app acts as a **Resource Server** and validates JWTs issued by Keycloak; you do not implement the authorization server in the app. The same `SecurityFilterChain` and OAuth2 Resource Server setup (sections 2–3) apply; only the configuration of the issuer changes.

**issuer-uri for Keycloak:** Use the realm URL as the issuer. Format: `https://<keycloak-host>/realms/<realm-name>`. Spring Boot discovers the JWK Set from that issuer’s OIDC well-known metadata.

```yaml
# application.yaml — Keycloak realm as issuer
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.acme.com/realms/myapp
          # Optional: validate audience (e.g. Keycloak client ID or resource)
          # audiences: my-backend-api
```

If your Keycloak client or resource is configured to emit an `aud` claim, set `jwt.audiences` to the expected value(s) so that Spring Security validates audience in addition to signature and expiry.

For **browser-based login** (OAuth2 Client / OIDC login) with Keycloak, use `spring-boot-starter-oauth2-client` and configure `spring.security.oauth2.client.provider.keycloak` and a client registration; that is separate from the Resource Server (JWT) setup described here.

---

**Summary:** Use `SecurityFilterChain` with lambda DSL, OAuth2 Resource Server with JWT for APIs, `@EnableMethodSecurity` and `@PreAuthorize` for method-level rules, and configure CORS in the security pipeline when the API is consumed by a browser client. For Keycloak as the authorization server, use section 7 (issuer-uri per realm, optional audience).
