import os
from typing import BinaryIO


def get_sticker(name: str) -> BinaryIO:
    """
    Необходимо для правильной работы на сервере.
    :param name: Название стикера.
    :return: Стикер, который можно отправить.
    """
    path = f"stickers/{name}.webp"
    try:
        return open(path, "rb")
    except FileNotFoundError:
        os.chdir("EkMakarek")
        return get_sticker(name)
