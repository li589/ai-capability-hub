# Python Stack Reference

## Key Conventions

- Use type hints everywhere. Run mypy in strict mode.
- FastAPI: leverage Pydantic models for request/response validation. Use
  dependency injection for services.
- Django: use Django REST Framework for APIs. Fat models, thin views.
  Use `select_related`/`prefetch_related` to avoid N+1.
- Flask: use Blueprints for modularity. Don't put business logic in routes.
- Always use `async` in FastAPI when doing I/O. Don't mix sync and async
  carelessly.
- Use Alembic (SQLAlchemy) or Django migrations for schema changes.
- Virtual environments are mandatory. Pin all dependencies with versions.

---

## Project Structure (FastAPI)

```
src/
├── main.py
├── config.py
├── dependencies.py
├── database.py
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── users/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── models.py
│   │   └── orders/
│   │       └── ...
├── core/
│   ├── exceptions.py
│   ├── middleware.py
│   └── security.py
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
└── tests/
    ├── conftest.py
    ├── test_users.py
    └── factories.py
```

## Project Structure (Django REST Framework)

```
project/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── selectors.py
│   │   ├── permissions.py
│   │   ├── admin.py
│   │   ├── migrations/
│   │   └── tests/
│   └── orders/
│       └── ...
└── common/
    ├── models.py
    ├── pagination.py
    └── exceptions.py
```

---

## FastAPI Patterns

```python
# schemas.py — Pydantic request/response models
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.USER


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


# router.py
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    body: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        user = await service.create(body)
        return UserResponse.model_validate(user)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
```

---

## Error Handling

```python
# core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class NotFoundError(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            message=f"{resource} with id {id} not found",
            status_code=404,
            code="NOT_FOUND",
        )


# Register in main.py
@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, exc: AppException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                **({"details": exc.details} if exc.details else {}),
            }
        },
    )
```

---

## SQLAlchemy Async Patterns

```python
# database.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# repository.py
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def find_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
```

---

## Testing

```python
# conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# test_users.py
@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/api/v1/users/", json={
        "email": "test@example.com",
        "name": "Test User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

---

## Alembic Migration Example

```python
"""create users table

Revision ID: 001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email")
    op.drop_table("users")
```
