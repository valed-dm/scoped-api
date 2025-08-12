from typing import AsyncGenerator, cast, Any
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
async def async_client(app_with_db: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Function-scoped async client bound to the overridden DB."""
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# --- Database Fixtures (Function-Scoped for Maximum Stability) ---


@pytest.fixture(scope="session")
def docker_client() -> Generator[docker.client.DockerClient, None, None]:
    """Session-scoped Docker client for performance."""
    client = docker.from_env()
    yield client
    client.close()  # type: ignore


@pytest.fixture(scope="function")
def postgres_container(
    docker_client: docker.client.DockerClient,
) -> Generator[PostgresContainer, None, None]:
    """Fresh Postgres container per test for full isolation."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncEngine, None]:
    """Creates a new async engine & schema for each test."""
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
    """Primary SQLAlchemy session for a test."""
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def raw_db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Independent session to verify committed state."""
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


# --- Dependency Overrides ---


@pytest.fixture
def override_get_db(
    db_session: AsyncSession,
) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def app_with_db(
    app: FastAPI,
    override_get_db: Callable[[], AsyncGenerator[AsyncSession, None]],
) -> Generator[FastAPI, None, None]:
    """FastAPI app with DB dependency overridden."""
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


# --- Test-specific Fixtures ---


@pytest.fixture
async def test_user(db_session: AsyncSession) -> tuple[str, str]:
    """Creates a default test user."""
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


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> tuple[str, str]:
    """Creates an admin user."""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        scopes=["admin"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.username, "AdminPass123!"


@pytest.fixture
async def auth_token(async_client: AsyncClient, test_user: tuple[str, str]) -> str:
    """Logs in as the test user and returns a Bearer token."""
    username, password = test_user
    resp = await async_client.post(
        "/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    json_data = cast(dict[str, Any], resp.json())
    return cast(str, json_data["access_token"])


@pytest.fixture
async def admin_token(async_client: AsyncClient, admin_user: tuple[str, str]) -> str:
    """Logs in as admin and returns a Bearer token."""
    username, password = admin_user
    resp = await async_client.post(
        "/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return cast(str, resp.json()["access_token"])
