"""Удаление «шумных» сообщений пользователя (команда /start и нажатия reply-меню)."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any, Awaitable, Callable, FrozenSet

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, TelegramObject

from bot.handlers.i18n import all_locale_values
from core.config import Config

logger = logging.getLogger(__name__)

_MENU_TEXT_KEYS = (
    "btn_install",
    "btn_profile",
    "btn_tariffs",
    "btn_invite",
    "btn_faq",
    "btn_switch_en",
    "btn_switch_ru",
)


@lru_cache(maxsize=1)
def _reply_menu_texts() -> FrozenSet[str]:
    texts: set[str] = set()
    for key in _MENU_TEXT_KEYS:
        texts.update(all_locale_values(key))
    return frozenset(texts)


def _should_delete_user_message(message: Message) -> bool:
    if not message.text or message.chat is None:
        return False
    if message.chat.type != "private":
        return False
    raw = message.text.strip()
    if raw.startswith("/start"):
        return True
    return raw in _reply_menu_texts()


async def _delete_message_after(
    bot: Any,
    chat_id: int,
    message_id: int,
    delay_sec: float,
) -> None:
    try:
        await asyncio.sleep(delay_sec)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest as exc:
        logger.debug("delete_message skipped: %s", exc)
    except Exception:
        logger.debug("delete_message failed", exc_info=True)


class TidyChatMiddleware(BaseMiddleware):
    """После успешной обработки планирует удаление триггер-сообщения пользователя."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        result = await handler(event, data)
        if not isinstance(event, Message):
            return result
        cfg = data.get("config")
        if not isinstance(cfg, Config):
            return result
        delay = cfg.delete_user_menu_message_after_sec
        if delay <= 1:
            return result
        if not _should_delete_user_message(event):
            return result
        asyncio.create_task(
            _delete_message_after(
                event.bot,
                event.chat.id,
                event.message_id,
                float(delay),
            )
        )
        return result
