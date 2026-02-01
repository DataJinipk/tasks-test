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

| Method | Endpoint  | Description                    |
|--------|-----------|--------------------------------|
| GET    | `/`       | Root endpoint                  |
| GET    | `/health` | Health check for orchestration |
| GET    | `/docs`   | Swagger UI documentation       |
| GET    | `/redoc`  | ReDoc documentation            |

## Running Tests

```bash
pytest
```

## Project Structure

```
cloud-native-fastapi/
├── main.py           # FastAPI application
├── test_main.py      # Tests
├── pyproject.toml    # Project configuration
├── pytest.ini        # Pytest configuration
└── README.md         # This file
```

## Dependencies

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **SQLModel** - ORM with Pydantic integration
- **databases** - Async database support
- **Alembic** - Database migrations
- **pytest** - Testing framework
