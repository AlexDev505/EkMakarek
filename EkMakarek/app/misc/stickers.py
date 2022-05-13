import os
from typing import BinaryIO


def get_sticker(name: str) -> BinaryIO:
    path = f"stickers/{name}.webp"
    try:
        return open(path, "rb")
    except FileNotFoundError:
        os.chdir("ekmakarek")
        return get_sticker(name)
