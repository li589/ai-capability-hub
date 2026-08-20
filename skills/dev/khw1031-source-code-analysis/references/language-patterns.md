# 언어별 분석 휴리스틱

## TypeScript / Node.js

### 메타파일

| 파일 | 확인 항목 |
|------|----------|
| `package.json` | scripts, dependencies, engines, type(module/commonjs) |
| `tsconfig.json` | target, strict, paths, baseUrl, decorators |
| `.nvmrc` / `.node-version` | Node 버전 |

### 프레임워크 식별

| 단서 | 프레임워크 |
|------|-----------|
| `@nestjs/*` | NestJS (데코레이터 DI, 모듈 시스템) |
| `koa` | Koa (미들웨어 체인) |
| `express` | Express (라우터 + 미들웨어) |
| `fastify` | Fastify (스키마 기반, 플러그인) |
| `next` | Next.js (pages/ or app/ 라우팅) |

### DI 패턴

| 라이브러리 | 패턴 |
|-----------|------|
| `tsyringe` | `@singleton()`, `@injectable()`, `container.resolve()` |
| `inversify` | `@injectable()`, `Container`, `bind().to()` |
| NestJS 내장 | `@Injectable()`, `@Module({ providers })` |
| 수동 DI | 생성자 주입, Factory 함수 |

### 엔트리포인트 찾기

1. `package.json` → `main` 또는 `scripts.start`
2. `tsconfig.json` → `outDir` + main 파일
3. `src/index.ts`, `src/main.ts`, `src/app.ts` 순서로 탐색

### 비동기 패턴

- `async/await` (표준)
- `rxjs` Observable (NestJS, Angular 계열)
- `EventEmitter` 패턴
- Stream API (`pipe`, `Transform`)

---

## Python

### 메타파일

| 파일 | 확인 항목 |
|------|----------|
| `pyproject.toml` | build-system, project.dependencies, tool.* |
| `setup.py` / `setup.cfg` | 레거시 설정 |
| `requirements.txt` | 직접 의존성 |
| `Pipfile` / `poetry.lock` | 패키지 매니저 |

### 프레임워크 식별

| 단서 | 프레임워크 |
|------|-----------|
| `fastapi` | FastAPI (async, Pydantic, OpenAPI) |
| `django` | Django (ORM, MTV, admin) |
| `flask` | Flask (마이크로, 블루프린트) |
| `starlette` | Starlette (ASGI, 미들웨어) |
| `typer` / `click` | CLI 애플리케이션 |

### 패턴

- Type Hints (`typing` 모듈) 사용 수준
- `dataclasses` vs `pydantic` vs `attrs`
- `__init__.py` 패키지 구조
- `conftest.py` 테스트 설정

---

## Rust

### 메타파일

| 파일 | 확인 항목 |
|------|----------|
| `Cargo.toml` | edition, workspace, features, dependencies |
| `Cargo.lock` | 정확한 의존성 버전 |
| `build.rs` | 빌드 스크립트 |

### 패턴

- **Workspace**: 멀티 크레이트 프로젝트 → `[workspace]` 섹션
- **Feature flags**: 조건부 컴파일 → `[features]` 섹션
- **Trait 기반 추상화**: `impl Trait for Type`
- **Error 처리**: `Result<T, E>`, `thiserror`, `anyhow`
- **Async**: `tokio`, `async-std` 런타임

### 엔트리포인트

- `src/main.rs` (바이너리)
- `src/lib.rs` (라이브러리)
- `examples/` (예제 바이너리)

---

## Go

### 메타파일

| 파일 | 확인 항목 |
|------|----------|
| `go.mod` | module path, go version, require |
| `go.sum` | 체크섬 |
| `Makefile` | 빌드/테스트 명령어 |

### 패턴

- **Interface 기반 DI**: 암묵적 인터페이스 구현
- **패키지 구조**: `cmd/`, `internal/`, `pkg/` 컨벤션
- **Error 처리**: `if err != nil` 패턴
- **Goroutine/Channel**: 동시성 패턴

### 엔트리포인트

- `cmd/{app}/main.go` (표준 레이아웃)
- `main.go` (단일 바이너리)

---

## 공통 분석 포인트

### 설정 관리 패턴

| 패턴 | 예시 |
|------|------|
| 환경변수 | `process.env`, `os.environ`, `std::env` |
| 설정 파일 | `.env`, `config.yaml`, `settings.toml` |
| 설정 객체 | DTO/Schema로 타입 안전하게 로드 |
| 기본값 | 하드코딩 → 환경변수 → 설정 파일 폴백 체인 |

### 로깅 패턴

| 언어 | 라이브러리 |
|------|-----------|
| TypeScript | `pino`, `winston`, `console` |
| Python | `logging`, `loguru`, `structlog` |
| Rust | `tracing`, `log`, `env_logger` |
| Go | `log/slog`, `zap`, `logrus` |

### 테스트 패턴

| 관점 | 확인 |
|------|------|
| 단위 테스트 | 있는가? 커버리지는? |
| 통합 테스트 | DB/API 연동 테스트? |
| E2E 테스트 | 전체 파이프라인 테스트? |
| 모킹 전략 | DI 기반 / monkey-patch / test doubles |
