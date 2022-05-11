import random
from hashlib import sha256
from io import BytesIO

from PIL import Image


def get_seed(key: str) -> str:
    """
    Шифрует ключ.
    Используется как сид при дальнейшей генерации случайных чисел
     для получения случайных пикселей.
    :param key: Секретный ключ.
    :return: Сид для случайных чисел.
    """
    return sha256(key.encode()).hexdigest()  # Используем хэш-функция sha256


def char_to_bits(char_number: int) -> tuple[str, str, str]:
    """
    Конвертирует юникод число символа в двоичную систему счисления.
    :param char_number: Юникод число.
    :return: Двоичное представление символа.
    example:
        >>> char_to_bits(ord('F'))
        ('010', '00', '110')
    """
    bits = "{0:b}".format(char_number).rjust(8, "0")
    return bits[:3], bits[3:5], bits[5:]


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """
    Конвертирует RGB представление цвета в шестнадцатеричное.
    :param rgb: RGB цвет.
    :return: Шестнадцатеричное представление цвета.
    """
    return "0x{:02x}{:02x}{:02x}".format(*rgb)


def color_number_to_bits(color_number: int) -> tuple[str, str, str]:
    """
    Конвертирует десятеричное представление цвета в двоичное.
    :param color_number: Десятеричное представление цвета.
    :return: Двоичное представление цвета.
    example:
        >>> color_number_to_bits(int(rgb_to_hex((255, 1, 55)), 16))
        ('11111111', '00000001', '00110111')
    """
    bits = "{0:b}".format(color_number).rjust(24, "0")
    return bits[0:8], bits[8:16], bits[16:]


def color_number_to_rgb(color_number: int) -> tuple[int, int, int]:
    """
    Конвертирует десятеричное представление цвета в RGB.
    :param color_number: десятеричное представление цвета.
    :return: RGB представление цвета.
    """
    bits = color_number_to_bits(color_number)
    return int(bits[0], 2), int(bits[1], 2), int(bits[2], 2)


def encrypt(text: str, key: str, image: BytesIO) -> Image:
    """
    Шифрует текст в картинке.

    Алгоритм:
        Секретный ключ шифруется и используется в качестве сида
        для генератора псевдослучайных чисел.
        Алгоритм получает псевдослучайный пиксель, и последние биты RGB цвета
        заменяет на биты шифруемого символа.

    :param text: Текст для шифровки.
    :param key: Секретный ключ.
    :param image: Исходная картинка.
    :return: Картинка с зашифрованным текстом.
    :raise: RuntimeError.

    example:
        >>> import io
        >>> with open(file_path, 'rb') as file:  # noqa
        ...     data = file.read()
        >>> img = encrypt(text, key, io.BytesIO(data))  # noqa
        >>> img.save(target_file_path)  # noqa

    example:
        >>> import io
        >>> import requests  # noqa
        >>> data = requests.get(img_url).content  # noqa
        >>> img = encrypt(text, key, io.BytesIO(data))  # noqa
        >>> img.save(target_file_path)  # noqa
    """
    img = Image.open(image).convert("RGB")  # Загружаем изображение
    img_size = img.size[0] * img.size[1]  # Кол-во пикселей

    if not len(text):
        raise RuntimeError("Нет текста")
    elif len(text) >= img_size:
        raise RuntimeError("Картинка слишком маленькая")

    text += "\0"  # Знак того, что текст закончился. Нужно для дешифровки
    used_pixels: list[tuple[int, int]] = []  # Пиксели в которые уже зашифрован символ.
    random.seed(get_seed(key))  # Устанавливаем сид

    for i, char in enumerate(text):  # Перебираем символы в тексте.
        # Поиск свободного пикселя
        while True:
            # Получение псевдослучайного пикселя
            pix = (random.randrange(0, img.size[0]), random.randrange(0, img.size[1]))
            if pix not in used_pixels:  # Если он не занят
                used_pixels.append(pix)
                break

        char = ord(char)  # Юникод значение символа
        # Костыль для русских букв(Потому что их юникод значение слишком большое)
        if char > 1000:
            char -= 890

        color = int(rgb_to_hex(img.getpixel(pix)), 16)  # Исходный цвет пикселя

        # Вшиваем часть символа в последние 3 бита красного канала
        new_color = color & 0xF80000  # 11111000 00000000 00000000
        new_color |= (char & 0xE0) << 11  # 00000111 00000000 00000000

        # Вшиваем часть символа в последние 2 бита синего канала
        new_color |= color & (0x3F << 10)  # 00000000 11111100 00000000
        new_color |= (char & 0x18) << 5  # 00000000 00000011 00000000

        # Вшиваем часть символа в последние 3 бита зеленого канала
        new_color |= color & (0x1F << 3)  # 00000000 00000000 11111000
        new_color |= char & 0x7  # 00000000 00000000 00000111

        img.putpixel(
            pix, color_number_to_rgb(new_color)
        )  # Изменяем пиксель на картинке

    random.seed()  # Сбрасываем сид

    return img


def decrypt(key: str, image: BytesIO) -> str:
    """
    Декодирует сообщение из картинки.
    Алгоритм противоположный шифрованию.

    :param key: Секретный ключ.
    :param image: Картинка.
    :return: Текст.
    """
    img = Image.open(image).convert("RGB")

    random.seed(get_seed(key))  # Устанавливаем сид
    result = ""  # Расшифрованный текст
    checked_pixels: list[tuple[int, int]] = []  # Проверенные пиксели

    while True:
        # Поиск пикселя
        while True:
            # Получение псевдослучайного пикселя
            pix = (random.randrange(0, img.size[0]), random.randrange(0, img.size[1]))
            if pix not in checked_pixels:  # Если он не проверен
                checked_pixels.append(pix)
                break

        color = int(rgb_to_hex(img.getpixel(pix)), 16)  # Цвет пикселя

        char = 0  # Юникод значение символа
        # Получаем часть символа из красного канала
        # 00000111
        char |= (color & 0x70000) >> 11

        # Получаем часть символа из синего канала
        # 00000000 00000011 00000000
        char |= (color & 0x300) >> 5

        # Получаем часть символа из зеленого канала
        # 00000000 00000000 00000111
        char |= color & 0x7

        if char > 130:  # Возвращаем русские буквы
            char += 890

        if char == 0:  # Если текст закончился
            break

        result += chr(char)

    random.seed()  # Сбрасываем сид

    return result
