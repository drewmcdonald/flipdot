"""
Example script showing how to generate content for the flipdot driver.

This demonstrates:
- Creating frames with packed bit data
- Building content with playback configuration
- Creating content responses
- Serializing to JSON for the API
"""

import base64
import json


def pack_bits_little_endian(bits: list[int]) -> bytes:
    """Pack a list of bits into bytes using little-endian bit order."""
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits) and bits[i + j]:
                byte |= 1 << j
        result.append(byte)
    return bytes(result)


def create_frame(
    width: int, height: int, pattern: list[list[int]], duration_ms: int = None
):
    """
    Create a frame from a 2D bit pattern.

    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        pattern: 2D list of bits (0 or 1)
        duration_ms: How long to display (None = indefinite)

    Returns:
        Frame dictionary
    """
    # Flatten the pattern
    bits = []
    for row in pattern:
        bits.extend(row)

    # Pack and encode
    packed = pack_bits_little_endian(bits)
    b64 = base64.b64encode(packed).decode()

    frame = {
        "data_b64": b64,
        "width": width,
        "height": height,
    }

    if duration_ms is not None:
        frame["duration_ms"] = duration_ms

    return frame


def example_static_content():
    """Create a simple static content (checkerboard pattern)."""
    # 14x56 display (two 7x28 modules stacked)
    width, height = 56, 14

    # Create a checkerboard pattern
    pattern = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append((x + y) % 2)
        pattern.append(row)

    frame = create_frame(width, height, pattern, duration_ms=None)

    content = {
        "content_id": "checkerboard-static",
        "frames": [frame],
        "playback": {
            "loop": False,
            "priority": 0,
            "interruptible": True,
        },
    }

    response = {
        "status": "updated",
        "content": content,
        "poll_interval_ms": 60000,
    }

    return response


def example_animation():
    """Create an animated content (moving bar)."""
    width, height = 56, 14
    frames = []

    # Create 10 frames of a vertical bar moving across the screen
    for i in range(10):
        pattern = []
        for y in range(height):
            row = []
            for x in range(width):
                # Bar is 4 pixels wide, moves 5 pixels per frame
                bar_x = (i * 5) % width
                row.append(1 if bar_x <= x < bar_x + 4 else 0)
            pattern.append(row)

        frame = create_frame(width, height, pattern, duration_ms=100)
        frames.append(frame)

    content = {
        "content_id": "moving-bar-animation",
        "frames": frames,
        "playback": {
            "loop": True,
            "loop_count": None,  # Infinite loop
            "priority": 0,
            "interruptible": True,
        },
    }

    response = {
        "status": "updated",
        "content": content,
        "poll_interval_ms": 30000,
    }

    return response


def example_notification():
    """Create a high-priority notification."""
    width, height = 56, 14

    # Blinking pattern (2 frames)
    frames = []

    # Frame 1: All white
    pattern_on = [[1] * width for _ in range(height)]
    frames.append(create_frame(width, height, pattern_on, duration_ms=500))

    # Frame 2: All black
    pattern_off = [[0] * width for _ in range(height)]
    frames.append(create_frame(width, height, pattern_off, duration_ms=500))

    content = {
        "content_id": "notification-blink",
        "frames": frames,
        "playback": {
            "loop": True,
            "loop_count": 5,  # Blink 5 times
            "priority": 10,  # High priority
            "interruptible": False,  # Can't be interrupted
        },
    }

    response = {
        "status": "updated",
        "content": content,
        "poll_interval_ms": 5000,  # Check more frequently for notifications
    }

    return response


def example_no_change():
    """Create a no-change response."""
    response = {
        "status": "no_change",
        "poll_interval_ms": 30000,
    }
    return response


def example_clear():
    """Create a clear display response."""
    response = {
        "status": "clear",
        "poll_interval_ms": 30000,
    }
    return response


def main():
    """Generate example content files."""
    examples = {
        "static_checkerboard.json": example_static_content(),
        "animation_moving_bar.json": example_animation(),
        "notification_blink.json": example_notification(),
        "no_change.json": example_no_change(),
        "clear.json": example_clear(),
    }

    for filename, data in examples.items():
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Generated {filename}")

    print("\nExample JSON for checkerboard:")
    print(json.dumps(example_static_content(), indent=2))


if __name__ == "__main__":
    main()
