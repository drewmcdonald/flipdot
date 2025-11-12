"""
Bitmap font rendering for flipdot displays.

This module provides simple bitmap font loading and text rendering.
Fonts are pre-rendered to JSON files for fast loading without FreeType dependency.
"""

from __future__ import annotations

import json
from pathlib import Path

# Font registry: maps font names to loaded DotFont instances
_font_registry: dict[str, DotFont] = {}


class DotFont:
    """A bitmap font loaded from pre-rendered JSON data."""

    def __init__(
        self,
        name: str,
        height: int,
        space_width: int,
        char_spacing: int,
        glyphs: dict[str, list[list[int]]],
        baseline_offset: int | None = None,
    ):
        """
        Initialize a bitmap font.

        Args:
            name: Font name
            height: Font height in pixels
            space_width: Width of space character in pixels
            char_spacing: Spacing between characters in pixels
            glyphs: Character bitmaps (char -> 2D list of bits)
            baseline_offset: Distance from top of character to baseline (pixels)
        """
        self.name = name
        self.height = height
        self.space_width = space_width
        self.char_spacing = char_spacing
        self.glyphs = glyphs
        self.baseline_offset = baseline_offset if baseline_offset is not None else height

    @classmethod
    def load(cls, json_path: str | Path) -> DotFont:
        """
        Load a font from a JSON file.

        Args:
            json_path: Path to pre-rendered font JSON

        Returns:
            Loaded DotFont instance
        """
        with open(json_path) as f:
            data = json.load(f)

        return cls(
            name=data["name"],
            height=data["height"],
            space_width=data["space_width"],
            char_spacing=data["char_spacing"],
            glyphs=data["glyphs"],
            baseline_offset=data.get("baseline_offset"),
        )

    def get_char(self, char: str) -> list[list[int]]:
        """
        Get the bitmap for a character.

        Args:
            char: Character to render

        Returns:
            2D list of bits, shape [height, width]
            Returns space glyph if character not found
        """
        if char in self.glyphs:
            return self.glyphs[char]

        # Fall back to space for unknown characters
        return self.glyphs.get(" ", [])

    def render_text(self, text: str) -> list[list[int]]:
        """
        Render text to a bitmap.

        All glyphs are pre-padded to font height with baseline alignment,
        so this just concatenates them horizontally.

        Args:
            text: Text to render

        Returns:
            2D list of bits, shape [font_height, total_width]
        """
        if not text:
            return [[]]

        # Collect all character bitmaps
        char_bitmaps: list[list[list[int]]] = []
        for char in text:
            char_bitmaps.append(self.get_char(char))

        # Calculate total width
        total_width = 0
        for i, bitmap in enumerate(char_bitmaps):
            if not bitmap or not bitmap[0]:
                # Empty glyph (like space)
                total_width += self.space_width
            else:
                total_width += len(bitmap[0])

            # Add spacing between characters (but not after last char)
            if i < len(char_bitmaps) - 1:
                # Only add spacing if neither current nor next char is space
                current_is_space = text[i] == " "
                next_is_space = i + 1 < len(text) and text[i + 1] == " "
                if not current_is_space and not next_is_space:
                    total_width += self.char_spacing

        # Build the output bitmap (height is font height - all glyphs are pre-padded)
        result: list[list[int]] = [[0] * total_width for _ in range(self.height)]

        x_offset = 0
        for i, (char, bitmap) in enumerate(zip(text, char_bitmaps)):
            if not bitmap or not bitmap[0]:
                # Empty glyph (space)
                x_offset += self.space_width
                continue

            char_width = len(bitmap[0])

            # Copy character bitmap to result
            # All glyphs are already font height and baseline-aligned
            for row_idx in range(self.height):
                for col_idx in range(char_width):
                    if row_idx < len(bitmap) and col_idx < len(bitmap[row_idx]):
                        result[row_idx][x_offset + col_idx] = bitmap[row_idx][col_idx]

            x_offset += char_width

            # Add spacing between characters
            if i < len(char_bitmaps) - 1:
                current_is_space = text[i] == " "
                next_is_space = i + 1 < len(text) and text[i + 1] == " "
                if not current_is_space and not next_is_space:
                    x_offset += self.char_spacing

        return result


def load_fonts() -> None:
    """Load all pre-rendered fonts into the registry."""
    fonts_dir = Path(__file__).parent / "rendered"

    if not fonts_dir.exists():
        raise RuntimeError(
            f"Rendered fonts directory not found: {fonts_dir}\n"
            "Run 'python flipdot/font/prerender_fonts.py' to generate fonts"
        )

    for json_file in fonts_dir.glob("*.json"):
        font = DotFont.load(json_file)
        _font_registry[font.name] = font


def get_font(name: str) -> DotFont:
    """
    Get a font by name.

    Args:
        name: Font name (e.g., "axion_6x7")

    Returns:
        DotFont instance

    Raises:
        KeyError: If font not found
    """
    if not _font_registry:
        load_fonts()

    if name not in _font_registry:
        raise KeyError(
            f"Font '{name}' not found. Available fonts: {list(_font_registry.keys())}"
        )

    return _font_registry[name]


def list_fonts() -> list[str]:
    """
    List all available font names.

    Returns:
        List of font names
    """
    if not _font_registry:
        load_fonts()

    return list(_font_registry.keys())


def render_text(text: str, font_name: str = "axion_6x7") -> list[list[int]]:
    """
    Convenience function to render text with a font.

    Args:
        text: Text to render
        font_name: Font to use (default: "axion_6x7")

    Returns:
        2D list of bits, shape [font_height, width]
        All glyphs are baseline-aligned within the font height
    """
    font = get_font(font_name)
    return font.render_text(text)
