from typing import TypeAlias

import numpy as np

# Type alias for NumPy array representing a dot matrix.
# Values are np.uint8, where 0 is off (black) and 1 (or any non-zero) is on (white).
NPDotArray: TypeAlias = np.typing.NDArray[np.uint8]


class DotMatrix:
    """
    Represents a 2D matrix of dots (pixels), typically for a flip-dot display.

    The matrix is stored as a NumPy array of unsigned 8-bit integers,
    where 0 represents an "off" dot and any non-zero value (typically 1)
    represents an "on" dot.
    """
    def __init__(self, mat: NPDotArray):
        """
        Initializes a DotMatrix with a given NumPy array.

        Args:
            mat: The NumPy array representing the dot matrix.
                 Values should be np.uint8, where 0 is off and 1 (or non-zero) is on.
        """
        self.mat = mat

    def clear(self):
        """Sets all dots in the matrix to the "off" state (0)."""
        self.mat.fill(0)

    def __str__(self):
        """
        Return a string representation of the dot matrix using characters.

        '⚪' represents an "on" dot.
        '⚫' represents an "off" dot.
        """
        return "\n" + "\n".join(
            "".join("⚪" if cell else "⚫" for cell in row) for row in self.mat
        )

    def __repr__(self):
        """
        Return a concise string representation of the DotMatrix instance,
        primarily showing its shape.
        """
        return f"DotMatrix(shape={self.shape})"

    @classmethod
    def from_shape(cls, shape: tuple[int, int]) -> "DotMatrix":
        """
        Creates a new DotMatrix filled with "off" dots (0s) of a given shape.

        Args:
            shape: A tuple (height, width) specifying the dimensions of the matrix.

        Returns:
            A new DotMatrix instance initialized with zeros.
        """
        return cls(np.zeros(shape, dtype=np.uint8))

    @property
    def shape(self) -> tuple[int, int]:
        """The dimensions (height, width) of the dot matrix."""
        return self.mat.shape # type: ignore

    @property
    def width(self) -> int:
        """The width (number of columns) of the dot matrix."""
        return self.mat.shape[1]

    @property
    def height(self) -> int:
        """The height (number of rows) of the dot matrix."""
        return self.mat.shape[0]

    def pad(
        self, pad_width: tuple[tuple[int, int], tuple[int, int]]
    ) -> "DotMatrix":
        """
        Pads the matrix with "off" dots (0s) on all sides.

        Args:
            pad_width: A tuple of tuples ((top_pad, bottom_pad), (left_pad, right_pad))
                       specifying the number of dots to add to each side.

        Returns:
            A new DotMatrix instance with the padding applied.
        """
        # Uses np.pad with default constant_values=0
        return DotMatrix(np.pad(self.mat, pad_width))

    def vpad(self, pad_width: tuple[int, int]) -> "DotMatrix":
        """
        Pads the matrix vertically (top and bottom) with "off" dots (0s).

        Args:
            pad_width: A tuple (top_pad, bottom_pad) specifying the padding.

        Returns:
            A new DotMatrix instance with vertical padding.
        """
        return self.pad((pad_width, (0, 0)))

    def hpad(self, pad_width: tuple[int, int]) -> "DotMatrix":
        """
        Pads the matrix horizontally (left and right) with "off" dots (0s).

        Args:
            pad_width: A tuple (left_pad, right_pad) specifying the padding.

        Returns:
            A new DotMatrix instance with horizontal padding.
        """
        return self.pad(((0, 0), pad_width))

    def split(self, indices_or_sections: int | np.ndarray, axis: int) -> list["DotMatrix"]:
        """
        Splits the DotMatrix into multiple sub-matrices.

        This is a wrapper around np.split.

        Args:
            indices_or_sections: If an integer, N, the array will be divided into N equal
                                 arrays along axis. If such a split is not possible,
                                 an error is raised.
                                 If a 1-D array of sorted integers, the entries
                                 indicate where along axis the array is split.
            axis: The axis along which to split, 0 for vertical, 1 for horizontal.

        Returns:
            A list of new DotMatrix instances.
        """
        return [DotMatrix(mat) for mat in np.split(self.mat, indices_or_sections, axis=axis)]

    def __add__(self, other: "DotMatrix") -> "DotMatrix":
        """
        Concatenates this DotMatrix with another horizontally (side-by-side).

        Args:
            other: The DotMatrix to append to the right of this one.

        Returns:
            A new DotMatrix representing the horizontal concatenation.
        """
        return DotMatrix(np.concatenate([self.mat, other.mat], axis=1))

    def __iadd__(self, other: "DotMatrix") -> "DotMatrix":
        """
        In-place concatenates this DotMatrix with another horizontally.

        Args:
            other: The DotMatrix to append to the right of this one.

        Returns:
            This DotMatrix instance after modification.
        """
        self.mat = np.concatenate([self.mat, other.mat], axis=1)
        return self

    def __rshift__(self, amount: int) -> "DotMatrix":
        """
        Rolls the DotMatrix columns to the right by a given amount.

        Dots shifted off the right edge reappear on the left.

        Args:
            amount: The number of columns to roll to the right.

        Returns:
            A new DotMatrix with its columns rolled.
        """
        return DotMatrix(np.roll(self.mat, amount, axis=1))

    def __irshift__(self, amount: int) -> "DotMatrix":
        """
        In-place rolls the DotMatrix columns to the right by a given amount.

        Args:
            amount: The number of columns to roll to the right.

        Returns:
            This DotMatrix instance after modification.
        """
        self.mat = np.roll(self.mat, amount, axis=1)
        return self

    def __lshift__(self, amount: int) -> "DotMatrix":
        """
        Rolls the DotMatrix columns to the left by a given amount.

        Dots shifted off the left edge reappear on the right.

        Args:
            amount: The number of columns to roll to the left.

        Returns:
            A new DotMatrix with its columns rolled.
        """
        return DotMatrix(np.roll(self.mat, -amount, axis=1))

    def __ilshift__(self, amount: int) -> "DotMatrix":
        """
        In-place rolls the DotMatrix columns to the left by a given amount.

        Args:
            amount: The number of columns to roll to the left.

        Returns:
            This DotMatrix instance after modification.
        """
        self.mat = np.roll(self.mat, -amount, axis=1)
        return self

    def __invert__(self) -> "DotMatrix":
        """
        Inverts the DotMatrix, turning "on" dots "off" and vice-versa.

        Assumes "on" is 1 and "off" is 0. The underlying numpy operation `~`
        will flip bits (0 to 255, 1 to 254 for uint8). For boolean context
        (like in `__str__`), non-zero is "on". If a strict 0/1 representation
        is needed after inversion, further processing might be required.
        However, for typical flip-dot displays, any non-zero is usually "on".

        Returns:
            A new DotMatrix with its dots inverted.
        """
        # For uint8, ~0 is 255 (all bits set), ~1 is 254.
        # Both will evaluate to True in a boolean context, effectively being "on".
        # If strict 0 and 1 values are required, one might do `(self.mat == 0).astype(np.uint8)`.
        # However, the current implementation is simpler and often sufficient.
        return DotMatrix(~self.mat)
