"""Main entrypoint for the bot application."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import structlog
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import settings
from app.infra.db import init_db


def setup_logging() -> None:
    """Configure structured logging with structlog."""
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            (
                structlog.processors.JSONRenderer()
                if settings.log_level != "DEBUG"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(settings.log_level),
    )

    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown."""
    logger = structlog.get_logger()
    logger.info("Application starting up", timezone=settings.app_timezone)

    # Initialize database
    db_manager = init_db(settings.database_url)
    logger.info("Database connection initialized")

    # Run migrations
    try:
        await db_manager.run_migrations()
    except Exception as e:
        logger.error("Failed to run migrations", error=str(e))
        raise

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # TODO: Register middlewares
    # from app.bot.middlewares import AccessMiddleware
    # dp.update.middleware(AccessMiddleware())

    # TODO: Register routers
    # from app.bot.router import router as bot_router
    # dp.include_router(bot_router)

    # Store bot and dispatcher in app state
    app.state.bot = bot
    app.state.dp = dp
    app.state.db_manager = db_manager

    # Start bot polling in background
    polling_task = asyncio.create_task(start_bot_polling(bot, dp))
    logger.info("Bot polling started in background")

    yield

    # Shutdown
    logger.info("Application shutting down")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass

    await bot.session.close()
    await db_manager.close()
    logger.info("Application shutdown complete")


async def start_bot_polling(bot: Bot, dp: Dispatcher) -> None:
    """Start bot long polling."""
    logger = structlog.get_logger()
    try:
        await dp.start_polling(bot, handle_signals=False)
    except asyncio.CancelledError:
        logger.info("Bot polling cancelled")
    except Exception as e:
        logger.error("Bot polling error", error=str(e), exc_info=True)
        raise


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Telegram Yandex.Direct Bot",
        description="Single-tenant bot for Yandex.Direct statistics and budgets monitoring",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Mount health check router
    app.include_router(health_router)

    return app


def main() -> None:
    """Main entry point."""
    setup_logging()
    logger = structlog.get_logger()

    logger.info(
        "Starting Telegram Yandex.Direct Bot",
        version="0.1.0",
        timezone=settings.app_timezone,
        access_mode=settings.access_mode.value,
        owner_id=settings.owner_tg_id,
    )

    app = create_app()

    # Run FastAPI with uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,  # We use our own logging configuration
    )


if __name__ == "__main__":
    main()
