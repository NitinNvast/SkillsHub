"""ORM models — single import point.

Importing this module ensures every table is registered on Base.metadata,
which Alembic autogen and FastAPI dependency resolution both rely on.
"""
from app.db.models.certification import Certification
from app.db.models.embedding import EmployeeEmbedding
from app.db.models.employee import Availability, Employee
from app.db.models.employee_skill import EmployeeSkill, ProficiencyLevel, SkillSource
from app.db.models.project import Project
from app.db.models.resume_upload import ResumeUpload, UploadSource, UploadStatus
from app.db.models.skill import Skill, SkillCategory
from app.db.models.user import User, UserRole

__all__ = [
    "Availability",
    "Certification",
    "Employee",
    "EmployeeEmbedding",
    "EmployeeSkill",
    "ProficiencyLevel",
    "Project",
    "ResumeUpload",
    "Skill",
    "SkillCategory",
    "SkillSource",
    "UploadSource",
    "UploadStatus",
    "User",
    "UserRole",
]
