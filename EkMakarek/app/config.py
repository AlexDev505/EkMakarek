from dataclasses import dataclass

import os
from environs import Env


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


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
        ),
        logger=Logger(
            log_file=env.str("LOG_FILE"),
            loging_level=env.str("LOGGING_LEVEL")
        ),
        misc=Misc(
            version=env.str("VERSION")
        )
    )
