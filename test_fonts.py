#!/usr/bin/env python3
"""Test script to verify font rendering works."""

from flipdot import font


def print_bitmap(bitmap: list[list[int]]) -> None:
    """Print a bitmap to the console."""
    for row in bitmap:
        print("".join("█" if bit else " " for bit in row))


def main() -> None:
    """Test font rendering."""
    print("Available fonts:", font.list_fonts())
    print()

    test_text = "Hello!"

    print("=" * 50)
    print("BASELINE-ALIGNED FONTS (glyphs pre-padded)")
    print("=" * 50)
    print()

    for font_name in font.list_fonts():
        f = font.get_font(font_name)
        print(f"Font: {font_name}")
        print(f"Height: {f.height}px, Baseline at: {f.baseline_offset}px from top")
        print("-" * 40)

        bitmap = font.render_text(test_text, font_name)
        print_bitmap(bitmap)
        print(f"Size: {len(bitmap)}h x {len(bitmap[0]) if bitmap else 0}w")
        print()


if __name__ == "__main__":
    main()
