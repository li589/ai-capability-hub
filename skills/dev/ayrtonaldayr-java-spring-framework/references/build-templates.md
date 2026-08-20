# Build Templates — Spring Boot 4 / Spring Framework 7 (2026)

---

## Table of Contents
1. [Gradle KTS — Full Application Template](#1-gradle-kts--full-application-template)
2. [Maven POM — Full Application Template](#2-maven-pom--full-application-template)
3. [Key BOM Versions (2026)](#3-key-bom-versions-2026)
4. [Spring Initializr CLI Quick Start](#4-spring-initializr-cli-quick-start)

---

## 1. Gradle KTS — Full Application Template

```kotlin
// build.gradle.kts
import org.springframework.boot.gradle.tasks.bundling.BootJar

plugins {
    java
    id("org.springframework.boot")          version "4.0.3"
    id("io.spring.dependency-management")   version "1.1.7"
    id("org.graalvm.buildtools.native")     version "0.10.4"   // optional: native image
}

group   = "com.example"
version = "0.0.1-SNAPSHOT"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(25)
    }
}

// Enable preview features (Structured Concurrency, Scoped Values GA in Java 25)
tasks.withType<JavaCompile> {
    options.compilerArgs.addAll(listOf("--enable-preview"))
}

tasks.withType<Test> {
    jvmArgs("--enable-preview")
    useJUnitPlatform()
}

tasks.named<BootJar>("bootJar") {
    jvmArguments.addAll(listOf("--enable-preview"))
}

repositories {
    mavenCentral()
}

dependencyManagement {
    imports {
        mavenBom("org.springframework.modulith:spring-modulith-bom:2.0.3")
    }
}

dependencies {
    // --- Web ---
    implementation("org.springframework.boot:spring-boot-starter-web")
    // implementation("org.springframework.boot:spring-boot-starter-webflux")  // reactive

    // --- Data ---
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-jdbc")
    runtimeOnly("org.postgresql:postgresql")
    // runtimeOnly("com.h2database:h2")   // dev/test

    // --- Validation ---
    implementation("org.springframework.boot:spring-boot-starter-validation")

    // --- Security ---
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-resource-server")

    // --- Observability ---
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("io.micrometer:micrometer-tracing-bridge-otel")
    implementation("io.opentelemetry:opentelemetry-exporter-otlp")
    runtimeOnly("io.micrometer:micrometer-registry-prometheus")

    // --- Null Safety ---
    implementation("org.jspecify:jspecify:1.0.0")

    // --- Spring Modulith (optional) ---
    implementation("org.springframework.modulith:spring-modulith-starter-core")
    implementation("org.springframework.modulith:spring-modulith-starter-jpa")

    // --- Dev Tools ---
    developmentOnly("org.springframework.boot:spring-boot-devtools")
    annotationProcessor("org.springframework.boot:spring-boot-configuration-processor")

    // --- Testing ---
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation("org.springframework.modulith:spring-modulith-starter-test")
    testImplementation("org.testcontainers:postgresql")
    testImplementation("org.testcontainers:junit-jupiter")
}
```

---

## 2. Maven POM — Full Application Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
             https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>4.0.3</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <packaging>jar</packaging>

    <properties>
        <java.version>25</java.version>
        <spring-modulith.version>2.0.3</spring-modulith.version>
        <jspecify.version>1.0.0</jspecify.version>
    </properties>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.modulith</groupId>
                <artifactId>spring-modulith-bom</artifactId>
                <version>${spring-modulith.version}</version>
                <scope>import</scope>
                <type>pom</type>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <dependencies>
        <!-- Web -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <!-- Data -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Validation -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <!-- Security -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
        </dependency>

        <!-- Observability -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>io.micrometer</groupId>
            <artifactId>micrometer-tracing-bridge-otel</artifactId>
        </dependency>
        <dependency>
            <groupId>io.opentelemetry</groupId>
            <artifactId>opentelemetry-exporter-otlp</artifactId>
        </dependency>

        <!-- Null Safety -->
        <dependency>
            <groupId>org.jspecify</groupId>
            <artifactId>jspecify</artifactId>
            <version>${jspecify.version}</version>
        </dependency>

        <!-- Spring Modulith -->
        <dependency>
            <groupId>org.springframework.modulith</groupId>
            <artifactId>spring-modulith-starter-core</artifactId>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.modulith</groupId>
            <artifactId>spring-modulith-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>postgresql</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <compilerArgs>
                        <arg>--enable-preview</arg>
                    </compilerArgs>
                </configuration>
            </plugin>
        </plugins>
    </build>

    <!-- GraalVM Native Image (optional) -->
    <profiles>
        <profile>
            <id>native</id>
            <build>
                <plugins>
                    <plugin>
                        <groupId>org.graalvm.buildtools</groupId>
                        <artifactId>native-maven-plugin</artifactId>
                    </plugin>
                </plugins>
            </build>
        </profile>
    </profiles>
</project>
```

---

## 3. Key BOM Versions (2026)

| Library | Version |
|---|---|
| Spring Boot | 4.0.3 |
| Spring Framework | 7.0.5 |
| Spring Modulith | 2.0.3 |
| Spring Security | 7.x (managed by Boot) |
| Spring Data | 4.x (managed by Boot) |
| Hibernate ORM | 7.0 |
| JSpecify | 1.0.0 |
| Jackson | 3.x |
| GraalVM Build Tools | 0.10.4 |
| Testcontainers | 1.21.x |
| JUnit 5 | 5.12.x |
| Micrometer | 1.15.x |
| io.spring.dependency-management | 1.1.7 |

When updating BOM versions, keep the CLI templates under `templates/` and this reference in sync.

---

## 4. Spring Initializr CLI Quick Start

```bash
# Using Spring CLI (spring init)
spring init \
  --boot-version=4.0.3 \
  --java-version=25 \
  --build=gradle-project-kotlin \
  --dependencies=web,data-jpa,postgresql,security,actuator,validation,devtools \
  --group-id=com.example \
  --artifact-id=my-service \
  --name=MyService \
  my-service

# Or via curl to start.spring.io
curl https://start.spring.io/starter.tgz \
  -d type=gradle-project-kotlin \
  -d bootVersion=4.0.3 \
  -d javaVersion=25 \
  -d dependencies=web,data-jpa,postgresql,security,actuator,validation \
  -d groupId=com.example \
  -d artifactId=my-service \
  | tar -xzvf -
```
