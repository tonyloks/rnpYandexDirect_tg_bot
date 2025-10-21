"""Configuration module using Pydantic Settings."""

import base64
from enum import Enum
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AccessMode(str, Enum):
    """Access control modes for the bot."""

    OWNER_ONLY = "owner-only"
    ALLOWLIST = "allowlist"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot
    telegram_bot_token: str = Field(
        ...,
        description="Telegram Bot API token from @BotFather",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://bot:bot@localhost:5432/bot",
        description="PostgreSQL connection string",
    )

    # Application
    app_timezone: str = Field(
        default="Europe/Moscow",
        description="Timezone for date calculations (pytz compatible)",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Security & Access Control
    app_kms_key: str = Field(
        ...,
        description="Base64-encoded 32-byte encryption key for token storage",
    )

    owner_tg_id: int = Field(
        ...,
        description="Telegram user ID of the bot owner",
        gt=0,
    )

    # Keep the annotation as Any to avoid the dotenv settings source attempting
    # to JSON-decode the value (which fails for comma-separated lists).
    # The field_validator below will normalize a comma-separated string or
    # a list of ints into a list[int].
    allowed_tg_ids: Any = Field(
        default=[],
        description="Comma-separated list of allowed Telegram user IDs",
    )

    access_mode: AccessMode = Field(
        default=AccessMode.ALLOWLIST,
        description="Access control mode: owner-only or allowlist",
    )

    allow_group_chats: bool = Field(
        default=False,
        description="Allow bot usage in group chats",
    )

    # Yandex.Direct OAuth (optional)
    yandex_client_id: str = Field(
        default="",
        description="Yandex OAuth client ID (optional)",
    )

    yandex_client_secret: str = Field(
        default="",
        description="Yandex OAuth client secret (optional)",
    )

    yandex_redirect_url: str = Field(
        default="",
        description="Yandex OAuth redirect URL (optional)",
    )

    # FastAPI
    api_host: str = Field(
        default="0.0.0.0",
        description="FastAPI host binding",
    )

    api_port: int = Field(
        default=8080,
        description="FastAPI port",
        gt=0,
        lt=65536,
    )

    # Feature Flags
    enable_cache: bool = Field(
        default=False,
        description="Enable caching for Yandex.Direct API responses",
    )

    @field_validator("allowed_tg_ids", mode="before")
    @classmethod
    def parse_allowed_ids(cls, v: Any) -> list[int]:
        """
        Parse and validate allowed Telegram IDs.

        Supported input formats:
        - Comma-separated string: "123,456,789"
        - JSON array string: "[123, 456]"
        - Python list/tuple of ints: [123, 456]

        The validator returns a list[int] or raises ValueError with a clear message
        when the value can't be interpreted as a list of integers.
        """
        # If it's already a list/tuple of ints/strs, coerce to ints
        if isinstance(v, list | tuple):
            try:
                return [int(x) for x in v]
            except Exception as e:
                raise ValueError(f"Invalid ALLOWED_TG_IDS list contents: {e}") from e

        # Empty values -> empty list
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return []

        # If it's a string, accept JSON array or comma-separated integers
        if isinstance(v, str):
            s = v.strip()
            # Try JSON array first
            try:
                import json

                parsed = json.loads(s)
                if isinstance(parsed, list):
                    try:
                        return [int(x) for x in parsed]
                    except Exception as e:
                        raise ValueError(f"Invalid ALLOWED_TG_IDS JSON array contents: {e}") from e
            except Exception:
                # Fallthrough to comma-separated parsing
                pass

            # Validate comma-separated integers (e.g. "1, 2,3")
            import re

            if re.fullmatch(r"\s*\d+(\s*,\s*\d+)*\s*", s):
                return [int(x.strip()) for x in s.split(",") if x.strip()]

            raise ValueError(
                "ALLOWED_TG_IDS must be a comma-separated list of integers, a JSON array, or a list of ints"
            )

        # Other types are invalid
        raise ValueError("ALLOWED_TG_IDS must be a string or a list/tuple of integers")

    @field_validator("app_kms_key")
    @classmethod
    def validate_kms_key(cls, v: str) -> str:
        """Validate that KMS key is base64-encoded and has correct length."""
        if not v or v == "base64:CHANGEME_REPLACE_WITH_REAL_KEY_FROM_GENERATOR":
            raise ValueError(
                "APP_KMS_KEY must be set. Generate with: "
                "python -c \"import base64, os; print('base64:' + base64.b64encode(os.urandom(32)).decode())\""
            )

        # Remove base64: prefix if present
        key_data = v.replace("base64:", "").strip()

        try:
            decoded = base64.b64decode(key_data)
            if len(decoded) != 32:
                raise ValueError(f"KMS key must be 32 bytes, got {len(decoded)}")
        except Exception as e:
            raise ValueError(f"Invalid base64 KMS key: {e}") from e

        return v

    @property
    def kms_key_bytes(self) -> bytes:
        """Get decoded KMS key as bytes."""
        key_data = self.app_kms_key.replace("base64:", "").strip()
        return base64.b64decode(key_data)

    @property
    def is_owner_only_mode(self) -> bool:
        """Check if bot is in owner-only mode."""
        return self.access_mode == AccessMode.OWNER_ONLY

    @property
    def is_allowlist_mode(self) -> bool:
        """Check if bot is in allowlist mode."""
        return self.access_mode == AccessMode.ALLOWLIST

    def is_user_allowed(self, user_id: int) -> bool:
        """
        Check if a user is allowed to use the bot (without DB lookup).

        This only checks static configuration (owner + ALLOWED_TG_IDS env).
        For dynamic allowlist, use the database repository.
        """
        if user_id == self.owner_tg_id:
            return True

        if self.is_owner_only_mode:
            return False

        # In allowlist mode, check static allowed IDs from ENV
        return user_id in self.allowed_tg_ids


# Global settings instance
settings = Settings()
