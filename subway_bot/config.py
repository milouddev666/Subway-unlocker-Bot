from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from subway_bot.constants import DEFAULT_CATALOG_PAGE_SIZE


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int_set(raw_value: str | None) -> frozenset[int]:
    if not raw_value:
        return frozenset()
    return frozenset(int(part.strip()) for part in raw_value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    bot_mode: str
    webhook_url: str | None
    webhook_secret: str
    webhook_listen: str
    webhook_port: int
    drop_pending_updates: bool
    data_dir: Path
    catalog_cache_ttl_seconds: int
    request_timeout_seconds: float
    log_level: str
    allowed_user_ids: frozenset[int]
    catalog_page_size: int

    @property
    def webhook_path(self) -> str:
        return self.webhook_secret

    @property
    def webhook_endpoint(self) -> str:
        if not self.webhook_url:
            raise ValueError("WEBHOOK_URL must be set when BOT_MODE=webhook.")
        return f"{self.webhook_url.rstrip('/')}/{self.webhook_path}"

    @classmethod
    def from_env(cls) -> Settings:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required.")

        bot_mode = os.getenv("BOT_MODE", "polling").strip().lower()
        if bot_mode not in {"polling", "webhook"}:
            raise ValueError("BOT_MODE must be either 'polling' or 'webhook'.")

        webhook_secret = os.getenv("WEBHOOK_SECRET", "").strip()
        if not webhook_secret:
            webhook_secret = hashlib.sha256(token.encode("utf-8")).hexdigest()[:48]

        settings = cls(
            telegram_bot_token=token,
            bot_mode=bot_mode,
            webhook_url=os.getenv("WEBHOOK_URL", "").strip() or None,
            webhook_secret=webhook_secret,
            webhook_listen=os.getenv("WEBHOOK_LISTEN", "0.0.0.0").strip(),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8080")),
            drop_pending_updates=_parse_bool(os.getenv("DROP_PENDING_UPDATES"), default=True),
            data_dir=Path(os.getenv("DATA_DIR", "data")).resolve(),
            catalog_cache_ttl_seconds=int(os.getenv("CATALOG_CACHE_TTL_SECONDS", "3600")),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            allowed_user_ids=_parse_int_set(os.getenv("ALLOWED_USER_IDS")),
            catalog_page_size=int(
                os.getenv("CATALOG_PAGE_SIZE", str(DEFAULT_CATALOG_PAGE_SIZE))
            ),
        )

        if settings.bot_mode == "webhook" and not settings.webhook_url:
            raise ValueError("WEBHOOK_URL is required when BOT_MODE=webhook.")

        if settings.webhook_port <= 0:
            raise ValueError("WEBHOOK_PORT must be a positive integer.")

        if settings.catalog_cache_ttl_seconds <= 0:
            raise ValueError("CATALOG_CACHE_TTL_SECONDS must be a positive integer.")

        if settings.request_timeout_seconds <= 0:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be a positive number.")

        if settings.catalog_page_size <= 0:
            raise ValueError("CATALOG_PAGE_SIZE must be a positive integer.")

        return settings
