"""API behaviour tests for the task board.

@author Alfie
"""

from fastapi.testclient import TestClient


def create_task(client: TestClient, **overrides) -> dict:
    """Create a task through the API and return the JSON body.

    @author Alfie
    """
    payload = {"title": "Write the demo", "description": "Ship it"}
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    """The health endpoint is always available.

    @author Alfie
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_tasks(client: TestClient) -> None:
    """Creating a task makes it visible in the list.

    @author Alfie
    """
    created = create_task(client)
    assert created["title"] == "Write the demo"
    assert created["status"] == "todo"

    response = client.get("/tasks")
    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [created["id"]]


def test_filter_tasks_by_status(client: TestClient) -> None:
    """The status filter only returns matching tasks.

    @author Alfie
    """
    todo = create_task(client, title="Todo task")
    doing = create_task(client, title="Doing task", status="doing")

    response = client.get("/tasks", params={"status": "doing"})
    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [doing["id"]]

    response = client.get("/tasks", params={"status": "todo"})
    assert [task["id"] for task in response.json()] == [todo["id"]]


def test_get_task(client: TestClient) -> None:
    """A single task can be fetched by id.

    @author Alfie
    """
    created = create_task(client)
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_task(client: TestClient) -> None:
    """Partial updates only change the supplied fields.

    @author Alfie
    """
    created = create_task(client)
    response = client.patch(
        f"/tasks/{created['id']}",
        json={"status": "done", "title": "Updated title"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["title"] == "Updated title"
    assert body["description"] == "Ship it"


def test_delete_task(client: TestClient) -> None:
    """Deleted tasks disappear from the list and return 404 afterwards.

    @author Alfie
    """
    created = create_task(client)
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_reject_blank_title(client: TestClient) -> None:
    """Whitespace-only titles are rejected.

    @author Alfie
    """
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_reject_unknown_status(client: TestClient) -> None:
    """Unknown statuses are rejected by schema validation.

    @author Alfie
    """
    response = client.post("/tasks", json={"title": "x", "status": "blocked"})
    assert response.status_code == 422


def test_missing_task_returns_404(client: TestClient) -> None:
    """Operations on an unknown id return 404.

    @author Alfie
    """
    assert client.get("/tasks/999").status_code == 404
    assert client.patch("/tasks/999", json={"status": "done"}).status_code == 404
    assert client.delete("/tasks/999").status_code == 404


def test_priority_and_due_date_default(client: TestClient) -> None:
    """Tasks default to medium priority and no due date.

    @author Alfie
    """
    created = create_task(client)
    assert created["priority"] == "medium"
    assert created["due_date"] is None


def test_priority_and_due_date_round_trip(client: TestClient) -> None:
    """Priority and due date are returned by create, get, list and patch.

    @author Alfie
    """
    created = create_task(client, priority="high", due_date="2026-12-01")
    assert created["priority"] == "high"
    assert created["due_date"] == "2026-12-01"

    fetched = client.get(f"/tasks/{created['id']}").json()
    assert fetched["priority"] == "high"
    assert fetched["due_date"] == "2026-12-01"

    listed = client.get("/tasks").json()
    assert listed[0]["priority"] == "high"
    assert listed[0]["due_date"] == "2026-12-01"

    patched = client.patch(f"/tasks/{created['id']}", json={"status": "doing"}).json()
    assert patched["priority"] == "high"
    assert patched["due_date"] == "2026-12-01"


def test_update_priority_and_due_date(client: TestClient) -> None:
    """Priority and due date can be changed, and the due date can be cleared.

    @author Alfie
    """
    created = create_task(client, due_date="2026-12-01")

    response = client.patch(
        f"/tasks/{created['id']}",
        json={"priority": "low", "due_date": "2027-01-15"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == "low"
    assert body["due_date"] == "2027-01-15"
    assert body["title"] == created["title"]

    response = client.patch(f"/tasks/{created['id']}", json={"due_date": None})
    assert response.status_code == 200
    assert response.json()["due_date"] is None
    assert response.json()["priority"] == "low"


def test_filter_tasks_by_priority(client: TestClient) -> None:
    """The priority filter only returns matching tasks and combines with status.

    @author Alfie
    """
    high = create_task(client, title="High", priority="high")
    create_task(client, title="Low", priority="low")
    high_done = create_task(client, title="High done", priority="high", status="done")

    response = client.get("/tasks", params={"priority": "high"})
    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [high_done["id"], high["id"]]

    response = client.get("/tasks", params={"priority": "high", "status": "todo"})
    assert [task["id"] for task in response.json()] == [high["id"]]


def test_reject_unknown_priority(client: TestClient) -> None:
    """Unknown priorities are rejected on create, update and filter.

    @author Alfie
    """
    assert client.post("/tasks", json={"title": "x", "priority": "urgent"}).status_code == 422
    created = create_task(client)
    assert (
        client.patch(f"/tasks/{created['id']}", json={"priority": "urgent"}).status_code == 422
    )
    assert client.get("/tasks", params={"priority": "urgent"}).status_code == 422


def test_reject_null_priority_on_update(client: TestClient) -> None:
    """Priority cannot be cleared with an explicit null.

    @author Alfie
    """
    created = create_task(client)
    response = client.patch(f"/tasks/{created['id']}", json={"priority": None})
    assert response.status_code == 422


def test_reject_invalid_due_date(client: TestClient) -> None:
    """Malformed or impossible due dates are rejected.

    @author Alfie
    """
    for value in ["tomorrow", "2026-02-30", "2026/12/01"]:
        response = client.post("/tasks", json={"title": "x", "due_date": value})
        assert response.status_code == 422, value


def test_init_db_adds_columns_to_legacy_table(tmp_path) -> None:
    """A tasks table created before priority/due_date gains the new columns.

    @author Alfie
    """
    from sqlalchemy import create_engine, inspect, text

    from app.db import _add_missing_task_columns

    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE tasks (id INTEGER PRIMARY KEY, title VARCHAR(200) NOT NULL, "
                "description TEXT, status VARCHAR(16) NOT NULL, "
                "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO tasks (title, status, created_at, updated_at) "
                "VALUES ('old', 'todo', '2026-01-01', '2026-01-01')"
            )
        )

    _add_missing_task_columns(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("tasks")}
    assert {"priority", "due_date"} <= columns
    with engine.connect() as connection:
        row = connection.execute(text("SELECT priority, due_date FROM tasks")).one()
    assert row == ("medium", None)
