"""Create a new user module."""

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select, or_
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

    This function first performs a pre-flight check for an existing username or
    email to provide fast, user-friendly error messages. It then relies on the
    database's UNIQUE constraints within a nested transaction to ensure data
    integrity and provide safe race condition handling.

    Args:
        db: The SQLAlchemy async database session (assumed to be in a transaction).
        user: The Pydantic model containing the input data for creating a user.

    Returns:
        A Pydantic UserOut model of the newly created user.

    Raises:
        HTTPException: If the username or email is already taken.
    """
    stmt = select(DBUser).where(
        or_(DBUser.username == user.username, DBUser.email == user.email)
    )
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists.",
            )
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

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
        async with db.begin_nested():
            db.add(db_user)
            await db.flush()
            await db.refresh(db_user)

    except IntegrityError as e:
        log.warning(
            "Database IntegrityError (race condition) on user creation",
            extra={"constraint": str(e.orig), "username": user.username},
        )
        error_msg = str(e.orig)
        if "ix_users_username" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists.",
            ) from e
        if "ix_users_email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred.",
        ) from e

    return UserOut.model_validate(db_user)
