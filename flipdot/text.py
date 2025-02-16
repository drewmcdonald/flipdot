from flipdot.DotMatrix import DotMatrix
from flipdot.font import get_font


def string_to_dots(text: str, font_name: str) -> DotMatrix:
    font = get_font(font_name)
    chars = font.get_chars(text)
    spaced_chars = DotMatrix.from_shape((font.line_height, 0))

    prev_char = chars[0]

    for char in chars:
        if char.char != " " and prev_char.char != " ":
            spaced_chars += font.char_space.dot_matrix
        spaced_chars += char.dot_matrix
        prev_char = char

    spaced_chars += font.char_space.dot_matrix  # trailing character space

    return spaced_chars
