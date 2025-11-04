"""
Tests for the new driver implementation.
"""

import base64

import pytest

from flipdot.driver.hardware import (
    FlippyModule,
    Panel,
    pack_bits_little_endian,
)
from flipdot.driver.models import (
    Content,
    ContentResponse,
    DriverConfig,
    Frame,
    PlaybackMode,
    ResponseStatus,
)
from flipdot.driver.queue import ContentQueue


class TestBitPacking:
    """Test bit packing/unpacking utilities."""

    def test_pack_bits_simple(self):
        """Test packing a simple bit sequence."""
        bits = [1, 0, 1, 0, 1, 0, 1, 0]  # 0b01010101 = 0x55 (little-endian)
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0x55])

    def test_pack_bits_partial_byte(self):
        """Test packing bits that don't fill a complete byte."""
        bits = [1, 1, 0]  # 0b00000011 = 0x03 (little-endian, padded with zeros)
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0x03])

    def test_pack_bits_multiple_bytes(self):
        """Test packing multiple bytes."""
        bits = [1] * 8 + [0] * 8  # First byte all 1s, second all 0s
        packed = pack_bits_little_endian(bits)
        assert packed == bytes([0xFF, 0x00])


class TestFrame:
    """Test Frame model."""

    def test_frame_validation(self):
        """Test frame creation and validation."""
        # Create a simple 2x2 frame
        bits = [1, 0, 1, 0]  # 2x2 grid
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(
            data_b64=b64,
            width=2,
            height=2,
            duration_ms=1000,
        )

        assert frame.width == 2
        assert frame.height == 2
        assert frame.duration_ms == 1000

    def test_frame_to_bit_array(self):
        """Test converting frame back to bit array."""
        bits = [1, 0, 1, 0]
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(data_b64=b64, width=2, height=2)
        result = frame.to_bit_array()

        assert result == [[1, 0], [1, 0]]

    def test_frame_invalid_base64(self):
        """Test that invalid base64 raises an error."""
        with pytest.raises(ValueError, match="Invalid base64"):
            Frame(data_b64="not-valid-base64!", width=2, height=2)


class TestContent:
    """Test Content model."""

    def test_content_creation(self):
        """Test creating content with frames."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(data_b64=b64, width=2, height=2, duration_ms=1000)
        content = Content(
            content_id="test-1",
            frames=[frame],
            playback=PlaybackMode(loop=True, priority=5),
        )

        assert content.content_id == "test-1"
        assert len(content.frames) == 1
        assert content.playback.loop is True
        assert content.playback.priority == 5


class TestContentResponse:
    """Test ContentResponse model."""

    def test_response_updated(self):
        """Test response with updated status."""
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(data_b64=b64, width=2, height=2, duration_ms=1000)
        content = Content(
            content_id="test-1",
            frames=[frame],
        )

        response = ContentResponse(
            status=ResponseStatus.UPDATED,
            content=content,
            poll_interval_ms=30000,
        )

        assert response.status == ResponseStatus.UPDATED
        assert response.content is not None
        assert response.content.content_id == "test-1"

    def test_response_no_change(self):
        """Test response with no_change status."""
        response = ContentResponse(
            status=ResponseStatus.NO_CHANGE,
            poll_interval_ms=60000,
        )

        assert response.status == ResponseStatus.NO_CHANGE
        assert response.content is None

    def test_response_updated_without_content_fails(self):
        """Test that updated status requires content."""
        with pytest.raises(ValueError, match="content must be provided"):
            ContentResponse(
                status=ResponseStatus.UPDATED,
                content=None,
            )


class TestFlippyModule:
    """Test FlippyModule hardware class."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = FlippyModule(width=28, height=7, address=1)
        assert module.width == 28
        assert module.height == 7
        assert module.address == 1
        assert len(module.content) == 28 * 7

    def test_module_set_get_content(self):
        """Test setting and getting content."""
        module = FlippyModule(width=3, height=2, address=1)
        content = [[1, 0, 1], [0, 1, 0]]
        module.set_content(content)

        result = module.get_content()
        assert result == content

    def test_module_fetch_serial_command(self):
        """Test generating serial command."""
        module = FlippyModule(width=8, height=1, address=1)
        module.set_content([[1, 0, 1, 0, 1, 0, 1, 0]])

        command = module.fetch_serial_command(flush=True)

        # Should have START_BYTES_FLUSH (2) + ADDRESS (1) + DATA (1) + END_BYTES (1)
        assert len(command) == 5
        assert command[0:2] == bytes([0x80, 0x83])  # START_BYTES_FLUSH
        assert command[2] == 1  # address
        assert command[-1] == 0x8F  # END_BYTES


