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
from app.middlewares.throttling import rate_limit
from app.misc.crypto_img import encrypt
from app.misc.states import Encrypt
from app.misc.stickers import get_sticker


@rate_limit(5, "encrypt")
async def encrypt_start(message: Message, state: FSMContext):
    """
    Обработчик команды /encrypt
    Просит пользователя, написать текст и переходит к следующему шагу (get_text)
    """
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
    await Encrypt.waiting_for_text.set()  # Начинаем группу команд


async def get_text(message: Message, state: FSMContext):
    """
    Получение текста для шифрования.
    Переход к следующему шагу (get_key)
    """
    await state.update_data(text=message.text)  # Сохраняем текст
    # Переходим к следующему шагу
    await Encrypt.next()
    await message.answer(
        "Напишите ключ шифрования(слово, набор цифр, все что угодно...)"
    )


async def get_key(message: Message, state: FSMContext):
    """
    Получение ключа шифрования.
    Переход к следующему шагу (encrypt_finish)
    """
    await state.update_data(key=message.text)  # Сохраняем ключ
    # Переходим к следующему шагу
    await Encrypt.next()
    await message.answer(
        "Отправьте картинку(-и) (Не более 10)\n"
        "_Внимание:_ Если у картинки нет фона, он станет черным.",
        parse_mode=ParseMode.MARKDOWN,
    )


# === ENCRYPT_FINISH ===


async def validate_message_media(message: Message, state: FSMContext) -> True:
    """
    Проверяет соответствие media_group_id.
    :raises: CancelHandler
    """
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
                media_group_id=message.media_group_id,
                media_group_files_count=1,
                files={message.message_id: 1},
                processed_files=set(),
            )
            logger.trace("start of media group")
        else:
            # Группа уже инициализирована
            if current_media_group_id != message.media_group_id:
                # Вложение из другого сообщения
                raise CancelHandler()
            else:
                # Вложение из текущей группы
                logger.trace(f"new file. {data['media_group_files_count'] + 1=}")
                files = data["files"]
                files[message.message_id] = data["media_group_files_count"] + 1
                await state.update_data(
                    media_group_files_count=data["media_group_files_count"] + 1,
                    files=files,
                )  # Увеличиваем счетчик файлов

    return True


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
        elif message.photo:  # Сжатая картинка
            await message.photo[-1].download(destination_file=image)
        else:  # Получено что-то другое
            raise RuntimeError
    except (AttributeError, RuntimeError):
        await message.reply(
            "Отправьте картинку(-и).\nДля отмены операции используйте /cancel"
        )
        raise CancelHandler()

    return image


async def encrypt_image(message: Message, state: FSMContext, image: BytesIO) -> BytesIO:
    """
    Шифрует текст в картинку.
    :param message:
    :param state:
    :param image: Картинка.
    :return: Обработанная картинка.
    :raises: RuntimeError
    """
    data = await state.get_data()  # Обновляем локальные данные

    # Шифруем текст в картинку.
    # Запускаем блокирующую функцию encrypt в другом потоке.
    # Если просто так запустим encrypt, то бот зависнет.
    loop = asyncio.get_running_loop()  # Текущий цикл
    with concurrent.futures.ThreadPoolExecutor() as pool:
        logger.trace(
            "start encrypt {}".format(
                data["files"][message.message_id] if message.media_group_id else ""
            )
        )
        crypto_image = await loop.run_in_executor(
            pool,  # Новый поток
            functools.partial(
                encrypt, text=data["text"], key=data["key"], image=image
            ),  # Создаем callable объект с заготовленными параметрами
        )

    logger.trace(
        "finish encrypt {}".format(
            data["files"][message.message_id] if message.media_group_id else ""
        )
    )

    # Сохраняем картинку в BytesIO
    crypto_image_bio = BytesIO()
    crypto_image_bio.name = "crypto_image.png"
    crypto_image.save(crypto_image_bio, "PNG")
    crypto_image_bio.seek(0)

    return crypto_image_bio


@rate_limit(0, "get_image")  # Отключаем контроль флуда
async def encrypt_finish(message: Message, state: FSMContext):
    """
    Завершающая команда.
    Получение, шифрование и отправка обработанной картинки.
    """
    await validate_message_media(message, state)
    image = await get_image(message)
    msg_queue = await message.answer("Добавлено в очередь.")

    data = await state.get_data()  # Обновляем локальные данные
    logger.trace(f"{data=}")

    try:
        crypto_image_bio = await encrypt_image(message, state, image)
    except RuntimeError as err:  # Ошибки при шифровании
        await msg_queue.delete()  # Удаляем сообщение о добавлении в очередь
        await message.answer_sticker(get_sticker("error"))
        await message.answer(
            f"Возникла ошибка: {str(err)}.\n"
            f"Отправьте другую картинку или завершите командой /cancel"
        )
        return

    logger.trace(
        "send file {}".format(
            data["files"][message.message_id] if message.media_group_id else ""
        )
    )

    await message.answer_document(crypto_image_bio)
    await msg_queue.delete()

    if message.media_group_id:
        # Если обработана группа файлов.
        data = await state.get_data()  # Обновляем локальные данные
        data["processed_files"].add(message.message_id)
        logger.trace(f"{data=}")

        if data["processed_files"] != set(data["files"].keys()):
            # Еще остались необработанные файлы
            await state.update_data(processed_files=data["processed_files"])
            return
        logger.trace(f"finish media group {data['media_group_id']}")

    await state.finish()  # Завершаем команду
    await message.answer_sticker(
        get_sticker("complete"), reply_markup=commands_keyboard()
    )


# ======================


def register_encrypt(dp: Dispatcher):
    dp.register_message_handler(encrypt_start, commands=["encrypt"], state="*")
    dp.register_message_handler(get_text, state=Encrypt.waiting_for_text)
    dp.register_message_handler(get_key, state=Encrypt.waiting_for_key)
    dp.register_message_handler(
        encrypt_finish,
        state=Encrypt.waiting_for_img,
        content_types=[ContentType.TEXT, ContentType.DOCUMENT, ContentType.PHOTO],
    )
