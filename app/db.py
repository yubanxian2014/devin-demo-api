"""Database engine, session factory and FastAPI dependency.

@author Alfie
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
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
    _add_missing_task_columns(engine)


def _add_missing_task_columns(bind: Engine) -> None:
    """Add columns introduced after the first release to an existing ``tasks`` table.

    ``create_all`` never alters existing tables, so a ``tasks.db`` created by
    an older version would otherwise lack ``priority`` and ``due_date``.

    @author Alfie
    """
    existing = {column["name"] for column in inspect(bind).get_columns("tasks")}
    statements = {
        "priority": "ALTER TABLE tasks ADD COLUMN priority VARCHAR(16) NOT NULL DEFAULT 'medium'",
        "due_date": "ALTER TABLE tasks ADD COLUMN due_date DATE",
    }
    with bind.begin() as connection:
        for name, statement in statements.items():
            if name not in existing:
                connection.execute(text(statement))
