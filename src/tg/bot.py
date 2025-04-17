import time

from telebot import TeleBot, custom_filters
from telebot.states.sync.middleware import StateMiddleware

from app import config
from .exceptions import MyExcHandler
from .states import states_storage


bot = TeleBot(
    config.tg_bot.token,
    threaded=False,
    state_storage=states_storage,
    use_class_middlewares=True,
    parse_mode="HTML",
    exception_handler=MyExcHandler(),
)
bot.setup_middleware(StateMiddleware(bot))
bot.add_custom_filter(custom_filters.StateFilter(bot))


def setup_webhook() -> None:
    bot.remove_webhook()
    time.sleep(0.1)
    bot.set_webhook(
        f"{config.tg_bot.webhook.host}/{config.tg_bot.webhook.secret_key}",
        max_connections=1,
    )


def run_pooling():
    bot.remove_webhook()
    bot.infinity_polling()
