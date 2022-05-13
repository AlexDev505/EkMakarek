import asyncio
import concurrent.futures
import functools
from io import BytesIO

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import Message, ContentType, ParseMode
from loguru import logger

from app.keyboards.reply import cancel_keyboard, commands_keyboard
from app.misc.crypto_img import decrypt
from app.misc.states import Decrypt
from app.middlewares.throttling import rate_limit
from app.misc.stickers import get_sticker


@rate_limit(5, "decrypt")
async def decrypt_start(message: Message, state: FSMContext):
    if await state.get_state() is not None:  # Работает другая команда
        await message.reply("Воспользуйтесь командой /cancel и повторите попытку")
        return

    await message.answer(
        "Напишите ключ шифрования\n",
        reply_markup=cancel_keyboard(),
    )
    await Decrypt.waiting_for_key.set()  # Начинаем группу команд


async def get_key(message: Message, state: FSMContext):
    await state.update_data(key=message.text)  # Сохраняем ключ
    # Переходим к следующему шагу
    await Decrypt.next()
    await message.answer("Отправьте картинку(-и)")


# === DECRYPT_FINISH ===


async def get_image(message: Message) -> BytesIO:
    """
    Получает и скачивает картинку.
    :return: Картинка.
    :raises: CancelHandler
    """
    image = BytesIO()
    try:
        if message.document:  # Картинка без сжатия
            # Если получена не картинка, возникает AttributeError
            file = await message.bot.get_file(message.document.file_id)
            await message.bot.download_file(file.file_path, destination=image)
        else:  # Получено что-то другое
            raise RuntimeError
    except (AttributeError, RuntimeError):
        await message.reply(
            "Отправьте не сжатую картинку.\nДля отмены операции используйте /cancel"
        )
        raise CancelHandler()

    return image


async def decrypt_image(message: Message, state: FSMContext, image: BytesIO) -> str:
    """
    Расшифровывает текст из картинки.
    :param message:
    :param state:
    :param image: Картинка.
    :return: Текст.
    """
    data = await state.get_data()  # Обновляем локальные данные

    # Запускаем блокирующую функцию decrypt в другом потоке.
    # Если просто так запустим decrypt, то бот зависнет.
    loop = asyncio.get_running_loop()  # Текущий цикл
    with concurrent.futures.ThreadPoolExecutor() as pool:
        logger.trace(f"start decrypt {message.message_id}")
        text = await loop.run_in_executor(
            pool,  # Новый поток
            functools.partial(
                decrypt, key=data["key"], image=image
            ),  # Создаем callable объект с заготовленными параметрами
        )

    logger.trace(f"finish decrypt {message.message_id}")

    return text


async def decrypt_finish(message: Message, state: FSMContext):
    image = await get_image(message)
    msg_queue = await message.answer("Добавлено в очередь.")

    # Получаем сохраненные данные статуса (текст, ключ и др.)
    data = await state.get_data()
    logger.trace(f"{data=}")

    text = await decrypt_image(message, state, image)

    if len(text) + 25 > 4096:
        if len(text) > 4096:
            messages = []
            while len(text) > 4096:
                messages.append(text[:4096])
                text = text[4096:]
            await message.reply("Вот что я расшифровал:")
            for part in messages:
                await message.answer(part)
        else:
            await message.reply("Вот что я расшифровал:")
            await message.reply(text)
    else:
        await message.reply(f"Вот что я расшифровал:\n{text}")

    await msg_queue.delete()

    await state.finish()  # Завершаем команду
    await message.answer_sticker(
        get_sticker("complete"), reply_markup=commands_keyboard()
    )


# ======================


def register_decrypt(dp: Dispatcher):
    dp.register_message_handler(decrypt_start, commands=["decrypt"], state="*")
    dp.register_message_handler(get_key, state=Decrypt.waiting_for_key)
    dp.register_message_handler(
        decrypt_finish,
        state=Decrypt.waiting_for_img,
        content_types=[ContentType.TEXT, ContentType.DOCUMENT, ContentType.PHOTO],
    )
