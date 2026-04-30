from __future__ import annotations

from telegram.constants import ParseMode
from telegram.ext import Application, Defaults

from subway_bot.catalogs import CatalogRepository
from subway_bot.config import Settings
from subway_bot.constants import BOT_COMMANDS
from subway_bot.handlers import BotHandlers
from subway_bot.logging_config import configure_logging


async def _post_init(application: Application) -> None:
    await application.bot.set_my_commands(BOT_COMMANDS)


def build_application(settings: Settings) -> Application:
    catalogs = CatalogRepository(
        cache_dir=settings.data_dir / "catalog_cache",
        ttl_seconds=settings.catalog_cache_ttl_seconds,
        timeout_seconds=settings.request_timeout_seconds,
    )
    handlers = BotHandlers(settings=settings, catalogs=catalogs)

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .post_init(_post_init)
        .build()
    )
    handlers.register(application)
    return application


def main() -> None:
    settings = Settings.from_env()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(settings.log_level)

    application = build_application(settings)

    if settings.bot_mode == "webhook":
        application.run_webhook(
            listen=settings.webhook_listen,
            port=settings.webhook_port,
            url_path=settings.webhook_path,
            webhook_url=settings.webhook_endpoint,
            drop_pending_updates=settings.drop_pending_updates,
            secret_token=settings.webhook_secret,
        )
        return

    application.run_polling(drop_pending_updates=settings.drop_pending_updates)
