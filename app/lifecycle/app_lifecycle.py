"""
Application lifecycle management.

Handles startup and shutdown events including:
- Sentry error monitoring initialization
- aiohttp session management
- Database lifecycle hooks
"""

from typing import Optional

import aiohttp
from fastapi import FastAPI
import sentry_sdk

from app.core.config import settings
from app.core.logging import log
from app.lifecycle.db_lifecycle import DatabaseLifecycle


class AppLifecycle:
    """Orchestrates application startup and shutdown procedures."""

    app: FastAPI
    aiohttp_session: Optional[aiohttp.ClientSession]

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.aiohttp_session = None

    async def on_startup(self) -> None:
        """Run startup sequence for the application."""
        log.info("Starting up application...")

        sentry_sdk.init(
            str(settings.GLITCHTIP_DSN) if settings.GLITCHTIP_DSN else None,
            traces_sample_rate=1.0,
        )

        await self._initialize_aiohttp()
        await DatabaseLifecycle.initialize()

        log.info("Application startup complete. Ready to serve requests.")

    async def on_shutdown(self) -> None:
        """Run shutdown sequence for the application."""
        log.info("Shutting down application...")

        await self._close_aiohttp()
        await DatabaseLifecycle.shutdown()

        log.info("Application shutdown complete.")

    async def _initialize_aiohttp(self) -> None:
        """Create and attach a shared aiohttp client session."""
        self.aiohttp_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.AIOHTTP_TIMEOUT_SECONDS)
        )
        self.app.state.aiohttp_session = self.aiohttp_session
        log.info("Aiohttp session initialized.")

    async def _close_aiohttp(self) -> None:
        """Close the shared aiohttp client session if it exists."""
        try:
            if self.aiohttp_session and not self.aiohttp_session.closed:
                await self.aiohttp_session.close()
                log.info("Aiohttp session closed.")
        except Exception as e:
            log.exception(f"Error closing aiohttp session: {e}")
