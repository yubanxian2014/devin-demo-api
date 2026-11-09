"""Pydantic request and response schemas.

@author Alfie
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskStatus


class TaskCreate(BaseModel):
    """Payload used to create a task.

    @author Alfie
    """

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = TaskStatus.todo

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


class TaskUpdate(BaseModel):
    """Partial update payload. Only supplied fields are applied.

    @author Alfie
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None

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


class TaskRead(BaseModel):
    """Task representation returned by the API.

    @author Alfie
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
