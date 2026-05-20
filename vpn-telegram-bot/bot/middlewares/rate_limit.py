"""Rate-limit middleware: не более MAX_REQUESTS запросов за WINDOW_SECONDS секунд."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


MAX_REQUESTS = 8        # максимум действий
WINDOW_SECONDS = 10     # за это количество секунд

# user_id -> list of timestamps
_HISTORY: Dict[int, list] = {}
_LOCK = asyncio.Lock()


def _cleanup(now: float, history: list) -> list:
    cutoff = now - WINDOW_SECONDS
    return [t for t in history if t > cutoff]


class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            if user:
                user_id = user.id

        if user_id is not None:
            async with _LOCK:
                now = time.monotonic()
                history = _cleanup(now, _HISTORY.get(user_id, []))
                if len(history) >= MAX_REQUESTS:
                    # Молча блокируем без ошибки, только для callback_query — даём фидбек
                    if isinstance(event, CallbackQuery):
                        await event.answer("⏳ Не так быстро!", show_alert=False)
                    return
                history.append(now)
                _HISTORY[user_id] = history

        return await handler(event, data)
