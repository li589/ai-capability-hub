# Go / Rust Stack Reference

---

## Go

### Key Conventions

- Accept interfaces, return structs.
- Handle every error. No `_` for errors unless you document why.
- Use `context.Context` for cancellation and timeouts. Pass it as first param.
- Structure: `cmd/`, `internal/`, `pkg/`. Keep `pkg/` minimal.
- Use `sqlx` or `pgx` for database access. Avoid heavy ORMs.
- Table-driven tests. Use `testify` for assertions if needed.

### Project Structure

```
cmd/
├── api/
│   └── main.go
internal/
├── config/
│   └── config.go
├── server/
│   └── server.go
├── handler/
│   ├── user.go
│   └── middleware.go
├── service/
│   └── user.go
├── repository/
│   └── user.go
├── model/
│   └── user.go
├── apperror/
│   └── errors.go
└── database/
    ├── postgres.go
    └── migrations/
        ├── 001_create_users.up.sql
        └── 001_create_users.down.sql
pkg/
├── validator/
└── logger/
```

### Handler Pattern

```go
type UserHandler struct {
    service *service.UserService
}

func NewUserHandler(s *service.UserService) *UserHandler {
    return &UserHandler{service: s}
}

func (h *UserHandler) Create(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()

    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, apperror.NewBadRequest("invalid request body"))
        return
    }

    if err := validator.Validate(req); err != nil {
        respondError(w, apperror.NewValidation(err))
        return
    }

    user, err := h.service.Create(ctx, req)
    if err != nil {
        respondError(w, err)
        return
    }

    respondJSON(w, http.StatusCreated, user)
}

func respondJSON(w http.ResponseWriter, status int, data any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}

func respondError(w http.ResponseWriter, err error) {
    var appErr *apperror.AppError
    if errors.As(err, &appErr) {
        respondJSON(w, appErr.StatusCode, map[string]any{
            "error": map[string]any{
                "code":    appErr.Code,
                "message": appErr.Message,
            },
        })
        return
    }
    slog.Error("unhandled error", "error", err)
    respondJSON(w, 500, map[string]any{
        "error": map[string]any{
            "code":    "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
        },
    })
}
```

### Error Handling

```go
package apperror

import "fmt"

type AppError struct {
    Message    string `json:"message"`
    Code       string `json:"code"`
    StatusCode int    `json:"-"`
}

func (e *AppError) Error() string {
    return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func NewNotFound(resource, id string) *AppError {
    return &AppError{
        Message:    fmt.Sprintf("%s with id %s not found", resource, id),
        Code:       "NOT_FOUND",
        StatusCode: 404,
    }
}

func NewBadRequest(msg string) *AppError {
    return &AppError{Message: msg, Code: "BAD_REQUEST", StatusCode: 400}
}

func NewConflict(msg string) *AppError {
    return &AppError{Message: msg, Code: "CONFLICT", StatusCode: 409}
}
```

### Repository with sqlx

```go
type UserRepository struct {
    db *sqlx.DB
}

func NewUserRepository(db *sqlx.DB) *UserRepository {
    return &UserRepository{db: db}
}

func (r *UserRepository) FindByID(
    ctx context.Context, id uuid.UUID,
) (*model.User, error) {
    var user model.User
    err := r.db.GetContext(ctx, &user,
        `SELECT id, email, name, role, created_at, updated_at
         FROM users WHERE id = $1`, id)
    if errors.Is(err, sql.ErrNoRows) {
        return nil, apperror.NewNotFound("User", id.String())
    }
    if err != nil {
        return nil, fmt.Errorf("find user by id: %w", err)
    }
    return &user, nil
}

func (r *UserRepository) Create(
    ctx context.Context, user *model.User,
) error {
    _, err := r.db.NamedExecContext(ctx,
        `INSERT INTO users (id, email, name, password_hash, role)
         VALUES (:id, :email, :name, :password_hash, :role)`, user)
    if err != nil {
        var pgErr *pgconn.PgError
        if errors.As(err, &pgErr) && pgErr.Code == "23505" {
            return apperror.NewConflict("email already registered")
        }
        return fmt.Errorf("create user: %w", err)
    }
    return nil
}
```

### Testing

