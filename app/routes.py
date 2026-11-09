"""HTTP routes for the task board.

@author Alfie
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import repository
from app.db import get_db
from app.models import TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority_filter: TaskPriority | None = Query(default=None, alias="priority"),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    """List tasks, optionally filtered by status and/or priority.

    @author Alfie
    """
    return repository.list_tasks(db, status_filter, priority_filter)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    """Create a task.

    @author Alfie
    """
    return repository.create_task(db, payload)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    """Return one task or 404.

    @author Alfie
    """
    task = repository.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskRead:
    """Apply a partial update to a task.

    @author Alfie
    """
    task = repository.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return repository.update_task(db, task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a task.

    @author Alfie
    """
    task = repository.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    repository.delete_task(db, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
