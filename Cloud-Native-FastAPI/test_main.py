import pytest
from fastapi.testclient import TestClient
from main import app
from main import TodoItemResponse
client = TestClient(app)

def test_read_ root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Cloud Native FastAPI"}

def test_todo():
    response = client.get("/todo")
    assert response.status_code == 200
    expected_response = [
        {"id": 1, "task": "Learn Docker", "time_estimate": None, "completed": False},
        {"id": 2, "task": "Build a Docker Image", "time_estimate": None, "completed": False},
    ]

    assert response.json() == expected_response

def test_add_todo():
    new_todo = {"id": 3, "task": "Test FastAPI", "time_estimate": 30}
    response = client.post("/todo", json=new_todo)
    assert response.status_code == 200
    expected_response = {"id": 3, "task": "Test FastAPI", "time_estimate": 30, "completed": False}
    assert response.json() == expected_response

    def test_delete_todo():
        item_id = 1
        response = client.delete(f"/todo/{item_id}")
        assert response.status_code == 200
        assert response.json() == {"message": f"Todo item with ID {item_id} deleted"}

def test_update_todo():
    item_id = 2
    updated_todo = {"id": 2, "task": "Build a Docker Image - Updated", "time_estimate": 45}
    response = client.put(f"/todo/{item_id}", json=updated_todo)
    assert response.status_code == 200
    expected_response = {"id": 2, "task": "Build a Docker Image - Updated", "time_estimate": 45, "completed": False}
    assert response.json() == expected_response
    
def test_complete_todo():
    item_id = 2
    response = client.patch(f"/todo/{item_id}/complete")
    assert response.status_code == 200
    expected_response = {"id": item_id, "task": "Sample Task", "time_estimate": None, "completed": True}
    assert response.json() == expected_response

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "Service is running"
    
    

@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Cloud Native FastAPI"}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "Service is running"
