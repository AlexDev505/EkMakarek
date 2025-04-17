from __future__ import annotations

import os
import re
import typing as ty
from abc import ABC
from contextlib import suppress
from dataclasses import dataclass
from inspect import isclass


@dataclass
class ConfigSection(ABC):
    required_fields = []
    section_name = None

    def __post_init__(self):
        for var_name in self.required_fields:
            if self.__getattribute__(var_name) in {None, ""}:
                raise NotImplementedError(
                    f"{self.env_name(var_name)} not set in virtual environment"
                )
        self.format_values()

    def format_values(self) -> None:
        for var_name, value in self.__dict__.items():
            if isinstance(value, str):
                self.__setattr__(var_name, (value := value.format(os=os)))
                os.environ[self.env_name(var_name)] = str(value)

    @classmethod
    def env_name(cls, var_name) -> str:
        section_name = (
            cls.section_name if cls.section_name is not None else cls.__name__
        )
        section_name = re.sub(r"\B([A-Z])", r"_\g<1>", section_name)
        return f"{f'{section_name.upper()}_' if section_name else ''}{var_name.upper()}"

    @classmethod
    def load_from_env(cls) -> ConfigSection:
        kwargs = {}
        for var_name, var_type in ty.get_type_hints(cls).items():
            if isclass(var_type) and issubclass(var_type, ConfigSection):
                value = var_type.load_from_env()
            else:
                value = os.environ.get(
                    cls.env_name(var_name), getattr(cls, var_name, "")
                )
                with suppress(ValueError, TypeError):
                    if ty.get_origin(var_type):
                        value = (
                            list(map(ty.get_args(var_type)[0], value.split(",")))
                            if value
                            else []
                        )
                    elif var_type is bool:
                        value = bool(int(value))
                    else:
                        value = var_type(value)
            kwargs[var_name] = value
        return cls(**kwargs)  # noqa


@dataclass
class Base(ConfigSection):
    run_in_host: bool
    version: str

    section_name = ""
    required_fields = ["run_in_host"]


@dataclass
class Logging(ConfigSection):
    file: str
    console: bool = True
    level: str = "DEBUG"


@dataclass
class TgBot(ConfigSection):
    token: str
    webhook: TgBotWebhook
    admins: list[int]

    required_fields = ["token"]


@dataclass
class TgBotWebhook(ConfigSection):
    host: str
    secret_key: str

    if int(os.getenv("RUN_IN_HOST", "0")):
        required_fields = ["host"]

    def __post_init__(self):
        if not self.secret_key:
            self.secret_key = os.getenv("TG_BOT_TOKEN")
        super(TgBotWebhook, self).__post_init__()


@dataclass
class Config(ConfigSection):
    base: Base
    logger: Logging
    tg_bot: TgBot


def load_config() -> Config:
    return Config.load_from_env()
