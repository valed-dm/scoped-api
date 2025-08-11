"""Users table model."""

from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db import Base
from app.db import TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for database interaction.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The unique username associated with the user.
        email (str | None): The user's email address. Default to None.
        hashed_password (str): The user's hashed password. Required.
        full_name (str | None): The user's full name. Default to None.
        disabled (bool): Whether the user is disabled or not. Default to False.
        scopes (str): A space-separated string of the user's permissions.
        Default to empty string.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        default=None,
        nullable=True,
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, default=None, nullable=True)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[str] = mapped_column(String, default="")
