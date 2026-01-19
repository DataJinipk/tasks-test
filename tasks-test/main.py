from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select


# Database model
class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task: str
    completed: bool = False


# Request models
class TodoCreate(SQLModel):
    task: str
    completed: bool = False


class TodoUpdate(SQLModel):
    task: str | None = None
    completed: bool | None = None


# Database setup
DATABASE_URL = "sqlite:///todos.db"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


# GET all todos
@app.get("/todos")
def get_todos(session: Session = Depends(get_session)) -> list[Todo]:
    return session.exec(select(Todo)).all()


# GET single todo by id
@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, session: Session = Depends(get_session)) -> Todo:
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


# POST create new todo
@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)) -> Todo:
    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


# PUT update todo
@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: TodoUpdate, session: Session = Depends(get_session)) -> Todo:
    db_todo = session.get(Todo, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.task is not None:
        db_todo.task = todo.task
    if todo.completed is not None:
        db_todo.completed = todo.completed
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


# DELETE todo
@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
