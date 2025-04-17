from __future__ import annotations

import typing as ty
import re

if ty.TYPE_CHECKING:
    from telebot.types import Message


def get_target_user(message: Message) -> int | str | None:
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    possible_mentioned_text = message.text or message.caption
    if not possible_mentioned_text:
        return None

    entities = message.entities or message.caption_entities
    if not entities:
        return None

    for ent in entities:
        if ent.type == "text_mention":
            return ent.user.id
        elif ent.type == "mention":
            return possible_mentioned_text[ent.offset : ent.offset + ent.length][1:]
    return None


def get_command_args(text: str) -> str:
    return re.sub(r"^/\S+ ", "", text)


class CancelHandler(Exception):
    pass
