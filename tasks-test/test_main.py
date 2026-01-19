import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session, Todo


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_todo(client: TestClient):
    response = client.post("/todos", json={"task": "Test task"})
    assert response.status_code == 201
    data = response.json()
    assert data["task"] == "Test task"
    assert data["completed"] == False
    assert "id" in data


def test_create_todo_with_completed(client: TestClient):
    response = client.post("/todos", json={"task": "Already done", "completed": True})
    assert response.status_code == 201
    data = response.json()
    assert data["task"] == "Already done"
    assert data["completed"] == True


def test_get_todos_empty(client: TestClient):
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_get_todos(client: TestClient):
    client.post("/todos", json={"task": "Task 1"})
    client.post("/todos", json={"task": "Task 2"})
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_todo(client: TestClient):
    create_response = client.post("/todos", json={"task": "My task"})
    todo_id = create_response.json()["id"]
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["task"] == "My task"


def test_get_todo_not_found(client: TestClient):
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"


def test_update_todo_task(client: TestClient):
    create_response = client.post("/todos", json={"task": "Original"})
    todo_id = create_response.json()["id"]
    response = client.put(f"/todos/{todo_id}", json={"task": "Updated"})
    assert response.status_code == 200
    assert response.json()["task"] == "Updated"


def test_update_todo_completed(client: TestClient):
    create_response = client.post("/todos", json={"task": "Do this"})
    todo_id = create_response.json()["id"]
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["task"] == "Do this"
    assert data["completed"] == True


def test_update_todo_not_found(client: TestClient):
    response = client.put("/todos/999", json={"task": "Nope"})
    assert response.status_code == 404


def test_delete_todo(client: TestClient):
    create_response = client.post("/todos", json={"task": "Delete me"})
    todo_id = create_response.json()["id"]
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    # Verify it's gone
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404


def test_delete_todo_not_found(client: TestClient):
    response = client.delete("/todos/999")
    assert response.status_code == 404
