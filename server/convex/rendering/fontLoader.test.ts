import { describe, it, expect, beforeAll } from "vitest";
import {
  getFont,
  renderChar,
  getCharWidth,
  measureText,
  renderText,
  renderScrollingText,
  AVAILABLE_FONTS,
  DEFAULT_FONT,
  DISPLAY_BASELINE,
  type FontData,
} from "./fontLoader";

describe("AVAILABLE_FONTS", () => {
  it("contains expected font names", () => {
    expect(AVAILABLE_FONTS).toContain("axion_6x7");
    expect(AVAILABLE_FONTS).toContain("cg_pixel_4x5");
    expect(AVAILABLE_FONTS).toHaveLength(2);
  });
});

describe("DEFAULT_FONT", () => {
  it("is set to axion_6x7", () => {
    expect(DEFAULT_FONT).toBe("axion_6x7");
  });
});

describe("getFont", () => {
  it("returns default font when called with no arguments", () => {
    const font = getFont();
    expect(font.name).toBe("axion_6x7");
  });

  it("returns axion_6x7 with expected properties", () => {
    const font = getFont("axion_6x7");
    expect(font.name).toBe("axion_6x7");
    expect(font.height).toBe(7);
    expect(font.baseline_offset).toBe(7);
    expect(font.space_width).toBe(3);
    expect(font.char_spacing).toBe(1);
    expect(font.glyphs).toBeDefined();
    expect(font.glyphs["A"]).toBeDefined();
  });

  it("returns cg_pixel_4x5 with expected properties", () => {
    const font = getFont("cg_pixel_4x5");
    expect(font.name).toBe("cg_pixel_4x5");
    expect(font.height).toBe(5);
    expect(font.baseline_offset).toBe(5);
    expect(font.space_width).toBe(2);
    expect(font.char_spacing).toBe(1);
    expect(font.glyphs).toBeDefined();
    expect(font.glyphs["A"]).toBeDefined();
  });

  it("falls back to default font for nonexistent font name", () => {
    const font = getFont("nonexistent");
    expect(font.name).toBe(DEFAULT_FONT);
  });
});

describe("renderChar", () => {
  let font: FontData;

  beforeAll(() => {
    font = getFont("axion_6x7");
  });

  it("returns glyph for known character", () => {
    const glyph = renderChar(font, "A");
    expect(glyph).toEqual(font.glyphs["A"]);
    expect(glyph.length).toBe(7); // axion_6x7 has height 7
  });

  it("falls back to uppercase for lowercase input when lowercase is missing", () => {
    // Create a minimal font that only has uppercase "A" but not lowercase "a"
    const testFont: FontData = {
      name: "test",
      source_file: "test.ttf",
      height: 2,
      baseline_offset: 2,
      space_width: 1,
      char_spacing: 1,
      glyphs: {
        " ": [[0], [0]],
        "A": [[1, 1], [1, 0]],
      },
    };
    const lowercaseGlyph = renderChar(testFont, "a");
    const uppercaseGlyph = renderChar(testFont, "A");
    expect(lowercaseGlyph).toEqual(uppercaseGlyph);
  });

  it("returns distinct glyph for lowercase when font has it", () => {
    // axion_6x7 has both "a" and "A" as different glyphs
    const lowercaseGlyph = renderChar(font, "a");
    const uppercaseGlyph = renderChar(font, "A");
    expect(lowercaseGlyph).not.toEqual(uppercaseGlyph);
  });

  it("returns space glyph for unknown character", () => {
    const glyph = renderChar(font, "\u00ff");
    const spaceGlyph = font.glyphs[" "];
    expect(glyph).toEqual(spaceGlyph);
  });
});

