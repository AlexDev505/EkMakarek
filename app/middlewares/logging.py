import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters.builtin import Command
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для контроля флуда.
    """

    async def on_process_message(self, message: types.Message, data: dict):
        """
        Вызывается при получении команды.
        """
        if command := data.get("command"):
            command: Command.CommandObj
            logger.opt(colors=True).log(
                "COMMAND",
                "User <c>{user}</c> call command <y>{command_name}</y>".format(
                    user=f"{message.from_user.mention}({message.from_user.id})",
                    command_name=command.command,
                ),
            )
        elif raw_state := data.get("raw_state"):
            raw_state: str
            logger.opt(colors=True).debug(
                "User <c>{user}</c> on raw state <y>{raw_state}</y>".format(
                    user=f"{message.from_user.mention}({message.from_user.id})",
                    raw_state=raw_state,
                )
            )
        else:
            logger.debug("Process message: message={0}, data={1}".format(message, data))
