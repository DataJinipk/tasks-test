from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello, World!"}


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


class RecipeBase(SQLModel):
    title: str
    cuisine: str
    difficulty: str
    prep_time: int
    ingredients: str


class Recipe(RecipeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(SQLModel):
    title: str | None = None
    cuisine: str | None = None
    difficulty: str | None = None
    prep_time: int | None = None
    ingredients: str | None = None


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


# Recipe endpoints


@app.post("/recipes", status_code=201)
def create_recipe(
    recipe: RecipeCreate, session: Session = Depends(get_session)
) -> Recipe:
    db_recipe = Recipe.model_validate(recipe)
    session.add(db_recipe)
    session.commit()
    session.refresh(db_recipe)
    return db_recipe


@app.get("/recipes")
def list_recipes(
    session: Session = Depends(get_session),
    cuisine: str | None = None,
    difficulty: str | None = None,
) -> list[Recipe]:
    query = select(Recipe)
    if cuisine:
        query = query.where(Recipe.cuisine == cuisine)
    if difficulty:
        query = query.where(Recipe.difficulty == difficulty)
    return session.exec(query).all()


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int, session: Session = Depends(get_session)) -> Recipe:
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.put("/recipes/{recipe_id}")
def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    session: Session = Depends(get_session),
) -> Recipe:
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    update_data = recipe_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recipe, key, value)
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return recipe


@app.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, session: Session = Depends(get_session)):
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    session.delete(recipe)
    session.commit()
