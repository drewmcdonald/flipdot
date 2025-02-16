import logging
import pathlib
from functools import lru_cache

import freetype  # type: ignore
import numpy as np
from pydantic import BaseModel

from flipdot.DotMatrix import DotMatrix

logger = logging.getLogger('uvicorn')


class DotChar:
    def __init__(
        self,
        char: str | None,
        dot_matrix: DotMatrix,
    ):
        self.char = char
        self.dot_matrix = dot_matrix
        self.height, self.width = dot_matrix.shape

    def __str__(self):
        return str(self.dot_matrix)

    def __repr__(self):
        return f"DotChar({self.char or '<char space>'})"


class DotFontRef(BaseModel):
    name: str
    line_height: int
    space_width: int
    width_between_chars: int


class DotFont:

    def __init__(
        self,
        font_path: pathlib.Path,
        src_height: int,
        space_width: int | None = None,
        width_between_chars: int | None = None,
        warm_cache: bool = True,
    ):
        self.face = freetype.Face(str(font_path))
        self.face.set_char_size(src_height * 64)

        # Get font metrics directly from face.size
        self.ascender = self.face.size.ascender // 64  # Ascender in pixels
        self.line_height = self.face.size.height // 64  # Line height in pixels

        self.space_width = space_width or (self.line_height // 2)
        self.width_between_chars = width_between_chars or (self.line_height // 3)

        self.char_space = DotChar(
            None,
            DotMatrix.from_shape((self.line_height, self.width_between_chars)),
        )
        self.space = DotChar(
            " ",
            DotMatrix.from_shape((self.line_height, self.space_width)),
        )
        # warm the cache of characters with basic alphanumeric characters
        if warm_cache:
            chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            self.get_chars(chars)

    @lru_cache(maxsize=100)  # noqa: B019
    def get_char(self, char: str) -> DotChar:
        if char == " ":
            return self.space

        # Check if the font supports the requested character
        if self.face.get_char_index(ord(char)) == 0:
            logger.warning(f"The font does not support input character '{char}'")
            char = "?"

        self.face.load_char(char, freetype.FT_LOAD_RENDER)  # type: ignore
        bitmap = self.face.glyph.bitmap

        bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape(
            (bitmap.rows, bitmap.width)
        )

        # Create a new blank canvas to fit the line height
        dots = DotMatrix.from_shape((self.line_height, bitmap.width))

        # Calculate vertical offset for centering
        top_offset = self.ascender - self.face.glyph.bitmap_top
        bottom_offset = top_offset + bitmap.rows

        # Ensure the glyph fits within the canvas
        if top_offset < 0 or bottom_offset > self.line_height:
            raise ValueError("Glyph exceeds the allocated line height.")

        # Place the bitmap in the centered array
        dots.mat[top_offset:bottom_offset, : bitmap.width] = bitmap_array

        # threshold at 0 since we assume dot matrix fonts
        return DotChar(
            char,
            DotMatrix((dots.mat > 0).astype(np.uint8)),
        )

    def get_chars(self, text: str) -> list[DotChar]:
        return [self.get_char(char) for char in text]

    def to_ref(self) -> DotFontRef:
        return DotFontRef(
            name=self.face.family_name,
            line_height=self.line_height,
            space_width=self.space_width,
            width_between_chars=self.width_between_chars,
        )
