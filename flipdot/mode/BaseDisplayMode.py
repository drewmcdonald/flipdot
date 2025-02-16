from abc import abstractmethod
from typing import ClassVar

from pydantic import BaseModel, PrivateAttr

from flipdot.DotMatrix import DotMatrix
from flipdot.layout import Layout


class DisplayModeRef(BaseModel):
    """A reference to a display mode."""

    mode_name: str
    """The name of the display mode."""

    opts: dict | None = None
    """The options of the display mode."""


class BaseDisplayMode(BaseModel):
    """Base class for all display modes."""

    tick_interval: ClassVar[float] = 1
    """The number of seconds to pause between frames."""

    mode_name: ClassVar[str]
    """The name of the display mode."""

    layout: Layout
    """The layout of the display mode."""

    class Options(BaseModel):
        """A pydantic model for the options of the display mode."""

        class Config:
            arbitrary_types_allowed = True

    opts: Options
    """The options of the display mode."""

    _frame_idx: int = PrivateAttr(0)
    """The index of the frame to render."""

    class Config:
        arbitrary_types_allowed = True

    def should_render(self) -> bool:
        """Whether the display mode should render a new frame."""
        return True

    def reset(self) -> None:
        """Reset the display mode."""
        self._frame_idx = 0

    def setup(self) -> None:
        """
        Setup the display mode; runs after initialization and before the first
        render.
        """
        pass

    def render(self) -> DotMatrix:
        """Render the display."""
        frame = self.get_frame(self._frame_idx)
        self._frame_idx += 1
        return frame

    @abstractmethod
    def get_frame(self, frame_idx: int) -> DotMatrix:
        """Generate the Dotmatrix frame for the given frame index"""

    def to_ref(self) -> DisplayModeRef:
        """Convert the display mode to a DisplayModeRef."""
        return DisplayModeRef(mode_name=self.mode_name, opts=self.opts.model_dump())


class StaticDisplayMode(BaseDisplayMode):
    """Renders a static frame once."""

    _did_render: bool = PrivateAttr(False)

    def should_render(self) -> bool:
        if not self._did_render:
            self._did_render = True
            return True
        return False
