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

## Principles

### Type Hints (Required)
- Always use type hints for ALL path parameters: `item_id: int`
- Always use type hints for ALL query parameters: `q: str | None = None`
- Always use type hints for return types: `def get_item(...) -> dict:`
- Use `int`, `str`, `bool`, `float` for primitives
- Use `| None` for optional parameters

### Return Values (Required)
- Always return dictionaries, never `None`
- Every endpoint must return meaningful data
- DELETE endpoints return 204 with no body (the only exception)
- Error cases return HTTPException, not None

### Function Naming (Required)
- Function names MUST match endpoint purpose
- Use verb + noun pattern:
  - `get_item` for GET /items/{id}
  - `list_items` for GET /items
  - `create_item` for POST /items
  - `update_item` for PUT /items/{id}
  - `delete_item` for DELETE /items/{id}
  - `search_items` for GET /search
- Never use generic names like `handler` or `endpoint`

### Other Requirements
- Use Pydantic models for request/response bodies
- Return appropriate status codes (201 for create, 204 for delete)
- Include HTTPException for 404 errors on single-item endpoints
- Support optional query parameters for filtering on list endpoints
- Generate valid, runnable code that can be tested immediately
