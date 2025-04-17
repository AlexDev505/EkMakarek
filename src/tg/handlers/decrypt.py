from __future__ import annotations

import typing as ty
from io import BytesIO

from loguru import logger

from misc.crypto_img import encrypt, decrypt
from misc.stickers import get_sticker
from .. import keyboards
from ..bot import bot
from ..rate_limit import rate_limit
from ..states import Decrypt
from ..utils import CancelHandler


if ty.TYPE_CHECKING:
    from telebot.types import Message
    from telebot.states.sync.context import StateContext


@bot.message_handler(commands=["decrypt"])
@rate_limit(5)
def encrypt_start_handler(message: Message, state: StateContext):
    if state.get() is not None:
        return bot.reply_to(message, "Use /cancel and repeat the attempt")

    bot.send_message(
        message.chat.id,
        "Enter the encryption key\n",
        reply_markup=keyboards.cancel_keyboard(),
    )
    state.set(Decrypt.waiting_for_key)


@bot.message_handler(state=Decrypt.waiting_for_key)
def get_key(message: Message, state: StateContext):
    state.add_data(key=message.text)
    state.set(Decrypt.waiting_for_img)
    bot.send_message(message.chat.id, "Send image without compression")


def get_image(message: Message) -> BytesIO:
    try:
        if message.document:
            file = bot.get_file(message.document.file_id)
            return BytesIO(bot.download_file(file.file_path))
        raise RuntimeError
    except (AttributeError, RuntimeError):
        bot.reply_to(
            message,
            "Send the uncompressed picture.\n"
            "For canceling the operation use /cancel",
        )
        raise CancelHandler()


def decrypt_image(message: Message, state: StateContext, image: BytesIO) -> str:
    with state.data() as data:
        key = data["key"]

    logger.trace(f"start decrypt {message.message_id}")
    text = decrypt(key, image)
    logger.trace(f"finish decrypt {message.message_id}")

    return text


@bot.message_handler(
    state=Decrypt.waiting_for_img, content_types=["text", "photo", "document"]
)
def encrypt_finish(message: Message, state: StateContext):
    image = get_image(message)
    with state.data() as data:
        if data.get("processing"):
            return
        data["processing"] = True
    msg_queue = bot.reply_to(message, "Added to queue")

    try:
        text = decrypt_image(message, state, image)
    except RuntimeError as err:
        bot.delete_message(message.chat.id, msg_queue.message_id)
        bot.send_sticker(message.chat.id, get_sticker("error"))
        bot.send_message(
            message.chat.id,
            f"Something went wrong: {str(err)}.\n"
            "Send another picture or end with a command /cancel",
        )
        with state.data() as data:
            data["processing"] = False
        return

    if len(text) + 25 > 4096:
        if len(text) > 4096:
            messages = []
            while len(text) > 4096:
                messages.append(text[:4096])
                text = text[4096:]
            bot.reply_to(message, "Вот что я расшифровал:")
            for part in messages:
                bot.reply_to(message, part)
        else:
            bot.reply_to(message, "Вот что я расшифровал:")
            bot.reply_to(message, text)
    else:
        bot.reply_to(message, f"Вот что я расшифровал:\n{text}")
    bot.delete_message(message.chat.id, msg_queue.message_id)

    state.delete()
    bot.send_sticker(
        message.chat.id,
        get_sticker("complete"),
        reply_markup=keyboards.commands_keyboard(),
    )
