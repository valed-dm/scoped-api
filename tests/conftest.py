from typing import AsyncGenerator
from typing import Callable
from typing import Generator

import docker
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from app.auth.auth import get_password_hash
from app.core.config import settings
from app.db import Base
from app.db import User
from app.db.db_manager import get_db
from app.main import app as main_app


# --- App Fixtures ---


@pytest.fixture
def app() -> FastAPI:
    return main_app


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Function-scoped async client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# --- Database Fixtures (Function-Scoped for Maximum Stability) ---


@pytest.fixture(scope="session")
def docker_client() -> Generator[docker.client.DockerClient, None, None]:
    """Session-scoped Docker client for performance."""
    client = docker.from_env()
    yield client
    client.close()  # type: ignore[no-untyped-call]


@pytest.fixture(scope="function")
def postgres_container(
    docker_client: docker.client.DockerClient,
) -> Generator[PostgresContainer, None, None]:
    """
    Function-scoped Postgres container. Starts a fresh DB for each test.
    This is the key to ensuring complete isolation and clean teardown.
    """
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncEngine, None]:
    """
    Creates a new engine for each test function and creates the schema.
    """
    raw_url = postgres_container.get_connection_url()
    db_url = raw_url.replace("+psycopg2", "").replace(
        "postgresql", "postgresql+asyncpg", 1
    )

    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides the primary SQLAlchemy session for a test.
    Operations are committed directly to the test-specific database.
    """
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def raw_db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a second, independent session to verify the committed state
    of the database, bypassing the primary test session's state.
    """
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


# --- Dependency Overrides ---


@pytest.fixture
def override_get_db(
    db_session: AsyncSession,
) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    """
    Pytest fixture that returns a dependency-override function for get_db.

    This pattern is used to replace the production `get_db` dependency in
    FastAPI with a function that yields a single, test-specific database
    session, ensuring test isolation.

    Returns:
        A callable function that, when used as a dependency override, provides
        an async generator yielding a test database session.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def app_with_db(
    app: FastAPI,
    override_get_db: Callable[[], AsyncGenerator[AsyncSession, None]],
) -> Generator[FastAPI, None, None]:
    """
    Pytest fixture that provides a FastAPI app instance with the database
    dependency overridden to use a test-specific session.

    This is the primary fixture tests should use when they need to make
    API calls to the application that interact with the database.

    It ensures that each test run gets a clean, isolated database session
    and cleans up the override after the test completes.

    Yields:
        The FastAPI app instance, configured for isolated DB testing.
    """
    app.dependency_overrides[get_db] = override_get_db

    yield app

    app.dependency_overrides.clear()


# --- Test-specific Fixtures ---


@pytest.fixture
async def test_user(db_session: AsyncSession) -> tuple[str, str]:
    user = User(
        username=settings.TEST_USERNAME,
        email=settings.TEST_EMAIL,
        hashed_password=get_password_hash(settings.TEST_PASSWORD),
        full_name=settings.TEST_FULL_NAME,
        scopes=settings.TEST_SCOPE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.username, settings.TEST_PASSWORD
