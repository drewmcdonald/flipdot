"""
Comprehensive tests for the flipdot driver implementation.
"""

import base64
import json
import time
from http.server import HTTPServer
from threading import Thread
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from flipdot.driver.client import ContentClient, ErrorHandler
from flipdot.driver.hardware import (
    FlippyModule,
    Panel,
    SerialConnection,
    pack_bits_little_endian,
)
from flipdot.driver.models import (
    AuthConfig,
    Content,
    ContentResponse,
    DriverConfig,
    ErrorFallback,
    Frame,
    PlaybackMode,
    ResponseStatus,
)
from flipdot.driver.queue import ContentQueue, ContentState
from flipdot.driver.server import PushRequestHandler, PushServer


# =============================================================================
# Test Utilities
# =============================================================================


def create_test_frame(width: int = 2, height: int = 2, duration_ms: int = 1000) -> Frame:
    """Create a simple test frame."""
    bits = [1, 0] * ((width * height) // 2)
    if len(bits) < width * height:
        bits.append(1)
    packed = pack_bits_little_endian(bits[: width * height])
    b64 = base64.b64encode(packed).decode()
    return Frame(data_b64=b64, width=width, height=height, duration_ms=duration_ms)


def create_test_content(
    content_id: str = "test",
    num_frames: int = 1,
    priority: int = 0,
    loop: bool = False,
    interruptible: bool = True,
) -> Content:
    """Create test content with specified parameters."""
    frames = [create_test_frame() for _ in range(num_frames)]
    playback = PlaybackMode(
        loop=loop, priority=priority, interruptible=interruptible
    )
    return Content(content_id=content_id, frames=frames, playback=playback)


# =============================================================================
# Bit Packing Tests
# =============================================================================


class TestBitPacking:
    """Comprehensive bit packing tests."""

    def test_pack_bits_all_zeros(self):
        """Test packing all zeros."""
        bits = [0] * 16
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0x00, 0x00])

    def test_pack_bits_all_ones(self):
        """Test packing all ones."""
        bits = [1] * 16
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0xFF, 0xFF])

    def test_pack_bits_alternating(self):
        """Test alternating bit pattern."""
        bits = [1, 0, 1, 0, 1, 0, 1, 0]
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0x55])  # 01010101 in little-endian

        bits = [0, 1, 0, 1, 0, 1, 0, 1]
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0xAA])  # 10101010 in little-endian

    def test_pack_bits_partial_byte(self):
        """Test packing partial bytes with various lengths."""
        for length in range(1, 8):
            bits = [1] * length
            packed = pack_bits_little_endian(bits)
            expected = (1 << length) - 1
            assert packed == bytes([expected])

    def test_pack_bits_empty(self):
        """Test packing empty bit list."""
        packed = pack_bits_little_endian([])
        assert packed == bytes()

    def test_pack_bits_single_bit(self):
        """Test packing single bit."""
        assert pack_bits_little_endian([0]) == bytes([0x00])
        assert pack_bits_little_endian([1]) == bytes([0x01])

    def test_pack_bits_multiple_bytes(self):
        """Test packing multiple complete bytes."""
        bits = [1] * 8 + [0] * 8 + [1] * 8
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0xFF, 0x00, 0xFF])

    def test_pack_bits_specific_pattern(self):
        """Test specific bit patterns that might reveal endianness issues."""
        # Bit pattern: 10000000 (should be 0x01 in little-endian)
        bits = [1, 0, 0, 0, 0, 0, 0, 0]
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0x01])

        # Bit pattern: 00000001 (should be 0x80 in little-endian)
        bits = [0, 0, 0, 0, 0, 0, 0, 1]
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0x80])


# =============================================================================
# Frame Model Tests
# =============================================================================


