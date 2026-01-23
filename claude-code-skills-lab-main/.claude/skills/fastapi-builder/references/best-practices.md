# FastAPI Best Practices for Production

## Project Structure

### Professional Organization
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   ├── dependencies.py         # Shared dependencies
│   ├── exceptions.py           # Custom exceptions
│   ├── middleware.py           # Custom middleware
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── tasks.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── task_service.py
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── helpers.py
│
├── tests/                      # Test files mirror app structure
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_tasks.py
│
├── alembic/                    # Database migrations
├── .env                        # Environment variables (not in git)
├── .env.example               # Example environment file
├── requirements.txt           # Dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Configuration Management

### config.py with Pydantic Settings
```python
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    app_name: str = "FastAPI Application"
    debug: bool = False
    version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str
    db_echo: bool = False

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # External services
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

### Environment Variables (.env.example)
```env
# Application
APP_NAME=FastAPI Application
DEBUG=false
VERSION=1.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

## Error Handling

### Custom Exceptions
```python
# exceptions.py
class AppException(Exception):
    """Base exception for application"""
    pass

class NotFoundException(AppException):
    """Resource not found exception"""
    def __init__(self, resource: str, id: int):
        self.message = f"{resource} with id {id} not found"
        super().__init__(self.message)

class UnauthorizedException(AppException):
    """Unauthorized access exception"""
    pass
```

### Global Exception Handlers
```python
# main.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .exceptions import NotFoundException, UnauthorizedException

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message}
    )

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Unauthorized"}
    )
```

## Logging

### Structured Logging
```python
import logging
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add custom handler
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)

# Add file handler for production
logger.add(
    "logs/app_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="ERROR"
)

# Usage
logger.info("Application started")
logger.error("Error occurred", exc_info=True)
```

### Request Logging Middleware
```python
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.2f}s "
        f"with status {response.status_code}"
    )

    return response
```

## Dependency Injection

### Reusable Dependencies
```python
# dependencies.py
from fastapi import Depends, Query
from typing import Optional

class Pagination:
    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        self.skip = skip
        self.limit = limit

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional)
):
    if not token:
        return None
    return decode_and_verify_token(token)
```

## Service Layer Pattern

### Separation of Concerns
```python
# services/task_service.py
from sqlalchemy.orm import Session
from ..models import Task
from ..schemas import TaskCreate, TaskUpdate
from ..exceptions import NotFoundException

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def get_task(self, task_id: int) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundException("Task", task_id)
        return task

    def create_task(self, task_data: TaskCreate, owner_id: int) -> Task:
        task = Task(**task_data.dict(), owner_id=owner_id)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task(self, task_id: int, task_update: TaskUpdate) -> Task:
        task = self.get_task(task_id)
        update_data = task_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

# Usage in router
@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.get_task(task_id)
```

## Testing

### Comprehensive Test Setup
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture()
def auth_client(client, db):
    # Create test user and authenticate
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    })

    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })

    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

### Test Examples
```python
# tests/test_tasks.py
def test_create_task(auth_client):
    response = auth_client.post("/tasks", json={
        "title": "Test Task",
        "description": "Test Description"
    })
    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"

def test_get_tasks(auth_client):
    response = auth_client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_unauthorized_access(client):
    response = client.get("/tasks")
    assert response.status_code == 401
```

## Performance Optimization

### Database Query Optimization
```python
# Use select_in_loading to avoid N+1 queries
from sqlalchemy.orm import selectinload

tasks = db.query(Task).options(selectinload(Task.owner)).all()

# Use pagination for large datasets
def get_paginated_tasks(db: Session, page: int = 1, size: int = 50):
    offset = (page - 1) * size
    return db.query(Task).offset(offset).limit(size).all()
```

### Caching with Redis
```python
from redis import Redis
import json

redis_client = Redis.from_url("redis://localhost:6379")

def get_cached_tasks(user_id: int):
    cache_key = f"user:{user_id}:tasks"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    tasks = get_tasks_from_db(user_id)
    redis_client.setex(cache_key, 300, json.dumps(tasks))  # 5 min cache
    return tasks
```

### Background Tasks
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Simulate email sending
    time.sleep(2)
    print(f"Email sent to {email}")

@app.post("/send-notification")
async def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, message)
    return {"message": "Notification scheduled"}
```

## Security Best Practices

### Input Validation
```python
from pydantic import validator, Field

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
```

### SQL Injection Prevention
```python
# Always use parameterized queries (SQLAlchemy does this by default)
# GOOD
user = db.query(User).filter(User.username == username).first()

# BAD - never do this
db.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

## Documentation

### Enhanced API Docs
```python
app = FastAPI(
    title="My API",
    description="Comprehensive API for managing tasks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication operations"},
        {"name": "tasks", "description": "Task management"},
    ]
)

@app.post("/tasks", tags=["tasks"], summary="Create a new task")
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task with the following information:

    - **title**: required, task title
    - **description**: optional, detailed description
    - **completed**: optional, completion status (default: false)
    """
    ...
```

## Monitoring & Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_database_connection(),
        "redis": check_redis_connection()
    }

@app.get("/metrics")
async def metrics():
    return {
        "uptime": get_uptime(),
        "requests_count": get_request_count(),
        "error_rate": get_error_rate()
    }
```
