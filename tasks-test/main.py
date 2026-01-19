from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

todos = [
    {"id": 1, "task": "Build an API"},
    {"id": 2, "task": "Buy groceries"},
    {"id": 3, "task": "Read a book"}
]


class TodoCreate(BaseModel):
    task: str


class TodoUpdate(BaseModel):
    task: str


# GET all todos
@app.get("/todos")
async def get_todos():
    return todos


# GET single todo by id
@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")


# POST create new todo
@app.post("/todos", status_code=201)
async def create_todo(todo: TodoCreate):
    new_id = max(t["id"] for t in todos) + 1 if todos else 1
    new_todo = {"id": new_id, "task": todo.task}
    todos.append(new_todo)
    return new_todo


# PUT update todo
@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, todo: TodoUpdate):
    for t in todos:
        if t["id"] == todo_id:
            t["task"] = todo.task
            return t
    raise HTTPException(status_code=404, detail="Todo not found")


# DELETE todo
@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    for i, t in enumerate(todos):
        if t["id"] == todo_id:
            todos.pop(i)
            return
    raise HTTPException(status_code=404, detail="Todo not found")