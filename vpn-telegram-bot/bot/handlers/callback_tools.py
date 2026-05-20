"""Утилиты для callback: безопасное редактирование сообщения."""

from __future__ import annotations

import logging
from typing import Optional, Union

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


async def edit_callback_message(
    callback: CallbackQuery,
    text: str,
    *,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[Union[str, ParseMode]] = None,
) -> None:
    """Редактирует сообщение с кнопкой; при недоступном сообщении шлёт новое в чат."""
    msg = callback.message
    if isinstance(msg, Message) and msg.chat is not None:
        try:
            await msg.edit_text(
                text,
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
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except TelegramBadRequest as exc:
            logger.warning("send_message fallback failed: %s", exc)
