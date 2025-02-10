from dotenv import load_dotenv

from flipdot.create_app import create_app
from flipdot.display_mode import DisplayModeRef
from flipdot.display_mode.solid import Black, White
from flipdot.vend.flippydot import Panel

load_dotenv()


# # Optionally register custom display modes.
# # Example plugin (custom mode file provided by the user) might look like:
# from flipdot.display_mode import BaseDisplayMode, register_display_mode


# @register_display_mode
# class MyCustomMode(BaseDisplayMode):
#     mode_name = "flipFlop"

#     def get_frame(self, frame_idx: int):
#         if frame_idx % 2 == 0:
#             return White(layout=self.layout).get_frame(frame_idx)
#         else:
#             return Black(layout=self.layout).get_frame(frame_idx)


server = create_app(
    Panel([[1], [2]]), default_mode=DisplayModeRef(name="clock"), debug=True
)
