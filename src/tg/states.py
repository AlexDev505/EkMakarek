from telebot.states import State, StatesGroup
from telebot.storage import StateMemoryStorage


states_storage = StateMemoryStorage()


class Encrypt(StatesGroup):
    waiting_for_text = State()
    waiting_for_key = State()
    waiting_for_img = State()


class Decrypt(StatesGroup):
    waiting_for_key = State()
    waiting_for_img = State()
