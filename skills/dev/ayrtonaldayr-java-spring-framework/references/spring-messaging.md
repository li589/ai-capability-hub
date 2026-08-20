# Spring Messaging (Kafka) — Boot 4

**Spring Boot**: 4.0.x | **Spring Kafka**: aligned with Boot BOM | **Jakarta EE**: 11

---

## Table of Contents

1. [Dependencies](#1-dependencies)
2. [application.yaml](#2-applicationyaml)
3. [Consumer — @KafkaListener](#3-consumer--kafkalistener)
4. [Producer](#4-producer)
5. [Records for payloads](#5-records-for-payloads)

---

## 1. Dependencies

Spring Boot 4 BOM manages Spring Kafka. Add the starter:

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springframework.kafka:spring-kafka")
    // or explicitly:
    // implementation("org.springframework.boot:spring-boot-starter-web")  // or webflux
    // implementation("org.springframework.kafka:spring-kafka")
}
```

For JSON (de)serialization with Jackson 3 (Jakarta):

```kotlin
implementation("org.springframework.kafka:spring-kafka")
// Jackson is provided by Boot; ensure jakarta.* for JSON
```

---

## 2. application.yaml

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    consumer:
      group-id: my-app
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      properties:
        spring.json.trusted.packages: "*"
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
```

---

## 3. Consumer — @KafkaListener

Use Records for message payloads where possible. Listen on a topic and process with Jakarta and JSpecify where applicable.

```java
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

@Component
public class OrderEventsConsumer {

    @KafkaListener(topics = "orders", groupId = "my-app")
    public void onOrder(@Payload OrderEvent event,
                        @Header(KafkaHeaders.RECEIVED_KEY) String key) {
        // process event (OrderEvent as record)
    }
}
```

With batch consumption:

```java
@KafkaListener(topics = "orders", groupId = "my-app", containerFactory = "batchFactory")
public void onOrders(@Payload List<OrderEvent> events) {
    events.forEach(this::process);
}
```

---

## 4. Producer

Inject `KafkaTemplate` and send records. Use `JsonSerializer` for value when configured in application.yaml.

```java
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class OrderEventsProducer {

    private final KafkaTemplate<String, OrderEvent> kafkaTemplate;

    public OrderEventsProducer(KafkaTemplate<String, OrderEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void send(OrderEvent event) {
        kafkaTemplate.send("orders", event.orderId(), event);
    }
}
```

For a simple `KafkaTemplate<String, Object>` with JSON, ensure your payload type is on the trusted packages list for the consumer’s `JsonDeserializer`.

---

## 5. Records for payloads

Prefer Java records for event DTOs (Jackson 3 supports them):

```java
public record OrderEvent(String orderId, String productId, int quantity, java.time.Instant at) {}
```

Use `jakarta.*` and JSpecify nullability in shared libraries if you need strict null contracts; for internal events, records are often sufficient.

---

**Summary:** Use `spring-kafka` with Boot 4 BOM, configure bootstrap servers and (de)serializers in `application.yaml`, and use `@KafkaListener` for consumers and `KafkaTemplate` for producers. Prefer records for event payloads. For Spring Cloud Stream (bindings), see the Spring Cloud Stream docs; the same Kafka dependencies can be used with Stream if you add the appropriate starters.
