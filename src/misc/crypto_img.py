"""

Functions of encryption and decryption of text in pictures.
Copyright (c) 2022 Alex Filiov <https://github.com/AlexDev505>

https://github.com/AlexDev505/CryptoImg

"""

import random
from hashlib import sha256
from io import BytesIO

from PIL import Image, UnidentifiedImageError


def get_seed(key: str) -> str:
    """
    Gets hash of key.
    Used as seed in further generation of random numbers to get random pixels.
    :param key: Secret key.
    :returns: seed for random numbers.
    """
    return sha256(key.encode()).hexdigest()  # We use the Hash function Sha256


def char_to_bits(char_number: int) -> tuple[str, str, str]:
    """
    Converts the Unicode the number of symbols into the binary number system.
    :param char_number: Unicode number.
    :returns: Binary representation of the symbol.
    example:
        >>> char_to_bits(ord('F'))
        ('010', '00', '110')
    """
    bits = "{0:b}".format(char_number).rjust(8, "0")
    return bits[:3], bits[3:5], bits[5:]


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """
    Converts the RGB color representation in hexadecimal.
    :param rgb: RGB color.
    :returns: The hexadecimal color view.
    """
    return "0x{:02x}{:02x}{:02x}".format(*rgb)


def color_number_to_bits(color_number: int) -> tuple[str, str, str]:
    """
    Converts the ten color representation in the binary.
    :param color_number: Ten -sized color view.
    :returns: Binsry presentation of Color.
    example:
        >>> color_number_to_bits(int(rgb_to_hex((255, 1, 55)), 16))
        ('11111111', '00000001', '00110111')
    """
    bits = "{0:b}".format(color_number).rjust(24, "0")
    return bits[0:8], bits[8:16], bits[16:]


def color_number_to_rgb(color_number: int) -> tuple[int, int, int]:
    """
    Converts the ten color representation in RGB.
    :param color_number: Ten-sized color view.
    :returns: rgb color show.
    """
    bits = color_number_to_bits(color_number)
    return int(bits[0], 2), int(bits[1], 2), int(bits[2], 2)


def encrypt(text: str, key: str, image: BytesIO) -> Image:
    """
    The text is encrypted in the picture.

    Algorithm:
        The secret key is encrypted and used as a seed
        for the generator of pseudo-random numbers.
        The algorithm receives a pseudo pixel, and the last RGB bits
        replaces with the beats of the encrypted symbol.

    :param text: Text for encryption.
    :param key: Secret key.
    :param image: Initial picture.
    :returns: Picture with encrypted text.
    :raises: RuntimeError.

    example:
        >>> import io
        >>> with open(file_path, 'rb') as file:
        ...     data = file.read()
        >>> img = encrypt(text, key, io.BytesIO(data))
        >>> img.save(target_file_path)

    example:
        >>> import io
        >>> import requests
        >>> data = requests.get(img_url).content
        >>> img = encrypt(text, key, io.BytesIO(data))
        >>> img.save(target_file_path)
    """
    try:
        img = Image.open(image).convert("RGB")  # loads the image
    except UnidentifiedImageError:
        raise RuntimeError("It's not a picture")
    img_size = img.size[0] * img.size[1]  # pixes count

    if not len(text):
        raise RuntimeError("There is no text")
    elif len(text) >= img_size:
        raise RuntimeError("The picture is too small")

    text += "\0"  # The sign that the text is over. Need for decryption
    # Pixels in which the symbol is already encrypted.
    used_pixels: list[tuple[int, int]] = []
    random.seed(get_seed(key))  # Install the seed

    for i, char in enumerate(text):  # iterate over text symbols
        # Search for free pixel
        while True:
            # Obtaining a pseudo-random pixel
            pix = (random.randrange(0, img.size[0]), random.randrange(0, img.size[1]))
            if pix not in used_pixels:  # If he is not used
                used_pixels.append(pix)
                break

        char = ord(char)  # Unicode of symbol
        # crutch for Russian letters (because their unicode value is too much)
        if char > 1000:
            char -= 890

        color = int(rgb_to_hex(img.getpixel(pix)), 16)  # The initial color of the pixel

        # put part of the symbol in the last 3 bits of the red canal
        new_color = color & 0xF80000  # 11111000 00000000 00000000
        new_color |= (char & 0xE0) << 11  # 00000111 00000000 00000000

        # put part of the symbol in the last 2 bits of the blue channel
        new_color |= color & (0x3F << 10)  # 00000000 11111100 00000000
        new_color |= (char & 0x18) << 5  # 00000000 00000011 00000000

        # put part of the symbol in the last 3 bits of the green channel
        new_color |= color & (0x1F << 3)  # 00000000 00000000 11111000
        new_color |= char & 0x7  # 00000000 00000000 00000111

        img.putpixel(
            pix, color_number_to_rgb(new_color)
        )  # change the pixel in the picture

    random.seed()  # discard the seed

    return img


def decrypt(key: str, image: BytesIO) -> str:
    """
    Decodes a message from the picture.
    The algorithm is opposite to encryption.

    :param key: Secret key.
    :param image: Picture.
    :returns: Text.
    """
    try:
        img = Image.open(image).convert("RGB")
    except UnidentifiedImageError:
        raise RuntimeError("It's not a picture")

    random.seed(get_seed(key))  # Install the seed
    result = ""  # Decoded text
    checked_pixels: list[tuple[int, int]] = []

    while True:
        # Pixel search
        while True:
            # Obtaining a pseudo-random pixel
            pix = (random.randrange(0, img.size[0]), random.randrange(0, img.size[1]))
            if pix not in checked_pixels:
                checked_pixels.append(pix)
                break

        color = int(rgb_to_hex(img.getpixel(pix)), 16)

        char = 0  # unicode of symbol
        # get part of the symbol from the red canal
        # 00000111
        char |= (color & 0x70000) >> 11

        # get part of the symbol from the blue channel
        # 00000000 00000011 00000000
        char |= (color & 0x300) >> 5

        # get part of the symbol from the green channel
        # 00000000 00000000 00000111
        char |= color & 0x7

        if char > 130:  # Return Russian letters
            char += 890

        if char == 0:  # If the text is over
            break

        result += chr(char)

    random.seed()  # discard the seed

    return result