class TestFrame:
    """Comprehensive Frame model tests."""

    def test_frame_valid_creation(self):
        """Test creating valid frames."""
        frame = create_test_frame(width=28, height=7, duration_ms=500)
        assert frame.width == 28
        assert frame.height == 7
        assert frame.duration_ms == 500

    def test_frame_no_duration(self):
        """Test frame with no duration (display indefinitely)."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        frame = Frame(data_b64=b64, width=2, height=2, duration_ms=None)
        assert frame.duration_ms is None

    def test_frame_zero_duration(self):
        """Test frame with zero duration."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        frame = Frame(data_b64=b64, width=2, height=2, duration_ms=0)
        assert frame.duration_ms == 0

    def test_frame_invalid_base64(self):
        """Test that invalid base64 raises an error."""
        with pytest.raises(ValueError, match="Invalid base64"):
            Frame(data_b64="not!!!valid", width=2, height=2)

    def test_frame_negative_dimensions(self):
        """Test that negative dimensions are rejected."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        with pytest.raises(ValueError):
            Frame(data_b64=b64, width=-1, height=2)

        with pytest.raises(ValueError):
            Frame(data_b64=b64, width=2, height=-1)

    def test_frame_zero_dimensions(self):
        """Test that zero dimensions are rejected."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        with pytest.raises(ValueError):
            Frame(data_b64=b64, width=0, height=2)

    def test_frame_negative_duration(self):
        """Test that negative duration is rejected."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        with pytest.raises(ValueError):
            Frame(data_b64=b64, width=2, height=2, duration_ms=-1)

    def test_frame_decode_data(self):
        """Test decoding base64 data."""
        bits = [1, 0, 1, 0, 1, 0, 1, 0]
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        frame = Frame(data_b64=b64, width=8, height=1)

        decoded = frame.decode_data()
        assert decoded == packed

    def test_frame_to_bit_array_simple(self):
        """Test converting frame to bit array."""
        bits = [1, 0, 1, 0]
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        frame = Frame(data_b64=b64, width=2, height=2)

        result = frame.to_bit_array()
        assert result == [[1, 0], [1, 0]]

    def test_frame_to_bit_array_larger(self):
        """Test converting larger frame to bit array."""
        width, height = 4, 3
        bits = list(range(width * height))
        bits = [b % 2 for b in bits]  # Convert to 0s and 1s
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        frame = Frame(data_b64=b64, width=width, height=height)

        result = frame.to_bit_array()
        assert len(result) == height
        assert all(len(row) == width for row in result)

    def test_frame_with_metadata(self):
        """Test frame with metadata."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        metadata = {"frame_id": "test-123", "timestamp": "2024-01-01"}
        frame = Frame(data_b64=b64, width=2, height=2, metadata=metadata)

        assert frame.metadata == metadata

    def test_frame_serialization(self):
        """Test frame JSON serialization."""
        frame = create_test_frame()
        json_str = frame.model_dump_json()
        parsed = Frame.model_validate_json(json_str)
        assert parsed.width == frame.width
        assert parsed.height == frame.height
        assert parsed.data_b64 == frame.data_b64


# =============================================================================
# Content Model Tests
# =============================================================================


class TestContent:
    """Comprehensive Content model tests."""

    def test_content_single_frame(self):
        """Test content with single frame."""
        content = create_test_content(num_frames=1)
        assert len(content.frames) == 1
        assert content.playback.loop is False

    def test_content_multiple_frames(self):
        """Test content with multiple frames."""
        content = create_test_content(num_frames=5)
        assert len(content.frames) == 5

    def test_content_no_frames(self):
        """Test that content requires at least one frame."""
        with pytest.raises(ValueError):
            Content(content_id="test", frames=[], playback=PlaybackMode())

    def test_content_priority_levels(self):
        """Test different priority levels."""
        for priority in [0, 5, 10, 50, 99]:
            content = create_test_content(priority=priority)
            assert content.playback.priority == priority

    def test_content_invalid_priority(self):
        """Test invalid priority values."""
        frame = create_test_frame()

        with pytest.raises(ValueError):
            Content(
                content_id="test",
                frames=[frame],
                playback=PlaybackMode(priority=-1),
            )

        with pytest.raises(ValueError):
            Content(
                content_id="test",
                frames=[frame],
                playback=PlaybackMode(priority=100),
            )

    def test_content_loop_configurations(self):
        """Test various loop configurations."""
        # No loop
        content = create_test_content(loop=False)
        assert content.playback.loop is False
        assert content.playback.loop_count is None

        # Infinite loop
        frame = create_test_frame()
        content = Content(
            content_id="test",
            frames=[frame],
            playback=PlaybackMode(loop=True, loop_count=None),
        )
        assert content.playback.loop is True
        assert content.playback.loop_count is None

        # Limited loops
        content = Content(
            content_id="test",
            frames=[frame],
            playback=PlaybackMode(loop=True, loop_count=5),
        )
        assert content.playback.loop_count == 5

    def test_content_interruptible_flag(self):
        """Test interruptible configurations."""
        content = create_test_content(interruptible=True)
        assert content.playback.interruptible is True

        content = create_test_content(interruptible=False)
        assert content.playback.interruptible is False


# =============================================================================
# ContentResponse Model Tests
# =============================================================================


