# Cloud Native FastAPI

A cloud-native FastAPI starter application designed for containerized deployments.

## Requirements

- Python 3.13+
- uv (Python package manager)

## Setup

```bash
# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

## Running the Application

```bash
# Development server with auto-reload
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint                 | Description                    |
|--------|--------------------------|--------------------------------|
| GET    | `/`                      | Root endpoint                  |
| GET    | `/health`                | Health check for orchestration |
| GET    | `/todo`                  | List all todos                 |
| POST   | `/todo`                  | Create a new todo              |
| PUT    | `/todo/{item_id}`        | Update a todo                  |
| DELETE | `/todo/{item_id}`        | Delete a todo                  |
| PATCH  | `/todo/{item_id}/complete` | Mark todo as complete        |
| GET    | `/docs`                  | Swagger UI documentation       |
| GET    | `/redoc`                 | ReDoc documentation            |

## Docker

```bash
# Build the image
docker build -t docproject:dev .

# Run the container
docker run -d -p 8000:8000 --name docproject docproject:dev

# Run tests inside container
docker exec docproject uv run pytest -v

# Stop and remove
docker stop docproject && docker rm docproject
```

## Running Tests

```bash
pytest
```

## Project Structure

```
docproject/
├── main.py           # FastAPI application
├── test_main.py      # Tests
├── pyproject.toml    # Project configuration
├── pytest.ini        # Pytest configuration
├── Dockerfile        # Container configuration
├── .dockerignore     # Docker ignore rules
└── README.md         # This file
```

## Dependencies

**Currently Used:**
- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **pytest** - Testing framework

**Available for Future Use:**
- **SQLModel** - ORM with Pydantic integration
- **databases** - Async database support
- **Alembic** - Database migrations
