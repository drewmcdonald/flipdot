from typing import ClassVar

import numpy as np

from flipdot.DotMatrix import DotMatrix
from flipdot.mode.Clock import Clock


class DotClock(Clock):
    """Displays the current time as dots."""

    mode_name: ClassVar[str] = "dotclock"

    @staticmethod
    def hour_cols(hour: int) -> DotMatrix:
        hours = []
        for i in range(12):
            hours.append([int(i < hour), int((i + 12) < hour)])
        return DotMatrix(np.array(hours, dtype=np.uint8))

    @staticmethod
    def minute_cols(minute: int) -> DotMatrix:
        minutes = []
        for i in range(12):
            minutes.append([int(i * 5 + j < minute) for j in range(5)])
        return DotMatrix(np.array(minutes, dtype=np.uint8))

    def get_frame(self, frame_idx: int) -> DotMatrix:
        now = self.now()
        hour_cols = self.hour_cols(now.hour)
        space_col = DotMatrix.from_shape((12, 1))
        minute_cols = self.minute_cols(now.minute)
        self._last_rendered_minute = now.minute
        return self.layout.center_middle(hour_cols + space_col + minute_cols)
