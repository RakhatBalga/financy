"""Application entrypoint.

Runs in one of two modes depending on configuration:

* **Webhook** (``WEBHOOK_URL`` set) — a FastAPI app receives Telegram updates
  behind Nginx. Suitable for production.
* **Long polling** (``WEBHOOK_URL`` empty) — no public URL needed. Suitable
  for local development.

The APScheduler background jobs run in the same process in both modes.
"""

from __future__ import annotations

import asyncio
import contextlib

import structlog
import uvicorn
from aiogram import Bot
from aiogram.types import BotCommand, Update
from fastapi import FastAPI, Request, Response

from app.bot.dispatcher import create_bot, create_dispatcher
from app.core.config import settings
from app.core.logging import configure_logging
from app.scheduler.scheduler import create_scheduler

log = structlog.get_logger(__name__)

_BOT_COMMANDS = [
    BotCommand(command="start", description="Бастау / көмек"),
    BotCommand(command="today", description="Бүгінгі шығындар"),
    BotCommand(command="week", description="Апталық шығындар"),
    BotCommand(command="month", description="Айлық шығындар"),
    BotCommand(command="incomes", description="Айлық кіріс пен баланс"),
    BotCommand(command="chart", description="Айлық диаграмма"),
    BotCommand(command="recent", description="Шығындарды өзгерту/жою"),
    BotCommand(command="setbudget", description="Санат бойынша лимит"),
    BotCommand(command="income", description="Кірісті көрсету"),
    BotCommand(command="rule", description="50/30/20 ережесі"),
    BotCommand(command="advice", description="Айдың ЖИ талдауы"),
    BotCommand(command="profile", description="Қаржылық профиль"),
    BotCommand(command="benchmark", description="ҚР орташасымен салыстыру"),
    BotCommand(command="subscriptions", description="Жазылымдарды табу"),
    BotCommand(command="reset", description="Барлық шығын мен бюджетті жою"),
]


async def _set_commands(bot: Bot) -> None:
    """Publish the command menu shown in Telegram's UI."""
    await bot.set_my_commands(_BOT_COMMANDS)


async def _run_polling() -> None:
    """Local development: delete any webhook and long-poll for updates."""
    bot = create_bot()
    dp = create_dispatcher()
    scheduler = create_scheduler(bot)

    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await _set_commands(bot)
    log.info("starting_polling")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


def _build_webhook_app() -> FastAPI:
    """Production: FastAPI app that forwards updates to the Dispatcher."""
    bot = create_bot()
    dp = create_dispatcher()
    scheduler = create_scheduler(bot)

    app = FastAPI(title="Finance Bot")

    @app.on_event("startup")
    async def _on_startup() -> None:
        scheduler.start()
        webhook_url = settings.webhook_url.rstrip("/") + settings.webhook_path
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret or None,
            drop_pending_updates=True,
        )
        await _set_commands(bot)
        log.info("webhook_set", url=webhook_url)

    @app.on_event("shutdown")
    async def _on_shutdown() -> None:
        scheduler.shutdown(wait=False)
        await bot.delete_webhook()
        await bot.session.close()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(settings.webhook_path)
    async def telegram_webhook(request: Request) -> Response:
        if settings.webhook_secret:
            token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if token != settings.webhook_secret:
                return Response(status_code=401)
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return Response(status_code=200)

    return app


def main() -> None:
    configure_logging(settings.log_level)
    if settings.use_webhook:
        uvicorn.run(
            _build_webhook_app(),
            host=settings.webapp_host,
            port=settings.webapp_port,
        )
    else:
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(_run_polling())


if __name__ == "__main__":
    main()
