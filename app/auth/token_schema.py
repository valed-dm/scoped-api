from __future__ import annotations

from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    """
    Access token response model.

    Attributes:
        access_token (str): JWT issued after authentication.
        token_type (str): Token type, typically "bearer".
    """

    access_token: str
    token_type: str = settings.TOKEN_TYPE


class TokenData(BaseModel):
    """
    Payload data contained within the JWT.

    Attributes:
        username (str): Username of the authenticated user.
        scopes (str): Space-separated OAuth 2.0 scopes.
    """

    username: str
    scopes: str
