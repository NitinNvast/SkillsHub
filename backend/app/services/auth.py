"""Authentication service: verify credentials, mint tokens."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User, UserRole


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def issue_token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


async def register_employee(
    session: AsyncSession, name: str, email: str, password: str
) -> User | None:
    """Create a new employee User. Returns None if email is already taken."""
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        return None
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        role=UserRole.EMPLOYEE.value,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