class TestContentResponse:
    """Comprehensive ContentResponse model tests."""

    def test_response_updated_with_content(self):
        """Test updated response with content."""
        content = create_test_content()
        response = ContentResponse(
            status=ResponseStatus.UPDATED,
            content=content,
            poll_interval_ms=30000,
        )
        assert response.status == ResponseStatus.UPDATED
        assert response.content is not None

    def test_response_updated_without_content_fails(self):
        """Test that updated status requires content."""
        with pytest.raises(ValueError, match="content must be provided"):
            ContentResponse(status=ResponseStatus.UPDATED, content=None)

    def test_response_no_change(self):
        """Test no_change response."""
        response = ContentResponse(
            status=ResponseStatus.NO_CHANGE, poll_interval_ms=60000
        )
        assert response.status == ResponseStatus.NO_CHANGE
        assert response.content is None
        assert response.poll_interval_ms == 60000

    def test_response_clear(self):
        """Test clear response."""
        response = ContentResponse(status=ResponseStatus.CLEAR)
        assert response.status == ResponseStatus.CLEAR
        assert response.content is None

    def test_response_invalid_poll_interval(self):
        """Test invalid poll intervals."""
        with pytest.raises(ValueError):
            ContentResponse(status=ResponseStatus.NO_CHANGE, poll_interval_ms=500)

        with pytest.raises(ValueError):
            ContentResponse(status=ResponseStatus.NO_CHANGE, poll_interval_ms=-1000)

    def test_response_serialization(self):
        """Test response serialization."""
        content = create_test_content()
        response = ContentResponse(
            status=ResponseStatus.UPDATED, content=content, poll_interval_ms=30000
        )
        json_str = response.model_dump_json()
        parsed = ContentResponse.model_validate_json(json_str)
        assert parsed.status == response.status
        assert parsed.content.content_id == content.content_id


# =============================================================================
# FlippyModule Tests
# =============================================================================


