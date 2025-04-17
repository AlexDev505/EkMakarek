from app import app, config  # noqa
import tg  # noqa
from loguru import logger  # noqa

logger.info("app started")


if config.base.run_in_host:
    tg.setup_webhook()
    if __name__ == "__main__":
        app.run(debug=True)
else:
    with app.app_context():
        tg.run_pooling()
