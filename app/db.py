"""Database engine, session factory and FastAPI dependency.

@author Alfie
"""

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models.

    @author Alfie
    """


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session.

    The session is always closed, even when the route raises.

    @author Alfie
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables on startup.

    Importing ``app.models`` registers the ORM classes on ``Base.metadata``
    before ``create_all`` runs.

    @author Alfie
    """
    from app import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
    _add_missing_task_columns()


def _add_missing_task_columns() -> None:
    """Add ``priority`` / ``due_date`` to a ``tasks.db`` created before they existed.

    ``create_all`` never alters existing tables, so older local databases are
    upgraded in place here.

    @author Alfie
    """
    existing = {column["name"] for column in inspect(engine).get_columns("tasks")}
    statements = []
    if "priority" not in existing:
        statements.append(
            "ALTER TABLE tasks ADD COLUMN priority VARCHAR(16) NOT NULL DEFAULT 'medium'"
        )
    if "due_date" not in existing:
        statements.append("ALTER TABLE tasks ADD COLUMN due_date DATE")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
