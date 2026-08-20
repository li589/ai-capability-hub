# Recommended Base Images

Last updated: 2026-01

**Priority**: Always detect the local runtime version first. Only use this file as a fallback.

## Local Version Detection

Detect the user's local version before selecting a base image. This ensures consistency between development and production.

### Version Config Files

| Runtime | Config Files |
|---------|--------------|
| Node.js | `.nvmrc`, `.node-version`, `engines.node` in package.json, `volta.node` in package.json |
| Python | `.python-version`, `[tool.poetry.dependencies].python` in pyproject.toml, `python_requires` in Pipfile |
| Go | `go` directive in go.mod |
| Rust | `rust-toolchain.toml`, `rust-toolchain`, `rust-version` in Cargo.toml |
| Ruby | `.ruby-version`, `ruby` directive in Gemfile |
| Java | `java.version` in pom.xml, `sourceCompatibility` in build.gradle |
| PHP | `require.php` in composer.json |

### Version Commands

If no config file exists, run the local version command:

```bash
node --version      # Node.js (e.g., v24.13.0)
python --version    # Python (e.g., Python 3.12.1)
go version          # Go (e.g., go version go1.23.4)
rustc --version     # Rust (e.g., rustc 1.83.0)
ruby --version      # Ruby (e.g., ruby 3.3.0)
java --version      # Java (e.g., openjdk 21.0.1)
php --version       # PHP (e.g., PHP 8.3.1)
```

### Mapping to Docker Tags

Extract major.minor version and append variant:

| Local Version | Docker Image |
|---------------|--------------|
| `v24.13.0` | `node:24-slim` |
| `Python 3.12.1` | `python:3.12-slim` |
| `go1.23.4` | `golang:1.23-alpine` |
| `rustc 1.83.0` | `rust:1.83-slim` |
| `ruby 3.3.0` | `ruby:3.3-slim` |

---

## Fallback Versions

Use these only if local version detection fails.

## Node.js

| Image | Use Case |
|-------|----------|
| `node:24-slim` | Default for most apps (LTS 24.13.0) |
| `node:24-alpine` | Smaller image, some compatibility tradeoffs |
| `node:25-slim` | Latest features (25.4) |

Check current versions: https://nodejs.org/en/about/releases/

## Python

| Image | Use Case |
|-------|----------|
| `python:3.12-slim` | Default for most apps |
| `python:3.12-alpine` | Smaller image |

Check current versions: https://www.python.org/downloads/

## Go

| Image | Use Case |
|-------|----------|
| `golang:1.23-alpine` | Build stage |
| `gcr.io/distroless/static-debian12` | Production (static binaries) |
| `scratch` | Minimal production image |

Check current versions: https://go.dev/dl/

## Rust

| Image | Use Case |
|-------|----------|
| `rust:1.83-slim` | Build stage |
| `debian:bookworm-slim` | Production runtime |
| `gcr.io/distroless/cc-debian12` | Minimal production |

Check current versions: https://www.rust-lang.org/

## Ruby

| Image | Use Case |
|-------|----------|
| `ruby:3.3-slim` | Default |
| `ruby:3.3-alpine` | Smaller image |

Check current versions: https://www.ruby-lang.org/en/downloads/

## Java

| Image | Use Case |
|-------|----------|
| `eclipse-temurin:21-jdk` | Build stage (LTS) |
| `eclipse-temurin:21-jre` | Production runtime |

Check current versions: https://adoptium.net/

## PHP

| Image | Use Case |
|-------|----------|
| `php:8.3-fpm` | With nginx |
| `php:8.3-apache` | Standalone |
| `php:8.3-cli` | CLI apps |

Check current versions: https://www.php.net/supported-versions.php

## Databases (for reference in haloy.yaml)

| Image | Notes |
|-------|-------|
| `postgres:17` | Current stable |
| `mysql:8.4` | Current stable |
| `redis:7` | Current stable |
| `mongo:7` | Current stable |

## Web Servers

| Image | Use Case |
|-------|----------|
| `nginx:1.27-alpine` | Static file serving, reverse proxy |
| `caddy:2-alpine` | Auto HTTPS, simpler config |

## Version Selection Guidelines

1. **Use specific major.minor tags**, not `latest`
2. **Prefer LTS versions** for production stability
3. **Use slim/alpine variants** to reduce image size
4. **Match your local development version** when possible
5. **Check for security updates** on critical base images
