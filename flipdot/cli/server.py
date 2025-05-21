import asyncio
import json
import logging # Needed for Uvicorn log config

import click
import serial
from dotenv import load_dotenv

from flipdot.create_app import create_app
from flipdot.vend.flippydot import Panel
from flipdot.logging_config import setup_logging # Import the setup function

load_dotenv()


# Configure logging as early as possible
# The log level can be made configurable via CLI option or env var later if needed.
LOG_LEVEL = "INFO" # Default log level
setup_logging(log_level=LOG_LEVEL)


@click.command("run")
@click.option("--layout", type=str, default='[[1], [2]]')
@click.option("--device", type=str, default=None, required=False)
@click.option("--baudrate", type=int, default=57600)
@click.option("--host", type=str, default="0.0.0.0")
@click.option("--port", type=int, default=8080)
@click.option("--dev", is_flag=True, help="Print to console instead of a serial device")
def run(layout: str, device: str, baudrate: int, host: str, port: int, dev: bool):
    """
    Synchronous wrapper for the asynchronous run command.
    Sets up logging and then starts the Uvicorn server.
    """
    # setup_logging is already called when the module is imported.
    # If it needed to be configurable per command run, it would be called here.
    # For example: setup_logging(log_level=log_level_option_from_click)
    
    asyncio.run(run_async(layout, device, baudrate, host, port, dev))


async def run_async(
    layout: str, device: str, baudrate: int, host: str, port: int, dev: bool
):
    import uvicorn
    from structlog.stdlib import get_logger as structlog_get_logger

    logger = structlog_get_logger("flipdot.cli.server")
    logger.info(
        "Starting server setup", 
        layout=layout, device=device, baudrate=baudrate, 
        host=host, port=port, dev_mode=dev
    )

    parsed_layout = json.loads(layout)
    
    serial_connection = None
    if device:
        try:
            serial_connection = serial.Serial(port=device, baudrate=baudrate, timeout=1)
            logger.info("Serial connection established", device=device, baudrate=baudrate)
        except serial.SerialException as e:
            logger.error("Failed to establish serial connection", device=device, error=str(e), exc_info=True)
            # Decide if server should start without serial, for now it will.
            # Add return or raise if server shouldn't start.
    else:
        logger.info("No serial device specified, running in dev mode or without hardware.")

    app = create_app(
        panel=Panel(parsed_layout), # Panel creation might also need try-except if it can fail
        serial_conn=serial_connection,
        dev=dev, # Pass dev flag to create_app for its own logic
    )

    # Uvicorn logging configuration to use structlog's JSON output
    # This is a simplified version. For full control, one might need custom handlers.
    # Uvicorn's default access log format is quite specific.
    # We will try to make its own loggers use our structlog setup.
    # This means their logs will pass through the root logger handler we configured.
    
    # Uvicorn loggers: "uvicorn", "uvicorn.error", "uvicorn.access"
    # We've already configured the root logger in setup_logging.
    # So, Uvicorn logs should automatically use that configuration.
    # We just need to ensure Uvicorn's log level is respected or set.
    
    # The log_level in uvicorn.Config sets the level for uvicorn's loggers.
    # If LOG_LEVEL is "DEBUG", uvicorn access logs will be very verbose.
    # If LOG_LEVEL is "INFO", access logs are standard.

    config = uvicorn.Config(
        app, 
        host=host, 
        port=port, 
        log_level=LOG_LEVEL.lower(), # uvicorn expects lowercase log level string
        reload=dev,
        # No need for log_config if root logger setup in setup_logging is sufficient.
        # If we wanted a completely separate config for uvicorn logs:
        # log_config=get_uvicorn_log_config(LOG_LEVEL) # Would be a custom function
    )
    
    server = uvicorn.Server(config)
    logger.info("Uvicorn server configured, starting serve...", server_config=config.__dict__)
    await server.serve()
    logger.info("Server shutdown complete.")


if __name__ == "__main__":
    run()
