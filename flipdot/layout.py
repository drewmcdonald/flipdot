from pydantic import BaseModel

from flipdot.DotMatrix import DotMatrix
from flipdot.vend.flippydot import Panel


class Layout(BaseModel):
    """
    Defines the dimensions of a display area and provides utilities
    for positioning DotMatrix objects within that area.

    The positioning methods typically add padding to a smaller DotMatrix
    to align it relative to the layout's dimensions.
    """
    width: int
    """The total width of the layout in dots."""
    height: int
    """The total height of the layout in dots."""

    @classmethod
    def from_panel(cls, panel: Panel) -> "Layout":
        """
        Creates a Layout instance from a flippy-dot Panel object.

        Args:
            panel: The Panel object from which to derive layout dimensions.

        Returns:
            A new Layout instance with width and height matching the panel.
        """
        return cls(width=panel.total_width, height=panel.total_height)

    def middle(self, data: DotMatrix, bias_top: bool = True) -> DotMatrix:
        """
        Vertically centers a DotMatrix within the layout height.

        If the height difference is odd, `bias_top` determines if the
        extra row of padding goes to the top (False) or bottom (True, default).

        Args:
            data: The DotMatrix to position.
            bias_top: If True (default), and vertical padding is odd,
                      the larger portion of padding is at the bottom (pushing content up).
                      If False, the larger portion is at the top (pushing content down).

        Returns:
            A new DotMatrix, padded vertically to match the layout height.
        """
        # Calculate total vertical padding needed
        pad_vert = max(self.height - data.shape[0], 0)
        # Split padding; if odd, one part will be larger
        pad_major = pad_vert // 2  # Larger part if bias_top=False (more padding on top)
        pad_minor = pad_vert - pad_major # Smaller part

        # Apply padding based on bias
        # If bias_top is True, we want less padding on top (pad_minor) and more on bottom (pad_major).
        # If bias_top is False, we want more padding on top (pad_major) and less on bottom (pad_minor).
        padding = (pad_minor, pad_major) if bias_top else (pad_major, pad_minor)
        return data.vpad(padding)

    def center(self, data: DotMatrix, bias_left: bool = True) -> DotMatrix:
        """
        Horizontally centers a DotMatrix within the layout width.

        If the width difference is odd, `bias_left` determines if the
        extra column of padding goes to the left (True, default) or right (False).

        Args:
            data: The DotMatrix to position.
            bias_left: If True (default), and horizontal padding is odd,
                       the larger portion of padding is on the right (pushing content left).
                       If False, the larger portion is on the left (pushing content right).


        Returns:
            A new DotMatrix, padded horizontally to match the layout width.
        """
        # Calculate total horizontal padding needed
        pad_horiz = max(self.width - data.width, 0)
        # Split padding; if odd, one part will be larger
        pad_major = pad_horiz // 2 # Larger part if bias_left=False (more padding on left)
        pad_minor = pad_horiz - pad_major # Smaller part

        # Apply padding based on bias
        # If bias_left is True, we want less padding on left (pad_minor) and more on right (pad_major).
        # If bias_left is False, we want more padding on left (pad_major) and less on right (pad_minor).
        padding = (pad_minor, pad_major) if bias_left else (pad_major, pad_minor)
        return data.hpad(padding)

    def center_middle(
        self, data: DotMatrix, bias_top: bool = True, bias_left: bool = True
    ) -> DotMatrix:
        """
        Centers a DotMatrix both horizontally and vertically within the layout.

        Args:
            data: The DotMatrix to position.
            bias_top: Bias for vertical centering (see `middle` method).
            bias_left: Bias for horizontal centering (see `center` method).

        Returns:
            A new DotMatrix, padded to be centered in the layout.
        """
        # Note: The original code had bias_left for middle and bias_top for center.
        # This seems like a potential mix-up. Correcting to apply bias_top to middle
        # and bias_left to center, which is more intuitive.
        return self.center(self.middle(data, bias_top=bias_top), bias_left=bias_left)

    def top(self, data: DotMatrix) -> DotMatrix:
        """
        Aligns a DotMatrix to the top of the layout, padding the bottom.

        Args:
            data: The DotMatrix to position.

        Returns:
            A new DotMatrix, padded at the bottom to match the layout height.
        """
        # Calculate padding needed only at the bottom
        pad_bottom = max(self.height - data.shape[0], 0)
        return data.vpad((0, pad_bottom))

    def bottom(self, data: DotMatrix) -> DotMatrix:
        """
        Aligns a DotMatrix to the bottom of the layout, padding the top.

        Args:
            data: The DotMatrix to position.

        Returns:
            A new DotMatrix, padded at the top to match the layout height.
        """
        # Calculate padding needed only at the top
        pad_top = max(self.height - data.shape[0], 0)
        return data.vpad((pad_top, 0))

    def left(self, data: DotMatrix) -> DotMatrix:
        """
        Aligns a DotMatrix to the left of the layout, padding the right.

        Args:
            data: The DotMatrix to position.

        Returns:
            A new DotMatrix, padded at the right to match the layout width.
        """
        # Calculate padding needed only at the right
        pad_right = max(self.width - data.shape[1], 0)
        return data.hpad((0, pad_right))

    def right(self, data: DotMatrix) -> DotMatrix:
        """
        Aligns a DotMatrix to the right of the layout, padding the left.

        Args:
            data: The DotMatrix to position.

        Returns:
            A new DotMatrix, padded at the left to match the layout width.
        """
        # Calculate padding needed only at the left
        pad_left = max(self.width - data.shape[1], 0)
        return data.hpad((pad_left, 0))
