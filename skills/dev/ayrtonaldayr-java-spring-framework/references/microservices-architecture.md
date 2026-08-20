# Microservices Architecture — Spring Boot 4

**Spring Boot**: 4.0.x | Microservices design | **Jakarta EE**: 11

This reference covers when to choose microservices vs a modular monolith, service boundaries, inter-service communication, API Gateway, and distributed observability. For building each service, use `references/spring-boot-4.md`, `references/spring-framework-7.md`, and for event-driven messaging `references/spring-messaging.md`. For a modular monolith alternative, see `references/spring-modulith.md`.

---

## Table of Contents

1. [When to Choose Microservices vs Modular Monolith (Modulith)](#1-when-to-choose-microservices-vs-modular-monolith-modulith)
2. [Service Boundaries](#2-service-boundaries)
3. [Inter-Service Communication](#3-inter-service-communication)
4. [API Gateway](#4-api-gateway)
5. [Distributed Observability](#5-distributed-observability)
6. [Config and Discovery (Optional)](#6-config-and-discovery-optional)

---

## 1. When to Choose Microservices vs Modular Monolith (Modulith)

| Factor | Prefer Modulith (modular monolith) | Prefer Microservices |
|--------|-------------------------------------|----------------------|
| **Team structure** | Single team or few teams; shared codebase is manageable | Multiple teams owning different services; need independent delivery |
| **Scaling** | Scale the whole application (e.g. more replicas of the same process) | Scale individual services (e.g. only the heavy-read service) |
| **Deployment** | One deployable; simpler pipelines and rollbacks | Independent deploy per service; more operational complexity |
| **Transactions** | Single database or local transactions across modules | Distributed transactions are hard; prefer eventual consistency and events |
| **Latency** | In-process calls; low latency between modules | Network calls between services; higher latency and failure modes |
| **Domain** | Domains are related; modules can communicate via events in one process | Bounded contexts are clearly separate (e.g. different companies or products) |

Start with a **modular monolith** (Modulith) when the domain and team do not clearly demand separate deployments and scaling. Extract to microservices when you hit real limits (team boundaries, scaling, technology diversity). See `references/spring-modulith.md` for module structure and event-driven communication inside one application.

---

## 2. Service Boundaries

- **One service = one bounded context** (or a cohesive subdomain). Avoid sharing a single database across services; each service typically owns its own data store. This reduces coupling and allows independent schema evolution.
- **API contracts:** Define clear contracts between services. For REST, use **OpenAPI**; generate client DTOs or use a shared library. Document and version the API (e.g. URL path or header). See the OpenAPI/springdoc section in `references/spring-boot-4.md` for exposing and documenting REST APIs from each service.
- **Database per service:** Each service uses its own database (or schema). Replicate data across services only via events or explicit sync APIs when necessary; avoid distributed transactions.

---

## 3. Inter-Service Communication

**Synchronous (request/response):** Use **RestClient** (see `references/spring-framework-7.md`) to call other services. Share contracts (OpenAPI spec or DTOs). Handle timeouts, retries, and circuit breakers; Spring 7’s resilience annotations (`@Retryable`, `@CircuitBreaker`) can wrap outbound calls. For high-throughput or low-latency sync, consider gRPC in addition to REST.

**Asynchronous (events):** Use **Kafka** (or similar) for cross-service events. The producer service publishes domain events; consumer services subscribe and update their own state. Prefer events when you need decoupling, resilience (consumer can process later), or audit. See `references/spring-messaging.md` for producers and `@KafkaListener` consumers. Design for **idempotency** (consumer can process the same message twice safely) and **ordering** (partition by key when order matters).

**When to use which:** Use sync when the caller needs an immediate response (e.g. “get order by ID”). Use async when the operation can complete later or when multiple services react to the same event (e.g. “order placed” → inventory, notifications, analytics).

---

## 4. API Gateway

An **API Gateway** sits in front of your services and handles routing, authentication/authorization at the edge, rate limiting, and sometimes aggregation. **Spring Cloud Gateway** is the Spring-based option: you configure routes (e.g. by path or host), filters (JWT validation, rate limiting), and point to backend services. Rate limiting at the gateway was mentioned in `references/spring-boot-4.md` (Rate limiting) as an alternative to in-app Bucket4j.

For examples of routes, filters (strip prefix, headers, rate limit, JWT) and YAML configuration, see `references/spring-cloud.md`. For full route and filter reference, see the [Spring Cloud Gateway documentation](https://docs.spring.io/spring-cloud-gateway/reference/). Each backend service remains a Spring Boot application with its own security (e.g. OAuth2 Resource Server) as in `references/spring-security-7.md`.

---

## 5. Distributed Observability

**Distributed tracing:** Propagate a **trace ID** across service boundaries so a single request can be followed through multiple services. **OpenTelemetry** (OTEL) with W3C Trace Context headers is the standard. Each Spring Boot 4 service enables Actuator and OTEL as in `references/spring-boot-4.md` (Actuator & Observability). Ensure the HTTP client (RestClient) and Kafka producers/consumers propagate trace context; Boot’s OTEL integration typically does this when configured. The collector receives spans from all services and correlates them by trace ID.

**Metrics and logs:** Each service exposes metrics (e.g. Prometheus) and logs in a consistent format. Aggregate metrics and logs in a central platform (e.g. Grafana, centralized logging). Use the same stack (Micrometer, OTEL) in every service for consistency. See `references/spring-boot-4.md` for Actuator, OTEL export, and health groups.

---

## 6. Config and Discovery (Optional)

**Centralized config:** **Spring Cloud Config** can provide configuration (e.g. `application.yaml`) to multiple services from a central server. Use it when you need to change config without redeploying each service. For examples of Config server (Git backend) and client bootstrap, see `references/spring-cloud.md`. See the [Spring Cloud Config documentation](https://docs.spring.io/spring-cloud-config/reference/) for full setup.

**Service discovery:** When services need to find each other by name (e.g. “order-service” instead of a fixed URL), use a discovery mechanism (e.g. Consul, Eureka, or Kubernetes services). Spring Cloud supports discovery clients; each service registers itself and resolves others by name. For Eureka server, client registration, and Gateway with `lb://service-name`, see `references/spring-cloud.md`. This is optional; you can also use static URLs or a gateway that routes by path.

---

**Summary:** Choose **microservices** when team boundaries, independent scaling, or deployment justify the operational cost; otherwise start with a **modular monolith** (Modulith). Define **service boundaries** around bounded contexts and avoid shared databases. Use **RestClient** for sync and **Kafka** for async communication; design for idempotency and ordering. Put an **API Gateway** (e.g. Spring Cloud Gateway) at the edge for routing and auth. Use **OpenTelemetry** and propagate trace context so you get **distributed observability** across all services.
