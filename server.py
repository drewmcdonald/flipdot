import asyncio
import json

import click
import serial
from dotenv import load_dotenv

from flipdot.create_app import create_app
from flipdot.vend.flippydot import Panel

load_dotenv()


@click.command("run")
@click.option("--layout", type=str, default='[[1], [2]]')
@click.option("--device", type=str, default=None, required=False)
@click.option("--baudrate", type=int, default=57600)
@click.option("--host", type=str, default="0.0.0.0")
@click.option("--port", type=int, default=8080)
@click.option("--dev", is_flag=True)
def run(layout: str, device: str, baudrate: int, host: str, port: int, dev: bool):
    """
    Synchronous wrapper for the asynchronous run command.
    """
    asyncio.run(run_async(layout, device, baudrate, host, port, dev))


async def run_async(
    layout: str, device: str, baudrate: int, host: str, port: int, dev: bool
):
    import uvicorn

    parsed_layout = json.loads(layout)
    conn = serial.Serial(port=device, baudrate=baudrate, timeout=1) if device else None
    app = create_app(
        Panel(parsed_layout),
        serial_conn=conn,
        dev=dev,
    )
    config = uvicorn.Config(app, host=host, port=port, log_level="info", reload=dev)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    run()
