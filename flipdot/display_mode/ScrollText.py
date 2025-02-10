from typing import ClassVar

import numpy as np
from pydantic import PrivateAttr

from flipdot.display_mode.BaseDisplayMode import BaseDisplayMode
from flipdot.text import string_to_dots
from flipdot.types import DotMatrix


class ScrollText(BaseDisplayMode):
    """A display mode that scrolls text across the screen."""

    mode_name: ClassVar[str] = "scroll_text"

    tick_interval = 0.05

    class Options(BaseDisplayMode.Options):
        text: str = "Hi, Mom!"
        """The text to scroll across the screen."""

        font: str = "axion_6x7"
        """The font to use for the text."""

    opts: Options

    _buffer: DotMatrix = PrivateAttr()
    _text_width: int = PrivateAttr()

    def setup(self) -> None:
        self._buffer, self._text_width = self.create_buffer(
            self.opts.text, self.opts.font
        )

    def create_buffer(self, text: str, font: str) -> tuple[DotMatrix, int]:
        data = self.layout.middle(string_to_dots(text, font))
        text_width = data.shape[1]
        data: DotMatrix = np.pad(data, ((0, 0), (self.layout.width, self.layout.width)))  # type: ignore
        return data, text_width

    def get_frame(self, frame_idx: int) -> DotMatrix:
        if frame_idx == self._text_width + self.layout.width:
            self.reset()
        frame: DotMatrix = self._buffer[:, frame_idx : frame_idx + self.layout.width]  # type: ignore
        return frame
