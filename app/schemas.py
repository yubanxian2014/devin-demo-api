"""Pydantic request and response schemas.

@author Alfie
"""

import re
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskPriority, TaskStatus

_ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _require_iso_date_string(value: Any) -> Any:
    """Only accept ``YYYY-MM-DD`` strings (or ``None``) for due dates.

    Pydantic's lax date parsing would otherwise also accept timestamps and
    datetime strings.

    @author Alfie
    """
    if value is None or isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str) and _ISO_DATE_PATTERN.match(value):
        return value
    raise ValueError("due_date must be a date in YYYY-MM-DD format")


class TaskCreate(BaseModel):
    """Payload used to create a task.

    @author Alfie
    """

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        """Reject titles that only contain whitespace.

        @author Alfie
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        return cleaned

    @field_validator("due_date", mode="before")
    @classmethod
    def due_date_must_be_iso_date(cls, value: Any) -> Any:
        """Reject due dates that are not ``YYYY-MM-DD``.

        @author Alfie
        """
        return _require_iso_date_string(value)


class TaskUpdate(BaseModel):
    """Partial update payload. Only supplied fields are applied.

    ``due_date`` may be set to ``null`` to clear it; ``priority`` may not.

    @author Alfie
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def optional_title_must_not_be_blank(cls, value: str | None) -> str | None:
        """Reject an explicitly supplied blank title.

        @author Alfie
        """
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        return cleaned

    @field_validator("priority", mode="before")
    @classmethod
    def priority_must_not_be_null(cls, value: Any) -> Any:
        """Reject an explicit ``null`` priority; every task keeps one.

        @author Alfie
        """
        if value is None:
            raise ValueError("priority must be one of: low, medium, high")
        return value

    @field_validator("due_date", mode="before")
    @classmethod
    def due_date_must_be_iso_date(cls, value: Any) -> Any:
        """Reject due dates that are not ``YYYY-MM-DD``.

        @author Alfie
        """
        return _require_iso_date_string(value)


class TaskRead(BaseModel):
    """Task representation returned by the API.

    @author Alfie
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    created_at: datetime
    updated_at: datetime
