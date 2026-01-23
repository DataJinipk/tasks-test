"""
CRUD API Example with FastAPI and Pydantic
Run: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing tasks",
    version="1.0.0"
)

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

# In-memory database
tasks_db: List[Task] = []
task_id_counter = 0


@app.get("/")
async def root():
    return {"message": "Task API - visit /docs for documentation"}


@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task"""
    global task_id_counter
    task_id_counter += 1
    new_task = Task(id=task_id_counter, **task.model_dump())
    tasks_db.append(new_task)
    return new_task


@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    """Get all tasks"""
    return tasks_db


@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Get a specific task by ID"""
    task = next((t for t in tasks_db if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_update: TaskUpdate):
    """Update an existing task"""
    task_idx = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    if task_idx is None:
        raise HTTPException(status_code=404, detail="Task not found")

    existing_task = tasks_db[task_idx]
    update_data = task_update.model_dump(exclude_unset=True)
    updated_task = existing_task.model_copy(update=update_data)
    tasks_db[task_idx] = updated_task
    return updated_task


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """Delete a task"""
    task_idx = next((i for i, t in enumerate(tasks_db) if t.id == task_id), None)
    if task_idx is None:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_db.pop(task_idx)
