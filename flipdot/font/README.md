# FlipDot Bitmap Fonts

This directory contains pre-rendered bitmap fonts for the FlipDot display driver.

## Available Fonts

All fonts are pixel/dot-matrix fonts designed for displays:

- **axion_6x7** - 7px height, most commonly used (default)
- **cg_pixel_4x5** - 5px height, smaller for dense text
- **hanover_6x13m** - 13px height, tallest/most readable

## Font Sources

Fonts are TrueType (`.ttf`) files located in `fonts/`:
- Created with [FontStruct](https://fontstruct.com/)
- Licensed under FontStruct Non-Commercial License
- See individual `-readme.txt` and `-license.txt` files for details

## Pre-rendered Format

At build time, TTF fonts are rendered to JSON bitmaps in `rendered/`:
- Contains all printable ASCII characters (32-126)
- Each character is a 2D array of bits (0 or 1)
- No runtime FreeType dependency needed

## Usage

```python
from flipdot import font

# Simple text rendering
bitmap = font.render_text("Hello!", font_name="axion_6x7")

# Get a specific font
f = font.get_font("cg_pixel_4x5")
bitmap = f.render_text("Compact text")

# List available fonts
print(font.list_fonts())
```

## Generating Fonts

To re-generate the pre-rendered JSON files:

```bash
# Install FreeType (development only)
poetry add --group dev freetype-py

# Run the pre-rendering script
poetry run python flipdot/font/prerender_fonts.py
```

This is only needed if:
- Adding new fonts
- Modifying font parameters (spacing, etc.)
- Updating to new font versions

## Integration with Hardware

The rendered bitmaps are compatible with `flipdot.hardware.Panel`:

```python
from flipdot import font
from flipdot.hardware import Panel

# Render text
bitmap = font.render_text("Hello")

# Send to display
panel = Panel(layout=[[1], [2]])
serial_data = panel.set_content(bitmap)
```

## Adding New Fonts

1. Add the `.ttf` file to `fonts/`
2. Add font config to `prerender_fonts.py` FONTS dict
3. Run `poetry run python flipdot/font/prerender_fonts.py`
4. The font will be automatically available via `font.get_font()`
