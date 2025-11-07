"""
Configuration constants for the flipdot driver.

Centralizes all magic numbers and limits to make them configurable
and easier to understand/tune.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContentLimits:
    """Limits for content validation to prevent OOM attacks."""

    # Maximum number of frames per content item
    max_frames_per_content: int = 1000

    # Maximum total byte size per content (frame data + metadata)
    max_total_bytes: int = 5 * 1024 * 1024  # 5MB

    # Maximum metadata size per frame or content
    max_metadata_bytes: int = 10 * 1024  # 10KB


@dataclass(frozen=True)
class QueueLimits:
    """Limits for the content queue to prevent memory exhaustion."""

    # Maximum number of items in the main queue
    max_queued_items: int = 50

    # Maximum number of interrupted items to keep on stack
    max_interrupted_items: int = 10


@dataclass(frozen=True)
class ClientBackoff:
    """Network client backoff and retry configuration."""

    # Initial backoff delay after first error
    initial_backoff_ms: int = 1000  # 1 second

    # Multiplier for exponential backoff (delay doubles each failure)
    backoff_multiplier: float = 2.0

    # Maximum backoff delay
    max_backoff_ms: int = 300000  # 5 minutes

    # Request timeout
    timeout_seconds: int = 10


@dataclass(frozen=True)
class SerialConfig:
    """Serial connection and reconnection configuration."""

    # Maximum consecutive failures before giving up on reconnection
    max_consecutive_failures: int = 10

    # Initial reconnection backoff delay
    initial_reconnect_backoff_ms: int = 1000  # 1 second

    # Maximum reconnection backoff delay
    max_reconnect_backoff_ms: int = 60000  # 60 seconds


@dataclass(frozen=True)
class ServerLimits:
    """HTTP push server limits."""

    # Maximum size of HTTP POST request body
    max_request_size: int = 10 * 1024 * 1024  # 10MB


@dataclass(frozen=True)
class LoopTiming:
    """Main loop timing configuration."""

    # Fixed sleep interval for main loop (seconds)
    # 20ms = 50 iterations/second, sufficient for display updates
    sleep_interval_seconds: float = 0.020


@dataclass(frozen=True)
class DriverLimits:
    """
    All driver limits and configuration constants.

    This centralizes all magic numbers to make them configurable
    and easier to understand/tune for different deployments.
    """

    content: ContentLimits = ContentLimits()
    queue: QueueLimits = QueueLimits()
    client: ClientBackoff = ClientBackoff()
    serial: SerialConfig = SerialConfig()
    server: ServerLimits = ServerLimits()
    loop: LoopTiming = LoopTiming()


# Default driver limits instance
DEFAULT_LIMITS = DriverLimits()
