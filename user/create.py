"""Create a new user module."""

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_password_hash
from app.core.logging import log
from app.db import User as DBUser
from user.user import UserCreate
from user.user import UserOut


async def create_user(db: AsyncSession, user: UserCreate) -> UserOut:
    """
    Create a new user in the database atomically.

    This function relies on the database's UNIQUE constraints to ensure data
    integrity for username and email, providing safe race condition handling.

    Args:
        db: Async SQLAlchemy session.
        user: UserCreate Pydantic model with input user data.

    Returns:
        UserOut: Pydantic model of the newly created user.

    Raises:
        HTTPException: Raised with 409 status if username or email is already taken,
                       or 500 for other database errors.
    """
    hashed_password = get_password_hash(user.password)

    db_user = DBUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        disabled=user.disabled,
        scopes=user.scopes or "user",
    )

    try:
        async with db.begin():
            db.add(db_user)

        await db.refresh(db_user)

    except IntegrityError as e:
        log.warning(
            "Database IntegrityError on user creation:"
            " {constraint}, username: {username}",
            constraint=str(e.orig),
            username=user.username,
        )
        error_msg = str(e.orig)
        if "users_username_key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists.",
            ) from e
        if "users_email_key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred.",
        ) from e

    return UserOut.model_validate(db_user)
