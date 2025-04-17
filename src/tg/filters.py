from __future__ import annotations

import typing as ty

from telebot.custom_filters import AdvancedCustomFilter

from .bot import bot

if ty.TYPE_CHECKING:
    from telebot.types import CallbackQuery
    from telebot.callback_data import CallbackDataFilter


class ProductsCallbackFilter(AdvancedCustomFilter):
    key = "cb_filter"

    def check(self, call: CallbackQuery, cb_filter: CallbackDataFilter):
        return cb_filter.check(query=call)


bot.add_custom_filter(ProductsCallbackFilter())
