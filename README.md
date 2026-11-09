# devin-demo-api

A deliberately small task board API used as the backend half of a
multi-repository Devin demo. The matching frontend lives in `devin-demo-web`.

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
`tasks.db`. Older `tasks.db` files are upgraded in place with the `priority`
and `due_date` columns.

## Task fields

| Field | Type | Notes |
| --- | --- | --- |
| `title` | string | Required, 1–200 chars, not blank |
| `description` | string \| null | Up to 2000 chars |
| `status` | `todo` \| `doing` \| `done` | Defaults to `todo` |
| `priority` | `low` \| `medium` \| `high` | Defaults to `medium`; cannot be `null` on update |
| `due_date` | `YYYY-MM-DD` \| null | Optional; send `null` on PATCH to clear it |

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness probe |
| GET | `/tasks` | List tasks; optional `?status=todo\|doing\|done` and `?priority=low\|medium\|high` |
| POST | `/tasks` | Create a task |
| GET | `/tasks/{id}` | Fetch one task |
| PATCH | `/tasks/{id}` | Partially update a task |
| DELETE | `/tasks/{id}` | Delete a task |

## Test

```bash
pytest
```
