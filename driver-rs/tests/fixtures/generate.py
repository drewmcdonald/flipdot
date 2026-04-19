"""
Regenerate canonical JSON fixtures from the Python Pydantic models.

Run from repo root:
    poetry run python driver-rs/tests/fixtures/generate.py

Any change to Python models that affects the wire format should be reflected
here, then the Rust tests re-run. The purpose of these fixtures is to catch
divergence between the Python and Rust serde implementations.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from flipdot.models import (
    Content,
    ContentResponse,
    DriverConfig,
    Frame,
    PlaybackMode,
    ResponseStatus,
)

FIXTURES = Path(__file__).parent


def write(name: str, payload: object) -> None:
    path = FIXTURES / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {path.relative_to(FIXTURES.parent.parent.parent)}")


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def frame_single_pixel_28x14() -> Frame:
    # Bit 0 set -> pixel (0,0) on. 28*14 = 392 bits = 49 bytes.
    raw = bytearray(49)
    raw[0] = 0x01
    return Frame(data_b64=b64(bytes(raw)), width=28, height=14, duration_ms=500)


def frame_all_on_28x14() -> Frame:
    raw = bytes([0xFF] * 49)
    return Frame(data_b64=b64(raw), width=28, height=14, duration_ms=None)


def main() -> None:
    # Frame fixtures
    single = frame_single_pixel_28x14()
    all_on = frame_all_on_28x14()
    write("frame_single_pixel.json", single.model_dump(mode="json"))
    write("frame_all_on_indefinite.json", all_on.model_dump(mode="json"))

    # PlaybackMode fixtures
    write(
        "playback_default.json",
        PlaybackMode().model_dump(mode="json"),
    )
    write(
        "playback_loop_infinite.json",
        PlaybackMode(loop=True).model_dump(mode="json"),
    )
    write(
        "playback_loop_count.json",
        PlaybackMode(loop=True, loop_count=3).model_dump(mode="json"),
    )

    # Content fixtures
    content_two_frames = Content(
        content_id="test-content-1",
        frames=[single, all_on],
        playback=PlaybackMode(loop=True, loop_count=2),
        metadata={"source": "fixture"},
    )
    write("content_two_frames.json", content_two_frames.model_dump(mode="json"))

    # ContentResponse fixtures
    updated = ContentResponse(
        status=ResponseStatus.UPDATED,
        playlist=[content_two_frames],
        poll_interval_ms=30000,
    )
    cleared = ContentResponse(
        status=ResponseStatus.CLEAR,
        playlist=[],
        poll_interval_ms=30000,
    )
    write("response_updated.json", updated.model_dump(mode="json"))
    write("response_clear.json", cleared.model_dump(mode="json"))

    # DriverConfig fixture matches flipdot/config.example.json
    cfg = DriverConfig(
        convex_url="https://your-deployment.convex.cloud",
        display_name="main",
        serial_device="/dev/ttyUSB0",
        serial_baudrate=57600,
        module_layout=[[1], [2]],
        module_width=28,
        module_height=7,
        dev_mode=False,
        log_level="INFO",
    )
    write("driver_config.json", cfg.model_dump(mode="json"))


if __name__ == "__main__":
    main()
