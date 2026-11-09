"""ORM models for the task board.

The baseline model intentionally has no priority or due-date fields: the
multi-repository Devin demo asks the agent to add them across the API and the
web client.

@author Alfie
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    @author Alfie
    """
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    """Allowed task statuses.

    @author Alfie
    """

    todo = "todo"
    doing = "doing"
    done = "done"


class Task(Base):
    """A single task in the board.

    @author Alfie
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=TaskStatus.todo.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
