# Todo API

A simple REST API for managing todos, built with FastAPI and SQLModel.

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn main:app --reload
```

Server runs at http://127.0.0.1:8000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/todos` | List all todos |
| GET | `/todos/{id}` | Get a todo |
| POST | `/todos` | Create a todo |
| PUT | `/todos/{id}` | Update a todo |
| DELETE | `/todos/{id}` | Delete a todo |

### Request/Response Examples

**Create:**
```bash
curl -X POST http://localhost:8000/todos -H "Content-Type: application/json" -d '{"task":"Buy milk"}'
```

**Update (mark complete):**
```bash
curl -X PUT http://localhost:8000/todos/1 -H "Content-Type: application/json" -d '{"completed":true}'
```

## Interactive Docs

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Tests

```bash
uv run pytest -v
```

## Tech Stack

- FastAPI
- SQLModel (SQLAlchemy + Pydantic)
- SQLite
- pytest
