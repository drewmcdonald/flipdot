/**
 * Font loader for pre-rendered JSON fonts
 * Loads fonts from the Python driver's rendered font files
 */

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
 * Cache of loaded fonts
 */
const fontCache: Map<string, FontData> = new Map();

/**
 * Default display baseline position on 14-pixel display
 * Set at pixel 11 from top, leaving 3 pixels below for descenders
 */
export const DISPLAY_BASELINE = 11;

/**
 * Available font names
 * Note: hanover_6x13m font is too large for Val Town file limits (101K)
 */
export const AVAILABLE_FONTS = ["axion_6x7", "cg_pixel_4x5"];

/**
 * Default font name
 */
export const DEFAULT_FONT = "axion_6x7";

/**
 * Load a font from JSON file
 * Works in both local dev (using Deno.readTextFile) and Val Town (using readFile utility)
 */
export async function loadFont(fontName: string): Promise<FontData> {
  // Check cache first
  if (fontCache.has(fontName)) {
    return fontCache.get(fontName)!;
  }

  // Validate font name
  if (!AVAILABLE_FONTS.includes(fontName)) {
    throw new Error(
      `Unknown font: ${fontName}. Available fonts: ${AVAILABLE_FONTS.join(", ")}`,
    );
  }

  try {
    let fontContent: string;

    // Determine if we're running locally or on Val Town
    const isLocal = import.meta.url.startsWith("file://");

    if (isLocal) {
      // Local development: use Deno's file system APIs
      const currentDir = new URL(".", import.meta.url).pathname;
      const fontPath = `${currentDir}../../fonts/${fontName}.json`;
      fontContent = await Deno.readTextFile(fontPath);
    } else {
      // Val Town: use readFile utility
      const { readFile } = await import("https://esm.town/v/std/utils@85-main/index.ts");
      const fontPath = `/fonts/${fontName}.json`;
      fontContent = await readFile(fontPath, import.meta.url);
    }

    const fontData = JSON.parse(fontContent) as FontData;

    // Cache the font
    fontCache.set(fontName, fontData);

    return fontData;
  } catch (error) {
    throw new Error(`Failed to load font ${fontName}: ${error}`);
  }
}

/**
 * Get a font, loading it if necessary
 * Returns default font if requested font is not available
 */
export async function getFont(fontName?: string): Promise<FontData> {
  const name = fontName || DEFAULT_FONT;

  try {
    return await loadFont(name);
  } catch (error) {
    console.warn(
      `Failed to load font ${name}, falling back to ${DEFAULT_FONT}:`,
      error,
    );
    return await loadFont(DEFAULT_FONT);
  }
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
  xOffset: number,
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
  frameDelayMs: number = 100,
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
 * Render text to a flat bit array (28×14 pixels = 392 bits)
 * Text is centered horizontally, baseline-aligned vertically.
 */
export function renderText(
  font: FontData,
  text: string,
  displayWidth: number,
  displayHeight: number,
): number[] {
  const textWidth = measureText(font, text);

  // Calculate horizontal centering offset
  const xOffset = Math.floor((displayWidth - textWidth) / 2);

  return renderTextAtOffset(font, text, displayWidth, displayHeight, xOffset);
}
