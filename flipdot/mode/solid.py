from typing import ClassVar

from flipdot.DotMatrix import DotMatrix
from flipdot.mode.BaseDisplayMode import DisplayModeOptions, StaticDisplayMode


class Black(StaticDisplayMode):
    """Renders a persistent black frame."""

    mode_name: ClassVar[str] = "black"

    opts: DisplayModeOptions = DisplayModeOptions()

    def get_frame(self, frame_idx: int) -> DotMatrix:
        return DotMatrix.from_shape((self.layout.height, self.layout.width))


class White(StaticDisplayMode):
    """Renders a persistent white frame."""

    mode_name: ClassVar[str] = "white"

    opts: DisplayModeOptions = DisplayModeOptions()

    def get_frame(self, frame_idx: int) -> DotMatrix:
        return ~DotMatrix.from_shape((self.layout.height, self.layout.width))
