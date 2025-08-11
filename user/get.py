"""Get current authorized user module."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import SecurityScopes
import jwt
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.token_schema import TokenData, oauth2_scheme
from app.core.config import settings
from app.db import User
from app.db.db_manager import get_db


async def get_user(db: AsyncSession, username: str | None) -> User | None:
    """
    Retrieve a user from the database by username.

    Args:
        db: Async database session.
        username: Username to look up.

    Returns:
        User instance if found, otherwise None.

    Raises:
        HTTPException 401 if username is None.
        HTTPException 500 on database errors.
    """
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalars().first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        ) from e
    else:
        return user


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """
    Decode JWT token, validate user, and check required scopes.

    Args:
        security_scopes: Required scopes for the endpoint.
        token: JWT bearer token.
        db: Async database session.

    Returns:
        Authenticated User if valid and authorized.

    Raises:
        HTTPException 401 if credentials invalid or insufficient permissions.
    """
    authenticate_value = (
        f'Bearer scope="{security_scopes.scope_str}"'
        if security_scopes.scopes
        else "Bearer"
    )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_scopes = payload.get("scopes", "")
        token_data = TokenData(scopes=token_scopes, username=username)

    except (jwt.InvalidTokenError, ValidationError) as err:
        raise credentials_exception from err

    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["admin user"])],
) -> User | None:
    """
    Ensure the current user is active (not disabled).

    Args:
        current_user: Injected authenticated user.

    Returns:
        Active User instance.

    Raises:
        HTTPException 400 if user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