class TestPanel:
    """Test Panel hardware class."""

    def test_panel_initialization(self):
        """Test panel initialization."""
        panel = Panel(layout=[[1, 2], [3, 4]], module_width=28, module_height=7)
        assert panel.n_rows == 2
        assert panel.n_cols == 2
        assert panel.total_width == 56
        assert panel.total_height == 14

    def test_panel_set_get_content(self):
        """Test setting and getting panel content."""
        panel = Panel(layout=[[1], [2]], module_width=2, module_height=2)
        # 4x2 total (2 modules stacked)
        content = [[1, 0], [0, 1], [1, 1], [0, 0]]
        panel.set_content(content)

        result = panel.get_content()
        assert result == content

    def test_panel_set_content_from_frame(self):
        """Test setting content from packed frame data."""
        panel = Panel(layout=[[1]], module_width=2, module_height=2)
        bits = [1, 0, 1, 0]
        packed = pack_bits_little_endian(bits)

        serial_data = panel.set_content_from_frame(packed, width=2, height=2)

        # Should generate valid serial command
        assert len(serial_data) > 0
        assert serial_data[0:2] == bytes([0x80, 0x83])  # START_BYTES_FLUSH


class TestContentQueue:
    """Test ContentQueue."""

    def test_queue_initialization(self):
        """Test queue starts empty."""
        queue = ContentQueue()
        assert not queue.has_content()
        assert queue.get_current_content_id() is None

    def test_queue_add_content(self):
        """Test adding content to empty queue."""
        queue = ContentQueue()
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(data_b64=b64, width=2, height=2, duration_ms=100)
        content = Content(content_id="test-1", frames=[frame])

        queue.add_content(content)

        assert queue.has_content()
        assert queue.get_current_content_id() == "test-1"

    def test_queue_priority_interrupt(self):
        """Test that higher priority content interrupts lower priority."""
        queue = ContentQueue()
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        # Add low priority content
        frame1 = Frame(data_b64=b64, width=2, height=2, duration_ms=100)
        content1 = Content(
            content_id="low",
            frames=[frame1],
            playback=PlaybackMode(priority=0, interruptible=True),
        )
        queue.add_content(content1)
        assert queue.get_current_content_id() == "low"

        # Add high priority content
        frame2 = Frame(data_b64=b64, width=2, height=2, duration_ms=100)
        content2 = Content(
            content_id="high",
            frames=[frame2],
            playback=PlaybackMode(priority=10),
        )
        queue.add_content(content2)

        # Should have switched to high priority
        assert queue.get_current_content_id() == "high"

    def test_queue_clear(self):
        """Test clearing the queue."""
        queue = ContentQueue()
        bits = [1, 0] * 4
        packed = pack_bits_little_endian(bits)
        b64 = base64.b64encode(packed).decode()

        frame = Frame(data_b64=b64, width=2, height=2, duration_ms=100)
        content = Content(content_id="test-1", frames=[frame])
        queue.add_content(content)

        queue.clear()
        assert not queue.has_content()


class TestDriverConfig:
    """Test DriverConfig model."""

    def test_config_minimal(self):
        """Test creating minimal config."""
        config = DriverConfig(poll_endpoint="http://localhost:8000/content")

        assert config.poll_endpoint == "http://localhost:8000/content"
        assert config.poll_interval_ms == 30000
        assert config.enable_push is False

    def test_config_full(self):
        """Test creating full config."""
        config = DriverConfig(
            poll_endpoint="http://example.com/content",
            poll_interval_ms=60000,
            enable_push=True,
            push_port=9000,
            serial_device="/dev/ttyUSB0",
            module_layout=[[1], [2]],
        )

        assert config.enable_push is True
        assert config.push_port == 9000
        assert config.serial_device == "/dev/ttyUSB0"
