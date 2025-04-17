from __future__ import annotations

import typing as ty

from misc.stickers import get_sticker
from .. import keyboards
from ..bot import bot
from ..rate_limit import rate_limit


if ty.TYPE_CHECKING:
    from telebot.types import Message
    from telebot.states.sync import StateContext


@bot.message_handler(commands=["test"])
@rate_limit(5)
def test_handler(message: Message) -> None:
    print(message)
    bot.reply_to(message, "I`m fine...")


@bot.message_handler(commands=["start"])
@rate_limit(2)
def start_handler(message: Message) -> None:
    bot.send_sticker(message.chat.id, sticker=get_sticker("hello"))
    bot.send_message(
        message.chat.id,
        text="Hi! I'm Ёк макарек)\nHere's what I can offer you now:\n/help",
        reply_markup=keyboards.start_keyboard(),
    )


@bot.message_handler(commands=["help"])
@rate_limit(2)
def help_handler(message: Message) -> None:
    bot.send_message(
        message.chat.id,
        text=(
            "I can hide and find the text in the picture."
            "Even knowing the encryption algorithm, an outsider cannot"
            "find out the hidden message, as only you know the key!\n\n"
            "Available commands:\n"
            "/help - The withdrawal of this message\n"
            "/encrypt - encrypt the text in the picture\n"
            "/decrypt - decrypt the text\n"
            "/cancel - cancel the current operation\n"
        ),
    )


@bot.message_handler(commands=["cancel"], state="*")
@rate_limit(2)
def cancel_handler(message: Message, state: StateContext) -> None:
    state.delete()
    bot.send_message(
        message.chat.id,
        "Operation cancelled",
        reply_markup=keyboards.commands_keyboard(),
    )
