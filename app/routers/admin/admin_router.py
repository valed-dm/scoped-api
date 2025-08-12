from typing import Annotated
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User as DBUser
from app.db.db_manager import get_db
from user.get import get_current_active_user
from user.user import UserFullUpdate


admin_router = APIRouter()


@admin_router.get("/users/", response_model=list[UserFullUpdate])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[DBUser, Security(get_current_active_user, scopes=["admin"])],
    limit: int = 10,
    offset: int = 0,
) -> list[UserFullUpdate]:
    """
    List users with pagination. Admins only.

    Args:
        db: Async DB session.
        _: Admin user via Security dependency.
        limit: Max users returned.
        offset: Users to skip.

    Returns:
        List of UserFullUpdate Pydantic models.
    """
    stmt = select(DBUser).limit(limit).offset(offset)
    result = await db.execute(stmt)
    db_users = result.scalars().all()
    return [UserFullUpdate.model_validate(user) for user in db_users]


@admin_router.patch("/users/{user_id}", response_model=UserFullUpdate)
async def update_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[DBUser, Security(get_current_active_user, scopes=["admin"])],
    user_id: int,
    user_update: UserFullUpdate,
) -> UserFullUpdate:
    """
    Update user details by ID. Admins only.

    Args:
        db: Async DB session.
        _: Admin user via Security dependency.
        user_id: User ID to update.
        user_update: Fields to update.

    Returns:
        Updated UserFullUpdate Pydantic model.

    Raises:
        HTTPException 404 if user not found.
    """
    async with db.begin():
        stmt = select(DBUser).where(DBUser.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found.",
            )

        updated_data = user_update.model_dump(exclude_unset=True)
        for key, value in updated_data.items():
            setattr(user, key, value)

        db.add(user)

    await db.refresh(user)
    return UserFullUpdate.model_validate(user)


@admin_router.get("/status/")
async def read_system_status(
    current_user: Annotated[
        DBUser,
        Security(get_current_active_user, scopes=["admin"]),
    ],
) -> dict[str, Any]:
    """
    Return system status. Admins only.

    Args:
        current_user: Authenticated admin user.

    Returns:
        Status dict with username and admin flag.
    """
    return {"status": "ok", "user": current_user.username, "is_admin": True}