class TestFlippyModule:
    """Comprehensive FlippyModule tests."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = FlippyModule(width=28, height=7, address=1)
        assert module.width == 28
        assert module.height == 7
        assert module.address == 1
        assert len(module.content) == 28 * 7
        assert all(bit == 0 for bit in module.content)

    def test_module_set_get_content_simple(self):
        """Test setting and getting content."""
        module = FlippyModule(width=3, height=2, address=1)
        content = [[1, 0, 1], [0, 1, 0]]
        module.set_content(content)
        result = module.get_content()
        assert result == content

    def test_module_set_content_wrong_height(self):
        """Test setting content with wrong height."""
        module = FlippyModule(width=3, height=2, address=1)
        content = [[1, 0, 1]]  # Only 1 row instead of 2
        with pytest.raises(ValueError, match="height"):
            module.set_content(content)

    def test_module_set_content_wrong_width(self):
        """Test setting content with wrong width."""
        module = FlippyModule(width=3, height=2, address=1)
        content = [[1, 0], [0, 1]]  # Only 2 columns instead of 3
        with pytest.raises(ValueError, match="width"):
            module.set_content(content)

    def test_module_set_content_all_zeros(self):
        """Test setting all zeros."""
        module = FlippyModule(width=4, height=2, address=1)
        content = [[0, 0, 0, 0], [0, 0, 0, 0]]
        module.set_content(content)
        assert module.content == [0] * 8

    def test_module_set_content_all_ones(self):
        """Test setting all ones."""
        module = FlippyModule(width=4, height=2, address=1)
        content = [[1, 1, 1, 1], [1, 1, 1, 1]]
        module.set_content(content)
        assert module.content == [1] * 8

    def test_module_fetch_serial_command_flush(self):
        """Test generating serial command with flush."""
        module = FlippyModule(width=8, height=1, address=5)
        module.set_content([[1, 0, 1, 0, 1, 0, 1, 0]])
        command = module.fetch_serial_command(flush=True)

        # START_BYTES_FLUSH (2) + ADDRESS (1) + DATA (1 byte) + END_BYTES (1) = 5 bytes
        assert len(command) == 5
        assert command[0:2] == bytes([0x80, 0x83])
        assert command[2] == 5
        assert command[-1] == 0x8F

    def test_module_fetch_serial_command_buffer(self):
        """Test generating serial command with buffer."""
        module = FlippyModule(width=8, height=1, address=3)
        module.set_content([[1, 1, 1, 1, 1, 1, 1, 1]])
        command = module.fetch_serial_command(flush=False)

        assert command[0:2] == bytes([0x80, 0x84])  # START_BYTES_BUFFER
        assert command[2] == 3
        assert command[-1] == 0x8F

    def test_module_serial_command_data_correctness(self):
        """Test that serial command data is correctly packed."""
        module = FlippyModule(width=8, height=1, address=1)
        module.set_content([[1, 0, 0, 0, 0, 0, 0, 0]])
        command = module.fetch_serial_command()

        # Data should be at index 3
        assert command[3] == 0x01  # Little-endian: first bit is LSB

    def test_module_different_addresses(self):
        """Test modules with different addresses."""
        for address in [1, 5, 10, 255]:
            module = FlippyModule(width=2, height=2, address=address)
            command = module.fetch_serial_command()
            assert command[2] == address


# =============================================================================
# Panel Tests
# =============================================================================


class TestPanel:
    """Comprehensive Panel tests."""

    def test_panel_single_module(self):
        """Test panel with single module."""
        panel = Panel(layout=[[1]], module_width=28, module_height=7)
        assert panel.n_rows == 1
        assert panel.n_cols == 1
        assert panel.total_width == 28
        assert panel.total_height == 7

    def test_panel_two_modules_stacked(self):
        """Test panel with two modules stacked vertically."""
        panel = Panel(layout=[[1], [2]], module_width=28, module_height=7)
        assert panel.n_rows == 2
        assert panel.n_cols == 1
        assert panel.total_width == 28
        assert panel.total_height == 14

    def test_panel_two_modules_side_by_side(self):
        """Test panel with two modules side by side."""
        panel = Panel(layout=[[1, 2]], module_width=28, module_height=7)
        assert panel.n_rows == 1
        assert panel.n_cols == 2
        assert panel.total_width == 56
        assert panel.total_height == 7

    def test_panel_four_modules_grid(self):
        """Test panel with 2x2 grid of modules."""
        panel = Panel(layout=[[1, 2], [3, 4]], module_width=28, module_height=7)
        assert panel.n_rows == 2
        assert panel.n_cols == 2
        assert panel.total_width == 56
        assert panel.total_height == 14

    def test_panel_invalid_layout_empty(self):
        """Test that empty layout is rejected."""
        with pytest.raises(ValueError, match="non-empty"):
            Panel(layout=[], module_width=28, module_height=7)

        with pytest.raises(ValueError, match="non-empty"):
            Panel(layout=[[]], module_width=28, module_height=7)

    def test_panel_invalid_layout_not_rectangular(self):
        """Test that non-rectangular layout is rejected."""
        with pytest.raises(ValueError, match="rectangular"):
            Panel(layout=[[1, 2], [3]], module_width=28, module_height=7)

    def test_panel_dimensions_property(self):
        """Test dimensions property returns (height, width)."""
        panel = Panel(layout=[[1, 2], [3, 4]], module_width=10, module_height=5)
        height, width = panel.dimensions
        assert height == 10  # 2 rows * 5
        assert width == 20  # 2 cols * 10

    def test_panel_set_get_content_simple(self):
        """Test setting and getting panel content."""
        panel = Panel(layout=[[1]], module_width=2, module_height=2)
        content = [[1, 0], [0, 1]]
        panel.set_content(content)
        result = panel.get_content()
        assert result == content

    def test_panel_set_content_wrong_dimensions(self):
        """Test setting content with wrong dimensions."""
        panel = Panel(layout=[[1]], module_width=2, module_height=2)

        # Wrong height
        with pytest.raises(ValueError, match="height"):
            panel.set_content([[1, 0]])

        # Wrong width
        with pytest.raises(ValueError, match="width"):
            panel.set_content([[1], [0]])

    def test_panel_set_content_multiple_modules(self):
        """Test setting content across multiple modules."""
        panel = Panel(layout=[[1, 2]], module_width=2, module_height=2)
        # 2x4 total (2 modules side by side)
        content = [[1, 0, 1, 0], [0, 1, 0, 1]]
        panel.set_content(content)
        result = panel.get_content()
        assert result == content

    def test_panel_serial_command_generation(self):
        """Test that panel generates valid serial commands."""
        panel = Panel(layout=[[1], [2]], module_width=2, module_height=2)
        content = [[1, 0], [0, 1], [1, 1], [0, 0]]
        serial_data = panel.set_content(content)

        # Should have 2 modules worth of commands
        # Each command: START(2) + ADDR(1) + DATA(1) + END(1) = 5 bytes
        assert len(serial_data) == 10

        # Check structure of first command
        assert serial_data[0:2] == bytes([0x80, 0x83])
        assert serial_data[4] == 0x8F

        # Check structure of second command
        assert serial_data[5:7] == bytes([0x80, 0x83])
        assert serial_data[9] == 0x8F

    def test_panel_set_content_from_frame(self):
        """Test setting content from packed frame data."""
        panel = Panel(layout=[[1]], module_width=2, module_height=2)
        bits = [1, 0, 1, 0]
        packed = pack_bits_little_endian(bits)

        serial_data = panel.set_content_from_frame(packed, width=2, height=2)
        assert len(serial_data) > 0

        # Verify content was set correctly
        result = panel.get_content()
        assert result == [[1, 0], [1, 0]]

    def test_panel_set_content_from_frame_wrong_dimensions(self):
        """Test setting frame with wrong dimensions."""
        panel = Panel(layout=[[1]], module_width=2, module_height=2)
        bits = [1, 0] * 6
        packed = pack_bits_little_endian(bits)

        with pytest.raises(ValueError, match="dimensions"):
            panel.set_content_from_frame(packed, width=3, height=4)


# =============================================================================
# SerialConnection Tests
# =============================================================================


class TestSerialConnection:
    """Test SerialConnection wrapper."""

    def test_serial_dev_mode(self):
        """Test serial in dev mode."""
        conn = SerialConnection(dev_mode=True)
        assert conn.dev_mode is True
        assert conn._serial is None

        # Should not raise error
        conn.write(b"test")
        conn.close()

    def test_serial_no_device(self):
        """Test serial with no device."""
        conn = SerialConnection(device=None, dev_mode=False)
        assert conn._serial is None

        conn.write(b"test")  # Should not crash
        conn.close()

    @patch("flipdot.driver.hardware.serial.Serial")
    def test_serial_with_device(self, mock_serial_class):
        """Test serial with device."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/ttyUSB0", baudrate=57600, dev_mode=False)

        mock_serial_class.assert_called_once_with("/dev/ttyUSB0", 57600, timeout=1)
        assert conn._serial == mock_serial

    @patch("flipdot.driver.hardware.serial.Serial")
    def test_serial_write(self, mock_serial_class):
        """Test writing to serial."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/ttyUSB0", dev_mode=False)
        conn.write(b"test data")

        mock_serial.write.assert_called_once_with(b"test data")

    @patch("flipdot.driver.hardware.serial.Serial")
    def test_serial_close(self, mock_serial_class):
        """Test closing serial connection."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/ttyUSB0", dev_mode=False)
        conn.close()

        mock_serial.close.assert_called_once()


