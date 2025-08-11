from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_manager import get_db
from user.create import create_user
from user.user import UserCreate
from user.user import UserOut


user_register_router = APIRouter()


@user_register_router.post("/register", response_model=UserOut)
async def register_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    """
    Register a new user in the system.

    Creates a new user after validating uniqueness of username and email,
    hashes the password, and persists user data in the database.

    Args:
        user (UserCreate): Input data for the new user.
        db (AsyncSession): Database session.

    Returns:
        UserOut: The created user's information.

    Raises:
        HTTPException: Raised if username or email already exists.
    """
    return await create_user(db, user)
