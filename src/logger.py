from __future__ import annotations

import os
import re
import sys
import typing as ty

from loguru import logger

logger.remove(0)

if ty.TYPE_CHECKING:
    from src.config import Config


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


def uncolored_formatter(record) -> str:
    if "" in record["message"]:
        record["message"] = re.sub(r"\[((\d+);?)+m", "", record["message"])
    return formatter(record)


def init_logger(config: Config) -> None:
    if config.logger.console:
        logger.add(
            sys.stdout, colorize=True, format=formatter, level=config.logger.level
        )

    if DEBUG_PATH := config.logger.file:
        logger.add(
            DEBUG_PATH,
            colorize=False,
            format=uncolored_formatter,
            level=config.logger.level,
        )

    logger.level("TRACE", color="<lk>")  # TRACE - blue
    logger.level("DEBUG", color="<w>")  # DEBUG - white
    logger.level("INFO", color="<c><bold>")  # INFO - cyan
