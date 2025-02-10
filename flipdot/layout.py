import numpy as np
from pydantic import BaseModel

from flipdot.types import DotMatrix
from flipdot.vend.flippydot import Panel


class Layout(BaseModel):
    width: int
    height: int

    @classmethod
    def from_panel(cls, panel: Panel) -> "Layout":
        return cls(width=panel.total_width, height=panel.total_height)

    def middle(self, data: DotMatrix, bias_top=True) -> DotMatrix:
        pad_vert = max(self.height - data.shape[0], 0)
        pad_major = pad_vert // 2
        pad_minor = pad_vert - pad_major

        padding = (pad_major, pad_minor) if bias_top else (pad_minor, pad_major)
        return _typed_pad(data, (padding, (0, 0)))

    def center(self, data: DotMatrix, bias_left=True) -> DotMatrix:
        pad_horiz = max(self.width - data.shape[1], 0)
        pad_major = pad_horiz // 2
        pad_minor = pad_horiz - pad_major

        padding = (pad_major, pad_minor) if bias_left else (pad_minor, pad_major)
        return _typed_pad(data, ((0, 0), padding))

    def center_middle(
        self, data: DotMatrix, bias_top=True, bias_left=True
    ) -> DotMatrix:
        return self.center(self.middle(data, bias_left), bias_top)

    def top(self, data: DotMatrix) -> DotMatrix:
        pad = max(self.height - data.shape[0], 0)
        return _typed_pad(data, ((0, pad), (0, 0)))

    def bottom(self, data: DotMatrix) -> DotMatrix:
        pad_top = max(self.height - data.shape[0], 0)
        return _typed_pad(data, ((pad_top, 0), (0, 0)))

    def left(self, data: DotMatrix) -> DotMatrix:
        pad_right = max(self.width - data.shape[1], 0)
        return _typed_pad(data, ((0, 0), (0, pad_right)))

    def right(self, data: DotMatrix) -> DotMatrix:
        pad_left = max(self.width - data.shape[1], 0)
        return _typed_pad(data, ((0, 0), (pad_left, 0)))


def _typed_pad(
    data: DotMatrix, pad: tuple[tuple[int, int], tuple[int, int]]
) -> DotMatrix:
    return np.pad(data, pad)  # type: ignore
