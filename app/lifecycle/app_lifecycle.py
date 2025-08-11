"""
Application lifecycle management.

Handles startup and shutdown sequences including initialization
of monitoring, HTTP sessions, and database connections.
"""

from typing import Optional

import aiohttp
from fastapi import FastAPI
import sentry_sdk

from app.core.config import settings
from app.core.logging import log
from app.lifecycle.db_lifecycle import DatabaseLifecycle


class AppLifecycle:
    """Manages the startup and shutdown of the FastAPI application."""

    app: FastAPI
    aiohttp_session: Optional[aiohttp.ClientSession]

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.aiohttp_session = None

    async def on_startup(self) -> None:
        """Orchestrates the application's startup sequence."""
        log.info("Starting {} app...", settings.APP_NAME)

        sentry_sdk.init(str(settings.GLITCHTIP_DSN), traces_sample_rate=1.0)

        await self._initialize_aiohttp()
        await DatabaseLifecycle.initialize()

        log.info("{} startup complete. Ready to serve requests.", settings.APP_NAME)

    async def on_shutdown(self) -> None:
        """Orchestrates the application's shutdown sequence."""
        log.info("Shutting down {} app...", settings.APP_NAME)

        await self._close_aiohttp()
        await DatabaseLifecycle.shutdown()

        log.info("{} shutdown complete.", settings.APP_NAME)

    async def _initialize_aiohttp(self) -> None:
        """Initializes the shared aiohttp client session."""
        self.aiohttp_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.AIOHTTP_TIMEOUT_SECONDS)
        )
        self.app.state.aiohttp_session = self.aiohttp_session
        log.info("Aiohttp session initialized.")

    async def _close_aiohttp(self) -> None:
        """Gracefully closes the shared aiohttp client session."""
        try:
            if self.aiohttp_session and not self.aiohttp_session.closed:
                await self.aiohttp_session.close()
                log.info("Aiohttp session closed.")
        except Exception as e:
            log.error("Error closing aiohttp session: {}", e, exc_info=True)
