from typing import ClassVar

import numpy as np

from flipdot.display_mode.BaseDisplayMode import StaticDisplayMode
from flipdot.types import DotMatrix


class Black(StaticDisplayMode):
    """Renders a persistent black frame."""

    mode_name: ClassVar[str] = "black"

    opts: StaticDisplayMode.Options = StaticDisplayMode.Options()

    def get_frame(self, frame_idx: int) -> DotMatrix:
        return np.zeros((self.layout.height, self.layout.width), dtype=np.uint8)


class White(StaticDisplayMode):
    """Renders a persistent white frame."""

    mode_name: ClassVar[str] = "white"

    opts: StaticDisplayMode.Options = StaticDisplayMode.Options()

    def get_frame(self, frame_idx: int) -> DotMatrix:
        return np.ones((self.layout.height, self.layout.width), dtype=np.uint8)
