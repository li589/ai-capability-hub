---
name: fastapi-generator
description: Generates FastAPI endpoints with proper Pydantic models, dependency injection, async handlers, and OpenAPI documentation. Use when building Python REST APIs.
install_source: official
install_method: download
skill_id: official_4g0oLdvc
enabled_at: 1787231551123
version: 1.0.0
name_zh: FastAPI生成
---

# FastAPI Endpoint Generator Skill

Expert at creating modern FastAPI applications with async/await, Pydantic models, and proper architecture.

## When to Activate

- "create FastAPI endpoint for [resource]"
- "generate Python API with FastAPI"
- "build FastAPI routes for [feature]"
- "scaffold FastAPI application"

## Complete FastAPI Structure

### 1. Main Router

```python
# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from ..schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from ..services.user_service import UserService
from ..dependencies import get_current_user, get_user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    service: UserService = Depends(get_user_service),
):
    """
    Retrieve list of users with pagination.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Optional search query
    """
    users, total = await service.get_all(skip=skip, limit=limit, search=search)

    return UserListResponse(
        users=users,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Get user by ID"""
    user = await service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """Create a new user"""
    return await service.create(user_data)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user),
):
    """Update existing user"""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    user = await service.update(user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user),
):
    """Delete a user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    success = await service.delete(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
```

### 2. Pydantic Schemas

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a digit')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
```

### 3. Service Layer

```python
# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, Tuple, List
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash
from fastapi import HTTPException, status

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Get all users with pagination and search"""
        query = select(User)

        if search:
            query = query.where(
                or_(
                    User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return users, total

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """Create new user"""
        # Check if email exists
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            **user_data.dict(exclude={'password'}),
            hashed_password=hashed_password
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return db_user

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)

        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete(self, user_id: int) -> bool:
        """Delete user"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()

        return True
```

### 4. Dependencies

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .services.user_service import UserService
from .core.security import decode_token

security = HTTPBearer()

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency for user service"""
    return UserService(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user"""
    token = credentials.credentials

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_service = UserService(db)
    user = await user_service.get_by_id(payload.get("sub"))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
```

## File Structure

```
app/
├── main.py                 # FastAPI app initialization
├── routers/
│   ├── __init__.py
│   └── users.py
├── schemas/
│   ├── __init__.py
│   └── user.py
├── services/
│   ├── __init__.py
│   └── user_service.py
├── models/
│   ├── __init__.py
│   └── user.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── security.py
├── dependencies.py
└── database.py
```

## Best Practices

- ✅ Use async/await for all I/O operations
- ✅ Pydantic models for validation
- ✅ Dependency injection
- ✅ Proper HTTP status codes
- ✅ OpenAPI documentation
- ✅ Type hints everywhere
- ✅ Service layer for business logic
- ✅ Proper error handling
- ✅ Security (password hashing, JWT)
- ✅ Pagination for lists
- ✅ Database connection pooling
- ✅ CORS configuration

## Output Checklist

- ✅ Router with endpoints
- ✅ Pydantic schemas
- ✅ Service layer
- ✅ Dependencies setup
- ✅ Error handling
- ✅ Authentication
- ✅ Tests
- 📝 OpenAPI docs auto-generated
