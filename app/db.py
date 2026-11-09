"""Database engine, session factory and FastAPI dependency.

@author Alfie
"""

from collections.abc import Generator

from sqlalchemy import create_engine
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
