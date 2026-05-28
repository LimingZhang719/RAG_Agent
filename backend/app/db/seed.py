from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.enums import RoleName
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.db.session import AsyncSessionLocal


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        org = await session.scalar(select(Organization).where(Organization.name == "HQ"))
        if org is None:
            org = Organization(name="HQ")
            session.add(org)
            await session.flush()

        roles_by_name: dict[RoleName, Role] = {}
        for role_name in RoleName:
            role = await session.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                role = Role(name=role_name, description=role_name.value)
                session.add(role)
                await session.flush()
            roles_by_name[role_name] = role

        users = [
            ("admin", RoleName.admin),
            ("dept_admin", RoleName.department_admin),
            ("user", RoleName.user),
            ("finance", RoleName.finance),
        ]

        for username, role_name in users:
            existing = await session.scalar(
                select(User).where(User.username == username)
            )
            if existing is not None:
                continue

            user = User(
                username=username,
                email=f"{username}@example.com",
                full_name=username.title(),
                password_hash=hash_password("ChangeMe123!"),
                org_id=org.id,
                is_active=True,
            )
            session.add(user)
            await session.flush()

            session.add(UserRole(user_id=user.id, role_id=roles_by_name[role_name].id))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
