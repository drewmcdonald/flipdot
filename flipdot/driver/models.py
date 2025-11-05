"""
Data models for the flipdot driver protocol.

All content is fetched from a remote server in a structured format.
Frames contain base64-encoded packed bit data for efficiency.
"""

import base64
from enum import Enum
from typing import ClassVar, Literal

from pydantic import BaseModel, Field, field_validator


class Frame(BaseModel):
    """A single frame to display with timing information."""

    data_b64: str = Field(
        ...,
        description="Base64-encoded packed bits representing the frame data. "
        "Bits are packed row-by-row, little-endian bit order.",
    )
    width: int = Field(..., gt=0, description="Width of the frame in pixels")
    height: int = Field(..., gt=0, description="Height of the frame in pixels")
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description="How long to display this frame in milliseconds. "
        "None or 0 means display indefinitely.",
    )
    metadata: dict | None = Field(
        default=None, description="Optional metadata for debugging"
    )

    @field_validator("data_b64")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate that data_b64 is valid base64."""
        try:
            base64.b64decode(v, validate=True)
        except Exception as e:
            raise ValueError(f"Invalid base64 data: {e}")
        return v

    def decode_data(self) -> bytes:
        """Decode the base64 data to raw bytes."""
        return base64.b64decode(self.data_b64)

    def to_bit_array(self) -> list[list[int]]:
        """
        Convert the packed bits to a 2D array of 0s and 1s.
        Returns a list of lists representing rows of pixels.
        """
        data = self.decode_data()
        bits = []
        bit_idx = 0

        for _ in range(self.height):
            row = []
            for _ in range(self.width):
                byte_idx = bit_idx // 8
                bit_pos = bit_idx % 8
                if byte_idx < len(data):
                    bit = (data[byte_idx] >> bit_pos) & 1
                    row.append(bit)
                else:
                    row.append(0)
                bit_idx += 1
            bits.append(row)

        return bits


class PlaybackMode(BaseModel):
    """Playback configuration for a content sequence."""

    loop: bool = Field(default=False, description="Whether to loop through frames")
    loop_count: int | None = Field(
        default=None,
        ge=1,
        description="How many times to loop (null = infinite if loop=true)",
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=99,
        description="Priority level: 0=normal, 10=notification, 99=urgent",
    )
    interruptible: bool = Field(
        default=True, description="Can this content be interrupted by higher priority?"
    )

    @field_validator("loop_count")
    @classmethod
    def validate_loop_count(cls, v: int | None, info) -> int | None:
        """Validate that loop_count requires loop=True."""
        if v is not None:
            loop = info.data.get("loop", False)
            if not loop:
                raise ValueError("loop_count can only be set when loop=True")
        return v


class Content(BaseModel):
    """A sequence of frames with playback instructions."""

    content_id: str = Field(..., description="Unique identifier for this content")
    frames: list[Frame] = Field(..., min_length=1, description="Frames to display")
    playback: PlaybackMode = Field(
        default_factory=PlaybackMode, description="Playback configuration"
    )
    metadata: dict | None = Field(
        default=None, description="Optional metadata for debugging"
    )

    # Security limits to prevent OOM attacks
    # These defaults match config.py DEFAULT_LIMITS
    MAX_FRAMES_PER_CONTENT: ClassVar[int] = 1000
    MAX_TOTAL_BYTES: ClassVar[int] = 5 * 1024 * 1024  # 5MB
    MAX_METADATA_BYTES: ClassVar[int] = 10 * 1024  # 10KB

    @field_validator("frames")
    @classmethod
    def validate_frame_dimensions(cls, frames: list[Frame]) -> list[Frame]:
        """Validate that all frames have consistent dimensions and enforce limits."""
        if not frames:
            raise ValueError("At least one frame is required")

        # Enforce frame count limit to prevent OOM
        if len(frames) > cls.MAX_FRAMES_PER_CONTENT:
            raise ValueError(
                f"Too many frames: {len(frames)} exceeds limit of {cls.MAX_FRAMES_PER_CONTENT}"
            )

        first_frame = frames[0]
        width, height = first_frame.width, first_frame.height

        # Calculate total byte size while validating
        total_bytes = 0
        for i, frame in enumerate(frames):
            if i > 0 and (frame.width != width or frame.height != height):
                raise ValueError(
                    f"Frame {i} has dimensions {frame.width}x{frame.height}, "
                    f"but frame 0 has {width}x{height}. All frames must match."
                )

            # Add size of decoded frame data
            total_bytes += len(frame.decode_data())

            # Add approximate size of metadata (if present)
            if frame.metadata:
                import json

                metadata_size = len(json.dumps(frame.metadata).encode("utf-8"))
                if metadata_size > cls.MAX_METADATA_BYTES:
                    raise ValueError(
                        f"Frame {i} metadata too large: {metadata_size} bytes exceeds limit of {cls.MAX_METADATA_BYTES}"
                    )
                total_bytes += metadata_size

        # Enforce total memory limit
        if total_bytes > cls.MAX_TOTAL_BYTES:
            raise ValueError(
                f"Content too large: {total_bytes} bytes exceeds limit of {cls.MAX_TOTAL_BYTES}"
            )

        return frames

    @field_validator("metadata")
    @classmethod
    def validate_metadata_size(cls, v: dict | None) -> dict | None:
        """Validate that metadata doesn't exceed size limit."""
        if v is None:
            return v

        import json

        metadata_size = len(json.dumps(v).encode("utf-8"))
        if metadata_size > cls.MAX_METADATA_BYTES:
            raise ValueError(
                f"Content metadata too large: {metadata_size} bytes exceeds limit of {cls.MAX_METADATA_BYTES}"
            )

        return v

    def validate_display_dimensions(
        self, display_width: int, display_height: int
    ) -> None:
        """
        Validate that content dimensions match the display.

        Args:
            display_width: Expected display width in pixels
            display_height: Expected display height in pixels

        Raises:
            ValueError: If frame dimensions don't match display
        """
        if self.frames:
            frame = self.frames[0]
            if frame.width != display_width or frame.height != display_height:
                raise ValueError(
                    f"Content {self.content_id} has frame dimensions "
                    f"{frame.width}x{frame.height}, but display is "
                    f"{display_width}x{display_height}"
                )


