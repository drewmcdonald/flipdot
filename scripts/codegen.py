#! /usr/bin/env python3

import json
import os
import pathlib
import subprocess

from flipdot.create_app import create_app
from flipdot.vend.flippydot import Panel

if __name__ == "__main__":

    server = create_app(Panel([[1]]))
    text = json.dumps(server.openapi(), indent=2)
    pathlib.Path("flipdot/server_schema.json").write_text(text)

    os.chdir("frontend")
    subprocess.run(
        [
            "bunx",
            "openapi-typescript",
            "../flipdot/server_schema.json",
            "-o",
            "./src/api/schema.d.ts",
        ]
    )
    os.chdir("..")
