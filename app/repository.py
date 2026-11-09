"""Persistence helpers for tasks.

Keeping SQL in this module makes the route handlers small and gives the demo
agent a clear place to extend the model.

@author Alfie
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskUpdate


def list_tasks(
    db: Session,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    """Return tasks, newest first, optionally filtered by status and priority.

    @author Alfie
    """
    statement = select(Task).order_by(Task.created_at.desc(), Task.id.desc())
    if status is not None:
        statement = statement.where(Task.status == status.value)
    if priority is not None:
        statement = statement.where(Task.priority == priority.value)
    return list(db.scalars(statement))


def get_task(db: Session, task_id: int) -> Task | None:
    """Return one task by id, or ``None`` when it does not exist.

    @author Alfie
    """
    return db.get(Task, task_id)


def create_task(db: Session, payload: TaskCreate) -> Task:
    """Insert a new task and return the persisted entity.

    @author Alfie
    """
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status.value,
        priority=payload.priority.value,
        due_date=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    """Apply the supplied fields to a task and persist the result.

    @author Alfie
    """
    changes = payload.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] is not None:
        changes["status"] = changes["status"].value
    if "priority" in changes and changes["priority"] is not None:
        changes["priority"] = changes["priority"].value
    for field, value in changes.items():
        setattr(task, field, value)
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """Delete a task.

    @author Alfie
    """
    db.delete(task)
    db.commit()
