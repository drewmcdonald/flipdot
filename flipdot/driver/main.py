"""
Main driver entry point.

This is the minimal driver that runs on the Raspberry Pi. It:
- Polls a remote server for content
- Optionally accepts push notifications
- Manages a priority queue of content
- Displays frames on the flipdot hardware
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, cast, final

from flipdot.driver.client import ContentClient, ErrorHandler
from flipdot.driver.hardware import Panel, SerialConnection
from flipdot.driver.models import (
    Content,
    DriverConfig,
    ResponseStatus,
)
from flipdot.driver.queue import ContentQueue
from flipdot.driver.server import PushServer

if TYPE_CHECKING:
    from flipdot.driver.config import DriverLimits

logger = logging.getLogger(__name__)


@final
class FlipDotDriver:
    """Main driver class that orchestrates all components."""

    def __init__(self, config: DriverConfig, limits: DriverLimits | None = None):
        """
        Initialize the driver.

        Args:
            config: Driver configuration
            limits: Driver limits configuration
        """
        from flipdot.driver.config import DEFAULT_LIMITS

        self.config = config
        self.limits = limits if limits is not None else DEFAULT_LIMITS
        self.running = False

        # Set up logging
        log_level: int | None = getattr(logging, config.log_level.upper(), None)
        if log_level is None:
            log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

        # Initialize hardware
        logger.info("Initializing hardware...")
        self.panel = Panel(
            layout=config.module_layout,
            module_width=config.module_width,
            module_height=config.module_height,
        )
        self.serial = SerialConnection(
            device=config.serial_device,
            baudrate=config.serial_baudrate,
            dev_mode=config.dev_mode,
            limits=limits,
        )

        height, width = self.panel.dimensions
        logger.info(f"Display dimensions: {width}x{height}")

        # Initialize content management
        self.queue = ContentQueue(limits=limits)
        self.client = ContentClient(
            endpoint=config.poll_endpoint,
            auth=config.auth,
            limits=limits,
        )
        self.error_handler = ErrorHandler(fallback=config.error_fallback)

        # Initialize push server if enabled
        self.push_server: PushServer | None = None
        if config.enable_push:
            self.push_server = PushServer(
                host=config.push_host,
                port=config.push_port,
                auth=config.auth,
                content_callback=self._handle_push_content,
                limits=limits,
            )

    def _handle_push_content(self, content: Content) -> None:
        """
        Handle content received via push notification.

        Args:
            content: Pushed content
        """
        logger.info(f"Received push content: {content.content_id}")

        # Validate content dimensions against display before queuing
        height, width = self.panel.dimensions
        try:
            content.validate_display_dimensions(width, height)
        except ValueError as e:
            logger.error(f"Rejecting push content due to dimension mismatch: {e}")
            return

        self.queue.add_content(content)
        # Reset poll timer since we just got fresh data
        self.client.reset_poll_timer()

    def _poll_for_content(self) -> None:
        """Poll the server for content updates."""
        if not self.client.should_poll():
            return

        response = self.client.fetch_content()

        if response is None:
            # Handle error
            logger.warning("Failed to fetch content, using fallback")
            response = self.error_handler.get_fallback_response()
            if response is None:
                return

        # Record successful fetch
        if response.content:
            self.error_handler.set_last_successful(response)

        # Process response
        if response.status == ResponseStatus.UPDATED and response.content:
            # Validate content dimensions against display before queuing
            height, width = self.panel.dimensions
            try:
                response.content.validate_display_dimensions(width, height)
            except ValueError as e:
                logger.error(f"Rejecting content due to dimension mismatch: {e}")
                return

            # Check if we should replace existing content with same ID
            if not self.queue.replace_if_same_id(response.content):
                # Add as new content
                self.queue.add_content(response.content)

        elif response.status == ResponseStatus.CLEAR:
            logger.info("Server requested display clear")
            self.queue.clear()
            self._clear_display()

        # NO_CHANGE means keep current content, do nothing

    def _clear_display(self) -> None:
        """Clear the display (show blank)."""
        height, width = self.panel.dimensions
        blank = [[0] * width for _ in range(height)]
        serial_data = self.panel.set_content(blank)
        if not self.serial.write(serial_data):
            logger.error("Failed to clear display due to serial error")

    def _calculate_next_sleep_ms(self) -> float:
        """
        Calculate the sleep duration for the main loop.

        Uses a fixed small interval to keep the loop responsive without
        burning CPU. The queue and client handle their own timing internally.

        Returns:
            Sleep time in seconds (from config)
        """
        return self.limits.loop.sleep_interval_seconds

    def _render_frame(self) -> None:
        """Render the current frame to the display."""
        frame = self.queue.update()

        if frame is None:
            # Nothing to display
            return

        try:
            # Convert frame to serial data and send
            # (dimensions are already validated when content is queued)
            frame_data = frame.decode_data()
            serial_data = self.panel.set_content_from_frame(
                frame_data, frame.width, frame.height
            )

            if not self.serial.write(serial_data):
                logger.error("Failed to render frame: serial write failed")
                # Note: We don't stop the driver on serial errors;
                # the user can still receive new content and display will recover
                # if the device is reconnected

        except Exception as e:
            logger.error(f"Error rendering frame: {e}", exc_info=True)

    def start(self) -> None:
        """Start the driver."""
        logger.info("Starting FlipDot driver...")

        # Start push server if enabled
        if self.push_server:
            self.push_server.start()

        self.running = True

        # Main loop
        try:
            while self.running:
                # Poll for new content
                self._poll_for_content()

                # Render current frame
                self._render_frame()

                # Sleep until the next event (frame change or poll time)
                # This prevents busy-waiting and reduces CPU usage
                sleep_seconds = self._calculate_next_sleep_ms()
                time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the driver gracefully."""
        if not self.running:
            return

        logger.info("Stopping driver...")
        self.running = False

        # Stop push server
        if self.push_server:
            self.push_server.stop()

        # Clear display
        logger.info("Clearing display...")
        self._clear_display()

        # Close serial connection
        self.serial.close()

        logger.info("Driver stopped")


def load_config(config_path: str) -> DriverConfig:
    """
    Load driver configuration from a file.

    Args:
        config_path: Path to configuration JSON file

    Returns:
        Parsed configuration
    """
    import json

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        data = cast(dict[str, object], json.load(f))

    return DriverConfig.model_validate(data)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="FlipDot Display Driver")
    _ = parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to configuration JSON file",
    )

    args: argparse.Namespace = parser.parse_args()

    try:
        config = load_config(cast(str, args.config))
        driver = FlipDotDriver(config)

        # Handle SIGTERM gracefully
        def signal_handler(sig: int, _frame: FrameType | None) -> None:
            logger.info(f"Received signal {sig}")
            driver.stop()
            sys.exit(0)

        _ = signal.signal(signal.SIGTERM, signal_handler)
        _ = signal.signal(signal.SIGINT, signal_handler)

        driver.start()

    except Exception as e:
        logger.error(f"Failed to start driver: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
