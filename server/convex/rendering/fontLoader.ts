/**
 * Font loader for pre-rendered bitmap fonts
 * Adapted for Convex with embedded font data (no async loading)
 */

import { AXION_6X7 } from "../fonts/axion_6x7";
import { CG_PIXEL_4X5 } from "../fonts/cg_pixel_4x5";

/**
 * Font metadata and glyph data
 */
export interface FontData {
  name: string;
  source_file: string;
  height: number;
  baseline_offset: number;
  space_width: number;
  char_spacing: number;
  glyphs: Record<string, number[][]>;
}

/**
 * Default display baseline position on 14-pixel display
 * Set at pixel 11 from top, leaving 3 pixels below for descenders
 */
export const DISPLAY_BASELINE = 11;

/**
 * Available font names
 */
export const AVAILABLE_FONTS = ["axion_6x7", "cg_pixel_4x5"] as const;
export type FontName = (typeof AVAILABLE_FONTS)[number];

/**
 * Default font name
 */
export const DEFAULT_FONT: FontName = "axion_6x7";

/**
 * Embedded font registry
 */
const FONTS: Record<FontName, FontData> = {
  axion_6x7: AXION_6X7,
  cg_pixel_4x5: CG_PIXEL_4X5,
};

/**
 * Get a font by name (synchronous - fonts are embedded)
 * Returns default font if requested font is not available
 */
export function getFont(fontName?: string): FontData {
  const name = (fontName || DEFAULT_FONT) as FontName;

  if (name in FONTS) {
    return FONTS[name];
  }

  console.warn(`Unknown font: ${name}, falling back to ${DEFAULT_FONT}`);
  return FONTS[DEFAULT_FONT];
}

/**
 * Get bitmap for a single character from a font
 * Returns space glyph for unsupported characters
 */
export function renderChar(font: FontData, char: string): number[][] {
  // Try to find the character in the font
  if (char in font.glyphs) {
    return font.glyphs[char];
  }

  // Try uppercase version
  const upperChar = char.toUpperCase();
  if (upperChar in font.glyphs) {
    return font.glyphs[upperChar];
  }

  // Fall back to space
  return font.glyphs[" "] || [];
}

/**
 * Calculate the width of a character in pixels
 */
export function getCharWidth(font: FontData, char: string): number {
  const glyph = renderChar(font, char);
  if (glyph.length === 0) return font.space_width;

  // The glyph is stored as rows, each row is an array of columns
  // Find the maximum width across all rows
  let maxWidth = 0;
  for (const row of glyph) {
    maxWidth = Math.max(maxWidth, row.length);
  }

  return maxWidth;
}

/**
 * Measure text width in pixels (including spacing)
 */
export function measureText(font: FontData, text: string): number {
  if (text.length === 0) return 0;

  let totalWidth = 0;
  for (let i = 0; i < text.length; i++) {
    totalWidth += getCharWidth(font, text[i]);
    if (i < text.length - 1) {
      totalWidth += font.char_spacing;
    }
  }

  return totalWidth;
}

/**
 * Render text at a specific X offset (for scrolling)
 * Returns a flat bit array for the display.
 */
export function renderTextAtOffset(
  font: FontData,
  text: string,
  displayWidth: number,
  displayHeight: number,
  xOffset: number
): number[] {
  // Calculate y-offset to align font baseline to display baseline
  const yOffset = DISPLAY_BASELINE - font.baseline_offset;

  // Initialize empty display buffer
  const bits = new Array(displayWidth * displayHeight).fill(0);

  // Render each character
  let cursorX = xOffset;
  for (let i = 0; i < text.length; i++) {
    const charBitmap = renderChar(font, text[i]);
    const charWidth = getCharWidth(font, text[i]);

    // Draw character to buffer
    for (let row = 0; row < charBitmap.length; row++) {
      const rowData = charBitmap[row];
      for (let col = 0; col < rowData.length; col++) {
        const x = cursorX + col;
        const y = yOffset + row;

        // Bounds check
        if (x >= 0 && x < displayWidth && y >= 0 && y < displayHeight) {
          const bitIndex = y * displayWidth + x;
          bits[bitIndex] = rowData[col];
        }
      }
    }

    cursorX += charWidth + font.char_spacing;
  }

  return bits;
}

/**
 * Generate scrolling animation frames for text
 * Text scrolls from right to left across the display
 */
export function renderScrollingText(
  font: FontData,
  text: string,
  displayWidth: number,
  displayHeight: number,
  frameDelayMs: number = 100
): Array<{ bits: number[]; duration_ms: number }> {
  const textWidth = measureText(font, text);
  const frames: Array<{ bits: number[]; duration_ms: number }> = [];

  // Start position: text completely off-screen to the right
  // End position: text completely off-screen to the left
  const startX = displayWidth;
  const endX = -textWidth;

  // Generate frames scrolling from right to left, one pixel at a time
  for (let x = startX; x >= endX; x--) {
    const bits = renderTextAtOffset(font, text, displayWidth, displayHeight, x);
    frames.push({
      bits,
      duration_ms: frameDelayMs,
    });
  }

  return frames;
}

/**
 * Render text to a flat bit array (28x14 pixels = 392 bits)
 * Text is centered horizontally, baseline-aligned vertically.
 */
export function renderText(
  font: FontData,
  text: string,
  displayWidth: number,
  displayHeight: number
): number[] {
  const textWidth = measureText(font, text);

  // Calculate horizontal centering offset
  const xOffset = Math.floor((displayWidth - textWidth) / 2);

  return renderTextAtOffset(font, text, displayWidth, displayHeight, xOffset);
}