# =============================================================================
# ContentState Tests
# =============================================================================


class TestContentState:
    """Test ContentState internal class."""

    def test_state_initialization(self):
        """Test content state initialization."""
        content = create_test_content(num_frames=3)
        state = ContentState(content)

        assert state.frame_index == 0
        assert state.loop_count == 0
        assert state.paused is False
        assert state.time_paused == 0

    def test_state_current_frame(self):
        """Test getting current frame."""
        content = create_test_content(num_frames=3)
        state = ContentState(content)

        assert state.current_frame == content.frames[0]

        state.frame_index = 1
        assert state.current_frame == content.frames[1]

    def test_state_is_complete_no_loop(self):
        """Test completion detection without looping."""
        content = create_test_content(num_frames=2, loop=False)
        state = ContentState(content)

        assert state.is_complete is False

        state.frame_index = 1
        assert state.is_complete is True

    def test_state_is_complete_infinite_loop(self):
        """Test that infinite loop never completes."""
        frames = [create_test_frame(duration_ms=100)]
        content = Content(
            content_id="test",
            frames=frames,
            playback=PlaybackMode(loop=True, loop_count=None),
        )
        state = ContentState(content)

        state.frame_index = 0
        state.loop_count = 100
        assert state.is_complete is False

    def test_state_is_complete_limited_loop(self):
        """Test completion with limited loops."""
        frames = [create_test_frame(duration_ms=100)]
        content = Content(
            content_id="test",
            frames=frames,
            playback=PlaybackMode(loop=True, loop_count=3),
        )
        state = ContentState(content)

        state.frame_index = 0
        state.loop_count = 2
        assert state.is_complete is False

        state.loop_count = 3
        assert state.is_complete is True

    def test_state_advance_frame_with_duration(self):
        """Test advancing frames with duration."""
        content = create_test_content(num_frames=2)
        content.frames[0].duration_ms = 50  # 50ms duration
        state = ContentState(content)

        # Should not advance immediately
        assert state.advance_frame() is False
        assert state.frame_index == 0

        # Wait for duration
        time.sleep(0.06)
        assert state.advance_frame() is True
        assert state.frame_index == 1

    def test_state_advance_frame_no_duration(self):
        """Test that frames with no duration don't advance."""
        frame = create_test_frame()
        frame.duration_ms = None
        content = Content(content_id="test", frames=[frame])
        state = ContentState(content)

        assert state.advance_frame() is False
        assert state.frame_index == 0

    def test_state_pause_resume(self):
        """Test pausing and resuming."""
        content = create_test_content()
        state = ContentState(content)

        assert state.paused is False

        state.pause()
        assert state.paused is True
        assert state.paused_at is not None

        time.sleep(0.01)

        state.resume()
        assert state.paused is False
        assert state.time_paused > 0

    def test_state_reset(self):
        """Test resetting state."""
        content = create_test_content(num_frames=3)
        state = ContentState(content)

        state.frame_index = 2
        state.loop_count = 5
        state.time_paused = 1.5

        state.reset()

        assert state.frame_index == 0
        assert state.loop_count == 0
        assert state.time_paused == 0


# =============================================================================
# ContentQueue Tests
# =============================================================================


