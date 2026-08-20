# Spring Data MongoDB — Boot 4

**Spring Boot**: 4.0.x | **Spring Data MongoDB**: aligned with Boot BOM | **Jakarta EE**: 11

---

## Table of Contents

1. [Dependencies](#1-dependencies)
2. [application.yaml](#2-applicationyaml)
3. [Documents and @Document](#3-documents-and-document)
4. [MongoRepository](#4-mongorepository)
5. [MongoTemplate](#5-mongotemplate)
6. [Transactions and indexes](#6-transactions-and-indexes)

---

## 1. Dependencies

Spring Boot 4 BOM manages Spring Data MongoDB. Add the starter:

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-data-mongodb")
}
```

---

## 2. application.yaml

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/mydb
      # or separately:
      # host: localhost
      # port: 27017
      # database: mydb
      # username: app
      # password: secret
```

For connection pool tuning (MongoDB driver):

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/mydb
      auto-index-creation: true
```

---

## 3. Documents and @Document

Use a Java record or class with `@Document` and `@Id`. Prefer records for DTOs; for entities that need lazy loading or complex mapping, a class is fine.

```java
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.index.Indexed;

@Document(collection = "products")
public record Product(
    @Id String id,
    String name,
    @Indexed String sku,
    java.math.BigDecimal price
) {}
```

For mutable entities (e.g. append-only fields), use a class with getters/setters and `@Id` on the identifier field.

---

## 4. MongoRepository

Extend `MongoRepository<Entity, IdType>` for CRUD and query methods. Use `String` as ID type for MongoDB ObjectId-backed ids.

```java
import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface ProductRepository extends MongoRepository<Product, String> {

    List<Product> findByName(String name);

    List<Product> findByPriceBetween(java.math.BigDecimal min, java.math.BigDecimal max);

    boolean existsBySku(String sku);
}
```

Custom queries with `@Query`:

```java
@Query("{ 'name' : { $regex: ?0, $options: 'i' } }")
List<Product> findByNameRegex(String pattern);
```

Use `MongoRepository` when you need standard CRUD and derived queries; use `MongoTemplate` for dynamic queries or aggregations (see [Spring Data MongoDB docs](https://docs.spring.io/spring-data/mongodb/reference/) for aggregation pipelines).

---

## 5. MongoTemplate

For programmatic or dynamic queries, inject `MongoTemplate`:

```java
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Service;

@Service
public class ProductService {

    private final MongoTemplate mongo;

    public ProductService(MongoTemplate mongo) {
        this.mongo = mongo;
    }

    public Product findById(String id) {
        return mongo.findById(id, Product.class);
    }

    public List<Product> findBySku(String sku) {
        return mongo.find(Query.query(Criteria.where("sku").is(sku)), Product.class);
    }

    public Product insert(Product product) {
        return mongo.insert(product);
    }

    public void updatePrice(String id, java.math.BigDecimal price) {
        mongo.updateFirst(
            Query.query(Criteria.where("id").is(id)),
            Update.update("price", price),
            Product.class
        );
    }
}
```

---

## 6. Transactions and indexes

**Transactions:** Supported when MongoDB is run as a replica set. Enable with `@Transactional` on the method (or class). Spring Data MongoDB uses the same transaction manager as other Spring Data stores when configured.

```java
@Transactional
public void transfer(Product from, Product to, int qty) {
    // multiple read/write operations in one transaction
}
```

**Indexes:** Use `@Indexed` on fields for single-field indexes. For compound or custom indexes, create them at startup via `MongoTemplate.indexOps(Product.class).ensureIndex(new Index().on("name", Sort.Direction.ASC).on("price", Sort.Direction.DESC))` or with `@CompoundIndex` on the document class. Set `spring.data.mongodb.auto-index-creation: true` in development; in production, manage indexes via migrations or infrastructure as code.

---

**Summary:** Use `spring-boot-starter-data-mongodb` with Boot 4 BOM, configure URI (or host/port/database) in `application.yaml`, and model documents with `@Document` and `@Id`. Use `MongoRepository` for CRUD and derived queries; use `MongoTemplate` for dynamic or programmatic access. Use transactions on replica sets and define indexes via `@Indexed` or programmatic API. For aggregation pipelines, see the official Spring Data MongoDB reference.
