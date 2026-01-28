# FastAPI Agent API Generator

Generate FastAPI applications with common endpoint patterns.

## Usage

When invoked, generate a complete FastAPI app based on the user's requirements.

## Default Template

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()
```

## Endpoint Patterns

### Root Endpoint
```python
@app.get("/")
def root():
    return {"message": "Welcome to the API"}
```

### Path Parameter Endpoint
```python
@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
```

### Query Parameter Endpoint
```python
@app.get("/search")
def search(
    q: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return {"query": q, "limit": limit, "offset": offset, "results": []}
```

### POST with Request Body
```python
class ItemCreate(BaseModel):
    name: str
    description: str | None = None

@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    return {"id": 1, **item.model_dump()}
```

### Full CRUD Pattern
When asked for CRUD, include:
- POST /resources - Create
- GET /resources - List (with optional filtering)
- GET /resources/{id} - Read single
- PUT /resources/{id} - Update
- DELETE /resources/{id} - Delete (return 204)

## Instructions

1. Always include type hints
2. Use Pydantic models for request/response bodies
3. Return appropriate status codes (201 for create, 204 for delete)
4. Include HTTPException for 404 errors on single-item endpoints
5. Support optional query parameters for filtering on list endpoints
6. Generate valid, runnable code that can be tested immediately