class TestContentQueue:
    """Comprehensive ContentQueue tests."""

    def test_queue_initialization(self):
        """Test queue starts empty."""
        queue = ContentQueue()
        assert not queue.has_content()
        assert queue.get_current_content_id() is None
        assert len(queue.queue) == 0
        assert len(queue.interrupted) == 0

    def test_queue_add_to_empty(self):
        """Test adding content to empty queue."""
        queue = ContentQueue()
        content = create_test_content("test-1")
        queue.add_content(content)

        assert queue.has_content()
        assert queue.get_current_content_id() == "test-1"

    def test_queue_priority_interrupt(self):
        """Test higher priority interrupts lower priority."""
        queue = ContentQueue()

        # Add low priority
        low = create_test_content("low", priority=0, interruptible=True)
        queue.add_content(low)
        assert queue.get_current_content_id() == "low"

        # Add high priority
        high = create_test_content("high", priority=10)
        queue.add_content(high)

        # Should have switched
        assert queue.get_current_content_id() == "high"
        assert len(queue.interrupted) == 1
        assert queue.interrupted[0].content.content_id == "low"

    def test_queue_non_interruptible(self):
        """Test that non-interruptible content can't be interrupted."""
        queue = ContentQueue()

        # Add non-interruptible content
        content = create_test_content("locked", priority=0, interruptible=False)
        queue.add_content(content)

        # Try to interrupt with higher priority
        high = create_test_content("high", priority=10)
        queue.add_content(high)

        # Should NOT have switched
        assert queue.get_current_content_id() == "locked"
        assert len(queue.queue) == 1  # High priority in queue
        assert len(queue.interrupted) == 0

    def test_queue_resume_after_interrupt(self):
        """Test resuming interrupted content."""
        queue = ContentQueue()

        # Add base content
        base = create_test_content("base", priority=0, interruptible=True)
        queue.add_content(base)

        # Interrupt with notification
        notif_frames = [create_test_frame(duration_ms=10)]
        notif = Content(
            content_id="notif",
            frames=notif_frames,
            playback=PlaybackMode(priority=10, loop=False),
        )
        queue.add_content(notif)

        assert queue.get_current_content_id() == "notif"

        # Wait for notification to complete
        time.sleep(0.02)
        queue.update()

        # Should resume base content
        assert queue.get_current_content_id() == "base"

    def test_queue_multiple_in_queue(self):
        """Test multiple items in queue."""
        queue = ContentQueue()

        # All same priority, should queue in order
        for i in range(3):
            content = create_test_content(f"content-{i}", priority=0)
            queue.add_content(content)

        assert queue.get_current_content_id() == "content-0"
        assert len(queue.queue) == 2

    def test_queue_priority_ordering(self):
        """Test queue maintains priority order."""
        queue = ContentQueue()

        # Add initial content
        queue.add_content(create_test_content("current", priority=10))

        # Add various priorities to queue
        queue.add_content(create_test_content("low", priority=5))
        queue.add_content(create_test_content("high", priority=15))
        queue.add_content(create_test_content("medium", priority=10))

        # Queue should be ordered by priority (highest first)
        priorities = [state.content.playback.priority for state in queue.queue]
        assert priorities == sorted(priorities, reverse=True)

    def test_queue_clear(self):
        """Test clearing the queue."""
        queue = ContentQueue()

        queue.add_content(create_test_content("c1"))
        queue.add_content(create_test_content("c2"))
        queue.add_content(create_test_content("c3"))

        queue.clear()

        assert not queue.has_content()
        assert len(queue.queue) == 0
        assert len(queue.interrupted) == 0

    def test_queue_update_advances_frames(self):
        """Test that update advances frames."""
        queue = ContentQueue()

        frame = create_test_frame(duration_ms=10)
        content = Content(content_id="test", frames=[frame, frame])
        queue.add_content(content)

        initial_idx = queue.current.frame_index
        time.sleep(0.02)
        queue.update()

        assert queue.current.frame_index > initial_idx

    def test_queue_replace_by_id(self):
        """Test replacing content by ID."""
        queue = ContentQueue()

        content1 = create_test_content("test", num_frames=1)
        queue.add_content(content1)

        content2 = create_test_content("test", num_frames=2)
        replaced = queue.replace_if_same_id(content2)

        assert replaced is True
        assert len(queue.current.content.frames) == 2

    def test_queue_replace_not_found(self):
        """Test replacing content that doesn't exist."""
        queue = ContentQueue()

        content1 = create_test_content("test1")
        queue.add_content(content1)

        content2 = create_test_content("test2")
        replaced = queue.replace_if_same_id(content2)

        assert replaced is False


# =============================================================================
# ContentClient Tests
# =============================================================================


