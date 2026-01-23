#!/usr/bin/env python3
"""
FastAPI Project Generator

Creates a professional FastAPI project structure with all necessary files.

Usage:
    python create_project.py <project-name>

Example:
    python create_project.py my-api
"""

import sys
import os
from pathlib import Path


MAIN_PY = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .routers import auth, tasks

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
'''

CONFIG_PY = '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "{project_name}"
    version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite:///./app.db"

    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
'''

DATABASE_PY = '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

USER_MODEL = '''from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="owner")
'''

TASK_MODEL = '''from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="tasks")
'''

USER_SCHEMA = '''from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
'''

TASK_SCHEMA = '''from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class Task(TaskBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
'''

AUTH_ROUTER = '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register")
async def register():
    return {"message": "Register endpoint - implement authentication"}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"message": "Login endpoint - implement authentication"}
'''

TASKS_ROUTER = '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import task as schemas

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[schemas.Task])
async def get_tasks(db: Session = Depends(get_db)):
    return []


@router.post("/", response_model=schemas.Task, status_code=201)
async def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return {"message": "Create task - implement logic"}
'''

REQUIREMENTS_TXT = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
'''

DOCKERFILE = '''FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

DOCKER_COMPOSE = '''version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./app:/code/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
'''

ENV_EXAMPLE = '''# Application
APP_NAME={project_name}
DEBUG=false
VERSION=1.0.0

# Database
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]
'''

README_MD = '''# {project_name}

FastAPI application generated using create_project.py

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
cp .env.example .env
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker

Build and run with Docker:
```bash
docker-compose up --build
```

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI app initialization
├── config.py            # Configuration
├── database.py          # Database connection
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
└── routers/             # API endpoints
```
'''

GITIGNORE = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/

# FastAPI
*.db
*.db-journal

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
'''


def create_project(project_name):
    """Create FastAPI project structure"""
    project_path = Path(project_name)

    if project_path.exists():
        print(f"Error: Directory '{project_name}' already exists")
        return False

    print(f"Creating FastAPI project: {project_name}")

    # Create main directories
    app_path = project_path / "app"
    app_path.mkdir(parents=True)

    (app_path / "models").mkdir()
    (app_path / "schemas").mkdir()
    (app_path / "routers").mkdir()
    (project_path / "tests").mkdir()

    # Create __init__.py files
    (app_path / "__init__.py").write_text("")
    (app_path / "models" / "__init__.py").write_text("")
    (app_path / "schemas" / "__init__.py").write_text("")
    (app_path / "routers" / "__init__.py").write_text("")

    # Create main files
    (app_path / "main.py").write_text(MAIN_PY)
    (app_path / "config.py").write_text(CONFIG_PY.format(project_name=project_name))
    (app_path / "database.py").write_text(DATABASE_PY)

    # Create models
    (app_path / "models" / "user.py").write_text(USER_MODEL)
    (app_path / "models" / "task.py").write_text(TASK_MODEL)

    # Create schemas
    (app_path / "schemas" / "user.py").write_text(USER_SCHEMA)
    (app_path / "schemas" / "task.py").write_text(TASK_SCHEMA)

    # Create routers
    (app_path / "routers" / "auth.py").write_text(AUTH_ROUTER)
    (app_path / "routers" / "tasks.py").write_text(TASKS_ROUTER)

    # Create project files
    (project_path / "requirements.txt").write_text(REQUIREMENTS_TXT)
    (project_path / "Dockerfile").write_text(DOCKERFILE)
    (project_path / "docker-compose.yml").write_text(DOCKER_COMPOSE)
    (project_path / ".env.example").write_text(ENV_EXAMPLE.format(project_name=project_name))
    (project_path / "README.md").write_text(README_MD.format(project_name=project_name))
    (project_path / ".gitignore").write_text(GITIGNORE)

    print(f"✅ Project '{project_name}' created successfully!")
    print("\nNext steps:")
    print(f"  cd {project_name}")
    print("  python -m venv venv")
    print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("  pip install -r requirements.txt")
    print("  cp .env.example .env")
    print("  uvicorn app.main:app --reload")

    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_project.py <project-name>")
        print("Example: python create_project.py my-api")
        sys.exit(1)

    project_name = sys.argv[1]
    success = create_project(project_name)
    sys.exit(0 if success else 1)
