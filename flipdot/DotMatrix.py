from typing import TypeAlias

import numpy as np

NPDotArray: TypeAlias = np.typing.NDArray[np.uint8]


class DotMatrix:
    def __init__(self, mat: NPDotArray):
        self.mat = mat

    def clear(self):
        self.mat.fill(0)

    def __str__(self):
        """Return a string representation of the dot matrix."""
        return "\n" + "\n".join(
            "".join("⚪" if cell else "⚫" for cell in row) for row in self.mat
        )

    def __repr__(self):
        """Return a string representation of the dot matrix."""
        return f"DotMatrix(shape={self.shape})"

    @classmethod
    def from_shape(cls, shape: tuple[int, int]) -> "DotMatrix":
        return cls(np.zeros(shape, dtype=np.uint8))

    @property
    def shape(self):
        return self.mat.shape

    @property
    def width(self):
        return self.mat.shape[1]

    @property
    def height(self):
        return self.mat.shape[0]

    def pad(self, pad: tuple[tuple[int, int], tuple[int, int]]) -> "DotMatrix":
        return DotMatrix(np.pad(self.mat, pad))

    def vpad(self, pad: tuple[int, int]) -> "DotMatrix":
        return self.pad((pad, (0, 0)))

    def hpad(self, pad: tuple[int, int]) -> "DotMatrix":
        return self.pad(((0, 0), pad))

    def split(self, width: int, axis: int) -> list["DotMatrix"]:
        return [DotMatrix(mat) for mat in np.split(self.mat, width, axis)]

    def __add__(self, other: "DotMatrix") -> "DotMatrix":
        return DotMatrix(np.concatenate([self.mat, other.mat], axis=1))

    def __iadd__(self, other: "DotMatrix") -> "DotMatrix":
        self.mat = np.concatenate([self.mat, other.mat], axis=1)
        return self

    def __rshift__(self, other: int) -> "DotMatrix":
        return DotMatrix(np.roll(self.mat, other, axis=1))

    def __irshift__(self, other: int) -> "DotMatrix":
        self.mat = np.roll(self.mat, other, axis=1)
        return self

    def __lshift__(self, other: int) -> "DotMatrix":
        return DotMatrix(np.roll(self.mat, -other, axis=1))

    def __ilshift__(self, other: int) -> "DotMatrix":
        self.mat = np.roll(self.mat, -other, axis=1)
        return self

    def __invert__(self) -> "DotMatrix":
        return DotMatrix(~self.mat)
