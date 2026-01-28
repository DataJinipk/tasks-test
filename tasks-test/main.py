from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()


class TodoBase(SQLModel):
    task: str
    completed: bool = False


class Todo(TodoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    task: str | None = None
    completed: bool | None = None


engine = create_engine("sqlite:///todos.db", connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)) -> Todo:
    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@app.get("/todos")
def get_todos(
    session: Session = Depends(get_session),
    completed: bool | None = None,
    search: str | None = None,
) -> list[Todo]:
    query = select(Todo)
    if completed is not None:
        query = query.where(Todo.completed == completed)
    if search:
        query = query.where(Todo.task.contains(search))
    return session.exec(query).all()


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, session: Session = Depends(get_session)) -> Todo:
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.put("/todos/{todo_id}")
def update_todo(
    todo_id: int, todo_update: TodoUpdate, session: Session = Depends(get_session)
) -> Todo:
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    update_data = todo_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(todo, key, value)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
