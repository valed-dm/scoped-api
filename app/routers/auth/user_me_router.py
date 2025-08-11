from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User as DBUser
from app.db.db_manager import get_db
from user.get import get_current_active_user
from user.user import User
from user.user import UserBaseUpdate


user_me_router = APIRouter()


@user_me_router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[
        DBUser, Security(get_current_active_user, scopes=["admin user"])
    ],
) -> User:
    """
    Retrieve the profile of the current authenticated user.

    Args:
        current_user (DBUser): Authenticated user, injected via Security dependency.

    Returns:
        User: Pydantic user model with profile data.
    """
    return User.model_validate(current_user)


@user_me_router.put("/users/me/update/", response_model=User, status_code=200)
async def update_own_user(
    user_update: UserBaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        DBUser, Security(get_current_active_user, scopes=["admin user"])
    ],
) -> User:
    """
    Allow the current user to update their own profile fields.

    Args:
        user_update (UserBaseUpdate): Partial user data for update.
        db (AsyncSession): Async database session.
        current_user (DBUser): Authenticated user.

    Returns:
        User: Updated user data as Pydantic model.

    Raises:
        HTTPException: 404 if user not found in the database.
    """
    async with db.begin():
        stmt = select(DBUser).where(DBUser.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        db.add(user)

    return User.model_validate(user)
