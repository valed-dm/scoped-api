from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import authenticate_user
from app.auth.auth import create_access_token
from app.auth.token_schema import Token
from app.core.config import settings
from app.core.logging import log
from app.db.db_manager import get_db


user_token_router = APIRouter()


@user_token_router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Authenticate user and return JWT access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Username and password.
        db (AsyncSession): Database session.

    Returns:
        Token: JWT access token with bearer type.

    Raises:
        HTTPException: If authentication fails (401 Unauthorized).
    """
    user = await authenticate_user(db, form_data.username, form_data.password)

    if user is None:
        log.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type=settings.TOKEN_TYPE)
