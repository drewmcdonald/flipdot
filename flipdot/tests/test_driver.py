"""
Comprehensive tests for the flipdot driver implementation.
"""

import base64
import json
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from flipdot.hardware import (
    FlippyModule,
    Panel,
    SerialConnection,
    pack_bits_little_endian,
)
from flipdot.models import (
    Content,
    ContentResponse,
    DriverConfig,
    Frame,
    PlaybackMode,
    ResponseStatus,
)
from flipdot.queue import ContentQueue, ContentState

# =============================================================================
# Test Utilities
# =============================================================================


def create_test_frame(
    width: int = 2, height: int = 2, duration_ms: int = 1000
) -> Frame:
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
    loop: bool = False,
    loop_count: int | None = None,
) -> Content:
    """Create test content with specified parameters."""
    frames = [create_test_frame() for _ in range(num_frames)]
    playback = (
        PlaybackMode(loop=loop, loop_count=loop_count)
        if loop
        else PlaybackMode(loop=loop)
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
        assert packed == b""

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
        metadata: dict[str, object] = {
            "frame_id": "test-123",
            "timestamp": "2024-01-01",
        }
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
            playlist=[content],
            poll_interval_ms=30000,
        )
        assert response.status == ResponseStatus.UPDATED
        assert len(response.playlist) == 1

    def test_response_updated_without_content_fails(self):
        """Test that updated status requires non-empty playlist."""
        with pytest.raises(ValueError, match="playlist must be non-empty"):
            ContentResponse(status=ResponseStatus.UPDATED, playlist=[])

    def test_response_clear(self):
        """Test clear response."""
        response = ContentResponse(status=ResponseStatus.CLEAR)
        assert response.status == ResponseStatus.CLEAR
        assert len(response.playlist) == 0

    def test_response_invalid_poll_interval(self):
        """Test invalid poll intervals."""
        with pytest.raises(ValueError):
            ContentResponse(status=ResponseStatus.CLEAR, poll_interval_ms=500)

        with pytest.raises(ValueError):
            ContentResponse(status=ResponseStatus.CLEAR, poll_interval_ms=-1000)

    def test_response_serialization(self):
        """Test response serialization."""
        content = create_test_content()
        response = ContentResponse(
            status=ResponseStatus.UPDATED, playlist=[content], poll_interval_ms=30000
        )
        json_str = response.model_dump_json()
        parsed = ContentResponse.model_validate_json(json_str)
        assert parsed.status == response.status
        assert len(parsed.playlist) == 1
        assert parsed.playlist[0].content_id == content.content_id


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

        # START(2) + ADDR(1) + DATA(8 cols) + END(1) = 12 bytes
        assert len(command) == 12
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
        # Each command: START(2) + ADDR(1) + DATA(2 cols) + END(1) = 6
        assert len(serial_data) == 12

        # Check structure of first command
        assert serial_data[0:2] == bytes([0x80, 0x83])
        assert serial_data[5] == 0x8F

        # Check structure of second command
        assert serial_data[6:8] == bytes([0x80, 0x83])
        assert serial_data[11] == 0x8F

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

    @patch("flipdot.hardware.serial.Serial")
    def test_serial_with_device(self, mock_serial_class):
        """Test serial with device."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/ttyUSB0", baudrate=57600, dev_mode=False)

        mock_serial_class.assert_called_once_with("/dev/ttyUSB0", 57600, timeout=1)
        assert conn._serial == mock_serial

    @patch("flipdot.hardware.serial.Serial")
    def test_serial_write(self, mock_serial_class):
        """Test writing to serial."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/ttyUSB0", dev_mode=False)
        conn.write(b"test data")

        mock_serial.write.assert_called_once_with(b"test data")

    @patch("flipdot.hardware.serial.Serial")
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
        assert state.frame_start_time > 0

    def test_state_current_frame(self):
        """Test getting current frame."""
        content = create_test_content(num_frames=3)
        state = ContentState(content)

        assert state.current_frame == content.frames[0]

        state.frame_index = 1
        assert state.current_frame == content.frames[1]

    def test_state_is_complete_no_loop(self):
        """Test completion detection without looping."""
        # Use very short duration so we can test completion
        frame1 = create_test_frame(duration_ms=10)
        frame2 = create_test_frame(duration_ms=10)
        content = Content(
            content_id="test",
            frames=[frame1, frame2],
            playback=PlaybackMode(loop=False),
        )
        state = ContentState(content)

        assert state.is_complete is False

        # Move to last frame
        state.frame_index = 1
        state.frame_start_time = time.time()

        # Not complete yet (duration hasn't elapsed)
        assert state.is_complete is False

        # Wait for duration to elapse
        time.sleep(0.02)
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

    def test_queue_set_playlist_single(self):
        """Test setting playlist with a single item."""
        queue = ContentQueue()
        content = create_test_content("test-1")
        queue.set_playlist([content])

        assert queue.has_content()
        assert queue.get_current_content_id() == "test-1"

    def test_queue_set_playlist_multiple(self):
        """Test setting playlist with multiple items."""
        queue = ContentQueue()
        items = [create_test_content(f"item-{i}") for i in range(3)]
        queue.set_playlist(items)

        assert queue.get_current_content_id() == "item-0"
        assert len(queue.queue) == 2

    def test_queue_set_playlist_preserves_state(self):
        """Test that set_playlist preserves state when content_id matches."""
        queue = ContentQueue()
        content1 = create_test_content("same-id", num_frames=3)
        queue.set_playlist([content1])

        # Advance the frame index
        queue.current.frame_index = 2

        # Set playlist again with the same content_id
        content2 = create_test_content("same-id", num_frames=3)
        queue.set_playlist([content2])

        # Frame index should be preserved
        assert queue.current.frame_index == 2

    def test_queue_set_playlist_replaces(self):
        """Test that set_playlist starts fresh with different content_id."""
        queue = ContentQueue()
        content1 = create_test_content("old-id", num_frames=3)
        queue.set_playlist([content1])

        queue.current.frame_index = 2

        # Set playlist with a different content_id
        content2 = create_test_content("new-id", num_frames=3)
        queue.set_playlist([content2])

        # Should start fresh
        assert queue.get_current_content_id() == "new-id"
        assert queue.current.frame_index == 0

    def test_queue_update_returns_frame(self):
        """Test that update returns the current frame."""
        queue = ContentQueue()
        content = create_test_content("test")
        queue.set_playlist([content])

        frame = queue.update()
        assert frame is not None
        assert frame == content.frames[0]

    def test_queue_update_advances_and_moves_to_next(self):
        """Test that update advances frames and moves to next content."""
        queue = ContentQueue()

        # Create two contents with short timed frames
        frame1 = create_test_frame(duration_ms=10)
        content1 = Content(
            content_id="first",
            frames=[frame1],
            playback=PlaybackMode(loop=False),
        )
        frame2 = create_test_frame(duration_ms=None)
        content2 = Content(
            content_id="second",
            frames=[frame2],
            playback=PlaybackMode(loop=False),
        )
        queue.set_playlist([content1, content2])

        assert queue.get_current_content_id() == "first"

        # Wait for first content to complete
        time.sleep(0.02)
        queue.update()

        # Should have moved to the second content
        assert queue.get_current_content_id() == "second"

    def test_queue_clear(self):
        """Test clearing the queue."""
        queue = ContentQueue()
        items = [create_test_content(f"item-{i}") for i in range(3)]
        queue.set_playlist(items)

        queue.clear()

        assert not queue.has_content()
        assert len(queue.queue) == 0

    def test_queue_set_playlist_empty(self):
        """Test that empty playlist clears the queue."""
        queue = ContentQueue()
        content = create_test_content("test")
        queue.set_playlist([content])
        assert queue.has_content()

        queue.set_playlist([])
        assert not queue.has_content()


