"""Skill catalog — canonical taxonomy of skills (seeded, mostly read-only)."""
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SkillCategory(str, Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    PLATFORM = "platform"
    TOOL = "tool"
    DOMAIN = "domain"


class Skill(Base):
    __tablename__ = "skills_catalog"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # SkillCategory values
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
