from io import BytesIO

import asyncio
import concurrent.futures
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType, ParseMode
import functools
from loguru import logger

from app.keyboards.reply import cancel_keyboard, commands_keyboard
from app.misc.crypto_img import encrypt
from app.misc.states import Encrypt


async def encrypt_start(message: Message, state: FSMContext):
    if await state.get_state() is not None:  # Работает другая команда
        await message.reply("Воспользуйтесь командой /cancel и повторите попытку")
        return
    await message.answer(
        "Напишите текст, который хотите спрятать.\n"
        "_Внимание:_ Используйте только "
        "знаки препинания, цифры, английские и русские символы",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await Encrypt.waiting_for_text.set()


async def get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)  # Сохраняем текст
    # Переходим к следующему шагу
    await Encrypt.next()
    await message.answer(
        "Напишите ключ шифрования(слово, набор цифр, все что угодно...)"
    )


async def get_key(message: Message, state: FSMContext):
    await state.update_data(key=message.text)  # Сохраняем ключ
    # Переходим к следующему шагу
    await Encrypt.next()
    await message.answer("Отправьте картинку(-и)")


async def encrypt_finish(message: Message, state: FSMContext):
    # Получаем сохраненные данные статуса (текст, ключ и др.)
    data = await state.get_data()

    # Принимаем все фото из альбома
    if message.media_group_id:
        logger.trace(f"{data=}")
        logger.trace(f"{message.media_group_id=}")
        current_media_group_id = data.get("media_group_id")
        if current_media_group_id is None:
            # Первое вложение из группы
            await state.update_data(
                media_group_id=message.media_group_id, media_group_files_count=1
            )
            logger.trace("start of media group")
        else:
            # Группа уже инициализирована
            if current_media_group_id != message.media_group_id:
                # Вложение из другого сообщения
                return
            else:
                # Вложение из текущей группы
                logger.trace(f"new file. {data['media_group_files_count'] + 1=}")
                await state.update_data(
                    media_group_files_count=data["media_group_files_count"] + 1
                )  # Увеличиваем счетчик файлов

    image = BytesIO()
    try:
        if message.document:
            # Если получена не картинка, возникает AttributeError
            await message.document.thumb.download(destination_file=image)
        elif message.photo:
            await message.photo[-1].download(destination_file=image)
        else:
            # Получено что-то другое
            raise RuntimeError
    except (AttributeError, RuntimeError):
        await message.reply(
            "Отправьте картинку(-и).\nДля отмены операции используйте /cancel"
        )
        return

    data = await state.get_data()  # Обновляем локальные данные
    logger.trace(f"{data=}")
    msg_queue = await message.answer("Добавлено в очередь.")

    try:
        # Шифруем текст в картинку.
        # Запускаем блокирующую функцию encrypt в другом потоке.
        # Если просто так запустим encrypt, то бот зависнет.
        loop = asyncio.get_running_loop()  # Текущий цикл
        with concurrent.futures.ThreadPoolExecutor() as pool:
            logger.trace(
                "start encrypt {}".format(
                    data["media_group_files_count"] if message.media_group_id else ""
                )
            )
            crypto_image = await loop.run_in_executor(
                pool,  # Новый поток
                functools.partial(
                    encrypt, text=data["text"], key=data["key"], image=image
                ),  # Создаем callable объект с заготовленными параметрами
            )
    except RuntimeError as err:  # Ошибки при шифровании
        await msg_queue.delete()  # Удаляем сообщение о добавлении в очередь
        await message.answer_sticker(open("stickers/error.webp", "rb"))
        await message.answer(
            f"Возникла ошибка: {str(err)}.\n"
            f"Отправьте другую картинку или завершите командой /cancel"
        )
        return

    logger.trace(
        "finish encrypt {}".format(
            data["media_group_files_count"] if message.media_group_id else ""
        )
    )

    # Сохраняем картинку в BytesIO
    crypto_image_bio = BytesIO()
    crypto_image_bio.name = "crypto_image.png"
    crypto_image.save(crypto_image_bio, "PNG")
    crypto_image_bio.seek(0)

    logger.trace(
        "send file {}".format(
            data["media_group_files_count"] if message.media_group_id else ""
        )
    )

    await message.answer_document(crypto_image_bio)
    await msg_queue.delete()

    if message.media_group_id:
        # Если обработана группа файлов.
        # Уменьшаем счетчик
        media_group_files_count = data["media_group_files_count"] - 1
        await state.update_data(media_group_files_count=media_group_files_count)
        if media_group_files_count != 0:
            # Еще остались необработанные файлы
            return
        logger.trace(f"finish media group {data['media_group_id']}")

    await state.finish()  # Завершаем команду
    await message.answer_sticker(
        open("stickers/complete.webp", "rb"), reply_markup=commands_keyboard()
    )


def register_encrypt(dp: Dispatcher):
    dp.register_message_handler(encrypt_start, commands=["encrypt"], state="*")
    dp.register_message_handler(get_text, state=Encrypt.waiting_for_text)
    dp.register_message_handler(get_key, state=Encrypt.waiting_for_key)
    dp.register_message_handler(
        encrypt_finish,
        state=Encrypt.waiting_for_img,
        content_types=[ContentType.TEXT, ContentType.DOCUMENT, ContentType.PHOTO],
    )
