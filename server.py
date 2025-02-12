import json
import pathlib
import sys

from dotenv import load_dotenv

from flipdot.create_app import create_app
from flipdot.display_mode import DisplayModeRef
from flipdot.vend.flippydot import Panel

load_dotenv()


server = create_app(
    Panel([[1], [2]]),
    default_mode=DisplayModeRef(name="clock"),
    debug=True,
)

# write the openapi schema
if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = json.dumps(server.openapi(), indent=2)
        pathlib.Path(sys.argv[1]).write_text(text)
