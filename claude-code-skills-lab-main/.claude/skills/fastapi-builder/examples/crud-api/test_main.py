"""Tests for CRUD API"""
from fastapi.testclient import TestClient
from main import app, tasks_db

client = TestClient(app)


def setup_function():
    """Clear database before each test"""
    tasks_db.clear()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Task API" in response.json()["message"]


def test_create_task():
    response = client.post(
        "/tasks",
        json={"title": "Test task", "description": "Test description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test task"
    assert data["description"] == "Test description"
    assert data["completed"] is False
    assert "id" in data


def test_get_tasks():
    # Create a task first
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_task():
    # Create a task
    create_response = client.post("/tasks", json={"title": "Test task"})
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test task"


def test_get_task_not_found():
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task():
    # Create a task
    create_response = client.post("/tasks", json={"title": "Original"})
    task_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated", "completed": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["completed"] is True


def test_delete_task():
    # Create a task
    create_response = client.post("/tasks", json={"title": "To delete"})
    task_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404