class TestContentClient:
    """Comprehensive ContentClient tests."""

    def test_client_initialization(self):
        """Test client initialization."""
        auth = AuthConfig(type="api_key", key="test-key")
        client = ContentClient("http://example.com/content", auth)

        assert client.endpoint == "http://example.com/content"
        assert client.auth == auth
        assert client.last_poll_time is None

    def test_client_build_headers_api_key(self):
        """Test building headers with API key auth."""
        auth = AuthConfig(type="api_key", key="secret-key", header_name="X-API-Key")
        client = ContentClient("http://example.com", auth)

        headers = client._build_headers()
        assert headers["X-API-Key"] == "secret-key"
        assert "Content-Type" in headers

    def test_client_build_headers_bearer(self):
        """Test building headers with bearer token auth."""
        auth = AuthConfig(type="bearer", token="bearer-token")
        client = ContentClient("http://example.com", auth)

        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer bearer-token"

    def test_client_should_poll_initially(self):
        """Test that client should poll initially."""
        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        assert client.should_poll() is True

    def test_client_should_poll_after_interval(self):
        """Test polling interval logic."""
        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        client.last_poll_time = time.time()
        client.poll_interval_ms = 100

        # Should not poll immediately
        assert client.should_poll() is False

        # Should poll after interval
        time.sleep(0.12)
        assert client.should_poll() is True

    def test_client_get_next_poll_delay(self):
        """Test calculating next poll delay."""
        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        client.last_poll_time = time.time()
        client.poll_interval_ms = 1000

        delay = client.get_next_poll_delay_ms()
        assert 0 <= delay <= 1000

    @patch("flipdot.driver.client.urlopen")
    def test_client_fetch_success(self, mock_urlopen):
        """Test successful content fetch."""
        content = create_test_content()
        response = ContentResponse(
            status=ResponseStatus.UPDATED, content=content, poll_interval_ms=30000
        )

        mock_response = Mock()
        mock_response.read.return_value = response.model_dump_json().encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        result = client.fetch_content()

        assert result is not None
        assert result.status == ResponseStatus.UPDATED
        assert client.consecutive_errors == 0

    @patch("flipdot.driver.client.urlopen")
    def test_client_fetch_http_error(self, mock_urlopen):
        """Test handling HTTP errors."""
        mock_urlopen.side_effect = HTTPError(
            "http://example.com", 404, "Not Found", {}, None
        )

        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        result = client.fetch_content()

        assert result is None
        assert client.consecutive_errors == 1

    @patch("flipdot.driver.client.urlopen")
    def test_client_fetch_auth_error(self, mock_urlopen):
        """Test handling authentication errors."""
        mock_urlopen.side_effect = HTTPError(
            "http://example.com", 401, "Unauthorized", {}, None
        )

        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        result = client.fetch_content()

        assert result is None
        assert client.consecutive_errors == 1

    @patch("flipdot.driver.client.urlopen")
    def test_client_fetch_network_error(self, mock_urlopen):
        """Test handling network errors."""
        mock_urlopen.side_effect = URLError("Network unreachable")

        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        result = client.fetch_content()

        assert result is None
        assert client.consecutive_errors == 1

    @patch("flipdot.driver.client.urlopen")
    def test_client_fetch_invalid_json(self, mock_urlopen):
        """Test handling invalid JSON response."""
        mock_response = Mock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        result = client.fetch_content()

        assert result is None
        assert client.consecutive_errors == 1

    def test_client_reset_poll_timer(self):
        """Test resetting poll timer."""
        auth = AuthConfig()
        client = ContentClient("http://example.com", auth)

        client.reset_poll_timer()
        assert client.last_poll_time is not None


# =============================================================================
# ErrorHandler Tests
# =============================================================================


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_handler_keep_last(self):
        """Test keep_last fallback."""
        handler = ErrorHandler(ErrorFallback.KEEP_LAST)

        # No previous content
        assert handler.get_fallback_response() is None

        # With previous content
        content = create_test_content()
        response = ContentResponse(
            status=ResponseStatus.UPDATED, content=content, poll_interval_ms=30000
        )
        handler.set_last_successful(response)

        fallback = handler.get_fallback_response()
        assert fallback is not None
        assert fallback.content.content_id == content.content_id

    def test_handler_blank(self):
        """Test blank fallback."""
        handler = ErrorHandler(ErrorFallback.BLANK)

        fallback = handler.get_fallback_response()
        assert fallback is not None
        assert fallback.status == ResponseStatus.CLEAR

    def test_handler_error_message(self):
        """Test error_message fallback."""
        handler = ErrorHandler(ErrorFallback.ERROR_MESSAGE)

        fallback = handler.get_fallback_response()
        assert fallback is not None
        assert fallback.status == ResponseStatus.CLEAR
        # In the future this might generate an error message frame


# =============================================================================
# DriverConfig Tests
# =============================================================================


