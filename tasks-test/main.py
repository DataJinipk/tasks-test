from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

todos = [
    {"id": 1, "task": "Build an API"},
    {"id": 2, "task": "Buy groceries"},
    {"id": 3, "task": "Read a book"}
]


class TodoCreate(BaseModel):
    task: str


@app.get("/todo")
def get_todos() -> list[dict[str, int | str]]:
    return todos


@app.get("/todo/{todo_id}")
def get_todo(todo_id: int) -> dict[str, int | str]:
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return {"message": f"Todo {todo_id} not found"}


@app.post("/todo")
def create_todo(todo: TodoCreate) -> dict[str, int | str]:
    new_id = max(t["id"] for t in todos) + 1 if todos else 1
    new_todo = {"id": new_id, "task": todo.task}
    todos.append(new_todo)
    return new_todo


@app.put("/todo/{todo_id}")
def update_todo(todo_id: int, todo: TodoCreate) -> dict[str, int | str]:
    for t in todos:
        if t["id"] == todo_id:
            t["task"] = todo.task
            return t
    return {"message": f"Todo {todo_id} not found"}


@app.delete("/todo/{todo_id}")
def delete_todo(todo_id: int) -> dict[str, str]:
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            todos.pop(i)
            return {"message": f"Todo {todo_id} deleted"}
    return {"message": f"Todo {todo_id} not found"}