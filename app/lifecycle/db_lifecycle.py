"""
Database lifecycle management.

Provides static methods to initialize and shut down the database connection
via the application's database manager.
"""

from app.core.logging import log
from app.db.db_manager import db_manager


class DatabaseLifecycle:
    """Handles database initialization and shutdown sequences."""

    @staticmethod
    async def initialize() -> None:
        """Initialize the database manager connection."""
        try:
            log.info("Initializing database connection...")
            await db_manager.initialize()
            log.info("Database manager initialized successfully.")
        except Exception as e:
            log.critical(
                "FATAL: Database initialization failed during startup: {}",
                e,
                exc_info=True,
            )
            raise RuntimeError(f"Database initialization failed: {e}") from e

    @staticmethod
    async def shutdown() -> None:
        """Shut down the database manager connection."""
        try:
            log.info("Shutting down database manager...")
            await db_manager.shutdown()
            log.info("Database manager shutdown complete.")
        except Exception as e:
            log.error(
                "Error during database shutdown: {}",
                e,
                exc_info=True,
            )
