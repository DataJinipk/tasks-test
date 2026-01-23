---
name: fastapi-builder
description: |
  Use when building FastAPI applications from Hello World to production-grade projects.
  Covers REST APIs, async operations, database integration, authentication, testing, and deployment.
  NOT for Flask or Django (use framework-specific skills).
---

# FastAPI Builder

Build professional FastAPI applications from Hello World to production-ready APIs with authentication, databases, testing, and deployment.

## Quick Start

### Level 1: Hello World
```bash
# Create project with uv
uv init my-api
cd my-api
uv add fastapi uvicorn
```

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello {name}"}

# Run: uvicorn main:app --reload
```

**Access docs**: http://localhost:8000/docs

### Level 2: CRUD API with Pydantic
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Task API", version="1.0.0")

class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    completed: bool = False

tasks_db = []

@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(task: Task):
    task.id = len(tasks_db) + 1
    tasks_db.append(task)
    return task

@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    return tasks_db

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    task = next((t for t in tasks_db if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: Task):
    idx = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.id = task_id
    tasks_db[idx] = task
    return task

@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    idx = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_db.pop(idx)
```

## Project Levels

| Level | Features | Use Case |
|-------|----------|----------|
| 1 | Hello World, basic routes | Learning, demos |
| 2 | CRUD, Pydantic models | Simple APIs |
| 3 | SQLAlchemy database | Persistent data |
| 4 | JWT authentication | Protected APIs |
| 5 | Testing with pytest | Quality assurance |
| 6 | Advanced features | Real applications |
| 7 | Docker deployment | Production |

## Level 3: Database Integration

### Project Structure
```
app/
├── __init__.py
├── main.py
├── database.py
├── models.py
├── schemas.py
└── crud.py
```

### Quick Setup
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

See [references/database-integration.md](references/database-integration.md) for complete implementation.

## Level 4: Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "user" or form_data.password != "password":
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}"}
```

**Dependencies**: `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`

See [references/authentication.md](references/authentication.md) for advanced patterns.

## Level 5: Testing

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_task():
    response = client.post("/tasks", json={"title": "Test task"})
    assert response.status_code == 201
    assert response.json()["title"] == "Test task"

def test_get_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Run**: `pytest test_main.py -v`

## Level 6: Advanced Features

### Background Tasks
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    print(f"Sending email to {email}: {message}")

@app.post("/send-notification")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Notification sent")
    return {"message": "Notification scheduled"}
```

### File Upload
```python
from fastapi import File, UploadFile

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

### WebSocket
```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Level 7: Production Deployment

### Professional Structure
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   └── dependencies.py
├── tests/
├── alembic/
├── .env
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### Configuration
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    database_url: str
    secret_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dbname
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: dbname
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

See [references/best-practices.md](references/best-practices.md) for production patterns.

## Common Patterns

### Router Organization
```python
# app/routers/tasks.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/")
async def get_tasks():
    return []

# app/main.py
from app.routers import tasks
app.include_router(tasks.router)
```

### Dependency Injection
```python
from fastapi import Depends

def get_settings():
    return Settings()

@app.get("/config")
async def config(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name}
```

### Error Handling
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"message": str(exc)})
```

## Quick Reference

### Dependencies
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
alembic>=1.12.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pytest>=7.4.0
httpx>=0.25.0
```

### Commands
| Command | Purpose |
|---------|---------|
| `uvicorn app.main:app --reload` | Dev server |
| `uvicorn app.main:app --port 8080` | Custom port |
| `uvicorn app.main:app --host 0.0.0.0 --workers 4` | Production |
| `alembic revision --autogenerate -m "msg"` | Generate migration |
| `alembic upgrade head` | Apply migrations |
| `pytest -v` | Run tests |

## Scripts

| Script | Purpose |
|--------|---------|
| [scripts/create_project.py](scripts/create_project.py) | Generate FastAPI project structure |
| [scripts/generate_crud.py](scripts/generate_crud.py) | Generate CRUD endpoints for a model |
| [scripts/verify.py](scripts/verify.py) | Verify skill follows requirements |

## References

| Reference | Content |
|-----------|---------|
| [references/database-integration.md](references/database-integration.md) | Complete SQLAlchemy setup |
| [references/authentication.md](references/authentication.md) | Advanced auth patterns |
| [references/best-practices.md](references/best-practices.md) | Production-ready patterns |

## Examples

| Example | Description |
|---------|-------------|
| [examples/hello-world/](examples/hello-world/) | Basic FastAPI app |
| [examples/crud-api/](examples/crud-api/) | CRUD with Pydantic |
