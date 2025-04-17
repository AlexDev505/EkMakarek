from __future__ import annotations

import time
import typing as ty
from functools import wraps

from .bot import bot


if ty.TYPE_CHECKING:
    from telebot.types import Message


def rate_limit(limit: int):
    """
    Decorator for command handlers.
    Implements command rate-limit.
    :param limit: Seconds.
    """

    def _decorator(func):
        # {<sender_id>: (<last_call_time>, <exceeded_count>)}
        last_calls: dict[int, tuple[int, int]] = {}

        @wraps(func)
        def _wrapper(message: Message, *args, **kwargs):
            last_call, exceeded_count = last_calls.get(message.chat.id, (0, 0))
            if (delta := (time.time() - last_call)) < limit:
                last_calls[message.chat.id] = (last_call, exceeded_count + 1)
                if exceeded_count == 0:
                    return bot.reply_to(
                        message,
                        "The team is temporarily locked, "
                        f"try after {round(limit - delta, 2)} seconds",
                    )
                return
            func(message, *args, **kwargs)
            last_calls[message.chat.id] = (int(time.time()), 0)

        return _wrapper

    return _decorator
