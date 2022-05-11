from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from app.config import load_config
from app.filters.admin import AdminFilter
from app.handlers.admin import register_admin
from app.handlers.echo import register_echo
from app.handlers.user import register_user
from app.middlewares.db import DbMiddleware
from app.misc.logger import init_logger, logger


def register_all_middlewares(dp):
    dp.setup_middleware(DbMiddleware())


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)

    register_echo(dp)


async def on_startup(_):
    logger.info('Bot started!')


def main():
    config = load_config(".env")
    init_logger()

    logger.debug('Starting bot')

    storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    bot['config'] = config

    register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)

    # start
    executor.start_polling(dispatcher=dp, on_startup=on_startup)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        logger.exception(err)