# =============================================================================
# DriverConfig Tests
# =============================================================================


class TestDriverConfig:
    """Comprehensive DriverConfig tests."""

    def test_config_minimal(self):
        """Test minimal valid configuration."""
        config = DriverConfig(convex_url="https://example.convex.cloud")
        assert config.convex_url == "https://example.convex.cloud"

    def test_config_full(self):
        """Test full configuration."""
        config = DriverConfig(
            convex_url="https://example.convex.cloud",
            display_name="test-display",
            serial_device="/dev/ttyUSB0",
            serial_baudrate=115200,
            module_layout=[[1, 2], [3, 4]],
            module_width=14,
            module_height=8,
            dev_mode=True,
            log_level="DEBUG",
        )

        assert config.convex_url == "https://example.convex.cloud"
        assert config.display_name == "test-display"
        assert config.serial_device == "/dev/ttyUSB0"
        assert config.serial_baudrate == 115200
        assert config.module_layout == [[1, 2], [3, 4]]
        assert config.module_width == 14
        assert config.module_height == 8
        assert config.dev_mode is True
        assert config.log_level == "DEBUG"

    def test_config_serialization(self):
        """Test config serialization."""
        config = DriverConfig(
            convex_url="https://example.convex.cloud",
            serial_device="/dev/ttyUSB0",
            module_layout=[[1], [2]],
        )

        json_str = config.model_dump_json()
        parsed = DriverConfig.model_validate_json(json_str)

        assert parsed.convex_url == config.convex_url
        assert parsed.serial_device == config.serial_device


