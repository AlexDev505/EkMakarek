from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from app.config import load_config

# === FILTERS ===
from app.filters.admin import AdminFilter

# === HANDLERS ===
from app.handlers.base_commands import register_user
from app.handlers.encrypt import register_encrypt

# === MISC ===
from app.misc.logger import init_logger, logger


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_user(dp)
    register_encrypt(dp)


async def on_startup(_):
    logger.info("Bot started!")


def main():
    config = load_config(".env")
    init_logger()

    logger.debug("Starting bot")

    storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)

    bot["config"] = config

    register_all_filters(dp)
    register_all_handlers(dp)

    # start
    executor.start_polling(dispatcher=dp, on_startup=on_startup)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        logger.exception(err)
