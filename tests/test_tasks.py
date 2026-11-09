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
