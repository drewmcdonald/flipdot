"""
Hardware driver for flipdot displays.

Rewritten from vend/flippydot.py to remove NumPy dependency for faster
startup times on Raspberry Pi.

Adapted from https://github.com/chrishemmings/flipPyDot
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from flipdot.config import DriverLimits

logger = logging.getLogger(__name__)

try:
    import serial

    SerialException: type[BaseException] = serial.SerialException  # type: ignore[assignment]
except ImportError:
    serial = None  # type: ignore
    SerialException = OSError

# Serial protocol constants
START_BYTES_FLUSH = bytes([0x80, 0x83])
START_BYTES_BUFFER = bytes([0x80, 0x84])
END_BYTES = bytes([0x8F])


def pack_bits_little_endian(bits: list[int]) -> bytes:
    """
    Pack a list of bits into bytes using little-endian bit order.

    Args:
        bits: List of 0s and 1s

    Returns:
        Packed bytes where bit 0 is the LSB of byte 0
    """
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits) and bits[i + j]:
                byte |= 1 << j  # Little-endian: LSB first
        result.append(byte)
    return bytes(result)


@final
class FlippyModule:
    """
    A single flipdot module (typically 28x7 pixels).

    Manages the content for one module and generates serial commands.
    """

    def __init__(self, width: int, height: int, address: int):
        """
        Initialize a flipdot module.

        Args:
            width: Width of the module in pixels
            height: Height of the module in pixels
            address: I2C/serial address for this module
        """
        self.width = width
        self.height = height
        self.address = address
        # Content is stored as a flat list of bits (row-major order)
        self.content: list[int] = [0] * (width * height)

    def set_content(self, content: list[list[int]]) -> None:
        """
        Set the content of this module.

        Args:
            content: 2D list of bits (0 or 1), shape [height, width]
        """
        if len(content) != self.height:
            raise ValueError(
                f"Content height {len(content)} doesn't match module height "
                f"{self.height}"
            )

        flat_content: list[int] = []
        for row in content:
            if len(row) != self.width:
                raise ValueError(
                    f"Content width {len(row)} doesn't match module width {self.width}"
                )
            flat_content.extend(row)

        self.content = flat_content

    def get_content(self) -> list[list[int]]:
        """
        Get the content as a 2D list.

        Returns:
            2D list of bits, shape [height, width]
        """
        result: list[list[int]] = []
        for i in range(self.height):
            start = i * self.width
            end = start + self.width
            result.append(self.content[start:end])
        return result

    def fetch_serial_command(self, flush: bool = True) -> bytes:
        """
        Generate the serial command to update this module.

        Args:
            flush: If True, display immediately. If False, buffer the update.

        Returns:
            Binary command to send over serial
        """
        start_bytes = START_BYTES_FLUSH if flush else START_BYTES_BUFFER

        # Pack bits column-wise (like numpy packbits with axis=0)
        # For each column, pack the bits from top to bottom
        packed_bits = bytearray()
        for col in range(self.width):
            # Extract column bits (top to bottom)
            col_bits: list[int] = []
            for row in range(self.height):
                bit_idx = row * self.width + col
                col_bits.append(self.content[bit_idx])

            # Pack this column into bytes (little-endian bit order)
            byte_val = 0
            for bit_pos, bit in enumerate(col_bits):
                if bit:
                    byte_val |= 1 << bit_pos
            packed_bits.append(byte_val)

        return start_bytes + bytes([self.address]) + bytes(packed_bits) + END_BYTES


@final
class Panel:
    """
    A panel composed of multiple flipdot modules.

    Handles splitting content across modules and generating serial commands
    for the entire display.
    """

    def __init__(
        self,
        layout: list[list[int]],
        module_width: int = 28,
        module_height: int = 7,
    ):
        """
        Initialize a panel with multiple modules.

        Args:
            layout: 2D list defining module arrangement with module addresses.
                   Example: [[1], [2]] = 2 modules stacked vertically with
                   addresses 1 and 2
            module_width: Width of each module in pixels
            module_height: Height of each module in pixels
        """
        self.modules: list[list[FlippyModule]] = []

        # Validate layout is rectangular
        if not layout or not layout[0]:
            raise ValueError("Layout must be a non-empty 2D list")

        self.n_rows = len(layout)
        self.n_cols = len(layout[0])

        for row in layout:
            if len(row) != self.n_cols:
                raise ValueError("Panel layout must be rectangular")

        self.module_width = module_width
        self.module_height = module_height

        # Create modules
        for row in layout:
            module_row: list[FlippyModule] = []
            for address in row:
                module_row.append(FlippyModule(module_width, module_height, address))
            self.modules.append(module_row)

        self.total_width = self.module_width * self.n_cols
        self.total_height = self.module_height * self.n_rows

    @property
    def dimensions(self) -> tuple[int, int]:
        """Get the total dimensions of the panel (height, width)."""
        return self.total_height, self.total_width

    def get_content(self) -> list[list[int]]:
        """
        Get the content of the entire panel as a 2D list.

        Returns:
            2D list of bits, shape [total_height, total_width]
        """
        result: list[list[int]] = []
        for module_row in self.modules:
            # Get content from each module in the row
            module_contents = [module.get_content() for module in module_row]

            # Concatenate horizontally (each row of each module)
            for row_idx in range(self.module_height):
                combined_row: list[int] = []
                for module_content in module_contents:
                    combined_row.extend(module_content[row_idx])
                result.append(combined_row)

        return result

    def set_content(self, matrix_data: list[list[int]]) -> bytes:
        """
        Set the content of the entire panel and generate serial commands.

        Args:
            matrix_data: 2D list of bits, shape [total_height, total_width]

        Returns:
            Complete serial command data for all modules
        """
        if len(matrix_data) != self.total_height:
            raise ValueError(
                f"Matrix height {len(matrix_data)} doesn't match panel height "
                f"{self.total_height}"
            )

        for row in matrix_data:
            if len(row) != self.total_width:
                raise ValueError(
                    f"Matrix width {len(row)} doesn't match panel width "
                    f"{self.total_width}"
                )

        # Split matrix into module-sized chunks
        for module_row_idx in range(self.n_rows):
            row_start = module_row_idx * self.module_height
            row_end = row_start + self.module_height
            row_data = matrix_data[row_start:row_end]

            for module_col_idx in range(self.n_cols):
                col_start = module_col_idx * self.module_width
                col_end = col_start + self.module_width

                # Extract this module's data
                module_data: list[list[int]] = []
                for row in row_data:
                    module_data.append(row[col_start:col_end])

                self.modules[module_row_idx][module_col_idx].set_content(module_data)

        # Generate serial commands for all modules
        serial_data = bytearray()
        for module_row in self.modules:
            for module in module_row:
                serial_data.extend(module.fetch_serial_command())

        return bytes(serial_data)

    def set_content_from_frame(
        self, frame_data: bytes, width: int, height: int
    ) -> bytes:
        """
        Set content from packed frame data (as received from server).

        Args:
            frame_data: Packed bits (little-endian)
            width: Width of the frame
            height: Height of the frame

        Returns:
            Complete serial command data for all modules
        """
        if width != self.total_width or height != self.total_height:
            raise ValueError(
                f"Frame dimensions ({height}x{width}) don't match panel dimensions "
                f"({self.total_height}x{self.total_width})"
            )

        # Unpack bits
        bits: list[int] = []
        for byte in frame_data:
            for bit_pos in range(8):
                bits.append((byte >> bit_pos) & 1)

        # Convert to 2D array
        matrix_data: list[list[int]] = []
        bit_idx = 0
        for _ in range(height):
            row: list[int] = []
            for _ in range(width):
                if bit_idx < len(bits):
                    row.append(bits[bit_idx])
                else:
                    row.append(0)
                bit_idx += 1
            matrix_data.append(row)

        return self.set_content(matrix_data)


@final
class SerialConnection:
    """Wrapper for serial connection with optional dev mode and reconnection."""

    def __init__(
        self,
        device: str | None = None,
        baudrate: int = 57600,
        dev_mode: bool = False,
        limits: DriverLimits | None = None,
    ):
        """
        Initialize serial connection.

        Args:
            device: Serial device path (e.g., /dev/ttyUSB0)
            baudrate: Baud rate for serial communication
            dev_mode: If True, print to console instead of serial
            limits: Driver limits configuration (uses DEFAULT_LIMITS if None)
        """
        from flipdot.config import DEFAULT_LIMITS

        self.dev_mode = dev_mode
        self.device = device
        self.baudrate = baudrate
        self.limits = limits if limits is not None else DEFAULT_LIMITS
        self._serial = None
        self.consecutive_failures = 0
        self.last_reconnect_attempt = 0.0
        self.reconnect_backoff_ms = self.limits.serial.initial_reconnect_backoff_ms

        if not dev_mode and device:
            if serial is None:
                raise ImportError("pyserial is required for serial communication")
            _ = self._connect()

    def _connect(self) -> bool:
        """
        Attempt to connect to the serial device.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if serial is None:
                raise ImportError("pyserial is required for serial communication")
            self._serial = serial.Serial(self.device, self.baudrate, timeout=1)
            self.consecutive_failures = 0
            self.reconnect_backoff_ms = self.limits.serial.initial_reconnect_backoff_ms
            logger.info(f"Connected to serial device {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.device}: {e}")
            self._serial = None
            return False

    def _should_attempt_reconnect(self) -> bool:
        """
        Check if we should attempt reconnection based on backoff timing.

        Returns:
            True if enough time has passed to retry
        """
        import time

        elapsed_ms = (time.time() - self.last_reconnect_attempt) * 1000
        return elapsed_ms >= self.reconnect_backoff_ms

    def _try_reconnect(self) -> bool:
        """
        Attempt to reconnect to the serial device with exponential backoff.

        Returns:
            True if reconnection successful, False otherwise
        """
        import time

        if not self._should_attempt_reconnect():
            return False

        self.last_reconnect_attempt = time.time()
        logger.info(
            f"Attempting serial reconnection "
            f"(failure count: {self.consecutive_failures})"
        )

        success = self._connect()

        if not success:
            # Exponential backoff
            self.reconnect_backoff_ms = min(
                self.reconnect_backoff_ms * 2,
                self.limits.serial.max_reconnect_backoff_ms,
            )
            logger.warning(
                f"Reconnection failed, will retry in {self.reconnect_backoff_ms}ms"
            )

        return success

    def write(self, data: bytes) -> bool:
        """
        Write data to serial or print in dev mode.
        Attempts reconnection on failure with exponential backoff.

        Args:
            data: Bytes to write

        Returns:
            True if write successful, False if failed
        """
        if self.dev_mode:
            logger.debug(f"[DEV] Would write {len(data)} bytes to serial: {data.hex()}")
            return True

        # Try to reconnect if we don't have a connection
        if not self._serial:
            if not self._try_reconnect():
                self.consecutive_failures += 1
                if (
                    self.consecutive_failures
                    >= self.limits.serial.max_consecutive_failures
                ):
                    logger.error(
                        f"Serial device unavailable after {self.consecutive_failures} "
                        f"consecutive failures. Please check hardware connection."
                    )
                return False

        try:
            if self._serial is None:
                self.consecutive_failures += 1
                logger.error("Serial connection is not available")
                return False

            bytes_written = self._serial.write(data)
            if bytes_written != len(data):
                self.consecutive_failures += 1
                logger.error(
                    f"Serial write incomplete: wrote {bytes_written}/{len(data)} "
                    "bytes. Device buffer may be full or connection unstable."
                )
                return False

            # Success - reset failure counter
            if self.consecutive_failures > 0:
                logger.info("Serial communication recovered")
            self.consecutive_failures = 0
            logger.debug(f"Successfully wrote {bytes_written} bytes to serial")
            return True

        except (OSError, SerialException) as e:
            self.consecutive_failures += 1
            logger.error(
                f"Serial write failed: {e}. Device may be disconnected "
                f"(failure {self.consecutive_failures}/"
                f"{self.limits.serial.max_consecutive_failures})."
            )
            # Close and mark for reconnection
            if self._serial:
                try:
                    self._serial.close()
                except Exception:
                    pass
                self._serial = None
            return False

        except BaseException as e:
            self.consecutive_failures += 1
            logger.error(f"Unexpected error writing to serial: {e}", exc_info=True)
            return False

    def close(self) -> None:
        """Close the serial connection."""
        if self._serial:
            self._serial.close()
