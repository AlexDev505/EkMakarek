import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled


def rate_limit(limit: int, key=None):
    """
    Декоратор для настройки лимита частоты использования команды.
    :param limit: Рак в сколько секунд можно использовать команду.
    :param key: Название команды.
    """

    def decorator(func):
        setattr(func, "throttling_rate_limit", limit)
        if key:
            setattr(func, "throttling_key", key)
        return func

    return decorator


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для контроля флуда.
    """

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix="antiflood_"):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, *_):
        """
        Вызывается при получении команды.
        :param message:
        """
        handler = current_handler.get()  # Получаем обработчик команды
        dispatcher = Dispatcher.get_current()  # Получаем диспетчер
        if handler:
            # Если обработчик команды зарегистрирован, получаем настройку антифлуда.
            limit = getattr(handler, "throttling_rate_limit", self.rate_limit)
            key = getattr(
                handler, "throttling_key", f"{self.prefix}_{handler.__name__}"
            )
        else:
            # Обработчика команды нет
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            # Проверяем соблюдение лимита
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            # Нарушение
            await self.message_throttled(message, t)
            raise CancelHandler()  # Не пропускаем событие дальше

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        """
        Уведомляет пользователя о превышение.
        Если команда уже заблокирована, то время блокировки прибавляется.
        """
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(
                handler, "throttling_key", f"{self.prefix}_{handler.__name__}"
            )
        else:
            key = f"{self.prefix}_message"

        # Определяем время блокировки команды
        delta = throttled.rate - throttled.delta

        # Уведомляем о превышении
        if throttled.exceeded_count <= 2:
            msg = await message.reply(
                f"Слишком много запросов! Команда временно заблокирована ({round(delta)} с)"
            )
            setattr(handler, "info_msg", msg)

        # Блокируем
        await asyncio.sleep(delta)

        # Проверяем статус блокировки
        thr = await dispatcher.check_key(key)

        if thr.exceeded_count == throttled.exceeded_count:
            # Если это последнее сообщение с вызовом команды

            # TODO: заменить на `await dispatcher.release_key(key)`.
            # в коде aiogram присутствует ошибка. Ждем фикса.
            # https://github.com/aiogram/aiogram/issues/907
            try:
                await dispatcher.release_key(key)
            except KeyError:
                chat_obj = types.Chat.get_current()
                chat_id = chat_obj.id if chat_obj else None

                user_obj = types.User.get_current()
                user_id = user_obj.id if user_obj else None

                bucket = await dispatcher.storage.get_bucket(chat=chat_id, user=user_id)
                if bucket and key in bucket:
                    del bucket[key]
                    await dispatcher.storage.set_bucket(
                        chat=chat_id, user=user_id, bucket=bucket
                    )

            if msg := getattr(handler, "info_msg", None):
                await msg.delete()
                delattr(handler, "info_msg")
            else:
                await message.reply("Unlocked.")
