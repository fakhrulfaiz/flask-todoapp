import pytest
from app import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_get_todos_empty(client):
    res = client.get("/todos")
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_todo(client):
    res = client.post("/todos", json={"title": "Buy milk"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Buy milk"
    assert data["done"] is False
    assert "id" in data


def test_create_todo_missing_title(client):
    res = client.post("/todos", json={})
    assert res.status_code == 400


def test_get_todo(client):
    created = client.post("/todos", json={"title": "Learn GitHub Actions"}).get_json()
    res = client.get(f"/todos/{created['id']}")
    assert res.status_code == 200
    assert res.get_json()["title"] == "Learn GitHub Actions"


def test_get_todo_not_found(client):
    res = client.get("/todos/99")
    assert res.status_code == 404


def test_update_todo(client):
    created = client.post("/todos", json={"title": "Old title"}).get_json()
    res = client.put(f"/todos/{created['id']}", json={"title": "New title", "done": True})
    assert res.status_code == 200
    data = res.get_json()
    assert data["title"] == "New title"
    assert data["done"] is True


def test_update_todo_not_found(client):
    res = client.put("/todos/99", json={"title": "Ghost"})
    assert res.status_code == 404


def test_delete_todo(client):
    created = client.post("/todos", json={"title": "Delete me"}).get_json()
    todo_id = created["id"]
    res = client.delete(f"/todos/{todo_id}")
    assert res.status_code == 200
    assert client.get(f"/todos/{todo_id}").status_code == 404


def test_delete_todo_not_found(client):
    res = client.delete("/todos/99")
    assert res.status_code == 404


def test_index_page(client):
    """The HTML page should render with a 200 status."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"My Tasks" in res.data


def test_ui_create_todo(client):
    """Creating a todo via the HTML form should redirect to index."""
    res = client.post("/ui/todos", data={"title": "Form todo"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Form todo" in res.data


def test_ui_toggle_todo(client):
    """Toggling a todo via the HTML form should flip its done state."""
    created = client.post("/todos", json={"title": "Toggle me"}).get_json()
    todo_id = created["id"]
    client.post(f"/ui/todos/{todo_id}/toggle")
    updated = client.get(f"/todos/{todo_id}").get_json()
    assert updated["done"] is True


def test_ui_delete_todo(client):
    """Deleting a todo via the HTML form should remove it."""
    created = client.post("/todos", json={"title": "Delete via UI"}).get_json()
    todo_id = created["id"]
    client.post(f"/ui/todos/{todo_id}/delete")
    assert client.get(f"/todos/{todo_id}").status_code == 404
