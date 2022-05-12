from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from app.keyboards.reply import start_keyboard, commands_keyboard
from app.middlewares.throttling import rate_limit


@rate_limit(2, "start")
async def start(message: Message):
    await message.answer_sticker(open("stickers/hello.webp", "rb"))
    await message.answer(
        "Привет! Я Ёк макарек)\n" "Вот что я могу предложить тебе сейчас:\n" "/help",
        reply_markup=start_keyboard(),
    )


@rate_limit(5, "help")
async def help_command(message: Message):
    await message.answer(
        "Я могу прятать и находить текст в картинке. "
        "Даже зная алгоритм шифрования, посторонний не сможет "
        "узнать спрятанное послание, так как ключ знаешь только ты!\n\n"
        "Доступные команды:\n"
        "/help - вывод этого сообщения\n"
        "/encrypt - зашифровать текст в картинке\n"
        "/decrypt - расшифровать текст\n"
        "/cancel - отменить текущую операцию\n"
    )


@rate_limit(2, "cancel")
async def cancel(message: Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=commands_keyboard())


def register_user(dp: Dispatcher):
    dp.register_message_handler(start, commands=["start"], state="*")
    dp.register_message_handler(help_command, commands=["help"], state="*")
    dp.register_message_handler(cancel, commands=["cancel"], state="*")
