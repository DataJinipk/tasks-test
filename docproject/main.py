from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Cloud Native FastAPI",
    description="A cloud-native FastAPI starter application",
    version="0.1.0",
)

class TodoItem(BaseModel):
    id: int
    title: str
    time_estimate: int = None  # in minutes

class TodoItemResponse(BaseModel):
    id: int
    title: str
    time_estimate: int = None  # in minutes
    completed: bool = False

# In-memory storage
todos: dict[int, TodoItemResponse] = {
    1: TodoItemResponse(id=1, title="Learn Docker", completed=False),
    2: TodoItemResponse(id=2, title="Build a Docker Image", completed=False),
}

@app.get("/")
def read_root():
    """Root endpoint running a Welcome to Cloud Native FastAPI message."""
    return {"message": "Welcome to Cloud Native FastAPI"}

@app.get("/todo")
def todo() -> List[TodoItemResponse]:
    return list(todos.values())

@app.post("/todo")
def add_todo(todo: TodoItem) -> TodoItemResponse:
    if todo.id == 0:
        raise HTTPException(status_code=400, detail="ID 0 is not allowed")
    if todo.id in todos:
        raise HTTPException(status_code=400, detail=f"Todo with ID {todo.id} already exists")
    todo_response = TodoItemResponse(**todo.model_dump(), completed=False)
    todos[todo.id] = todo_response
    return todo_response

@app.delete("/todo/{item_id}")
def delete_todo(item_id: int):
    """Delete a todo item by its ID"""
    if item_id not in todos:
        raise HTTPException(status_code=404, detail=f"Todo with ID {item_id} not found")
    del todos[item_id]
    return {"message": f"Todo item with ID {item_id} deleted"}

@app.put("/todo/{item_id}")
def update_todo(item_id: int, todo: TodoItem) -> TodoItemResponse:
    """Update a todo item by its ID"""
    if item_id not in todos:
        raise HTTPException(status_code=404, detail=f"Todo with ID {item_id} not found")
    existing = todos[item_id]
    todo_response = TodoItemResponse(**todo.model_dump(), completed=existing.completed)
    todos[item_id] = todo_response
    return todo_response

@app.patch("/todo/{item_id}/complete")
def complete_todo(item_id: int) -> TodoItemResponse:
    """Mark a todo item as completed"""
    if item_id not in todos:
        raise HTTPException(status_code=404, detail=f"Todo with ID {item_id} not found")
    todos[item_id].completed = True
    return todos[item_id]

@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
