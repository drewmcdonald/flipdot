"""
HTTP server for receiving content updates via POST.

Runs in a separate thread and allows the remote server to push
high-priority content (like notifications) immediately instead of
waiting for the next poll.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING, final

from typing_extensions import override

from flipdot.models import AuthConfig, Content

if TYPE_CHECKING:
    from flipdot.config import DriverLimits

logger = logging.getLogger(__name__)


class PushRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for push notifications."""

    # Class variables set by PushServer
    auth_config: AuthConfig | None = None
    content_callback: Callable[[Content], None] | None = None
    limits: DriverLimits | None = None

    def _authenticate(self) -> bool:
        """
        Verify authentication credentials.

        Returns:
            True if authenticated, False otherwise
        """
        if not self.auth_config:
            return True  # No auth configured

        if self.auth_config.type == "bearer":
            auth_header = self.headers.get("Authorization", "")
            expected = f"Bearer {self.auth_config.token}"
            return auth_header == expected

        elif self.auth_config.type == "api_key":
            api_key = self.headers.get(self.auth_config.header_name, "")
            return api_key == self.auth_config.key

        return False

    def _send_json_response(
        self, status_code: int, data: dict[str, str | int | float | bool]
    ) -> None:
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        _ = self.wfile.write(json.dumps(data).encode())

    def do_POST(self) -> None:
        """Handle POST requests with content data."""
        # Check authentication
        if not self._authenticate():
            logger.warning(f"Unauthorized push request from {self.client_address}")
            self._send_json_response(401, {"error": "Unauthorized"})
            return

        # Read body with size limit
        try:
            from flipdot.config import DEFAULT_LIMITS

            content_length = int(self.headers.get("Content-Length", 0))

            limits = self.limits if self.limits is not None else DEFAULT_LIMITS
            if content_length > limits.server.max_request_size:
                logger.warning(
                    f"Request too large: {content_length} bytes "
                    + f"(max {limits.server.max_request_size})"
                )
                self._send_json_response(413, {"error": "Request too large"})
                return

            if content_length == 0:
                self._send_json_response(400, {"error": "Empty request"})
                return

            body = self.rfile.read(content_length).decode("utf-8")

            # Parse as Content
            content = Content.model_validate(json.loads(body))

            logger.info(
                f"Received push content: {content.content_id} "
                + f"(priority={content.playback.priority})"
            )

            # Call the callback
            if self.content_callback:
                self.content_callback(content)

            self._send_json_response(200, {"status": "accepted"})

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in push request: {e}")
            self._send_json_response(400, {"error": "Invalid JSON"})

        except Exception as e:
            logger.error(f"Error processing push request: {e}")
            self._send_json_response(500, {"error": "Internal server error"})

    def do_GET(self) -> None:
        """Handle GET requests (health check)."""
        if self.path == "/health":
            self._send_json_response(200, {"status": "ok"})
        else:
            self._send_json_response(404, {"error": "Not found"})

    @override
    def log_message(
        self, format: str, *args: tuple[str | int | float | bool, ...]
    ) -> None:
        """Override to use our logger instead of stderr."""
        logger.info(f"Push server: {format % args}")


@final
class PushServer:
    """HTTP server for receiving push notifications."""

    def __init__(
        self,
        host: str,
        port: int,
        auth: AuthConfig,
        content_callback: Callable[[Content], None],
        limits: DriverLimits | None = None,
    ):
        """
        Initialize the push server.

        Args:
            host: Host address to bind to (e.g., "0.0.0.0")
            port: Port to listen on
            auth: Authentication configuration
            content_callback: Function to call when content is received
            limits: Driver limits configuration
        """
        from flipdot.config import DEFAULT_LIMITS

        self.host = host
        self.port = port
        self.auth = auth
        self.content_callback = content_callback
        self.limits = limits if limits is not None else DEFAULT_LIMITS

        # Configure the handler class
        PushRequestHandler.auth_config = auth
        PushRequestHandler.content_callback = content_callback
        PushRequestHandler.limits = self.limits

        self.server = HTTPServer((host, port), PushRequestHandler)
        self.thread: threading.Thread | None = None
        self.running = False

    def start(self) -> None:
        """Start the push server in a background thread."""
        if self.running:
            logger.warning("Push server already running")
            return

        logger.info(f"Starting push server on {self.host}:{self.port}")
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        """Run the server (called in background thread)."""
        try:
            logger.info("Push server listening for requests")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Push server error: {e}")
        finally:
            self.running = False

    def stop(self) -> None:
        """Stop the push server."""
        if not self.running:
            return

        logger.info("Stopping push server")
        self.running = False
        self.server.shutdown()
        self.server.server_close()

        if self.thread:
            self.thread.join(timeout=5)
