import os
from dataclasses import dataclass


@dataclass
class ConfigSection:
    def __post_init__(self):
        for var_name, value in vars(self).items():
            os.environ[var_name.upper()] = str(value)


@dataclass
class TgBot(ConfigSection):
    token: str
    admin_ids: list[int]


@dataclass
class Logger(ConfigSection):
    log_file: str
    loging_level: str


@dataclass
class Misc(ConfigSection):
    version: str


@dataclass
class Config:
    tg_bot: TgBot
    logger: Logger
    misc: Misc


def load_config() -> Config:
    return Config(
        tg_bot=TgBot(
            token=os.environ["BOT_TOKEN"],
            admin_ids=list(map(int, os.environ["ADMINS"].split(","))),
        ),
        logger=Logger(
            log_file=os.environ.get("LOG_FILE", "No file logging"),
            loging_level=os.environ.get("LOGGING_LEVEL", "DEBUG"),
        ),
        misc=Misc(version=os.environ.get("VERSION", "No info")),
    )
