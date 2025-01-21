import logging

import numpy as np

from flipdot.types import DotMatrix

from .font import DotFont, fonts
from .util import prettify_dot_matrix

logger = logging.getLogger(__name__)


def string_to_dots(text: str, font: DotFont) -> DotMatrix:
    chars = font.get_chars(text)
    spaced_chars = []

    prev_char = chars[0]

    for char in chars:
        if char.char != " " and prev_char.char != " ":
            spaced_chars.append(font.char_space)
        spaced_chars.append(char)
        prev_char = char

    spaced_chars.append(font.char_space)  # trailing character space

    return np.concatenate([char.dot_matrix for char in spaced_chars], axis=1)


if __name__ == "__main__":
    import sys

    dots = string_to_dots(sys.argv[1], fonts.axion_6x7)
    print(prettify_dot_matrix(dots))
