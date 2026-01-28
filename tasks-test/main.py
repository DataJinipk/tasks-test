from fastapi import FastAPI

app = FastAPI()

@app.get("/tasks")
def todo() -> list[dict[str, str | int]]:
    return [{"id": 1, "task": "Buy groceries"},
            {"id": 2, "task": "Read a book"},
            {"id": 3, "task": "Walk the dog"}]
