"""
Adapted from https://github.com/chrishemmings/flipPyDot at 12d597a
"""

from typing import Any

import numpy as np

from flipdot.DotMatrix import NPDotArray

START_BYTES_FLUSH = bytearray([0x80, 0x83])
START_BYTES_BUFFER = bytearray([0x80, 0x84])
END_BYTES = bytearray([0x8F])


def shape2d(a: list[list[Any]]) -> tuple[int, int]:
    return len(a), len(a[0])


class FlippyModule:

    def __init__(self, width: int, height: int, address: int):
        self.width = width
        self.height = height
        self.address = address
        self.content: NPDotArray = np.zeros((self.height, self.width), dtype=np.uint8)
        self.content[2][1] = 0x01

    def set_content(self, content: NPDotArray):
        self.content = content

    def fetch_serial_command(self, flush=True) -> np.ndarray:
        return np.array(
            np.concatenate(
                (
                    START_BYTES_FLUSH if flush else START_BYTES_BUFFER,
                    [self.address],
                    np.packbits(self.content, axis=0, bitorder='little').squeeze(),
                    END_BYTES,
                )
            ),
            dtype=np.uint8,
        )


class Panel:

    def __init__(
        self,
        layout: list[list[int]],
        module_width: int = 28,
        module_height: int = 7,
    ):
        """
        :param layout: An array structure of the panel layout with panel id's
        :param module_width: Module width, normally 28
        :param module_height: Module height, normally 7
        """
        self.modules: list[list[FlippyModule]] = []

        if len(shape2d(layout)) != 2:
            raise Exception("panel layout does not equate to a rectangle/square")

        self.n_rows, self.n_cols = shape2d(layout)
        self.module_width = module_width
        self.module_height = module_height

        for row in layout:
            module_row: list[FlippyModule] = []
            if len(row) != self.n_cols:
                raise Exception("panel layout does not equate to a rectangle/square")

            for address in row:
                module_row.append(FlippyModule(module_width, module_height, address))

            self.modules.append(module_row)

        self.total_width = self.module_width * self.n_cols
        self.total_height = self.module_height * self.n_rows

    @property
    def dimensions(self) -> tuple[int, int]:
        return self.total_height, self.total_width

    def get_content(self) -> NPDotArray:
        rows = [
            np.concatenate([module.content for module in module_row], axis=1)
            for module_row in self.modules
        ]
        return np.concatenate(rows, axis=0)

    def set_content(self, matrix_data: NPDotArray) -> bytearray:

        for i, row in enumerate(np.split(matrix_data, self.n_rows, 0)):
            modules = np.split(row, self.n_cols, 1)

            for j, module_data in enumerate(modules):
                self.modules[i][j].set_content(module_data)

        serial_data = np.array([])

        for moduleRow in self.modules:
            for module in moduleRow:
                output = module.fetch_serial_command()
                serial_data = np.append(serial_data, output.view('S32').squeeze())

        return bytearray(serial_data.tobytes())
