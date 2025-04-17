from loguru import logger
from telebot import ExceptionHandler

from .utils import CancelHandler


class MyExcHandler(ExceptionHandler):
    def handle(self, exception):
        if isinstance(exception, CancelHandler):
            return
        logger.exception(exception)
