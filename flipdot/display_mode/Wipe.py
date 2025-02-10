from typing import ClassVar, Literal

import numpy as np
from pydantic import PrivateAttr

from flipdot.display_mode.BaseDisplayMode import BaseDisplayMode
from flipdot.types import DotMatrix


class Wipe(BaseDisplayMode):
    """A display mode that wipes a solid color across the screen."""

    mode_name: ClassVar[str] = "wipe"
    tick_interval = 0.1

    class Options(BaseDisplayMode.Options):
        direction: Literal["lr", "rl", "tb", "bt"] = "lr"
        """The direction to wipe across the screen."""

    opts: Options

    _buffer: DotMatrix = PrivateAttr()

    def setup(self) -> None:
        self._buffer = np.zeros((self.layout.height, self.layout.width), dtype=np.uint8)

    def get_frame(self, frame_idx: int) -> DotMatrix:
        if frame_idx % self.layout.width == 0:
            self.setup()

        idx = frame_idx % self.layout.width
        if self.opts.direction == "lr":
            self._buffer[:, idx] = 1  # type: ignore
        elif self.opts.direction == "rl":
            self._buffer[:, self.layout.width - idx] = 1  # type: ignore
        elif self.opts.direction == "tb":
            self._buffer[idx, :] = 1  # type: ignore
        elif self.opts.direction == "bt":
            self._buffer[self.layout.height - idx, :] = 1  # type: ignore

        return self._buffer
