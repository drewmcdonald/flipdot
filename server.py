import asyncio
import json
import pathlib

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
@click.option("--debug", is_flag=True)
def run_sync(
    layout: str, device: str, baudrate: int, host: str, port: int, debug: bool
):
    """
    Synchronous wrapper for the asynchronous run command.
    """
    asyncio.run(run_async(layout, device, baudrate, host, port, debug))


async def run_async(
    layout: str, device: str, baudrate: int, host: str, port: int, debug: bool
):
    import uvicorn

    parsed_layout = json.loads(layout)
    conn = serial.Serial(port=device, baudrate=baudrate, timeout=1) if device else None
    app = create_app(
        Panel(parsed_layout),
        serial_conn=conn,
        debug=debug,
    )
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


@click.command('codegen')
@click.option('--output', type=pathlib.Path, default='openapi.json')
def codegen(output: pathlib.Path):
    """
    Generates OpenAPI specification.
    """
    server = create_app(Panel([[1]]))
    text = json.dumps(server.openapi(), indent=2)
    output.write_text(text)


@click.group()
def cli():
    """
    CLI group for server commands.
    """
    pass


cli.add_command(run_sync, "run")
cli.add_command(codegen)


if __name__ == "__main__":
    cli()