class TestDriverConfig:
    """Comprehensive DriverConfig tests."""

    def test_config_minimal(self):
        """Test minimal valid configuration."""
        config = DriverConfig(poll_endpoint="http://localhost:8000")
        assert config.poll_endpoint == "http://localhost:8000"
        assert config.enable_push is False
        assert config.dev_mode is False

    def test_config_full(self):
        """Test full configuration."""
        config = DriverConfig(
            poll_endpoint="http://example.com",
            poll_interval_ms=60000,
            enable_push=True,
            push_port=9000,
            push_host="127.0.0.1",
            auth=AuthConfig(type="api_key", key="secret"),
            serial_device="/dev/ttyUSB0",
            serial_baudrate=115200,
            module_layout=[[1, 2], [3, 4]],
            module_width=14,
            module_height=8,
            error_fallback=ErrorFallback.BLANK,
            dev_mode=True,
            log_level="DEBUG",
        )

        assert config.poll_interval_ms == 60000
        assert config.push_port == 9000
        assert config.serial_baudrate == 115200
        assert config.module_width == 14
        assert config.error_fallback == ErrorFallback.BLANK
        assert config.log_level == "DEBUG"

    def test_config_invalid_poll_interval(self):
        """Test invalid poll interval."""
        with pytest.raises(ValueError):
            DriverConfig(poll_endpoint="http://example.com", poll_interval_ms=500)

    def test_config_invalid_port(self):
        """Test invalid port numbers."""
        with pytest.raises(ValueError):
            DriverConfig(poll_endpoint="http://example.com", push_port=0)

        with pytest.raises(ValueError):
            DriverConfig(poll_endpoint="http://example.com", push_port=70000)

    def test_config_serialization(self):
        """Test config serialization."""
        config = DriverConfig(
            poll_endpoint="http://example.com",
            serial_device="/dev/ttyUSB0",
            module_layout=[[1], [2]],
        )

        json_str = config.model_dump_json()
        parsed = DriverConfig.model_validate_json(json_str)

        assert parsed.poll_endpoint == config.poll_endpoint
        assert parsed.serial_device == config.serial_device


# =============================================================================
# PushServer Tests
# =============================================================================


class TestPushServer:
    """Test PushServer."""

    def test_server_initialization(self):
        """Test server initialization."""
        auth = AuthConfig(type="api_key", key="test")
        callback = Mock()

        server = PushServer("127.0.0.1", 8888, auth, callback)

        assert server.host == "127.0.0.1"
        assert server.port == 8888
        assert server.running is False

    def test_server_start_stop(self):
        """Test starting and stopping server."""
        auth = AuthConfig(type="api_key", key="test")
        callback = Mock()

        server = PushServer("127.0.0.1", 0, auth, callback)  # Port 0 = random port
        server.start()

        time.sleep(0.1)
        assert server.running is True

        server.stop()
        time.sleep(0.1)
        assert server.running is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_frame_pipeline(self):
        """Test complete pipeline from frame creation to serial output."""
        # Create a frame
        width, height = 28, 7
        bits = [1 if (i + j) % 2 else 0 for i in range(height) for j in range(width)]
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(data_b64=b64, width=width, height=height, duration_ms=1000)

        # Create content
        content = Content(
            content_id="test",
            frames=[frame],
            playback=PlaybackMode(loop=False, priority=0),
        )

        # Add to queue
        queue = ContentQueue()
        queue.add_content(content)

        # Get frame from queue
        current_frame = queue.update()
        assert current_frame is not None

        # Convert to serial data
        panel = Panel(layout=[[1]], module_width=width, module_height=height)
        serial_data = panel.set_content_from_frame(
            current_frame.decode_data(), width, height
        )

        # Verify serial data structure
        assert len(serial_data) > 0
        assert serial_data[0:2] == bytes([0x80, 0x83])
        assert serial_data[-1] == 0x8F

    def test_interrupt_and_resume_workflow(self):
        """Test interrupt and resume workflow."""
        queue = ContentQueue()

        # Add base content
        base_frame = create_test_frame(duration_ms=50)
        base = Content(
            content_id="base",
            frames=[base_frame] * 10,
            playback=PlaybackMode(loop=True, priority=0, interruptible=True),
        )
        queue.add_content(base)

        # Advance a few frames
        time.sleep(0.06)
        queue.update()
        base_frame_idx = queue.current.frame_index

        # Interrupt with notification
        notif_frame = create_test_frame(duration_ms=20)
        notif = Content(
            content_id="notification",
            frames=[notif_frame],
            playback=PlaybackMode(loop=False, priority=10),
        )
        queue.add_content(notif)

        # Should be showing notification
        assert queue.get_current_content_id() == "notification"

        # Wait for notification to complete
        time.sleep(0.03)
        queue.update()

        # Should resume base content
        assert queue.get_current_content_id() == "base"

    def test_content_response_to_queue_pipeline(self):
        """Test processing content response into queue."""
        # Simulate server response
        content = create_test_content("clock")
        response = ContentResponse(
            status=ResponseStatus.UPDATED, content=content, poll_interval_ms=30000
        )

        # Process response
        queue = ContentQueue()
        if response.status == ResponseStatus.UPDATED and response.content:
            queue.add_content(response.content)

        assert queue.has_content()
        assert queue.get_current_content_id() == "clock"