class ResponseStatus(str, Enum):
    """Status of a content response."""

    UPDATED = "updated"  # New content available
    NO_CHANGE = "no_change"  # No change, keep current content
    CLEAR = "clear"  # Clear display


class ContentResponse(BaseModel):
    """Response from the content server."""

    status: ResponseStatus = Field(..., description="Status of the response")
    content: Content | None = Field(
        default=None, description="Content data (only if status=updated)"
    )
    poll_interval_ms: int = Field(
        default=30000, ge=1000, description="How long to wait before next poll"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Content | None, info) -> Content | None:
        """Validate that content is present when status is updated."""
        status = info.data.get("status")
        if status == ResponseStatus.UPDATED and v is None:
            raise ValueError("content must be provided when status is 'updated'")
        return v


class AuthConfig(BaseModel):
    """Authentication configuration."""

    type: Literal["bearer", "api_key"] = Field(
        default="api_key", description="Authentication type"
    )
    token: str | None = Field(default=None, description="Bearer token (if type=bearer)")
    key: str | None = Field(default=None, description="API key (if type=api_key)")
    header_name: str = Field(
        default="X-API-Key", description="Header name for API key auth"
    )


class ErrorFallback(str, Enum):
    """Fallback behavior when server is unreachable."""

    KEEP_LAST = "keep_last"  # Keep displaying last known content
    BLANK = "blank"  # Show blank screen
    ERROR_MESSAGE = "error_message"  # Show error message (if supported)


class DriverConfig(BaseModel):
    """Configuration for the flipdot driver."""

    # Server configuration
    poll_endpoint: str = Field(..., description="URL to poll for content updates")
    poll_interval_ms: int = Field(
        default=30000, ge=1000, description="Default polling interval"
    )

    # Push server configuration
    enable_push: bool = Field(
        default=False, description="Enable HTTP server for push notifications"
    )
    push_port: int = Field(
        default=8080, ge=1, le=65535, description="Port for push server"
    )
    push_host: str = Field(
        default="0.0.0.0", description="Host address for push server"
    )

    # Authentication
    auth: AuthConfig = Field(
        default_factory=AuthConfig, description="Authentication configuration"
    )

    # Hardware configuration
    serial_device: str | None = Field(
        default=None, description="Serial device path (e.g., /dev/ttyUSB0)"
    )
    serial_baudrate: int = Field(default=57600, description="Serial baud rate")
    module_layout: list[list[int]] = Field(
        default=[[1], [2]], description="Layout of flipdot modules"
    )
    module_width: int = Field(default=28, description="Width of each module in pixels")
    module_height: int = Field(default=7, description="Height of each module in pixels")

    # Behavior configuration
    error_fallback: ErrorFallback = Field(
        default=ErrorFallback.KEEP_LAST,
        description="What to do when server is unreachable",
    )
    dev_mode: bool = Field(
        default=False,
        description="Development mode: print to console instead of serial",
    )

    # Logging
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
