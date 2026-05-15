"""Seed demo data: HR + Employee users and the canonical skills catalog.

Run inside the backend container:
    docker compose exec backend uv run python -m app.seed.seed_demo

Full demo profiles (10–15 employees) are loaded by a separate seed script in Step 14.
This script is idempotent — re-running won't duplicate rows.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models import Skill, User, UserRole
from app.db.session import SessionLocal
from app.seed.skills_catalog import CANONICAL_SKILLS

DEMO_USERS = [
    {
        "email": "hr@demo.com",
        "password": "demo1234",
        "name": "Aria HR",
        "role": UserRole.HR.value,
    },
    {
        "email": "emp@demo.com",
        "password": "demo1234",
        "name": "Sam Employee",
        "role": UserRole.EMPLOYEE.value,
    },
]


async def seed_users(session: AsyncSession) -> None:
    for u in DEMO_USERS:
        existing = await session.execute(select(User).where(User.email == u["email"]))
        if existing.scalar_one_or_none():
            print(f"  · user exists: {u['email']}")
            continue
        session.add(
            User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                name=u["name"],
                role=u["role"],
            )
        )
        print(f"  ✓ user created: {u['email']} (role={u['role']})")
    await session.commit()


async def seed_skills(session: AsyncSession) -> None:
    existing = await session.execute(select(Skill.name))
    existing_names = {row[0] for row in existing.all()}
    added = 0
    for name, category, aliases in CANONICAL_SKILLS:
        if name in existing_names:
            continue
        session.add(Skill(name=name, category=category, aliases=aliases))
        added += 1
    await session.commit()
    total = len(CANONICAL_SKILLS)
    print(f"  ✓ skills_catalog: +{added} new, {total - added} existed (total {total})")


async def main() -> None:
    async with SessionLocal() as session:
        print("Seeding demo data…")
        await seed_users(session)
        await seed_skills(session)
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
