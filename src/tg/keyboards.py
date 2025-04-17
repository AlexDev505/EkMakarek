from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def start_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/help"))


def commands_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("/encrypt - зашифровать текст в картинке"),
        KeyboardButton("/decrypt - расшифровать текст"),
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/cancel"))
