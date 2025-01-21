import time

import numpy as np
from flippydot import Panel  # type: ignore

from flipdot.font import fonts
from flipdot.layout import Layout
from flipdot.text import string_to_dots
from flipdot.util import prettify_dot_matrix

panel = Panel(
    [[1], [2]],  # vertical stack of two horizontal modules
    module_width=28,
    module_height=7,
    module_rotation=0,
)

width, height = panel.get_total_width(), panel.get_total_height()
layout = Layout(width, height)

font = fonts.axion_6x7


rendered_min = 99  # force initial render

while True:
    t = time.localtime()

    if rendered_min == t.tm_min:
        time.sleep(1)
        continue

    rendered_min = t.tm_min
    time_data = layout.top(string_to_dots(time.strftime("%H:%M", t), font))
    pm_data = layout.right(layout.bottom(string_to_dots("pm", font)))

    # blend the two together by keeping 1 if either is 1
    data = np.maximum(time_data, pm_data)
    panel.apply_frame(data)

    # os.system("clear")
    print(prettify_dot_matrix(data))
    # delay longer after updating once a minute
    time.sleep(55)
