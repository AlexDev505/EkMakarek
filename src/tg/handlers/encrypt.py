from __future__ import annotations

import typing as ty
from io import BytesIO

from loguru import logger

from misc.crypto_img import encrypt
from misc.stickers import get_sticker
from .. import keyboards
from ..bot import bot
from ..rate_limit import rate_limit
from ..states import Encrypt
from ..utils import CancelHandler


if ty.TYPE_CHECKING:
    from telebot.types import Message
    from telebot.states.sync.context import StateContext


@bot.message_handler(commands=["encrypt"])
@rate_limit(5)
def encrypt_start_handler(message: Message, state: StateContext):
    if state.get() is not None:
        return bot.reply_to(message, "Use /cancel and repeat the attempt")

    bot.send_message(
        message.chat.id,
        "Enter the text you want to hide.\n"
        "_Note:_ use only punctuation marks, numbers, english and russian symbols",
        reply_markup=keyboards.cancel_keyboard(),
        parse_mode="markdown",
    )
    state.set(Encrypt.waiting_for_text)


@bot.message_handler(state=Encrypt.waiting_for_text)
def get_text(message: Message, state: StateContext):
    state.add_data(text=message.text)
    state.set(Encrypt.waiting_for_key)
    bot.send_message(
        message.chat.id, "Enter the encryption key (word, set of numbers, anything...)"
    )


@bot.message_handler(state=Encrypt.waiting_for_key)
def get_key(message: Message, state: StateContext):
    state.add_data(key=message.text)
    state.set(Encrypt.waiting_for_img)
    bot.send_message(
        message.chat.id,
        "Send image\n"
        "_Note:_ If the picture does not have a background, it will lose transparency.",
        parse_mode="markdown",
    )


def get_image(message: Message) -> BytesIO:
    try:
        if message.document:
            file = bot.get_file(message.document.file_id)
        elif message.photo:
            file = bot.get_file(message.photo[-1].file_id)
        else:
            raise RuntimeError
        return BytesIO(bot.download_file(file.file_path))
    except (AttributeError, RuntimeError):
        bot.reply_to(
            message, "Send the picture.\nFor canceling the operation use /cancel"
        )
        raise CancelHandler()


def encrypt_image(message: Message, state: StateContext, image: BytesIO) -> BytesIO:
    with state.data() as data:
        text = data["text"]
        key = data["key"]

    crypto_image = encrypt(text, key, image)

    # Save the picture in BytesIO
    crypto_image_bio = BytesIO()
    crypto_image_bio.name = "crypto_image.png"
    crypto_image.save(crypto_image_bio, "PNG")
    crypto_image_bio.seek(0)

    return crypto_image_bio


@bot.message_handler(
    state=Encrypt.waiting_for_img, content_types=["photo", "text", "document"]
)
def encrypt_finish(message: Message, state: StateContext):
    image = get_image(message)
    msg_queue = bot.reply_to(message, "Added to queue")

    try:
        crypto_image_bio = encrypt_image(message, state, image)
    except RuntimeError as err:
        bot.delete_message(message.chat.id, msg_queue.message_id)
        bot.send_sticker(message.chat.id, get_sticker("error"))
        bot.send_message(
            message.chat.id,
            f"Something went wrong: {str(err)}.\n"
            "Send another picture or end with a command /cancel",
        )
        return

    bot.send_document(message.chat.id, crypto_image_bio)
    bot.delete_message(message.chat.id, msg_queue.message_id)

    state.delete()
    bot.send_sticker(
        message.chat.id,
        get_sticker("complete"),
        reply_markup=keyboards.commands_keyboard(),
    )
