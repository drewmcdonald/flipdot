from flipdot.DotMatrix import DotMatrix
from flipdot.font import get_font


def string_to_dots(text: str, font_name: str) -> DotMatrix:
    """
    Converts a string of text into a DotMatrix representation using a specified font.

    The function renders each character from the input text using the given font
    and concatenates them horizontally to form a single DotMatrix.
    Spacing is added between characters based on the font's `char_space`
    definition, but not adjacent to actual space characters from the input text.
    A trailing space is also added at the end of the entire text.

    Args:
        text: The input string to convert.
        font_name: The name of the font to use for rendering (e.g., "telematrix").

    Returns:
        A DotMatrix object representing the rendered text.
        Returns an empty DotMatrix (height of font, width 0) if the input text is empty.
    """
    font = get_font(font_name)
    if not text:
        # Return an empty matrix with the correct height if the input string is empty
        return DotMatrix.from_shape((font.line_height, 0))

    chars = font.get_chars(text)
    # Initialize an empty DotMatrix with the font's line height and zero width.
    # This will serve as the canvas to append character matrices.
    spaced_chars = DotMatrix.from_shape((font.line_height, 0))

    # Keep track of the previous character to manage spacing.
    # Initialize with the first character; its spacing logic is handled implicitly
    # as there's no "previous" character before it to add space for.
    prev_char = chars[0]

    first_char_processed = False
    for char_obj in chars:
        # Add inter-character spacing if:
        # 1. This is not the very first character being added.
        # 2. The current character is not a space.
        # 3. The previous character was not a space.
        # This prevents adding space before the first char, or around explicit space chars.
        if first_char_processed and char_obj.char != " " and prev_char.char != " ":
            spaced_chars += font.char_space.dot_matrix
        
        spaced_chars += char_obj.dot_matrix
        prev_char = char_obj
        first_char_processed = True

    # Add a trailing character space at the very end of the text representation,
    # unless the original text was empty (handled above).
    spaced_chars += font.char_space.dot_matrix

    return spaced_chars
