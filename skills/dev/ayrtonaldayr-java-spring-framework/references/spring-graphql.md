# Spring for GraphQL — Boot 4

**Spring Boot**: 4.0.x | **Spring for GraphQL**: aligned with Boot BOM | **Jakarta EE**: 11

---

## Table of Contents

1. [Dependencies](#1-dependencies)
2. [application.yaml](#2-applicationyaml)
3. [Schema (SDL)](#3-schema-sdl)
4. [Query and mutation controllers](#4-query-and-mutation-controllers)
5. [Records for types](#5-records-for-types)
6. [Security](#6-security)

---

## 1. Dependencies

Spring Boot 4 BOM manages Spring for GraphQL. Add the starter:

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-graphql")
    implementation("org.springframework.boot:spring-boot-starter-web")  // or webflux
}
```

---

## 2. application.yaml

```yaml
spring:
  graphql:
    graphiql:
      enabled: true   # dev: UI at /graphiql
    path: /graphql    # default
    cors:
      allowed-origins: "https://myapp.example.com"
```

The GraphQL endpoint is exposed at `spring.graphql.path` (default `/graphql`). Use the same `SecurityFilterChain` as for REST to protect it; see section 6.

---

## 3. Schema (SDL)

Place schema files under `src/main/resources/graphql/**/*.graphqls` (or `.graphqls`). Boot auto-picks them.

Example `src/main/resources/graphql/schema.graphqls`:

```graphql
type Query {
  product(id: ID!): Product
  products(first: Int = 10): [Product!]!
}

type Mutation {
  createProduct(input: CreateProductInput!): Product!
}

type Product {
  id: ID!
  name: String!
  sku: String!
  price: Float!
}

input CreateProductInput {
  name: String!
  sku: String!
  price: Float!
}
```

---

## 4. Query and mutation controllers

Use `@Controller` and `@QueryMapping` / `@MutationMapping`. Method names match schema field names by default, or specify with the annotation.

```java
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.MutationMapping;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.stereotype.Controller;

@Controller
public class ProductGraphQLController {

    private final ProductService productService;

    public ProductGraphQLController(ProductService productService) {
        this.productService = productService;
    }

    @QueryMapping
    public Product product(@Argument String id) {
        return productService.findById(id);
    }

    @QueryMapping
    public java.util.List<Product> products(@Argument Integer first) {
        int limit = first != null ? first : 10;
        return productService.findAll(limit);
    }

    @MutationMapping
    public Product createProduct(@Argument CreateProductInput input) {
        return productService.create(input.name(), input.sku(), input.price());
    }
}
```

For nested types (e.g. `Product` has a `category` field), use `@SchemaMapping` on a method that takes the parent object and returns the nested one:

```java
@SchemaMapping(typeName = "Product", field = "category")
public Category category(Product product) {
    return categoryService.findById(product.categoryId());
}
```

---

## 5. Records for types

Use Java records for DTOs and inputs. Spring for GraphQL maps them to the schema:

```java
public record CreateProductInput(String name, String sku, double price) {}

public record Product(String id, String name, String sku, double price, String categoryId) {}
```

Ensure record component names align with schema field names (or use `@JsonProperty` if names differ). Use `jakarta.*` and JSpecify where applicable for nullability in the API layer.

---

## 6. Security

GraphQL is exposed over HTTP like REST. Protect the GraphQL path in your `SecurityFilterChain` (see `references/spring-security-7.md`): require authentication for `/graphql` and optionally allow anonymous for introspection in dev only. For authenticated GraphQL, clients typically send the same token (e.g. Bearer JWT) in the `Authorization` header; the resolver can access the current user via `SecurityContextHolder` or a custom context in the GraphQL execution.

Restrict introspection in production if you do not want to expose the full schema to unauthenticated clients.

---

**Summary:** Use `spring-boot-starter-graphql` with Boot 4 BOM, define the schema in `.graphqls` under `resources/graphql`, and implement queries and mutations with `@Controller`, `@QueryMapping`, and `@MutationMapping`. Use records for input and output types. Secure the GraphQL endpoint with the same Spring Security 7 configuration as REST.
