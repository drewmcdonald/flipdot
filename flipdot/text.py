import numpy as np

from flipdot.font import get_font
from flipdot.types import DotMatrix


def string_to_dots(text: str, font_name: str) -> DotMatrix:
    font = get_font(font_name)
    chars = font.get_chars(text)
    spaced_chars = []

    prev_char = chars[0]

    for char in chars:
        if char.char != " " and prev_char.char != " ":
            spaced_chars.append(font.char_space)
        spaced_chars.append(char)
        prev_char = char

    spaced_chars.append(font.char_space)  # trailing character space

    return np.concatenate([char.dot_matrix for char in spaced_chars], axis=1)  # type: ignore
