#!/usr/bin/env python3
"""
Example: Display text on a flipdot display.

This example shows how to render text using the font system
and send it to the display hardware.
"""

from flipdot import font
from flipdot.hardware import Panel, SerialConnection


def main() -> None:
    """Display text on the flipdot display."""
    # Configure your display
    # This example uses 2 stacked 28x7 modules
    panel = Panel(
        layout=[[1], [2]],  # 2 modules stacked vertically
        module_width=28,
        module_height=7,
    )

    # Serial connection
    # Set dev_mode=True to print to console instead of serial
    serial = SerialConnection(
        device="/dev/ttyUSB0",  # Change to your serial device
        baudrate=57600,
        dev_mode=True,  # Set to False for real hardware
    )

    # Render text with default font (axion_6x7)
    text = "Hi!"
    bitmap = font.render_text(text)

    print(f"Rendered '{text}' to {len(bitmap)}h x {len(bitmap[0])}w bitmap")
    print()

    # Print to console
    for row in bitmap:
        print("".join("█" if bit else " " for bit in row))
    print()

    # Pad bitmap to match display size if needed
    display_height, display_width = panel.dimensions
    if len(bitmap) < display_height or len(bitmap[0]) < display_width:
        print(
            f"Padding bitmap to match display size ({display_height}x{display_width})"
        )
        padded = [[0] * display_width for _ in range(display_height)]

        # Center vertically
        y_offset = (display_height - len(bitmap)) // 2

        # Copy bitmap
        for row_idx, row in enumerate(bitmap):
            for col_idx, bit in enumerate(row):
                if col_idx < display_width:
                    padded[y_offset + row_idx][col_idx] = bit

        bitmap = padded

    # Generate serial command
    serial_data = panel.set_content(bitmap)
    print(f"Generated {len(serial_data)} bytes of serial data")

    # Send to display
    success = serial.write(serial_data)
    if success:
        print("✓ Text sent to display successfully")
    else:
        print("✗ Failed to send to display")


if __name__ == "__main__":
    main()