```go
func TestUserHandler_Create(t *testing.T) {
    tests := []struct {
        name       string
        body       string
        setupMock  func(*mockService)
        wantStatus int
        wantCode   string
    }{
        {
            name: "success",
            body: `{"email":"a@b.com","name":"Test","password":"secret123"}`,
            setupMock: func(m *mockService) {
                m.createFn = func(
                    ctx context.Context, req CreateUserRequest,
                ) (*UserResponse, error) {
                    return &UserResponse{
                        ID: uuid.New(), Email: "a@b.com", Name: "Test",
                    }, nil
                }
            },
            wantStatus: 201,
        },
        {
            name:       "invalid json",
            body:       `{broken`,
            setupMock:  func(m *mockService) {},
            wantStatus: 400,
            wantCode:   "BAD_REQUEST",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mock := &mockService{}
            tt.setupMock(mock)
            handler := NewUserHandler(mock)

            req := httptest.NewRequest(http.MethodPost, "/users",
                strings.NewReader(tt.body))
            rec := httptest.NewRecorder()

            handler.Create(rec, req)

            assert.Equal(t, tt.wantStatus, rec.Code)
        })
    }
}
```

---

## Rust

### Key Conventions

- Use `Result<T, E>` everywhere. Custom error types with `thiserror`.
- Prefer `&str` over `String` in function params when possible.
- Use `tokio` for async runtime. `axum` or `actix-web` for HTTP.
- Leverage the type system for domain modeling (newtype pattern, enums for
  states).
- `clippy` with strict lints. `rustfmt` for formatting. No exceptions.

### Project Structure (Axum)

```
src/
├── main.rs
├── config.rs
├── routes/
│   ├── mod.rs
│   └── users.rs
├── handlers/
│   └── users.rs
├── services/
│   └── users.rs
├── repositories/
│   └── users.rs
├── models/
│   ├── user.rs
│   └── mod.rs
├── error.rs
├── database.rs
└── extractors/
    └── auth.rs
migrations/
├── 001_create_users.up.sql
└── 001_create_users.down.sql
```

### Error Handling with thiserror + axum

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("{resource} with id {id} not found")]
    NotFound { resource: String, id: String },

    #[error("Validation failed: {0}")]
    Validation(String),

    #[error("{0}")]
    Conflict(String),

    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, code) = match &self {
            AppError::NotFound { .. } =>
                (StatusCode::NOT_FOUND, "NOT_FOUND"),
            AppError::Validation(_) =>
                (StatusCode::BAD_REQUEST, "VALIDATION_ERROR"),
            AppError::Conflict(_) =>
                (StatusCode::CONFLICT, "CONFLICT"),
            AppError::Internal(e) => {
                tracing::error!("Internal error: {:?}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "INTERNAL_ERROR")
            }
        };

        let body = Json(json!({
            "error": {
                "code": code,
                "message": self.to_string(),
            }
        }));

        (status, body).into_response()
    }
}
```

### Handler Pattern

```rust
use axum::{extract::{State, Path}, Json};
use uuid::Uuid;

pub async fn create_user(
    State(state): State<AppState>,
    Json(req): Json<CreateUserRequest>,
) -> Result<(StatusCode, Json<UserResponse>), AppError> {
    req.validate()?;
    let user = state.user_service.create(req).await?;
    Ok((StatusCode::CREATED, Json(user)))
}

pub async fn find_by_id(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<UserResponse>, AppError> {
    let user = state.user_service.find_by_id(id).await?;
    Ok(Json(user))
}

// Router
pub fn user_routes() -> Router<AppState> {
    Router::new()
        .route("/users", post(create_user).get(list_users))
        .route("/users/:id",
            get(find_by_id).put(update_user).delete(delete_user))
}
```

### Repository with sqlx

```rust
pub struct UserRepository {
    pool: PgPool,
}

impl UserRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn find_by_id(
        &self, id: Uuid,
    ) -> Result<Option<User>, AppError> {
        let user = sqlx::query_as!(
            User,
            r#"SELECT id, email, name, role as "role: Role",
                      created_at, updated_at
               FROM users WHERE id = $1"#,
            id
        )
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| anyhow::anyhow!(e))?;

        Ok(user)
    }

    pub async fn create(
        &self, user: &NewUser,
    ) -> Result<User, AppError> {
        let created = sqlx::query_as!(
            User,
            r#"INSERT INTO users (email, name, password_hash, role)
               VALUES ($1, $2, $3, $4)
               RETURNING id, email, name,
                         role as "role: Role",
                         created_at, updated_at"#,
            user.email, user.name, user.password_hash,
            user.role as Role,
        )
        .fetch_one(&self.pool)
        .await
        .map_err(|e| match e {
            sqlx::Error::Database(ref db_err)
                if db_err.constraint()
                    == Some("users_email_key") =>
            {
                AppError::Conflict(
                    "Email already registered".into())
            }
            _ => anyhow::anyhow!(e).into(),
        })?;

        Ok(created)
    }
}
```
