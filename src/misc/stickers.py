from typing import BinaryIO


def get_sticker(name: str) -> BinaryIO:
    """
    :param name: The name of sticker.
    :return: A sticker that can be sent.
    """
    path = f"../stickers/{name}.webp"
    return open(path, "rb")
