# app/core/db_config.py
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database connection settings and connection pool configuration.

    Loads PostgreSQL database parameters and connection pool
    settings from environment variables.
    """

    POSTGRES_HOST: Annotated[str, Field(validation_alias="POSTGRES_HOST")]
    POSTGRES_USER: Annotated[str, Field(validation_alias="POSTGRES_USER")]
    POSTGRES_PASSWORD: Annotated[str, Field(validation_alias="POSTGRES_PASSWORD")]
    POSTGRES_PORT: Annotated[str, Field(validation_alias="POSTGRES_PORT")]
    POSTGRES_DB: Annotated[str, Field(validation_alias="POSTGRES_DB")]
    POSTGRES_TEST_DB_NAME: Annotated[
        str, Field(validation_alias="POSTGRES_TEST_DB_NAME")
    ]

    @property
    def database_url(self) -> str:
        """
        Construct the PostgreSQL database connection URL.

        Returns:
            str: PostgreSQL connection URL formatted for asyncpg.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    DB_POOL_SIZE: int = Field(
        default=10, description="Number of permanent connections in the pool.", gt=0
    )
    DB_MAX_OVERFLOW: int = Field(
        default=20,
        description="Temporary connections allowed beyond pool size.",
        ge=0,
    )
    DB_POOL_TIMEOUT: float = Field(
        default=30.0,
        description="Seconds to wait for a connection from the pool.",
        gt=0,
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        description="Recycle time (seconds) to prevent stale connections.",
        gt=0,
    )
    DB_CONNECT_TIMEOUT: int = Field(
        default=10, description="Initial database connection timeout in seconds.", gt=0
    )
    DB_USE_TWOPHASE: bool = Field(
        default=False,
        description="Enable two-phase commits for distributed transactions.",
    )
    DB_STATEMENT_TIMEOUT: int = Field(
        default=30, description="Query timeout in seconds before cancellation.", gt=0
    )
    DB_IDLE_TIMEOUT: int = Field(
        default=300, description="Idle-in-transaction timeout in seconds.", gt=0
    )
    DB_LOCK_TIMEOUT: int = Field(
        default=10, description="Lock acquisition timeout in seconds.", gt=0
    )
