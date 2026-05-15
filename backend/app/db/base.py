"""SQLAlchemy 2.0 declarative base."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All ORM models inherit from this."""
    pass