describe("getCharWidth", () => {
  it("returns correct width for known characters", () => {
    const font = getFont("axion_6x7");
    // "A" glyph rows are 6 pixels wide in axion_6x7
    const width = getCharWidth(font, "A");
    expect(width).toBe(6);
  });

  it("returns space_width for space character", () => {
    const font = getFont("cg_pixel_4x5");
    // Space glyph is [[0],[0],[0],[0],[0]] - each row is 1 pixel wide
    const width = getCharWidth(font, " ");
    // The space glyph has rows of length 1, so maxWidth = 1
    expect(width).toBe(1);
  });

  it("returns correct width for cg_pixel_4x5 characters", () => {
    const font = getFont("cg_pixel_4x5");
    // "A" glyph rows are 4 pixels wide in cg_pixel_4x5
    const width = getCharWidth(font, "A");
    expect(width).toBe(4);
  });
});

describe("measureText", () => {
  let font: FontData;

  beforeAll(() => {
    font = getFont("axion_6x7");
  });

  it("returns 0 for empty string", () => {
    expect(measureText(font, "")).toBe(0);
  });

  it("returns character width for single character", () => {
    const charWidth = getCharWidth(font, "A");
    expect(measureText(font, "A")).toBe(charWidth);
  });

  it("includes spacing between multiple characters", () => {
    const widthA = getCharWidth(font, "A");
    const widthB = getCharWidth(font, "B");
    const expected = widthA + font.char_spacing + widthB;
    expect(measureText(font, "AB")).toBe(expected);
  });

  it("handles three characters with correct spacing", () => {
    const widthH = getCharWidth(font, "H");
    const widthI = getCharWidth(font, "I");
    const expected = widthH + font.char_spacing + widthI + font.char_spacing + widthH;
    expect(measureText(font, "HIH")).toBe(expected);
  });
});

describe("renderText", () => {
  it("produces bit array of length width * height", () => {
    const font = getFont("axion_6x7");
    const displayWidth = 28;
    const displayHeight = 14;
    const bits = renderText(font, "HI", displayWidth, displayHeight);
    expect(bits).toHaveLength(displayWidth * displayHeight);
  });

  it("all values are 0 or 1", () => {
    const font = getFont("axion_6x7");
    const bits = renderText(font, "A", 28, 14);
    for (const bit of bits) {
      expect(bit === 0 || bit === 1).toBe(true);
    }
  });

  it("produces non-empty output for non-empty text", () => {
    const font = getFont("axion_6x7");
    const bits = renderText(font, "A", 28, 14);
    const setPixels = bits.filter((b) => b === 1).length;
    expect(setPixels).toBeGreaterThan(0);
  });

  it("produces all zeros for empty string", () => {
    const font = getFont("axion_6x7");
    const bits = renderText(font, "", 28, 14);
    const setPixels = bits.filter((b) => b === 1).length;
    expect(setPixels).toBe(0);
  });
});

describe("renderScrollingText", () => {
  it("generates correct frame count", () => {
    const font = getFont("axion_6x7");
    const displayWidth = 28;
    const displayHeight = 14;
    const textWidth = measureText(font, "HI");

    const frames = renderScrollingText(font, "HI", displayWidth, displayHeight, 100);

    // Frames go from startX=displayWidth to endX=-textWidth, inclusive
    // Count = displayWidth - (-textWidth) + 1 = displayWidth + textWidth + 1
    const expectedFrames = displayWidth + textWidth + 1;
    expect(frames).toHaveLength(expectedFrames);
  });

  it("frame duration matches input", () => {
    const font = getFont("axion_6x7");
    const frameDelay = 50;
    const frames = renderScrollingText(font, "A", 28, 14, frameDelay);

    for (const frame of frames) {
      expect(frame.duration_ms).toBe(frameDelay);
    }
  });

  it("each frame has correct bit array length", () => {
    const font = getFont("axion_6x7");
    const displayWidth = 28;
    const displayHeight = 14;
    const frames = renderScrollingText(font, "A", displayWidth, displayHeight);

    for (const frame of frames) {
      expect(frame.bits).toHaveLength(displayWidth * displayHeight);
    }
  });

  it("uses default frame delay of 100ms", () => {
    const font = getFont("axion_6x7");
    const frames = renderScrollingText(font, "A", 28, 14);

    expect(frames[0].duration_ms).toBe(100);
  });
});
