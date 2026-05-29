from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.enums import ApprovalStatus, RoleName
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.schemas.auth import RegisterRequest
from app.services.auth_service import (
    list_pending_approvals,
    register_user,
    update_registration_approval,
)


@pytest.mark.asyncio
async def test_register_finance_user_is_active(async_session):
    org = Organization(name="Finance Org")
    role = Role(name=RoleName.finance, description="finance")
    async_session.add_all([org, role])
    await async_session.flush()

    user = await register_user(
        async_session,
        RegisterRequest(
            username="finance_new",
            password="ChangeMe123!",
            email="finance_new@example.com",
            full_name="Finance New",
            role=RoleName.finance,
            org_id=org.id,
        ),
    )

    assert user.is_active is True
    assert user.approval_status == ApprovalStatus.approved
    assert [role.name for role in user.roles] == [RoleName.finance]


@pytest.mark.asyncio
async def test_register_department_user_requires_approval(async_session):
    org = Organization(name="Department Org")
    role = Role(name=RoleName.user, description="user")
    async_session.add_all([org, role])
    await async_session.flush()

    user = await register_user(
        async_session,
        RegisterRequest(
            username="pending_user",
            password="ChangeMe123!",
            email=None,
            full_name=None,
            role=RoleName.user,
            org_id=org.id,
        ),
    )

    persisted = await async_session.scalar(select(User).where(User.id == user.id))
    assert persisted is not None
    assert persisted.is_active is False
    assert persisted.approval_status == ApprovalStatus.pending


async def _create_user_with_role(async_session, username, org_id, role):
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed",
        org_id=org_id,
        is_active=True,
        approval_status=ApprovalStatus.approved,
    )
    async_session.add(user)
    await async_session.flush()
    async_session.add(UserRole(user_id=user.id, role_id=role.id))
    await async_session.commit()
    return await async_session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )


@pytest.mark.asyncio
async def test_admin_can_approve_department_admin(async_session):
    org = Organization(name="Approval Org")
    admin_role = Role(name=RoleName.admin, description="admin")
    dept_role = Role(name=RoleName.department_admin, description="department_admin")
    async_session.add_all([org, admin_role, dept_role])
    await async_session.flush()

    admin = await _create_user_with_role(
        async_session, "review_admin", org.id, admin_role
    )
    pending = await register_user(
        async_session,
        RegisterRequest(
            username="pending_dept_admin",
            password="ChangeMe123!",
            email=None,
            full_name=None,
            role=RoleName.department_admin,
            org_id=org.id,
        ),
    )

    approvals = await list_pending_approvals(async_session, admin)
    assert [user.id for user in approvals] == [pending.id]

    approved = await update_registration_approval(
        async_session, admin, pending.id, approved=True
    )
    assert approved.is_active is True
    assert approved.approval_status == ApprovalStatus.approved
    assert approved.approved_by == admin.id


@pytest.mark.asyncio
async def test_department_admin_can_approve_same_org_user(async_session):
    org = Organization(name="Same Org")
    other_org = Organization(name="Other Org")
    dept_role = Role(name=RoleName.department_admin, description="department_admin")
    user_role = Role(name=RoleName.user, description="user")
    async_session.add_all([org, other_org, dept_role, user_role])
    await async_session.flush()

    dept_admin = await _create_user_with_role(
        async_session, "same_org_admin", org.id, dept_role
    )
    same_org_user = await register_user(
        async_session,
        RegisterRequest(
            username="same_org_pending",
            password="ChangeMe123!",
            email=None,
            full_name=None,
            role=RoleName.user,
            org_id=org.id,
        ),
    )
    await register_user(
        async_session,
        RegisterRequest(
            username="other_org_pending",
            password="ChangeMe123!",
            email=None,
            full_name=None,
            role=RoleName.user,
            org_id=other_org.id,
        ),
    )

    approvals = await list_pending_approvals(async_session, dept_admin)
    assert [user.id for user in approvals] == [same_org_user.id]
