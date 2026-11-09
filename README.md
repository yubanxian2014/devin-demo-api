# devin-demo-api

A deliberately small task board API used as the backend half of a
multi-repository Devin demo. The baseline has no priority or due-date fields:
the demo requirement asks Devin to add them across this repository and
`devin-demo-web`.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- pytest

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. Tables are created on startup in
`tasks.db`.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness probe |
| GET | `/tasks` | List tasks; optional `?status=todo\|doing\|done` |
| POST | `/tasks` | Create a task |
| GET | `/tasks/{id}` | Fetch one task |
| PATCH | `/tasks/{id}` | Partially update a task |
| DELETE | `/tasks/{id}` | Delete a task |

## Test

```bash
pytest
```

## Demo requirement (not implemented on purpose)

Add `priority` (`low` / `medium` / `high`) and `due_date` to tasks, validate
them at the API boundary, return them from every endpoint, and cover the new
behaviour with pytest. The matching frontend change lives in
`devin-demo-web`.
