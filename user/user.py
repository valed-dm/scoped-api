from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    """
    Represents a user with basic information.

    Attributes:
        username (str): Unique login name.
        email (EmailStr | None): Optional email address.
        full_name (str | None): Optional full name.
        disabled (bool): Whether the user is disabled (default False).
        scopes (str): Space-separated user permissions.
    """

    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    disabled: bool = False
    scopes: str


class UserCreate(User):
    """
    User creation schema extending User with a password field.

    Attributes:
        password (str): Password required during creation.
    """

    password: str


class UserOut(User):
    """
    User output schema including database ID.

    Attributes:
        id (int): Unique database identifier.
    """

    id: int
    model_config = ConfigDict()


class UserBaseUpdate(BaseModel):
    """Schema for partial user updates, used by superusers."""

    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None

    Config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class UserFullUpdate(UserBaseUpdate):
    disabled: bool | None = None
    scopes: str | None = None
