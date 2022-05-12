from aiogram.dispatcher.filters.state import State, StatesGroup


class Encrypt(StatesGroup):
    waiting_for_text = State()
    waiting_for_key = State()
    waiting_for_img = State()


class Decrypt(StatesGroup):
    waiting_for_key = State()
    waiting_for_img = State()
