"""Утилиты для callback: безопасное редактирование сообщения."""

from __future__ import annotations

import logging
from typing import Optional, Union

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


def _sanitize(text: str) -> str:
    """Удаляет одиночные суррогатные символы, которые ломают UTF-8 кодирование в aiohttp.

    Суррогаты (U+D800–U+DFFF) могут появляться, если имя сервера или эмодзи флага
    (например 🇩🇪) хранится в БД или конфиге с некорректной кодировкой.
    encode('utf-8', 'surrogatepass') → decode('utf-8', 'ignore') безопасно
    удаляет все bitty-символы, не трогая нормальные Unicode-эмодзи.
    """
    return text.encode("utf-8", "surrogatepass").decode("utf-8", "ignore")


async def edit_callback_message(
    callback: CallbackQuery,
    text: str,
    *,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[Union[str, ParseMode]] = ParseMode.HTML,
) -> None:
    """Редактирует сообщение с кнопкой; при недоступном сообщении шлёт новое в чат."""
    safe_text = _sanitize(text)
    msg = callback.message
    if isinstance(msg, Message) and msg.chat is not None:
        try:
            await msg.edit_text(
                safe_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except TelegramBadRequest as exc:
            err = (getattr(exc, "message", None) or str(exc)).lower()
            if "message is not modified" in err:
                return
            logger.info("edit_text failed (%s), sending new message to user", exc)

    if callback.from_user is not None:
        try:
            await callback.bot.send_message(
                callback.from_user.id,
                safe_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except TelegramBadRequest as exc:
            logger.warning("send_message fallback failed: %s", exc)
