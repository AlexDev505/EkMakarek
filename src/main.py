from app import app, config  # noqa
import tg  # noqa
from loguru import logger  # noqa

logger.info("app started")


if __name__ == "__main__":
    if config.base.run_in_host:
        tg.bot.setup_webhook()
        app.run(debug=True)
    else:
        with app.app_context():
            tg.run_pooling()
