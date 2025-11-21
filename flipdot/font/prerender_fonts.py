#!/usr/bin/env python3
"""
Font pre-rendering script.

This script uses FreeType to render TTF fonts to bitmap JSON files.
Run this during development/build to generate the bitmap font data.

Requires: pip install freetype-py

Usage: python prerender_fonts.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import freetype
except ImportError:
    print("ERROR: freetype-py is required for font pre-rendering")
    print("Install with: pip install freetype-py")
    sys.exit(1)

# Font configurations matching the original registry
FONTS = {
    "axion_6x7": {
        "file": "axion-6x7-dotmap.ttf",
        "height": 7,
        "space_width": 3,
        "char_spacing": 1,
    },
    "cg_pixel_4x5": {
        "file": "cg-pixel-4x5.ttf",
        "height": 5,
        "space_width": 2,
        "char_spacing": 1,
    },
    "hanover_6x13m": {
        "file": "hanover-6x13m-dotmap.ttf",
        "height": 13,
        "space_width": 3,
        "char_spacing": 1,
    },
}

# Printable ASCII range
ASCII_START = 32  # Space
ASCII_END = 126  # Tilde


def render_char(face: freetype.Face, char: str) -> tuple[list[list[int]], int]:
    """
    Render a single character to a bitmap.

    Args:
        face: FreeType font face
        char: Character to render
        target_height: Target font height in pixels

    Returns:
        Tuple of (2D list of bits, bearing_y in pixels)
        bearing_y is distance from baseline to top of glyph
    """
    # Load the character
    face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]

    bitmap = face.glyph.bitmap
    width = bitmap.width
    rows = bitmap.rows

    # Get baseline bearing (distance from baseline to top of glyph)
    # FreeType returns this in 26.6 fractional pixel format
    bearing_y = face.glyph.metrics.horiBearingY // 64

    if width == 0 or rows == 0:
        # Empty character (like space) - return empty with width of 1
        return [[0] * max(1, width)], bearing_y

    # Convert bitmap buffer to 2D array
    # FreeType mono bitmaps are packed bits (8 pixels per byte)
    result: list[list[int]] = []

    for row_idx in range(rows):
        row_data: list[int] = []
        row_offset = row_idx * bitmap.pitch

        for col_idx in range(width):
            byte_idx = col_idx // 8
            bit_idx = 7 - (col_idx % 8)  # MSB first

            byte_val = bitmap.buffer[row_offset + byte_idx]
            bit = (byte_val >> bit_idx) & 1

            row_data.append(bit)

        result.append(row_data)

    return result, bearing_y


def pad_glyph_to_height(
    glyph: list[list[int]], bearing_y: int, max_bearing: int, target_height: int
) -> list[list[int]]:
    """
    Pad a glyph to target height with baseline alignment.

    Args:
        glyph: Original glyph bitmap
        bearing_y: Distance from baseline to top of this glyph
        max_bearing: Maximum bearing across all glyphs (baseline position)
        target_height: Target height for all glyphs

    Returns:
        Padded glyph bitmap of exactly target_height rows
    """
    if not glyph or not glyph[0]:
        # Empty glyph - return blank rows
        width = len(glyph[0]) if glyph and glyph[0] else 1
        return [[0] * width for _ in range(target_height)]

    glyph_height = len(glyph)
    glyph_width = len(glyph[0])

    # Calculate padding needed at top to align baselines
    top_padding = max_bearing - bearing_y

    # Calculate padding needed at bottom
    bottom_padding = target_height - glyph_height - top_padding

    # Build padded glyph
    result = []

    # Add top padding
    for _ in range(top_padding):
        result.append([0] * glyph_width)

    # Add glyph
    result.extend(glyph)

    # Add bottom padding
    for _ in range(bottom_padding):
        result.append([0] * glyph_width)

    return result


def render_font(
    font_path: Path, target_height: int
) -> tuple[dict[str, list[list[int]]], int]:
    """
    Render all printable ASCII characters for a font.

    All glyphs are padded to target_height with baseline alignment.

    Args:
        font_path: Path to TTF file
        target_height: Target font height in pixels

    Returns:
        Tuple of (dictionary mapping characters to bitmaps, baseline_offset)
        baseline_offset is the distance from top of character cell to baseline
    """
    face = freetype.Face(str(font_path))

    # Set pixel size (height)
    face.set_pixel_sizes(0, int(target_height))

    # First pass: render all glyphs and collect bearings
    raw_glyphs: dict[str, tuple[list[list[int]], int]] = {}
    bearings: list[int] = []

    for code in range(ASCII_START, ASCII_END + 1):
        char = chr(code)
        bitmap, bearing_y = render_char(face, char)
        raw_glyphs[char] = (bitmap, bearing_y)

        # Collect bearings from typical baseline characters
        if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
            bearings.append(bearing_y)

    # Calculate baseline offset: use the maximum bearing_y (top of tallest character)
    # This represents the distance from the top of the character cell to the baseline
    max_bearing = max(bearings) if bearings else target_height

    # Second pass: pad all glyphs to target height with baseline alignment
    glyphs: dict[str, list[list[int]]] = {}
    for char, (bitmap, bearing_y) in raw_glyphs.items():
        glyphs[char] = pad_glyph_to_height(
            bitmap, bearing_y, max_bearing, target_height
        )

    return glyphs, max_bearing


def main() -> None:
    """Generate pre-rendered bitmap fonts."""
    script_dir = Path(__file__).parent
    fonts_dir = script_dir / "fonts"
    output_dir = script_dir / "rendered"

    output_dir.mkdir(exist_ok=True)

    print("Pre-rendering fonts...")
    print()

    for font_name, config in FONTS.items():
        font_path = fonts_dir / config["file"]  # pyright: ignore[reportOperatorIssue]

        if not font_path.exists():
            print(f"⚠ Skipping {font_name}: {font_path} not found")
            continue

        print(f"Rendering {font_name} ({config['file']})...")

        # Render all glyphs and get baseline offset
        glyphs, baseline_offset = render_font(font_path, int(config["height"]))

        # Create font data
        font_data = {
            "name": font_name,
            "source_file": config["file"],
            "height": config["height"],
            "baseline_offset": baseline_offset,
            "space_width": config["space_width"],
            "char_spacing": config["char_spacing"],
            "glyphs": glyphs,
        }

        # Write to JSON
        output_path = output_dir / f"{font_name}.json"
        with open(output_path, "w") as f:
            json.dump(font_data, f, indent=2)

        # Stats
        non_empty = sum(1 for g in glyphs.values() if g)
        print(f"  ✓ Rendered {len(glyphs)} characters ({non_empty} non-empty)")
        print(f"  → Baseline offset: {baseline_offset} pixels from top")
        print(f"  → {output_path}")
        print()

    print("Done!")


if __name__ == "__main__":
    main()
