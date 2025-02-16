from datetime import datetime, timedelta, timezone
from typing import ClassVar

from pydantic import PrivateAttr

from flipdot.DotMatrix import DotMatrix
from flipdot.mode.BaseDisplayMode import BaseDisplayMode
from flipdot.text import string_to_dots


class Clock(BaseDisplayMode):
    """A display mode that displays the current time."""

    mode_name: ClassVar[str] = "clock"
    _last_rendered_minute: int = PrivateAttr(-1)
    """The last rendered minute."""

    class Options(BaseDisplayMode.Options):
        font: str = "axion_6x7"
        timezone_offset: int = -5

    opts: Options

    def now(self) -> datetime:
        return datetime.now(timezone(timedelta(hours=self.opts.timezone_offset)))

    def should_render(self) -> bool:
        return self._last_rendered_minute != self.now().minute

    def get_frame(self, frame_idx: int) -> DotMatrix:
        now = self.now()
        dots = self.layout.center_middle(
            string_to_dots(now.strftime("%-I:%M"), self.opts.font)
        )
        self._last_rendered_minute = now.minute
        return dots
