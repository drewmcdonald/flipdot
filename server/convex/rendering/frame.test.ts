import { describe, it, expect } from "vitest";
import {
  createFrame,
  createBlankFrame,
  createTestPattern,
  createCheckerboard,
  DISPLAY_WIDTH,
  DISPLAY_HEIGHT,
  DISPLAY_BITS,
} from "./frame";
import { base64ToBits } from "./bits";

describe("display constants", () => {
  it("DISPLAY_WIDTH is 28", () => {
    expect(DISPLAY_WIDTH).toBe(28);
  });

  it("DISPLAY_HEIGHT is 14", () => {
    expect(DISPLAY_HEIGHT).toBe(14);
  });

  it("DISPLAY_BITS equals DISPLAY_WIDTH * DISPLAY_HEIGHT", () => {
    expect(DISPLAY_BITS).toBe(DISPLAY_WIDTH * DISPLAY_HEIGHT);
  });

  it("DISPLAY_BITS is 392", () => {
    expect(DISPLAY_BITS).toBe(392);
  });
});

describe("createFrame", () => {
  it("creates a frame from a valid bit array", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    const frame = createFrame(bits);

    expect(frame.width).toBe(DISPLAY_WIDTH);
    expect(frame.height).toBe(DISPLAY_HEIGHT);
    expect(frame.duration_ms).toBeNull();
    expect(typeof frame.data_b64).toBe("string");
  });

  it("accepts an explicit duration_ms", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    const frame = createFrame(bits, 500);

    expect(frame.duration_ms).toBe(500);
  });

  it("accepts null duration_ms", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    const frame = createFrame(bits, null);

    expect(frame.duration_ms).toBeNull();
  });

  it("defaults duration_ms to null when omitted", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    const frame = createFrame(bits);

    expect(frame.duration_ms).toBeNull();
  });

  it("throws on too few bits", () => {
    const bits = new Array(DISPLAY_BITS - 1).fill(0);
    expect(() => createFrame(bits)).toThrow(
      `Invalid bit count: expected ${DISPLAY_BITS}, got ${DISPLAY_BITS - 1}`
    );
  });

  it("throws on too many bits", () => {
    const bits = new Array(DISPLAY_BITS + 1).fill(0);
    expect(() => createFrame(bits)).toThrow(
      `Invalid bit count: expected ${DISPLAY_BITS}, got ${DISPLAY_BITS + 1}`
    );
  });

  it("throws on empty array", () => {
    expect(() => createFrame([])).toThrow("Invalid bit count");
  });

  it("throws on invalid bit values", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    bits[10] = 2;
    expect(() => createFrame(bits)).toThrow("Invalid bit value at index 10: 2");
  });

  it("throws on negative bit values", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    bits[0] = -1;
    expect(() => createFrame(bits)).toThrow("Invalid bit value at index 0: -1");
  });

  it("round-trips bit data through base64 encoding", () => {
    const bits = new Array(DISPLAY_BITS).fill(0);
    // Set some specific bits
    bits[0] = 1;
    bits[7] = 1;
    bits[27] = 1;
    bits[100] = 1;
    bits[391] = 1;

    const frame = createFrame(bits);
    const decoded = base64ToBits(frame.data_b64, DISPLAY_BITS);

    expect(decoded).toEqual(bits);
  });

  it("round-trips all-ones data", () => {
    const bits = new Array(DISPLAY_BITS).fill(1);
    const frame = createFrame(bits);
    const decoded = base64ToBits(frame.data_b64, DISPLAY_BITS);

    expect(decoded).toEqual(bits);
  });
});

describe("createBlankFrame", () => {
  it("produces a frame with all zeros", () => {
    const frame = createBlankFrame();
    const bits = base64ToBits(frame.data_b64, DISPLAY_BITS);

    expect(bits.every((b) => b === 0)).toBe(true);
  });

  it("has correct dimensions", () => {
    const frame = createBlankFrame();

    expect(frame.width).toBe(DISPLAY_WIDTH);
    expect(frame.height).toBe(DISPLAY_HEIGHT);
  });

  it("has null duration_ms", () => {
    const frame = createBlankFrame();
    expect(frame.duration_ms).toBeNull();
  });
});

describe("createTestPattern", () => {
  it("produces a frame with all ones", () => {
    const frame = createTestPattern();
    const bits = base64ToBits(frame.data_b64, DISPLAY_BITS);

    expect(bits.every((b) => b === 1)).toBe(true);
  });

  it("has correct dimensions", () => {
    const frame = createTestPattern();

    expect(frame.width).toBe(DISPLAY_WIDTH);
    expect(frame.height).toBe(DISPLAY_HEIGHT);
  });

  it("has null duration_ms", () => {
    const frame = createTestPattern();
    expect(frame.duration_ms).toBeNull();
  });
});

describe("createCheckerboard", () => {
  it("produces an alternating pattern", () => {
    const frame = createCheckerboard();
    const bits = base64ToBits(frame.data_b64, DISPLAY_BITS);

    for (let y = 0; y < DISPLAY_HEIGHT; y++) {
      for (let x = 0; x < DISPLAY_WIDTH; x++) {
        const index = y * DISPLAY_WIDTH + x;
        const expected = (x + y) % 2;
        expect(bits[index]).toBe(expected);
      }
    }
  });

  it("has correct dimensions", () => {
    const frame = createCheckerboard();

    expect(frame.width).toBe(DISPLAY_WIDTH);
    expect(frame.height).toBe(DISPLAY_HEIGHT);
  });

  it("has null duration_ms", () => {
    const frame = createCheckerboard();
    expect(frame.duration_ms).toBeNull();
  });

  it("differs from blank and test pattern frames", () => {
    const checkerboard = createCheckerboard();
    const blank = createBlankFrame();
    const testPattern = createTestPattern();

    expect(checkerboard.data_b64).not.toBe(blank.data_b64);
    expect(checkerboard.data_b64).not.toBe(testPattern.data_b64);
  });
});
