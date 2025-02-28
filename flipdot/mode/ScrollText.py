from typing import ClassVar

from pydantic import PrivateAttr

from flipdot.DotMatrix import DotMatrix
from flipdot.mode.BaseDisplayMode import BaseDisplayMode, DisplayModeOptions
from flipdot.text import string_to_dots


class ScrollTextOptions(DisplayModeOptions):
    text: str = "Hi, Mom!"
    """The text to scroll across the screen."""

    font: str = "axion_6x7"
    """The font to use for the text."""


class ScrollText(BaseDisplayMode):
    """A display mode that scrolls text across the screen."""

    mode_name: ClassVar[str] = "scroll_text"
    Options: ClassVar[type[DisplayModeOptions]] = ScrollTextOptions

    tick_interval = 0.075

    opts: ScrollTextOptions = ScrollTextOptions()

    _buffer: DotMatrix = PrivateAttr()

    def setup(self) -> None:
        self._buffer = self.create_buffer(self.opts.text, self.opts.font)

    def create_buffer(self, text: str, font: str) -> DotMatrix:
        data = self.layout.middle(string_to_dots(text, font))
        data = data.hpad((self.layout.width, 0))
        return data

    def get_frame(self, frame_idx: int) -> DotMatrix:
        self._buffer = self._buffer << 1
        return DotMatrix(self._buffer.mat[:, : self.layout.width])
