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
`tasks.db`; an existing `tasks.db` from an older version gains the
`priority` and `due_date` columns automatically.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness probe |
| GET | `/tasks` | List tasks; optional `?status=todo\|doing\|done` and `?priority=low\|medium\|high` |
| POST | `/tasks` | Create a task |
| GET | `/tasks/{id}` | Fetch one task |
| PATCH | `/tasks/{id}` | Partially update a task |
| DELETE | `/tasks/{id}` | Delete a task |

## Task fields

| Field | Type | Notes |
| --- | --- | --- |
| `title` | string | Required, 1–200 chars, not blank |
| `description` | string \| null | Up to 2000 chars |
| `status` | `todo` \| `doing` \| `done` | Defaults to `todo` |
| `priority` | `low` \| `medium` \| `high` | Defaults to `medium`; cannot be set to `null` |
| `due_date` | `YYYY-MM-DD` \| null | Optional calendar date; `PATCH` with `null` clears it |

Invalid values are rejected with `422`.

## Test

```bash
pytest
```