# =============================================================================
# Content Validation / Security Limit Tests
# =============================================================================


class TestContentValidation:
    """Tests for content security limits and validation."""

    def test_max_frames_per_content_exceeded(self):
        """Test that exceeding MAX_FRAMES_PER_CONTENT raises an error."""
        num_frames = Content.MAX_FRAMES_PER_CONTENT + 1
        frames = [create_test_frame() for _ in range(num_frames)]
        with pytest.raises(ValueError, match="Too many frames"):
            Content(content_id="too-many-frames", frames=frames)

    def test_max_frames_per_content_at_limit(self):
        """Test that exactly MAX_FRAMES_PER_CONTENT is allowed."""
        num_frames = Content.MAX_FRAMES_PER_CONTENT
        frames = [create_test_frame() for _ in range(num_frames)]
        content = Content(content_id="at-limit", frames=frames)
        assert len(content.frames) == num_frames

    def test_max_total_bytes_exceeded(self):
        """Test that exceeding MAX_TOTAL_BYTES raises an error."""
        # 1024x1024 = 131072 bytes per frame. Need enough frames to exceed 5MB.
        width, height = 1024, 1024
        bits = [0] * (width * height)
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()
        frame = Frame(data_b64=b64, width=width, height=height, duration_ms=100)

        frame_size = len(packed)
        num_frames = (Content.MAX_TOTAL_BYTES // frame_size) + 1
        frames = [frame] * num_frames

        with pytest.raises(ValueError, match="Content too large"):
            Content(content_id="too-large", frames=frames)

    def test_max_metadata_bytes_exceeded_on_frame(self):
        """Test that frame metadata exceeding MAX_METADATA_BYTES raises an error."""
        large_value = "x" * (Content.MAX_METADATA_BYTES + 1)
        frame = create_test_frame()
        bits = [1, 0] * ((frame.width * frame.height) // 2)
        packed = pack_bits_little_endian(bits[: frame.width * frame.height])
        b64 = base64.b64encode(packed).decode()

        large_metadata: dict[str, object] = {"large_key": large_value}
        oversized_frame = Frame(
            data_b64=b64,
            width=frame.width,
            height=frame.height,
            duration_ms=100,
            metadata=large_metadata,
        )

        with pytest.raises(ValueError, match="metadata too large"):
            Content(content_id="big-meta", frames=[oversized_frame])

    def test_max_metadata_bytes_exceeded_on_content(self):
        """Test that content-level metadata exceeding MAX_METADATA_BYTES raises."""
        large_value = "x" * (Content.MAX_METADATA_BYTES + 1)
        large_metadata: dict[str, object] = {"large_key": large_value}
        frame = create_test_frame()

        with pytest.raises(ValueError, match="Content metadata too large"):
            Content(
                content_id="big-content-meta",
                frames=[frame],
                metadata=large_metadata,
            )

    def test_inconsistent_frame_dimensions(self):
        """Test that frames with different dimensions raise an error."""
        frame_2x2 = create_test_frame(width=2, height=2)
        frame_3x3 = create_test_frame(width=3, height=3)

        with pytest.raises(ValueError, match="dimensions"):
            Content(content_id="mismatched", frames=[frame_2x2, frame_3x3])

    def test_validate_display_dimensions_match(self):
        """Test validate_display_dimensions passes with matching dimensions."""
        content = create_test_content()
        frame = content.frames[0]
        content.validate_display_dimensions(frame.width, frame.height)

    def test_validate_display_dimensions_mismatch(self):
        """Test validate_display_dimensions raises with mismatched dimensions."""
        content = create_test_content()
        with pytest.raises(ValueError, match="frame dimensions"):
            content.validate_display_dimensions(999, 999)


# =============================================================================
# PlaybackMode Validation Tests
# =============================================================================


class TestPlaybackModeValidation:
    """Tests for PlaybackMode validation rules."""

    def test_loop_count_with_loop_false_raises(self):
        """Test that setting loop_count with loop=False raises ValueError."""
        with pytest.raises(ValueError, match="loop_count can only be set when loop=True"):
            PlaybackMode(loop=False, loop_count=5)

    def test_loop_count_with_loop_true_allowed(self):
        """Test that setting loop_count with loop=True is valid."""
        mode = PlaybackMode(loop=True, loop_count=5)
        assert mode.loop_count == 5

    def test_loop_count_none_with_loop_false_allowed(self):
        """Test that loop_count=None with loop=False is valid."""
        mode = PlaybackMode(loop=False, loop_count=None)
        assert mode.loop_count is None


# =============================================================================
# Serial Reconnection Tests
# =============================================================================


class TestSerialReconnection:
    """Tests for serial reconnection and error handling logic."""

    def test_should_attempt_reconnect_timing(self):
        """Test _should_attempt_reconnect respects backoff timing."""
        conn = SerialConnection(dev_mode=True)
        conn.dev_mode = False
        conn.device = "/dev/fake"
        conn.reconnect_backoff_ms = 1000

        # Just attempted: should not reconnect
        conn.last_reconnect_attempt = time.time()
        assert conn._should_attempt_reconnect() is False

        # Long ago: should reconnect
        conn.last_reconnect_attempt = time.time() - 10
        assert conn._should_attempt_reconnect() is True

    @patch("flipdot.hardware.serial.Serial")
    def test_try_reconnect_success(self, mock_serial_class):
        """Test _try_reconnect succeeds when serial connects."""
        mock_serial_class.return_value = Mock()
        conn = SerialConnection(dev_mode=True)
        conn.dev_mode = False
        conn.device = "/dev/fake"
        conn.baudrate = 57600
        conn._serial = None
        conn.last_reconnect_attempt = 0.0
        conn.reconnect_backoff_ms = 0

        result = conn._try_reconnect()
        assert result is True
        assert conn._serial is not None
        assert conn.consecutive_failures == 0

    @patch("flipdot.hardware.serial.Serial")
    def test_try_reconnect_failure_increases_backoff(self, mock_serial_class):
        """Test _try_reconnect fails and increases backoff."""
        mock_serial_class.side_effect = OSError("no device")
        conn = SerialConnection(dev_mode=True)
        conn.dev_mode = False
        conn.device = "/dev/fake"
        conn.baudrate = 57600
        conn._serial = None
        conn.last_reconnect_attempt = 0.0
        initial_backoff = conn.reconnect_backoff_ms

        result = conn._try_reconnect()
        assert result is False
        assert conn._serial is None
        assert conn.reconnect_backoff_ms == min(
            initial_backoff * 2, conn.limits.serial.max_reconnect_backoff_ms
        )

    def test_try_reconnect_respects_backoff(self):
        """Test _try_reconnect returns False when backoff hasn't elapsed."""
        conn = SerialConnection(dev_mode=True)
        conn.dev_mode = False
        conn.device = "/dev/fake"
        conn.reconnect_backoff_ms = 60000
        conn.last_reconnect_attempt = time.time()

        result = conn._try_reconnect()
        assert result is False

    @patch("flipdot.hardware.serial.Serial")
    def test_write_incomplete_write(self, mock_serial_class):
        """Test write returns False on incomplete write."""
        mock_serial = Mock()
        mock_serial.write.return_value = 2  # Only 2 of 5 bytes written
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/fake", baudrate=57600, dev_mode=False)
        result = conn.write(b"hello")
        assert result is False
        assert conn.consecutive_failures == 1

    @patch("flipdot.hardware.serial.Serial")
    def test_write_exception_closes_serial(self, mock_serial_class):
        """Test write handles OSError by closing serial and marking for reconnect."""
        mock_serial = Mock()
        mock_serial.write.side_effect = OSError("device disconnected")
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/fake", baudrate=57600, dev_mode=False)
        result = conn.write(b"hello")

        assert result is False
        assert conn.consecutive_failures == 1
        assert conn._serial is None
        mock_serial.close.assert_called_once()

    @patch("flipdot.hardware.serial.Serial")
    def test_write_consecutive_failures_accumulate(self, mock_serial_class):
        """Test that consecutive write failures accumulate the failure counter."""
        mock_serial = Mock()
        mock_serial.write.side_effect = OSError("device disconnected")
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/fake", baudrate=57600, dev_mode=False)

        conn.write(b"hello")
        assert conn.consecutive_failures == 1

        # After the first OSError, _serial is None and _try_reconnect is called.
        # Make reconnect fail so failures accumulate without being reset.
        mock_serial_class.side_effect = OSError("still no device")

        conn.write(b"hello")
        assert conn.consecutive_failures == 2

        conn.write(b"hello")
        assert conn.consecutive_failures == 3

    @patch("flipdot.hardware.serial.Serial")
    def test_write_success_resets_failures(self, mock_serial_class):
        """Test that a successful write resets the failure counter."""
        mock_serial = Mock()
        mock_serial.write.return_value = 5
        mock_serial_class.return_value = mock_serial

        conn = SerialConnection(device="/dev/fake", baudrate=57600, dev_mode=False)
        conn.consecutive_failures = 5

        result = conn.write(b"hello")
        assert result is True
        assert conn.consecutive_failures == 0


# =============================================================================
# FlipDotDriver Tests
# =============================================================================


class TestFlipDotDriver:
    """Tests for the main FlipDotDriver class."""

    def _make_config(self, **overrides: object) -> DriverConfig:
        """Create a DriverConfig with dev_mode defaults for testing."""
        defaults: dict[str, object] = {
            "convex_url": "https://test.convex.cloud",
            "display_name": "test-display",
            "dev_mode": True,
            "module_layout": [[1]],
            "module_width": 2,
            "module_height": 2,
            "log_level": "WARNING",
        }
        defaults.update(overrides)
        return DriverConfig(**defaults)

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_init_wires_up_components(self, mock_convex_cls: MagicMock) -> None:
        """__init__ creates Panel, SerialConnection, ContentQueue, and ConvexContentClient."""
        from flipdot.main import FlipDotDriver

        config = self._make_config()
        driver = FlipDotDriver(config)

        # Panel created with correct layout
        assert driver.panel.n_rows == 1
        assert driver.panel.n_cols == 1
        height, width = driver.panel.dimensions
        assert width == 2
        assert height == 2

        # Serial is in dev_mode
        assert driver.serial.dev_mode is True

        # Queue initialised
        assert driver.queue is not None
        assert not driver.queue.has_content()

        # ConvexContentClient constructed and started
        mock_convex_cls.assert_called_once_with(
            "https://test.convex.cloud", "test-display"
        )
        mock_convex_cls.return_value.start.assert_called_once()

        # running starts False
        assert driver.running is False

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_init_uses_default_limits(self, mock_convex_cls: MagicMock) -> None:
        """__init__ without explicit limits uses DEFAULT_LIMITS."""
        from flipdot.config import DEFAULT_LIMITS
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        assert driver.limits is DEFAULT_LIMITS

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_init_uses_custom_limits(self, mock_convex_cls: MagicMock) -> None:
        """__init__ with explicit limits uses those limits."""
        from flipdot.config import DriverLimits, LoopTiming
        from flipdot.main import FlipDotDriver

        custom = DriverLimits(loop=LoopTiming(sleep_interval_seconds=0.5))
        driver = FlipDotDriver(self._make_config(), limits=custom)
        assert driver.limits is custom
        assert driver.limits.loop.sleep_interval_seconds == 0.5

    # -- _poll_for_content ------------------------------------------------

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_poll_for_content_with_update(self, mock_convex_cls: MagicMock) -> None:
        """_poll_for_content sets playlist on queue when UPDATED."""
        from flipdot.main import FlipDotDriver

        config = self._make_config()
        driver = FlipDotDriver(config)

        content = create_test_content("c1")
        response = ContentResponse(
            status=ResponseStatus.UPDATED, playlist=[content]
        )
        driver._convex_client.wait_for_update.return_value = response

        driver._poll_for_content(timeout=0.0)

        assert driver.queue.has_content()
        assert driver.queue.get_current_content_id() == "c1"

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_poll_for_content_rejects_bad_dimensions(
        self, mock_convex_cls: MagicMock
    ) -> None:
        """_poll_for_content rejects playlist with mismatched dimensions."""
        from flipdot.main import FlipDotDriver

        config = self._make_config(module_width=2, module_height=2)
        driver = FlipDotDriver(config)

        # Create content with dimensions that don't match the 2x2 display
        wrong_content = create_test_content("bad")
        # Manually override frame dimensions to trigger mismatch
        wrong_content.frames[0].width = 99
        wrong_content.frames[0].height = 99

        response = ContentResponse(
            status=ResponseStatus.UPDATED, playlist=[wrong_content]
        )
        driver._convex_client.wait_for_update.return_value = response

        driver._poll_for_content(timeout=0.0)

        # Queue should remain empty because dimensions didn't match
        assert not driver.queue.has_content()

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_poll_for_content_with_clear(self, mock_convex_cls: MagicMock) -> None:
        """_poll_for_content clears queue and display on CLEAR status."""
        from flipdot.main import FlipDotDriver

        config = self._make_config()
        driver = FlipDotDriver(config)

        # Pre-populate queue
        driver.queue.set_playlist([create_test_content("c1")])
        assert driver.queue.has_content()

        response = ContentResponse(status=ResponseStatus.CLEAR, playlist=[])
        driver._convex_client.wait_for_update.return_value = response

        driver._poll_for_content(timeout=0.0)

        assert not driver.queue.has_content()

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_poll_for_content_none_response(self, mock_convex_cls: MagicMock) -> None:
        """_poll_for_content does nothing when response is None."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        driver._convex_client.wait_for_update.return_value = None

        driver._poll_for_content(timeout=0.0)
        assert not driver.queue.has_content()

    # -- _clear_display ---------------------------------------------------

    @patch("flipdot.convex_client.ConvexContentClient")
    @patch("flipdot.hardware.serial.Serial")
    def test_clear_display_writes_blank_frame(
        self, mock_serial_cls: MagicMock, mock_convex_cls: MagicMock
    ) -> None:
        """_clear_display writes an all-zero frame to serial."""
        from flipdot.main import FlipDotDriver

        config = self._make_config(
            dev_mode=False, serial_device="/dev/ttyFAKE"
        )
        driver = FlipDotDriver(config)
        mock_serial_instance = mock_serial_cls.return_value

        driver._clear_display()

        mock_serial_instance.write.assert_called_once()
        data = mock_serial_instance.write.call_args[0][0]
        assert isinstance(data, bytes)
        assert len(data) > 0

    # -- _render_frame ----------------------------------------------------

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_render_frame_writes_to_serial(self, mock_convex_cls: MagicMock) -> None:
        """_render_frame gets frame from queue and writes to serial."""
        from flipdot.main import FlipDotDriver

        config = self._make_config()
        driver = FlipDotDriver(config)

        content = create_test_content("c1")
        driver.queue.set_playlist([content])

        # Mock serial write
        driver.serial.write = MagicMock(return_value=True)

        driver._render_frame()

        driver.serial.write.assert_called_once()
        written = driver.serial.write.call_args[0][0]
        assert isinstance(written, bytes)

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_render_frame_empty_queue_noop(self, mock_convex_cls: MagicMock) -> None:
        """_render_frame does nothing when queue is empty."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        driver.serial.write = MagicMock()

        driver._render_frame()

        driver.serial.write.assert_not_called()

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_render_frame_handles_serial_failure(
        self, mock_convex_cls: MagicMock
    ) -> None:
        """_render_frame logs error but does not raise when serial write fails."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        content = create_test_content("c1")
        driver.queue.set_playlist([content])
        driver.serial.write = MagicMock(return_value=False)

        # Should not raise
        driver._render_frame()

        driver.serial.write.assert_called_once()

    # -- _calculate_next_sleep_s ------------------------------------------

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_calculate_next_sleep_s_default(self, mock_convex_cls: MagicMock) -> None:
        """_calculate_next_sleep_s returns the configured interval."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        result = driver._calculate_next_sleep_s()
        assert result == driver.limits.loop.sleep_interval_seconds

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_calculate_next_sleep_s_custom(self, mock_convex_cls: MagicMock) -> None:
        """_calculate_next_sleep_s respects custom limits."""
        from flipdot.config import DriverLimits, LoopTiming
        from flipdot.main import FlipDotDriver

        custom = DriverLimits(loop=LoopTiming(sleep_interval_seconds=1.5))
        driver = FlipDotDriver(self._make_config(), limits=custom)
        assert driver._calculate_next_sleep_s() == 1.5

    # -- start / stop lifecycle -------------------------------------------

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_start_and_stop_lifecycle(self, mock_convex_cls: MagicMock) -> None:
        """start() runs the loop and stop() cleanly shuts down."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        mock_client = driver._convex_client

        # Use stop() to break the loop, which is the normal shutdown path.
        call_count = 0

        def side_effect(timeout: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                driver.stop()
            return None

        mock_client.wait_for_update.side_effect = side_effect

        driver.serial.write = MagicMock(return_value=True)
        driver.serial.close = MagicMock()

        driver.start()

        # After start returns, driver should be stopped
        assert driver.running is False
        mock_client.close.assert_called_once()
        driver.serial.close.assert_called_once()

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_stop_idempotent(self, mock_convex_cls: MagicMock) -> None:
        """Calling stop() when not running is a no-op."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        assert driver.running is False

        # Should not raise
        driver.stop()
        driver.stop()

        # close() should not have been called since running was False
        driver._convex_client.close.assert_not_called()

    @patch("flipdot.convex_client.ConvexContentClient")
    def test_stop_clears_display_and_closes(self, mock_convex_cls: MagicMock) -> None:
        """stop() clears display, closes convex client and serial."""
        from flipdot.main import FlipDotDriver

        driver = FlipDotDriver(self._make_config())
        driver.running = True

        driver.serial.write = MagicMock(return_value=True)
        driver.serial.close = MagicMock()

        driver.stop()

        assert driver.running is False
        # _clear_display writes to serial
        driver.serial.write.assert_called()
        driver.serial.close.assert_called_once()
        driver._convex_client.close.assert_called_once()


# =============================================================================
# load_config Tests
# =============================================================================


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_valid(self, tmp_path: object) -> None:
        """load_config loads a valid JSON config file."""
        from pathlib import Path

        from flipdot.main import load_config

        p = Path(str(tmp_path)) / "config.json"
        data = {
            "convex_url": "https://test.convex.cloud",
            "display_name": "my-display",
            "dev_mode": True,
            "module_layout": [[1, 2]],
            "module_width": 28,
            "module_height": 7,
        }
        p.write_text(json.dumps(data))

        config = load_config(str(p))

        assert config.convex_url == "https://test.convex.cloud"
        assert config.display_name == "my-display"
        assert config.dev_mode is True
        assert config.module_layout == [[1, 2]]

    def test_load_config_missing_file(self) -> None:
        """load_config raises FileNotFoundError for missing file."""
        from flipdot.main import load_config

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config("/no/such/path/config.json")

    def test_load_config_invalid_json(self, tmp_path: object) -> None:
        """load_config raises error for invalid JSON."""
        from pathlib import Path

        from flipdot.main import load_config

        p = Path(str(tmp_path)) / "bad.json"
        p.write_text("not json at all {{{")

        with pytest.raises(Exception):
            load_config(str(p))

    def test_load_config_missing_required_fields(self, tmp_path: object) -> None:
        """load_config raises validation error when required fields are missing."""
        from pathlib import Path

        from flipdot.main import load_config

        p = Path(str(tmp_path)) / "partial.json"
        # Missing required convex_url
        p.write_text(json.dumps({"dev_mode": True}))

        with pytest.raises(Exception):
            load_config(str(p))
