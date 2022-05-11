from __future__ import annotations

from dataclasses import dataclass
import os
import sys

from loguru import logger


try:  # Удаление настроек логгера по умолчанию
    logger.remove(0)
except ValueError:
    pass


@dataclass
class LoggingLevel:
    """
    Вспомогательный класс для фильтрации логов по их уровню.
    """

    level: str

    def __call__(self, record: dict) -> bool:
        level_no = logger.level(self.level).no
        return record["level"].no >= level_no


def update_logging_level(level: str) -> None:
    """
    Обновляет уровень логов логгера.
    :param level: Новый уровень для логов.
    """
    level_handler.level = level


def formatter(record) -> str:
    record["extra"]["VERSION"] = os.environ["VERSION"]
    return (
        "<lvl><n>[{level.name} </n></lvl>"
        "<g>{time:YYYY-MM-DD HH:mm:ss.SSS}</g> "
        "<lg>v{extra[VERSION]}</lg>"
        "<lvl><n>]</n></lvl> "
        "<w>{thread.name}:{module}.{function}</w>: "
        "<lvl><n>{message}</n></lvl>\n{exception}"
    )


def init_logger() -> None:
    update_logging_level(os.environ["LOGGING_LEVEL"])

    logger.add(
        sys.stdout,
        colorize=True,
        format=formatter,
        filter=level_handler,
        level=0,
    )

    logger.add(
        os.environ["LOG_FILE"],
        colorize=False,
        format=formatter,
        filter=level_handler,
        level=6,  # Больше, чем TRACE
    )

    logger.level("TRACE", color="<e>")  # TRACE - синий
    logger.level("DEBUG", color="<w>")  # DEBUG - белый
    logger.level("INFO", color="<c>")  # INFO - бирюзовый


level_handler = LoggingLevel('DEBUG')
