import os
import time

import cv2
import numpy as np
from flippydot import Panel  # type: ignore

from flipdot.font import fonts
from flipdot.text import string_to_dots
from flipdot.util import prettify_dot_matrix

# Configure our FlipDot panel
panel = Panel(
    [[1], [2]],  # vertical stack of two horizontal modules
    module_width=28,
    module_height=7,
    module_rotation=0,
)

width, height = panel.get_total_width(), panel.get_total_height()

frame_delay = 0.01

cv2.namedWindow("x", cv2.WINDOW_NORMAL)


def draw():
    panel_content = panel.get_content()
    cv2.imshow('x', np.uint8(panel_content * 255))  # type: ignore
    cv2.resizeWindow("x", 10 * width, 10 * height)
    cv2.waitKey(1)


data = string_to_dots("Hello", fonts.axion_6x7)

# Calculate padding for vertical dimension
pad_vert = height - data.shape[0]
pad_bottom = pad_vert // 2
pad_top = pad_vert - pad_bottom

pad_horiz = width - data.shape[1]

# pad data up to the dimensions of the panel
data = np.pad(
    data,
    (
        (pad_top, pad_bottom),
        (width, min(width, data.shape[1])),
    ),
)


frame = 0
buffer = np.zeros((height, width), dtype=np.uint8)
while frame < (data.shape[1] - width):
    buffer = data[:, frame : frame + width]
    os.system("clear")
    print(prettify_dot_matrix(buffer))
    panel.apply_frame(buffer)
    draw()
    frame += 1
    time.sleep(frame_delay)
