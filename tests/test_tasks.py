"""API behaviour tests for the task board.

@author Alfie
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app import db as db_module


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


def test_create_defaults_priority_to_medium_and_due_date_to_null(client: TestClient) -> None:
    """Omitted priority and due date fall back to their defaults.

    @author Alfie
    """
    created = create_task(client)
    assert created["priority"] == "medium"
    assert created["due_date"] is None


def test_create_with_priority_and_due_date(client: TestClient) -> None:
    """Supplied priority and due date are persisted and returned.

    @author Alfie
    """
    created = create_task(client, priority="high", due_date="2026-12-31")
    assert created["priority"] == "high"
    assert created["due_date"] == "2026-12-31"


def test_every_task_endpoint_returns_priority_and_due_date(client: TestClient) -> None:
    """List, get and patch responses include both new fields.

    @author Alfie
    """
    created = create_task(client, priority="low", due_date="2026-11-20")

    listed = client.get("/tasks").json()[0]
    fetched = client.get(f"/tasks/{created['id']}").json()
    patched = client.patch(f"/tasks/{created['id']}", json={"status": "doing"}).json()

    for body in (listed, fetched, patched):
        assert body["priority"] == "low"
        assert body["due_date"] == "2026-11-20"


def test_update_priority_and_due_date(client: TestClient) -> None:
    """PATCH changes priority and due date without touching other fields.

    @author Alfie
    """
    created = create_task(client)
    response = client.patch(
        f"/tasks/{created['id']}",
        json={"priority": "high", "due_date": "2027-01-15"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["priority"] == "high"
    assert body["due_date"] == "2027-01-15"
    assert body["title"] == created["title"]
    assert body["status"] == created["status"]


def test_update_without_new_fields_keeps_them(client: TestClient) -> None:
    """A PATCH that omits priority and due date leaves them unchanged.

    @author Alfie
    """
    created = create_task(client, priority="high", due_date="2026-12-01")
    body = client.patch(f"/tasks/{created['id']}", json={"title": "Renamed"}).json()
    assert body["priority"] == "high"
    assert body["due_date"] == "2026-12-01"


def test_update_can_clear_due_date(client: TestClient) -> None:
    """Sending ``null`` clears the due date.

    @author Alfie
    """
    created = create_task(client, due_date="2026-12-01")
    response = client.patch(f"/tasks/{created['id']}", json={"due_date": None})
    assert response.status_code == 200, response.text
    assert response.json()["due_date"] is None


@pytest.mark.parametrize("priority", ["urgent", "HIGH", "", 1])
def test_create_rejects_invalid_priority(client: TestClient, priority: object) -> None:
    """Unknown priorities are rejected on create.

    @author Alfie
    """
    response = client.post("/tasks", json={"title": "x", "priority": priority})
    assert response.status_code == 422


@pytest.mark.parametrize("priority", ["urgent", None])
def test_update_rejects_invalid_priority(client: TestClient, priority: object) -> None:
    """Unknown or null priorities are rejected on update and nothing changes.

    @author Alfie
    """
    created = create_task(client, priority="low")
    response = client.patch(f"/tasks/{created['id']}", json={"priority": priority})
    assert response.status_code == 422
    assert client.get(f"/tasks/{created['id']}").json()["priority"] == "low"


@pytest.mark.parametrize(
    "due_date",
    [
        "2026/12/31",
        "31-12-2026",
        "2026-1-5",
        "2026-02-30",
        "2026-13-01",
        "2026-12-31T00:00:00",
        "tomorrow",
        "",
        20261231,
    ],
)
def test_create_rejects_invalid_due_date(client: TestClient, due_date: object) -> None:
    """Due dates must be real calendar dates in ``YYYY-MM-DD`` format.

    @author Alfie
    """
    response = client.post("/tasks", json={"title": "x", "due_date": due_date})
    assert response.status_code == 422


@pytest.mark.parametrize("due_date", ["2026/12/31", "2026-02-30", 0])
def test_update_rejects_invalid_due_date(client: TestClient, due_date: object) -> None:
    """Invalid due dates are rejected on update and nothing changes.

    @author Alfie
    """
    created = create_task(client, due_date="2026-12-01")
    response = client.patch(f"/tasks/{created['id']}", json={"due_date": due_date})
    assert response.status_code == 422
    assert client.get(f"/tasks/{created['id']}").json()["due_date"] == "2026-12-01"


def test_filter_tasks_by_priority(client: TestClient) -> None:
    """The priority filter only returns matching tasks.

    @author Alfie
    """
    low = create_task(client, title="Low", priority="low")
    medium = create_task(client, title="Medium")
    high = create_task(client, title="High", priority="high")

    for priority, expected in (("low", low), ("medium", medium), ("high", high)):
        response = client.get("/tasks", params={"priority": priority})
        assert response.status_code == 200
        assert [task["id"] for task in response.json()] == [expected["id"]]


def test_filter_by_priority_and_status_combined(client: TestClient) -> None:
    """Priority and status filters can be combined.

    @author Alfie
    """
    create_task(client, title="High todo", priority="high")
    high_doing = create_task(client, title="High doing", priority="high", status="doing")
    create_task(client, title="Low doing", priority="low", status="doing")

    response = client.get("/tasks", params={"priority": "high", "status": "doing"})
    assert [task["id"] for task in response.json()] == [high_doing["id"]]


def test_filter_rejects_unknown_priority(client: TestClient) -> None:
    """An unknown priority filter value is a validation error.

    @author Alfie
    """
    assert client.get("/tasks", params={"priority": "urgent"}).status_code == 422


def test_init_db_upgrades_legacy_tasks_table(tmp_path, monkeypatch) -> None:
    """A ``tasks`` table created before the new columns gains them on startup.

    @author Alfie
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE tasks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(200) NOT NULL, "
                "description TEXT, status VARCHAR(16) NOT NULL, "
                "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO tasks (title, status, created_at, updated_at) "
                "VALUES ('Old task', 'todo', '2026-11-01 00:00:00', '2026-11-01 00:00:00')"
            )
        )
    monkeypatch.setattr(db_module, "engine", engine)

    db_module.init_db()
    db_module.init_db()

    columns = {column["name"] for column in inspect(engine).get_columns("tasks")}
    assert {"priority", "due_date"} <= columns
    with engine.connect() as connection:
        row = connection.execute(text("SELECT priority, due_date FROM tasks")).one()
    assert row == ("medium", None)


def test_init_db_tolerates_concurrent_legacy_upgrade(tmp_path, monkeypatch) -> None:
    """A column added by another worker after the check does not abort startup.

    @author Alfie
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE tasks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(200) NOT NULL, "
                "description TEXT, status VARCHAR(16) NOT NULL, "
                "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
            )
        )
    monkeypatch.setattr(db_module, "engine", engine)
    real_column_names = db_module._task_column_names
    calls = {"count": 0}

    def stale_then_real() -> set[str]:
        calls["count"] += 1
        if calls["count"] == 1:
            names = real_column_names()
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE tasks ADD COLUMN priority VARCHAR(16) NOT NULL DEFAULT 'medium'")
                )
            return names
        return real_column_names()

    monkeypatch.setattr(db_module, "_task_column_names", stale_then_real)

    db_module.init_db()

    assert {"priority", "due_date"} <= real_column_names()

